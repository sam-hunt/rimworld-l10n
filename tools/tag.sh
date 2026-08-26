#!/usr/bin/env bash
# Cut a rimworld-l10n release: an annotated vMAJOR.MINOR.PATCH tag on HEAD,
# bumped by the given part from the latest tag, then pushed together with
# the branch (consumers fetch tags from the remote, not this working tree).
#
#   tools/tag.sh major|minor|patch [--no-push]
#
# Which part (decided by what a CONSUMER must do, see CLAUDE.md § Versioning):
#   major  consumers must edit something (shim attribute, CLI/output format,
#          sidecar format, skill step) — every consumer is bumped now
#   minor  behaviour picked up unchanged at the next bump (new checker rule,
#          engine, language-mechanics finding, process refinement)
#   patch  vocabulary/grounding additions, lessons, doc fixes
#
# Refuses on staged-but-uncommitted changes or a detached HEAD so the tag
# names exactly what is committed (unstaged WIP only warns: it is not in
# HEAD). Tag one coherent batch, not every commit.
set -euo pipefail

part="${1:-}"
push=1
[ "${2:-}" = "--no-push" ] && push=0
case "$part" in
    major|minor|patch) ;;
    *) echo "usage: tools/tag.sh major|minor|patch [--no-push]" >&2; exit 2 ;;
esac

root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$root"

if ! git diff --cached --quiet; then
    echo "error: staged changes are uncommitted; commit them first" >&2
    exit 1
fi
if ! git diff --quiet; then
    echo "warning: unstaged changes are NOT part of this tag:" >&2
    git diff --stat >&2
fi
branch="$(git symbolic-ref --quiet --short HEAD || true)"
if [ -z "$branch" ]; then
    echo "error: detached HEAD; tag from the branch you want released" >&2
    exit 1
fi

git fetch -q --tags origin
latest="$(git tag --list 'v*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)"
IFS=. read -r maj min pat <<< "${latest#v}"
: "${maj:=0}" "${min:=0}" "${pat:=0}"
case "$part" in
    major) maj=$((maj + 1)); min=0; pat=0 ;;
    minor) min=$((min + 1)); pat=0 ;;
    patch) pat=$((pat + 1)) ;;
esac
next="v$maj.$min.$pat"

git tag -a "$next" -m "$next"
echo "tagged $(git rev-parse --short HEAD) as $next (previous: ${latest:-none})"
if [ "$push" = 1 ]; then
    git push origin "$branch" "$next"
else
    echo "not pushed: run  git push origin $branch $next"
fi
