# Make your own catalog by hand

The [Catalog Manager](../README.md#bots) bot does all of this for you, and the README's [Make Your Own Catalog](../README.md#make-your-own-catalog) section has prompts for each step. This page is the same process for people who would rather click through it themselves, plus how the pieces fit together.

## How it fits together

- Each bot's source lives in `bots/<slug>/`. You only edit those files.
- The Build workflow runs on every push to `dev`. It regenerates the README table, each bot's `avatar.svg`, and one install bundle per bot in `dist/<slug>.md`. Each bundle adds the shared update skill and daily routine from `catalog/`.
- Merging `dev` into `master` is a release. The Release workflow tags each bot whose version changed as `<slug>-v<version>`.
- Every installed copy checks `master` once a day. When it finds a newer version, it shows its user the changelog and a diff link between the two tags, and updates only if they say yes. Users can turn the checks off or back on by asking the bot.

## 1. Create the catalog

1. On the template's GitHub page, click **Use this template**, then **Create a new repository**. Make it public, because installed bots read their updates from it.
2. In the new repository, open **Actions**, enable workflows if asked, and run **Set up catalog** on `master`. Leave its fields blank to be credited by your GitHub name and profile, or fill in your name, X handle, or GitHub username and a link. Pick a license for your bots too. The template's own files stay GPL-3.0. It points the catalog at your repository, removes the template note and the Catalog Manager, regenerates everything, and creates `dev`.
3. Under **Settings > Rules > Rulesets**, choose **New ruleset > Import a ruleset** and import each file in `.github/rulesets/`: `protect-master.json`, `protect-dev.json`, and `protect-release-tags.json`. From a terminal, `scripts/protect-repo.sh` does the same. GitHub only allows rulesets on public repositories unless you have a paid plan. Then turn on **Settings > Security > Private vulnerability reporting** so people can report problems privately. Also turn on **Settings > General > Automatically delete head branches** so merged pull request branches are cleaned up; `scripts/protect-repo.sh` does this too.
4. Under **Settings > Secrets and variables > Actions**, add a secret named `PRIVATE_DENYLIST` that lists your personal details one per line: names, emails, handles, addresses, employer. CI rejects any bot file that contains one. Entries match whole words. Write an entry with its capital letters, like `Will`, to match only that case, or all lowercase to match any case.

To change the byline or title later, run **Set up catalog** again with new values before you protect `master`. After that, edit `author`, `author_url`, or `title` in `catalog.toml` through a pull request into `dev`.

## 2. Add a bot

1. Copy the bot's description, skills, and routines out of Grok into a new `bots/<slug>/` folder, following [CONTRIBUTING.md](../CONTRIBUTING.md). Leave out the "Check for bot updates" skill and routine, because the catalog adds those.
2. Remove every personal detail before you commit. The repository is public from the first push.
3. Open a pull request into `dev` and merge it once the check passes.

## 3. Release and publish

1. Open a pull request from `dev` into `master` and merge it once the check passes.
2. Create a new Grok Bot and paste in: "Fetch `https://raw.githubusercontent.com/<you>/<catalog>/master/dist/<slug>.md` and set yourself up exactly as its 'How to apply' section says." Set its name and avatar to match `bot.toml`.
3. In that bot, choose **Share > Create template > Public link** and copy the link.
4. Put the link in `share_url` in `bot.toml` through a pull request into `dev`, then release again. A change to `share_url` alone needs no version bump.

## 4. Ship an update

1. Change the bot's files on a branch off `dev`.
2. Bump `version` in `bot.toml`. Use patch for wording fixes, minor for new skills or routines, and major for changes in what the bot does on its own.
3. Add a changelog section for the new version. Users read it before they accept, so say what changes for them and name every new skill, routine, or permission.
4. Merge into `dev`, then release. Installed copies offer the update within a day.
5. Optional: in your published bot, choose **Share > Update template** so new users start on the latest version.
