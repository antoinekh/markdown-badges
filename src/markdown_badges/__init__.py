"""Badges for Markdown.

Write ``!<name>`` anywhere (prose, headings, table cells, list items) and it
renders as a small inline pill. Names come from a catalogue that ships with the
package, grouped into three types: ``priority`` badges carry a severity rank,
``status`` badges say where an item sits in a workflow, and ``branding`` badges
carry a logo inlined as a ``data:`` URI.

The whole catalogue is active out of the box. Narrow it with ``catalogue``, add
or recolour entries with ``badges``, and opt into a task-list shorthand with
``shorthand``. A badge value is written into the badge's ``style`` attribute as
its ``background-color``, so it may carry further CSS declarations after a
``;``. The text colour is derived from the leading colour.

A keyword is left literal when escaped (``\\!high``) or written inside a code
span, because the inline processor is registered below Python-Markdown's own
``escape`` and ``backtick`` patterns.
"""

from collections.abc import Mapping
from typing import Any

from markdown import Extension, Markdown

from markdown_badges.catalogue import CATALOGUE, Badge, BadgeType, catalogue_for
from markdown_badges.parsing import (
    INLINE_PRIORITY,
    TREE_PRIORITY,
    BadgeInlineProcessor,
    ShorthandTreeprocessor,
    badges_in,
    inline_re,
    priority_of,
    rank_of,
)

__all__ = [
    "CATALOGUE",
    "Badge",
    "BadgeType",
    "MarkdownBadgesExtension",
    "badges_in",
    "catalogue_for",
    "makeExtension",
    "priority_of",
    "rank_of",
    "resolve_badges",
]

_TYPE_NAMES = ", ".join(t.value for t in BadgeType)


def _badge_type(name: str, where: str) -> BadgeType:
    """The BadgeType called `name`, or a ValueError naming the valid ones."""
    try:
        return BadgeType(name)
    except ValueError:
        raise ValueError(
            f"markdown-badges: {where} names an unknown badge type {name!r}; "
            f"valid types are {_TYPE_NAMES}"
        ) from None


def _check_value(name: str, value: Any) -> str:
    """The badge value as a string, or a ValueError. Content is not restricted:
    a value may extend the badge's declaration list past the first `;`."""
    if not isinstance(value, str):
        raise ValueError(
            f"markdown-badges: badge {name!r} has a non-string value {value!r}; "
            "give it a CSS colour string instead, for example '#7b1fa2'"
        )
    if not value.strip():
        raise ValueError(
            f"markdown-badges: badge {name!r} has an empty value; "
            "give it a CSS colour string instead, for example '#7b1fa2'"
        )
    return value


def resolve_badges(
    catalogue_scope: list[str], user_badges: Mapping[str, Mapping[str, Any]]
) -> dict[str, Badge]:
    """The active badge map: the scoped catalogue with `user_badges` merged over.

    A user name that already exists is replaced in place, keeping its position
    and its catalogue type. A new name is inserted after the last badge of the
    same type, so a new priority outranks every catalogue priority."""
    scoped = [_badge_type(n, "catalogue") for n in catalogue_scope]
    ordered: list[Badge] = list(catalogue_for(*scoped).values()) if scoped else []

    for type_name, entries in user_badges.items():
        badge_type = _badge_type(type_name, "badges")
        if not isinstance(entries, Mapping):
            raise ValueError(
                f"markdown-badges: badges[{type_name!r}] is {entries!r}, not a table; "
                "it must map badge name to value, for example {'blocker': '#7b1fa2'}"
            )
        for name, raw in entries.items():
            value = _check_value(name, raw)
            position = next((i for i, b in enumerate(ordered) if b.name == name), None)
            if position is not None:
                kept = ordered[position]
                ordered[position] = Badge(name, value, kept.type, kept.note)
                continue
            last = max((i for i, b in enumerate(ordered) if b.type is badge_type), default=None)
            new = Badge(name, value, badge_type)
            if last is None:
                ordered.append(new)
            else:
                ordered.insert(last + 1, new)

    return {b.name: b for b in ordered}


class MarkdownBadgesExtension(Extension):
    """Registers the inline `!<name>` keyword and the optional shorthand."""

    def __init__(self, **kwargs: Any) -> None:
        self.config = {
            "catalogue": [
                [t.value for t in BadgeType],
                "Badge types to load from the shipped catalogue; [] disables it",
            ],
            "badges": [{}, "Extra or recoloured badges, keyed by badge type"],
            "shorthand": [{}, "Task-list marker -> badge name"],
        }
        if "levels" in kwargs:
            raise ValueError(
                "markdown-badges: the 'levels' option was removed in 1.0. Declare priority "
                "badges under badges.priority instead, for example "
                "badges={'priority': {'blocker': '#7b1fa2'}}. See MIGRATING.md."
            )
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown) -> None:
        badges = resolve_badges(
            list(self.getConfig("catalogue", [])), dict(self.getConfig("badges", {}) or {})
        )
        shorthand: dict[str, Badge] = {}
        for marker, name in (self.getConfig("shorthand", {}) or {}).items():
            if name not in badges:
                raise ValueError(
                    f"markdown-badges: shorthand {marker!r} points at badge {name!r}, "
                    "which is not in scope; add it under badges, or widen catalogue"
                )
            shorthand[marker] = badges[name]

        if shorthand:
            md.treeprocessors.register(
                ShorthandTreeprocessor(md, shorthand), "badges-shorthand", TREE_PRIORITY
            )
        if badges:
            md.inlinePatterns.register(
                BadgeInlineProcessor(inline_re(list(badges)), md, badges),
                "badges-inline",
                INLINE_PRIORITY,
            )


def makeExtension(**kwargs: Any) -> MarkdownBadgesExtension:
    return MarkdownBadgesExtension(**kwargs)
