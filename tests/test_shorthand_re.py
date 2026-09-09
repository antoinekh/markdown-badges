"""Tests for `shorthand_re`, the task-list shorthand pattern builder."""

from markdown_badges.parsing import shorthand_re


def test_a_single_marker_matches_after_a_checkbox():
    m = shorthand_re(["!"]).match("[ ] ! Prod is down")
    assert m is not None
    assert m.group("checkbox") == "[ ] "
    assert m.group("marker") == "!"
    assert m.group("rest") == "Prod is down"


def test_longest_marker_wins_when_both_are_configured():
    m = shorthand_re(["!", "!!"]).match("[ ] !! Prod down")
    assert m is not None
    assert m.group("marker") == "!!"


def test_a_multi_character_marker_works():
    m = shorthand_re([">>"]).match("[ ] >> Later")
    assert m is not None
    assert m.group("marker") == ">>"
    assert m.group("rest") == "Later"


def test_a_marker_with_no_trailing_whitespace_does_not_match():
    assert shorthand_re(["!"]).match("[ ] !important") is None


def test_checkbox_states_all_match():
    pattern = shorthand_re(["!"])
    assert pattern.match("[ ] ! text") is not None
    assert pattern.match("[x] ! text") is not None
    assert pattern.match("[X] ! text") is not None


def test_a_regex_special_marker_is_escaped_and_matches_literally():
    m = shorthand_re(["?"]).match("[ ] ? Needs a decision")
    assert m is not None
    assert m.group("marker") == "?"
    assert m.group("rest") == "Needs a decision"
    # Would match anything if `?` were left as an unescaped quantifier.
    assert shorthand_re(["+"]).match("[ ] x extra text") is None
