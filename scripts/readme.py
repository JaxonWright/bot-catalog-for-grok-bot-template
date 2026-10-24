"""The README: its header art, bot table, and the generated sections between its marker comments."""

import html
import re
from pathlib import Path

from avatars import ANIMATION_STYLE, INK, avatar_body
from model import BOT_LICENSES, PROMPTS, README, ROOT, TEMPLATES, Bot, Catalog, fence, substitute
from wordmark import STROKE, bubble_word

NOTE_START = "<!-- template-note:start -->"
NOTE_END = "<!-- template-note:end -->"
LICENSE_START = "<!-- license:start -->"
LICENSE_END = "<!-- license:end -->"
MAINTAIN_START = "<!-- maintain:start -->"
MAINTAIN_END = "<!-- maintain:end -->"
IMPROVE_START = "<!-- improve:start -->"
IMPROVE_END = "<!-- improve:end -->"
GUIDE_START = "<!-- guide:start -->"
GUIDE_END = "<!-- guide:end -->"
PLACEHOLDER_REPO = "YOUR-USER/bot-catalog-for-grok-bot"
# The README's generated prose, with {{key}} placeholders.
PROSE = TEMPLATES / "readme"
HEADER_START = "<!-- header:start -->"
HEADER_END = "<!-- header:end -->"
BOTS_START = "<!-- bots:start -->"
BOTS_END = "<!-- bots:end -->"


# (shape, color, x, y, size, animation offset in seconds). Drawn in order, so later ones sit in front.
HEADER_GROUP = (
    ("teardrop", "violet", 92, 0, 64, 5.7),
    ("cloud", "orange", 12, 8, 70, 2.1),
    ("hex", "blue", 0, 80, 70, 0.0),
    ("squircle", "green", 106, 86, 66, 1.2),
    # "wordmark" takes the wordmark's color, so this bot is dark in the light header and white in the dark one.
    ("circle", "wordmark", 42, 44, 88, 4.3),
)
HEADER_INK = {"light": INK, "dark": "#E6EDF3"}
SANS = "-apple-system, Segoe UI, Helvetica, Arial, sans-serif"
# Pixels per bubble-letter grid unit, and the distance between stacked words.
WORDMARK_SCALE = 4.2
WORDMARK_LINE = 16 * WORDMARK_SCALE
WORDMARK_COLOR = {"light": "ink", "dark": "white"}


def render_header(catalog: Catalog, theme: str) -> dict[Path, str]:
    logo, byline, _, _ = draw_header(catalog, theme)
    return {ROOT / "assets" / f"header-{theme}.svg": logo, ROOT / "assets" / f"byline-{theme}.svg": byline}


def draw_header(catalog: Catalog, theme: str) -> tuple[str, str, int, int]:
    """The logo and the "<author>'s" line above it, drawn the same width so the line starts where the title does, and the logo's size.

    The logo is the avatar group beside the title, with each word before " for " stacked in bubble letters and the rest under them.
    """
    ink = HEADER_INK[theme]
    lead, _, rest = catalog.title.partition(" for ")
    rows, row_widths, offset, descender = [], [], 0, None
    for i, word in enumerate(lead.split()):
        top = i * WORDMARK_LINE
        bubbles = bubble_word(word, WORDMARK_COLOR[theme], offset, theme)
        if bubbles:
            drawing, width, descender = bubbles
            rows.append(f'<g transform="translate(0 {top:g}) scale({WORDMARK_SCALE})">{drawing}</g>')
            row_widths.append(width * WORDMARK_SCALE)
        else:
            descender = 0
            rows.append(
                f'<text y="{top + 12.6 * WORDMARK_SCALE:g}" fill="{ink}" stroke="none" font-family="{SANS}" '
                f'font-size="{14 * WORDMARK_SCALE:g}" font-weight="700">{html.escape(word)}</text>'
            )
            row_widths.append(len(word) * 8.6 * WORDMARK_SCALE)
        offset += len(word)
    last_top = (len(rows) - 1) * WORDMARK_LINE
    text_height = last_top + (13.5 + STROKE) * WORDMARK_SCALE
    if rest:
        tagline_width = len(rest) * 12 + 40
        # The tagline tucks just under the letters unless a descender hangs over it.
        clear = descender is None or descender * WORDMARK_SCALE > tagline_width + 8
        baseline = last_top + (10 + STROKE) * WORDMARK_SCALE + 27 if clear else text_height + 18
        text_height = max(text_height, baseline + 6)
        rows.append(
            f'<text x="2" y="{baseline:g}" fill="{ink}" stroke="none" font-family="{SANS}" '
            f'font-size="22" font-weight="600">for {html.escape(rest)}</text>'
        )
        row_widths.append(tagline_width)
    group_width = max(x + size for _, _, x, _, size, _ in HEADER_GROUP)
    group_height = max(y + size for _, _, _, y, size, _ in HEADER_GROUP)
    height = round(max(text_height, group_height)) + 16
    text_x = group_width + 32
    width = round(text_x + max(row_widths)) + 12
    avatars = "".join(
        f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 60 60" style="--d: -{delay}s">'
        f"{avatar_body(shape, WORDMARK_COLOR[theme] if color == 'wordmark' else color, theme)}</svg>"
        for shape, color, x, y, size, delay in HEADER_GROUP
    )
    logo = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{html.escape(catalog.title)}"><style>{ANIMATION_STYLE}</style>'
        f'<g transform="translate(0 {(height - group_height) / 2:g})">{avatars}</g>'
        f'<g transform="translate({text_x} {(height - text_height) / 2:g})" fill="none" stroke-width="{STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round">{"".join(rows)}</g></svg>\n'
    )
    owner = html.escape(f"{catalog.author or '<name>'}\u2019s")
    byline = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 30" width="{width}" height="30" role="img" aria-label="{owner}">'
        f'<text x="{text_x + 2}" y="23" fill="{ink}" font-family="{SANS}" font-size="22" font-weight="600">{owner}</text></svg>\n'
    )
    return logo, byline, width, height


