#!/bin/sh
# Everything master's required "check" covers. CI runs it on pull requests and pushes to master, and Build runs it
# on the commit it adds to a pull request. BASE is the branch a pull request merges into, empty on master.
# RANGE is the commits to scan for secrets.
set -e
cd "$(dirname "$0")/.."

python -m unittest discover -s scripts

if [ -n "$BASE" ]; then
  python scripts/catalog.py check --generated --base "origin/$BASE"
else
  python scripts/catalog.py check --generated
fi

# The gitleaks command line itself, pinned and checksummed. Its GitHub Action needs a license for
# organization repositories, and fails on a new repository's first push.
GITLEAKS_VERSION=8.24.3
GITLEAKS_SHA256=9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c
dir=$(mktemp -d)
curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v$GITLEAKS_VERSION/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" -o "$dir/gitleaks.tar.gz"
echo "$GITLEAKS_SHA256  $dir/gitleaks.tar.gz" | sha256sum -c -
tar -xzf "$dir/gitleaks.tar.gz" -C "$dir" gitleaks
"$dir/gitleaks" git --redact --no-banner --log-opts="$RANGE" .
