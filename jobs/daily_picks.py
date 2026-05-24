import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from src.data.prices import get_universe, get_index_data
from src.data.news import get_market_sentiment
from src.strategies.short_term import screen_short_term
from src.strategies.long_term import screen_long_term
from src.notify.email_sender import send_daily_digest


def main():
    print("🚀 Starting daily stock pick generation...")

    # Load universe
    symbols = get_universe()
    print(f"📊 Scanning {len(symbols)} stocks...")

    # Get market context
    nifty = get_index_data("^NSEI", period="5d")
    nifty_change = 0
    if not nifty.empty and len(nifty) >= 2:
        nifty_change = ((nifty["Close"].iloc[-1] - nifty["Close"].iloc[-2]) / nifty["Close"].iloc[-2]) * 100

    # Market sentiment
    market_sent, market_articles = get_market_sentiment()
    headlines = [a["title"] for a in market_articles[:5]]

    market_summary = {
        "nifty_change": float(nifty_change),
        "market_sentiment": float(market_sent),
        "headlines": headlines,
    }

    # Run short-term screen
    print("⚡ Running short-term momentum screen...")
    short_term = screen_short_term(symbols)
    if not short_term.empty:
        print(f"  Found {len(short_term)} short-term candidates, top 5 selected.")
    else:
        print("  No short-term picks today.")

    # Run long-term screen
    print("💰 Running long-term dividend screen...")
    long_term = screen_long_term(symbols)
    if not long_term.empty:
        print(f"  Found {len(long_term)} long-term candidates, top 5 selected.")
    else:
        print("  No long-term picks today.")

    # Save picks to JSON for Streamlit
    picks_data = {
        "date": pd.Timestamp.now().isoformat(),
        "market_summary": market_summary,
        "short_term": short_term.head(5).to_dict("records") if not short_term.empty else [],
        "long_term": long_term.head(5).to_dict("records") if not long_term.empty else [],
    }

    picks_path = Path(__file__).resolve().parents[1] / "data" / "latest_picks.json"
    picks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(picks_path, "w") as f:
        json.dump(picks_data, f, indent=2, default=str)
    print(f"💾 Picks saved to {picks_path}")

    # Send email
    try:
        send_daily_digest(
            short_term.head(5) if not short_term.empty else pd.DataFrame(),
            long_term.head(5) if not long_term.empty else pd.DataFrame(),
            market_summary,
        )
        print("📧 Email digest sent successfully!")
    except Exception as e:
        print(f"⚠️ Email sending failed: {e}")
        print("  (Picks are still saved to data/latest_picks.json)")

    print("✅ Daily picks generation complete!")


if __name__ == "__main__":
    main()
