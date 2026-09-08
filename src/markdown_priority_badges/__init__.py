"""Priority badges for Markdown, two ways.

- **Task lists (shorthand):** a leading ``!`` / ``!!`` right after the
  checkbox renders a HIGH / CRITICAL badge. A Treeprocessor runs just before
  ``pymdownx.tasklist`` (priority 26 > 25), so it sees pristine ``[ ] !!
  text`` list-item text; it strips the marker and prepends a stashed raw-HTML
  badge span, leaving the ``[ ]`` checkbox intact for tasklist.
- **Anywhere (inline keyword):** ``!low`` / ``!medium`` / ``!high`` /
  ``!critical`` (and any custom level) in ordinary prose, headings, table
  cells, etc. render the same badge inline. An InlineProcessor matches only
  the configured level keywords, so ordinary ``!`` in text is untouched.

Levels are a name->color map, configurable via the ``levels`` option (merged
over the built-ins). The badge carries its own inline styles, so the extension
is self-contained: no external stylesheet is needed. Badge text color (black
or white) is chosen automatically for legibility against each background.

A level value is written into the badge's ``style`` attribute as its
``background-color``, so it may carry further CSS declarations after a ``;``
to give one level an icon, a gradient, or a shadow. The contrast calculation
reads the leading color, before the first ``;``.

A keyword is left literal when it is escaped (``\\!high``) or written inside a
code span, because the inline processor is registered below Python-Markdown's
own ``escape`` and ``backtick`` patterns.
"""

import re
import xml.etree.ElementTree as etree
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from markdown import Extension, Markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor

__all__ = [
    "DEFAULT_LEVELS",
    "INLINE_PRIORITY",
    "LEVELS",
    "MARKER_RE",
    "TREE_PRIORITY",
    "PriorityBadgesExtension",
    "PriorityInlineProcessor",
    "TasklistShorthandTreeprocessor",
    "level_rank",
    "makeExtension",
    "priority_of",
]

# Built-in level -> badge background color. Config `levels` merges over this.
DEFAULT_LEVELS = {
    "low": "#2e7d32",  # green
    "medium": "#f9a825",  # amber
    "high": "#ef6c00",  # orange
    "critical": "#d32f2f",  # red
}

# Built-in level names in ascending severity order (keys of DEFAULT_LEVELS).
LEVELS: tuple[str, ...] = tuple(DEFAULT_LEVELS)

# Leading task-list shorthand without the checkbox prefix: a run of `!` at the
# very start of an item's text, followed by whitespace. `priority_of` works on
# item content (the checkbox is already stripped by the caller).
_LEADING_BANGS_RE = re.compile(r"^(!+)\s")

# Task-list shorthand: checkbox prefix, a leading run of `!`, then required
# whitespace. The checkbox part mirrors pymdownx.tasklist's own pattern so the
# same items match. One `!` maps to "high", two or more to "critical".
MARKER_RE = re.compile(r"^(?P<checkbox> *\[(?:x|X| )\] +)(?P<bangs>!+)\s+(?P<rest>.*)", re.DOTALL)

# Treeprocessor priority: above pymdownx.tasklist (25), so the shorthand is
# read from pristine `[ ] !! text` before tasklist turns it into a checkbox.
TREE_PRIORITY = 26

# Inline-pattern priority: below Python-Markdown's `escape` (180), so a
# backslash-escaped `\!high` stays literal, and below `backtick` (190), so a
# keyword inside a code span survives verbatim.
INLINE_PRIORITY = 175

# Shared pill geometry; per-badge background and (auto) text color are appended.
_BADGE_STYLE = (
    "display:inline-block;padding:0.05em 0.45em;margin-right:0.15em;"
    "border-radius:0.35em;font-size:0.62em;font-weight:700;line-height:1.5;"
    "letter-spacing:0.04em;text-transform:uppercase;vertical-align:middle;"
    "-webkit-user-select:none;user-select:none;"
)


