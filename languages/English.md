# English — the player-facing register

English is the family's source language, so this file is read at a different
moment from the other `languages/*.md`: **whenever player-facing text enters
a repo** (def labels and descriptions, `Keyed/` strings, `About.xml`, the
Workshop page), not at translation time. Every consuming repo's CLAUDE.md
points here. It came out of the Medic Warcasket pass of 2026-11-04, after a
settings page read as generated, and applies to every mod in the family;
the section "The tells to remove" is also the template each target
language's own "Generated-text tells" section follows, because a tell in the
English ships in every translation.

The mechanical tells (dashes, semicolons, "Whether" openers, parenthetical
asides) are enforced by the checker (`check_translations.py`, "player text"
warnings; errors under `--strict`, so a release cannot ship them). The
judgment tells below are a read, done when the text is written and again at
release over the strings that changed since the last tag.

## 1. What vanilla sounds like

Vanilla's text is plain, slightly informal, and happy to be a little wordy. It
names things by their visible noun ("the armor", "the target"), uses future
tense for consequences, and explains what a thing does for the player, not how
the code reaches it. Real examples from the game's `Data/` folder, each the
shape to copy:

| Kind of text | Vanilla example |
|---|---|
| Option label | "Pause on load", "Autosave interval", "Screen shake intensity" |
| Slider tooltip | "The number of in game days between each auto save." |
| Toggle tooltip | "When enabled, the camera will quickly pan when focusing on a new location. When disabled, the camera will jump instantly." |
| Difficulty tooltip | "Adjust the speed of research." / "Allow wild predators to hunt humans." |
| Ability description | "Block pain pathways in the target's brain for a short time. This can allow a person to move and act even with grievous injuries which would normally incapacitate them." |
| Ability description | "Use special glands in the wrists to quickly tend someone's wounds." |
| Hediff description | "Go-juice in the bloodstream. It supercharges combat-related abilities, and instantly increases psyfocus when first injected." |
| Stat description | "Speed at which the character tends to wounds and illnesses." |
| Rejection message | "{0_labelShort} is downed." / "{0_labelShort} is already inspired." / "Cannot shoot in melee." |
| Trait description | "{PAWN_nameDef} gets a rush from hurting people, and never minds the sight of blood or death. {PAWN_pronoun} is four times as likely to start a social fight as others." |
| Apparel description | "A suit of powered armor. Layered plasteel-weave plates are very effective at stopping attacks, with few vulnerable joint sections. Neuro-memetic assistors allow a human to wear the armor and still move easily.\n\nArmor like this is often used by rapid-incursion space marines." |
| Job report string | "tending to TargetA." |

A mod that extends another mod sits beside that mod's text in the same lists,
so the base mod's register is the ceiling where it is looser than vanilla
(see the VFE Pirates domain section below for the worked case).

Where to find the corpus (the local install; in WSL the Windows path is
`/mnt/c/Program Files (x86)/Steam/steamapps/common/RimWorld`, the Linux one
`~/.local/share/Steam/steamapps/common/RimWorld`):

```
Data/Core/Languages/English/Keyed/Menu_Options.xml                       option labels and tooltips
Data/Core/Languages/English/Keyed/Messages.xml, Misc_Gameplay.xml, GameplayCommands.xml   rejection messages, gizmo text
Data/Core/Languages/English/Keyed/Dialogs_Various.xml (Difficulty_*_Info)  settings-page tooltips
Data/Royalty/Defs/AbilityDefs/*.xml, Data/Biotech/Defs/AbilityDefs/*.xml   ability descriptions
Data/Core/Defs/HediffDefs/*.xml, Data/Core/Defs/Stats/*.xml, Data/Core/Defs/TraitDefs/*.xml
<base mod checkout>/<version>/Defs/**/*.xml and Languages/English/Keyed/*.xml  the base mod's own text
```

Grep these rather than reading whole files; one
`grep -rhoE '<description>[^<]*</description>'` over a def folder gives a
sample in seconds.

## 2. The tells to remove

Readers flag text as generated from patterns that recur across many strings,
more than from any one sentence. Look for these across the whole Keyed file,
not string by string. Each target language's file carries the same list
instantiated for that language, plus calque (English syntax under native
words), under "Generated-text tells".

1. **The same sentence frame on every setting.** The Medic pass had seven
   tooltips of the shape "A suite already holding more than this loses the
   excess" / "A shot already given keeps its own clock". Vanilla never
   documents what happens to in-flight state when an option changes. Cut them
   all; keep at most one where the behavior would truly surprise.
2. **"Whether ..." tooltip openers.** That is docstring voice. Toggles take
   vanilla's frame: "When enabled, X will Y. When disabled, Z."
