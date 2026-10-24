"""Draws the diagrams in docs/how-it-works.md as light and dark SVGs in docs/diagrams/.

Run python scripts/diagrams.py after changing a diagram here. It prints any label too wide for its box.
"""

import html
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "diagrams"
SANS = "-apple-system, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
THEMES = {
    "light": dict(bg="#fbfdfc", fg="#15201e", muted="#566864", line="#a9b9b5", file="#ffffff", auto="#0e7468",
                  auto_bg="#e0f1ed", gate="#9a5806", gate_bg="#fbeedb", bot="#3f4f8c", bot_bg="#e9ecf8"),
    "dark": dict(bg="#131b1a", fg="#e2ebe8", muted="#93a6a1", line="#3c4c48", file="#18211f", auto="#52c4b3",
                 auto_bg="#11302b", gate="#e9a84b", gate_bg="#33250e", bot="#9daaf0", bot_bg="#1c2240"),
}
# Rough pixels per character, to catch a label that spills out of its box.
CHAR_WIDTH = {"title": 7.0, "sub": 6.3, "mono": 6.9}
too_wide = []


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def fits(text: str, kind: str, room: float, where: str) -> None:
    if len(text) * CHAR_WIDTH[kind] > room:
        too_wide.append(f"{where}: {text!r} is too wide for its box")


def box(x, y, w, h, kind, title, subs=(), mono=False):
    """A rectangle with a bold title and muted lines under it, centered. kind is file, out, auto, gate, or bot."""
    cx = x + w / 2
    top = y + h / 2 - len(subs) * 7.5 + 4
    fits(title, "mono" if mono else "title", w - 14, title)
    parts = [f'<rect class="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>',
             f'<text class="{"tm" if mono else "tt"}" x="{cx}" y="{top}" text-anchor="middle">{esc(title)}</text>']
    for i, sub in enumerate(subs):
        fits(sub, "sub", w - 14, title)
        parts.append(f'<text class="ts" x="{cx}" y="{top + 16 + i * 15}" text-anchor="middle">{esc(sub)}</text>')
    return "".join(parts)


def edge(points, label=None, at=None, anchor="middle", accent=False):
    """An arrow along points, with an optional label of one or more lines starting at at."""
    path = " ".join(f"{x},{y}" for x, y in points)
    out = f'<polyline class="edge{" accent" if accent else ""}" points="{path}" marker-end="url(#{"ha" if accent else "h"})"/>'
    for i, line in enumerate([label] if isinstance(label, str) else label or []):
        out += f'<text class="tl" x="{at[0]}" y="{at[1] + i * 14}" text-anchor="{anchor}">{esc(line)}</text>'
    return out


def card(x, y, w, h, title, lines):
    """A file's contents: a title over lines of monospace text, each drawn as normal or changed."""
    parts = [f'<rect class="file" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>',
             f'<text class="tt" x="{x + 14}" y="{y + 24}">{esc(title)}</text>',
             f'<line class="rule" x1="{x}" y1="{y + 36}" x2="{x + w}" y2="{y + 36}"/>']
    for i, (text, changed) in enumerate(lines):
        fits(text, "mono", w - 24, title)
        parts.append(f'<text class="{"tma" if changed else "tm"}" x="{x + 14}" y="{y + 58 + i * 20}">{esc(text)}</text>')
    return "".join(parts)


def note(x, y, text):
    return f'<text class="tl" x="{x}" y="{y}" text-anchor="middle">{esc(text)}</text>'


