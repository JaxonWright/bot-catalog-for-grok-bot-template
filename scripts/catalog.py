#!/usr/bin/env python3
"""Build, check, and release the bots in this catalog. Run with no arguments for usage."""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from avatars import COLORS, DARK_MODE_STYLE, SHAPES, avatar_body
from wordmark import STROKE, bubble_word

# The fork check sets CATALOG_ROOT to a pull request's files, so this repository's own copy of the script reads them.
ROOT = Path(os.environ.get("CATALOG_ROOT") or Path(__file__).resolve().parent.parent).resolve()
BOTS = ROOT / "bots"
TEMPLATES = ROOT / "catalog"
DIST = ROOT / "dist"
README = ROOT / "README.md"
AVATAR_FILE = "avatar.svg"
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
PROMPTS = ROOT / "docs" / "prompts"
PLACEHOLDER_REPO = "YOUR-USER/bot-catalog-for-grok-bot"
HEADER_START = "<!-- header:start -->"
HEADER_END = "<!-- header:end -->"
BOTS_START = "<!-- bots:start -->"
BOTS_END = "<!-- bots:end -->"

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
ICON_TYPES = {".svg", ".gif", ".webp", ".png"}
ICON_NAME = re.compile(r"[\w-]+(\.[\w-]+)*")
SHARE_URL = re.compile(r"https://x\.ai/bot/[\w-]+")
LINK = re.compile(r"https?://[^\s)>\]\"'`]+")
BOT_LICENSES = {
    "GPL-3.0": ("GNU General Public License v3.0", "If you share a changed version, it must stay under the GPL-3.0 and include its source."),
    "MIT": ("MIT License", "Keep the copyright notice when you share them."),
    "Apache-2.0": ("Apache License 2.0", "Keep the notices and say what you changed when you share them."),
    "CC0-1.0": ("CC0 1.0 Universal public domain dedication", "There are no conditions."),
}

PRIVATE_PATTERNS = {
    "email address": re.compile(r"[\w.+-]+@(?!example\.(?:com|org)\b)[\w-]+\.[\w.-]+"),
    "phone number": re.compile(r"(?<!\d)(?:\+?\d{1,2}[ .-])?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)"),
    "private IP address": re.compile(
        r"(?<![\d.])(?:(?:10|127)(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\.?\d)"
    ),
    "API key": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|xai-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"),
}


@dataclass(frozen=True)
class Routine:
    name: str
    schedule: str
    instructions: str


@dataclass(frozen=True)
class Bot:
    slug: str
    name: str
    version: str
    summary: str
    icon: str
    avatar: tuple[str, str] | None
    share_url: str
    instructions: str
    skills: tuple[tuple[str, str], ...]
    routines: tuple[Routine, ...]
    changelog: dict[str, str]
    template_only: bool


@dataclass(frozen=True)
class Catalog:
    repo: str
    title: str
    author: str
    author_url: str
    template: bool
    template_repo: str
    template_paths: list[str]
    bots_license: str
    release_branch: str
    dev_branch: str


class Invalid(Exception):
    pass


def version_key(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in SEMVER.match(version).groups())


def parse_changelog(text: str) -> dict[str, str]:
    sections = re.split(r"^## +", text, flags=re.M)[1:]
    return {s.split("\n", 1)[0].strip(): s.split("\n", 1)[1].strip() if "\n" in s else "" for s in sections}


def read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Invalid(f"{path.relative_to(ROOT)}: {error}") from None


def load_routine(path: Path) -> Routine:
    data = read_toml(path)
    missing = {"name", "schedule", "instructions"} - data.keys()
    if missing:
        raise Invalid(f"{path.relative_to(ROOT)} is missing {', '.join(sorted(missing))}")
    return Routine(data["name"], data["schedule"], data["instructions"].strip())


def load_skill(path: Path) -> tuple[str, str]:
    text = path.read_text().strip()
    first, _, body = text.partition("\n")
    if not first.startswith("# "):
        raise Invalid(f"{path.relative_to(ROOT)} must start with a '# Skill name' heading")
    return first[2:].strip(), body.strip()


