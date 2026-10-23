# Update a catalog from the template

Use this when the user asks to bring their catalog up to date with the template, or when the "Check the catalog" routine finds the template has changed.

1. Read `template_paths` from `catalog.toml` in https://github.com/{{template_repo}}. Those are the files the template owns: workflows, scripts, the shared update skill, and the docs. Everything else, including `bots/` and `catalog.toml`, belongs to the user's catalog.
2. Compare those paths on the template's `master` with `master` in `catalog_repo`. If nothing differs, say so and stop.
3. Summarize the differences for the user in plain words, and show the full changes to anything under `.github/workflows/` or `scripts/`, because those run with write access to their repository.
4. On yes, create a branch off `master`, copy those paths from the template exactly, and open a pull request into `master` titled "Update from the template". Also delete any file under `.github/` that the template no longer has.
5. If the update changes the install bundles, for example through `catalog/` or `scripts/catalog.py`, the check asks for a version bump on each released bot. Bump each one by a patch version and add a changelog section that says "Updated the catalog's automatic update check." Add more detail only if the template's change gives users something new.
6. When the check passes, ask the user whether to merge. Merging releases every bot whose version changed.
7. If `catalog_repo` still has a `dev` branch, this update removes it. Open the pull request into `dev` instead, merge it, then open one from `dev` into `master` and merge that. Then delete `dev` and the "Protect dev" ruleset, and remove `dev_branch` from `catalog.toml` in a pull request into `master`. Ask before each step.
