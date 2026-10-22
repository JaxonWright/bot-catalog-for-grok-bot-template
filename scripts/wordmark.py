"""Bubble letters: each glyph is a centerline drawn with a fat round-capped stroke.

Glyphs sit on a grid where capitals run from y=0 to the baseline at y=10, lowercase starts at y=3,
and descenders reach y=13.5. A glyph is its advance width and its centerline paths.
"""

import math

from avatars import ARTWORK_COLORS, avatar_body

STROKE = 2.6
GAP = 1.2
DESCENDERS = set("gjpqy")


def line(*points: tuple[float, float]) -> str:
    return "M" + " L".join(f"{x:g} {y:g}" for x, y in points)


def arc(cx: float, cy: float, rx: float, ry: float, start: float, end: float) -> str:
    """An elliptical arc between two angles in degrees, 0 pointing right and 90 pointing down."""

    def at(angle):
        return cx + rx * math.cos(math.radians(angle)), cy + ry * math.sin(math.radians(angle))

    (x0, y0), (x1, y1) = at(start), at(end)
    large = 1 if abs(end - start) > 180 else 0
    sweep = 1 if end > start else 0
    return f"M{x0:.2f} {y0:.2f} A{rx:g} {ry:g} 0 {large} {sweep} {x1:.2f} {y1:.2f}"


def ellipse(cx: float, cy: float, rx: float, ry: float) -> str:
    return f"M{cx - rx:g} {cy:g} A{rx:g} {ry:g} 0 1 0 {cx + rx:g} {cy:g} A{rx:g} {ry:g} 0 1 0 {cx - rx:g} {cy:g} Z"


def dot(x: float, y: float) -> str:
    return f"M{x:g} {y:g} h0.01"


BOWL = ellipse(2.6, 6.5, 2.6, 3.5)
ARCH = "M{x} 6.2 Q{x} 3 {m} 3 Q{r} 3 {r} 6.2 V10"
B_UPPER = "M0 0 H3.2 Q5.6 0 5.6 2.4 Q5.6 4.8 3.2 4.8 H0"
P_UPPER = "M0 10 V0 H3.4 Q6.2 0 6.2 2.8 Q6.2 5.6 3.4 5.6 H0"

