"""The catalog's data: where its files live, what a bot and a catalog hold, and the text helpers both builders use."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

# The fork check sets CATALOG_ROOT to a pull request's files, so this repository's own copy of the script reads them.
ROOT = Path(os.environ.get("CATALOG_ROOT") or Path(__file__).resolve().parent.parent).resolve()
BOTS = ROOT / "bots"
TEMPLATES = ROOT / "catalog"
DIST = ROOT / "dist"
README = ROOT / "README.md"
AVATAR_FILE = "avatar.svg"
# Every file the template owns. Catalogs keep the template's copy, so an update can tell which files the template removed.
TEMPLATE_FILES = ROOT / ".github" / "template-files.txt"
PROMPTS = ROOT / "docs" / "prompts"

BOT_LICENSES = {
    "GPL-3.0": ("GNU General Public License v3.0", "If you share a changed version, it must stay under the GPL-3.0 and include its source."),
    "MIT": ("MIT License", "Keep the copyright notice when you share them."),
    "Apache-2.0": ("Apache License 2.0", "Keep the notices and say what you changed when you share them."),
    "CC0-1.0": ("CC0 1.0 Universal public domain dedication", "There are no conditions."),
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
    # Template updates don't touch catalog.toml, so every key added after repo needs a default for older catalogs.
    repo: str
    title: str = "Bot Catalog for Grok Bot"
    author: str = ""
    author_url: str = ""
    template: bool = False
    template_repo: str = "JaxonWright/bot-catalog-for-grok-bot-template"
    template_paths: tuple[str, ...] = ()
    bots_license: str = "GPL-3.0"


class Invalid(Exception):
    pass


def substitute(text: str, values: dict[str, str]) -> str:
    """Fills each {{key}} in text from values. A key values doesn't have stays as written."""
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), text)


def fence(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`{3,}", text)), default=2)
    ticks = "`" * (longest + 1)
    return f"{ticks}markdown\n{text}\n{ticks}"
