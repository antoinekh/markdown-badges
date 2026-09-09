"""Tests for the configurable task-list shorthand."""

import markdown

from markdown_badges import MarkdownBadgesExtension


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(text, extensions=["pymdownx.tasklist", MarkdownBadgesExtension(**cfg)])


def test_no_shorthand_by_default():
    html = render("- [ ] !! Prod is down")
    assert "badge--critical" not in html
    assert "!! Prod is down" in html


def test_a_configured_marker_renders_a_badge():
    html = render("- [ ] ! Call vendor", shorthand={"!": "high"})
    assert 'class="badge badge--high"' in html
    assert "Call vendor" in html
    assert "! Call vendor" not in html


def test_longest_marker_wins():
    html = render("- [ ] !! Prod down", shorthand={"!": "high", "!!": "critical"})
    assert "badge--critical" in html
    assert "badge--high" not in html


def test_a_multi_character_marker_works():
    html = render("- [ ] >> Later", shorthand={">>": "low"})
    assert "badge--low" in html
    assert "Later" in html


def test_a_marker_needs_trailing_whitespace():
    html = render("- [ ] !important CSS flag", shorthand={"!": "high"})
    assert "badge" not in html
    assert "!important CSS flag" in html


def test_shorthand_works_on_a_checked_item():
    html = render("- [x] ! Rotated keys", shorthand={"!": "high"})
    assert "badge--high" in html
    assert "checked" in html


def test_shorthand_works_on_an_uppercase_checkbox():
    html = render("- [X] ! Rotated keys", shorthand={"!": "high"})
    assert "badge--high" in html


def test_shorthand_works_in_a_loose_list():
    html = render("- [ ] ! Prod down\n\n- [ ] second\n", shorthand={"!": "high"})
    assert "badge--high" in html


def test_shorthand_works_in_a_nested_list():
    html = render("- [ ] parent\n    - [ ] ! child", shorthand={"!": "high"})
    assert "badge--high" in html
    assert "child" in html


def test_shorthand_can_point_at_a_status_badge():
    html = render("- [ ] ~ Half migrated", shorthand={"~": "wip"})
    assert "badge--wip" in html