3. **Telegraphese.** Clipped present-tense fragments with no "will", "can" or
   "also": "Its levels scale with it." "Queued dressings wait it out." "and
   the skill sets the pace." Vanilla writes consequences in future tense and
   spends the extra words. An over-corrected text that avoids every flourish
   reads as generated too.
4. **Balanced tricolons and aphoristic closers in lore.** Three parallel
   clauses, then a line like "diagnoses what no bandage treats" or "holds out
   long after its bandages run out". Vanilla says what the thing is for and
   stops.
5. **Sentence-initial participle clauses.** "A long crash follows, leaving
   them dull and slow." Vanilla: "Afterward they will crash for hours,
   becoming dull and slow" is fine; the participle hanging off a short
   abstract subject is the tell.
6. **Hyphenated coinages and possessive chains.** "medicine-laden",
   "spacer-tier combat-medic", "the shoulders' injector", "the suite's
   gauge". Name the visible item: "the shoulders", "the medicine gauge".
7. **Semicolons, colon pivots and parenthetical asides** in tooltips and
   descriptions. Vanilla almost never uses them. Dashes are banned outright
   in player text (the checker warns; `--strict` fails).
8. **Signature phrases repeated across surfaces.** The same coined phrase
   ("on the spot", "free to doctor", "a while longer", "dull and slow") in
   About, the descriptions, the abilities and the Workshop page. Say it once;
   elsewhere say it plainly.
9. **Over-explanation.** A tooltip teaching geometry ("a range of 1.9 reaches
   every adjacent cell, diagonals included") or restating a mechanic the
   row's value already shows.
10. **Modder vocabulary.** "definitions", "defs", "caring work types",
    internal subsystem names ("the suite", "the stream") that the player
    never sees labeled anywhere.

## 3. Recipes by text type

- **Option label.** Two to four words, a noun phrase, sentence case: "Kit
  capacity", "Casting time", "Raider medics give adrenaline shots". Units go
  in the shown value, or in the label in parentheses ("Cooldown (hours)").
  Both are fine; stay consistent within one mod.
- **Slider tooltip.** One or two sentences. "The number of ..." / "The time
  ..." / "How long ..." then at most one sentence of consequence. Mods whose
  rows show "(default)" only while unset append "Default: {0}." Example:
  "The time the pilot must wait after a dressing before starting another.
  Default: {0}."
- **Toggle tooltip.** "When enabled, ... will .... When disabled, ....
  Default: {0}." Both halves, even when one is obvious, because that is the
  vanilla shape.
- **Item picker tooltip.** "The <thing> loaded into the <item>, one per
  <charge>. <One sentence on what the choice changes>. Default: {0}."
- **Section summary line.** Plain declaratives with the numbers inline, no
  passives: "The cooldown after a dressing is {5}." not "Each dressing is
  followed by {5} of cooldown."
- **Ability description.** Imperative opener naming the action and the
  target ("Inject a nearby person or animal with ..."), then one to three
  sentences of effect in future tense ("Afterward they will ..."), then any
  condition as "If ..., ... will ... instead." Two to four sentences total.
- **Hediff description.** "<Substance> in the bloodstream. It <effect>, then
  <effect>." One or two sentences. Stage labels are one or two lowercase
  words.
- **Stat description.** "The <quantity> ..." in one sentence, with a second
  sentence for the exception. Vanilla's "Speed at which the character tends
  to wounds and illnesses." is the ceiling for terseness.
- **Rejection message.** One clause: "{0} is hostile." "{0} has no wounds to
  tend." "{0} already has an adrenaline shot." Match the hediff's labelNoun
  the way vanilla's "{0} is already inspired" matches the inspiration label.
- **Trait description.** Keep the base mod's sentences where the trait sits
  beside the base mod's own trait in the same list, and change only the
  clause that differs.
- **Apparel and item description.** Vanilla's three-part shape: what it is,
  how it protects or works, who uses it, in two or three short paragraphs.
  A mod extending another mod follows that mod's description shape instead
  (VFE Pirates below).
- **Job report string.** Present participle, lowercase, trailing period:
  "tending to TargetA.", "giving TargetA an adrenaline shot."
- **About.xml description.** Two or three short paragraphs: what the mod
  adds, what each piece does, what it supports. Use the dependency's full
  display name once ("Vanilla Factions Expanded - Pirates"); after that the
  short form is fine.

## 4. Length

Vanilla is short per string but not clipped. Use these as ceilings, measured
against the closest vanilla or base-mod equivalent, not against the previous
draft:

| Text | Vanilla ceiling |
|---|---|
| Option tooltip | 2 sentences, about 30 words before "Default: {0}." |
| Difficulty-style toggle tooltip | 2 sentences |
| Ability description | 4 sentences, about 60 words |
| Hediff description | 2 sentences, about 30 words |
| Stat description | 2 sentences |
| Rejection message | 1 clause |
| Trait description | 3 to 4 sentences |
| Item description | 3 paragraphs; a lore paragraph 60 to 120 words |
| Section summary (mod settings) | 3 sentences |

A rewrite that fixes voice usually grows a little, because "When enabled ...
When disabled ..." and future tense cost words. After the pass, measure each
changed string against its ceiling and trim by removing a whole clause, never
by compressing the grammar back into telegraphese. Keep, in order: the
condition the player must know (what the setting changes), the consequence,
the default. Drop first: restated mechanics, the second half of a symmetric
toggle sentence when it only negates the first, and edge cases.

## 5. Process

Writing new text: read sections 2 and 3 for the text type, write it in the
recipe's shape, run the checker. Reviewing a mod's existing text:

1. **Gather the mod's text in one place.** Keyed file,
   `grep -nE '<(label|description|labelNoun|reportString)>'` over `Defs/`,
   `About.xml`, and the `.Translate(` calls in the C# source to catch any
   string assembled in code.
2. **Gather the comparison corpus** from the paths in section 1: the vanilla
   strings of the same kind for every kind of text the mod has, and the base
   mod's equivalents.
3. **Review for the tells in section 2 across the whole set first**, then
   string by string. Report findings with a suggested rewrite each; leave
   lore paragraphs that carry the mod's voice to the author unless asked.
4. **Apply with an exact-match script** (a Python replace that fails on zero
   or multiple matches) so no string changes silently. Check the def
   headers, C# comments, README and Workshop page for rationale or quotes of
   the old wording; design specs that quote pre-landing drafts can stay.
5. **Rebuild, run the tests, run the translation checker.** The checker
   compares the English text against the checked-in sidecar and fails on any
   change; regenerate the sidecar with the repo's refresh script (game
   closed, it boots the probe) before committing.
