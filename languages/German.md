# German — RimWorld localization mechanics

Grounded across the mod family: Persona Weapons Unbound's (PWU) 2026-07-28
de generation (no preseed — the first pass), extended by Unique Weapons
Unbound's (UWU) same-day pass (re-ran every preseeded row against the
Core/Royalty/Ideology/Odyssey/Anomaly/Biotech de tars and confirmed them),
Unique Melee Weapons' (UMW) 2026-07-28 pass (resolved the two questions PWU
had left open — both weapon/RulePackDef-specific and not carried here), and
consolidated with Better Traders Guild's (BTG) 2026-08-10 generation pass
(Core + Odyssey vanilla data), which re-verified the engine mechanics
against the 1.6 assembly and corrected an earlier family claim (see
Pitfalls below). No language in this family has had a native review yet.
RimWorld's language folder is `German` (tar: `German (Deutsch).tar`).

## Engine mechanics (LanguageWorker)

**Case is the German landmine, not gender** (decompile-verified:
`Verse.GrammarResolverSimple`, `LanguageWorker_German`, `LanguageWordInfo`).
`"key".Translate(args)` — i.e. any ordinary Keyed string — reaches
`GrammarResolverSimple`, not the full rulepack `GrammarResolver`. A plain
`string` arg becomes a `NamedArgument` with a null label and lands in that
class's `obj is string` branch, which supports `{0_gender ? m : f : n}`,
`{0_definite}`, `{0_indefinite}`, `{0_plural}` on a plain string, resolving
gender **from the word itself** via `LoadedLanguage.ResolveGender` →
`WordInfo/Gender/{Male,Female,Neuter,Other}.txt` (~2450 nouns in Core), with
no arg metadata required. `WithDefiniteArticle`/`WithIndefiniteArticle`
return **nominative only** (der/die/das, ein/eine).

**Correction (2026-08-10, re-verified against the 1.6 assembly): `lookup`
IS available in a plain Keyed string, superseding an earlier family claim
that `GrammarResolverSimple` implements no `lookup` function.** A
`{name: args}` span parses as a *function* call and reaches
`LanguageWorker.ResolveFunction`, which handles `lookup` and `replace`, so
`{lookup: {0}; decline; N}` and the 2457-row `decline.txt` case forms are
available in a plain Keyed string after all (the same mechanism Russian
uses against `Case.txt`). The confirmed tables: both `WordInfo/decline.txt`
(singular) and `WordInfo/plural_decline.txt` (plural) exist in Core *and*
Odyssey, sharing the header
`NOM;1_GEN;2_DAT;3_ACC;4_NOM_DEF;5_GEN_DEF;6_DAT_DEF;7_ACC_DEF` — so index
**3** is bare accusative and **7** is accusative-with-definite-article.
Vanilla's own two uses are worth copying verbatim: every site approach
string is `Greife {lookup: {0}; decline; 3} an` /
`Greift {lookup: {0}; decline; 3} an.`, and every
`messageDefendersAttacking` is
`{0} der Fraktion '{1}' greifen deine {lookup: {2}; plural_decline; 7} an.`