# Common CSS named colors, so `levels` can use a name as well as hex and still
# get an auto-contrasted text color. Anything not resolvable to a hex triple
# (other named colors, rgb()/hsl(), etc.) falls back to white text.
_NAMED_COLORS = {
    "black": "#000000",
    "white": "#ffffff",
    "gray": "#808080",
    "grey": "#808080",
    "silver": "#c0c0c0",
    "red": "#ff0000",
    "maroon": "#800000",
    "orange": "#ffa500",
    "yellow": "#ffff00",
    "olive": "#808000",
    "lime": "#00ff00",
    "green": "#008000",
    "teal": "#008080",
    "aqua": "#00ffff",
    "cyan": "#00ffff",
    "blue": "#0000ff",
    "navy": "#000080",
    "purple": "#800080",
    "fuchsia": "#ff00ff",
    "magenta": "#ff00ff",
    "rebeccapurple": "#663399",
}


def _to_hex6(color: str) -> str | None:
    """Normalize a CSS color to six hex digits, or None if it cannot be
    resolved. Accepts 3-/4-/6-/8-digit hex (any alpha channel is dropped) and
    the common named colors above. A value carrying extra CSS declarations is
    read up to the first `;`, which is its `background-color`."""
    c = color.split(";", 1)[0].strip().lower()
    c = _NAMED_COLORS.get(c, c)
    if not c.startswith("#"):
        return None
    h = c[1:]
    if not h or not all(ch in "0123456789abcdef" for ch in h):
        return None
    if len(h) in (3, 4):
        h = "".join(ch * 2 for ch in h)
    if len(h) in (6, 8):
        return h[:6]
    return None


