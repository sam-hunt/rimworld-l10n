# rimworld-l10n

The shared localization toolkit for this author's family of RimWorld mods
(BetterTradersGuild, UniqueWeaponsUnbound, UniqueMeleeWeapons,
PersonaWeaponsUnbound, XenogermTraderStock, ArchotechAndroidHardware,
ArchotechThumb, BionicThumbGuild, ...). Everything localization-related that
is true for *every* mod lives here, exactly once; each mod repo keeps only its
own facts (its translation surface, compat roots, coined-term glossary) and
consumes this repo as a git submodule (conventionally at `l10n/`).

## Layout

| Path | What it is |
| --- | --- |
| `process.md` | The family translation workflow: non-negotiables, file/format conventions, terminology grounding method, generation/update/audit workflows |
| `lessons.md` | Cross-language lessons — techniques and engine findings that hold across languages |
| `languages/<Language>.md` | Per-language mechanics: LanguageWorker behaviour, grammar rules, vanilla corpus style findings, grounded common vocabulary. Read ONLY the target language's file during a pass |
| `workshop.md` | Steam Workshop description/title localization conventions |
| `checker/` | The `check-translations` engine. Each repo's `Scripts/check-translations.py` is a thin config shim importing it |
| `refresh/` | The `refresh-translation-expectations` engine (drives the probe), consumed the same way |
| `probe/` | L10nProbe, the local-only dev mod that dumps a mod's expected DefInjected key set to the sidecar JSON. See `probe/README.md` |
| `tools/` | `tag.sh` cuts a `vX.Y.Z` release tag; `consumer-status.sh` lists every sibling's pin against it; `bump-consumer.sh` moves one consumer's pin to a tag |

## How the mod repos consume this

- **As a submodule**: `git submodule add ../rimworld-l10n.git l10n` (relative
  URL — resolves against the superproject's GitHub remote). Clone a mod repo
  with `git clone --recurse-submodules`; an existing clone runs
  `git submodule update --init`.
- **Skills**: each repo's `.claude/skills/translate/SKILL.md` holds the
  mod-specific facts and points here for process (`l10n/process.md`),
  lessons (`l10n/lessons.md`) and the target language
  (`l10n/languages/<Language>.md`) — progressive disclosure: a pass loads
  only the files it needs.
- **Scripts**: the per-repo `Scripts/check-translations.py` and
  `Scripts/refresh-translation-expectations.py` keep their repo's config
  (required DLCs, parity exemptions, pinned probe mod list) and rationale
  comments, and import the engines from `l10n/`.
- **CI**: `actions/checkout` with `submodules: true`; the checker then runs
  exactly as it does locally.

## Updating shared content

New mod-independent learnings land here, once — never in a single repo's
skill (see `process.md` § Recording new learnings). Commit, push, and when
the batch is complete cut a release tag with `tools/tag.sh major|minor|patch`
(major = consumers must edit their shim or flow; minor = behaviour they pick
up unchanged; patch = vocabulary, lessons, doc fixes — see `CLAUDE.md`
§ Versioning).

Consumers pin release tags, and a pin moves only at that repo's release, at
the start of a translation pass, or when a new major lands — never per
upstream commit, so a stable mod's history stays free of pin bumps. A repo
left on an older tag is pinned-stale, which is visible (`git submodule
status` prints the tag; `tools/consumer-status.sh` lists all siblings) and
recoverable (`l10n/tools/bump-consumer.sh` from inside the repo) — unlike the
silent divergence the pre-submodule copies suffered.

## The probe and deployment

`probe/` is a RimWorld dev mod that must be built and deployed into the local
RimWorld `Mods/` folder before a sidecar refresh. **Only the canonical clone
of this repo deploys it**: the csproj's deploy target detects submodule and
worktree checkouts (where `.git` is a gitfile, not a directory) and skips the
deploy, so a mod repo's pinned copy can never overwrite the deployed probe
with a stale version. Never upload the probe to the Steam Workshop.
