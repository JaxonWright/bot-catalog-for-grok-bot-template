#!/bin/sh
set -e
git -C "$(dirname "$0")/.." config core.hooksPath .githooks
echo "pre-commit check installed"