def load_bot(directory: Path) -> Bot:
    slug = directory.name
    where = f"bots/{slug}"
    if not SLUG.match(slug):
        raise Invalid(f"{where}: folder name must be lowercase words joined by hyphens")
    meta_path = directory / "bot.toml"
    if not meta_path.exists():
        raise Invalid(f"{where}: missing bot.toml")
    meta = read_toml(meta_path)
    missing = {"name", "version", "summary"} - meta.keys()
    if missing:
        raise Invalid(f"{where}/bot.toml is missing {', '.join(sorted(missing))}")
    if not SEMVER.match(meta["version"]):
        raise Invalid(f"{where}/bot.toml: version must look like 1.2.3")
    if ("avatar" in meta) == ("icon" in meta):
        raise Invalid(f"{where}/bot.toml: set either avatar = {{ shape, color }} or icon = \"<file>\", not both")
    avatar = None
    if "avatar" in meta:
        shape, color = meta["avatar"].get("shape"), meta["avatar"].get("color")
        if shape not in SHAPES:
            raise Invalid(f"{where}/bot.toml: avatar shape must be one of {', '.join(SHAPES)}")
        if color not in COLORS:
            raise Invalid(f"{where}/bot.toml: avatar color must be one of {', '.join(COLORS)}")
        avatar = (shape, color)
    else:
        icon = directory / meta["icon"]
        if not ICON_NAME.fullmatch(meta["icon"]) or icon.suffix.lower() not in ICON_TYPES or not icon.is_file():
            raise Invalid(f"{where}: icon must be an existing {'/'.join(sorted(ICON_TYPES))} file")
    if any(re.search(r"https?://|www\.", meta[key], re.I) for key in ("name", "summary")):
        raise Invalid(f"{where}/bot.toml: name and summary can't contain links")
    share_url = meta.get("share_url", "")
    if share_url and not SHARE_URL.fullmatch(share_url):
        raise Invalid(f"{where}/bot.toml: share_url must be empty or a Grok Bot share link like https://x.ai/bot/abc123")
    instructions_path = directory / "instructions.md"
    if not instructions_path.exists() or not instructions_path.read_text().strip():
        raise Invalid(f"{where}: instructions.md is missing or empty")
    changelog_path = directory / "CHANGELOG.md"
    changelog = parse_changelog(changelog_path.read_text()) if changelog_path.exists() else {}
    if meta["version"] not in changelog:
        raise Invalid(f"{where}/CHANGELOG.md needs a '## {meta['version']}' section")
    return Bot(
        slug=slug,
        name=meta["name"],
        version=meta["version"],
        summary=meta["summary"].strip(),
        icon=AVATAR_FILE if avatar else meta["icon"],
        avatar=avatar,
        share_url=share_url,
        instructions=instructions_path.read_text().strip(),
        skills=tuple(load_skill(p) for p in sorted((directory / "skills").glob("*.md"))),
        routines=tuple(load_routine(p) for p in sorted((directory / "routines").glob("*.toml"))),
        changelog=changelog,
        template_only=bool(meta.get("template_only", False)),
    )


def load_catalog() -> Catalog:
    catalog = Catalog(**read_toml(ROOT / "catalog.toml"))
    if catalog.bots_license not in BOT_LICENSES:
        raise Invalid(f"catalog.toml: bots_license must be one of {', '.join(BOT_LICENSES)}")
    return catalog


def load_bots() -> list[Bot]:
    if not BOTS.exists():
        return []
    return [load_bot(d) for d in sorted(BOTS.iterdir()) if d.is_dir()]


def fill(template: str, catalog: Catalog, bot: Bot) -> str:
    values = {
        "repo": catalog.repo,
        "template_repo": catalog.template_repo,
        "release_branch": catalog.release_branch,
        "slug": bot.slug,
        "name": bot.name,
        "version": bot.version,
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)


def fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`{3,}", text)), default=2)
    ticks = "`" * (longest + 1)
    return f"{ticks}markdown\n{text}\n{ticks}"


def render_bundle(catalog: Catalog, bot: Bot) -> str:
    header = fill((TEMPLATES / "description-header.md").read_text().strip(), catalog, bot)
    updater_skill = load_skill(TEMPLATES / "updater-skill.md")
    updater_routine = load_routine(TEMPLATES / "updater-routine.toml")
    skills = tuple((name, fill(body, catalog, bot)) for name, body in bot.skills + (updater_skill,))
    routines = tuple(
        Routine(r.name, r.schedule, fill(r.instructions, catalog, bot)) for r in bot.routines + (updater_routine,)
    )

    out = [
        f"<!-- Generated by scripts/catalog.py from bots/{bot.slug}. Do not edit. -->",
        f"# {bot.name} {bot.version}",
        "",
        "## How to apply",
        "",
        "This bundle is the complete definition of the bot. To install or update it:",
        "",
        "1. Replace your description with the Description block below, word for word.",
        "2. Make your skills match the Skills section. Add or overwrite each one by name, and delete any skill from an older version of this bundle that is no longer listed.",
        "3. Make your routines match the Routines section the same way. Keep any routine the user created themselves.",
        "4. Keep your memory, logins, and the user's settings.",
        "",
        "## Description",
        "",
        fence(f"{header}\n\n{fill(bot.instructions, catalog, bot)}"),
        "",
        "## Skills",
    ]
    for name, body in skills:
        out += ["", f"### {name}", "", fence(body)]
    out += ["", "## Routines"]
    for routine in routines:
        out += ["", f"### {routine.name}", "", f"Schedule: {routine.schedule}", "", fence(routine.instructions)]
    return "\n".join(out) + "\n"


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
# Each header is drawn for one theme, so only a bot's own avatar follows the viewer's mode.
AVATAR_STYLE = ANIMATION_STYLE + DARK_MODE_STYLE


