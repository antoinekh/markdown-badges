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
