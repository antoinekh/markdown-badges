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
    assert set(only_branding) == {"gitlab", "github", "claude", "docker", "aws"}
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
    for name in ("gitlab", "github", "claude", "docker"):
        value = catalogue_for(BadgeType.BRANDING)[name].value
        assert "background-image:url('data:image/svg+xml," in value
        assert "http" not in value.split("background-image")[0]


def test_aws_badge_is_a_plain_colour():
    # No CC0 AWS mark exists, and the badge text already reads AWS.
    aws = catalogue_for(BadgeType.BRANDING)["aws"]
    assert aws.value == "#232f3e"
    assert "background-image" not in aws.value


def test_docker_badge_contrasts_with_its_white_mark():
    from markdown_badges.styling import text_color

    docker = catalogue_for(BadgeType.BRANDING)["docker"]
    assert text_color(docker.value) == "#fff"