**A German lookup miss is genuinely harmless, unlike Russian's**
(decompile-verified): `LanguageWorker_German` does **not** override
`TryLookUp`, so the base implementation runs, and its miss branch returns
`keyName` — the *original*, not the lowercased probe key it built. A
mod-coined label therefore passes through with its capitalization intact
and simply stays in its base (nominative) form. (`LanguageWorker_Russian`
*does* override `TryLookUp` and lowercases the key first — the two
languages genuinely differ here; don't generalize either way.) So the
vanilla `lookup`/`decline` construct is safe to reuse even for a coined
label, and for a neuter noun a miss is additionally indistinguishable from
a hit, since German neuter accusative equals nominative.

What remains true is that de's article helpers are nominative-only and a
`decline` miss falls back to the key unchanged, so restructuring an oblique
slot is still the safer default when the injected label is mod-coined and
absent from the table. This is load-bearing, not theoretical: a symbol that
resolves through `WithDefiniteArticle` prepends a bare nominative
`der`/`die`/`das`, so an English source built on "… on \<the definite
noun\>" cannot be translated literally once that noun needs an oblique
case (e.g. "auf" needs no case change but a dative/accusative-governing
preposition does) — the sentence has to be rebuilt so the injected symbol
lands in a nominative slot instead. A gender lookup that misses **defaults
to masculine** (`ResolveGender`'s `defaultGender`) — safe only for vanilla
nouns in nominative slots, never for a mod-coined label absent from the
Gender tables.

**Inside a RulePackDef the full resolver runs, so `lookup` was never in
question there** — the opposite constraint (`GrammarResolverSimple`, not
`GrammarResolver`) applies only to `.Translate()`. Vanilla de rulepacks use
`{lookup: [SOME_label]; decline; 2}` freely; it resolves a noun label but
not a proper name, so prefer restructuring over relying on it for a proper
noun. (From RulePackDef naming-grammar work in the weapon-mod siblings;
generalizes to any RulePackDef, not just their own def types.)

`PostProcessed` also rewrites a trailing English `'s` to `s` (or a bare `'`
after s/ß/z/x/ce) — a closing ASCII single quote immediately followed by
lowercase `s` is silently mangled, so never write `'{0}'s` in German prose.

`LanguageWorker_German.PostProcessThingLabelForRelic` truncates a label to
its bare head noun (via `EndsWith`) whenever the underlying item becomes an
Ideology relic, matching against a hardcoded 26-noun list: Horn, Lanze,
Pulser, Werfer, Axt, Flinte, Bogen, Revolver, Gewehr, Stoßzahn, Stab,
Hammer, Schwert, Pistole, Dolch, Büchse, Kanone, Granaten, Granate, Keule,
Säbel, Messer, Rapier, Klinge, Sense, Speer; on no match it falls back to
the substring after the last space or hyphen. This is a generic vanilla
mechanic (not tied to any mod's own defs) — relevant whenever a mod's
`ThingDef` label might surface as a relic name. Note **Waffe is not on the
list**; Schwert, Hammer, Klinge, Messer, Speer, Keule, Axt and Stab are.

## Style and corpus findings

Style rules from the vanilla de data (mandatory, apply to any Keyed string
regardless of mod domain):

- **ASCII single quotes** for cited def labels and UI labels — vanilla
  writes `Forschungsprojekt '{0}'` and `Die Quest '{0}' erfordert …`.
  Core+Royalty Keyed ship 140 single-quoted placeholders and **zero**
  German `„…"`. Never use `„ "`, `» «`, or curly quotes. Pawn names are not
  quoted.
- **If a dash is genuinely unavoidable it is an en dash `–`, never an em
  dash `—`** (20 vs 0 in Core Keyed). German joins main clauses quite
  happily with `:` and `,` instead, unlike English, so reflow into one of
  those rather than introducing a dash the English source doesn't have.
- Ellipsis is ASCII `...` (74 in Core Keyed, `…` zero).
- Descriptions end with `.`; labels and buttons take none. Player-facing
  prose is informal **du** with imperatives, never Sie — **except scenario
  prose, where Odyssey de addresses the crew as ihr/euch**
  (`TheGravship.description` and its GameStartDialog). Both registers are
  vanilla-attested; pick per context, not uniformly.
- **`reportString`s keep the trailing period and are third-person present
  verbs** — e.g. `entfernt TargetA.`, `füttert TargetB mit TargetA.` This
  is the opposite of Russian and Korean, which both drop the period on
  this string type; don't carry that habit over into German.
- `RecipeDef.label` is `X herstellen` with **no article** (Core
  `Make_ComponentSpacer` = Hightech-Bauteil herstellen); `jobString` is
  third-person `Stellt X her.` **with** a period, matching the
  `reportString` register above.
- Research labels are lowercase noun phrases (Hightech-Fabrikation, lange
  Klingen, mehrläufige Waffen, Maschinenbau, Schmieden) or verb-final
  phrases (Bier brauen, Maschinenpersona überreden).
- Units: vanilla de writes percentages **tight** (`{0}%`) and hours tight
  (`{0}h`), but watts **spaced** (`{0} W`, 6 occurrences). Copy per unit
  rather than applying one rule across the board.

**Stuff-naming inverts in German** — a generic Core mechanic, not tied to
any mod's own defs. `ThingMadeOfStuffLabel` is `{1} aus {0}` where English
is `{0} {1}` ("wooden longsword" → "Langschwert aus Holz", not "hölzernes
Langschwert"). Correspondingly de Core defines `stuffProps.stuffAdjective`
for only 9 defs, because the prepositional frame replaces the adjective,
and **every value is a bare noun built for that dative frame**: `Holz`,
`Gold`, `Granit`, `Marmor`, `Kalkstein`, `Schiefer`, `Sandstein`,
`Vakuumstein`, and decisively `Leather_Heavy` = **`dickem Fell`**, already
dative-inflected. Where `stuffAdjective` is absent, the fallback is the
stuff's plain `label`, which in German is likewise always a noun (`Stahl`,
`Plastahl`, `Uran`, `Jade`, `Silber`). Any mod defining a custom
`stuffAdjective` (or relying on the label fallback) should build on the
`aus [noun]` frame rather than trying to prepend an inflected adjective.

**Material colour labels split by kind:** vanilla capitalizes material
colours as nouns (Gold, Jade, Silber) but keeps purely descriptive colours
as lowercase adjectives (grau, schwarz).

**A pre-inflected vanilla string can be untemplatable.** Core's
`NormalQualityOrBetter` renders as "normale Qualität oder besser" — already
inflected for its one fixed use, and quality tiers are adjectives that
would otherwise need gender/case agreement with whatever noun follows. A
template built on the same pattern (e.g. "{0} quality or better") is safer
reshaped as `Qualität {0} oder besser`, putting the injected label after
the noun so no agreement is required.

## Grounded common vocabulary

Core/DLC-grounded terms usable by any mod in the family (verbatim vanilla
strings unless noted):

| English | Use | Never | Why |
|---|---|---|---|
| Cancel / Reset / Confirm / Randomize | Abbrechen / Zurücksetzen / Bestätigen / Zufällig | | Core buttons |
| Reset to defaults / default | Auf Standard zurücksetzen / Standard | Standardwerte wiederherstellen | Core `ResetBinding`, `Default` — de's settings-page verb for "reset" collides with plain `Reset`, so the keybinding-specific phrasing is the one that disambiguates |
| None | Nichts | Keine, Kein | Core `None` |
| quality / tiers | Qualität / übel·schlecht·normal·gut·exzellent·meisterlich·legendär | | Core `Quality`, `QualityCategory_*` |
| trader / orbital trader | Händler / Orbitalhändler | | Core `Silver`-era vocabulary; Odyssey `TradersGuild.description` |
| bulk / exotic goods trader | Großhändler / Händler exotischer Güter | | Core orbital `TraderKindDef`s |
| Traders will pay more/less for it. | Händler werden mehr dafür bezahlen. / … weniger dafür bezahlen. | | Odyssey WeaponTraitDef descriptions — verbatim |
| goodwill / caravan / negotiator | Ruf / Karawane / Unterhändler | Wohlwollen | Core `Goodwill`, `Caravan.label`, `Negotiator` |
| silver / market value / comms console / packaged survival meal | Silber / Marktwert / Funkanlage / Überlebensration | | Core |
| steel / vacuum / safe / power output | Stahl / Vakuum / Tresor / Leistungsabgabe | | Core |
| orbital platform / settlement platform | Orbitalplattform / Siedlungsplattform | | Odyssey `OrbitalPlatform.label`, `SettlementPlatform.label` |
| orbital settlement / settlement | orbitale Siedlung / Siedlung | | Odyssey `SpaceSettlement.label`, Core `Settlement.label` |
| shuttle | Raumfähre | Shuttle | Core `Shuttle.label`, Odyssey `Shuttles.label` (shuttle engine = Fährentriebwerk) |
| drop pod vs cargo pod | Landekapsel vs Vorratskapsel | | Core `DropPodIncoming` / `CargoPodCrash` — distinct, don't merge |
| signal jammer / sentry drone / life support unit | Signalstörer / Wächterdrohne / Lebenserhaltungseinheit | | Odyssey |
| gravship / gravlite panel / pilot console | Gravschiff / Gravlitplatte / Pilotenkonsole | | Odyssey |
| mechhive / orbital relay | Mechnest / Orbitalrelais | Mechbau | Odyssey `Mechhive.label`, `TheGravship.description` |
| hostile to {0} | Feindliche Beziehungen zur Fraktion '{0}' | | shaped from Core `QuestHostileTo` |
| {0} from {1} are attacking your {2}. | {0} der Fraktion '{1}' greifen deine {lookup: {2}; plural_decline; 7} an. | | every vanilla de `FactionDef` — verbatim; demonstrates the `lookup`/`decline` mechanism above |
| Attack {0} / Attacking {0}. | Greife {lookup: {0}; decline; 3} an / Greift {lookup: {0}; decline; 3} an. | | Core site approach strings — verbatim |
| Quest failed: [resolvedQuestName] | Quest gescheitert: [resolvedQuestName] | | Core `TradeRequest` — verbatim |
| [faction_name] became hostile to you. | Die Fraktion [faction_name] wurde dir gegenüber feindselig. | | Core `TradeRequest` — verbatim |
| starting people (ScenPart) | Anzahl Startcharaktere | | Core `ConfigPage_ConfigureStartingPawns.label` — identical English source, reuse verbatim |
| reportStrings (clean/rescue/tend/feed/hack/open/board) | entfernt TargetA. / rettet TargetA. / behandelt TargetA. / füttert TargetB mit TargetA. / hackt TargetA. / öffnet TargetA. / betritt TargetA. | | Core `JobDef`s — verbatim; an NPC-safe copy of these JobDefs can reuse them 1:1, trailing period and all |
| quest | Quest | Auftrag (that's de's word for bills/recipes) | Core `Quest`, MainButton `Quests.label` |
| relic | Reliquie | Relikt | Ideology `Relic`, `RelicOf` (reliquary = Reliquienschrein) |
| ideoligion / reform | Ideologie / Ideologie reformieren | Ideoligion | Ideology `IdeoligionOf`, `ReformIdeoligion` — de uses the plain word, no portmanteau |
| tech levels | neolithisch / mittelalterlich / industriell / Raumfahrt / Ultra / Archotech | Weltraum, Ultratech | Core `TechLevel_*`; "tech level" itself is Techstufe |
| wood / plasteel / uranium / jade / steel / silver / gold | Holz / Plastahl / Uran / Jade / Stahl / Silber / Gold | Plasteel, Plastik | Core labels — Plastahl is translated, unlike some other family languages |

## Pitfalls and lessons

- **Resolved conflict (lookup availability):** an earlier family note
  (from UWU's and PWU's 2026-07-28 passes) claimed
  `GrammarResolverSimple`/`LanguageWorker_German` "implements no `lookup`
  function," making case declension unreachable outside a RulePackDef.
  BTG's 2026-08-10 pass, re-verified against the 1.6 assembly, corrects
  this: `lookup` **is** available in a plain Keyed string via
  `LanguageWorker.ResolveFunction`, with `decline.txt`/`plural_decline.txt`
  as the backing tables (see Engine mechanics above). The corrected finding
  wins; do not restructure around the old "no lookup" premise.
- **RulePackDef namer lists must tag each entry with its grammatical
  gender.** Vanilla de namer grammar marks every noun with an `|M|`/`|F|`/
  `|N|` prefix and strips it later with `{replace:}` to emit the right
  article/adjective ending; an unmarked entry leaves nothing for the
  `{replace:}` slot to match and produces a broken name. (From weapon-mod
  namer work; generalizes to any RulePackDef namer list that needs gender
  agreement, not just weapon names.)
- **Attributive adjectives fed into RulePackDef concatenation must be bare,
  uninflected stems** — the resolver appends `-er`/`-e`/`-es` (strong
  declension) or `-e`/`-en` after a definite article (weak declension), so
  a stem already ending in `-e`/`-er`, containing a space, or actually a
  noun breaks the concatenation. This differs from a bare Keyed adjective
  used standalone (e.g. a gizmo label), which vanilla writes uninflected
  with no markers at all — check which context a given field feeds before
  choosing a form.
- Never write `'{0}'s` — see `PostProcessed`'s `'s`-rewrite above; the
  checker cannot see this, it's a runtime string mangling.
- A gender/case miss on a mod-coined label is forgiving in German (masks
  as masculine nominative, or passes through unchanged on a `lookup` miss)
  but never assume the same shape holds in another family language —
  Russian's `TryLookUp` override lowercases the key on a miss, which German
  does not do.