def _text_color(bg: str) -> str:
    """Black or white, whichever has the higher WCAG contrast against `bg`.
    `bg` may be 3-/4-/6-/8-digit hex, a common named color, or any of those
    followed by extra CSS declarations; anything else falls back to white."""
    hex6 = _to_hex6(bg)
    if hex6 is None:
        return "#fff"
    r, g, b = (int(hex6[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    contrast_black = (lum + 0.05) / 0.05
    contrast_white = 1.05 / (lum + 0.05)
    return "#000" if contrast_black >= contrast_white else "#fff"


def _shorthand_level(bangs: str) -> str:
    """One bang is 'high'; two or more collapse to 'critical'."""
    return "high" if len(bangs) == 1 else "critical"


def level_rank(level: str, levels: Iterable[str] = LEVELS) -> int:
    """Severity rank of `level` within `levels` (higher = more severe), or -1.

    `levels` is any iterable of level names in ascending severity order. A
    name->color mapping (such as the extension's `levels` option) works too:
    its keys are read, in insertion order."""
    names = tuple(levels)
    return names.index(level) if level in names else -1


def priority_of(text: str, levels: Iterable[str] = LEVELS) -> str | None:
    """Highest-ranked priority level found in `text`, or None.

    Considers a leading `!` / `!!` shorthand (high / critical) and every inline
    `!<name>` keyword for `name` in `levels`. Returns the level with the greatest
    `level_rank`. `levels` accepts the same values as `level_rank`.

    `text` is raw item content, with any checkbox prefix stripped. This is a
    plain-text scan, not a Markdown parse: unlike the rendered badge, a keyword
    inside a code span or escaped as `\\!high` still counts."""
    names = tuple(levels)
    found: list[str] = []
    if (m := _LEADING_BANGS_RE.match(text)) is not None:
        shorthand = _shorthand_level(m.group(1))
        if shorthand in names:
            found.append(shorthand)
    found += re.findall(_inline_re(names), text)
    if not found:
        return None
    return max(found, key=lambda name: level_rank(name, names))


def _badge_element(level: str, color: str) -> etree.Element:
    """A styled inline badge <span> for `level` on background `color`.

    `color` joins the declaration list verbatim, so a value such as
    `#b71c1c;background-image:url(...)` adds declarations to the badge."""
    el = etree.Element("span")
    el.set("class", f"task-prio task-prio--{level}")
    el.set("style", f"{_BADGE_STYLE}background-color:{color};color:{_text_color(color)};")
    el.text = level
    return el


def _badge_html(level: str, color: str) -> str:
    """The badge as an HTML string with a trailing space (used by the task-list
    treeprocessor via the HTML stash)."""
    return etree.tostring(_badge_element(level, color), encoding="unicode") + " "


class TasklistShorthandTreeprocessor(Treeprocessor):
    """Rewrite task-list items flagged with a leading `!` run into a badge."""

    def __init__(self, md: Markdown, levels: dict[str, str]) -> None:
        super().__init__(md)
        self.levels = levels

    def _rewrite(self, holder: etree.Element) -> bool:
        m = MARKER_RE.match(holder.text or "")
        if m is None:
            return False
        level = _shorthand_level(m.group("bangs"))
        badge = self.md.htmlStash.store(_badge_html(level, self.levels[level]))
        holder.text = m.group("checkbox") + badge + m.group("rest")
        return True

    def run(self, root: etree.Element) -> None:
        for li in root.iter("li"):
            if self._rewrite(li):
                continue
            # Loose lists wrap the checkbox text in a child <p>.
            if len(li):
                first = next(iter(li))
                if first.tag == "p":
                    self._rewrite(first)


class PriorityInlineProcessor(InlineProcessor):
    """Render an inline `!<level>` keyword as a badge span."""

    def __init__(self, pattern: str, md: Markdown, levels: dict[str, str]) -> None:
        super().__init__(pattern, md)
        self.levels = levels

    # The stub types `handleMatch` on the legacy one-argument `Pattern` base,
    # so the correct two-argument InlineProcessor signature needs the ignore.
    def handleMatch(  # type: ignore[override]
        self, m: re.Match[str], data: str
    ) -> tuple[etree.Element, int, int]:
        level = m.group(1)
        return _badge_element(level, self.levels[level]), m.start(0), m.end(0)


def _inline_re(names: Sequence[str]) -> str:
    """`!<name>` inline-keyword regex for the configured level names: not
    preceded by a word char or another `!`, ending on a word boundary. Longer
    names are tried first so no name shadows a longer one."""
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return rf"(?<![\w!])!({alts})\b"


def _validate_levels(levels: Mapping[str, Any]) -> None:
    """Raise ValueError for a level value that cannot produce CSS at all.

    Values come from site config (TOML / YAML), so their type is checked. What
    they contain is deliberately not restricted: a value may extend the badge's
    declaration list past the first `;` (see `_badge_element`). The config is
    the site owner's own file, trusted the same way an `extra_css` entry is."""
    for name, color in levels.items():
        if not isinstance(color, str):
            raise ValueError(f"priority-badges: level {name!r} has a non-string color {color!r}")
        if not color.strip():
            raise ValueError(f"priority-badges: level {name!r} has an empty color")


class PriorityBadgesExtension(Extension):
    """Registers the task-list shorthand and the inline `!<level>` keyword."""

    def __init__(self, **kwargs: Any) -> None:
        self.config = {
            "levels": [{}, "Level->color map, merged over the built-in defaults"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown) -> None:
        configured: Mapping[str, Any] = self.getConfig("levels", {}) or {}
        _validate_levels(configured)
        levels: dict[str, str] = {**DEFAULT_LEVELS, **configured}
        md.treeprocessors.register(
            TasklistShorthandTreeprocessor(md, levels), "priority-badge-tasklist", TREE_PRIORITY
        )
        md.inlinePatterns.register(
            PriorityInlineProcessor(_inline_re(tuple(levels)), md, levels),
            "priority-badge-inline",
            INLINE_PRIORITY,
        )


def makeExtension(**kwargs: Any) -> PriorityBadgesExtension:
    return PriorityBadgesExtension(**kwargs)
