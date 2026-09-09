# Changelog

## 1.0.0 - 2026-09-08

Renamed from `markdown-priority-badges`. Breaking release: see [MIGRATING.md](MIGRATING.md).

### Added

- A 20-badge catalogue ships in the package and is active with no config: 6 priority, 9 status, 5 branding. `catalogue` narrows which types load, `[]` disables it.
- `shorthand` maps any task-list marker to any badge, so anyone can invent their own markers.
- Extended badge values: anything after a `;` in a value becomes a further CSS declaration, so a badge can carry an icon, a gradient or a shadow with no site CSS.
- `badges_in(text)` returns every badge on a line, of any type, in document order.
- Public API: `Badge`, `BadgeType`, `CATALOGUE`, `catalogue_for`, `resolve_badges`, `badges_in`, `priority_of`, `rank_of`.

### Changed

- Import path and config key are now `markdown_badges`; the CSS class prefix is `badge` instead of `task-prio`.
- Badges are declared under `badges`, keyed by type (`priority`, `status`, `branding`), replacing the flat `levels` map.
- `priority_of` and `rank_of` consider only `priority` badges, so a status or branding badge can no longer be reported as a severity.
- The scanning API takes a `Mapping[str, Badge]` rather than a sequence of level names.

### Removed

- The `levels` option. A leftover `levels` key raises a `ValueError` pointing at the migration guide.
- The built-in `!` / `!!` task-list shorthand. Three lines of `shorthand` config restore it.
- `LEVELS`, `DEFAULT_LEVELS`, `level_rank`, `MARKER_RE`, `PriorityBadgesExtension`, `PriorityInlineProcessor`, `TasklistShorthandTreeprocessor`.

### Fixed

- A backslash-escaped keyword (`\!high`) renders as literal text instead of a badge with a stray backslash.
- The text-contrast calculation reads a badge value up to its first `;`, so a value carrying extra declarations contrasts against its real background instead of falling back to white text.
- Every invalid config raises a `ValueError` naming the offending key and the fix, instead of failing silently or with an `AttributeError`.
- README links are absolute, so they resolve on the PyPI project page.

## 0.2.0 - 2026-07-01

### Added

- Public parsing API: `LEVELS`, `level_rank(level, levels=LEVELS)`, and `priority_of(text, levels=LEVELS)` for tools that aggregate or filter task items by priority.

## 0.1.0 - 2026-07-01

### Added

- Inline keywords: `!low` / `!medium` / `!high` / `!critical` (and any custom level) render a badge anywhere in prose, headings, or table cells. Only configured level keywords match, so an ordinary `!` in text is untouched.
- Task-list shorthand: a leading `!` (high) / `!!` (critical) after a checkbox renders a priority badge, via a Treeprocessor running just before `pymdownx.tasklist`.
- Configurable `levels` map (name -> color), merged over the built-in `low` / `medium` / `high` / `critical`, so levels can be recolored or added from config.
- Self-contained styling: badges ship inline styles (no external CSS), with the text color auto-contrasted (black or white) against each background.
- Colors accept 3- or 6-digit hex and common CSS names.
