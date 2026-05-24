import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def build_html_digest(short_term_picks, long_term_picks, market_summary=None):
    """Build HTML email body from picks DataFrames."""
    date_str = pd.Timestamp.now().strftime("%d %b %Y")

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: 0 auto; }}
            h1 {{ color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 10px; }}
            h2 {{ color: #2e86ab; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th {{ background-color: #2e86ab; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .positive {{ color: #27ae60; font-weight: bold; }}
            .negative {{ color: #e74c3c; font-weight: bold; }}
            .disclaimer {{ font-size: 11px; color: #888; font-style: italic; margin-top: 30px;
                          border-top: 1px solid #ddd; padding-top: 10px; }}
            .market-pulse {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <h1>📈 Daily Stock Picks – {date_str}</h1>
    """

    # Short-term picks section
    html += "<h2>⚡ Short-Term Picks (1-10 days)</h2>"
    if short_term_picks is not None and not short_term_picks.empty:
        html += """<table>
            <tr><th>Ticker</th><th>Price</th><th>Buy Zone</th><th>Stop Loss</th><th>Target</th><th>Why</th></tr>"""
        for _, row in short_term_picks.head(5).iterrows():
            from src.strategies.short_term import get_short_term_reason
            reason = get_short_term_reason(row)
            html += f"""<tr>
                <td><strong>{row['symbol']}</strong></td>
                <td>₹{row['price']:.2f}</td>
                <td>₹{row['price']*0.99:.2f} - ₹{row['price']*1.01:.2f}</td>
                <td class="negative">₹{row['stop_loss']:.2f}</td>
                <td class="positive">₹{row['target']:.2f}</td>
                <td>{reason}</td>
            </tr>"""
        html += "</table>"
    else:
        html += "<p>No short-term picks today (market conditions may be unfavorable).</p>"

    # Long-term picks section
    html += "<h2>💰 Long-Term Dividend Picks (12+ months)</h2>"
    if long_term_picks is not None and not long_term_picks.empty:
        html += """<table>
            <tr><th>Ticker</th><th>Yield %</th><th>ROCE %</th><th>P/E</th><th>Why</th></tr>"""
        for _, row in long_term_picks.head(5).iterrows():
            from src.strategies.long_term import get_long_term_reason
            reason = get_long_term_reason(row)
            html += f"""<tr>
                <td><strong>{row['symbol']}</strong></td>
                <td class="positive">{row['dividend_yield']:.1f}%</td>
                <td>{row['ROCE']:.1f}%</td>
                <td>{row['trailing_PE']:.1f}</td>
                <td>{reason}</td>
            </tr>"""
        html += "</table>"
    else:
        html += "<p>No long-term picks meeting all quality criteria today.</p>"

    # Market pulse
    if market_summary:
        html += '<div class="market-pulse">'
        html += "<h2>📊 Market Pulse</h2>"
        if "nifty_change" in market_summary:
            direction = "positive" if market_summary["nifty_change"] >= 0 else "negative"
            html += f'<p>Nifty 50: <span class="{direction}">{market_summary["nifty_change"]:+.2f}%</span></p>'
        if "headlines" in market_summary:
            html += "<p><strong>Top Headlines:</strong></p><ul>"
            for headline in market_summary["headlines"][:3]:
                html += f"<li>{headline}</li>"
            html += "</ul>"
        html += "</div>"

    # Disclaimer
    html += """
        <p class="disclaimer">
            ⚠️ <strong>Disclaimer:</strong> This is an automated screener for educational purposes only,
            not investment advice. Past performance does not guarantee future results. Always verify
            information independently and consult a SEBI-registered advisor before making investment decisions.
            The creators are not responsible for any financial losses.
        </p>
    </body>
    </html>
    """
    return html


def send_daily_digest(short_term_picks, long_term_picks, market_summary=None):
    """Send the daily email digest."""
    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")
    recipients_str = os.environ.get("RECIPIENTS", "")

    if not email_address or not email_password:
        raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment")

    recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
    if not recipients:
        recipients = [email_address]

    html_body = build_html_digest(short_term_picks, long_term_picks, market_summary)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Daily Stock Picks – {pd.Timestamp.now().strftime('%d %b %Y')}"
    msg["From"] = email_address
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)
        server.sendmail(email_address, recipients, msg.as_string())

    print(f"Email sent to {', '.join(recipients)}")