6. **Second pass for length** (section 4) on only the changed strings,
   against the vanilla ceilings, without reintroducing the tells.
7. Translations come after, through the repo's translate skill, never in the
   same pass.

## 6. Checklist

- [ ] No tooltip opens with "Whether".
- [ ] Every toggle tooltip reads "When enabled ... When disabled ...".
- [ ] No sentence frame repeats across more than two strings.
- [ ] No semicolons, dashes or parenthetical asides in player text.
- [ ] No hyphenated coinage that vanilla does not already use.
- [ ] Ability descriptions open with an imperative and use "will" for consequences.
- [ ] Rejection messages are one clause and name the pawn with `{0}`.
- [ ] Shared lore paragraphs are verbatim from the base mod's sets of the same generation.
- [ ] Each changed string is at or under its vanilla ceiling.
- [ ] Translation sidecar regenerated; checker, build and tests green.

## VFE Pirates warcasket domain

VFE Pirates (the warcasket mods' base mod) is looser than vanilla: longer, a
little awkward, with the tactical role spelled out ("Because of this, this
series is somewhat lacklustre when operating solo...") and a catchphrase in
quotes at the end of a lore paragraph. Every set of one warcasket generation
shares its generation paragraph word for word; a new set in that generation
pastes the paragraph verbatim and writes only a "The <Series> series ..."
paragraph of its own. The corpus:

```
<VFEP checkout>/1.6/Defs/ThingDefs_Misc/Apparel_*.xml   warcasket descriptions
<VFEP checkout>/Languages/English/Keyed/*.xml            VFEP's own UI strings
```

- **Warcasket description.** Three paragraphs. First line: "Specialized
  spacer-tech warcasket <piece> with <protection>, equipped with <module>
  that <does what>." (VFEP says "equipped with", not "fitted with".) Second:
  the generation paragraph, pasted verbatim from a VFEP set of the same
  generation (American spelling, as vanilla). Third: "The <Series> series
  ..." in VFEP's functional voice, saying what each piece does and where the
  set belongs in a fight, with a quoted catchphrase if one fits. The first
  line is also the `shortDescription`. The series paragraph is 60 to 120
  words.
- **Warcasket trait.** VFEP's own sentences, changing only the clause that
  differs: "No amount of pain will have an effect on {PAWN_objective}, and
  {PAWN_pronoun} can never go into a pain shock or drop unconscious due to
  pain. Because of how bulky the armor is and how much energy it takes to use
  it, {PAWN_nameDef} is not capable of most work, but can still do doctor
  work."
- **Settings.** The warcasket mods append "Default: {0}." to every tooltip
  and show units in the row's value, not the label.
