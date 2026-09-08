# Changelog

## 1.0.0 - 2026-09-08

### Added

- The badge catalogue ships in the package and is active with no config. `catalogue` narrows it; `[]` disables it.
- `badges_in(text)` returns every badge on a line, of any type, in document order.
- `shorthand` maps any task-list marker to any badge, so `!` / `!!` is config a user opts into and anyone can invent their own markers.
- `BadgeType`, `Badge`, `CATALOGUE`, and `catalogue_for` are public.
- **Extended badge values.** A badge value under `badges` becomes the badge's `background-color`, and anything after a `;` becomes a further declaration on that badge. A badge can carry a background image, a gradient, or a shadow straight from config, with no site CSS. The value is not parsed or filtered, exactly like an `extra_css` rule.
- Badge catalogue at `docs/badges.md`: every catalogue badge listed with its keyword, value, and resolved text colour, grouped into priority, status, and branding. Generated from `CATALOGUE` in `src/markdown_badges/catalogue.py` by `scripts/gen_badges.py`, so adding a badge is one entry plus a re-run.
- Logo badges for GitLab, GitHub, Claude, and Docker, each with its mark inlined as a `data:` URI so a page makes no network request for it.
- `__all__`, plus the `TREE_PRIORITY` and `INLINE_PRIORITY` constants that document why each processor is registered where it is.
- Colors accept 4- and 8-digit hex (`#eeef`, `#eeeeeeff`); the alpha channel is dropped before the contrast calculation.
- A badge value is rejected with a `ValueError` when the extension loads if it is not a string, or is empty. Those cannot produce CSS at all, so they are config mistakes rather than intent.
- `mypy --strict` over `src`, and `ruff format --check`, both run in CI.
- Tests for the escape hatch, nested task lists, `*` / `+` bullets, an uppercase `[X]` checkbox, an inline keyword inside a task item, alpha hex colors, extended badge values, and value validation.

### Changed

- Renamed to `markdown-badges`. Import path is `markdown_badges`, config key is `markdown_badges`, CSS class prefix is `badge` instead of `task-prio`.
- Badges are declared under `badges`, keyed by type (`priority`, `status`, `branding`), replacing the flat `levels` map.
- `priority_of` and `rank_of` consider only `priority` badges, so a status or branding badge can no longer be reported as a severity.
- The scanning API takes a `Mapping[str, Badge]` rather than a sequence of level names.
- The text-contrast calculation reads a badge value up to its first `;`, so a value carrying extra declarations now contrasts against its real background instead of silently falling back to white text.
- The ruff lint rule set now selects `E`, `F`, `I`, `UP`, and `B`.
- Both workflows use the same action versions (`actions/checkout@v6`, `astral-sh/setup-uv@v8.2.0`).
- Added the per-version Python, Markdown topic, and `Typing :: Typed` classifiers, plus the `Repository` and `Issues` project URLs.

### Removed

- The `levels` option. A leftover `levels` key raises a `ValueError` pointing at `MIGRATING.md`.
- The built-in `!` / `!!` task-list shorthand. Restore it with three lines of `shorthand` config.
- `LEVELS`, `DEFAULT_LEVELS`, `level_rank`, `MARKER_RE`, `PriorityBadgesExtension`, `PriorityInlineProcessor`, `TasklistShorthandTreeprocessor`.

### Fixed

- A backslash-escaped keyword (`\!high`) now renders as literal text instead of a badge with a stray backslash. The inline processor moved from priority 185 to 175, below Python-Markdown's own `escape` pattern (180).
- README image and `LICENSE` links are absolute, so they render on the PyPI project page instead of breaking.
- A `badges` entry whose type value is not a mapping (for example a list) now raises a `ValueError` naming the offending type key, instead of an `AttributeError` from calling `.items()` on it.
- The two badge-value validation errors now say what a valid value looks like, matching the `levels` and `shorthand` error messages.

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
