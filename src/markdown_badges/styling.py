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
