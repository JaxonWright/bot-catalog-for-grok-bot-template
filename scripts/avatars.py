"""Bot avatars: a colored body with two solid eyes, drawn on a 60 by 60 canvas."""

import math
from dataclasses import dataclass

# The colors Grok Bot offers for a bot, by the same names, so a bot's avatar can be copied straight across.
COLORS = {
    "black": "#16161A",
    "brown": "#8F5E34",
    "red": "#F2414F",
    "orange": "#FF7A1A",
    "yellow": "#FFB224",
    "green": "#1DBF73",
    "cyan": "#14B8C4",
    "blue": "#2F80FF",
    "violet": "#8B5CF6",
    "magenta": "#EE3D96",
    "gray": "#8A8F98",
}
# Only the README header uses these. Bots can't, because Grok Bot has no white, and its black turns white in
# dark mode while the header's ink stays dark.
ARTWORK_COLORS = COLORS | {"white": "#FFFFFF", "ink": COLORS["black"]}
# Bots have white eyes in light mode and black eyes in dark mode, where a black bot also turns white,
# as in Grok Bot. Every avatar SVG carries this rule. The header's white and ink keep their eyes fixed.
DARK_MODE_STYLE = """
@media (prefers-color-scheme: dark) {
  .black .skin { fill: #FFFFFF; color: #FFFFFF; }
  .eye { fill: #000000; }
}
"""


@dataclass(frozen=True)
class Eyes:
    cy: float = 28
    width: float = 7
    height: float = 12
    gap: float = 13


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


SMALL_EYES = Eyes(cy=30, width=6, height=10, gap=11)
# A lid in a darker shade of the body, so the cylinder reads as round on top.
SHADE = 'fill="#000" fill-opacity="0.18"'

# Grok Bot's shapes, by the same names. The drawings are this project's own.
SHAPES = {
    "blob": Shape((smooth_closed(radial([25, 27, 23, 26, 24, 27, 22, 26], cy=31)),), Eyes(cy=29)),
    "pebble": Shape((smooth_closed(radial([26, 27, 28, 26, 25, 27, 28, 26], cy=31, squash=0.74)),), Eyes(cy=30, height=11)),
    "bean": Shape((smooth_closed([(14, 14), (30, 20), (46, 14), (56, 29), (46, 46), (30, 50), (14, 46), (4, 29)]),), Eyes(cy=33)),
    "egg": Shape(('<path d="M30 4 C44 4 52 24 52 36 C52 48 42 56 30 56 C18 56 8 48 8 36 C8 24 16 4 30 4 Z"/>',), Eyes(cy=33)),
    "squircle": Shape((superellipse(25, 4.5),)),
    "tablet": Shape(('<rect x="11" y="4" width="38" height="52" rx="10"/>',), Eyes(cy=26, gap=12)),
    "capsule": Shape(('<rect x="14" y="5" width="32" height="50" rx="16"/>',), Eyes(cy=26, width=6.5, gap=11)),
    "cylinder": Shape(
        (
            '<path d="M9 14 A21 8 0 0 1 51 14 V46 A21 8 0 0 1 9 46 Z"/>',
            f'<ellipse cx="30" cy="14" rx="21" ry="8" {SHADE}/>',
        ),
        Eyes(cy=34),
    ),
    "hex": Shape((regular_polygon(6, 27, 6),)),
    "gem": Shape((rounded_polygon([(17, 9), (43, 9), (56, 24), (30, 55), (4, 24)], 4),), Eyes(cy=24, height=10)),
    "crystal": Shape((rounded_polygon([(30, 3), (47, 15), (47, 45), (30, 57), (13, 45), (13, 15)], 4),), Eyes(cy=29, width=6, gap=12)),
    "wedge": Shape((rounded_polygon([(30, 6), (56, 51), (4, 51)], 9),), Eyes(cy=37, width=6, height=10, gap=11)),
    "shield": Shape(('<path d="M8 11 Q30 1 52 11 V28 C52 42 42 51 30 57 C18 51 8 42 8 28 Z"/>',), Eyes(cy=26)),
    "dome": Shape(('<path d="M5 47 V37 A25 25 0 0 1 55 37 V47 Q55 52 50 52 H10 Q5 52 5 47 Z"/>',), Eyes(cy=33)),
    "arch": Shape(('<path d="M6 55 V30 A24 24 0 0 1 54 30 V55 H41 V41 A11 11 0 0 0 19 41 V55 Z"/>',), Eyes(cy=21, height=10)),
    "cloud": Shape(
        (
            '<circle cx="18" cy="35" r="13"/>',
            '<circle cx="31" cy="25" r="16"/>',
            '<circle cx="43" cy="35" r="12"/>',
            '<rect x="16" y="30" width="28" height="18" rx="6"/>',
        ),
        Eyes(cy=32),
    ),
    "teardrop": Shape(('<path d="M30 3 C38 13 52 24 52 34 A22 22 0 0 1 8 34 C8 24 22 13 30 3 Z"/>',), Eyes(cy=35)),
    "leaf": Shape(('<path d="M7 53 C7 25 25 7 53 7 C53 35 35 53 7 53 Z"/>',), Eyes(cy=30, width=6, height=10, gap=12)),
    "square": Shape(('<rect x="7" y="7" width="46" height="46" rx="6"/>',)),
    "sparkle": Shape(('<path d="M30 3 Q37 23 57 30 Q37 37 30 57 Q23 37 3 30 Q23 23 30 3 Z"/>',), Eyes(cy=30, width=5, height=9, gap=9)),
    "clover": Shape(
        ('<path d="M30 36 Q31 48 39 56" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>', *ring(3, 12, 13.5, cy=27), '<circle cx="30" cy="27" r="11"/>'),
        Eyes(cy=27, width=6, height=10, gap=11),
    ),
    "flower": Shape((*ring(5, 16, 11), '<circle cx="30" cy="30" r="15"/>'), SMALL_EYES),
    "heart": Shape(('<path d="M30 54 C14 42 4 33 4 21 C4 12 11 6 19 6 C24 6 28 9 30 13 C32 9 36 6 41 6 C49 6 56 12 56 21 C56 33 46 42 30 54 Z"/>',), Eyes(cy=25)),
    "house": Shape((rounded_polygon([(30, 4), (56, 27), (50, 27), (50, 55), (10, 55), (10, 27), (4, 27)], 3),), Eyes(cy=38)),
    "star": Shape((star(5, 28, 14, 32, 3),), Eyes(cy=33, width=5, height=9, gap=9)),
}
# Only the README header's wordmark uses a plain circle. Bots can't, because Grok Bot has no circle.
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
    eyes = "".join(
        f'<rect class="{eye_class}" x="{30 + side * e.gap / 2 - e.width / 2:.2f}" y="{e.cy - e.height / 2:.2f}" '
        f'width="{e.width}" height="{e.height}" rx="{e.width / 2}" fill="{ink}"/>'
        for side in (-1, 1)
    )
    fill = ARTWORK_COLORS[color]
    return (
        f'<g class="body {color}">{outline}<g class="skin" fill="{fill}" color="{fill}">{parts}</g>'
        f'<g class="look">{eyes}</g></g>'
    )
