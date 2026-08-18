#!/usr/bin/env bash
# Bump the l10n submodule pin in every consuming mod repo to this repo's
# current origin/main, and commit the bump. Run from anywhere; repos are
# discovered as ~/dev siblings carrying an l10n submodule. Push here first —
# consumers pull the pin from the remote, not from this working tree.
set -euo pipefail

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for repo in "$DEV_DIR"/*/; do
    [ -f "$repo/.gitmodules" ] || continue
    git -C "$repo" config -f .gitmodules submodule.l10n.url >/dev/null 2>&1 || continue
    name="$(basename "$repo")"
    before="$(git -C "$repo" rev-parse HEAD:l10n 2>/dev/null || echo none)"
    git -C "$repo" submodule update --init --remote l10n
    after="$(git -C "$repo" -C l10n rev-parse HEAD)"
    if [ "$before" = "$after" ]; then
        echo "$name: already at ${after:0:9}"
        continue
    fi
    git -C "$repo" add l10n
    git -C "$repo" commit -q -m "chore: Bump l10n submodule to ${after:0:9}"
    echo "$name: ${before:0:9} -> ${after:0:9} (committed, not pushed)"
done
