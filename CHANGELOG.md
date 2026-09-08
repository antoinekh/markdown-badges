# Changelog

## Unreleased

### Fixed

- A backslash-escaped keyword (`\!high`) now renders as literal text instead of a badge with a stray backslash. The inline processor moved from priority 185 to 175, below Python-Markdown's own `escape` pattern (180).
- `priority_of` and `level_rank` no longer raise `AttributeError` when passed a name -> color mapping. They accept any iterable of level names, so the extension's own `levels` option can be reused directly.
- README image and `LICENSE` links are absolute, so they render on the PyPI project page instead of breaking.

### Added

- **Extended level values.** A `levels` value becomes the badge's `background-color`, and anything after a `;` becomes a further declaration on that badge. A level can now carry a background image, a gradient, or a shadow straight from config, with no site CSS. This behaviour existed before but was undocumented and unsupported; it is now a documented feature with tests. The value is not parsed or filtered, exactly like an `extra_css` rule.
- `__all__`, plus the `TREE_PRIORITY` and `INLINE_PRIORITY` constants that document why each processor is registered where it is.
- Colors accept 4- and 8-digit hex (`#eeef`, `#eeeeeeff`); the alpha channel is dropped before the contrast calculation.
- A `levels` value is rejected with a `ValueError` when the extension loads if it is not a string, or is empty. Those cannot produce CSS at all, so they are config mistakes rather than intent.
- `mypy --strict` over `src`, and `ruff format --check`, both run in CI.
- Tests for the escape hatch, nested task lists, `*` / `+` bullets, an uppercase `[X]` checkbox, an inline keyword inside a task item, alpha hex colors, extended level values, and value validation.

### Changed

- The text-contrast calculation reads a level value up to its first `;`, so a value carrying extra declarations now contrasts against its real background instead of silently falling back to white text.
- The ruff lint rule set now selects `E`, `F`, `I`, `UP`, and `B`.
- Both workflows use the same action versions (`actions/checkout@v6`, `astral-sh/setup-uv@v8.2.0`).
- Added the per-version Python, Markdown topic, and `Typing :: Typed` classifiers, plus the `Repository` and `Issues` project URLs.

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
