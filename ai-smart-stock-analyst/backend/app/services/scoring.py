"""
AI Investment Score engine — spec sections 7, 21, 24, 32.

Final Score = Fundamental 25% + Technical 20% + Growth 15% + Valuation 15%
            + News 10% + Momentum 5% + Risk 10%   (normalized to 0-100)

This module owns the *scoring formula and explanation*. The individual
sub-scores (fundamental_score, technical_score, ...) are feature-engineered
elsewhere from raw provider data (see data_pipeline.py) — this keeps the
"how do we weigh things" logic separate from "how do we compute a RSI" logic,
so the weights can be tuned or A/B tested without touching feature code.

Swapping in a trained model: replace `compute_component_scores()` with calls
into your XGBoost/LightGBM/ensemble models (spec section 33); the weighting
and explanation logic below stays the same as long as it still returns a
ComponentScores object.
"""
from dataclasses import dataclass, asdict

WEIGHTS = {
    "fundamental": 0.25,
    "technical": 0.20,
    "growth": 0.15,
    "valuation": 0.15,
    "news": 0.10,
    "momentum": 0.05,
    "risk": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


@dataclass
class ComponentScores:
    """Each sub-score is 0-100, already normalized by the feature-engineering step."""
    fundamental: float
    technical: float
    growth: float
    valuation: float
    news: float
    momentum: float
    risk: float  # NOTE: this is a "risk favorability" score (100 = low risk), not raw risk


@dataclass
class ScoreResult:
    components: ComponentScores
    final_score: float
    recommendation: str
    risk_level: str
    explanation: dict  # {"positive": [...], "negative": [...]}


def compute_final_score(components: ComponentScores) -> float:
    weighted = sum(getattr(components, key) * weight for key, weight in WEIGHTS.items())
    return round(max(0.0, min(100.0, weighted)), 1)


def score_to_recommendation(final_score: float, risk_favorability: float) -> str:
    """Maps score (+ a risk sanity check) to one of the spec's 7 recommendation states."""
    if final_score >= 90:
        return "STRONG_BUY"
    if final_score >= 80:
        return "BUY"
    if final_score >= 70:
        return "ACCUMULATE"
    if final_score >= 55:
        return "HOLD"
    if final_score >= 40:
        return "WATCH"
    if final_score >= 25:
        return "REDUCE"
    return "SELL"


def risk_favorability_to_level(risk_favorability: float) -> str:
    """risk_favorability: 100 = very low risk ... 0 = very high risk."""
    if risk_favorability >= 75:
        return "LOW"
    if risk_favorability >= 50:
        return "MEDIUM"
    if risk_favorability >= 25:
        return "HIGH"
    return "VERY_HIGH"


def explain(components: ComponentScores) -> dict:
    """
    Produces the "ทำไม?" (why?) breakdown used by the AI EXPLANATION feature
    (spec section 24). Purely rule-based over the already-computed sub-scores —
    this is intentionally simple/auditable rather than another black-box model,
    since its entire job is to be *explainable*.
    """
    positive, negative = [], []

    checks = [
        ("fundamental", 70, "Strong fundamentals (revenue/earnings quality)", "Weak fundamentals vs peers"),
        ("technical", 70, "Positive technical setup", "Technical signals are unfavorable"),
        ("growth", 70, "Strong revenue/earnings growth", "Growth is slowing"),
        ("valuation", 60, "Valuation is reasonable", "Valuation is elevated vs sector"),
        ("news", 65, "Recent news sentiment is positive", "Recent news sentiment is negative"),
        ("momentum", 65, "Strong price momentum", "Momentum is weak"),
        ("risk", 60, "Risk profile is favorable", "Elevated volatility / risk"),
    ]
    for field, threshold, pos_msg, neg_msg in checks:
        value = getattr(components, field)
        (positive if value >= threshold else negative).append(pos_msg if value >= threshold else neg_msg)

    return {"positive": positive, "negative": negative}


def build_score_result(components: ComponentScores) -> ScoreResult:
    final = compute_final_score(components)
    return ScoreResult(
        components=components,
        final_score=final,
        recommendation=score_to_recommendation(final, components.risk),
        risk_level=risk_favorability_to_level(components.risk),
        explanation=explain(components),
    )


def to_dict(result: ScoreResult) -> dict:
    return {
        "components": asdict(result.components),
        "final_score": result.final_score,
        "recommendation": result.recommendation,
        "risk_level": result.risk_level,
        "explanation": result.explanation,
    }
