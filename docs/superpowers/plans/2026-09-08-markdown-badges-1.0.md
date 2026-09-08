# markdown-badges 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `markdown-priority-badges` into `markdown-badges` 1.0: a badge system with a catalogue shipped in the package, badges keyed by type, ranking limited to priority badges, and a config-driven task-list shorthand.

**Architecture:** One 300-line `__init__.py` becomes four focused modules. `catalogue.py` holds all badge data and no Markdown imports. `styling.py` holds colour maths and span building. `parsing.py` holds the inline pattern, the shorthand treeprocessor, and the text-scanning API. `__init__.py` holds only the extension, config resolution, and re-exports.

**Tech Stack:** Python 3.10+, Python-Markdown 3.5+, `pymdownx.tasklist` (dev only), uv, pytest, ruff, mypy strict.

**Spec:** `docs/superpowers/specs/2026-09-08-badges-1.0-design.md`

## Global Constraints

- Package renames to `markdown-badges` (PyPI) / `markdown_badges` (import) / `markdown_badges` (config key). Version becomes `1.0.0`.
- `requires-python = ">=3.10"`. Use `X | None`, not `Optional[X]`.
- Every public function and method is fully type annotated. `mypy --strict` over `src` must pass.
- `ruff check .` and `ruff format --check .` must pass. Line length 100. Lint set `E`, `F`, `I`, `UP`, `B`.
- Use f-strings only. Prefer `dataclass` and `Enum` over dict literals for structured data.
- A badge value is never parsed or filtered beyond its type. Extended CSS after a `;` must keep working.
- The inline processor stays at priority 175 (below Python-Markdown `escape` at 180). The shorthand treeprocessor stays at 26 (above `pymdownx.tasklist` at 25).
- Every invalid config raises `ValueError` at extension load, naming the offending key and the fix.
- Commit after every task. Commit subject lines are lowercase, one line, no AI attribution.
- After the rename, the README status badges must point at the new PyPI project: `img.shields.io/pypi/v/markdown-badges` and `img.shields.io/pypi/pyversions/markdown-badges`. Leaving them on the old name silently shows a frozen 0.2.0.

---

### Task 1: Rename the package to `markdown_badges`

Mechanical move first, so every later task lands in the final location. No behaviour change.

**Files:**
- Create: `src/markdown_badges/__init__.py` (moved from `src/markdown_priority_badges/__init__.py`)
- Create: `src/markdown_badges/py.typed` (moved)
- Delete: `src/markdown_priority_badges/`
- Modify: `pyproject.toml`
- Modify: `tests/test_parsing.py`, `tests/test_priority_badges.py`, `scripts/gen_badges.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the importable module path `markdown_badges` with the 0.2.0-plus-`review-fixes` API unchanged (`PriorityBadgesExtension`, `priority_of`, `level_rank`, `LEVELS`, `DEFAULT_LEVELS`, `_text_color`, `_to_hex6`, `_badge_element`, `_BADGE_STYLE`, `MARKER_RE`).

- [ ] **Step 1: Move the package directory**

```bash
git mv src/markdown_priority_badges src/markdown_badges
```

- [ ] **Step 2: Update every import in tests and scripts**

```bash
grep -rl markdown_priority_badges tests scripts | xargs sed -i 's/markdown_priority_badges/markdown_badges/g'
```

- [ ] **Step 3: Update `pyproject.toml`**

Set the project name, version, and wheel package path:

```toml
[project]
name = "markdown-badges"
version = "1.0.0"

[tool.hatch.build.targets.wheel]
packages = ["src/markdown_badges"]
```

- [ ] **Step 4: Re-sync and run the suite to verify nothing broke**

Run: `uv sync --dev && uv run pytest -q`
Expected: PASS, 46 passed.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "rename the package to markdown_badges and bump to 1.0.0"
```

---

### Task 2: `catalogue.py` with the typed badge model

**Files:**
- Create: `src/markdown_badges/catalogue.py`
- Create: `tests/test_catalogue.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BadgeType` (Enum with `PRIORITY`/`STATUS`/`BRANDING`, values `"priority"`/`"status"`/`"branding"`), `Badge` (frozen dataclass: `name: str`, `value: str`, `type: BadgeType`, `note: str = ""`), `ICONS: dict[str, str]`, `claude_burst(rays: int = 11, r_out: float = 11.0, r_in: float = 1.0) -> str`, `CATALOGUE: tuple[Badge, ...]`, `catalogue_for(*types: BadgeType) -> dict[str, Badge]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_catalogue.py`:

