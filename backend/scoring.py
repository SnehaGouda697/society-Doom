"""Monthly point aggregation and badge rules."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import PointEntry

CATEGORY_MAXIMUMS = {"cleanliness": 40, "discipline": 30, "events": 30}


def clamp_score(value: int | float, maximum: int) -> int:
    """Keep a category score between zero and its allowed maximum."""
    return max(0, min(maximum, int(value)))


def badge_for_score(score: int | float) -> str:
    if score >= 85:
        return "Hero"
    if score >= 70:
        return "Safe"
    if score >= 50:
        return "Warning"
    return "Doom Zone"


def score_breakdown(entries: list[PointEntry]) -> dict[str, int]:
    """Sum signed points by category, then enforce each category's limit."""
    totals = {category: 0 for category in CATEGORY_MAXIMUMS}
    for entry in entries:
        if entry.category in totals:
            totals[entry.category] += entry.points
    breakdown = {
        category: clamp_score(points, CATEGORY_MAXIMUMS[category])
        for category, points in totals.items()
    }
    breakdown["total"] = sum(breakdown.values())
    return breakdown


def monthly_score(session: Session, flat_id: int, month: int, year: int) -> dict[str, int | str]:
    """Load a flat's point entries and return its score, badge, and breakdown."""
    entries = session.scalars(
        select(PointEntry).where(
            PointEntry.flat_id == flat_id,
            PointEntry.month == month,
            PointEntry.year == year,
        )
    ).all()
    result: dict[str, int | str] = score_breakdown(entries)
    result["badge"] = badge_for_score(int(result["total"]))
    return result


def society_average(scores: list[int | float]) -> float:
    """Average the provided flat scores, returning zero for an empty society."""
    return round(sum(scores) / len(scores), 1) if scores else 0.0
