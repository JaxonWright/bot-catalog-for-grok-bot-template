#!/bin/sh
# Draws assets/social-preview.png from the SVG the build writes, since GitHub's social preview takes only an uploaded PNG.
# Liberation Sans stands in for the header's Helvetica and Arial, which Linux runners don't have.
set -e
cd "$(dirname "$0")/.."
if ! command -v rsvg-convert >/dev/null || ! fc-list | grep -q "Liberation Sans"; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq --no-install-recommends librsvg2-bin fonts-liberation
fi
rsvg-convert assets/social-preview.svg -o assets/social-preview.png
