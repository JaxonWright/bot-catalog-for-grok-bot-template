# Security

A bot catalog changes the instructions of every Grok Bot installed from it, and those bots act with their users' logins and connected apps. This page lists what can go wrong, what the catalog does about each risk, and the risks you accept by using it. It applies to the template and to every catalog made from it.

## Reporting a problem

Please don't open a public issue for a security problem. Use **Security > Report a vulnerability** on the repository instead, which reaches its maintainers privately. Catalog setup and `scripts/protect-repo.sh` turn that form on. A problem with the template itself, its workflows, scripts, update check, or Catalog Manager, goes to the [template repository](https://github.com/JaxonWright/bot-catalog-for-grok-bot-template/security).

## Risks and how they are handled

### Whoever controls a catalog controls its bots

Anyone who can push to a catalog's `master` branch can change what every installed copy of its bots is told to do, through an update. That includes an attacker who takes over a maintainer's GitHub account.

- **Handled.** An installed bot never updates on its own. It compares the new version with what it runs now and tells its user, in its own words, what would change, including anything the changelog leaves out. It also shows the changelog and a link to the full diff, and updates only after a yes. Once the rulesets in `.github/rulesets/` are imported, `master` only changes through a pull request that passes its required checks and merges with a merge commit. The one exception comes before that: "Set up catalog" pushes a single commit straight to `master` when the catalog is created. Release tags can't be moved or deleted, and the update check reads the changelog and bundle from the release tag itself, so what a user reviews is exactly what they install.
- **You accept.** If you approve an update without reading it, you are trusting the catalog's maintainer and their account security. Maintainers should use a hardware key or passkey for GitHub two-factor sign-in.
- **To opt out.** Tell any installed bot to turn automatic update checks off. It keeps its current version until you turn them back on.

### A moved or deleted release tag

Installed bots fetch each update from its release tag, `<slug>-v<version>`.

- **Handled.** The `protect-release-tags.json` ruleset blocks updating or deleting any `*-v*` tag. CI fails while any `*-v*` tag points outside `master`'s history, so a tag made by hand ahead of a release shows up before its version merges. The Release workflow tags nothing unless `master` passes the catalog check, including up-to-date install bundles and the tag rule above, and it runs one release at a time. It also tags nothing in a new copy of the template until "Set up catalog" points `catalog.toml` at that copy. Branches must be up to date with `master` before they merge, so a bundle built from an older update check can't slip in.
- **You accept.** Rulesets need a public repository or a paid GitHub plan, and repository admins can turn them off. A catalog without its rulesets imported has no tag protection and no required checks. Anyone with write access can still create tags. A tag made outside `master` in the seconds between a merge and its Release run would be installed before CI flags it, and a tag on `master` for a version that isn't released yet installs content that was already reviewed under the wrong version number. Give write access only to people you'd trust to ship an update.

### A pull request that adds harmful instructions

Anyone can propose changes to a bot. A change could quietly tell the bot to send data somewhere, or to act without asking.

- **Handled.** Every change needs a maintainer to merge it. CI warns about every new link in a bot's files, including ones written without `https://`. The Catalog Manager's triage calls out new permissions, routines, outside contacts, and links, and it treats everything written in issues and pull requests as data, never as instructions.
- **You accept.** A reviewer can miss something. Read the changelog and diff before you accept an update.

### A swapped Add Grok Bot link

A bot's `share_url` decides which bot the README's **Add Grok Bot** button installs. Pointing it at a look-alike bot would be easy to miss in review.

- **Handled.** The Fork check workflow rejects a pull request from a fork that adds or deletes a bot, changes a `share_url`, or changes anything outside `bots/` besides generated files, including `catalog.toml`, whose `repo` decides where every bot looks for updates, and the README's own text. It runs this repository's own copy of the check and only reads the fork's files, and `master` requires it, so the pull request can't switch it off. The Catalog Manager moves a fork's pull request into the repository only after its Fork check passes. Only the catalog's owner adds bots, and a new bot can't merge until they publish it and add the link. CI accepts only Grok Bot share links (`https://x.ai/bot/...`), so the button can't lead to another website. The README shows each bot's name and summary as plain text, and names must be one line with no links or markup, so neither can add a second button or link. Two bots can't have names that differ only by case or punctuation. The Catalog Manager's triage calls out any `share_url` change.
- **You accept.** A maintainer can still change it, so the button is only as trustworthy as the catalog's maintainers. A fork's own workflows could report a check named `fork-check`, so setup makes every outside contributor's workflow runs wait for a maintainer's approval. Never approve them. A fork's pull request is moved, never merged as it is, and the real Fork check runs without approval.

