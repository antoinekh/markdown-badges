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
