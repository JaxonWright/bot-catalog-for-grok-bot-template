"""The README: its header art, bot table, and the generated sections between its marker comments."""

import html
from pathlib import Path

from avatars import ANIMATION_STYLE, avatar_body
from model import BOT_LICENSES, PROMPTS, README, ROOT, Bot, Catalog, fence, substitute
from wordmark import STROKE, bubble_word

NOTE_START = "<!-- template-note:start -->"
NOTE_END = "<!-- template-note:end -->"
TEMPLATE_NOTE = """> [!NOTE]
> This repository is a template. It is meant to be duplicated, so anyone can build their own shareable, self-updating catalog of Grok Bots. See [Make Your Own Catalog](#make-your-own-catalog)."""
LICENSE_START = "<!-- license:start -->"
LICENSE_END = "<!-- license:end -->"
MAINTAIN_START = "<!-- maintain:start -->"
MAINTAIN_END = "<!-- maintain:end -->"
GUIDE_START = "<!-- guide:start -->"
GUIDE_END = "<!-- guide:end -->"
PLACEHOLDER_REPO = "YOUR-USER/bot-catalog-for-grok-bot"
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
HEADER_INK = {"light": "#1F2328", "dark": "#E6EDF3"}
SANS = "-apple-system, Segoe UI, Helvetica, Arial, sans-serif"
# Pixels per bubble-letter grid unit, and the distance between stacked words.
WORDMARK_SCALE = 4.2
WORDMARK_LINE = 16 * WORDMARK_SCALE
WORDMARK_COLOR = {"light": "ink", "dark": "white"}


