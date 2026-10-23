"""Bot avatars: a colored body with two solid eyes, drawn on a 60 by 60 canvas."""

import math
from dataclasses import dataclass

# The colors Grok Bot offers for a bot, by the same names and values, so a bot's avatar can be copied straight across.
COLORS = {
    "black": "#000000",
    "brown": "#A27952",
    "red": "#FF3E51",
    "orange": "#FF781C",
    "yellow": "#FFAF38",
    "green": "#00C972",
    "cyan": "#1CC3B0",
    "blue": "#2A92FE",
    "violet": "#A97EFE",
    "magenta": "#FF5EB1",
    "gray": "#959595",
}
# Grok Bot darkens each color in dark mode, and turns black white.
DARK_COLORS = {
    "black": "#FFFFFF",
    "brown": "#855C36",
    "red": "#E02135",
    "orange": "#FF6700",
    "yellow": "#FF9800",
    "green": "#009957",
    "cyan": "#00A592",
    "blue": "#0E74E0",
    "violet": "#804EE0",
    "magenta": "#E02A88",
    "gray": "#777777",
}
# Only the README header uses these. Bots can't, because Grok Bot has no white, and its black turns white in
# dark mode while the header's ink stays dark.
# GitHub's light-theme text color, so the header's bubble letters and plain text match.
INK = "#1F2328"
ARTWORK_COLORS = COLORS | {"white": "#FFFFFF", "ink": INK}
if DARK_COLORS.keys() != COLORS.keys():
    raise RuntimeError("COLORS and DARK_COLORS must name the same colors")


def dark_mode_style(color: str) -> str:
    """Bots have white eyes in light mode and black eyes in dark mode, as in Grok Bot, and a darker body.

    The header is drawn once per theme, so it takes its colors from avatar_body's theme instead.
    """
    value = DARK_COLORS[color]
    return f"\n@media (prefers-color-scheme: dark) {{\n  .{color} .skin {{ fill: {value}; color: {value}; }}\n  .eye {{ fill: #000000; }}\n}}\n"


@dataclass(frozen=True)
class Eyes:
    cy: float = 29
    width: float = 5
    height: float = 12
    gap: float = 12.5


@dataclass(frozen=True)
class Shape:
    parts: tuple[str, ...]
    eyes: Eyes = Eyes()


def rounded_polygon(points: list[tuple[float, float]], corner: float) -> str:
    def toward(a, b):
        length = math.dist(a, b)
        return (a[0] + (b[0] - a[0]) * corner / length, a[1] + (b[1] - a[1]) * corner / length)

    segments = []
    for i, vertex in enumerate(points):
        before, after = points[i - 1], points[(i + 1) % len(points)]
        start, end = toward(vertex, before), toward(vertex, after)
        segments.append(f"{'M' if i == 0 else 'L'}{start[0]:.2f} {start[1]:.2f} Q{vertex[0]:.2f} {vertex[1]:.2f} {end[0]:.2f} {end[1]:.2f}")
    return f'<path d="{" ".join(segments)} Z"/>'


def regular_polygon(sides: int, radius: float, corner: float) -> str:
    points = [
        (30 + radius * math.cos(math.radians(-90 + i * 360 / sides)), 30 + radius * math.sin(math.radians(-90 + i * 360 / sides)))
        for i in range(sides)
    ]
    return rounded_polygon(points, corner)


def smooth_closed(points: list[tuple[float, float]]) -> str:
    """A closed curve through every point, with no corners."""
    n = len(points)
    segments = [f"M{points[0][0]:.2f} {points[0][1]:.2f}"]
    for i in range(n):
        p0, p1, p2, p3 = points[i - 1], points[i], points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segments.append(f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    return f'<path d="{" ".join(segments)} Z"/>'


def radial(radii: list[float], cx: float = 30, cy: float = 30, squash: float = 1) -> list[tuple[float, float]]:
    """Points around a center, one radius per equal step of angle, starting at the top."""
    step = 2 * math.pi / len(radii)
    return [(cx + r * math.sin(i * step), cy - r * squash * math.cos(i * step)) for i, r in enumerate(radii)]


def star(points: int, outer: float, inner: float, cy: float, corner: float) -> str:
    step = math.pi / points
    vertices = [
        (30 + r * math.sin(i * step), cy - r * math.cos(i * step))
        for i, r in enumerate([outer, inner] * points)
    ]
    return rounded_polygon(vertices, corner)


def superellipse(radius: float, power: float) -> str:
    vertices = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        c, s = math.cos(t), math.sin(t)
        vertices.append((30 + radius * math.copysign(abs(c) ** (2 / power), c), 30 + radius * math.copysign(abs(s) ** (2 / power), s)))
    return "<path d=\"M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in vertices) + ' Z"/>'


def ring(count: int, distance: float, radius: float, cy: float = 30) -> tuple[str, ...]:
    return tuple(
        f'<circle cx="{30 + distance * math.sin(2 * math.pi * i / count):.2f}" '
        f'cy="{cy - distance * math.cos(2 * math.pi * i / count):.2f}" r="{radius}"/>'
        for i in range(count)
    )


def petal(angle: float, distance: float, rx: float, ry: float, twist: float) -> str:
    """An ellipse pointing out from the center at angle degrees clockwise from the top, turned by twist."""
    a = math.radians(angle)
    cx, cy = 30 + distance * math.sin(a), 30 - distance * math.cos(a)
    return f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx}" ry="{ry}" transform="rotate({angle - 90 + twist:g} {cx:.2f} {cy:.2f})"/>'


