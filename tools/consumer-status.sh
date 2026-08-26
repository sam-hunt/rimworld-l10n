#!/usr/bin/env bash
# Show each consuming mod repo's l10n pin against the latest upstream
# release tag. Repos are discovered as ~/dev siblings carrying an l10n
# submodule. Read-only; nothing is fetched into the consumers.
#
#   tools/consumer-status.sh
#
# Columns: repo, pinned tag (or untagged@sha), status:
#   current       on the latest tag
#   behind        minor/patch behind — picked up at that repo's next release
#                 or translation pass; do NOT bump it for this alone
#   MAJOR BEHIND  the shim/flow contract changed — bump now, with the
#                 accompanying per-repo edit (tools/bump-consumer.sh <repo>)
#   untagged      pinned to a commit that is not a release — pin a tag
set -euo pipefail

root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
dev_dir="$(cd "$root/.." && pwd)"

git -C "$root" fetch -q --tags origin 2>/dev/null || echo "note: offline; using local tags"
latest="$(git -C "$root" tag --list 'v*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)"
if [ -z "$latest" ]; then
    echo "error: no vX.Y.Z release tags exist yet (tools/tag.sh)" >&2
    exit 1
fi
latest_major="${latest#v}"; latest_major="${latest_major%%.*}"
echo "latest upstream release: $latest"
echo

for repo in "$dev_dir"/*/; do
    [ -f "$repo/.gitmodules" ] || continue
    git -C "$repo" config -f .gitmodules submodule.l10n.url >/dev/null 2>&1 || continue
    name="$(basename "$repo")"
    sha="$(git -C "$repo" rev-parse HEAD:l10n 2>/dev/null || true)"
    if [ -z "$sha" ]; then
        printf '%-28s %-22s %s\n' "$name" "-" "no pin committed"
        continue
    fi
    # Describe against the canonical checkout: it holds every tag, while a
    # consumer's submodule checkout may not have fetched them yet.
    tag="$(git -C "$root" describe --tags --exact-match --match 'v*' "$sha" 2>/dev/null || true)"
    dirty=""
    git -C "$repo" diff --quiet -- l10n 2>/dev/null || dirty=" (l10n modified in tree)"
    if [ -z "$tag" ]; then
        printf '%-28s %-22s %s\n' "$name" "untagged@${sha:0:9}" "untagged$dirty"
        continue
    fi
    major="${tag#v}"; major="${major%%.*}"
    if [ "$tag" = "$latest" ]; then
        status="current"
    elif [ "$major" -lt "$latest_major" ]; then
        status="MAJOR BEHIND"
    else
        status="behind"
    fi
    printf '%-28s %-22s %s\n' "$name" "$tag" "$status$dirty"
done
