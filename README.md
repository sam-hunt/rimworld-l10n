# rimworld-l10n

The shared localization toolkit for this author's family of RimWorld mods
(BetterTradersGuild, UniqueWeaponsUnbound, UniqueMeleeWeapons,
PersonaWeaponsUnbound, TradersStockXenogerms, ArchotechAndroidHardware,
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
skill (see `process.md` § Recording new learnings). After committing here,
bump the submodule pin in each mod repo (`git -C <repo> submodule update
--remote l10n`, commit). A repo left unbumped is pinned-stale, which is
visible and recoverable — unlike the silent divergence the pre-submodule
copies suffered.

## The probe and deployment

`probe/` is a RimWorld dev mod that must be built and deployed into the local
RimWorld `Mods/` folder before a sidecar refresh. **Only the canonical clone
of this repo deploys it**: the csproj's deploy target detects submodule and
worktree checkouts (where `.git` is a gitfile, not a directory) and skips the
deploy, so a mod repo's pinned copy can never overwrite the deployed probe
with a stale version. Never upload the probe to the Steam Workshop.
