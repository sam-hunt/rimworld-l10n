# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in
this repository.

## Project Overview

**rimworld-l10n** is the shared localization toolkit for this author's family
of RimWorld mods (BetterTradersGuild, UniqueWeaponsUnbound,
UniqueMeleeWeapons, PersonaWeaponsUnbound, TradersStockXenogerms,
ArchotechAndroidHardware, ArchotechThumb, BionicThumbGuild). Every consuming
mod repo pins this repo as its `l10n/` git submodule. See README.md for the
full layout; in short: `process.md` (workflow authority), `lessons.md`,
`workshop.md`, `languages/<Language>.md` (per-language mechanics and
vanilla-grounded vocabulary), `checker/` and `refresh/` (script engines
consumed via per-repo `Scripts/*.py` config shims), `probe/` (the L10nProbe
dev mod), `tools/bump-consumers.sh`.

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

## The propagation loop

1. Edit the relevant file in THIS checkout (`~/dev/rimworld-l10n` is the
   canonical clone), commit here.
2. `git push` (consumers fetch pins from the remote, not this working tree).
3. `tools/bump-consumers.sh` — dynamically discovers every `~/dev` sibling
   repo carrying an `l10n` submodule, fast-forwards each pin to origin/main,
   and commits the bump per repo (it does not push the consumers; push them
   when their state is ready).

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
