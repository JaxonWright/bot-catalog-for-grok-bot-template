# Contributing

Thanks for helping improve these bots. This catalog holds its owner's bots, so a pull request from a fork can suggest changes to a bot that's already here, but can't add a new one. To suggest a new bot, open a **Bot idea** issue, or [make your own catalog](README.md#make-your-own-catalog) and share it from there.

## Pull requests

- Open every pull request against `master`. It is the released catalog, and merging into it releases each bot whose version changed.
- Change one bot per pull request. Other bots may change only their version, changelog, and `avatar.svg`, as when a change to `catalog/` bumps every bot at once.
- The owner adds new bots themselves, from a branch in this repository. A new bot can't merge until they publish it and add its `share_url`.

## Changing a bot

Each bot lives in `bots/<slug>/`:

| File | What it holds |
| --- | --- |
| `bot.toml` | Name, version, one-line summary, avatar, and public share link (`https://x.ai/bot/...`). |
| `instructions.md` | The bot's description, meaning its standing instructions. |
| `skills/*.md` | One skill per file. The first line is `# Skill name`. |
| `routines/*.toml` | One routine per file, with `name`, `schedule`, and `instructions`. |
| `CHANGELOG.md` | One `## <version>` section per release. People read it before they accept an update. |
| `avatar.svg` | Generated from `avatar = { shape, color }` in `bot.toml`, with eyes that look around and blink. Don't edit it. |

A bot's name, each skill's name, and each routine's `name` and `schedule` are one line of plain text, with no links, `<`, `>`, `[`, `]`, or backticks. They appear outside code blocks in the README and the install bundle.

Set `avatar.shape` and `avatar.color` to the shape and color the bot has in Grok Bot. The names match Grok Bot's own, and a bot installed from the bundle sets its built-in default mark to them rather than generating a picture. The shapes are blob, pebble, bean, egg, squircle, tablet, capsule, cylinder, hex, gem, crystal, wedge, shield, dome, arch, cloud, teardrop, leaf, square, sparkle, clover, flower, heart, house, and star. The colors are black, brown, red, orange, yellow, green, cyan, blue, violet, magenta, and gray. As in Grok Bot, a black bot turns white in dark mode. Both lists live in [scripts/avatars.py](scripts/avatars.py). A bot with an uploaded picture can use `icon = "<file>"` with its own SVG, GIF, WebP, or PNG instead.

Any change to a bot needs a version bump in `bot.toml` and a matching changelog section. Write the changelog for the person deciding whether to update. Say what changes for them, and call out any new skill, routine, or permission.

Change only the files in the table above, apart from `avatar.svg`. You don't need to run anything. On a pull request from a branch in this repository, the Build workflow regenerates the README table, the avatar, and the install bundle in `dist/`. A fork's branch can't be pushed to, so a maintainer moves a fork's pull request into a branch here, keeping your commits and credit. A pull request from a fork can change only the files of bots already in `bots/`, and each must be a regular file, not a symlink.

If you work from a clone, `scripts/install-hooks.sh` adds a pre-commit hook. It runs the same validation and privacy check as CI before anything leaves your machine.

## Keep it generic

Everything here is public, and every copy of a bot reads it. Anything pushed, including branches, commits, and pull request text, is public right away and stays in history even if deleted later. CI checks after the push, so it can't take a leak back. Check your files before you push. CI checks every line and commit message a pull request adds, not only its final files. Every commit also shows its author's email. To keep yours private, commit with your GitHub `noreply` address. Never commit names, email addresses, account handles, addresses, internal links, or keys. If a bot needs something personal, have it ask the user once and remember the answer. The check rejects common patterns. Maintainers can also list their own personal strings in `.private-denylist` (git-ignored) and in the `PRIVATE_DENYLIST` repository secret. Each entry matches whole words only. An entry with a capital letter matches that exact case, and an all-lowercase entry matches any case. CI logs are public, so a `PRIVATE_DENYLIST` match doesn't say where it is. Find it with the same entries in `.private-denylist`.

Only the maintainers change `share_url`, because it decides which bot the README's **Add Grok Bot** button installs. The Fork check rejects a change to it from a fork, using this repository's own copy of the check. CI also warns about every new link in a bot's files, so reviewers can check where it points. When a pull request from this repository fails because a bot's `share_url` is missing or invalid, CI leaves one comment on it that says how to fix it, and updates that comment when it's fixed.

`catalog/` holds the update routine that ships inside every bot. A change there changes every bot's install bundle, so CI asks for a version bump on each bot that has a release. CI compares each bundle with the one in the bot's latest release tag and asks for a bump whenever they differ.
