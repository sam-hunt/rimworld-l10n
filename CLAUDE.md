# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in
this repository.

## Project Overview

**rimworld-l10n** is the shared localization toolkit for this author's family
of RimWorld mods (BetterTradersGuild, UniqueWeaponsUnbound,
UniqueMeleeWeapons, PersonaWeaponsUnbound, XenogermTraderStock,
ArchotechAndroidHardware, ArchotechThumb, BionicThumbGuild). Every consuming
mod repo pins this repo as its `l10n/` git submodule. See README.md for the
full layout; in short: `process.md` (workflow authority), `lessons.md`,
`workshop.md`, `languages/<Language>.md` (per-language mechanics and
vanilla-grounded vocabulary), `checker/` and `refresh/` (script engines
consumed via per-repo `Scripts/*.py` config shims), `probe/` (the L10nProbe
dev mod), `tools/` (release tagging and consumer pin management).

## The content contract

- **Mod-independent knowledge lives here, exactly once**: engine mechanics
  (LanguageWorker findings), per-language grammar/style rules, vanilla corpus
  facts, vanilla-grounded common vocabulary, cross-language lessons, process.
  When a translation pass in a consuming repo surfaces such a finding, it is
  recorded HERE — never in that repo's skill.
- **Mod-specific knowledge stays in each consuming repo**: coined terms,
  phrasing decisions, def-to-template maps, Workshop titles — in that repo's
  `.claude/skills/translate/glossary/<Language>.md`.
- Corrections replace, not stack: when a later pass disproves an earlier
  claim, the file carries only the corrected finding with its date and a
  brief resolution note (see `languages/German.md`'s lookup correction for
  the pattern).

## Versioning

Every release of this repo is an annotated `vMAJOR.MINOR.PATCH` tag, cut
with `tools/tag.sh major|minor|patch` once the batch is pushed — one tag per
coherent batch, not per commit. The part to bump is decided by what a
CONSUMER has to do, never by how important the change feels:

- **major** — consumers must edit something or their flow changes: a shim
  attribute added/renamed, a checker CLI flag or output-format change, a
  sidecar format change, a release/translate skill step that must be
  reworded. Every consumer is bumped now, and each bump commit carries that
  edit. Say what the edit is in the tag's commit message.
- **minor** — behaviour consumers pick up unchanged at their next bump: a
  new checker rule, a new engine, a language-mechanics or grammar finding, a
  process.md refinement.
- **patch** — vocabulary/grounding additions in `languages/*.md`, lessons,
  doc fixes, roster/wording changes.

Consumers pin release tags only, never an untagged commit. `git submodule
status` in a consumer then prints the pinned tag, so staleness is visible
without tooling, and a repo still on `v1.x` while the family is on `v2.x` is
one that owes a shim/flow edit — `tools/consumer-status.sh` lists this for
every sibling.

## The propagation loop

1. Edit the relevant file in THIS checkout (`~/dev/rimworld-l10n` is the
   canonical clone), commit here, `git push` (consumers fetch pins and tags
   from the remote, not this working tree).
2. When the batch is complete, `tools/tag.sh <part>` (pushes the tag).
3. Do NOT bump consumers per upstream change. A pin moves at exactly three
   moments, and a stable mod's history must never fill with pin bumps:
   - **at release** — the consumer's release skill runs
     `l10n/tools/bump-consumer.sh` before the checker;
   - **at the start of a translation pass** — the translate skill runs it
     first, so the pass reads current language docs;
   - **on a new major** — bump every consumer now (`tools/consumer-status.sh`
     shows who is behind; `tools/bump-consumer.sh <repo>` bumps one), with
     the required per-repo edit in the same commit.
   The checker enforces this from the consumer side (`[l10n engine pin]`):
   a major lag or an untagged pin warns always; a minor/patch lag warns only
   under `--strict` (release gates run on the latest tag) and is a note
   otherwise.

Never edit a consuming repo's `l10n/` checkout in place — it is a pinned
read-only copy and the change would be lost on the next bump.

## Script engines

`checker/check_translations.py` and `refresh/refresh_expectations.py` hold
all logic; each consuming repo's `Scripts/check-translations.py` and
`Scripts/refresh-translation-expectations.py` are thin shims that import the
engine and assign config by module attribute (see the `SHIM_TEMPLATE.py`
beside each engine, and any consuming repo's shims for real examples with
per-repo rationale). Behavioral changes belong in the engine; per-repo values
and their rationale comments belong in the shims. The engines were extracted
byte-identical from the repos' original scripts — keep CLI flags and output
format stable, since consumers' CI release gates run the checker.

## The probe

`probe/` is L10nProbe, a local-only dev mod that dumps a mod's expected
DefInjected key set (see `probe/README.md` and `probe/CLAUDE.md` for design
and build). **Only this canonical checkout deploys it**: the csproj's deploy
target checks whether the repo root's `.git` is a real directory and no-ops
in submodule/worktree checkouts, so a consumer's pinned copy can never
overwrite the deployed probe with a stale version. Never upload it to the
Steam Workshop.

## Policy

Translation generation passes are token-expensive and run only on explicit
request, one language at a time (see `process.md`'s non-negotiables).
Editing this repo's docs, engines, or probe is infra work and always fine.
