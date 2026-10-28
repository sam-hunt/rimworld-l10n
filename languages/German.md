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
**`Pluralize` is the English worker's, with the `plural` lookup first**
(decompile-verified 2026-10-11): `LanguageWorker_German.Pluralize` delegates
to `LanguageWorker_English.Pluralize`, which tries `TryLookupPluralForm`
against the active language's `plural` table (Core's `WordInfo/plural.txt`,
auto-generated from Core labels and thin: no `Sprung`, no `Einheit`) and
otherwise appends `s`. A coined compound in a `{X_plural}` slot therefore
ships as `…s` unless the mod supplies the line itself in
`Languages/German/WordInfo/plural.txt` (`Treibstoffeinheit;Treibstoffeinheiten`);
the table is assembled from every mod's language folder, lowercase file
name (see `lessons.md`). The `plural_decline` lookup that
`CommandReload_NoCharges` applies to that plural misses harmlessly, as
above, so the dative plural reads as the nominative plural, identical for
an `-en` plural.

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
| advanced fabrication (research) | Hightech-Fabrikation | | Core `AdvancedFabrication.label` — verbatim (verified 2026-08-18) |
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | Megapascal spelled out in a label | CE 16.7.4 ships no German (its `Languages/German/Keyed/Text.xml` is a stray Achtung! file), so CE's own info card shows the English `CE_MPa`/`CE_mmRHA`; DIN 1301 symbols are the same |
| blunt armor / sharp armor | Rüstung - Wucht / Rüstung - Schnitt | stumpf, scharf | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; Wucht/Schnitt are the damage classes in prose too |
| flak vest / flak jacket / frag grenade | Schutzweste / Schutzjacke / Splitterhandgranaten | Flakweste | Core labels — verbatim; the grenade label is plural in de |
| spacer-tech (attributive) | aus der Raumfahrttechnik | | Core `Plasteel.description` / `Synthread.description` render "spacer-tech" exactly so |
| Imperial (adj.) | imperial (imperiale, imperialen ...) | | Royalty `PawnKinds_Empire` (imperialer Grenadier), `Apparel_ArmorRecon.description` (imperialen Spähtrupps) |
| respirator / breathing | Atemgerät / Atmen, Atemleistung | | Odyssey research story "Atemgeräten"; Core `Breathing` = Atmen |
| sealed (airtight) | luftdicht versiegelt | | Odyssey `GravshipHull.description` "luftdichte Wand" |
| chemfuel | Sprit | | Core `Chemfuel.label` |
| mod (noun) | die Mod | | Core Keyed `ModLoadFolder...` "About.xml der Mod" |
| Off / On / When enabled / When disabled (settings) | Aus / an / Wenn aktiviert / Wenn deaktiviert | | Core Keyed `Off`, `On`, `CommandAllowCutDesc` |
| cooldown / cells | Abklingzeit / Zellen | | Core Keyed `CooldownTime`, `MapSizeDesc` |
| Odyssey (DLC name) | Odyssey | | Core `ExpansionDef` `Odyssey.label` keeps the English name |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | setzt Fähigkeit '{0}' ein. | | VEF ships English only; third-person present like Core's `JobDef.reportString`s, trailing period kept (Shipcracker Warcasket, shipped since 2026-09-26) |
| on cooldown (a reloadable comp's `cooldownGerund`) | klingt gerade ab | | Vanilla's default for `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker Warcasket) |

## Grounded common vocabulary, VFE Pirates warcasket domain (coined in Shipcracker Warcasket's 2026-09-26 pass, extended by Toxin Warcasket's 2026-10-13 and 2026-10-22 passes; 2026-10-28)

VFE Pirates ships English only, and no community German translation could be
grounded against: a Workshop pack "Vanilla Factions Expanded - Pirates
Deutsch" (id 2810180496) exists, but its page shows none of its terms and its
files were not available, so every VFEP term here is a family coinage pending
native review. If that pack's files turn up, re-ground these rows against them
and prefer its renderings. Every warcasket set in the family (Shipcracker,
Toxin, Medic, Overlord) renders these terms alike so the sets read as one
family in-game; a change is made here first and each set's shipped files
follow at its next pass. A set's own name, its Workshop title and its own
coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket | Kriegssarg (m.), pl. Kriegssärge | Literal war + coffin, mirroring the English compound and vanilla's war- → Kriegs- pattern (`MeleeWeapon_Zeushammer` = Kriegshammer). Does not collide with Core's coffin furniture, whose label is `Sarcophagus` = Sarkophag ("Sarg" appears only inside that def's description, never as a label in Core, Royalty or Odyssey). Masculine, like every label head in the sets, so the Gender-table miss default (masculine) is correct. Rejected: Kriegssarkophag (collides with Sarkophag and doubles up in VFEP's Sarkophag set), Kriegskapsel (vanilla casket = Kapsel, but loses the coffin sense and reads as a drop pod), Panzersarg (invites a tank reading and clashes with Schulterpanzer), Kampfsarg (Kriegs- mirrors the English war- and vanilla's Kriegshammer), Kriegsrüstung / Kriegshülle (lose the sealed-coffin sense; Rüstung is vanilla's generic armor), the English loan (vanilla de translates its coined nouns: Plastahl, Sprit). |
| compound rule for Kriegssarg | always hyphenated to a set name or part: `<Set>`-Kriegssarg, Kriegssarg-Helm, Kriegssarg-Hülle, Kriegssarg-Schulterpanzer, Kriegssarg-Gießerei | Durchkopplung once a set prefix is present; kept uniform in descriptions too so labels and prose match. |
| `<set>` warcasket / shoulders / helmet (label pattern) | `<Set>`-Kriegssarg / `<Set>`-Kriegssarg-Schulterpanzer / `<Set>`-Kriegssarg-Helm | VFEP's `<set> warcasket <part>` label pattern. |
| pauldrons / shoulders / shoulder pads | Schulterpanzer | Ordinary German armor term for VFEP's "warcasket shoulders" and the Workshop "shoulder pads". Rejected: Schultern (reads as the body part), Schulterstücke (reads as uniform epaulettes). |
| warcasket shell | Kriegssarg-Hülle | Per the compound rule. |
| warcasket foundry | Kriegssarg-Gießerei | foundry = Gießerei per Core `FoundryApprentice76.title` = Gießereilehrling. Rejected: Kriegssargschmiede (Schmiede is vanilla's smithy), Kriegssarggießerei unhyphenated (hard to read). |
| entomb | einsargen | Real German verb (to put into a coffin), derived directly from Kriegssarg. The Workshop page's "weld" stays einschweißen, as in English. Rejected: einschließen (too weak), einmauern (walling in, wrong image), bestatten (burial). |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | 'Raumfahrt-Kriegssärge' / 'spezialisierte Kriegssärge' | Core `TechLevel_Spacer` = Raumfahrt; single-quoted as a cited label per this file, lowercase adjective start per its research-label rule. |
| VFEP set names | Belagerungsbrecher (siegebreaker), Rohling (brute), Wächter (guardian), Kontrolleur (controller), Sarkophag (sarcophagus), Luft-Kriegssarg (aerial), Kataphrakt (cataphract; Kataphrakt-Entwurf, Kataphrakt-Chassis), Gefahrenschutz (hazard; Gefahrenschutz-Kriegssarg, das Gefahrenschutz-Set) | Plain coinages hyphenated to Kriegssarg per the compound rule, all pending native review except Sarkophag (Core `Sarcophagus` label) and Kataphrakt (Royalty `Empire_Fighter_Cataphract.label` = Kataphrakt, `Apparel_ArmorCataphract.label` = Kataphraktrüstung). Gefahrenschutz renders the hazmat set as "hazard protection". |
| 7th generation / 10th generation (VFEP's two chassis) | die Kriegssärge der 7. Generation / das Raumfahrt-Chassis der 10. Generation | Shipcracker's and Toxin's prose; VFEP's dashed aside on the 7th generation is reflowed as "die zwar untereinander austauschbar sind, im Set aber besser funktionieren". |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | Eine spezialisierte Kriegssarg-Hülle / Spezialisierte Kriegssarg-Schulterpanzer / Ein spezialisierter Kriegssarg-Helm mit überlegenem Schutz und höherem Gewicht | Toxin Warcasket's shipped `shortDescription`s; plain description wording. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | Eine spezialisierte Kriegssarg-Hülle / Spezialisierte Kriegssarg-Schulterpanzer / Ein spezialisierter Kriegssarg-Helm aus der Raumfahrttechnik mit Standardschutz | "aus der Raumfahrttechnik" is Core's "spacer-tech" (main table); Shipcracker's variant ends "mit verbesserter Stoßverteilung" for its "improved impact dispersion"; "standard" as in Shipcracker's Standardschild. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | Die Kriegssärge der 10. Generation gingen eigentlich aus erbeuteten Piratenmodellen hervor, ... selbst über Generationen hinweg. | Translated, no pack; the full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/German/`. power armour = Powerrüstungen (Core `Fabrication.description`); dreadnoughts = wandelnde Schlachtschiffe; "armour series" = Baureihen. |
| pilot (the wearer) | Pilot | Core/Odyssey (Pilotenkonsole, Pilotenassistent); Shipcracker's prose. |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | Raumfahrt-Panzerung und -Isolierung / Schutzschild / Hightech-Bauteile | Core `Insulation_Cold.label` (Isolierung), `Make_ComponentSpacer.label` (Hightech-Bauteil); Schutzschild per Core `Apparel_ShieldBelt.description` "persönlichen Schutzschild". |

Pending native review for the whole family: Kriegssarg, Kriegssarg-Gießerei,
einsargen, Schulterpanzer, the coined set names and the two research labels
(all may differ from the community pack). The set-specific coinages each repo
lists stay pending there.

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

- **A coined charge noun that is not masculine needs a `WordInfo/Gender`
  line** (2026-10-13, Toxin Warcasket): `Stat_Thing_ReloadPerCharge_Desc`
  and `Stat_Thing_ReloadDestroyOnEmpty_Desc` switch on `{CHARGENOUN_gender}`
  and a table miss is masculine, so `Spriteinheit` prints "einen
  Spriteinheit" until `WordInfo/Gender/Female.txt` lists `spriteinheit`
  (lowercase, no comment lines). Core's own `Giftladung` is in the table;
  see `lessons.md` for the mechanism.
