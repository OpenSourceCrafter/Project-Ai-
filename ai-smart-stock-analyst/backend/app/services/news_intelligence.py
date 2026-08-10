"""
AI News Intelligence — spec sections 14, 15, 16, 17.

Three responsibilities:
  1. Important News Detection — tag which topic(s) an article touches
     (Earnings, FDA, M&A, etc.) so HIGH IMPACT badges can be shown.
  2. Sentiment classification — Positive / Neutral / Negative + a -1..+1 score.
     In production this calls a FinBERT (or similar) model — see `classify_sentiment`
     for where that model call belongs; a lexicon fallback is provided so the
     service still degrades gracefully rather than fabricating a verdict.
  3. Impact scoring — 0-100, combining topic severity + sentiment magnitude.

This module never invents a headline or fabricates sentiment for an article
it hasn't actually received (spec section 46).
"""
from dataclasses import dataclass

# Topics considered potentially high-impact (spec section 16)
HIGH_IMPACT_TOPICS = {
    "earnings", "revenue", "ceo change", "product launch", "fda",
    "government regulation", "lawsuit", "acquisition", "merger", "partnership",
    "dividend", "stock buyback", "insider trading", "analyst upgrade",
    "analyst downgrade", "interest rate", "inflation", "war",
    "geopolitical risk", "supply chain", "commodity price",
}

# Minimal lexicon fallback — replace with FinBERT / LLM call in production.
_POSITIVE_WORDS = {"beat", "surge", "growth", "upgrade", "record", "profit", "strong", "buyback"}
_NEGATIVE_WORDS = {"miss", "lawsuit", "downgrade", "decline", "cut", "recall", "probe", "weak"}


@dataclass
class SentimentResult:
    sentiment: str          # POSITIVE | NEUTRAL | NEGATIVE
    sentiment_score: float  # -1.0 .. +1.0
    model_name: str


@dataclass
class ImpactResult:
    topics: list[str]
    is_high_impact: bool
    impact_score: int       # 0-100


def detect_topics(headline: str, summary: str | None = None) -> list[str]:
    text = f"{headline} {summary or ''}".lower()
    return sorted(topic for topic in HIGH_IMPACT_TOPICS if topic in text)


def classify_sentiment(headline: str, summary: str | None = None) -> SentimentResult:
    """
    Placeholder rule-based classifier. Swap the body of this function for a
    real FinBERT / LLM call (spec section 33) — keep the return contract the
    same so callers (news_pipeline, API responses) don't need to change.
    """
    text = f"{headline} {summary or ''}".lower()
    pos_hits = sum(1 for w in _POSITIVE_WORDS if w in text)
    neg_hits = sum(1 for w in _NEGATIVE_WORDS if w in text)

    if pos_hits == neg_hits:
        return SentimentResult("NEUTRAL", 0.0, "lexicon-fallback-v0")

    score = (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)
    sentiment = "POSITIVE" if score > 0 else "NEGATIVE"
    return SentimentResult(sentiment, round(score, 2), "lexicon-fallback-v0")


def score_impact(topics: list[str], sentiment: SentimentResult) -> ImpactResult:
    """Impact = topic severity (more/rarer topics => higher) blended with
    how strongly the sentiment leans one way."""
    base = min(len(topics) * 20, 60)                    # topic coverage component
    magnitude = abs(sentiment.sentiment_score) * 40      # conviction component
    impact_score = int(round(min(base + magnitude, 100)))
    is_high_impact = impact_score >= 65 or bool(topics)
    return ImpactResult(topics=topics, is_high_impact=is_high_impact, impact_score=impact_score)


def analyze_article(headline: str, summary: str | None = None) -> dict:
    """Convenience wrapper used by the ingestion pipeline for a single article."""
    topics = detect_topics(headline, summary)
    sentiment = classify_sentiment(headline, summary)
    impact = score_impact(topics, sentiment)
    return {
        "topics": topics,
        "sentiment": sentiment.sentiment,
        "sentiment_score": sentiment.sentiment_score,
        "model_name": sentiment.model_name,
        "impact_score": impact.impact_score,
        "is_high_impact": impact.is_high_impact,
    }


def aggregate_sentiment(article_sentiments: list[SentimentResult]) -> dict:
    """Rolls up article-level sentiment into the Positive/Neutral/Negative %
    breakdown + overall 0-100 score shown in spec section 15."""
    if not article_sentiments:
        return {"positive_pct": 0, "neutral_pct": 0, "negative_pct": 0, "overall_score": None}

    total = len(article_sentiments)
    pos = sum(1 for s in article_sentiments if s.sentiment == "POSITIVE")
    neu = sum(1 for s in article_sentiments if s.sentiment == "NEUTRAL")
    neg = sum(1 for s in article_sentiments if s.sentiment == "NEGATIVE")

    avg_score = sum(s.sentiment_score for s in article_sentiments) / total  # -1..+1
    overall_score = round((avg_score + 1) * 50)  # rescale to 0-100

    return {
        "positive_pct": round(pos / total * 100),
        "neutral_pct": round(neu / total * 100),
        "negative_pct": round(neg / total * 100),
        "overall_score": overall_score,
    }