def render_avatar(shape: str, color: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60" width="128" height="128">'
        f"<style>{AVATAR_STYLE}</style>{avatar_body(shape, color)}</svg>\n"
    )


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
        "dev_branch": catalog.dev_branch,
    }

    def prompt(name: str) -> str:
        text = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], (PROMPTS / f"{name}.md").read_text().strip())
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
        "It reads the bot's full definition, strips anything personal, and shows you every file plus what it removed. After your yes, it does the rest. It adds the bot to your catalog and releases it. For a new bot, it also creates the public copy that carries the update check and puts its **Add Grok Bot** button in the README. People who already added the bot are offered the update within a day.",
        *fallback(catalog, "Without the Catalog Manager, paste this into the bot you want to share.", "share-bot", "2-share-a-bot", "the bot you want to share"),
        "",
        "Merged a pull request from someone else? Tell your Catalog Manager *Release my catalog* to send it out.",
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


def expected_outputs(catalog: Catalog, bots: list[Bot]) -> dict[Path, str]:
    outputs = {README: render_readme(catalog, bots)}
    for theme in HEADER_INK:
        outputs |= render_header(catalog, theme)
    outputs |= {DIST / f"{bot.slug}.md": render_bundle(catalog, bot) for bot in bots}
    outputs |= {BOTS / bot.slug / AVATAR_FILE: render_avatar(*bot.avatar) for bot in bots if bot.avatar}
    return outputs


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def version_problems(catalog: Catalog, bots: list[Bot]) -> list[str]:
    tags = git("tag", "--list", "*-v*").split()
    problems = []
    for bot in bots:
        released = [t.removeprefix(f"{bot.slug}-v") for t in tags if t.startswith(f"{bot.slug}-v")]
        released = [v for v in released if SEMVER.match(v)]
        if not released:
            continue
        latest = max(released, key=version_key)
        if version_key(bot.version) < version_key(latest):
            problems.append(f"bots/{bot.slug}: version {bot.version} is behind the released {latest}")
        elif bot.version == latest and text_at(f"{bot.slug}-v{latest}", f"dist/{bot.slug}.md") != render_bundle(catalog, bot):
            problems.append(
                f"bots/{bot.slug}: its install bundle changed since the {latest} release, "
                "so bump version and add a changelog section"
            )
    return problems