SOCIAL_PREVIEW = ROOT / "assets" / "social-preview.svg"
SOCIAL_WIDTH, SOCIAL_HEIGHT = 1280, 640
SOCIAL_BACKGROUND = "#FFFFFF"
SOCIAL_MUTED = "#59636E"
TAGLINE = "Shareable Grok Bots that keep themselves up to date."
BYLINE_HEIGHT = 30


def render_social_preview(catalog: Catalog) -> dict[Path, str]:
    """The card link previews show: the light header and its byline, scaled up and centered over the tagline.

    GitHub takes only a PNG uploaded by hand, so Set up catalog draws this to social-preview.png beside it.
    The template has no author yet, so its card leaves out the byline rather than show "<name>'s".
    """
    logo, byline, width, height = draw_header(catalog, "light")
    byline_height = BYLINE_HEIGHT if catalog.author else 0
    scale = min(980 / width, 400 / (height + byline_height))
    tagline_gap, tagline_size = 64, 34
    block = (height + byline_height) * scale + tagline_gap
    top = (SOCIAL_HEIGHT - block) / 2
    art = f'<g transform="translate({(SOCIAL_WIDTH - width * scale) / 2:.1f} {top:.1f}) scale({scale:.4f})">'
    if catalog.author:
        art += byline
    art += f'<g transform="translate(0 {byline_height})">{logo}</g></g>'
    card = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SOCIAL_WIDTH} {SOCIAL_HEIGHT}" width="{SOCIAL_WIDTH}" height="{SOCIAL_HEIGHT}" '
        f'role="img" aria-label="{html.escape(catalog.title)}"><rect width="{SOCIAL_WIDTH}" height="{SOCIAL_HEIGHT}" fill="{SOCIAL_BACKGROUND}"/>{art}'
        f'<text x="{SOCIAL_WIDTH / 2:g}" y="{top + block:.0f}" text-anchor="middle" fill="{SOCIAL_MUTED}" font-family="{SANS}" '
        f'font-size="{tagline_size}" font-weight="500">{TAGLINE}</text></svg>\n'
    )
    return {SOCIAL_PREVIEW: card}


def render_byline(catalog: Catalog) -> str:
    owner = (
        '<picture>\n'
        '    <source media="(prefers-color-scheme: dark)" srcset="assets/byline-dark.svg">\n'
        f'    <img src="assets/byline-light.svg" alt="{html.escape(catalog.author or "<name>")}\u2019s">\n'
        '  </picture>'
    )
    if catalog.author_url:
        owner = f'<a href="{html.escape(catalog.author_url)}">{owner}</a>'
    return (
        f'<p align="center">\n  {owner}<br>\n  <picture>\n'
        '    <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg">\n'
        f'    <img src="assets/header-light.svg" alt="{html.escape(catalog.title)}">\n'
        '  </picture>\n</p>'
    )


# GitHub caps every README image at max-width: 100%, so a table squeezes images in narrow columns.
# A width on each icon and button cell holds those columns open. 26 covers GitHub's cell padding.
# GitHub also sets height: auto, so only an image's width attribute sizes it.
ICON_SIZE = 96
BUTTON_WIDTH = 164
ICON_CELL = ICON_SIZE + 26
BUTTON_CELL = BUTTON_WIDTH + 26


def render_table(catalog: Catalog, bots: list[Bot]) -> str:
    # Raw HTML, so markdown never runs on a bot's name or summary and escaping them is enough.
    rows = [
        "<table>",
        f'<tr><th width="{ICON_CELL}"></th><th>Bot</th><th>Description</th><th width="{BUTTON_CELL}"></th></tr>',
    ]
    for bot in bots:
        icon = f'<img src="bots/{bot.slug}/{bot.icon}" width="{ICON_SIZE}" height="{ICON_SIZE}" alt="">'
        name = f'<a href="bots/{bot.slug}"><b>{html.escape(bot.name)}</b></a><br><sub>v{bot.version}</sub>'
        if bot.share_url:
            add = (
                f'<a href="{html.escape(bot.share_url)}">'
                f'<img src="assets/add-grok-bot.svg" width="{BUTTON_WIDTH}" alt="Add Grok Bot"></a>'
            )
        else:
            add = "<sub>Not published yet</sub>"
        summary = html.escape(" ".join(bot.summary.split()))
        rows.append(
            f'<tr><td width="{ICON_CELL}" align="center">{icon}</td><td>{name}</td><td>{summary}</td>'
            f'<td width="{BUTTON_CELL}" align="center">{add}</td></tr>'
        )
    if not bots:
        rows.append("<tr><td></td><td><sub>No bots yet</sub></td><td></td><td></td></tr>")
    rows.append("</table>")
    return "\n".join(rows)


