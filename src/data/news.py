from gnews import GNews
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

# Download VADER lexicon on first use
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

sia = SentimentIntensityAnalyzer()


def get_stock_news(symbol, company_name=None, max_results=10):
    query = f"{symbol} stock" if not company_name else f"{company_name} stock"
    try:
        gn = GNews(language="en", country="IN", period="1d", max_results=max_results)
        articles = gn.get_news(query)
        return articles if articles else []
    except Exception:
        return []


def get_market_news(max_results=10):
    try:
        gn = GNews(language="en", country="IN", period="1d", max_results=max_results)
        articles = gn.get_news("Indian stock market Nifty")
        return articles if articles else []
    except Exception:
        return []


def score_sentiment(text):
    if not text:
        return 0.0
    scores = sia.polarity_scores(text)
    return scores["compound"]


def get_news_sentiment(symbol, company_name=None, max_results=5):
    articles = get_stock_news(symbol, company_name, max_results)
    if not articles:
        return 0.0, []

    scored_articles = []
    for article in articles:
        title = article.get("title", "")
        sentiment = score_sentiment(title)
        scored_articles.append({
            "title": title,
            "published": article.get("published date", ""),
            "source": article.get("publisher", {}).get("title", "Unknown"),
            "sentiment": sentiment,
        })

    avg_sentiment = sum(a["sentiment"] for a in scored_articles) / len(scored_articles) if scored_articles else 0.0
    return avg_sentiment, scored_articles


def get_bulk_sentiment(symbols, company_names=None):
    results = {}
    for i, symbol in enumerate(symbols):
        name = company_names[i] if company_names and i < len(company_names) else None
        avg_sent, articles = get_news_sentiment(symbol, name, max_results=5)
        results[symbol] = {"avg_sentiment": avg_sent, "articles": articles}
    return results


def get_market_sentiment():
    articles = get_market_news(max_results=10)
    if not articles:
        return 0.0, []

    scored = []
    for article in articles:
        title = article.get("title", "")
        sentiment = score_sentiment(title)
        scored.append({
            "title": title,
            "published": article.get("published date", ""),
            "source": article.get("publisher", {}).get("title", "Unknown"),
            "sentiment": sentiment,
        })

    avg = sum(a["sentiment"] for a in scored) / len(scored) if scored else 0.0
    return avg, scored
