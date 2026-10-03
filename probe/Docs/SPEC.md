# L10nProbe — spec

A tiny, local-only RimWorld 1.6 dev mod that dumps the **complete expected
DefInjected key set** (with current English values) for selected loaded mods to
machine-readable files. It replaces the manual in-game translation report in the
mod family's release flows (UniqueMeleeWeapons, UniqueWeaponsUnbound,
PersonaWeaponsUnbound), making unknown localization gaps discoverable by
structure instead of by hand. **Never shipped to Steam Workshop.**

## Why (problem statement)

The sibling repos' `Scripts/check-translations.py` validates translations
against an expected key set derived from the mod's own def XML plus a
hand-maintained `EXTERNAL_INJECTIONS` manifest. The manifest exists because
some translatable text appears in no XML anywhere: fields inherited from
vanilla `ParentName` defs (tool labels, `labelNounPretty`,
`messageDefendersAttacking`) and C# field defaults
(`CompProperties_EquippableAbilityReloadable.chargeNoun`/`cooldownGerund`).
Only reflection over the **live, loaded DefDatabase** sees everything — which
today means the in-game translation report: slow, noisy with vanilla's own
missing data, and manual (UI actuation, language switching, desktop output).

The game's report is just a wrapper. The underlying walker is directly
callable, mod-filterable, and language-independent — this mod calls it.

## Decompile-verified API surface (RimWorld 1.6, verified 2026-07-31)

Re-verify against the current build with
`ilspycmd "$RIMWORLD_PATH/RimWorldWin64_Data/Managed/Assembly-CSharp.dll" -t <Type>`.