def text_at(ref: str, path: str) -> str:
    try:
        return git("show", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        return ""


def share_url_problems(base: str, bots: list[Bot]) -> list[str]:
    problems = []
    for bot in bots:
        old = tomllib.loads(text_at(base, f"bots/{bot.slug}/bot.toml") or "").get("share_url", "")
        if bot.share_url != old:
            problems.append(
                f"bots/{bot.slug}/bot.toml: share_url can only change in a pull request from this repository, "
                "because it decides which bot the Add Grok Bot button installs"
            )
    return problems


def new_links(base: str, bots: list[Bot]) -> list[tuple[str, str]]:
    found = []
    for bot in bots:
        for path in sorted((BOTS / bot.slug).rglob("*")):
            if not path.is_file() or path.suffix.lower() in {".svg", ".png", ".gif", ".webp"}:
                continue
            relative = str(path.relative_to(ROOT))
            before = set(LINK.findall(text_at(base, relative)))
            found += [(relative, url) for url in sorted(set(LINK.findall(path.read_text())) - before)]
    return found


def privacy_problems() -> list[str]:
    patterns = dict(PRIVATE_PATTERNS)
    denylist = os.environ.get("PRIVATE_DENYLIST", "").splitlines()
    local = ROOT / ".private-denylist"
    if local.exists():
        denylist += local.read_text().splitlines()
    for i, term in enumerate(t.strip() for t in denylist):
        if term and not term.startswith("#"):
            # Whole words only. An entry with a capital letter matches that exact case, so "Will" skips "will".
            flags = 0 if term != term.lower() else re.I
            patterns[f"private denylist entry #{i + 1}"] = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", flags)

    problems = []
    for path in sorted([*BOTS.rglob("*"), *TEMPLATES.rglob("*")]):
        if not path.is_file() or path.suffix.lower() in {".png", ".gif", ".webp"}:
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for label, pattern in patterns.items():
                if pattern.search(line):
                    problems.append(f"{path.relative_to(ROOT)}:{number}: possible {label}")
    return problems


def cmd_build(_args) -> int:
    for path, text in expected_outputs(load_catalog(), load_bots()).items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
    for stale in set(DIST.glob("*.md")) - {DIST / f"{b.slug}.md" for b in load_bots()}:
        stale.unlink()
    print("README.md and dist/ are up to date")
    return 0


def cmd_check(args) -> int:
    catalog, bots = load_catalog(), load_bots()
    problems = privacy_problems() + version_problems(catalog, bots)
    if args.generated:
        for path, text in expected_outputs(catalog, bots).items():
            if not path.exists() or path.read_text() != text:
                problems.append(f"{path.relative_to(ROOT)} is out of date. The Build workflow regenerates it on {catalog.dev_branch}")
        extra = set(DIST.glob("*.md")) - {DIST / f"{b.slug}.md" for b in bots}
        problems += [f"{p.relative_to(ROOT)} has no matching bot. The Build workflow removes it on {catalog.dev_branch}" for p in extra]
    if catalog.bots_license != "GPL-3.0" and not (ROOT / "LICENSE-BOTS").exists():
        problems.append(f"catalog.toml says the bots are {catalog.bots_license}, but LICENSE-BOTS is missing")
    if args.base:
        if args.fork:
            problems += share_url_problems(args.base, bots)
        for path, url in new_links(args.base, bots):
            print(f"warning: {path}: new link {url}")
            if os.environ.get("GITHUB_ACTIONS"):
                print(f"::warning file={path}::New link {url}. Make sure it belongs here before merging.")
    for problem in problems:
        print(f"error: {problem}")
    if not problems:
        print(f"ok: {len(bots)} bot(s) checked")
    return 1 if problems else 0


def cmd_configure(args) -> int:
    path = ROOT / "catalog.toml"
    text = path.read_text()
    for key in ("repo", "title", "author", "author_url", "template", "bots_license"):
        value = getattr(args, key)
        if key == "template" and value is not None:
            value = value == "true"
        if value is not None:
            text = re.sub(rf"^{key} = .*$", lambda _: f"{key} = {json.dumps(value, ensure_ascii=False)}", text, count=1, flags=re.M)
    path.write_text(text)
    if not load_catalog().template:
        for bot in load_bots():
            if bot.template_only:
                shutil.rmtree(BOTS / bot.slug)
    return cmd_build(args)


def cmd_unreleased(_args) -> int:
    tags = set(git("tag", "--list").split())
    for bot in load_bots():
        if f"{bot.slug}-v{bot.version}" not in tags:
            print(bot.slug, bot.version)
    return 0


def cmd_notes(args) -> int:
    bot = load_bot(BOTS / args.slug)
    print(bot.changelog[bot.version])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    commands.add_parser("build", help="regenerate README.md's bot table and dist/").set_defaults(run=cmd_build)
    check = commands.add_parser("check", help="validate bots, privacy, and generated files")
    check.add_argument("--base", help="git ref to compare against for new links and share_url changes, e.g. origin/dev")
    check.add_argument("--fork", action="store_true", help="the changes come from a fork, so share_url must not change")
    check.add_argument("--generated", action="store_true", help="also require README.md, avatars, and dist/ to be up to date")
    check.set_defaults(run=cmd_check)
    configure = commands.add_parser("configure", help="set catalog.toml values, then rebuild")
    for key in ("repo", "title", "author", "author_url"):
        configure.add_argument(f"--{key.replace('_', '-')}", dest=key)
    configure.add_argument("--bots-license", dest="bots_license", choices=list(BOT_LICENSES), help="license for the bots in this catalog")
    configure.add_argument("--template", choices=["true", "false"], help="show the README note that this repo is a template")
    configure.set_defaults(run=cmd_configure)
    commands.add_parser("unreleased", help="print 'slug version' for each bot without a release tag").set_defaults(run=cmd_unreleased)
    notes = commands.add_parser("notes", help="print the changelog section for a bot's current version")
    notes.add_argument("slug")
    notes.set_defaults(run=cmd_notes)
    args = parser.parse_args()
    try:
        return args.run(args)
    except Invalid as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