GLYPHS: dict[str, tuple[float, tuple[str, ...]]] = {
    "a": (5.2, (BOWL, line((5.2, 3), (5.2, 10)))),
    "b": (5.2, (BOWL, line((0, 0), (0, 10)))),
    "c": (5.2, (arc(2.8, 6.5, 2.8, 3.5, 320, 40),)),
    "d": (5.2, (BOWL, line((5.2, 0), (5.2, 10)))),
    "e": (5.4, (line((0.2, 6.5), (5.4, 6.5)), arc(2.7, 6.5, 2.7, 3.5, 360, 45))),
    "f": (3.8, ("M1.4 10 V2.6 Q1.4 0 3.8 0", line((0, 3.6), (3.6, 3.6)))),
    "g": (5.2, (BOWL, "M5.2 3 V11 Q5.2 13.5 2.6 13.5 Q0.9 13.5 0.2 12.6")),
    "h": (5.2, (line((0, 0), (0, 10)), ARCH.format(x=0, m=2.6, r=5.2))),
    "i": (0, (line((0, 3), (0, 10)), dot(0, 0.3))),
    "j": (1.2, ("M1.2 3 V11.4 Q1.2 13.5 -0.8 13.5", dot(1.2, 0.3))),
    "k": (4.8, (line((0, 0), (0, 10)), line((4.4, 3), (0.4, 6.4)), line((1.8, 5.4), (4.8, 10)))),
    "l": (0, (line((0, 0), (0, 10)),)),
    "m": (8.8, (line((0, 3), (0, 10)), ARCH.format(x=0, m=2.2, r=4.4), ARCH.format(x=4.4, m=6.6, r=8.8))),
    "n": (5.2, (line((0, 3), (0, 10)), ARCH.format(x=0, m=2.6, r=5.2))),
    "o": (5.6, (ellipse(2.8, 6.5, 2.8, 3.5),)),
    "p": (5.2, (BOWL, line((0, 3), (0, 13.5)))),
    "q": (5.2, (BOWL, line((5.2, 3), (5.2, 13.5)))),
    "r": (3.6, (line((0, 3), (0, 10)), "M0 6.4 Q0 3 3.6 3")),
    "s": (4.6, ("M4.4 3.7 Q3.6 3 2.3 3 Q0.2 3 0.2 4.8 Q0.2 6.4 2.3 6.5 Q4.6 6.6 4.6 8.3 Q4.6 10 2.3 10 Q1 10 0 9.3",)),
    "t": (3.4, ("M1.4 0.8 V8.2 Q1.4 10 3.4 10", line((0, 3.6), (3.4, 3.6)))),
    "u": (5.2, ("M0 3 V6.8 Q0 10 2.6 10 Q5.2 10 5.2 6.8", line((5.2, 3), (5.2, 10)))),
    "v": (5.2, (line((0, 3), (2.6, 10), (5.2, 3)),)),
    "w": (7.8, (line((0, 3), (1.95, 10), (3.9, 4.6), (5.85, 10), (7.8, 3)),)),
    "x": (4.8, (line((0, 3), (4.8, 10)), line((4.8, 3), (0, 10)))),
    "y": (5.2, (line((0, 3), (2.7, 9.6)), "M5.2 3 L2.3 11.6 Q1.6 13.5 -0.2 13.5")),
    "z": (4.8, (line((0, 3), (4.8, 3), (0, 10), (4.8, 10)),)),
    "A": (7, (line((0, 10), (3.5, 0), (7, 10)), line((1.4, 6.6), (5.6, 6.6)))),
    "B": (6.2, ("M0 0 V10 H3.6 Q6.2 10 6.2 7.4 Q6.2 4.8 3.4 4.8 H0", B_UPPER)),
    "C": (7, (arc(4.2, 5, 4.2, 5, 318, 42),)),
    "D": (6.8, ("M0 0 V10 H2.4 Q6.8 10 6.8 5 Q6.8 0 2.4 0 Z",)),
    "E": (5.4, (line((5.4, 0), (0, 0), (0, 10), (5.4, 10)), line((0, 5), (4.4, 5)))),
    "F": (5.4, (line((5.4, 0), (0, 0), (0, 10)), line((0, 5), (4.4, 5)))),
    "G": (8, (arc(4.2, 5, 4.2, 5, 318, 0) + " H8 V6.4", line((8, 5.4), (4.8, 5.4)))),
    "H": (6.2, (line((0, 0), (0, 10)), line((6.2, 0), (6.2, 10)), line((0, 5), (6.2, 5)))),
    "I": (0, (line((0, 0), (0, 10)),)),
    "J": (4.8, ("M4.8 0 V6.6 Q4.8 10 2.2 10 Q0.2 10 -0.3 7.8",)),
    "K": (6, (line((0, 0), (0, 10)), line((5.6, 0), (0.4, 5.6)), line((2.2, 4), (6, 10)))),
    "L": (5, (line((0, 0), (0, 10), (5, 10)),)),
    "M": (8, (line((0, 10), (0, 0), (4, 6.4), (8, 0), (8, 10)),)),
    "N": (6.4, (line((0, 10), (0, 0), (6.4, 10), (6.4, 0)),)),
    "O": (8.8, (ellipse(4.4, 5, 4.4, 5),)),
    "P": (6.2, (P_UPPER,)),
    "Q": (8.8, (ellipse(4.4, 5, 4.4, 5), line((5.8, 7.2), (8.8, 10.4)))),
    "R": (6.2, (P_UPPER, line((3, 5.6), (6.2, 10)))),
    "S": (5.8, ("M5.6 1.2 Q4.6 0 2.9 0 Q0.2 0 0.2 2.5 Q0.2 4.6 2.9 4.9 Q5.8 5.2 5.8 7.4 Q5.8 10 2.9 10 Q1 10 0 8.8",)),
    "T": (6.6, (line((0, 0), (6.6, 0)), line((3.3, 0), (3.3, 10)))),
    "U": (6.4, ("M0 0 V6.4 Q0 10 3.2 10 Q6.4 10 6.4 6.4 V0",)),
    "V": (7, (line((0, 0), (3.5, 10), (7, 0)),)),
    "W": (9.8, (line((0, 0), (2.45, 10), (4.9, 2.6), (7.35, 10), (9.8, 0)),)),
    "X": (6.4, (line((0, 0), (6.4, 10)), line((6.4, 0), (0, 10)))),
    "Y": (6.6, (line((0, 0), (3.3, 5.2), (6.6, 0)), line((3.3, 5.2), (3.3, 10)))),
    "Z": (6.2, (line((0, 0), (6.2, 0), (0, 10), (6.2, 10)),)),
    "0": (6, (ellipse(3, 5, 3, 5),)),
    "1": (2.4, (line((0, 1.8), (2.4, 0), (2.4, 10)),)),
    "2": (5.8, ("M0.2 2.4 Q0.8 0 3 0 Q5.6 0 5.6 2.6 Q5.6 4.4 3.4 6 L0 10 H5.8",)),
    "3": (5.8, ("M0.2 1.2 Q1.2 0 2.9 0 Q5.4 0 5.4 2.4 Q5.4 4.8 2.6 4.8 Q5.8 4.8 5.8 7.4 Q5.8 10 2.9 10 Q1 10 0 8.8",)),
    "4": (6, (line((4.4, 10), (4.4, 0), (0, 7), (6, 7)),)),
    "5": (5.8, ("M5.4 0 H0.8 L0.4 4.6 Q1.4 3.8 2.9 3.8 Q5.8 3.8 5.8 6.9 Q5.8 10 2.9 10 Q1 10 0 8.8",)),
    "6": (5.8, (ellipse(2.9, 6.8, 2.9, 3.2), "M5 0.6 Q4.2 0 3.2 0 Q0 0 0 6.8")),
    "7": (5.8, (line((0, 0), (5.8, 0), (2, 10)),)),
    "8": (5.8, (ellipse(2.9, 2.4, 2.5, 2.4), ellipse(2.9, 7.4, 2.9, 2.6))),
    "9": (5.8, (ellipse(2.9, 3.2, 2.9, 3.2), "M5.8 3.2 Q5.8 10 2.6 10 Q1.4 10 0.6 9.4")),
    "'": (0, (line((0, 0), (0, 2.4)),)),
    "-": (3.6, (line((0, 6.2), (3.6, 6.2)),)),
    "!": (0, (line((0, 0), (0, 6.4)), dot(0, 10))),
    ".": (0, (dot(0, 10),)),
}