```python
"""Tests for the shipped badge catalogue."""

from markdown_badges.catalogue import CATALOGUE, Badge, BadgeType, catalogue_for


def test_every_catalogue_name_is_unique():
    names = [b.name for b in CATALOGUE]
    assert len(names) == len(set(names))


def test_catalogue_covers_all_three_types():
    assert {b.type for b in CATALOGUE} == set(BadgeType)


def test_priority_badges_are_in_ascending_severity_order():
    priority = [b.name for b in CATALOGUE if b.type is BadgeType.PRIORITY]
    assert priority == ["trivial", "low", "medium", "high", "critical", "blocker"]


def test_catalogue_for_with_no_arguments_returns_everything():
    assert len(catalogue_for()) == len(CATALOGUE)


def test_catalogue_for_filters_by_type():
    only_branding = catalogue_for(BadgeType.BRANDING)
    assert set(only_branding) == {"gitlab", "github", "claude"}
    assert all(b.type is BadgeType.BRANDING for b in only_branding.values())


def test_catalogue_for_accepts_several_types():
    subset = catalogue_for(BadgeType.PRIORITY, BadgeType.STATUS)
    assert "high" in subset
    assert "wip" in subset
    assert "github" not in subset


def test_catalogue_for_preserves_catalogue_order():
    order = [b.name for b in CATALOGUE if b.type is BadgeType.PRIORITY]
    assert list(catalogue_for(BadgeType.PRIORITY)) == order


def test_badge_is_frozen():
    badge = Badge("x", "#000", BadgeType.STATUS)
    try:
        badge.name = "y"  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("Badge must be immutable")


def test_branding_badges_inline_their_icon():
    for name in ("gitlab", "github", "claude"):
        value = catalogue_for(BadgeType.BRANDING)[name].value
        assert "background-image:url('data:image/svg+xml," in value
        assert "http" not in value.split("background-image")[0]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'markdown_badges.catalogue'`

- [ ] **Step 3: Write `src/markdown_badges/catalogue.py`**

Move `claude_burst`, `ICONS`, and the badge data out of `scripts/gen_badges.py` into the package. Note the priority order changes from the script: `trivial` moves to the front so the tuple is in ascending severity order.

