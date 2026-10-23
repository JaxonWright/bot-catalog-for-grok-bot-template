# Changelog

## 1.1.0

- Catalogs no longer have a `dev` branch. Each bot's pull request goes straight into `master`, and merging it releases the bot. The "Release" skill is gone, because there is nothing left to release by hand.
- A new bot's pull request merges only after you publish the bot from it and add its share link, so the README never lists a bot without an **Add Grok Bot** button. Only you are asked for that link, never the person who opened the pull request.
- A new routine, "Check the catalog", looks for new issues and pull requests every day and tells you about them. It replaces the weekly digest, and still checks for template updates on Mondays.
- Accepting a pull request from a fork now moves it into a branch of your catalog, keeping its author, so it can get its generated files.
- "Update my catalog from the template" removes the `dev` branch from a catalog that still has one, asking before each step.

## 1.0.2

- Setting up a catalog now turns on automatic deletion of merged pull request branches.

## 1.0.1

- Installing or updating a bot now sets its avatar with Grok Bot's built-in default mark, and never generates or uploads a custom picture.

## 1.0.0

- First release. Sets up a catalog, shares bots from it, triages contributions, and keeps a catalog current with the template.
