# markdown-priority-badges

[![CI](https://github.com/antoinekh/markdown-priority-badges/actions/workflows/ci.yml/badge.svg)](https://github.com/antoinekh/markdown-priority-badges/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/markdown-priority-badges)](https://pypi.org/project/markdown-priority-badges/)
[![Python versions](https://img.shields.io/pypi/pyversions/markdown-priority-badges)](https://pypi.org/project/markdown-priority-badges/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/antoinekh/markdown-priority-badges/blob/master/LICENSE)

A Python-Markdown extension that renders **priority badges** two ways: `!level` keywords inline anywhere, and a `!` / `!!` shorthand on task-list items. Works in Zensical, MkDocs, or plain Python-Markdown. The badge ships its own inline styles, so no external CSS is required.

## Why?

This is not a replacement for admonitions / callouts (`!!! warning`, `> [!NOTE]`). Those wrap a block of explanatory text. Priority badges are the opposite: tiny inline pills you can drop anywhere, but that fit especially nicely into a **list item, todo, or table cell**, so priority is scannable at a glance without turning the line into a block. The intended usage is exactly that split: reach for a callout when you have a paragraph to say, and reach for a badge to mark some rows.

## Inline keywords

Inline `!level` keywords (`!low` / `!medium` / `!high` / `!critical`) work anywhere (prose, headings, table cells):

```markdown
This migration is !critical and blocks the release.

## !high Rotate the keys
```

![Inline priority badges rendered in prose and a heading](https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/inline-badges.png)

Only the configured level keywords match, so an ordinary `!`, `!important`, or `!highest` in text is never touched. To write a level keyword literally, escape it (`\!high`) or put it in a code span (`` `!high` ``).

## Todo shorthand

Inside a checkbox item, `!` = high and `!!` = critical, a quick shorthand for `!high` / `!critical`. The explicit `!level` keywords (including custom ones like `!todo`) work in list items too, so a todo list can mix all of them:

```markdown
- [ ] !blocker Waiting on vendor API access
- [ ] !! Ship the security patch today
- [ ] ! Review the migration PR
- [ ] !medium Update the runbook
- [ ] !low Tidy up log formatting
- [x] !! Rotate the leaked credentials
- [ ] Weekly backup check
```

<img alt="Todo list with priority badges" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/todo-badges.png" width="560">

The shorthand marker must come first (right after the checkbox) and be followed by a space, so `- [ ] !important note` is left untouched. Works with `-`, `*`, `+` bullets and both `[ ]` / `[x]` states.

## Levels

Four built-in levels, plus any custom level you add via config (`blocker` below is an example):

| Level    | Origin         | Keyword     | Renders as                                            |
| -------- | -------------- | ----------- | ----------------------------------------------------- |
| Low      | built-in       | `!low`      | <img alt="low" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/low.png" height="26">           |
| Medium   | built-in       | `!medium`   | <img alt="medium" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/medium.png" height="26">     |
| High     | built-in       | `!high`     | <img alt="high" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/high.png" height="26">         |
| Critical | built-in       | `!critical` | <img alt="critical" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/critical.png" height="26"> |
| Blocker  | example custom | `!blocker`  | <img alt="blocker" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/blocker.png" height="26">   |
| Todo     | example custom | `!todo`     | <img alt="todo" src="https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/todo.png" height="26">         |

The default backgrounds are low green, medium amber, high orange, critical red. The `!` / `!!` task-list shorthand always maps to `high` / `critical`; lower levels are used via their inline keyword (`!low`, `!medium`). Badge text color (black or white) is chosen automatically for legibility against each background.

### Custom / extra levels

The `levels` option is a name → color map that is **merged over** the built-ins, so you can recolor a level or add your own:

```toml
# zensical.toml
[project.markdown_extensions.markdown_priority_badges.levels]
blocker = "#7b1fa2"  # a new purple level, used as !blocker
todo    = "#1565c0"  # a new blue level, used as !todo
low     = "#1b5e20"  # recolor a built-in
```

```python
# plain Python-Markdown
from markdown_priority_badges import PriorityBadgesExtension
markdown.markdown(text, extensions=["pymdownx.tasklist", PriorityBadgesExtension(levels={"blocker": "#7b1fa2"})])
```

Colors may be 3-, 4-, 6-, or 8-digit hex (`#7b1fa2`, `#eee`, `#eeeeeeff`) or a common CSS name (`red`, `yellow`, `rebeccapurple`); the badge text color auto-contrasts against them. Any alpha channel is ignored for the contrast calculation.

### Extended level values

A level value becomes the badge's `background-color`, so anything you add after a `;` becomes a further declaration on that badge. Use it to give one level an icon, a gradient, or a shadow, without writing any site CSS:

```toml
[project.markdown_extensions.markdown_priority_badges.levels]
# A background image, plus the padding that makes room for it.
icon = "#b71c1c;background-image:url('data:image/svg+xml,…');background-repeat:no-repeat;background-position:0.4em center;background-size:0.85em;padding-left:1.7em"
# A gradient instead of a flat fill.
gradient = "#4a148c;background-image:linear-gradient(90deg,#4a148c,#c2185b)"
# A colored ring and halo.
glow = "#111;box-shadow:0 0 0 2px #ff1744,0 0 10px #ff1744"
```

The contrast calculation reads the leading color, up to the first `;`, so the badge text stays legible against the base you picked.

#### Example: logo badges

A level does not have to mean a priority. Inline a single-path logo as a `data:` URI and you get a brand badge that costs no network request, usable as `!gitlab` / `!github` / `!claude` anywhere a level keyword works:

```markdown
- [ ] !gitlab Rebase the config-models MR before the release
- [ ] !github !high Review the PR before the release
- [x] !claude Ask about the badge design
```

The full TOML for these three, and for every other badge shown below, is in the [badge catalogue](docs/badges.md).

Pick the base color and the logo fill together: the badge text color is chosen from the base, so a white mark needs a base dark enough to resolve to white text, and a dark mark needs a light one.

## Badge catalogue

Ready-to-paste `levels` entries for priority, status, and branding badges: **[docs/badges.md](docs/badges.md)**.

![Every badge in the catalogue, rendered](https://raw.githubusercontent.com/antoinekh/markdown-priority-badges/master/docs/img/catalogue.png)

The catalogue is generated from `CATALOGUE` in `scripts/gen_badges.py`. To add a badge, append one `Badge(...)` entry and run `uv run python scripts/gen_badges.py`. For a logo, add its single-path SVG to `ICONS` first; the script URL-encodes it and builds the `data:` URI.

> [!NOTE]
> The value is not parsed or filtered. It joins the badge's declaration list verbatim, exactly like an `extra_css` rule you write yourself, and the `levels` map is your own site config. Only the value's type is checked: a non-string or empty value raises a `ValueError` when the extension loads.

## Reusing the parser

The level metadata and marker parsing are exposed for tools that aggregate or filter task items (for example a todo dashboard):

```python
from markdown_priority_badges import LEVELS, level_rank, priority_of

priority_of("ping !high vendor")   # -> "high" (leading !/!! or any inline keyword)
priority_of("weekly backup")       # -> None  (no marker)

# the second arg is the ordered list of names to recognise (defaults to LEVELS);
# extend it to match custom badge levels, ranked by position:
priority_of("!blocker access", (*LEVELS, "blocker"))  # -> "blocker"
```

`priority_of` returns the highest-ranked level found anywhere in the text, or `None`. `level_rank` gives a level's severity index. Both accept any iterable of level names in ascending severity order, including the `levels` name → color map itself (its keys are read, in order).

> [!NOTE]
> `priority_of` is a plain-text scan, not a Markdown parse. Unlike the rendered badge, a keyword inside a code span or escaped as `\!high` still counts.

## Install & enable

```bash
uv add markdown-priority-badges
```

(or `pip install markdown-priority-badges`)

Zensical (`zensical.toml`):

```toml
[project.markdown_extensions.markdown_priority_badges]
```

Plain Python-Markdown:

```python
markdown.markdown(text, extensions=["pymdownx.tasklist", "markdown_priority_badges"])
```

The badge renders as `<span class="task-prio task-prio--<level>" style="...">...</span>`. The `task-prio` classes are kept for optional site-side overriding, but no CSS is needed by default.
