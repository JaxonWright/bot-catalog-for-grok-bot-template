# Share a bot

Use this when the user wants to share one of their bots, or ship a change to one that is already shared from `catalog_repo`. Sharing covers everything: adding the bot to the catalog, releasing it, and the first time, publishing the public copy that people add.

1. Ask which bot. Read `CONTRIBUTING.md` in `catalog_repo` for the file format, and check whether `bots/` already has this bot.
2. Get the bot's full definition: its description, every skill and every routine, word for word, plus its avatar's shape and color. Read it directly if you can. Otherwise message the bot and ask it to send you exactly that, with nothing summarized. If neither works, give the user a short message to paste into that bot and ask them to paste its answer back to you.
3. Draft the files for `bots/<slug>/`: `bot.toml`, `instructions.md`, one file per skill in `skills/`, one file per routine in `routines/`, and `CHANGELOG.md`. Use a short lowercase slug. Use the shape and color of the bot's built-in default mark in Grok Bot. If it has a custom picture, pick the closest shape and color. Leave out the "Check for bot updates" skill and routine, because the catalog adds those.
4. Remove everything personal: everything in `private_denylist`, plus names, email addresses, accounts, handles, phone numbers, addresses, links to private files or tools, keys, and anything the bot knows only from its memory or its conversations. Where a skill needs one of those, rewrite it to ask the user and remember the answer.
5. If the bot is already in the catalog, bump `version`: patch for wording fixes, minor for new skills or routines, major for changes to what the bot does on its own. Add a changelog section for the new version that says what changes for the people using it.
6. Show the user every file in full, then a separate list of everything you removed. Then say what happens next: you will add it to the catalog, release it, and for a new bot, create its public copy and share link. Wait for their yes. That yes covers every step below for this bot only.
7. Create a branch off `dev`, commit the approved files exactly as approved, and open a pull request into `dev`. When its check passes, merge it. If it fails, show the user the error and what you would change, and wait.
8. If the bot is new, publish it before you release:
   1. Wait for the Build workflow on `dev` to finish, so `dist/<slug>.md` exists on `dev`.
   2. Create a new Bot. Have it fetch https://raw.githubusercontent.com/<catalog_repo>/dev/dist/<slug>.md and set itself up exactly as that file's "How to apply" section says. Give it the name in `bot.toml`, and have it set its avatar with Grok Bot's built-in default mark using the shape and color listed there. It must not generate or upload a custom picture; if one is installed, it clears it. This copy is the one people will add, because it carries the update check.
   3. Create a public share link for the new Bot: Share, then "Create template", then "Public link". If you can't, ask the user to do it and paste you the link.
   4. Create a branch off `dev`, set `share_url` in `bots/<slug>/bot.toml` to the link, change nothing else, open a pull request into `dev`, and merge it when its check passes.
9. Run the "Release" skill. The user's yes from step 6 counts as the release confirmation.
10. Tell the user it's live. For a new bot, give them the share link and point out its **Add Grok Bot** button in the README. For an update, say that people who added the bot will be offered it within a day.
