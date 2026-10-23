#!/usr/bin/env python3
"""Build, check, and release the bots in this catalog. Run with no arguments for usage."""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

from avatars import COLORS, SHAPES, render_avatar
from model import (
    AVATAR_FILE, BOT_LICENSES, BOTS, DIST, README, ROOT, TEMPLATE_FILES, TEMPLATES, Bot, Catalog, Invalid, Routine, fence, substitute,
)
from readme import HEADER_INK, render_header, render_readme

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
ICON_TYPES = {".svg", ".gif", ".webp", ".png"}
ICON_NAME = re.compile(r"[\w-]+(\.[\w-]+)*")
SHARE_URL = re.compile(r"https://x\.ai/bot/[\w-]+")
LINK = re.compile(r"https?://[^\s)>\]\"'`]+")
# Characters that would start markdown or HTML in the bundle's headings and Schedule lines, which sit outside code blocks.
MARKUP = re.compile(r"[<>\[\]`]|https?://|www\.", re.I)

PRIVATE_PATTERNS = {
    # noreply addresses, like GitHub's and the Co-Authored-By trailer's, belong to nobody.
    "email address": re.compile(r"(?<![\w.+-])(?!noreply@)[\w.+-]+@(?!(?:example\.(?:com|org)|users\.noreply\.github\.com)\b)[\w-]+\.[\w.-]+"),
    "phone number": re.compile(r"(?<!\d)(?:\+?\d{1,2}[ .-])?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)|(?<![\w+])\+\d[\d .()-]{7,}\d"),
    "private IP address": re.compile(
        r"(?<![\d.])(?:(?:10|127)(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\.?\d)"
    ),
    "API key": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|xai-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{22,}|AKIA[0-9A-Z]{16})\b"),
}


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


def one_line(data: dict, key: str, where: str, limit: int) -> str:
    value = data[key]
    if not isinstance(value, str) or not value.strip() or len(value) > limit or not value.isprintable() or MARKUP.search(value):
        raise Invalid(f"{where}: {key} must be one line of plain text, up to {limit} characters, with no links, <, >, [, ], or `")
    return value.strip()


def load_routine(path: Path) -> Routine:
    data = read_toml(path)
    where = str(path.relative_to(ROOT))
    missing = {"name", "schedule", "instructions"} - data.keys()
    if missing:
        raise Invalid(f"{where} is missing {', '.join(sorted(missing))}")
    if not isinstance(data["instructions"], str):
        raise Invalid(f"{where}: instructions must be text")
    return Routine(one_line(data, "name", where, 80), one_line(data, "schedule", where, 120), data["instructions"].strip())


def load_skill(path: Path) -> tuple[str, str]:
    text = path.read_text().strip()
    first, _, body = text.partition("\n")
    if not first.startswith("# "):
        raise Invalid(f"{path.relative_to(ROOT)} must start with a '# Skill name' heading")
    return one_line({"name": first[2:]}, "name", str(path.relative_to(ROOT)), 80), body.strip()


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
    if not isinstance(meta["version"], str) or not SEMVER.match(meta["version"]):
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
    name = one_line(meta, "name", f"{where}/bot.toml", 60)
    if not isinstance(meta["summary"], str) or re.search(r"https?://|www\.", meta["summary"], re.I):
        raise Invalid(f"{where}/bot.toml: summary must be text with no links")
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
        name=name,
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
    # Older catalogs can carry keys the template has since dropped, like dev_branch.
    types = {f.name: type(f.default) if f.name != "repo" else str for f in fields(Catalog)}
    data = {k: v for k, v in read_toml(ROOT / "catalog.toml").items() if k in types}
    if "repo" not in data:
        raise Invalid("catalog.toml is missing repo")
    for key, value in data.items():
        if not isinstance(value, list if types[key] is tuple else types[key]):
            raise Invalid(f"catalog.toml: {key} has the wrong type")
    catalog = Catalog(**data | {"template_paths": tuple(data.get("template_paths", ()))})
    if catalog.bots_license not in BOT_LICENSES:
        raise Invalid(f"catalog.toml: bots_license must be one of {', '.join(BOT_LICENSES)}")
    return catalog