SMALL_EYES = Eyes(width=4.5, height=10, gap=10)

# Grok Bot's shapes, by the same names, drawn to match how Grok Bot shows them. The drawings are this project's own.
SHAPES = {
    "blob": Shape(('<circle cx="30" cy="30" r="23"/>',)),
    "pebble": Shape((smooth_closed(radial([21, 23, 24, 22, 21, 22, 24, 22], cy=30.5, squash=0.9)),), Eyes(cy=27)),
    "bean": Shape((smooth_closed([(29, 8), (40, 11), (46.5, 22), (46, 36), (39, 48), (28, 52), (18, 49), (15, 41), (18, 32), (16, 20), (20, 11)]),), Eyes(cy=28)),
    "egg": Shape(('<path d="M30 7 C40 7 49 22 49 35 C49 46 40 53 30 53 C20 53 11 46 11 35 C11 22 20 7 30 7 Z"/>',), Eyes(cy=31)),
    "squircle": Shape((superellipse(23, 7),)),
    "tablet": Shape(('<rect x="7" y="15" width="46" height="30" rx="15"/>',), Eyes(cy=30)),
    "capsule": Shape(('<rect x="15" y="7" width="30" height="46" rx="15"/>',), Eyes(cy=26, gap=11)),
    "cylinder": Shape(('<path d="M10 13 A20 6 0 0 1 50 13 V47 A20 6 0 0 1 10 47 Z"/>',), Eyes(cy=27)),
    "hex": Shape((regular_polygon(6, 24, 5),)),
    "gem": Shape(('<path d="M30 7 C38 11 53 22 53 30 C53 38 38 49 30 53 C22 49 7 38 7 30 C7 22 22 11 30 7 Z"/>',), Eyes(cy=28)),
    "crystal": Shape((rounded_polygon([(30, 6), (43, 18), (43, 42), (30, 54), (17, 42), (17, 18)], 3),), SMALL_EYES),
    "wedge": Shape((rounded_polygon([(30, 6), (56, 51), (4, 51)], 9),), Eyes(cy=33, width=4.5, height=11, gap=11)),
    "shield": Shape(('<path d="M15 7 Q30 5 45 7 Q50 8 50 13 C50 37 43 53 30 53 C17 53 10 37 10 13 Q10 8 15 7 Z"/>',), Eyes(cy=24)),
    "dome": Shape(('<path d="M7 45 V37 A23 23 0 0 1 53 37 V45 Q53 47 51 47 H9 Q7 47 7 45 Z"/>',), Eyes(cy=34)),
    "arch": Shape(('<path d="M14 51 V23 A16 16 0 0 1 46 23 V51 Q46 53 44 53 H16 Q14 53 14 51 Z"/>',), Eyes(cy=27, gap=11)),
    "cloud": Shape(
        (
            '<circle cx="24.5" cy="22" r="11.5"/>',
            '<circle cx="37" cy="24.5" r="10"/>',
            '<circle cx="17" cy="34.5" r="10"/>',
            '<circle cx="43" cy="34.5" r="10"/>',
            '<circle cx="30" cy="37" r="11.5"/>',
        ),
        Eyes(cy=27),
    ),
    "teardrop": Shape(('<path d="M30 7 C34 12 49.5 23 49.5 33.5 A19.5 19.5 0 0 1 10.5 33.5 C10.5 23 26 12 30 7 Z"/>',), Eyes(cy=26)),
    "leaf": Shape(('<path d="M30 7 C41 14 47.5 23 47.5 30 C47.5 37 41 46 30 53 C19 46 12.5 37 12.5 30 C12.5 23 19 14 30 7 Z"/>',), Eyes(cy=29, gap=11)),
    "square": Shape(('<rect x="7" y="7" width="46" height="46" rx="5"/>',)),
    "sparkle": Shape((*(petal(angle, 11, 12, 7, -15) for angle in (15, 105, 195, 285)), '<circle cx="30" cy="30" r="9"/>'), SMALL_EYES),
    "clover": Shape(tuple(f'<circle cx="{x}" cy="{y}" r="12"/>' for x in (19, 41) for y in (19, 41)) + ('<rect x="19" y="19" width="22" height="22"/>',), Eyes(cy=30)),
    "flower": Shape((*ring(6, 15, 8.5), '<circle cx="30" cy="30" r="14"/>'), SMALL_EYES),
    "heart": Shape(
        (
            '<circle cx="19.5" cy="22" r="11"/>',
            '<circle cx="40.5" cy="22" r="11"/>',
            rounded_polygon([(11.7, 29.8), (30, 48.5), (48.3, 29.8), (30, 20)], 3),
        ),
        Eyes(cy=27),
    ),
    "house": Shape((rounded_polygon([(30, 7), (52, 21), (52, 53), (8, 53), (8, 21)], 4),), Eyes(cy=27)),
    "star": Shape((star(6, 24, 15, 30, 4),), SMALL_EYES),
}
# Only the README header and wordmark use this circle, which fills the canvas so a stretched one can wrap a letter.
ARTWORK_SHAPES = SHAPES | {"circle": Shape(('<circle cx="30" cy="30" r="25"/>',))}


