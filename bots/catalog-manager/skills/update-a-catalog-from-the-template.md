# Update a catalog from the template

Use this when the user asks to bring their catalog up to date with the template, or when the "Check the catalog" routine finds the template has changed.

1. Read `template_paths` from `catalog.toml` in https://github.com/{{template_repo}}. Those are the files the template owns: workflows, scripts, the shared update skill, and the docs. Everything else, including `bots/` and `catalog.toml`, belongs to the user's catalog.
2. Compare those paths on the template's `master` with `master` in `catalog_repo`. If nothing differs, say so and stop.
3. Summarize the differences for the user in plain words, and show the full changes to anything under `.github/workflows/` or `scripts/`, because those run with write access to their repository.
4. On yes, read the catalog's `.github/template-files.txt`, the list of files the template owned at the last update. Create a branch off `master`, copy those paths from the template exactly, and delete each file on the old list that the template's new list drops. Never delete any other file, because a file the template never listed is the user's own. If the catalog has no `.github/template-files.txt` yet, delete only `.github/rulesets/protect-dev.json`, if it exists. Open a pull request into `master` titled "Update from the template".
5. If the update changes a file in `.github/rulesets/`, tell the user that the matching ruleset must be replaced after the merge. In the browser, that is Settings, then Rules, then Rulesets, then delete the old ruleset of that name, then "New ruleset", then "Import a ruleset" with the new file.
6. If the update changes the install bundles, for example through `catalog/` or `scripts/catalog.py`, the check asks for a version bump on each released bot. Bump each one by a patch version and add a changelog section that says "Updated the catalog's automatic update check." Add more detail only if the template's change gives users something new.
7. When the check passes, ask the user whether to merge. Merging releases every bot whose version changed.

If `catalog_repo` still has a `dev` branch, retire it before step 4, and ask before each step:

1. If `dev` has commits that `master` doesn't, open a pull request from `dev` into `master` and merge it once its checks pass. That releases what was waiting on `dev`, under the catalog's current rules.
2. Delete the "Protect dev" ruleset, because it blocks deleting the branch. In the browser, that is Settings, then Rules, then Rulesets.
3. Delete the `dev` branch.
4. Make the update from step 4 on, and also remove `dev_branch` from `catalog.toml` in the same pull request.