def link_problems() -> list[str]:
    """Symlinks and special files among what build reads and writes, which could pull in files like .git/config."""
    paths = [ROOT / "catalog.toml", README, BOTS, TEMPLATES, ROOT / "docs", ROOT / "assets", DIST]
    for directory in [p for p in paths if p.is_dir() and not p.is_symlink()]:
        for top, dirs, files in os.walk(directory):
            paths += [Path(top) / name for name in dirs + files]
    return [
        f"{path.relative_to(ROOT)} is a symlink or special file. Replace it with a regular file"
        for path in paths
        if path.exists() or path.is_symlink()
        if not (stat.S_ISDIR(path.lstat().st_mode) or stat.S_ISREG(path.lstat().st_mode))
    ]


def load_bots() -> list[Bot]:
    if not BOTS.exists():
        return []
    return [load_bot(d) for d in sorted(BOTS.iterdir()) if d.is_dir()]


def fill(template: str, catalog: Catalog, bot: Bot) -> str:
    values = {
        "repo": catalog.repo,
        "template_repo": catalog.template_repo,
        "slug": bot.slug,
        "name": bot.name,
        "version": bot.version,
    }
    return substitute(template, values)


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
        *(
            [
                f"4. Set your avatar with Grok Bot's built-in default mark: shape `{bot.avatar[0]}` and color `{bot.avatar[1]}`. "
                "Do not generate or upload a custom picture; if one is installed, clear it."
            ]
            if bot.avatar
            else []
        ),
        f"{5 if bot.avatar else 4}. Keep your memory, logins, and the user's settings.",
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


def expected_outputs(catalog: Catalog, bots: list[Bot]) -> dict[Path, str]:
    outputs = {README: render_readme(catalog, bots)}
    for theme in HEADER_INK:
        outputs |= render_header(catalog, theme)
    outputs |= {DIST / f"{bot.slug}.md": render_bundle(catalog, bot) for bot in bots}
    outputs |= {BOTS / bot.slug / AVATAR_FILE: render_avatar(*bot.avatar) for bot in bots if bot.avatar}
    if catalog.template:
        outputs[TEMPLATE_FILES] = render_template_files(catalog)
    return outputs


def render_template_files(catalog: Catalog) -> str:
    owned = set(git("ls-files", "--", *catalog.template_paths).splitlines()) | {str(TEMPLATE_FILES.relative_to(ROOT))}
    return (
        "# The files the template owns, written by scripts/catalog.py build in the template. Don't edit it.\n"
        "# Updating a catalog from the template deletes each file in its old copy of this list that the new copy drops.\n"
        + "".join(f"{path}\n" for path in sorted(owned))
    )


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


def changed_paths(base: str) -> list[str]:
    return git("diff", "--name-only", f"{base}...HEAD").split()


def fork_path_problems(base: str, outputs: dict[Path, str]) -> list[str]:
    """A fork may change bots, plus generated files only when they match what build would write."""
    generated = {str(path.relative_to(ROOT)): text for path, text in outputs.items()}
    problems = []
    for path in changed_paths(base):
        if path.startswith("bots/") and path not in generated:
            continue
        current = ROOT / path
        if path in generated and current.is_file() and current.read_text() == generated[path]:
            continue
        if path.startswith("dist/") and not current.exists():
            continue
        problems.append(
            f"{path}: a pull request from a fork can only change files in bots/. "
            "A maintainer makes changes to anything else, after reviewing them"
        )
    return problems


def tag_problems(branch: str) -> list[str]:
    """Release tags must sit on the release branch, so nobody can tag a version ahead of the Release workflow."""
    problems = []
    for tag in git("tag", "--list", "*-v*").split():
        if subprocess.run(["git", "merge-base", "--is-ancestor", tag, branch], cwd=ROOT, capture_output=True).returncode:
            problems.append(f"tag {tag} isn't on {branch}. Installed bots would install it, so delete it before its version is released")
    return problems


def scope_problems(base: str) -> list[str]:
    paths = changed_paths(base)
    slugs = sorted({p.split("/")[1] for p in paths if p.startswith("bots/") and p.count("/") >= 2})
    # A change to the shared update check or scripts bumps every bot at once.
    if len(slugs) > 1 and not any(p.startswith(("catalog/", "scripts/")) for p in paths):
        return [f"this pull request changes {len(slugs)} bots ({', '.join(slugs)}). Split it into one pull request per bot"]
    return []


def unpublished_problems(base: str, bots: list[Bot]) -> list[str]:
    return [
        f"bots/{bot.slug} is a new bot, so it needs share_url before it merges. "
        "The catalog's owner publishes it from this pull request and adds the link"
        for bot in bots
        if not bot.share_url and not text_at(base, f"bots/{bot.slug}/bot.toml")
    ]


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