OUTLINE = "#D0D0D0"


def avatar_body(shape: str, color: str, theme: str | None = None) -> str:
    """theme fixes the eyes for one README theme. Without it, the eyes follow the viewer's mode."""
    spec = ARTWORK_SHAPES[shape]
    parts = "".join(spec.parts)
    # A white body would vanish on GitHub's light theme, so it sits on a slightly larger gray copy of itself.
    outline = f'<g fill="{OUTLINE}" stroke="{OUTLINE}" stroke-width="2.4">{parts}</g>' if color == "white" else ""
    ink = "#000000" if color == "white" or theme == "dark" else "#FFFFFF"
    eye_class = "blink eye" if color in COLORS and theme is None else "blink"
    e = spec.eyes
    # Grok Bot's eyes lean a little to the right.
    eyes = "".join(
        f'<g transform="rotate(7 {30 + side * e.gap / 2:.2f} {e.cy})"><rect class="{eye_class}" '
        f'x="{30 + side * e.gap / 2 - e.width / 2:.2f}" y="{e.cy - e.height / 2:.2f}" '
        f'width="{e.width}" height="{e.height}" rx="{e.width / 2}" fill="{ink}"/></g>'
        for side in (-1, 1)
    )
    fill = DARK_COLORS[color] if theme == "dark" and color in DARK_COLORS else ARTWORK_COLORS[color]
    return (
        f'<g class="body {color}">{outline}<g class="skin" fill="{fill}" color="{fill}">{parts}</g>'
        f'<g class="look">{eyes}</g></g>'
    )

ANIMATION_STYLE = """
.body { transform-origin: 30px 30px; animation: breathe 3.2s ease-in-out var(--d, 0s) infinite; }
.look { animation: look 8s ease-in-out var(--d, 0s) infinite; }
.blink { transform-box: fill-box; transform-origin: center; animation: blink 8s var(--d, 0s) infinite; }
@keyframes breathe { 50% { transform: scale(1.05); } }
@keyframes look {
  0%, 10% { transform: translate(0, 0); }
  16%, 32% { transform: translate(-2.6px, -0.4px); }
  38%, 48% { transform: translate(0, 0); }
  54%, 70% { transform: translate(2.6px, 0.6px); }
  76%, 86% { transform: translate(1.2px, -1.8px); }
  92%, 100% { transform: translate(0, 0); }
}
@keyframes blink {
  0%, 34%, 38%, 88%, 92%, 100% { transform: scaleY(1); }
  36%, 90% { transform: scaleY(0.12); }
}
@media (prefers-reduced-motion: reduce) { .body, .look, .blink { animation: none; } }
"""


def render_avatar(shape: str, color: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60" width="128" height="128">'
        f"<style>{ANIMATION_STYLE}{dark_mode_style(color)}</style>{avatar_body(shape, color)}</svg>\n"
    )
