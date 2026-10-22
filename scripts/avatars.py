"""Bot avatars: a colored body with two solid eyes, drawn on a 60 by 60 canvas."""

import math
from dataclasses import dataclass

COLORS = {
    "white": "#FFFFFF",
    "black": "#16161A",
    "gray": "#8A8F98",
    "red": "#F2414F",
    "orange": "#FF7A1A",
    "yellow": "#FFB224",
    "green": "#1DBF73",
    "cyan": "#14B8C4",
    "blue": "#2F80FF",
    "violet": "#8B5CF6",
    "pink": "#F2559D",
}


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


SHAPES = {
    "circle": Shape(('<circle cx="30" cy="30" r="25"/>',)),
    "oval": Shape(('<ellipse cx="30" cy="30" rx="26" ry="21"/>',), Eyes(cy=29)),
    "rounded-square": Shape(('<rect x="6" y="6" width="48" height="48" rx="15"/>',)),
    "pill": Shape(('<rect x="14" y="5" width="32" height="50" rx="16"/>',), Eyes(cy=26, width=6.5, gap=11)),
    "triangle": Shape((rounded_polygon([(30, 6), (56, 51), (4, 51)], 9),), Eyes(cy=37, width=6, height=10, gap=11)),
    "hexagon": Shape((regular_polygon(6, 27, 6),)),
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
}

OUTLINE = "#D0D0D0"


def avatar_body(shape: str, color: str) -> str:
    spec = SHAPES[shape]
    parts = "".join(spec.parts)
    # A white body would vanish on GitHub's light theme, so it sits on a slightly larger gray copy of itself.
    outline = f'<g fill="{OUTLINE}" stroke="{OUTLINE}" stroke-width="2.4">{parts}</g>' if color == "white" else ""
    ink = "#FFFFFF" if color == "black" else "#000000"
    e = spec.eyes
    eyes = "".join(
        f'<rect class="blink" x="{30 + side * e.gap / 2 - e.width / 2:.2f}" y="{e.cy - e.height / 2:.2f}" '
        f'width="{e.width}" height="{e.height}" rx="{e.width / 2}" fill="{ink}"/>'
        for side in (-1, 1)
    )
    return f'<g class="body">{outline}<g fill="{COLORS[color]}">{parts}</g><g class="look">{eyes}</g></g>'
