# Changelog

## 1.1.3

- Only you add bots to your catalog. Other people's pull requests can suggest changes to your bots but can't add new ones, so the Catalog Manager points them to a "Bot idea" issue instead.
- It calls out any bot whose name looks like another bot's.
- When an update is available, the Catalog Manager now compares it with what it runs today and tells you in its own words what would change, including anything the changelog leaves out.

## 1.1.2

- Updating your catalog from the template deletes only the files the template removed, never workflows or other files you added yourself.
- The daily "Check the catalog" routine remembers where it left off only after it has told you what's new, so nothing is skipped if a check stops partway.
- Setting up a catalog also makes workflow runs from outside contributors wait for approval, and the Catalog Manager never approves them.

## 1.1.1

- It moves a pull request from a fork into your catalog only when the Fork check passed, so a moved pull request changes nothing outside `bots/` and never sets a share link.
- Retiring the `dev` branch now happens in an order that works. It merges what's waiting on `dev` first, removes the "Protect dev" ruleset, deletes `dev`, and then updates your catalog from the template. Sharing a bot runs this first if your catalog still has `dev`.
- When a template update changes a ruleset, it tells you how to replace the ruleset in your repository's settings.

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
