# Security

A bot catalog changes the instructions of every Grok Bot installed from it, and those bots act with their users' logins and connected apps. This page lists what can go wrong, what the catalog does about each risk, and the risks you accept by using it. It applies to the template and to every catalog made from it.

## Reporting a problem

Please don't open a public issue for a security problem. Use **Security > Report a vulnerability** on the repository instead, which reaches its maintainers privately. A problem with the template itself, its workflows, scripts, update check, or Catalog Manager, goes to the [template repository](https://github.com/JaxonWright/bot-catalog-for-grok-bot-template/security).

## Risks and how they are handled

### Whoever controls a catalog controls its bots

Anyone who can push to a catalog's `master` branch can change what every installed copy of its bots is told to do, through an update. That includes an attacker who takes over a maintainer's GitHub account.

- **Handled.** An installed bot never updates on its own. It shows its user the changelog and a link to the full diff, and updates only after a yes. `master` only changes through a pull request from `dev` that passes CI and merges with a merge commit. Release tags can't be moved or deleted, and the update check reads the changelog and bundle from the release tag itself, so what a user reviews is exactly what they install.
- **You accept.** If you approve an update without reading it, you are trusting the catalog's maintainer and their account security. Maintainers should use a hardware key or passkey for GitHub two-factor sign-in.
- **To opt out.** Tell any installed bot to turn automatic update checks off. It keeps its current version until you turn them back on.

### A moved or deleted release tag

Installed bots fetch each update from its release tag, `<slug>-v<version>`.

- **Handled.** The `protect-release-tags.json` ruleset blocks updating or deleting any `*-v*` tag. The Release workflow can still create new ones.
- **You accept.** Repository admins can turn rulesets off. A catalog without its rulesets imported has no tag protection.

### A pull request that adds harmful instructions

Anyone can propose changes to a bot. A change could quietly tell the bot to send data somewhere, or to act without asking.

- **Handled.** Every change needs a maintainer to merge it. CI warns about every new link in a bot's files. The Catalog Manager's triage calls out new permissions, routines, outside contacts, and links, and it treats everything written in issues and pull requests as data, never as instructions.
- **You accept.** A reviewer can miss something. Read the changelog and diff before you accept an update.

### A swapped Add Grok Bot link

A bot's `share_url` decides which bot the README's **Add Grok Bot** button installs. Pointing it at a look-alike bot would be easy to miss in review.

- **Handled.** The Fork check workflow rejects any change to a `share_url` in a pull request from a fork. It runs this repository's own copy of the check and only reads the fork's files, so the pull request can't switch it off. CI accepts only Grok Bot share links (`https://x.ai/bot/...`), so the button can't lead to another website. The README shows each bot's name and summary as plain text, so a summary can't add a second button or link. The Catalog Manager's triage calls out any `share_url` change.
- **You accept.** A maintainer can still change it, so the button is only as trustworthy as the catalog's maintainers.

### Personal details published by mistake

The repository is public. Anything pushed to it, including branches, commits, and pull request text, is public right away and stays in its history even after it is deleted.

- **Handled.** The Catalog Manager and the share prompt draft everything in chat, list what they removed only there, and push nothing until the user approves. CI rejects email addresses, phone numbers, private IP addresses, API-key shapes, and anything in the maintainer's `PRIVATE_DENYLIST` secret. gitleaks scans for secrets.
- **You accept.** CI runs after a push, so it catches a leak but can't take it back. The approval in chat is the real safeguard. If something private is pushed, treat it as public. Rotate any key, and ask GitHub Support to purge cached views if needed.

### Tricking the Catalog Manager

The Catalog Manager reads text written by strangers, such as issues, pull requests, comments, and web pages, and it can push to a catalog.

- **Handled.** Its instructions treat all of that text as data. It never merges, releases, publishes, or deletes without the user's yes in chat, and a yes covers only the plan it showed. If its GitHub connection lets you choose repositories, limit it to the catalog repository.
- **You accept.** Language models can be manipulated in ways nobody predicted. The approval step is the main defense, so read what it asks you to approve.

### Template updates run code in your repository

"Update my catalog from the template" copies the template's workflows and scripts into a catalog, where they run with write access.

- **Handled.** The Catalog Manager shows every change to workflows and scripts in full and opens a pull request only after a yes. Nothing updates automatically.
- **You accept.** Accepting a template update means trusting the template's maintainer for that change.

### Workflow permissions

- **Handled.** CI runs on pull requests with a read-only token, and pull requests from forks get no secrets. The Fork check reads a fork's files but never runs them. Set up catalog runs only when someone starts it by hand. Release creates tags only after a merge into `master`. Build commits generated files to `dev` after each push to `dev`.
- **You accept.** Anyone with write access can push to `dev` without a pull request, and code on `dev` runs in the Build workflow with write access. Review changes to `scripts/` and `.github/` with extra care.

### Updates have no signatures

Installed bots fetch updates over HTTPS from GitHub. Nothing signs the content.

- **You accept.** An update is as trustworthy as GitHub and the catalog's maintainers.

## Not covered

This is an independent community project, not an official Grok Bot project. How Grok Bot stores bots, runs routines, and grants app access is up to Grok Bot, and it can change without notice. Treat every bot you add, from this catalog or anywhere else, like any other app you give access to your accounts.
