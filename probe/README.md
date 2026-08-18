# L10nProbe

> A local-only RimWorld 1.6 dev mod that dumps the complete expected DefInjected key set of selected mods

**Never upload this to the Steam Workshop.** It is a build tool that happens to be a mod: it
adds no content and changes no behaviour. Its job is to call RimWorld's own def-injection
walker over the live `DefDatabase`, filtered to one mod at a time, and write the complete set
of translation keys that mod is expected to have — with current English values — to JSON. That
includes the keys no XML in the probed repo ever mentions (fields inherited from vanilla
`ParentName` defs, C# field defaults), which is exactly the class of localization gap a
hand-maintained manifest cannot see. Expected keys are language-independent, so nothing has to
switch language and the active one is irrelevant.

## Usage

- **Manual:** tick the mods to probe in the mod's settings window and press "Probe now".
- **Automated:** launch the game with `-l10nprobe` — it probes once defs are loaded and quits,
  no user input. This is the hook the family repos' release flows drive.

Output defaults to this mod's own `Output/<packageId>.json` (in the *deployed* mod folder). A
per-mod path override writes straight into a mod's source repo instead.

## Consumers

The dumps are consumed by the `Scripts/check-translations.py` checker every sidecar-bearing
repo in the mod family carries (a thin shim over the shared engine in `../checker/`), which
checks a dump in as a sidecar and fails when it is stale. Each repo's
`Scripts/refresh-translation-expectations.py` (a shim over `../refresh/`) regenerates its
sidecar by driving this probe in the deployed Mods folder. `Docs/SPEC.md` (local-only,
untracked) holds this mod's design and the decompile-verified API surface it is built on.

## Development

See [CLAUDE.md](CLAUDE.md) for build and deployment.