@dataclass(frozen=True)
class Privacy:
    patterns: dict[str, re.Pattern]
    # PRIVATE_DENYLIST entries. CI logs are public, so a match never says which entry, file, or line it was.
    secret: tuple[re.Pattern, ...]

    def scan(self, lines: list[str], where: str) -> tuple[list[str], bool]:
        problems, secret_hit = [], False
        for number, line in enumerate(lines, 1):
            problems += [f"{where}:{number}: possible {label}" for label, pattern in self.patterns.items() if pattern.search(line)]
            secret_hit = secret_hit or any(pattern.search(line) for pattern in self.secret)
        return problems, secret_hit


def load_privacy() -> Privacy:
    def compile_terms(lines: list[str], label: str) -> dict[str, re.Pattern]:
        compiled = {}
        for i, term in enumerate(t.strip() for t in lines):
            if term and not term.startswith("#"):
                # Whole words only. An entry with a capital letter matches that exact case, so "Will" skips "will".
                flags = 0 if term != term.lower() else re.I
                compiled[f"{label} #{i + 1}"] = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", flags)
        return compiled

    local = ROOT / ".private-denylist"
    patterns = PRIVATE_PATTERNS | compile_terms(local.read_text().splitlines() if local.exists() else [], ".private-denylist entry")
    secret = compile_terms(os.environ.get("PRIVATE_DENYLIST", "").splitlines(), "PRIVATE_DENYLIST entry")
    return Privacy(patterns, tuple(secret.values()))


IMAGE_TYPES = {".png", ".gif", ".webp", ".jpg", ".jpeg"}
# EXIF can hold where and when a photo was taken, and XMP can hold names.
IMAGE_METADATA = (b"Exif\x00", b"<x:xmpmeta", b"eXIf")


def privacy_problems(privacy: Privacy) -> tuple[list[str], bool]:
    problems, secret_hit = [], False
    for path in sorted([*BOTS.rglob("*"), *TEMPLATES.rglob("*")]):
        where = str(path.relative_to(ROOT))
        if not path.is_file():
            continue
        if path.suffix.lower() in IMAGE_TYPES:
            if any(marker in path.read_bytes() for marker in IMAGE_METADATA):
                problems.append(f"{where} has EXIF or XMP metadata, which can include a location or names. Save it without metadata")
            continue
        found, hit = privacy.scan(path.read_text(errors="replace").splitlines(), where)
        problems, secret_hit = problems + found, secret_hit or hit
    return problems, secret_hit


def public_email(address: str) -> bool:
    allowed = {e.strip().lower() for e in re.split(r"[\s,]+", os.environ.get("PUBLIC_EMAILS", "")) if e.strip()}
    address = address.lower()
    return address.endswith("@users.noreply.github.com") or address == "noreply@github.com" or address in allowed


def history_problems(privacy: Privacy, since: str, generated: set[str]) -> tuple[list[str], list[str], bool]:
    """Every commit a pull request adds stays in master's history once it merges, even one a later commit undid."""
    problems, email_problems, secret_hit = [], [], False
    for line in git("log", "--format=%H%x09%ae%x09%ce", f"{since}..HEAD").splitlines():
        sha, *emails = line.split("\t")
        for kind, address in zip(("author", "committer"), emails):
            if not public_email(address):
                email_problems.append(
                    f"commit {sha[:7]}: its {kind} email isn't a GitHub noreply address. Commit with the noreply address "
                    "from https://github.com/settings/emails, or add the address to the PUBLIC_EMAILS repository variable"
                )
        found, hit = privacy.scan(git("log", "-1", "--format=%B", sha).splitlines(), f"commit {sha[:7]} message")
        problems, secret_hit = problems + found, secret_hit or hit
    log = git("log", "--no-merges", "--no-renames", "-p", "--unified=0", "--format=%x00%h", f"{since}..HEAD")
    for commit in log.split("\0")[1:]:
        sha, path, added = commit.split("\n", 1)[0], None, {}
        for line in commit.splitlines():
            if line.startswith("+++ "):
                path = line[6:] if line.startswith("+++ b/") else None
            elif line.startswith("+") and path and path not in generated and not path.startswith("dist/"):
                added.setdefault(path, []).append(line[1:])
        for path, lines in added.items():
            found, hit = privacy.scan(lines, f"commit {sha} {path} added line")
            problems, secret_hit = problems + found, secret_hit or hit
    return problems, email_problems, secret_hit


