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

## Decompile-verified API surface (RimWorld 1.6, verified 2026-07-30)

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
- **Which entries count as "must translate":** the report's missing-entries
  pass applies a further filter on top of the walker
  (`DefInjectionUtility.ShouldCheckMissingInjection` or equivalent — check
  its name/accessibility in `LanguageReportGenerator.AppendMissingDefInjections`;
  if internal, call via reflection rather than replicating its logic).
  Reuse the game's filter verbatim: divergence from the report is a bug.
- **Def type enumeration:** iterate the same universe the report does
  (see `AppendMissingDefInjections`; expected to be
  `GenDefDatabase.AllDefTypesWithDatabases()` — verify).
- **What the probe replaces:** `Verse.LanguageReportGenerator` — UI-only
  (debug action), refuses to run unless a non-English language is active,
  writes `TranslationReport.txt` to a fixed location, and diffs against the
  active language (which the probe deliberately does not: expected keys are
  language-independent; per-language diffing stays in each repo's checker).

## Behavior

1. **When triggered**, for each configured target mod: enumerate every def
   type, run the walker with `onlyFromMod`, apply the game's
   missing-injection filter, and write one output file per mod.
2. **Triggers:**
   - A **"Probe now"** button in the mod settings window (primary manual path).
   - **Command-line automation:** when the game is launched with
     `-l10nprobe` (check arg readability via `Verse.GenCommandLine`), run the
     probe automatically once defs are loaded (queue via `LongEventHandler`
     after `StaticConstructorOnStartup` time) and then **quit the game**
     (`Root.Shutdown()`). This is the hook release scripts drive.
   - Optional settings toggle: probe on every boot (no quit).
3. **Output** — one JSON file per probed mod, stable-sorted for git-diffing:

```json
{
  "meta": {
    "gameBuild": "<VersionControl.CurrentVersionStringWithRev>",
    "activeDlcs": ["Core", "Royalty", "Odyssey", "..."],
    "modPackageId": "...",
    "modName": "...",
    "generated": "2026-07-30T00:00:00Z"
  },
  "defInjections": {
    "ThingDef": {
      "UMW_Axe_Unique.tools.handle.label": { "english": "handle" },
      "UMW_Axe_Unique.label": { "english": "unique axe" }
    },
    "WeaponTraitDef": {
      "UMW_Lightweight.traitAdjectives": {
        "english": ["lightweight", "featherlight"],
        "isCollection": true, "fullListAllowed": true
      }
    }
  }
}
```

   Scalar entries may omit the flag fields (default false). `activeDlcs`
   matters because `MayRequire`-gated defs (e.g. UMW's Axe/Warhammer uniques
   need Royalty) only exist — and only emit keys — when their DLC is active;
   consumer scripts must be able to detect a probe run with the wrong DLC set.
4. **Settings UI** (standard `Mod`/`ModSettings` subclass):
   - Checkbox list of **active mods** to probe (default: none; the family's
     three mods are simply ticked once on this machine). Persist packageIds.
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

## Non-goals

- No Keyed analysis (each repo's checker already validates Keyed completeness
  against its English source; "matching English (maybe ok)" is documented
  per-repo as deliberate).
- No per-language diffing, no translation writing — consumers do that.
- No backstories/strings-folder handling (the family's mods have none; add
  later only if a report section for them ever lights up).
- No Workshop packaging, no CI, no localization of the probe's own UI.

## Repo/mod conventions

- RimWorld 1.6 mod layout: `About/About.xml` (packageId placeholder
  `shunt.l10nprobe` — confirm against the family's packageId convention),
  `1.6/Assemblies/`, C# source under `Source/` mirroring the family's csproj
  layout (auto-detect `RIMWORLD_PATH`, `Krafs.Rimworld.Ref` fallback). No
  Harmony dependency expected — everything is public API calls at startup —
  and none of the family's `MayRequire` gymnastics: the probe itself is
  DLC-agnostic.
- `loadAfter` everything it probes (or simply rely on it being last in the
  local mod list; document this in About.xml description).
- README: one paragraph — what it is, "never upload", the `-l10nprobe` flag,
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