def svg(width, height, label, body, theme):
    c = THEMES[theme]
    style = (
        f"text{{font-family:{SANS};fill:{c['fg']}}}"
        ".tt{font-size:13px;font-weight:600}"
        f".tm,.tma{{font:600 12px {MONO};fill:{c['fg']}}}.tma{{fill:{c['auto']}}}"
        f".ts{{font-size:11.5px;fill:{c['muted']}}}.tl{{font-size:11.5px;font-style:italic;fill:{c['muted']}}}"
        f"rect{{stroke-width:1.5}}.file{{fill:{c['file']};stroke:{c['line']}}}"
        f".auto,.out{{fill:{c['auto_bg']};stroke:{c['auto']}}}.out{{stroke-width:3.2}}"
        f".gate{{fill:{c['gate_bg']};stroke:{c['gate']};stroke-dasharray:5 3}}"
        f".bot{{fill:{c['bot_bg']};stroke:{c['bot']}}}.panel{{fill:none;stroke:{c['line']};stroke-width:1;stroke-dasharray:2 3}}"
        f".rule{{stroke:{c['line']}}}.edge{{fill:none;stroke:{c['muted']};stroke-width:1.4}}"
        f".edge.accent{{stroke:{c['auto']};stroke-width:2}}"
    )
    heads = "".join(
        f'<marker id="{id}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
        for id, color in (("h", c["muted"]), ("ha", c["auto"]))
    )
    pad = 16
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-pad} {width + 2 * pad} {height + 2 * pad}" '
        f'width="{width + 2 * pad}" height="{height + 2 * pad}" role="img" aria-label="{esc(label)}">'
        f"<style>{style}</style><defs>{heads}</defs>"
        f'<rect x="{-pad}" y="{-pad}" width="{width + 2 * pad}" height="{height + 2 * pad}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["line"]}" stroke-width="1"/>{body}</svg>\n'
    )


def placeholders():
    return 1000, 300, "".join([
        box(20, 30, 240, 66, "file", "bots/<slug>/*.md", ["you edit; has {{template_repo}}"], mono=True),
        box(20, 117, 240, 66, "file", "catalog/updater-skill.md", ["{{repo}}  {{slug}}  {{version}}"], mono=True),
        box(20, 204, 240, 66, "file", "catalog.toml", ["repo and template_repo values"], mono=True),
        box(330, 117, 170, 66, "auto", "catalog.py build", ["fills every {{key}}"], mono=True),
        edge([(260, 63), (328, 138)]),
        edge([(260, 150), (328, 150)]),
        edge([(260, 237), (328, 162)], "values", (300, 222), "end"),
        box(570, 30, 210, 66, "file", "bots/<slug>/bot.toml", ["fetched as written"], mono=True),
        box(570, 114, 210, 72, "out", "dist/<slug>.md", ["real URLs, no {{…}} left", "read at tag <slug>-v<ver>"], mono=True),
        box(570, 204, 210, 66, "file", "bots/<slug>/CHANGELOG.md", ["fetched as written"], mono=True),
        edge([(500, 150), (568, 150)], "writes", (534, 142), accent=True),
        box(850, 90, 130, 120, "bot", "Installed bot", ["daily update", "check"]),
        edge([(780, 63), (848, 115)], "version", (806, 80)),
        edge([(780, 150), (848, 150)], "applies", (814, 142), accent=True),
        edge([(780, 237), (848, 185)], "shows", (806, 230)),
    ])


def pull_requests():
    return 870, 400, "".join([
        box(20, 40, 150, 66, "file", "PR from a branch", ["in this repo"]),
        box(210, 40, 200, 66, "auto", "Build workflow", ["regenerates README, dist,", "avatars, then commits"]),
        box(450, 40, 160, 66, "auto", "check.sh", ["tests, check, gitleaks"], mono=True),
        box(650, 40, 200, 66, "auto", "Push + post statuses", ["check and fork-check", "deletes held runs"]),
        edge([(170, 73), (208, 73)]),
        edge([(410, 73), (448, 73)]),
        edge([(610, 73), (648, 73)]),
        box(20, 190, 150, 66, "file", "PR from a fork", ["can't be pushed to"]),
        box(210, 190, 200, 66, "auto", "Fork check", ["trusted scripts read the PR", "bots only, no share_url"]),
        box(450, 190, 160, 66, "gate", "Moved by Manager", ["after your yes"]),
        edge([(170, 223), (208, 223)]),
        edge([(410, 223), (448, 223)], "passed", (429, 215)),
        edge([(530, 190), (530, 150), (95, 150), (95, 108)], "re-opened as a branch here", (312, 143)),
        box(210, 320, 200, 66, "gate", "Merge to master", ["both checks green", "and your yes"]),
        box(450, 320, 160, 66, "auto", "Release workflow", ["check --generated"]),
        box(650, 320, 200, 66, "out", "Tag <slug>-v<ver>", ["each unreleased bot", "can't move or be deleted"]),
        edge([(750, 106), (750, 285), (310, 285), (310, 318)], "required checks", (530, 278), accent=True),
        edge([(410, 353), (448, 353)]),
        edge([(610, 353), (648, 353)]),
    ])


