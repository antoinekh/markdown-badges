"""Tests for the shipped badge catalogue."""

from markdown_badges.catalogue import CATALOGUE, Badge, BadgeType, catalogue_for


def test_every_catalogue_name_is_unique():
    names = [b.name for b in CATALOGUE]
    assert len(names) == len(set(names))


def test_catalogue_covers_all_three_types():
    assert {b.type for b in CATALOGUE} == set(BadgeType)


def test_priority_badges_are_in_ascending_severity_order():
    priority = [b.name for b in CATALOGUE if b.type is BadgeType.PRIORITY]
    assert priority == ["trivial", "low", "medium", "high", "critical", "blocker"]


def test_catalogue_for_with_no_arguments_returns_everything():
    assert len(catalogue_for()) == len(CATALOGUE)


def test_catalogue_for_filters_by_type():
    only_branding = catalogue_for(BadgeType.BRANDING)
    assert set(only_branding) == {"gitlab", "github", "claude"}
    assert all(b.type is BadgeType.BRANDING for b in only_branding.values())


def test_catalogue_for_accepts_several_types():
    subset = catalogue_for(BadgeType.PRIORITY, BadgeType.STATUS)
    assert "high" in subset
    assert "wip" in subset
    assert "github" not in subset


def test_catalogue_for_preserves_catalogue_order():
    order = [b.name for b in CATALOGUE if b.type is BadgeType.PRIORITY]
    assert list(catalogue_for(BadgeType.PRIORITY)) == order


def test_badge_is_frozen():
    badge = Badge("x", "#000", BadgeType.STATUS)
    try:
        badge.name = "y"  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("Badge must be immutable")


def test_branding_badges_inline_their_icon():
    for name in ("gitlab", "github", "claude"):
        value = catalogue_for(BadgeType.BRANDING)[name].value
        assert "background-image:url('data:image/svg+xml," in value
        assert "http" not in value.split("background-image")[0]
