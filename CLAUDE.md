# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project Overview

**L10nProbe** is a local-only RimWorld 1.6 **dev tool shipped as a mod**: it dumps the complete
expected DefInjected key set (with current English values) of selected loaded mods to JSON, by
calling the game's own def-injection walker over the live `DefDatabase`. It adds no content and
changes no game behaviour. **Never uploaded to the Steam Workshop, no CI, no release flow.**

It exists to close a blind spot in the sibling mods' translation checkers — see
`../UniqueMeleeWeapons/HANDOVER.md` for the consumer side.

**Key technologies:** C# (.NET Framework 4.7.2), RimWorld modding API. No Harmony, no XML defs.

### Where documentation lives

- **`SPEC.md`** is the design authority: the decompile-verified API surface
  (`DefInjectionUtility.ForEachPossibleDefInjection` and friends), triggers, output schema,
  settings, acceptance criteria. Read it before implementing anything. Keep it current when the
  design changes — it is also what the consuming repos cite.
- **This file** holds only cross-cutting rules and rationale. Per-item detail lives in the
  header comment of the file it describes, as in the family's other repos.
- **`../UniqueMeleeWeapons/HANDOVER.md`** holds the integration plan on the consumer side.

## Build Commands

```bash
# Build (outputs to 1.6/Assemblies/ AND redeploys to the RimWorld Mods folder)
dotnet build L10nProbe.sln -c Release

# Stage the mod into an arbitrary folder (same manifest as the local deploy)
dotnet build Source/1.6/L10nProbe.csproj -c Release \
  -t:StageMod -p:StageDir=/path/to/output/L10nProbe
```

The build auto-detects the RimWorld install (Windows/Linux/Mac, including WSL targeting a
Windows install), falling back to the `Krafs.Rimworld.Ref` NuGet package when there is none.

**WSL setup:** `RIMWORLD_PATH` in `~/.bashrc` pointing at the Windows install, e.g.
`/mnt/c/Program Files (x86)/Steam/steamapps/common/RimWorld`.

Verifying a change end to end means launching the game — the probe only sees a loaded
`DefDatabase`. `"$RIMWORLD_PATH/RimWorldWin64.exe" -l10nprobe` dumps and quits (~1-2 min boot).

### Deployment

The repo lives outside the Mods folder; every local build redeploys.

- **One manifest, one place:** the `_ModFiles` ItemGroup in the `StageMod` target of
  `Source/1.6/L10nProbe.csproj`. This mod ships only `About/`, `LoadFolders.xml` and the
  assembly; a new content type needs a line there *and* a matching line in that target's wipe
  list, which is enumerated rather than a blanket `RemoveDir` **so that the deployed
  `Output/` folder survives a rebuild** (dumps land there; a wipe would eat ones a release
  script had not collected yet).
- **Stop hook (`.claude/hooks/sync-mod.sh`):** rebuilds+redeploys after a turn only when
  mod-relevant files changed, logs to `$TMPDIR/l10nprobe-build.log`, warns on failure.
  `.claude/` is gitignored, so this is local-only — if it is ever promoted to committed config,
  move the helper somewhere version-controlled.
- **Load order:** the probe must load **last**, after everything it probes. `About.xml`'s
  `loadAfter` lists the DLCs and the family's three mods; a newly probed mod belongs there too.

## Architecture

- **C#:** root namespace `L10nProbe`, sources under `Source/1.6/` mirroring the family's csproj
  layout. Startup work goes in `Core/L10nProbe_Startup.cs` (`[StaticConstructorOnStartup]`,
  post-def-load), never in the `Mod` constructor — that runs before any def exists.
- **No Harmony, no patches, no defs.** Everything is public API called at startup. A probe that
  altered game behaviour would compromise the dumps it exists to produce, so this is a rule and
  not just a fact about the current code. It also keeps the mod DLC-agnostic — none of the
  family's `MayRequire` gymnastics.
- **Logging convention:** `Log.Message($"{L10nProbeMod.LogPrefix} ...")` → `[L10nProbe] ...`.
  Release scripts grep for that prefix, so it is a constant, not a per-call-site literal.
- **Settings** (`Core/L10nProbeSettings.cs`, recipe in its header) are keyed by **packageId**,
  never by `ModContentPack`/`ModMetaData`, so a stored selection survives a session with the
  probed mod unloaded.
- **The probe's own UI is deliberately not localized** — plain string literals, no `Keyed/`
  files. It never ships (SPEC.md non-goals).

### Hard-won constraints

- **Reuse the game's filters verbatim; never re-implement them.** Which entries count as
  "must translate", and which def types are in scope, come from the same code
  `LanguageReportGenerator.AppendMissingDefInjections` uses — via reflection if a member is
  internal. Divergence from the in-game report is a bug, and the whole point of the probe is
  that it sees what the game sees.
- **Emit `suggestedPath`, not a reconstructed path.** The walker already applies
  `TranslationHandleUtility` list handles (`tools.handle.label`, not `tools.0.label`) and
  `TKeySystem` remapping; that string is what a translation file must use.
- **There is no JSON library.** RimWorld's `Managed/` ships no Newtonsoft, and
  `UnityEngine.JsonUtility` is class-shaped (no dictionaries), so the writer is hand-rolled.
  Output must be **stable-sorted and byte-identical across runs** (`meta.generated` aside) —
  consumers check dumps into git and diff them.
- **Fail loudly, never partially.** Any per-mod exception logs with the `[L10nProbe]` prefix and
  leaves no valid output file: write to a temp name and rename on success. A release script must
  never mistake a truncated dump for a complete one.
- **`meta.activeDlcs` is load-bearing.** `MayRequire`-gated defs only exist — and only emit
  keys — when their DLC is active, so a dump taken with the wrong DLC set is silently short.
  Consumers reject on it; always record it.

## Debugging

1. **Dev Mode:** Settings > Dev Mode > Logging.
2. **Log:** `%USERPROFILE%\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Player.log`
   (WSL: `/mnt/c/Users/*/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Player.log`).
3. **Inspect the API:** `ilspycmd "/mnt/c/.../RimWorldWin64_Data/Managed/Assembly-CSharp.dll" -t "Namespace.ClassName"`.
   Re-verify SPEC.md's API section against the installed build whenever RimWorld updates.