```python
"""The badge catalogue: the data every install gets without any config.

To add a badge, append a `Badge` to `CATALOGUE`. A branding badge needs its
logo as a single-path SVG in `ICONS`; pick a base colour and an icon fill that
agree, because the badge text colour is derived from the base.
"""

import math
import urllib.parse
from dataclasses import dataclass
from enum import Enum

__all__ = ["CATALOGUE", "Badge", "BadgeType", "catalogue_for", "claude_burst"]


class BadgeType(Enum):
    """What a badge means. Only PRIORITY badges carry a severity rank."""

    PRIORITY = "priority"
    STATUS = "status"
    BRANDING = "branding"


@dataclass(frozen=True)
class Badge:
    """One badge: a keyword, the CSS it renders with, and what it means."""

    name: str
    value: str
    type: BadgeType
    note: str = ""


def claude_burst(rays: int = 11, r_out: float = 11.0, r_in: float = 1.0) -> str:
    """The Claude starburst: `rays` tapered spokes around a common center."""
    w_out, w_in, cx, cy = 1.15, 2.05, 12.0, 12.0
    parts: list[str] = []
    for i in range(rays):
        angle = 2 * math.pi * i / rays - math.pi / 2
        ca, sa = math.cos(angle), math.sin(angle)
        px, py = -sa, ca
        corners = [
            (cx + ca * r_in + px * w_in / 2, cy + sa * r_in + py * w_in / 2),
            (cx + ca * r_out + px * w_out / 2, cy + sa * r_out + py * w_out / 2),
            (cx + ca * r_out - px * w_out / 2, cy + sa * r_out - py * w_out / 2),
            (cx + ca * r_in - px * w_in / 2, cy + sa * r_in - py * w_in / 2),
        ]
        parts.append("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in corners) + "Z")
    return "".join(parts)


# Single-path logo marks on a 24x24 viewBox. Copy the existing values verbatim
# from scripts/gen_badges.py on this branch: ICONS["gitlab"] and ICONS["github"].
ICONS: dict[str, str] = {
    "gitlab": (
        "M23.955 13.587l-1.342-4.135-2.664-8.189a.455.455 0 00-.867 0L16.418 9.45H7.582"
        "L4.919 1.263a.455.455 0 00-.867 0L1.386 9.45.044 13.587a.924.924 0 00.331 1.03"
        "L12 23.054l11.625-8.436a.92.92 0 00.33-1.031"
    ),
    "github": (
        "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82"
        "-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633"
        " 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236"
        " 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332"
        "-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322"
        " 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23"
        " 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805"
        " 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69"
        ".825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
    ),
    "claude": claude_burst(),
}

# Shared geometry for an icon badge: the mark sits left of the text.
_ICON_LAYOUT = (
    "background-repeat:no-repeat;background-position:0.45em center;"
    "background-size:0.8em;padding-left:1.75em"
)


def _icon_value(color: str, icon: str, fill: str = "#fff") -> str:
    """A badge value whose background carries `icon` as an inline data: URI."""
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
        f"fill='{fill}'><path d='{ICONS[icon]}'/></svg>"
    )
    uri = "data:image/svg+xml," + urllib.parse.quote(svg, safe="")
    return f"{color};background-image:url('{uri}');{_ICON_LAYOUT}"


CATALOGUE: tuple[Badge, ...] = (
    # Priority, in ascending severity order. Rank is position in this run.
    Badge("trivial", "#78909c", BadgeType.PRIORITY, "Nice to have."),
    Badge("low", "#2e7d32", BadgeType.PRIORITY, "Green."),
    Badge("medium", "#f9a825", BadgeType.PRIORITY, "Amber."),
    Badge("high", "#ef6c00", BadgeType.PRIORITY, "Orange."),
    Badge("critical", "#d32f2f", BadgeType.PRIORITY, "Red."),
    Badge("blocker", "#7b1fa2", BadgeType.PRIORITY, "Work that cannot start."),
    # Status: where an item sits in a workflow.
    Badge("todo", "#1565c0", BadgeType.STATUS, "Not started."),
    Badge("wip", "#0277bd", BadgeType.STATUS, "In progress."),
    Badge("review", "#6a1b9a", BadgeType.STATUS, "Waiting on a reviewer."),
    Badge("blocked", "#b71c1c", BadgeType.STATUS, "Waiting on someone else."),
    Badge("approved", "#2e7d32", BadgeType.STATUS, "Signed off, not yet shipped."),
    Badge("done", "#37474f", BadgeType.STATUS, "Finished."),
    Badge("onhold", "#8d6e63", BadgeType.STATUS, "Paused on purpose."),
    Badge("experimental", "#00838f", BadgeType.STATUS, "Not stable yet."),
    Badge("deprecated", "#5d4037", BadgeType.STATUS, "On the way out."),
    # Branding: a logo inlined as a data: URI, so no network request.
    Badge("gitlab", _icon_value("#7759c2", "gitlab"), BadgeType.BRANDING, "GitLab purple."),
    Badge("github", _icon_value("#181717", "github"), BadgeType.BRANDING, "GitHub near-black."),
    Badge(
        "claude",
        _icon_value("#d97757", "claude", fill="#1f1e1d"),
        BadgeType.BRANDING,
        "Claude coral, dark mark.",
    ),
)


def catalogue_for(*types: BadgeType) -> dict[str, Badge]:
    """The catalogue, filtered to `types`, in catalogue order.

    No arguments means every type."""
    wanted = set(types) if types else set(BadgeType)
    return {b.name: b for b in CATALOGUE if b.type in wanted}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: PASS, 9 passed.

- [ ] **Step 5: Commit**

```bash
git add src/markdown_badges/catalogue.py tests/test_catalogue.py
git commit -m "add the typed badge catalogue to the package"
```

---

### Task 3: Extract `styling.py`

Pure move of the colour maths and span construction. Behaviour must not change.

**Files:**
- Create: `src/markdown_badges/styling.py`
- Create: `tests/test_styling.py`
- Modify: `src/markdown_badges/__init__.py` (delete the moved names, import them instead)

**Interfaces:**
- Consumes: nothing.
- Produces: `BADGE_STYLE: str`, `text_color(bg: str) -> str`, `to_hex6(color: str) -> str | None`, `badge_element(badge: Badge) -> etree.Element`, `badge_html(badge: Badge) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_styling.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_styling.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'markdown_badges.styling'`

- [ ] **Step 3: Write `src/markdown_badges/styling.py`**

Move `_NAMED_COLORS`, `_to_hex6`, `_text_color`, `_BADGE_STYLE`, `_badge_element`, `_badge_html` from `__init__.py`, dropping the leading underscore on the four names other modules use, and change the CSS class prefix from `task-prio` to `badge`.

```python
"""Badge appearance: colour resolution and the rendered <span>."""

import xml.etree.ElementTree as etree

from markdown_badges.catalogue import Badge

__all__ = ["BADGE_STYLE", "badge_element", "badge_html", "text_color", "to_hex6"]

# Shared pill geometry. The per-badge value and text colour are appended.
BADGE_STYLE = (
    "display:inline-block;padding:0.05em 0.45em;margin-right:0.15em;"
    "border-radius:0.35em;font-size:0.62em;font-weight:700;line-height:1.5;"
    "letter-spacing:0.04em;text-transform:uppercase;vertical-align:middle;"
    "-webkit-user-select:none;user-select:none;"
)

