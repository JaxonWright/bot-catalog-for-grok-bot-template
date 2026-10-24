# How the catalog works

This page shows how a bot gets from the files in `bots/` into someone's Grok Bot, and how it stays up to date after that. To do these steps yourself, see [Make your own catalog by hand](make-your-own.md).

In the diagrams, a gray border is a file in the repository and a teal border is a script or workflow. A blue border is a Grok Bot doing something, and a dashed orange border is a step that waits for your yes.

## People install the built bundle, not the source files

You edit the files in `bots/<slug>/`. People install `dist/<slug>.md`, which `scripts/catalog.py build` generates from those files. The build replaces each `{{key}}` with a value from `catalog.toml`, so the placeholders in `bots/` and `catalog/` never reach an installed bot.

```mermaid
flowchart LR
  src["bots/#lt;slug#gt;/*.md<br>may use {{template_repo}}"]:::file
  upd["catalog/updater-skill.md<br>uses {{repo}}, {{slug}}, {{version}}"]:::file
  toml["catalog.toml<br>repo, template_repo"]:::file
  build[["catalog.py build<br>fills every {{key}}"]]:::auto
  dist["dist/#lt;slug#gt;.md<br>no placeholders left"]:::out
  bt["bots/#lt;slug#gt;/bot.toml"]:::file
  cl["bots/#lt;slug#gt;/CHANGELOG.md"]:::file
  bot(["Installed bot"]):::bot
  src --> build
  upd --> build
  toml -- values --> build
  build -- writes --> dist
  bt -- "version, from master" --> bot
  dist -- "applied, from the release tag" --> bot
  cl -- "shown to the user" --> bot
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef auto stroke:#14907f,stroke-width:2px
  classDef out stroke:#14907f,stroke-width:3px
  classDef bot stroke:#5866b8,stroke-width:2px
```

The build fills `repo`, `template_repo`, `slug`, `name`, and `version`. It leaves any other `{{key}}` as written, so a misspelled key ships as literal text.

## Every change reaches master through a pull request

`master` requires two checks, `check` and `fork-check`. A branch in this repository gets both from the Build workflow. A fork's branch can't be pushed to, so the Catalog Manager moves a fork's pull request into a branch here before it can merge.

```mermaid
flowchart TB
  subgraph fork ["From a fork"]
    direction LR
    fpr["Pull request"]:::file --> fc[["Fork check: this repository's<br>scripts read the fork's files"]]:::auto
    fc -- passed --> move("Catalog Manager moves it<br>into a branch here"):::gate
  end
  subgraph here ["From a branch in this repository"]
    direction LR
    pr["Pull request"]:::file --> build[["Build: regenerate the README,<br>avatars, and dist, then commit"]]:::auto
    build --> chk[["scripts/check.sh: tests,<br>catalog.py check, gitleaks"]]:::auto
    chk --> push[["Push the commit and post<br>the check and fork-check statuses"]]:::auto
  end
  subgraph main ["On master"]
    direction LR
    merge("Merge into master"):::gate --> rel[["Release: catalog.py<br>check --generated"]]:::auto
    rel --> tag["Tag #lt;slug#gt;-v#lt;version#gt;<br>for each unreleased bot"]:::out
  end
  move -- "new pull request" --> pr
  push -- "both checks pass" --> merge
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef auto stroke:#14907f,stroke-width:2px
  classDef out stroke:#14907f,stroke-width:3px
  classDef gate stroke:#c47a12,stroke-width:2px,stroke-dasharray:5 3
```

GitHub holds the workflow runs that a workflow's own push starts. That's why Build runs `check.sh` on its commit itself, posts both statuses, and deletes the held runs. CI also runs `check.sh` on every pull request and every push to `master`. Fork check never gets the `PRIVATE_DENYLIST` secret. A release tag can't be moved or deleted, so Release runs the check again before it tags anything.

## Installed bots check for updates once a day

The build adds a "Check for bot updates" skill and a daily routine to every bot. The check says nothing unless it has an update to offer or finds that the bot or the repository is gone.

```mermaid
flowchart LR
  on{"Checks on, or<br>the user asked?"}:::bot -- yes --> ver["Read the version<br>from master's bot.toml"]:::bot
  ver -- found --> newer{"Newer, and<br>not skipped?"}:::bot
  newer -- yes --> fetch["Fetch dist at<br>the new tag"]:::bot
  fetch -- tagged --> cmp["Compare the bundle<br>with itself"]:::bot
  cmp --> ask("Ask the user"):::gate
  ask --> ans["Update, skip this version,<br>or turn checks off"]:::out
  on -- no --> stop1["Stop"]:::file
  ver -- "not found" --> tell["Tell the user the bot<br>or the repository is gone"]:::file
  newer -- no --> stop2["Stop quietly"]:::file
  fetch -- "not tagged yet" --> retry["Try again tomorrow"]:::file
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef out stroke:#14907f,stroke-width:3px
  classDef gate stroke:#c47a12,stroke-width:2px,stroke-dasharray:5 3
  classDef bot stroke:#5866b8,stroke-width:2px
```

