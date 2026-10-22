#!/usr/bin/env bash
# Applies .github/rulesets/*.json to this repository. Same result as importing them under
# Settings > Rules > Rulesets, and turns on Settings > General > Automatically delete head branches. Safe to run again. Needs a public repo or a paid GitHub plan.
set -euo pipefail
cd "$(dirname "$0")/.."
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

for file in .github/rulesets/*.json; do
  name=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['name'])" "$file")
  id=$(gh api "repos/$repo/rulesets" --jq ".[] | select(.name == \"$name\") | .id")
  if [ -n "$id" ]; then
    gh api -X PUT "repos/$repo/rulesets/$id" --input "$file" >/dev/null
  else
    gh api -X POST "repos/$repo/rulesets" --input "$file" >/dev/null
  fi
  echo "ruleset '$name' applied"
done

gh api -X PATCH "repos/$repo" -f delete_branch_on_merge=true >/dev/null
echo "automatic deletion of merged branches turned on"