def bubble_word(text: str, color: str, offset: int, theme: str) -> tuple[str, float, float | None] | None:
    """The word in glyph units with its top-left stroke edge at the origin, its width, and where its first descender starts.

    None if a letter has no glyph. offset staggers the animation of each o so they don't blink together.
    """
    if not all(ch in GLYPHS for ch in text):
        return None
    pad = STROKE / 2
    x, parts, descender = pad, [], None
    for i, ch in enumerate(text):
        width, paths = GLYPHS[ch]
        if ch in DESCENDERS and descender is None:
            descender = x - pad
        if ch == "o":
            # The o is a little bot: a circle avatar stretched over the letter's outer edge.
            w, h = (width + STROKE) * 60 / 50, (7 + STROKE) * 60 / 50
            parts.append(
                f'<svg x="{x + width / 2 - w / 2:.2f}" y="{pad + 6.5 - h / 2:.2f}" width="{w:.2f}" height="{h:.2f}" '
                f'viewBox="0 0 60 60" preserveAspectRatio="none" style="--d: -{(offset + i) * 1.3 % 8:.1f}s">{avatar_body("circle", color, theme)}</svg>'
            )
        else:
            parts.append(f'<path transform="translate({x:.2f} {pad})" d="{" ".join(paths)}" stroke="{ARTWORK_COLORS[color]}"/>')
        x += width + STROKE + GAP
    return "".join(parts), x - GAP - pad, descender
