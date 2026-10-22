# Update a catalog from the template

Use this when the user asks to bring their catalog up to date with the template, or when the weekly digest finds the template has changed.

1. Read `template_paths` from `catalog.toml` in https://github.com/{{template_repo}}. Those are the files the template owns: workflows, scripts, the shared update skill, and the docs. Everything else, including `bots/` and `catalog.toml`, belongs to the user's catalog.
2. Compare those paths on the template's `master` with `dev` in `catalog_repo`. If nothing differs, say so and stop.
3. Summarize the differences for the user in plain words, and show the full changes to anything under `.github/workflows/` or `scripts/`, because those run with write access to their repository.
4. On yes, create a branch off `dev`, copy those paths from the template exactly, and open a pull request into `dev` titled "Update from the template".
5. If the update changes the install bundles, for example through `catalog/` or `scripts/catalog.py`, the check asks for a version bump on each released bot. Bump each one by a patch version and add a changelog section that says "Updated the catalog's automatic update check." Add more detail only if the template's change gives users something new.
6. When the check passes, ask the user whether to merge, then offer to release.
