from types import SimpleNamespace

from backend.scoring import badge_for_score, score_breakdown, society_average


def test_score_breakdown_applies_caps_and_penalties():
    entries = [
        SimpleNamespace(category="cleanliness", points=45),
        SimpleNamespace(category="discipline", points=24),
        SimpleNamespace(category="discipline", points=-8),
        SimpleNamespace(category="events", points=-50),
    ]
    assert score_breakdown(entries) == {
        "cleanliness": 40,
        "discipline": 16,
        "events": 0,
        "total": 56,
    }


def test_badge_boundaries_and_empty_average():
    assert [badge_for_score(score) for score in (90, 70, 50, 49)] == ["Hero", "Safe", "Warning", "Doom Zone"]
    assert society_average([]) == 0.0
    assert society_average([60, 80]) == 70.0