def update_check():
    xs = [10 + i * 166 for i in range(6)]
    steps = [("bot", "Checks on?", ["auto_update memory"]), ("bot", "Read version", ["master bot.toml"]),
             ("bot", "Newer?", ["and not skipped"]), ("bot", "Fetch bundle", ["dist at the new tag"]),
             ("bot", "Compare", ["bundle vs. itself,", "then changelog"]), ("gate", "Ask the user", ["never updates alone"])]
    exits = {0: ("off", "Stop", ["unless asked"]), 1: ("not found", "Tell the user", ["bot or repo is gone"]),
             2: ("no", "Stop quietly", []), 3: ("not tagged yet", "Try tomorrow", []),
             5: ("answer", "Your answer", ["update, skip, off"])}
    parts = []
    for i, (kind, title, subs) in enumerate(steps):
        parts.append(box(xs[i], 30, 135, 70, kind, title, subs))
        if i:
            parts.append(edge([(xs[i - 1] + 135, 65), (xs[i] - 2, 65)]))
    for i, (label, title, subs) in exits.items():
        parts.append(box(xs[i], 180, 135, 58, "out" if i == 5 else "file", title, subs))
        parts.append(edge([(xs[i] + 67, 100), (xs[i] + 67, 178)], label, (xs[i] + 75, 145), "start", accent=i == 5))
    return 990, 260, "".join(parts)


def setup():
    template = [('repo = "JaxonWright/…-template"', False), ("template = true", False),
                ('template_repo = "JaxonWright/…"', False), ("bots/catalog-manager/", False)]
    return 950, 230, "".join([
        card(10, 20, 250, 170, "Template repo", template),
        card(350, 20, 250, 170, "Your copy, just made", [(text, i < 2) for i, (text, _) in enumerate(template)]),
        card(690, 20, 250, 170, "After Set up catalog", [('repo = "you/bot-catalog-for-…"', True), ("template = false", True),
                                                         ('template_repo = "JaxonWright/…"', False), ("catalog-manager removed", True)]),
        edge([(260, 105), (348, 105)], ["Use this", "template"], (304, 82)),
        edge([(600, 105), (688, 105)], ["Set up", "catalog run"], (644, 82), accent=True),
        note(475, 215, "still says it's the template"),
        note(815, 215, "{{template_repo}} still points home"),
    ])


def template_updates():
    return 960, 275, "".join([
        '<rect class="panel" x="10" y="20" width="300" height="240" rx="8"/>',
        '<text class="tt" x="26" y="44">Template repo, master</text>',
        box(26, 60, 268, 184, "auto", "template_paths", [".github/  scripts/  catalog/", "docs/  CONTRIBUTING.md",
                                                         "SECURITY.md  .gitignore", "assets/add-grok-bot.svg", "",
                                                         "listed in .github/", "template-files.txt"], mono=True),
        '<rect class="panel" x="470" y="20" width="300" height="240" rx="8"/>',
        '<text class="tt" x="486" y="44">Your catalog, master</text>',
        box(486, 60, 268, 100, "auto", "Template-owned copy", ["replaced on your yes;", "files the new list drops", "are deleted"]),
        box(486, 172, 268, 72, "file", "Yours, never touched", ["bots/  catalog.toml  README.md"]),
        edge([(294, 110), (484, 110)], ["Monday check finds a diff,", "opens a PR on your yes"], (390, 84), accent=True),
        box(810, 20, 140, 46, "auto", "Bump each bot", ["patch version"]),
        box(810, 84, 140, 46, "gate", "Merge", ["your yes"]),
        box(810, 148, 140, 46, "auto", "Release tags", []),
        box(810, 212, 140, 48, "bot", "Bots offer it", ["within a day"]),
        edge([(754, 90), (782, 90), (782, 43), (808, 43)]),
        edge([(880, 66), (880, 82)]),
        edge([(880, 130), (880, 146)]),
        edge([(880, 194), (880, 210)]),
    ])


