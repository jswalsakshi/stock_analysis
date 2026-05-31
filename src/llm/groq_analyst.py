import os
from dotenv import load_dotenv

load_dotenv()


def get_groq_client():
    """Create and return a Groq client."""
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def validate_and_explain_pick(symbol, price, daily_rsi, weekly_rsi, monthly_rsi, sma50, price_vs_sma50_pct):
    """
    Use Groq LLM to validate the RSI + SMA50 setup and provide explanation.

    Returns:
        dict with keys: 'valid' (bool), 'confidence' (str), 'explanation' (str)
        Returns None if LLM is unavailable.
    """
    client = get_groq_client()
    if client is None:
        return None

    prompt = f"""You are an expert Indian stock market technical analyst. Analyze this stock setup and determine if it's a valid swing trade entry.

Stock: {symbol}
Current Price: ₹{price}
50-day SMA: ₹{sma50}
Price vs SMA50: {price_vs_sma50_pct:+.2f}%

RSI (14-period):
- Monthly RSI: {monthly_rsi}
- Weekly RSI: {weekly_rsi}
- Daily RSI: {daily_rsi}

Setup Rules:
1. Monthly RSI ≥ 60 = strong macro uptrend
2. Weekly RSI ≥ 60 = strong medium-term trend
3. Daily RSI 48-65 = pullback zone, not overbought
4. Price near SMA50 = taking support or consolidating

Based on this data:
1. Is this a VALID entry setup? (Yes/No)
2. Confidence level: High / Medium / Low
3. Brief explanation (2-3 sentences max) on why this is or isn't a good entry.
4. Any risk to watch out for (1 sentence).

Respond in this exact format:
VALID: Yes or No
CONFIDENCE: High or Medium or Low
EXPLANATION: your explanation here
RISK: risk note here"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )

        text = response.choices[0].message.content.strip()
        return _parse_llm_response(text)

    except Exception as e:
        return {"valid": True, "confidence": "Unknown", "explanation": f"LLM error: {str(e)}", "risk": "N/A"}


def get_batch_analysis(candidates_df):
    """
    Analyze all candidates in one LLM call for efficiency.

    Returns a list of dicts with 'valid', 'confidence', 'explanation', 'risk' for each stock.
    """
    client = get_groq_client()
    if client is None or candidates_df.empty:
        return None

    stocks_text = ""
    for _, row in candidates_df.iterrows():
        stocks_text += (
            f"- {row['symbol']}: Price ₹{row['price']}, SMA50 ₹{row['sma50']}, "
            f"Price vs SMA50: {row['price_vs_sma50_pct']:+.2f}%, "
            f"Daily RSI: {row['daily_rsi']}, Weekly RSI: {row['weekly_rsi']}, Monthly RSI: {row['monthly_rsi']}\n"
        )

    prompt = f"""You are an expert Indian stock market technical analyst. Analyze these stocks that passed RSI + SMA50 screening criteria.

Setup Rules applied:
- Monthly RSI ≥ 60 (macro uptrend confirmed)
- Weekly RSI ≥ 60 (medium-term momentum)
- Daily RSI 48-65 (healthy pullback, not overbought)
- Price at/near 50-day SMA support

Stocks passing the screen:
{stocks_text}

For EACH stock, provide:
1. Is the setup genuinely valid for a swing trade entry?
2. Confidence: High/Medium/Low
3. One-line explanation
4. One-line risk

Format your response as:
STOCK: SYMBOL
VALID: Yes/No
CONFIDENCE: High/Medium/Low
EXPLANATION: reason
RISK: risk note
---
(repeat for each stock)"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        text = response.choices[0].message.content.strip()
        return _parse_batch_response(text, candidates_df)

    except Exception as e:
        return [{"valid": True, "confidence": "Unknown", "explanation": f"LLM error: {e}", "risk": "N/A"}] * len(candidates_df)


def _parse_llm_response(text):
    """Parse single-stock LLM response."""
    result = {"valid": True, "confidence": "Medium", "explanation": "", "risk": ""}

    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("VALID:"):
            result["valid"] = "yes" in line.lower()
        elif line.upper().startswith("CONFIDENCE:"):
            result["confidence"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("EXPLANATION:"):
            result["explanation"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("RISK:"):
            result["risk"] = line.split(":", 1)[1].strip()

    return result


def _parse_batch_response(text, df):
    """Parse batch LLM response into list of dicts."""
    results = []
    blocks = text.split("---")

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        entry = {"valid": True, "confidence": "Medium", "explanation": "", "risk": ""}
        for line in block.split("\n"):
            line = line.strip()
            if line.upper().startswith("VALID:"):
                entry["valid"] = "yes" in line.lower()
            elif line.upper().startswith("CONFIDENCE:"):
                entry["confidence"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("EXPLANATION:"):
                entry["explanation"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("RISK:"):
                entry["risk"] = line.split(":", 1)[1].strip()
        results.append(entry)

    # Pad if LLM returned fewer entries
    while len(results) < len(df):
        results.append({"valid": True, "confidence": "Unknown", "explanation": "No LLM analysis", "risk": "N/A"})

    return results[:len(df)]