- **`Verse.DefInjectionUtility.ForEachPossibleDefInjection(Type defType,
PossibleDefInjectionTraverser action, ModMetaData onlyFromMod = null)`** —
  the ground-truth enumerator.
  - Delegate: `(string suggestedPath, string normalizedPath, bool isCollection,
string currentValue, IEnumerable<string> currentValueCollection,
bool translationAllowed, bool fullListTranslationAllowed,
FieldInfo fieldInfo, Def def)`.
  - Walks the live def object graph recursively (visited-set; skips `Thing`
    and `Def`-valued fields), so vanilla-inherited values and C# constructor
    defaults are present in `currentValue`.
  - `suggestedPath` already applies `TranslationHandleUtility` list handles
    (`tools.handle.label`, not `tools.0.label`) and `TKeySystem` remapping —
    emit `suggestedPath`, it is what translation files must use.
  - `translationAllowed` is false for `[NoTranslate]`/`[Unsaved]` fields;
    `fullListTranslationAllowed` marks `[TranslationCanChangeCount]` lists
    (e.g. UWU's `labelKeywords`) — carry both flags into the output.
  - `onlyFromMod` filters by `def.modContentPack.PackageId` — this is the
    noise-elimination: only the probed mod's defs are visited, vanilla's
    missing translations never appear.
- **Which entries count as "must translate":**
  `Verse.DefInjectionUtility.ShouldCheckMissingInjection(string str,
  FieldInfo fi, Def def)` — **public**, no reflection needed. The report's
  missing pass (`DefInjectionPackage.MissingInjections`, called per package by
  `LanguageReportGenerator.AppendMissingDefInjections`) applies it on top of
  the walker: scalars count iff `translationAllowed && ShouldCheck(value)`;
  string collections are checked **per element** with the same predicate.
  The probe's expected key set is therefore exactly what `MissingInjections`
  would report for a language with no translation files. Reuse the game's
  filter verbatim: divergence from the report is a bug.
- **Def type enumeration:** `GenDefDatabase.AllDefTypesWithDatabases()` —
  public, verified; it is the universe `TranslationFilesCleaner` generates
  DefInjected files from (the report iterates the active language's
  `DefInjectionPackage`s, whose def types come from the same set).
- **What the probe replaces:** `Verse.LanguageReportGenerator` — UI-only
  (debug action), refuses to run unless a non-English language is active,
  writes `TranslationReport.txt` to a fixed location, and diffs against the
  active language (which the probe deliberately does not: expected keys are
  language-independent; per-language diffing stays in each repo's checker).
- **When the walk runs** (verified 2026-10-03, 1.6.4871):
  `PlayDataLoader.DoPlayLoad` runs inside an asynchronous long event, and
  `LongEventHandler.ExecuteWhenFinished` delegates queued during it run on
  the main thread, in queue order, once it ends (each in its own try/catch).
  `Mod` constructors (`LoadedModManager.CreateModClasses`, early in
  `DoPlayLoad`) queue first; `DoPlayLoad` itself then queues
  `SolidBioDatabase.LoadAllBios`, `LoadedLanguage.InjectIntoData_AfterImpliedDefs`,
  `StaticConstructorOnStartupUtility.CallAll`, atlas baking and GC.
  `InjectIntoData_BeforeImpliedDefs` (non-generated defs) ran synchronously
  inside `DoPlayLoad`, before `ResolveReferences`. The probe queues its dump
  pass from its `Mod` constructor, so it walks the complete, resolved,
  injected def graph **before any mod's static constructor**; it queues the
  log dump and shutdown from a `[StaticConstructorOnStartup]` type, so those
  run **after them all**. A value another mod assigns to a probed def from its
  static constructor (Vanilla Expanded Framework's
  `ResearchProjectUtility.AutoAssignRules` filling every research project's
  null `generalRules` with its 75-line schematic grammar) is therefore absent
  from the dump — correctly, since the game's injection passes are over by
  then and no translation of such a key could load. The in-game report walks
  late and lists it; this timing is the one deliberate divergence from the
  report. See `Core/L10nProbe_Startup.cs`.

## Behavior

1. **When triggered**, for each configured target mod: enumerate every def
   type, run the walker with `onlyFromMod`, record the game's
   missing-injection verdict per entry (`required`), and write one output
   file per mod.
2. **Triggers:**
   - A **"Probe now"** button in the mod settings window (manual path, for
     eyeballing). It walks after startup, so its dumps carry
     `meta.collectedAfterStartup: true` and the refresh engine refuses them.
   - **Command-line automation:** when the game is launched with
     `-l10nprobe` (check arg readability via `Verse.GenCommandLine`), run the
     dump pass from the delegate the `Mod` constructor queued (complete def
     graph, before any static constructor — see the API section), then, from
     a delegate queued at `StaticConstructorOnStartup` time, write the boot
     log dump and **quit the game** (`Root.Shutdown()`). This is the hook
     release scripts drive.
   - Optional settings toggle: probe on every boot (no quit); same timing as
     the command-line path.
   - Both startup triggers ALSO write the **boot log dump** (§3a) after the
     probe run and before the shutdown line, so the log includes the probe's
     own FAILED lines and a reader can tell "run complete, no dump" apart
     from "dump present".
3. **Output** — one JSON file per probed mod, stable-sorted for git-diffing:

```json
{
  "meta": {
    "gameBuild": "<VersionControl.CurrentVersionStringWithRev>",
    "activeDlcs": ["Core", "Royalty", "Odyssey", "..."],
    "modPackageId": "...",
    "modName": "...",
    "activeMods": ["brrainz.harmony", "ludeon.rimworld", "...", "shunter.l10nprobe"],
    "generated": "2026-07-30T00:00:00Z"
  },
  "defInjections": {
    "ThingDef": {
      "UMW_Axe_Unique.tools.handle.label": { "english": "handle", "required": true },
      "UMW_Axe_Unique.label": { "english": "unique axe", "required": true },
      "UMW_Cut_Ragged.comps.HediffComp_TendDuration.labelTendedWell": {
        "english": "bandaged",
        "normalized": "UMW_Cut_Ragged.comps.0.labelTendedWell"
      }
    },
    "UniqueWeaponsUnbound.TraitCostRuleDef": {
      "UWU_Akimbo.labelKeywords": {
        "english": ["akimbo"],
        "isCollection": true,
        "fullListAllowed": true
      }
    }
  }
}
```

Every entry is a **legal injection point**: `translationAllowed`, on a
non-`generated` def, with a non-empty current value — the full set the game
would actually load a translation into. The game's must-translate filter is
recorded, not applied as a cut: `"required": true` marks entries
`ShouldCheckMissingInjection` passes (collections: any element passes,
mirroring the per-element check in `DefInjectionPackage.MissingInjections`)
— i.e. exactly what the in-game report would list as missing. Non-required
entries (single-word labels without `[MustTranslate]`, `[MayTranslate]`
fields, `fullListAllowed` keyword lists) exist because real translations
target them and consumers must be able to validate those for staleness.

Flag fields are emitted only when true. `"normalized"` is emitted only when
it differs from the key: the key is `suggestedPath` (handle form); existing
translation files may use the equally-valid index form, which the game
dedups by `normalizedPath` — consumers match legacy keys against it.

Def types are keyed by the DefInjected **folder name the game's loader
accepts** (`GenTypes.GetTypeInAnyAssembly`): short name for ignored
namespaces (Verse, RimWorld), full name for custom-namespace def types like
`UniqueWeaponsUnbound.TraitCostRuleDef`.

A collection is emitted as one entry at its `suggestedPath` carrying **all**
current elements, because a full-list `<li>` translation must match the
element count unless `fullListAllowed` is set. `activeDlcs` uses
`ExpansionDef.defName` (language-independent, unlike labels) in DefDatabase
order. It matters because `MayRequire`-gated defs (e.g. UMW's Axe/Warhammer
uniques need Royalty) only exist — and only emit keys — when their DLC is
active; consumer scripts must be able to detect a probe run with the wrong
DLC set. `activeMods` is every running mod's packageId in load order
(lowercase, the `_steam` postfix the game appends when a local copy of the
same mod is also installed stripped; Core and DLCs included, the probe
itself last): the boot configuration the dump reflects. A mod that is
loaded can patch or assign into the probed mod's defs, so the refresh engine
compares this list to the consuming repo's pinned one and refuses a dump
from any other boot (a sibling repo's refresh, a smoke test).
`collectedAfterStartup: true` is emitted only by a post-startup walk (the
settings button); consumers refuse it too.

4. **Settings UI** (standard `Mod`/`ModSettings` subclass):

- Checkbox list of **active mods** to probe (default: none; the family's
  three mods are simply ticked once on this machine). Persist packageIds.
  Ticking a mod pops a reminder dialog: consuming repos pin the probe boot's
  mod list (`CANONICAL_ACTIVE_MODS` in their refresh scripts), and a mod
  ticked here but missing there is not loaded during the run, so its dump
  fails. The tick is the memorable onboarding step; the dialog points at the
  forgettable one.
- Per-mod **output path** override (text field). Default:
  `<probe mod's own folder>/Output/<packageId>.json`. The point of the
  override is writing straight into each mod's **source repo** rather than
  its deployed Mods-folder copy — for this machine that means WSL UNC
  paths like `\\wsl.localhost\<distro>\home\shunt\dev\<Repo>\Scripts\...`.
  Verify plain `System.IO` writes to UNC paths work from the game; if they
  prove flaky, fall back to the default folder and let the WSL-side
  release script fetch from there.

5. **Failure loudly:** any exception per mod is logged with a `[L10nProbe]`
   prefix and a clearly invalid/absent output file — a release script must
   never mistake a partial dump for a complete one (write to a temp name,
   rename on success).

### 3a. Boot log dump (`Output/log-messages.json`, added 2026-08-28)

Serialises `Verse.Log.Messages` (decompile-verified 1.6.4871: static
`IEnumerable<LogMessage>`; `LogMessage` has public `text`, `type`
(`LogMessageType.Message|Warning|Error`), `repeats`, and a `StackTrace`
property RimWorld fills itself via `StackTraceUtility.ExtractStackTrace`).
Consumer: the family's startup smoke engine, `../smoke/startup_smoke.py`,
which needs levels a 1.6 Player.log no longer records.

```json
{
  "meta": {
    "schema": 1,
    "gameBuild": "1.6.4871 rev591",
    "trigger": "-l10nprobe",
    "messageCount": 14,
    "queueCapacity": 1000,
    "generated": "2026-08-28T00:00:00Z"
  },
  "messages": [
    {"type": "Error", "repeats": 1, "text": "...", "stackTrace": "..."}
  ]
}
```

- `queueCapacity` is `LogMessageQueue.maxMessages` read by reflection (null if
  unreadable): the queue drops its OLDEST message past that count, so a dump
  whose `messageCount` reaches it is possibly truncated and the smoke engine
  fails the run. Consecutive identical messages merge with `repeats` capped
  at 99.
- Messages that never pass through `Verse.Log` (a raw exception Unity logs
  itself) are not in the queue; the reader merges those from Player.log.
- Same write contract as the def dumps: temp file + rename, stale file
  deleted first, failure logged as `[L10nProbe] FAILED writing log dump` and
  never allowed to block the shutdown. Success logs
  `[L10nProbe] wrote log dump <path>`, which the smoke engine greps for.
- Not stable-sorted (it is chronological) and never checked into git.

## Non-goals

- No Keyed analysis (each repo's checker already validates Keyed completeness
  against its English source; "matching English (maybe ok)" is documented
  per-repo as deliberate).
- No per-language diffing, no translation writing — consumers do that.
- No backstories/strings-folder handling (the family's mods have none; add
  later only if a report section for them ever lights up).
- No Workshop packaging, no localization of the probe's own UI.

## Repo/mod conventions

- RimWorld 1.6 mod layout: `About/About.xml` (packageId `shunter.l10nprobe`),
  `1.6/Assemblies/`, C# source under `Source/` mirroring the family's csproj
  layout (auto-detect `RIMWORLD_PATH`, `Krafs.Rimworld.Ref` fallback). No
  Harmony dependency expected — everything is public API calls at startup —
  and none of the family's `MayRequire` gymnastics: the probe itself is
  DLC-agnostic.
- Load order: the probe relies on being last in the mod list (it can only see defs
  that are loaded); `About.xml`'s `loadAfter` and description say so.
- README: one paragraph — what it is, the `-l10nprobe` flag,
  and a pointer to the family repos' HANDOVER/release-skill integration.

## Acceptance criteria

1. With UMW+UWU+PWU active and configured, a `-l10nprobe` launch produces
   three JSON files and exits without user input.
2. The UMW dump's key set is a **superset of** the 44 entries in UMW's
   2026-07-30 in-game report (all now translated; see UMW commit `abd0a9b`'s
   `EXTERNAL_INJECTIONS` manifest for the exact 38 externally-sourced keys +
   6 `WeaponCategoryDef` labels), and covers every key currently present in
   UMW's language folders (superset of each language's translated key union,
   modulo `fullListAllowed` extras like UWU's `labelKeywords`).
3. The UWU/PWU dumps confirm those repos' current expectation: no
   externally-sourced keys beyond what their own def XML shows.
4. Repeated runs on an unchanged game+mod set produce byte-identical output
   (stable ordering, no timestamps beyond `meta.generated`).
5. A value another mod assigns to a probed def from a
   `[StaticConstructorOnStartup]` constructor is absent from a `-l10nprobe`
   dump: with Vanilla Expanded Framework active, PWU's
   `PWU_BladelinkCustomization.generalRules.rulesStrings` (VEF's
   `AutoAssignRules`) does not appear, where the in-game report lists it
   (verified 2026-10-03).
