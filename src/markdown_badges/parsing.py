"""Finding badge keywords in text, and rendering them inline."""

import re
import xml.etree.ElementTree as etree
from collections.abc import Mapping, Sequence

from markdown import Markdown
from markdown.inlinepatterns import InlineProcessor

from markdown_badges.catalogue import Badge, BadgeType, catalogue_for
from markdown_badges.styling import badge_element

__all__ = [
    "INLINE_PRIORITY",
    "BadgeInlineProcessor",
    "badges_in",
    "inline_re",
    "priority_of",
    "rank_of",
]

# Below Python-Markdown's `escape` (180), so `\!high` stays literal, and below
# `backtick` (190), so a keyword inside a code span survives verbatim.
INLINE_PRIORITY = 175


def inline_re(names: Sequence[str]) -> str:
    """`!<name>` regex for `names`: not preceded by a word char or another `!`,
    ending on a word boundary. Longer names first so none shadows a longer one."""
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return rf"(?<![\w!])!({alts})\b"


def _resolve(badges: Mapping[str, Badge] | None) -> Mapping[str, Badge]:
    return catalogue_for() if badges is None else badges


def _priority_names(badges: Mapping[str, Badge]) -> list[str]:
    return [b.name for b in badges.values() if b.type is BadgeType.PRIORITY]


def rank_of(name: str, badges: Mapping[str, Badge] | None = None) -> int:
    """Severity rank of `name` among the priority badges of `badges`, or -1.

    A status or branding badge has no rank and returns -1."""
    names = _priority_names(_resolve(badges))
    return names.index(name) if name in names else -1


def badges_in(text: str, badges: Mapping[str, Badge] | None = None) -> list[Badge]:
    """Every badge keyword found in `text`, of any type, in document order.

    This is a plain-text scan, not a Markdown parse: unlike the rendered badge,
    a keyword inside a code span or escaped as `\\!high` still counts."""
    resolved = _resolve(badges)
    if not resolved:
        return []
    pattern = inline_re(list(resolved))
    return [resolved[m.group(1)] for m in re.finditer(pattern, text)]


def priority_of(text: str, badges: Mapping[str, Badge] | None = None) -> str | None:
    """The highest-ranked priority badge name in `text`, or None.

    Status and branding badges are ignored. Same plain-text caveat as
    `badges_in`."""
    resolved = _resolve(badges)
    found = [b.name for b in badges_in(text, resolved) if b.type is BadgeType.PRIORITY]
    if not found:
        return None
    return max(found, key=lambda name: rank_of(name, resolved))


class BadgeInlineProcessor(InlineProcessor):
    """Render an inline `!<name>` keyword as a badge span."""

    def __init__(self, pattern: str, md: Markdown, badges: Mapping[str, Badge]) -> None:
        super().__init__(pattern, md)
        self.badges = badges

    # The stub types `handleMatch` on the legacy one-argument `Pattern` base,
    # so the correct two-argument InlineProcessor signature needs the ignore.
    def handleMatch(  # type: ignore[override]
        self, m: re.Match[str], data: str
    ) -> tuple[etree.Element, int, int]:
        return badge_element(self.badges[m.group(1)]), m.start(0), m.end(0)
