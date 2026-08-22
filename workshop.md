# Steam Workshop localization conventions

Family-wide conventions for the `.steamworkshop/` folder each mod repo carries.
Nothing in that folder ships with a mod (the StageMod manifest never matches it)
or is loaded by RimWorld — it is publishing metadata for the mod's Workshop page.
A `Media/` folder for Workshop images can live beside it.

## Description/ layout

One file per language, named after the RimWorld language folders in
`1.6/Languages/` (`English.txt`, `German.txt`, `ChineseSimplified.txt`, ...).
English is the source of truth; the others are machine-assisted first passes
pending native review. Format:

- Line 1: the Workshop title for that language
- Line 2: blank
- Rest: the BBCode description

Every language present in `1.6/Languages/` should have a description file;
check for gaps whenever a language lands.

## Size limit: 8000 UTF-8 bytes, not characters

Steam's description save limit is **8000 UTF-8 bytes with CRLF newlines**
(what a browser textarea submits). The Workshop edit UI only counts
*characters* client-side, so an oversized paste passes the visible check and
then silently fails to save. CJK text (3 bytes/char) and Cyrillic
(2 bytes/char) hit the limit long before Latin scripts do — observed 2026-08
across the family: PWU Japanese/Korean/Russian and UWU/UMW Russian all failed
to save while every Latin-script sibling (largest: PWU French at 7988 CRLF
bytes) saved fine.

Practical budget: keep each body (everything after the title + blank line) at
or below 7700 CRLF bytes. For Russian that means roughly 2800 Cyrillic chars
of prose alongside typical BBCode/URL overhead — translations must be
noticeably terser than the English, not sentence-for-sentence. **The checker
enforces this** (error over 8000 bytes, warning within 200 bytes of it).

## Title conventions

- **Lean on vanilla vocabulary.** Each mod's English title deliberately reuses
  a vanilla term players search for (BTG: "Traders Guild"; UWU: Odyssey's
  "Unique Weapon"); every localized title must contain that language's
  vanilla-localized form of the same term. The specific anchor term is
  mod-specific — each repo's `.steamworkshop/README.md` names its own.
- **Fully localized, no English brand appended.** Workshop search is
  language-agnostic (any language's title matches regardless of UI language,
  verified 2026-08-12) and the preview thumbnail already carries the English
  name.
- **Title–settings coupling.** Each language's localized Workshop title must
  equal that language's localized mod-name Keyed value (the settings-window
  header: `BTG_Settings_ModName`, `UWU_SettingsCategory`, or the repo's
  equivalent — named in the repo's CLAUDE.md localization note). Always change
  the two together; the English pair keeps the English mod name in both.
  **The checker enforces this** (each shim names its key via
  `WORKSHOP_TITLE_KEY`), along with the file format above (both errors) and
  per-shipped-language description coverage (a warning, since Steam pastes
  are manual and CI's non-strict release gate must not fail on backlog).
  Staleness of the translated descriptions is the one part no check covers —
  the release skill's diff of `English.txt` against the last release tag
  remains the guard there.

## Publishing workflow

Steam has no API for per-language Workshop text, so updated files are pasted
manually into the Workshop page's per-language edit UI. Note Steam's own
language names differ from RimWorld's folder names: `schinese`, `koreana`,
`brazilian`, `latam`, ...

Each repo's `release` skill diffs `English.txt` against the last release tag
and refreshes the translations whenever it changed; after a release, list the
affected languages so each updated title and description gets pasted into the
Workshop edit UI.

## Description content

Translated descriptions follow the same grounding discipline as in-game
strings: vanilla-grounded terminology (see `languages/<Language>.md` and the
repo's own glossary), no new dashes the English source does not have, and
machine-assisted passes are labelled as pending native review in the repo's
`.steamworkshop/README.md`.
