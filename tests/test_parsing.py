"""Unit tests for the reusable priority-parsing API."""

from markdown_priority_badges import LEVELS, level_rank, priority_of


def test_levels_are_ascending_builtins():
    assert LEVELS == ("low", "medium", "high", "critical")


def test_level_rank_orders_builtins():
    assert level_rank("low") < level_rank("high") < level_rank("critical")
    assert level_rank("nope") == -1


def test_leading_single_bang_is_high():
    assert priority_of("! Call vendor") == "high"


def test_leading_double_bang_is_critical():
    assert priority_of("!! Ship the patch") == "critical"


def test_leading_keyword_is_that_level():
    assert priority_of("!high Rotate keys") == "high"


def test_midline_keyword_is_detected():
    assert priority_of("Ping !critical vendor now") == "critical"


def test_highest_marker_anywhere_wins():
    assert priority_of("!low but also !high later") == "high"


def test_plain_text_has_no_priority():
    assert priority_of("Weekly backup check") is None
    assert priority_of("") is None
    assert priority_of("an important !note") is None  # not a level keyword


def test_custom_level_recognized_only_when_listed():
    levels = (*LEVELS, "blocker")
    assert priority_of("!blocker vendor access", levels) == "blocker"
    assert priority_of("!blocker vendor access") is None  # not in default LEVELS


def test_shorthand_ignored_when_high_not_in_levels():
    assert priority_of("! do it", ("low", "medium")) is None


def test_levels_accepts_a_name_to_color_mapping():
    # The extension's own `levels` option is a dict; reusing it must work.
    levels = {"low": "#2e7d32", "high": "#ef6c00", "blocker": "#7b1fa2"}
    assert priority_of("!blocker vendor access", levels) == "blocker"
    assert priority_of("!low then !high", levels) == "high"
    assert level_rank("blocker", levels) == 2
    assert level_rank("nope", levels) == -1


def test_parsing_is_a_raw_scan_not_a_markdown_parse():
    # Documented limit: `priority_of` sees text the renderer would leave alone.
    assert priority_of("use `!critical` verbatim") == "critical"
    assert priority_of(r"escaped \!high") == "high"