The bot works out what would change by comparing the bundle with its own setup, because whoever wrote the changelog may have left something out. It still shows the changelog, and it points out anything the bundle changes that the changelog doesn't mention.

## Set up catalog turns a copy of the template into a catalog

**Use this template** makes an exact copy, and the copy's `catalog.toml` still says it is the template. Until the Set up catalog workflow runs, Release tags nothing in it.

```mermaid
flowchart LR
  t["Template<br>repo = the template<br>template = true<br>bots/catalog-manager/"]:::file
  c["Your new copy<br>repo = the template<br>template = true<br>bots/catalog-manager/"]:::file
  s["Your catalog<br>repo = your repository<br>template = false<br>Catalog Manager removed"]:::out
  t -- "Use this template" --> c
  c -- "Set up catalog" --> s
  s -. "template_repo still points here" .-> t
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef out stroke:#14907f,stroke-width:3px
```

Set up catalog refuses to run in the template itself. It credits you, sets the bots' license, removes every bot marked `template_only`, and rebuilds the README and bundles. After that, `{{repo}}` fills in as your repository, and `{{template_repo}}` still names the template, which is where template updates come from.

## Template updates arrive as a pull request

The template owns the paths listed in `template_paths` in `catalog.toml`. Every Monday, the Catalog Manager compares those paths with your `master` and offers a pull request if they differ.

```mermaid
flowchart LR
  subgraph tpl ["Template master"]
    owned["template_paths: .github/, scripts/,<br>catalog/, docs/, and a few files"]:::auto
  end
  subgraph cat ["Your catalog's master"]
    copy["Template-owned copy"]:::auto
    mine["bots/, catalog.toml, README.md<br>never touched"]:::file
  end
  owned -- "Monday check finds a difference" --> pr("Pull request: Update from the template"):::gate
  pr -- "copies the paths and deletes<br>files the new list drops" --> copy
  pr -- "if the bundles change" --> bump["Patch bump for<br>each released bot"]:::file
  bump --> merge("Merge"):::gate
  merge --> tags[["Release tags each bot"]]:::auto
  tags --> bots(["Installed bots offer<br>the update within a day"]):::bot
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef auto stroke:#14907f,stroke-width:2px
  classDef gate stroke:#c47a12,stroke-width:2px,stroke-dasharray:5 3
  classDef bot stroke:#5866b8,stroke-width:2px
```

`.github/template-files.txt` lists the files the template owned at the last update. The update deletes only the files on that old list that the new list drops, so it never deletes a file you added. A change to `catalog/` or `scripts/catalog.py` changes every bundle, so the check asks for a patch bump on each released bot. That bump is how installed bots get the new update check.

## A new bot needs its share link before it can merge

A new bot's check fails until `bot.toml` has a `share_url`. The link must open a Grok Bot set up from the branch's own bundle, so you publish the bot from inside the pull request.

```mermaid
flowchart LR
  draft["Draft bots/#lt;slug#gt;/ with<br>personal details removed"]:::file --> yes("Your yes, after<br>reading every file"):::gate
  yes --> pr[["Pull request and Build<br>write dist/#lt;slug#gt;.md"]]:::auto
  pr --> chk{"check:<br>share_url set?"}:::auto
  chk -- "no link yet" --> pub(["New Bot set up from the<br>branch's dist, then Share,<br>Create template"]):::bot
  pub -- "public link" --> url["Set share_url in bot.toml<br>on the same branch"]:::file
  url -- push --> pr
  chk -- passes --> merge("Merge"):::gate
  merge --> rel[["Release tags<br>#lt;slug#gt;-v#lt;version#gt;"]]:::auto
  classDef file stroke:#8a9a96,stroke-width:1.5px
  classDef auto stroke:#14907f,stroke-width:2px
  classDef gate stroke:#c47a12,stroke-width:2px,stroke-dasharray:5 3
  classDef bot stroke:#5866b8,stroke-width:2px
```

Only the Bot you create in this step can later use **Share**, then **Update template**. If you delete it, its public link stays on its current version for good.