def replace_between(text: str, start_marker: str, end_marker: str, body: str, heading: str | None = None) -> str:
    """Replaces what sits between the markers with body.

    A catalog made before the template generated a section has no markers for it yet. If it has the section's
    heading, the markers go around the text under that heading, which the template wrote. Otherwise they go at the end.
    """
    if start_marker not in text or end_marker not in text:
        found = re.search(rf"^{re.escape(heading)}\n\n(.*?)(?=^## |\Z)", text, re.M | re.S) if heading else None
        if found:
            text = f"{text[:found.start(1)]}{start_marker}\n{end_marker}\n\n{text[found.end(1):]}"
        else:
            text = f"{text.rstrip()}\n\n{start_marker}\n{end_marker}\n"
    start, end = text.index(start_marker) + len(start_marker), text.index(end_marker)
    inner = f"\n{body}\n" if body else "\n"
    return f"{text[:start]}{inner}{text[end:]}"


def render_readme(catalog: Catalog, bots: list[Bot], readme: str | None = None) -> str:
    """Fills the generated sections of readme, the README.md on disk by default. Everything else stays as written."""
    text = replace_between(README.read_text() if readme is None else readme, HEADER_START, HEADER_END, render_byline(catalog))
    text = replace_between(text, NOTE_START, NOTE_END, prose("template-note") if catalog.template else "")
    text = replace_between(text, IMPROVE_START, IMPROVE_END, prose("improve"), heading="## Improve a Bot")
    text = replace_between(text, GUIDE_START, GUIDE_END, render_guide(catalog))
    text = replace_between(text, MAINTAIN_START, MAINTAIN_END, render_maintain(catalog))
    text = replace_between(text, LICENSE_START, LICENSE_END, render_license(catalog))
    return replace_between(text, BOTS_START, BOTS_END, render_table(catalog, bots))


def prose(name: str, **values: str) -> str:
    return substitute((PROSE / f"{name}.md").read_text().strip(), values)


def fallback(catalog: Catalog, summary: str, name: str, anchor: str, where: str) -> str:
    """The prompt that does a Catalog Manager step by hand, inline in the template and linked from every catalog."""
    text = (PROMPTS / f"{name}.md").read_text().strip()
    # Only the template carries the prompt text, so every catalog uses the version its maintainer keeps current.
    if catalog.template:
        values = {"repo": PLACEHOLDER_REPO, "template_repo": catalog.template_repo}
        prompt = fence(substitute(text, values)).replace("```markdown", "```text", 1)
        return f"<details><summary>{summary}</summary>\n\n{prompt}\n\n</details>"
    link = f"https://github.com/{catalog.template_repo}#{anchor}"
    swap = f" Change `{PLACEHOLDER_REPO}` in it to `{catalog.repo}`." if "{{repo}}" in text else ""
    return f"Rather not use the Catalog Manager? Paste [this prompt from the template]({link}) into {where}.{swap}"


def create_steps(catalog: Catalog, manager_link: str) -> str:
    summary = "Rather not add the Catalog Manager? Paste this into any Grok Bot instead."
    return prose(
        "create",
        manager_link=manager_link,
        fallback=fallback(catalog, summary, "create-catalog", "1-create-your-catalog", "any Grok Bot"),
    )


def manage_steps(catalog: Catalog, first: int) -> str:
    summary = "Without the Catalog Manager, paste this into the bot you want to share."
    return prose(
        "manage",
        first=str(first),
        second=str(first + 1),
        fallback=fallback(catalog, summary, "share-bot", "2-share-a-bot", "the bot you want to share"),
    )


def render_guide(catalog: Catalog) -> str:
    template = f"https://github.com/{catalog.template_repo}"
    if catalog.template:
        return prose("guide-template", create=create_steps(catalog, "the table above"), manage=manage_steps(catalog, 2))
    return prose("guide-catalog", template_url=template, create=create_steps(catalog, f"the [template's bot list]({template}#bots)"))


def render_license(catalog: Catalog) -> str:
    if catalog.bots_license == "GPL-3.0":
        return prose("license-gpl")
    name, condition = BOT_LICENSES[catalog.bots_license]
    return prose(
        "license-other",
        license_name=name,
        license_condition=condition,
        template_url=f"https://github.com/{catalog.template_repo}",
    )


def render_maintain(catalog: Catalog) -> str:
    if catalog.template:
        return ""
    return prose("maintain", template_url=f"https://github.com/{catalog.template_repo}", manage=manage_steps(catalog, 1))