def render_header(catalog: Catalog, theme: str) -> dict[Path, str]:
    """The logo and the "<author>'s" line above it, drawn the same width so the line starts where the title does.

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
    return {ROOT / "assets" / f"header-{theme}.svg": logo, ROOT / "assets" / f"byline-{theme}.svg": byline}


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


def replace_between(text: str, start_marker: str, end_marker: str, body: str) -> str:
    start, end = text.index(start_marker) + len(start_marker), text.index(end_marker)
    inner = f"\n{body}\n" if body else "\n"
    return f"{text[:start]}{inner}{text[end:]}"


def render_readme(catalog: Catalog, bots: list[Bot]) -> str:
    text = replace_between(README.read_text(), HEADER_START, HEADER_END, render_byline(catalog))
    text = replace_between(text, NOTE_START, NOTE_END, TEMPLATE_NOTE if catalog.template else "")
    text = replace_between(text, GUIDE_START, GUIDE_END, render_guide(catalog))
    text = replace_between(text, MAINTAIN_START, MAINTAIN_END, render_maintain(catalog))
    text = replace_between(text, LICENSE_START, LICENSE_END, render_license(catalog))
    return replace_between(text, BOTS_START, BOTS_END, render_table(catalog, bots))


def guide_prompts(catalog: Catalog):
    repo = PLACEHOLDER_REPO if catalog.template else catalog.repo
    values = {
        "repo": repo,
        "template_repo": catalog.template_repo,
        "release_branch": catalog.release_branch,
    }

    def prompt(name: str) -> str:
        text = substitute((PROMPTS / f"{name}.md").read_text().strip(), values)
        return fence(text).replace("```markdown", "```text", 1)

    return repo, prompt


def fallback(catalog: Catalog, summary: str, name: str, anchor: str, where: str) -> list[str]:
    # Only the template carries the prompt text, so every catalog uses the version its maintainer keeps current.
    if catalog.template:
        _, prompt = guide_prompts(catalog)
        return ["", f"<details><summary>{summary}</summary>", "", prompt(name), "", "</details>"]
    link = f"https://github.com/{catalog.template_repo}#{anchor}"
    uses_repo = "{{repo}}" in (PROMPTS / f"{name}.md").read_text()
    swap = f" Change `{PLACEHOLDER_REPO}` in it to `{catalog.repo}`." if uses_repo else ""
    return ["", f"Rather not use the Catalog Manager? Paste [this prompt from the template]({link}) into {where}.{swap}"]


def create_steps(catalog: Catalog, manager_link: str) -> list[str]:
    return [
        f"Add the **Catalog Manager** from {manager_link}, then tell it *Set up my catalog*. It connects GitHub, creates your catalog from the template, protects its branches, and remembers which personal details must never be published. Nothing personal reaches GitHub without your yes in chat.",
    ] + fallback(catalog, "Rather not add the Catalog Manager? Paste this into any Grok Bot instead.", "create-catalog", "1-create-your-catalog", "any Grok Bot")


def manage_steps(catalog: Catalog, heading: str, first: int) -> list[str]:
    return [
        f"{heading} {first}. Share a Bot",
        "",
        "Tell your Catalog Manager *Share my &lt;bot name&gt;*. Say the same thing later to ship an improvement to a bot you already share.",
        "",
        "It reads the bot's full definition, strips anything personal, and shows you every file plus what it removed. After your yes, it does the rest. It opens a pull request for the bot. For a new bot, it also creates the public copy that carries the update check and adds its share link, so the bot appears in the README with its **Add Grok Bot** button. Merging the pull request releases the bot. People who already added the bot are offered the update within a day.",
        *fallback(catalog, "Without the Catalog Manager, paste this into the bot you want to share.", "share-bot", "2-share-a-bot", "the bot you want to share"),
        "",
        "Every day, your Catalog Manager checks for new issues and pull requests and tells you about them. When someone else's pull request adds a new bot, it asks you to publish the bot and add its share link before merging.",
        "",
        f"{heading} {first + 1}. Keep Up With the Template",
        "",
        "The template's workflows, scripts, and update check improve over time, and a catalog doesn't get those changes on its own. Tell your Catalog Manager *Update my catalog from the template*. It also checks every week and asks before it changes anything.",
        "",
        "Prefer to work by hand, or curious how the pieces fit together? See [docs/make-your-own.md](docs/make-your-own.md).",
    ]


def render_guide(catalog: Catalog) -> str:
    template = f"https://github.com/{catalog.template_repo}"
    if catalog.template:
        lines = ["### 1. Create Your Catalog", ""] + create_steps(catalog, "the table above") + [
            "",
            "Once your catalog exists, its README has a **Maintain This Catalog** section with the next steps.",
            "",
        ] + manage_steps(catalog, "###", 2)
    else:
        lines = [
            f"This catalog was made from the [Bot Catalog for Grok Bot template]({template}). To make your own, start from that template, not from this repository. A catalog made from the template gets its own setup workflow, its own bots, and its own update channel, and nothing in it depends on this one.",
            "",
        ] + create_steps(catalog, f"the [template's bot list]({template}#bots)")
    return "\n".join(lines)


def render_license(catalog: Catalog) -> str:
    gpl = "[GNU General Public License v3.0](LICENSE)"
    if catalog.bots_license == "GPL-3.0":
        return (
            f"The bots, scripts, and docs in this repo are licensed under the {gpl}. You can use, change, and share them. "
            "If you share a changed version, it must stay under the GPL-3.0 and include its source."
        )
    name, condition = BOT_LICENSES[catalog.bots_license]
    template = f"https://github.com/{catalog.template_repo}"
    return (
        f"The bots in `bots/` are licensed under the [{name}](LICENSE-BOTS). You can use, change, and share them. {condition}\n\n"
        f"The scripts, workflows, and docs come from the [Bot Catalog for Grok Bot template]({template}) and stay under the {gpl}."
    )


def render_maintain(catalog: Catalog) -> str:
    if catalog.template:
        return ""
    return "\n".join([
        "## Maintain This Catalog",
        "",
        f"For whoever runs this catalog. The [Catalog Manager](https://github.com/{catalog.template_repo}#bots) does each step when you ask it.",
        "",
    ] + manage_steps(catalog, "###", 1))