# Common CSS named colours, so a badge value can use a name and still get an
# auto-contrasted text colour. Anything unresolvable falls back to white text.
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


def to_hex6(color: str) -> str | None:
    """Normalize a CSS colour to six hex digits, or None if unresolvable.

    Accepts 3-/4-/6-/8-digit hex (any alpha channel is dropped) and the common
    named colours. A value carrying extra CSS declarations is read up to the
    first `;`, which is its `background-color`."""
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


def text_color(bg: str) -> str:
    """Black or white, whichever has the higher WCAG contrast against `bg`."""
    hex6 = to_hex6(bg)
    if hex6 is None:
        return "#fff"
    r, g, b = (int(hex6[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    contrast_black = (lum + 0.05) / 0.05
    contrast_white = 1.05 / (lum + 0.05)
    return "#000" if contrast_black >= contrast_white else "#fff"


def badge_element(badge: Badge) -> etree.Element:
    """The badge as an inline <span>.

    `badge.value` joins the declaration list verbatim, so a value such as
    `#b71c1c;background-image:url(...)` adds declarations to the badge."""
    el = etree.Element("span")
    el.set("class", f"badge badge--{badge.name}")
    el.set("style", f"{BADGE_STYLE}background-color:{badge.value};color:{text_color(badge.value)};")
    el.text = badge.name
    return el


def badge_html(badge: Badge) -> str:
    """The badge as an HTML string with a trailing space, for the HTML stash."""
    return etree.tostring(badge_element(badge), encoding="unicode") + " "
```

- [ ] **Step 4: Delete the moved names from `__init__.py`**

Remove `_NAMED_COLORS`, `_to_hex6`, `_text_color`, `_BADGE_STYLE`, `_badge_element`, `_badge_html` from `src/markdown_badges/__init__.py` and add near the top:

```python
from markdown_badges.styling import BADGE_STYLE, badge_element, badge_html, text_color, to_hex6
```

Then replace each old call site in that file: `_badge_html(level, levels[level])` becomes `badge_html(...)`, and so on. The file will not fully work until Task 6 rewrites it; the goal here is only that the module imports and `tests/test_styling.py` and `tests/test_catalogue.py` pass.

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `uv run pytest tests/test_styling.py tests/test_catalogue.py -q`
Expected: PASS, 19 passed.

- [ ] **Step 6: Commit**

```bash
git add src/markdown_badges/styling.py tests/test_styling.py src/markdown_badges/__init__.py
git commit -m "extract badge styling into its own module"
```

---

### Task 4: `parsing.py` inline pattern and the text-scanning API

**Files:**
- Create: `src/markdown_badges/parsing.py`
- Create: `tests/test_scanning.py`

**Interfaces:**
- Consumes: `Badge`, `BadgeType`, `catalogue_for` from `markdown_badges.catalogue`; `badge_element` from `markdown_badges.styling`.
- Produces: `INLINE_PRIORITY: int = 175`, `inline_re(names: Sequence[str]) -> str`, `BadgeInlineProcessor(pattern: str, md: Markdown, badges: Mapping[str, Badge])`, `rank_of(name: str, badges: Mapping[str, Badge] | None = None) -> int`, `priority_of(text: str, badges: Mapping[str, Badge] | None = None) -> str | None`, `badges_in(text: str, badges: Mapping[str, Badge] | None = None) -> list[Badge]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scanning.py`:

```python
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
    # `blocked` (status) and `blocker` (priority) share a prefix.
    assert [b.name for b in badges_in("!blocked !blocker")] == ["blocked", "blocker"]


def test_scanning_is_a_raw_scan_not_a_markdown_parse():
    assert priority_of("use `!critical` verbatim") == "critical"
    assert priority_of(r"escaped \!high") == "high"


def test_catalogue_subset_limits_what_is_found():
    only_priority = catalogue_for(BadgeType.PRIORITY)
    assert badges_in("!high and !github", only_priority) == [only_priority["high"]]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_scanning.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'markdown_badges.parsing'`

- [ ] **Step 3: Write the inline half of `src/markdown_badges/parsing.py`**

The shorthand treeprocessor is added in Task 5; this step creates the file with everything else.

```python
"""Finding badge keywords in text, and rendering them inline."""

import re
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
```

Add `import xml.etree.ElementTree as etree` to the imports at the top of the file.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_scanning.py -q`
Expected: PASS, 14 passed.

- [ ] **Step 5: Commit**

```bash
git add src/markdown_badges/parsing.py tests/test_scanning.py
git commit -m "add the badge scanning API with type-aware ranking"
```

---

### Task 5: Config-driven shorthand treeprocessor

**Files:**
- Modify: `src/markdown_badges/parsing.py`
- Create: `tests/test_shorthand.py`

**Interfaces:**
- Consumes: `Badge` from `markdown_badges.catalogue`; `badge_html` from `markdown_badges.styling`.
- Produces: `TREE_PRIORITY: int = 26`, `shorthand_re(markers: Sequence[str]) -> re.Pattern[str]`, `ShorthandTreeprocessor(md: Markdown, markers: Mapping[str, Badge])`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_shorthand.py`:

```python
"""Tests for the configurable task-list shorthand."""

import markdown

from markdown_badges import MarkdownBadgesExtension


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(
        text, extensions=["pymdownx.tasklist", MarkdownBadgesExtension(**cfg)]
    )


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_shorthand.py -q`
Expected: FAIL with `ImportError: cannot import name 'MarkdownBadgesExtension'`

- [ ] **Step 3: Add the treeprocessor to `src/markdown_badges/parsing.py`**

Append to the module, and add `"TREE_PRIORITY"`, `"ShorthandTreeprocessor"`, `"shorthand_re"` to `__all__`. Add `from markdown.treeprocessors import Treeprocessor` and `from markdown_badges.styling import badge_html` to the imports.

```python
# Above pymdownx.tasklist (25), so the marker is read from pristine
# `[ ] <marker> text` before tasklist turns it into a checkbox.
TREE_PRIORITY = 26


def shorthand_re(markers: Sequence[str]) -> re.Pattern[str]:
    """Checkbox prefix, one configured marker, then required whitespace.

    Markers are matched longest-first, so `!!` wins over `!`."""
    alts = "|".join(re.escape(m) for m in sorted(markers, key=len, reverse=True))
    return re.compile(
        rf"^(?P<checkbox> *\[(?:x|X| )\] +)(?P<marker>{alts})\s+(?P<rest>.*)", re.DOTALL
    )


class ShorthandTreeprocessor(Treeprocessor):
    """Rewrite a task-list item whose text starts with a configured marker."""

    def __init__(self, md: Markdown, markers: Mapping[str, Badge]) -> None:
        super().__init__(md)
        self.markers = markers
        self.pattern = shorthand_re(list(markers))

    def _rewrite(self, holder: etree.Element) -> bool:
        m = self.pattern.match(holder.text or "")
        if m is None:
            return False
        badge = self.md.htmlStash.store(badge_html(self.markers[m.group("marker")]))
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
```

- [ ] **Step 4: Run the tests to verify they fail on the extension, not the treeprocessor**

Run: `uv run pytest tests/test_shorthand.py -q`
Expected: still FAIL with `ImportError: cannot import name 'MarkdownBadgesExtension'`. Task 6 supplies it. Confirm `uv run python -c "from markdown_badges.parsing import ShorthandTreeprocessor"` succeeds.

- [ ] **Step 5: Commit**

```bash
git add src/markdown_badges/parsing.py tests/test_shorthand.py
git commit -m "add the configurable shorthand treeprocessor"
```

---

### Task 6: The extension, config resolution, and validation

This is the task that makes `tests/test_shorthand.py` pass and replaces the old extension wholesale.

**Files:**
- Modify: `src/markdown_badges/__init__.py` (full rewrite)
- Create: `tests/test_extension.py`
- Delete: `tests/test_parsing.py`, `tests/test_priority_badges.py` (their coverage moves to the new files)
- Create: `tests/test_rendering.py`

**Interfaces:**
- Consumes: everything produced by Tasks 2 to 5.
- Produces: `MarkdownBadgesExtension(**kwargs)` with config keys `catalogue`, `badges`, `shorthand`; `makeExtension(**kwargs) -> MarkdownBadgesExtension`; `resolve_badges(catalogue_scope, user_badges) -> dict[str, Badge]`; and the package re-exports `Badge`, `BadgeType`, `CATALOGUE`, `catalogue_for`, `badges_in`, `priority_of`, `rank_of`.

- [ ] **Step 1: Write the failing config tests**

Create `tests/test_extension.py`:

```python
"""Tests for config resolution and validation."""

import markdown
import pytest

from markdown_badges import MarkdownBadgesExtension, resolve_badges
from markdown_badges.catalogue import BadgeType


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(
        text, extensions=["pymdownx.tasklist", MarkdownBadgesExtension(**cfg)]
    )


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_extension.py -q`
Expected: FAIL with `ImportError: cannot import name 'MarkdownBadgesExtension'`

- [ ] **Step 3: Rewrite `src/markdown_badges/__init__.py`**

```python
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
from markdown_badges.styling import BADGE_STYLE, badge_element, badge_html, text_color, to_hex6

__all__ = [
    "BADGE_STYLE",
    "CATALOGUE",
    "Badge",
    "BadgeType",
    "MarkdownBadgesExtension",
    "badge_element",
    "badge_html",
    "badges_in",
    "catalogue_for",
    "makeExtension",
    "priority_of",
    "rank_of",
    "resolve_badges",
    "text_color",
    "to_hex6",
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
        raise ValueError(f"markdown-badges: badge {name!r} has a non-string value {value!r}")
    if not value.strip():
        raise ValueError(f"markdown-badges: badge {name!r} has an empty value")
    return value


def resolve_badges(
    catalogue_scope: list[str], user_badges: Mapping[str, Mapping[str, Any]]
) -> dict[str, Badge]:
    """The active badge map: the scoped catalogue with `user_badges` merged over.

    A user name that already exists is replaced in place, keeping its position
    and type. A new name is appended to the end of its type's run."""
    scoped = [_badge_type(n, "catalogue") for n in catalogue_scope]
    resolved = catalogue_for(*scoped) if scoped else {}

    additions: dict[BadgeType, list[Badge]] = {}
    for type_name, entries in user_badges.items():
        badge_type = _badge_type(type_name, "badges")
        for name, value in entries.items():
            badge = Badge(name, _check_value(name, value), badge_type)
            if name in resolved:
                resolved[name] = Badge(name, badge.value, resolved[name].type, resolved[name].note)
            else:
                additions.setdefault(badge_type, []).append(badge)

    # Append new names after the last catalogue badge of the same type, so a
    # new priority ranks above every catalogue priority.
    for badge_type, new in additions.items():
        tail = [b for b in resolved.values() if b.type is badge_type]
        rest = [b for b in resolved.values() if b.type is not badge_type]
        ordered = tail + new + rest if tail else list(resolved.values()) + new
        resolved = {b.name: b for b in ordered}
    return resolved


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
```

- [ ] **Step 4: Port the rendering tests**

Delete `tests/test_parsing.py` and `tests/test_priority_badges.py`, then create `tests/test_rendering.py` carrying forward the coverage that is still relevant:

```python
"""Rendering tests for the badge extension."""

import markdown

from markdown_badges import MarkdownBadgesExtension


def render(text: str, **cfg: object) -> str:
    return markdown.markdown(
        text, extensions=["pymdownx.tasklist", MarkdownBadgesExtension(**cfg)]
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
    html = render("Watch out! Also !important and !nosuch are not badges.")
    assert "badge" not in html


def test_word_boundaries_are_respected():
    assert "badge" not in render("foo!high and !highest priority")


def test_keyword_in_a_code_span_survives():
    html = render("Use `!critical` verbatim in code.")
    assert "badge" not in html
    assert "!critical" in html


def test_keyword_in_a_code_block_survives():
    html = render("```\n!critical not a badge\n```\n")
    assert "badge" not in html
    assert "!critical not a badge" in html


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
```

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: PASS. `tests/test_extension.py` 14, `tests/test_shorthand.py` 10, `tests/test_rendering.py` 13, `tests/test_scanning.py` 14, `tests/test_styling.py` 10, `tests/test_catalogue.py` 9.

- [ ] **Step 6: Run lint and types**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy`
Expected: all pass. Fix any finding before committing.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "replace the levels option with type-keyed badges and a catalogue scope"
```

---

### Task 7: Regenerate the catalogue docs from the package

**Files:**
- Modify: `scripts/gen_badges.py` (drop its data, import from the package)
- Modify: `docs/badges.md` (regenerated output)

**Interfaces:**
- Consumes: `CATALOGUE`, `BadgeType` from `markdown_badges.catalogue`; `text_color` from `markdown_badges.styling`.
- Produces: nothing importable. `docs/badges.md` on disk.

- [ ] **Step 1: Rewrite `scripts/gen_badges.py` as a renderer only**

```python
"""Regenerate `docs/badges.md` from the catalogue shipped in the package.

    uv run python scripts/gen_badges.py

To add a badge, edit `CATALOGUE` in `src/markdown_badges/catalogue.py`, not this
file. Refresh `docs/img/catalogue.png` by hand when the catalogue changes.
"""

import pathlib

from markdown_badges.catalogue import CATALOGUE, BadgeType
from markdown_badges.styling import text_color

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "docs" / "badges.md"


def render() -> str:
    lines: list[str] = [
        "# Badge catalogue",
        "",
        "Every badge below ships with the package and is active out of the box. Nothing "
        "here needs config. Use `catalogue` to narrow the set, and `badges` to recolour "
        "an entry or add your own.",
        "",
        "Generated from `CATALOGUE` in `src/markdown_badges/catalogue.py` by "
        "`scripts/gen_badges.py`. Edit the catalogue, not this file.",
        "",
        "![Every badge in the catalogue, rendered](img/catalogue.png)",
        "",
        "> [!NOTE]",
        "> Only `priority` badges carry a severity rank. `priority_of` and `rank_of` "
        "ignore `status` and `branding` badges entirely; use `badges_in` to get every "
        "badge on a line whatever its type.",
        "",
    ]
    for badge_type in BadgeType:
        group = [b for b in CATALOGUE if b.type is badge_type]
        lines += [f"## {badge_type.value.title()}", ""]
        lines += ["| Keyword | Value | Text | Notes |", "| --- | --- | --- | --- |"]
        for b in group:
            base = b.value.split(";", 1)[0]
            shown = base if base == b.value else f"{base} plus icon CSS"
            lines.append(f"| `!{b.name}` | `{shown}` | `{text_color(b.value)}` | {b.note} |")
        lines.append("")
    lines += [
        "## Narrowing the catalogue",
        "",
        "```toml",
        "[project.markdown_extensions.markdown_badges]",
        'catalogue = ["priority", "status"]   # drop the branding badges',
        "```",
        "",
        "## Adding your own",
        "",
        "```toml",
        "[project.markdown_extensions.markdown_badges.badges.priority]",
        'showstopper = "#000000"   # a new priority, ranked above every catalogue one',
        'critical = "#8e0000"      # an existing name: recolours it, keeping its rank',
        "```",
        "",
        "For a logo badge, add the mark as a single-path SVG to `ICONS` in "
        "`src/markdown_badges/catalogue.py` and build the value with `_icon_value`. Pick "
        "the base colour and the icon fill together: the badge text colour comes from the "
        "base, so a white mark needs a base that resolves to white text.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render())
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(CATALOGUE)} badges)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Regenerate and eyeball the output**

Run: `uv run python scripts/gen_badges.py && head -30 docs/badges.md`
Expected: `wrote docs/badges.md (18 badges)`, and three sections titled Priority, Status, Branding.

- [ ] **Step 3: Verify the generated TOML advice is accurate**

Run: `uv run python -c "
import markdown
from markdown_badges import MarkdownBadgesExtension as E
html = markdown.markdown('!showstopper !critical', extensions=[E(badges={'priority': {'showstopper': '#000000', 'critical': '#8e0000'}})])
assert 'badge--showstopper' in html and 'background-color:#8e0000' in html
print('ok')"`
Expected: `ok`

- [ ] **Step 4: Run lint**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/gen_badges.py docs/badges.md
git commit -m "generate the catalogue docs from the shipped catalogue"
```

---

### Task 8: Migration guide, README, and changelog

**Files:**
- Create: `MIGRATING.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: the final public API from Tasks 2 to 6.
- Produces: nothing importable.

- [ ] **Step 1: Write `MIGRATING.md`**

```markdown
# Migrating from markdown-priority-badges 0.2.0 to markdown-badges 1.0

## Install

Replace the dependency. The old project stays on PyPI at 0.2.0 and receives no further releases.

```bash
uv remove markdown-priority-badges && uv add markdown-badges
```

## Config

The extension key changes, `levels` becomes `badges.priority`, and the catalogue is active by default.

```toml
# before
[project.markdown_extensions.markdown_priority_badges.levels]
blocker = "#7b1fa2"

# after
[project.markdown_extensions.markdown_badges.badges.priority]
blocker = "#7b1fa2"
```

Leaving a `levels` key in place raises a `ValueError` naming this file, rather than being silently ignored.

## Restoring the `!` / `!!` shorthand

It is no longer built in. Three lines bring it back, and you can pick different markers.

```toml
[project.markdown_extensions.markdown_badges.shorthand]
"!" = "high"
"!!" = "critical"
```

## API

| 0.2.0 | 1.0 |
| --- | --- |
| `from markdown_priority_badges import ...` | `from markdown_badges import ...` |
| `LEVELS` | `catalogue_for(BadgeType.PRIORITY)` |
| `DEFAULT_LEVELS` | `CATALOGUE` |
| `level_rank(name, levels)` | `rank_of(name, badges)` |
| `priority_of(text, levels)` | `priority_of(text, badges)` |
| `PriorityBadgesExtension` | `MarkdownBadgesExtension` |
| no equivalent | `badges_in(text, badges)` for every badge type |

The second argument changes from a sequence of names to a `Mapping[str, Badge]`, which is what `catalogue_for` returns.

`priority_of` now considers only `priority` badges, and no longer looks at a leading `!` / `!!`, because that shorthand is no longer built in.

## CSS classes

The class prefix changes from `task-prio` to `badge`: `class="badge badge--high"`. Update any site CSS that targeted `.task-prio`.
```

- [ ] **Step 2: Restructure `README.md`**

Rewrite the body around the new model, in this section order: what a badge is and the `!name` syntax; the three types; the catalogue with the `docs/img/catalogue.png` image and a link to `docs/badges.md`; narrowing with `catalogue`; adding and recolouring with `badges`; extended CSS values including the logo recipe; the `shorthand` option; the scanning API (`badges_in`, `priority_of`, `rank_of`); install and enable; and a link to `MIGRATING.md`. Keep every image and `LICENSE` link absolute (`https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/...`) so they render on PyPI. Replace every `markdown_priority_badges` occurrence with `markdown_badges`.

- [ ] **Step 3: Restructure `CHANGELOG.md`**

Replace the `## Unreleased` heading with `## 1.0.0 - 2026-09-08`, keep the existing entries, and add these sections:

```markdown
### Changed

- Renamed to `markdown-badges`. Import path is `markdown_badges`, config key is `markdown_badges`, CSS class prefix is `badge` instead of `task-prio`.
- Badges are declared under `badges`, keyed by type (`priority`, `status`, `branding`), replacing the flat `levels` map.
- `priority_of` and `rank_of` consider only `priority` badges, so a status or branding badge can no longer be reported as a severity.
- The scanning API takes a `Mapping[str, Badge]` rather than a sequence of level names.

### Added

- The badge catalogue ships in the package and is active with no config. `catalogue` narrows it; `[]` disables it.
- `badges_in(text)` returns every badge on a line, of any type, in document order.
- `shorthand` maps any task-list marker to any badge, so `!` / `!!` is config a user opts into and anyone can invent their own markers.
- `BadgeType`, `Badge`, `CATALOGUE`, and `catalogue_for` are public.

### Removed

- The `levels` option. A leftover `levels` key raises a `ValueError` pointing at `MIGRATING.md`.
- The built-in `!` / `!!` task-list shorthand. Restore it with three lines of `shorthand` config.
- `LEVELS`, `DEFAULT_LEVELS`, `level_rank`, `MARKER_RE`, `PriorityBadgesExtension`, `PriorityInlineProcessor`, `TasklistShorthandTreeprocessor`.
```

- [ ] **Step 4: Verify every documented snippet actually works**

Run: `uv run python -c "
import markdown
from markdown_badges import MarkdownBadgesExtension as E
assert 'badge--critical' in markdown.markdown('- [ ] !! x', extensions=['pymdownx.tasklist', E(shorthand={'!': 'high', '!!': 'critical'})])
assert 'badge--blocker' in markdown.markdown('!blocker', extensions=[E(badges={'priority': {'blocker': '#7b1fa2'}})])
print('ok')"`
Expected: `ok`

- [ ] **Step 5: Run the full gate one last time**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q && uv build`
Expected: all pass, and the wheel builds as `markdown_badges-1.0.0-py3-none-any.whl`.

- [ ] **Step 6: Confirm the wheel ships the right files**

Run: `uv run python -c "
import zipfile, glob
names = zipfile.ZipFile(sorted(glob.glob('dist/markdown_badges-1.0.0-*.whl'))[-1]).namelist()
assert any(n.endswith('catalogue.py') for n in names), names
assert any(n.endswith('py.typed') for n in names), names
assert not any('markdown_priority_badges' in n for n in names), names
print('ok')"`
Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "document the 1.0 model and the 0.2.0 migration"
```

---

## Self-Review

**Spec coverage.** Config surface, Task 6. Package layout, Tasks 1 to 6. Data model, Task 2. Resolution, Task 6 (`resolve_badges`). Public API, Tasks 4 and 6. Shorthand, Tasks 5 and 6. Error handling and migration, Tasks 6 and 8. Docs and tooling, Tasks 7 and 8. Testing, spread across Tasks 2 to 6. Release, Tasks 1 and 8. No spec section is unimplemented.

**Placeholder scan.** No TBD, no "add error handling", no "similar to Task N". Every code step carries the code. Task 8 Step 2 describes a README restructure by section list rather than pasting the whole file, which is deliberate: the section order and the absolute-URL constraint are the requirements, and the prose is the writer's.

**Type consistency.** `Badge(name, value, type, note)` is constructed the same way in Tasks 2, 4, 5, and 6. `catalogue_for` returns `dict[str, Badge]` in Task 2 and is consumed as `Mapping[str, Badge]` in Task 4. `badge_element`/`badge_html` take a `Badge` in Task 3 and are called with one in Tasks 4 and 5. `INLINE_PRIORITY` and `TREE_PRIORITY` are defined in `parsing.py` (Tasks 4 and 5) and imported in Task 6. `resolve_badges(catalogue_scope, user_badges)` is defined and called with the same two positional arguments in Task 6.

**One gap fixed inline.** Task 3 Step 4 leaves `__init__.py` temporarily inconsistent between Tasks 3 and 6, which would break `pytest` on the old test files. The step now states that only the two new test files need to pass at that point, and Task 6 Step 4 deletes the stale test files.
