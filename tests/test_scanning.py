"""Tests for the reusable text-scanning API."""

from markdown_badges.catalogue import Badge, BadgeType, catalogue_for
from markdown_badges.parsing import badges_in, priority_of, rank_of


def test_rank_of_orders_catalogue_priorities():
    assert rank_of("trivial") < rank_of("high") < rank_of("blocker")


def test_rank_of_returns_minus_one_for_an_unknown_name():
    assert rank_of("nope") == -1


def test_rank_of_returns_minus_one_for_a_non_priority_badge():
    # `done` exists, but it is a status badge, so it has no severity rank.
    assert rank_of("done") == -1


def test_priority_of_finds_a_keyword():
    assert priority_of("Ping !critical vendor now") == "critical"


def test_priority_of_returns_the_highest_rank():
    assert priority_of("!low but also !high later") == "high"


def test_priority_of_ignores_status_and_branding():
    assert priority_of("!wip on !github") is None


def test_priority_of_returns_none_for_plain_text():
    assert priority_of("Weekly backup check") is None
    assert priority_of("") is None
    assert priority_of("an important !note") is None


def test_badges_in_returns_every_type_in_document_order():
    found = badges_in("!github then !high then !wip")
    assert [b.name for b in found] == ["github", "high", "wip"]
    assert [b.type for b in found] == [
        BadgeType.BRANDING,
        BadgeType.PRIORITY,
        BadgeType.STATUS,
    ]


def test_badges_in_returns_an_empty_list_for_plain_text():
    assert badges_in("nothing here") == []


def test_scanning_accepts_a_custom_badge_map():
    badges = {
        "p1": Badge("p1", "#111", BadgeType.PRIORITY),
        "p2": Badge("p2", "#222", BadgeType.PRIORITY),
    }
    assert priority_of("!p1 and !p2", badges) == "p2"
    assert rank_of("p1", badges) == 0
    assert priority_of("!high", badges) is None


def test_scanning_respects_word_boundaries():
    assert priority_of("foo!high and !highest priority") is None


def test_longer_names_are_not_shadowed():
    # `p` is a strict prefix of `p1`: alternation order must try `p1` first,
    # or `!p1` would match `p` and leave a stray `1` behind.
    badges = {
        "p": Badge("p", "#111", BadgeType.PRIORITY),
        "p1": Badge("p1", "#222", BadgeType.PRIORITY),
    }
    assert [b.name for b in badges_in("!p1", badges)] == ["p1"]


def test_scanning_is_a_raw_scan_not_a_markdown_parse():
    assert priority_of("use `!critical` verbatim") == "critical"
    assert priority_of(r"escaped \!high") == "high"


def test_catalogue_subset_limits_what_is_found():
    only_priority = catalogue_for(BadgeType.PRIORITY)
    assert badges_in("!high and !github", only_priority) == [only_priority["high"]]
