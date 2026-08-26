#!/usr/bin/env bash
# Move ONE consuming repo's l10n pin to a release tag and commit just that
# pointer. Run from the consumer itself as  l10n/tools/bump-consumer.sh
# (the repo defaults to the superproject this script is checked out in), or
# from anywhere with an explicit repo path.
#
#   l10n/tools/bump-consumer.sh [repo-dir] [vX.Y.Z]     (default: latest tag)
#
# Pins move at exactly three moments — release (the release skill runs this
# first), the start of a translation pass, and a new upstream MAJOR — never
# per upstream commit; see CLAUDE.md § The propagation loop. The commit
# carries only the l10n path (other staged work is left staged, untouched);
# on a MAJOR bump it reminds you to add the per-repo edit before pushing.
# Does not push. Exit 0 with a message when already on the requested tag.
set -euo pipefail

here="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
repo="${1:-}"
want="${2:-}"
if [ -z "$repo" ]; then
    repo="$(git -C "$here" rev-parse --show-superproject-working-tree)"
    if [ -z "$repo" ]; then
        echo "usage: l10n/tools/bump-consumer.sh [repo-dir] [vX.Y.Z]  (no superproject found)" >&2
        exit 2
    fi
fi
repo="$(cd "$repo" && pwd)"
sub="$repo/l10n"
[ -f "$repo/.gitmodules" ] && git -C "$repo" config -f .gitmodules submodule.l10n.url >/dev/null 2>&1 \
    || { echo "error: $repo has no l10n submodule" >&2; exit 1; }

git -C "$repo" submodule update --init l10n >/dev/null
git -C "$sub" fetch -q --tags origin
if [ -z "$want" ]; then
    want="$(git -C "$sub" tag --list 'v*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)"
    [ -n "$want" ] || { echo "error: upstream has no vX.Y.Z release tags" >&2; exit 1; }
fi
git -C "$sub" rev-parse -q --verify "refs/tags/$want^{commit}" >/dev/null \
    || { echo "error: no such upstream tag: $want" >&2; exit 1; }

before_sha="$(git -C "$repo" rev-parse HEAD:l10n)"
before="$(git -C "$sub" describe --tags --exact-match --match 'v*' "$before_sha" 2>/dev/null || echo "${before_sha:0:9}")"
if [ "$before" = "$want" ]; then
    echo "$(basename "$repo"): already on $want"
    exit 0
fi

git -C "$sub" checkout -q "refs/tags/$want"
git -C "$repo" add l10n
git -C "$repo" commit -q -m "chore: Bump l10n submodule $before -> $want" -- l10n
echo "$(basename "$repo"): $before -> $want (committed, not pushed)"

old_major="${before#v}"; old_major="${old_major%%.*}"
new_major="${want#v}"; new_major="${new_major%%.*}"
if [[ "$before" == v* ]] && [ "$old_major" != "$new_major" ]; then
    echo "MAJOR bump: upstream changed the shim/flow contract — apply this repo's"
    echo "accompanying edit (see the upstream release notes) before pushing."
fi