def cmd_build(_args) -> int:
    if problems := link_problems():
        raise Invalid(problems[0])
    for path, text in expected_outputs(load_catalog(), load_bots()).items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
    for stale in set(DIST.glob("*.md")) - {DIST / f"{b.slug}.md" for b in load_bots()}:
        stale.unlink()
    print("README.md and dist/ are up to date")
    return 0


REBUILD = (
    "The Build workflow regenerates it on pull request branches in this repository, "
    "or run python scripts/catalog.py build"
)


def warn(message: str, path: str | None = None) -> None:
    print(f"warning: {message}", file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning{f' file={path}' if path else ''}::{message}")


def cmd_check(args) -> int:
    if problems := link_problems():
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    catalog, bots = load_catalog(), load_bots()
    outputs = expected_outputs(catalog, bots)
    privacy = load_privacy()
    problems, secret_hit = privacy_problems(privacy)
    problems += version_problems(catalog, bots) + tag_problems(args.base or "HEAD")
    if args.generated:
        for path, text in outputs.items():
            if not path.exists() or path.read_text() != text:
                problems.append(f"{path.relative_to(ROOT)} is out of date. {REBUILD}")
        extra = set(DIST.glob("*.md")) - {DIST / f"{b.slug}.md" for b in bots}
        problems += [f"{p.relative_to(ROOT)} has no matching bot. {REBUILD}" for p in extra]
    if catalog.bots_license != "GPL-3.0" and not (ROOT / "LICENSE-BOTS").exists():
        problems.append(f"catalog.toml says the bots are {catalog.bots_license}, but LICENSE-BOTS is missing")
    if args.base:
        # Compare with where the branch started, so changes merged into master since then don't count as this one's.
        since = git("merge-base", args.base, "HEAD").strip()
        problems += scope_problems(args.base) + unpublished_problems(since, bots)
        found, email_problems, hit = history_problems(privacy, since, {str(p.relative_to(ROOT)) for p in outputs})
        problems, secret_hit = problems + found, secret_hit or hit
        if args.fork:
            # A contributor's email is theirs to share, so it's only a warning.
            for problem in email_problems:
                warn(problem)
            problems += fork_path_problems(args.base, outputs) + share_url_problems(since, bots)
        else:
            problems += email_problems
        for path, url in new_links(since, bots):
            warn(f"{path}: new link {url}. Make sure it belongs here before merging", path)
    if secret_hit:
        problems.append(
            "something matches an entry in the PRIVATE_DENYLIST secret. "
            "Find it with the same entries in a local .private-denylist file, or ask the Catalog Manager"
        )
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
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


def cmd_unreleased(args) -> int:
    # A new copy of the template still says it's the template until "Set up catalog" runs, so its bots aren't its own yet.
    repo = load_catalog().repo
    if args.repo and args.repo.lower() != repo.lower():
        print(f"catalog.toml says this is {repo}, not {args.repo}, so nothing is released until it's set up", file=sys.stderr)
        return 0
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
    check.add_argument("--base", help="git ref a pull request merges into, e.g. origin/master, to check what it changes")
    check.add_argument("--fork", action="store_true", help="the changes come from a fork, so only bots/ may change, and share_url must not")
    check.add_argument("--generated", action="store_true", help="also require README.md, avatars, and dist/ to be up to date")
    check.set_defaults(run=cmd_check)
    configure = commands.add_parser("configure", help="set catalog.toml values, then rebuild")
    for key in ("repo", "title", "author", "author_url"):
        configure.add_argument(f"--{key.replace('_', '-')}", dest=key)
    configure.add_argument("--bots-license", dest="bots_license", choices=list(BOT_LICENSES), help="license for the bots in this catalog")
    configure.add_argument("--template", choices=["true", "false"], help="show the README note that this repo is a template")
    configure.set_defaults(run=cmd_configure)
    unreleased = commands.add_parser("unreleased", help="print 'slug version' for each bot without a release tag")
    unreleased.add_argument("--repo", help="owner/name of this repository. Prints nothing unless catalog.toml's repo matches")
    unreleased.set_defaults(run=cmd_unreleased)
    notes = commands.add_parser("notes", help="print the changelog section for a bot's current version")
    notes.add_argument("slug")
    notes.set_defaults(run=cmd_notes)
    args = parser.parse_args()
    try:
        return args.run(args)
    except Invalid as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
