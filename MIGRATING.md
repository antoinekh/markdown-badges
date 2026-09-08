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
