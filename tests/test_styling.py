"""Tests for badge colour maths and span construction."""

import xml.etree.ElementTree as etree

from markdown_badges.catalogue import Badge, BadgeType
from markdown_badges.styling import badge_element, badge_html, text_color, to_hex6


def test_to_hex6_expands_three_digit_hex():
    assert to_hex6("#eee") == "eeeeee"


def test_to_hex6_drops_the_alpha_channel():
    assert to_hex6("#eeeeeeff") == "eeeeee"
    assert to_hex6("#eeef") == "eeeeee"


def test_to_hex6_resolves_a_named_colour():
    assert to_hex6("yellow") == "ffff00"


def test_to_hex6_reads_up_to_the_first_semicolon():
    assert to_hex6("#eee;box-shadow:0 0 2px #000") == "eeeeee"


def test_to_hex6_returns_none_for_an_unresolvable_value():
    assert to_hex6("rgb(10,10,10)") is None


def test_text_color_contrasts():
    assert text_color("#d32f2f") == "#fff"
    assert text_color("#f9a825") == "#000"


def test_text_color_falls_back_to_white():
    assert text_color("rgb(10,10,10)") == "#fff"


def test_badge_element_carries_class_and_style():
    el = badge_element(Badge("wip", "#0277bd", BadgeType.STATUS))
    assert el.get("class") == "badge badge--wip"
    style = el.get("style") or ""
    assert "background-color:#0277bd;" in style
    assert style.endswith("color:#fff;")
    assert el.text == "wip"


def test_badge_element_passes_extended_css_through():
    el = badge_element(Badge("icon", "#900;padding-left:2em", BadgeType.BRANDING))
    assert "background-color:#900;padding-left:2em;color:#fff;" in (el.get("style") or "")


def test_badge_html_ends_with_a_space():
    html = badge_html(Badge("done", "#37474f", BadgeType.STATUS))
    assert html.endswith("> ") or html.endswith("</span> ")
    assert etree.fromstring(html.strip()).tag == "span"
