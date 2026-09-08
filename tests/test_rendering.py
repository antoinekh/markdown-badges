"""Rendering tests for the badge extension."""

import markdown

from markdown_badges import MarkdownBadgesExtension


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(
        text, extensions=["tables", "pymdownx.tasklist", MarkdownBadgesExtension(**cfg)]
    )


def test_inline_keyword_in_prose():
    html = render("This migration is !critical and blocks the release.")
    assert 'class="badge badge--critical"' in html
    assert "background-color:#d32f2f" in html
    assert "!critical" not in html


def test_inline_keyword_in_a_heading():
    html = render("# !high Rotate the keys")
    assert "<h1" in html
    assert "badge--high" in html
    assert "Rotate the keys" in html


def test_inline_keyword_in_a_table_cell():
    html = render("| a | b |\n| --- | --- |\n| x | !wip |\n")
    assert "badge--wip" in html
    assert "<td" in html


def test_unknown_keyword_is_left_alone():
    html = render("Watch out! Also !important and !nosuch are left alone.")
    assert "badge" not in html


def test_word_boundaries_are_respected():
    assert "badge" not in render("foo!high and !highest priority")


def test_keyword_in_a_code_span_survives():
    html = render("Use `!critical` verbatim in code.")
    assert "badge" not in html
    assert "!critical" in html


def test_keyword_in_a_code_block_survives():
    html = render("```\n!critical stays literal\n```\n")
    assert "badge" not in html
    assert "!critical stays literal" in html


def test_escaped_keyword_stays_literal():
    html = render(r"Literal \!high and real !high")
    assert html.count("badge--high") == 1
    assert "Literal !high and real" in html
    assert "\\" not in html


def test_text_colour_is_auto_contrasted():
    assert "color:#fff" in render("!critical")
    assert "color:#000" in render("!medium")


def test_extended_value_adds_declarations():
    html = render("!icon", badges={"branding": {"icon": "#b71c1c;padding-left:2em"}})
    assert "background-color:#b71c1c;padding-left:2em;color:#fff;" in html


def test_extended_value_contrasts_against_its_leading_colour():
    html = render("!a", badges={"status": {"a": "#eee;box-shadow:0 0 2px #000"}})
    assert "background-color:#eee;box-shadow:0 0 2px #000;color:#000;" in html


def test_three_and_eight_digit_hex_are_contrasted():
    html = render("!a !b", badges={"status": {"a": "#eee", "b": "#eeeeeeff"}})
    assert "background-color:#eee;color:#000" in html
    assert "background-color:#eeeeeeff;color:#000" in html


def test_branding_badge_inlines_its_logo():
    html = render("!github")
    assert "badge--github" in html
    assert "data:image/svg+xml," in html
