# Make your own catalog by hand

The [Catalog Manager](../README.md#bots) bot does all of this for you, and the README's [Make Your Own Catalog](../README.md#make-your-own-catalog) section has prompts for each step. This page is the same process for people who would rather click through it themselves, plus how the pieces fit together. For diagrams of each process, see [How the catalog works](how-it-works.md).

## How it fits together

- Each bot's source lives in `bots/<slug>/`. You only edit those files.
- The Build workflow runs on every pull request from a branch in the repository. It regenerates the README table, each bot's `avatar.svg`, and one install bundle per bot in `dist/<slug>.md`. Each bundle adds the shared update skill and daily routine from `catalog/`.
- Every pull request goes into `master` and changes one bot. Merging it is a release. The Release workflow tags each bot whose version changed as `<slug>-v<version>`.
- Every installed copy checks `master` once a day. When it finds a newer version, it shows its user the changelog and a diff link between the two tags, and updates only if they say yes. Users can turn the checks off or back on by asking the bot.

## 1. Create the catalog

1. On the template's GitHub page, click **Use this template**, then **Create a new repository**. Make it public, because installed bots read their updates from it.
2. In the new repository, open **Actions**, enable workflows if asked, and run **Set up catalog** on `master`. Leave its fields blank to be credited by your GitHub name and profile, or fill in your name, X handle, or GitHub username and a link. Pick a license for your bots too. The template's own files stay GPL-3.0. It points the catalog at your repository, removes the template note and the Catalog Manager, and regenerates everything.
3. Under **Settings > Rules > Rulesets**, choose **New ruleset > Import a ruleset** and import each file in `.github/rulesets/`: `protect-master.json` and `protect-release-tags.json`. From a terminal, `scripts/protect-repo.sh` does the same. GitHub only allows rulesets on public repositories unless you have a paid plan. Then turn on **Settings > Security > Private vulnerability reporting** so people can report problems privately, and **Settings > General > Automatically delete head branches** so merged pull request branches are cleaned up. Under **Settings > Actions > General**, choose **Require approval for all external contributors**, so a fork's own workflows can't run and report a fake Fork check. `scripts/protect-repo.sh` turns on all three too.
4. Optionally, under **Settings > Secrets and variables > Actions**, add a secret named `PRIVATE_DENYLIST` that lists your personal details one per line: names, emails, handles, addresses, employer. CI rejects any bot file that contains one. Anyone with write access to the repository can read it through a workflow on a branch of their own, so leave it out if that includes people who shouldn't see that list. Entries match whole words. Write an entry with its capital letters, like `Will`, to match only that case, or all lowercase to match any case.

To change the byline or title later, run **Set up catalog** again with new values before you protect `master`. After that, edit `author`, `author_url`, or `title` in `catalog.toml` through a pull request.

## 2. Add a bot

1. Copy the bot's description, skills, and routines out of Grok into a new `bots/<slug>/` folder, following [CONTRIBUTING.md](../CONTRIBUTING.md). Leave out the "Check for bot updates" skill and routine, because the catalog adds those.
2. Remove every personal detail before you commit. The repository is public from the first push.
3. Open a pull request into `master` from a branch in your repository. The Build workflow adds the generated files. The check then fails only because the new bot has no `share_url` yet.

## 3. Publish and release

1. Create a new Grok Bot and paste in: "Fetch `https://raw.githubusercontent.com/<you>/<catalog>/<branch>/dist/<slug>.md` and set yourself up exactly as its 'How to apply' section says." Set its name and avatar to match `bot.toml`.
2. In that bot, choose **Share > Create template > Public link**. Set the template's description to the `summary` in `bot.toml`, since that is what people see on the share link. Then copy the link.
3. Put the link in `share_url` in `bot.toml` on the same branch. If you change the bot's files after this, apply the new bundle to the published bot again and choose **Share > Update template**.
4. Merge the pull request once the check passes. That releases the bot.

## 4. Ship an update

1. Change the bot's files on a branch off `master`.
2. Bump `version` in `bot.toml`. Use patch for wording fixes, minor for new skills or routines, and major for changes in what the bot does on its own.
3. Add a changelog section for the new version. Users read it before they accept, so say what changes for them and name every new skill, routine, or permission.
4. Open a pull request into `master` and merge it once the check passes. That releases the update, and installed copies offer it within a day.
5. Optional: in your published bot, choose **Share > Update template** so new users start on the latest version.
