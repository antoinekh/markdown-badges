"""Tests for config resolution and validation."""

import markdown
import pytest

from markdown_badges import MarkdownBadgesExtension, resolve_badges
from markdown_badges.catalogue import BadgeType


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(text, extensions=["pymdownx.tasklist", MarkdownBadgesExtension(**cfg)])


def test_the_whole_catalogue_is_active_by_default():
    html = render("!high !wip !github")
    assert "badge--high" in html
    assert "badge--wip" in html
    assert "badge--github" in html


def test_catalogue_scope_narrows_the_active_badges():
    html = render("!high !wip", catalogue=["priority"])
    assert "badge--high" in html
    assert "badge--wip" not in html
    assert "!wip" in html


def test_an_empty_catalogue_scope_disables_the_catalogue():
    html = render("!high", catalogue=[])
    assert "badge" not in html
    assert "!high" in html


def test_a_user_badge_is_added():
    html = render("!jira", badges={"branding": {"jira": "#0052cc"}})
    assert 'class="badge badge--jira"' in html
    assert "background-color:#0052cc" in html


def test_a_user_badge_overrides_a_catalogue_colour_in_place():
    resolved = resolve_badges(["priority"], {"priority": {"critical": "#8e0000"}})
    assert resolved["critical"].value == "#8e0000"
    order = [b.name for b in resolved.values() if b.type is BadgeType.PRIORITY]
    assert order == ["trivial", "low", "medium", "high", "critical", "blocker"]


def test_a_new_user_priority_is_appended_after_the_catalogue_ones():
    resolved = resolve_badges(["priority"], {"priority": {"showstopper": "#000"}})
    order = [b.name for b in resolved.values() if b.type is BadgeType.PRIORITY]
    assert order[-1] == "showstopper"


def test_a_user_badge_works_with_an_empty_catalogue():
    html = render("!only", catalogue=[], badges={"status": {"only": "#123456"}})
    assert "badge--only" in html


def test_levels_option_raises_with_the_migration():
    with pytest.raises(ValueError, match="levels"):
        render("!high", levels={"high": "#000"})


def test_unknown_catalogue_type_raises():
    with pytest.raises(ValueError, match="priority, status, branding"):
        render("!high", catalogue=["nope"])


def test_unknown_badges_type_raises():
    with pytest.raises(ValueError, match="priority, status, branding"):
        render("!high", badges={"nope": {"x": "#000"}})


def test_badges_type_value_not_a_table_raises():
    with pytest.raises(ValueError, match="not a table"):
        render("!high", badges={"priority": ["#000"]})


def test_shorthand_pointing_at_an_unknown_badge_raises():
    with pytest.raises(ValueError, match="not in scope"):
        render("- [ ] ! x", shorthand={"!": "nosuchbadge"})


def test_shorthand_pointing_outside_the_catalogue_scope_raises():
    with pytest.raises(ValueError, match="not in scope"):
        render("- [ ] ! x", catalogue=["status"], shorthand={"!": "high"})


def test_non_string_badge_value_raises():
    with pytest.raises(ValueError, match="non-string"):
        render("!x", badges={"status": {"x": 42}})


def test_empty_badge_value_raises():
    with pytest.raises(ValueError, match="empty"):
        render("!x", badges={"status": {"x": "  "}})


def test_adding_to_two_types_keeps_catalogue_order():
    resolved = resolve_badges(
        ["priority", "status", "branding"],
        {"priority": {"showstopper": "#000"}, "status": {"triage": "#111"}},
    )
    types = [b.type for b in resolved.values()]
    # Each type still forms one contiguous run, in catalogue type order.
    assert types == sorted(
        types,
        key=lambda t: [BadgeType.PRIORITY, BadgeType.STATUS, BadgeType.BRANDING].index(t),
    )


def test_a_new_badge_lands_next_to_its_own_type():
    resolved = resolve_badges(["priority", "status"], {"priority": {"showstopper": "#000"}})
    names = list(resolved)
    assert names.index("showstopper") == names.index("blocker") + 1


def test_an_override_keeps_the_catalogue_type():
    # `critical` is a priority badge. Declaring it under `status` must not
    # turn it into one, or it would silently lose its rank.
    resolved = resolve_badges(["priority"], {"status": {"critical": "#8e0000"}})
    assert resolved["critical"].type is BadgeType.PRIORITY
    assert resolved["critical"].value == "#8e0000"