### Personal details published by mistake

The repository is public. Anything pushed to it, including branches, commits, and pull request text, is public right away and stays in its history even after it is deleted.

- **Handled.** The Catalog Manager and the share prompt draft everything in chat, list what they removed only there, and push nothing until the user approves. CI rejects email addresses, phone numbers, private IP addresses, API-key shapes, and anything in the maintainer's optional `PRIVATE_DENYLIST` secret, in the files under `bots/` and `catalog/` and in every line and commit message a pull request adds. Images can't carry EXIF or XMP metadata. CI logs are public, so a `PRIVATE_DENYLIST` match says only that something matched, never which entry, file, or line. gitleaks scans every commit for secrets.
- **You accept.** CI runs after a push, so it catches a leak but can't take it back. It doesn't check pull request text, commit names, or non-US phone numbers written without a `+` country code, and a pattern can't catch everything personal. Every commit shows its author's email. If you don't want yours public, commit with your GitHub `noreply` address and turn on "Keep my email addresses private" in GitHub's email settings. The approval in chat is the real safeguard. If something private is pushed, treat it as public. Rotate any key, and ask GitHub Support to purge cached views if needed.

### Tricking the Catalog Manager

The Catalog Manager reads text written by strangers, such as issues, pull requests, comments, and web pages, and it can push to a catalog.

- **Handled.** Its instructions treat all of that text as data. It never merges, releases, publishes, or deletes without the user's yes in chat, and a yes covers only the plan it showed. If its GitHub connection lets you choose repositories, limit it to the catalog repository.
- **You accept.** Language models can be manipulated in ways nobody predicted. The approval step is the main defense, so read what it asks you to approve.

### Template updates run code in your repository

"Update my catalog from the template" copies the template's workflows and scripts into a catalog, where they run with write access.

- **Handled.** The Catalog Manager shows every change to workflows and scripts in full and opens a pull request only after a yes. Nothing updates automatically. It deletes only the files the template's own file list says the template removed, never a file the catalog added.
- **You accept.** Accepting a template update means trusting the template's maintainer for that change.

### Workflow permissions

- **Handled.** CI runs on pull requests with a read-only token, and pull requests from forks get no secrets. The Fork check reads a fork's files but never runs them. Set up catalog runs only when someone starts it by hand. Release creates tags only from `master`, after a merge or when a maintainer reruns it. Build commits generated files to pull request branches in the repository, never to a fork. It reads the branch's files with no saved credentials, and the check rejects symlinks, so a file can't copy the workflow's token into `dist/`. GitHub holds the runs that Build's push starts until someone approves them, so Build checks its commit before it has credentials and reports that commit's `check` and `fork-check` itself.
- **You accept.** Anyone with write access can push a branch, and code on a pull request branch in the repository runs in the Build workflow with write access. Review changes to `scripts/` and `.github/` with extra care. Anyone with write access can also report a passing `check` or `fork-check` on a commit through GitHub's API, so the required checks guard against forks and mistakes, not against people with write access. A workflow on any branch can also read the repository's secrets, so anyone with write access can read `PRIVATE_DENYLIST`. Catalog setup names who that is and suggests leaving the secret out. The Catalog Manager moves a fork's pull request into the repository only when its Fork check passed, which means it changes nothing outside `bots/`.

### Updates have no signatures

Installed bots fetch updates over HTTPS from GitHub. Nothing signs the content.

- **You accept.** An update is as trustworthy as GitHub and the catalog's maintainers.

## Not covered

This is an independent community project, not an official Grok Bot project. How Grok Bot stores bots, runs routines, and grants app access is up to Grok Bot, and it can change without notice. Treat every bot you add, from this catalog or anywhere else, like any other app you give access to your accounts.
