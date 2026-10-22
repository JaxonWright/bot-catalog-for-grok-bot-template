# Release

Use this from the "Share a bot" skill, or when the user wants other merged changes, such as someone else's pull request, to reach the people using their bots.

1. Compare `master` with `dev` in `catalog_repo`. If there is nothing new on `dev`, say so and stop.
2. Summarize what the release contains for the user: each bot whose version changes, with its changelog section.
3. Open a pull request from `dev` into `master` titled "Release", or reuse an open one.
4. Wait for the check. If it fails because generated files are out of date, wait a few minutes for the Build workflow on `dev` to finish, then look again.
5. Merge only on the user's yes. If they already approved this release as part of a plan, such as sharing a bot, that yes counts.
6. Confirm that the Release workflow created a tag for each changed bot, named `<slug>-v<version>`. Tell the user that installed copies will offer the update within a day.
