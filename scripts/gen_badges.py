"""Generate `docs/badges.md`, the copy-paste badge catalogue.

Every badge lives in `CATALOGUE` below. To add one, append a `Badge` entry and
re-run this script:

    uv run python scripts/gen_badges.py

A branding badge needs its logo as a *single-path* SVG. Take the path data (the
`d` attribute), add it to `ICONS`, and reference it by key. Pick a base color
dark enough that the auto-contrast picks white when the logo is white, or light
enough that it picks black when the logo is dark, so mark and text agree.
"""

import math
import pathlib
import urllib.parse
from dataclasses import dataclass
from enum import Enum

# The catalogue reports the text color each base resolves to, so the table shows
# whether a logo fill matches. This is the package's own contrast helper.
from markdown_priority_badges import _text_color

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "docs" / "badges.md"


class Category(Enum):
    PRIORITY = "Priority"
    STATUS = "Status"
    BRANDING = "Branding"


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


# Single-path logo marks, on a 24x24 viewBox.
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

# Geometry shared by every icon badge: the mark sits left of the text, and the
# padding makes room for it.
_ICON_LAYOUT = (
    "background-repeat:no-repeat;background-position:0.45em center;"
    "background-size:0.8em;padding-left:1.75em"
)


@dataclass(frozen=True)
class Badge:
    """One `levels` entry: a name, a base color, and an optional logo."""

    name: str
    color: str
    category: Category
    note: str
    icon: str | None = None
    icon_fill: str = "#fff"

    @property
    def text_color(self) -> str:
        return _text_color(self.color)

    def value(self) -> str:
        """The `levels` value to paste into config."""
        if self.icon is None:
            return self.color
        svg = (
            f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
            f"fill='{self.icon_fill}'><path d='{ICONS[self.icon]}'/></svg>"
        )
        uri = "data:image/svg+xml," + urllib.parse.quote(svg, safe="")
        return f"{self.color};background-image:url('{uri}');{_ICON_LAYOUT}"


CATALOGUE: list[Badge] = [
    # --- Priority: ranked severity, the extension's built-in model ----------
    Badge("low", "#2e7d32", Category.PRIORITY, "Built-in. Green."),
    Badge("medium", "#f9a825", Category.PRIORITY, "Built-in. Amber."),
    Badge("high", "#ef6c00", Category.PRIORITY, "Built-in. Orange. Also the `!` shorthand."),
    Badge("critical", "#d32f2f", Category.PRIORITY, "Built-in. Red. Also the `!!` shorthand."),
    Badge("blocker", "#7b1fa2", Category.PRIORITY, "Above critical: work that cannot start."),
    Badge("trivial", "#78909c", Category.PRIORITY, "Below low: nice to have."),
    # --- Status: where an item sits in a workflow --------------------------
    Badge("todo", "#1565c0", Category.STATUS, "Not started."),
    Badge("wip", "#0277bd", Category.STATUS, "In progress."),
    Badge("review", "#6a1b9a", Category.STATUS, "Waiting on a reviewer."),
    Badge("blocked", "#b71c1c", Category.STATUS, "Waiting on someone else."),
    Badge("approved", "#2e7d32", Category.STATUS, "Signed off, not yet shipped."),
    Badge("done", "#37474f", Category.STATUS, "Finished."),
    Badge("onhold", "#8d6e63", Category.STATUS, "Paused on purpose."),
    Badge("experimental", "#00838f", Category.STATUS, "Not stable yet."),
    Badge("deprecated", "#5d4037", Category.STATUS, "On the way out."),
    # --- Branding: a logo inlined as a data: URI, no network request --------
    Badge("gitlab", "#7759c2", Category.BRANDING, "GitLab purple, white tanuki.", "gitlab"),
    Badge("github", "#181717", Category.BRANDING, "GitHub near-black, white mark.", "github"),
    Badge(
        "claude",
        "#d97757",
        Category.BRANDING,
        "Claude coral, dark starburst.",
        "claude",
        icon_fill="#1f1e1d",
    ),
]


def render() -> str:
    lines: list[str] = [
        "# Badge catalogue",
        "",
        "Ready-to-paste `levels` entries, grouped by what they are for. Copy the block you "
        "want into your config, under `[project.markdown_extensions."
        "markdown_priority_badges.levels]` (Zensical / MkDocs TOML) or into the "
        "`levels` dict (plain Python-Markdown).",
        "",
        "Generated by `scripts/gen_badges.py`. Edit the `CATALOGUE` there and re-run "
        "`uv run python scripts/gen_badges.py` rather than editing this file.",
        "",
        "![Every badge in the catalogue, rendered](img/catalogue.png)",
        "",
        "> [!NOTE]",
        "> Only `low`, `medium`, `high`, and `critical` ship as built-ins. Everything else "
        "here is config you add. Order matters for `priority_of`: a level's rank is its "
        "position in the map.",
        "",
    ]
    for category in Category:
        badges = [b for b in CATALOGUE if b.category is category]
        lines += [f"## {category.value}", ""]
        lines += ["| Keyword | Base | Text | Notes |", "| --- | --- | --- | --- |"]
        for b in badges:
            lines.append(f"| `!{b.name}` | `{b.color}` | `{b.text_color}` | {b.note} |")
        lines += ["", "```toml", "[project.markdown_extensions.markdown_priority_badges.levels]"]
        for b in badges:
            lines.append(f'{b.name} = "{b.value()}"')
        lines += ["```", ""]
    lines += [
        "## Adding a branding badge",
        "",
        "Take the logo as a single-path SVG and add its `d` attribute to `ICONS` in "
        '`scripts/gen_badges.py`, then add a `Badge(..., icon="<key>")` entry to '
        "`CATALOGUE`. The script URL-encodes the SVG and builds the `data:` URI, so the "
        "badge costs no network request.",
        "",
        "Pick the base color and the icon fill together. The badge text color is chosen "
        "automatically from the base, so a white mark needs a base dark enough to resolve "
        "to white text, and a dark mark needs a light one. The **Text** column above shows "
        "what each base resolves to.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render())
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(CATALOGUE)} badges)")


if __name__ == "__main__":
    main()