def sharing():
    xs = [10 + i * 165 for i in range(6)]
    return 990, 265, "".join([
        box(xs[0], 30, 140, 70, "file", "Draft bots/<slug>/", ["personal details", "stripped"]),
        box(xs[1], 30, 140, 70, "gate", "Your yes", ["after reading", "every file"]),
        box(xs[2], 30, 140, 70, "auto", "PR + Build", ["dist/<slug>.md", "on the branch"]),
        box(xs[3], 30, 140, 70, "auto", "check", ["share_url set?"], mono=True),
        box(xs[4], 30, 140, 70, "gate", "Merge", ["same yes covers it"]),
        box(xs[5], 30, 140, 70, "out", "Release", ["tag + Add Grok Bot", "button in README"]),
        *[edge([(xs[i] + 140, 65), (xs[i + 1] - 2, 65)], accent=i == 3) for i in range(5)],
        box(xs[3], 180, 140, 70, "bot", "Publish copy", ["new Bot from branch", "dist, then share"]),
        box(xs[2], 180, 140, 70, "file", "Set share_url", ["in bot.toml on", "the same branch"]),
        edge([(xs[3] + 70, 100), (xs[3] + 70, 178)], "no link yet", (xs[3] + 78, 145), "start"),
        edge([(xs[3], 215), (xs[2] + 142, 215)]),
        edge([(xs[2] + 70, 180), (xs[2] + 70, 102)], "push", (xs[2] + 62, 145), "end"),
    ])


def legend():
    keys = [("file", "File in the repo"), ("auto", "Script or workflow"), ("out", "What it produces"),
            ("bot", "A Grok Bot acting"), ("gate", "Waits for your yes")]
    parts = []
    for i, (kind, label) in enumerate(keys):
        x = i * 176
        parts.append(f'<rect class="{kind}" x="{x}" y="4" width="34" height="22" rx="4"/>')
        parts.append(f'<text class="ts" x="{x + 44}" y="20">{esc(label)}</text>')
    return 860, 30, "".join(parts)


DIAGRAMS = {
    "legend": (legend, "Key: a gray box is a file in the repository, a teal box is a script or workflow, a thick teal box "
               "is what it produces, a blue box is a Grok Bot acting, and a dashed orange box waits for your yes."),
    "placeholders": (placeholders, "Files with placeholders go through catalog.py build into dist. "
                     "The installed bot reads only bot.toml, the dist bundle, and the changelog."),
    "pull-requests": (pull_requests, "Pull requests from this repo go through Build and forks through Fork check. "
                      "Both checks pass before a merge, then Release tags each new version."),
    "update-check": (update_check, "The daily update check stops at each failed step and updates only after the user says yes."),
    "setup": (setup, "catalog.toml in the template, in a fresh copy, and after the Set up catalog workflow runs."),
    "template-updates": (template_updates, "Template-owned files reach a catalog by pull request, which bumps and releases its bots."),
    "sharing": (sharing, "A new bot's check fails until a public copy is made from the branch and its share link is committed."),
}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for name, (draw, label) in DIAGRAMS.items():
        width, height, body = draw()
        for theme in THEMES:
            (OUT / f"{name}-{theme}.svg").write_text(svg(width, height, label, body, theme))
    print("\n".join(too_wide) or f"Drew {len(DIAGRAMS)} diagrams in {OUT.relative_to(OUT.parent.parent)}")
    return 1 if too_wide else 0


if __name__ == "__main__":
    raise SystemExit(main())
