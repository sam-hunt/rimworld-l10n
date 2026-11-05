# French — RimWorld localization mechanics

Grounded across the mod family: Persona Weapons Unbound (PWU) and Unique
Weapons Unbound (UWU) each landed French independently on 2026-07-29 (PWU had
no preseed from a sibling), Unique Melee Weapons (UMW) landed its own pass the
same day, and Better Traders Guild (BTG) generated on top of all three on
2026-08-10, re-verifying the `LanguageWorker_French` decompile directly
against the 1.6 assembly and re-counting the corpus tree-wide rather than
Keyed-only. All four passes are machine-assisted with **no native review
yet**. Where BTG's later, re-verified pass corrects an earlier sibling's
finding, the correction is applied below and flagged inline. RimWorld's
language folder is `French` (tar: `French (Français).tar`); grounding draws
on Core, Royalty, Ideology, Anomaly, Biotech and Odyssey.

## Engine mechanics (LanguageWorker)

**`LanguageWorker_French` rewrites every finished string, and this is the
finding that shapes everything else** (decompile-verified) — including plain
`.Translate()` Keyed output, not just rulepacks. Its `PostProcessed` runs five
regexes in order:

```
ElisionE   \b(ce|de|je|le|me|ne|se|te|que|quoique|lorsque) + vowel   → c' d' j' l' m' n' s' t' qu' ...
ElisionLa  \bla + vowel                                             → l'
ElisionSi  \bsi il(s)                                               → s'il(s)
DeLe       \bde le(s)                                               → de / des
ALe        \bà le(s)                                                → au / aux
```

**So French is the inverse of Spanish: never hand-contract.** Write `de` /
`le` / `la` plainly and the worker fixes it — vanilla fr relies on this
throughout (`le [attack_noun]` renders "l'assaut", `dégâts de {1}` renders
"dégâts d'immolation"). Traps inside it:

- **`de le` becomes `de`, not `du`.** Group 2 captures only `e`/`es`, so
  `de les X` correctly yields "des X" but `de le X` yields "de X" — a vanilla
  bug Core fr itself ships (`... de [RECIPIENT_definite]` → "la jambe de
  pirate"), not guidance to imitate. Never write `de [X_definite]`;
  restructure so the entity is a subject, or use an agent phrase — **`par
  [X_definite]` never contracts** and is the clean escape.
- **`IsVowel` includes `h`** — and also `æ`/`œ` (re-verified 2026-08-10
  against the 1.6 assembly) — so the worker cannot distinguish *h muet* from
  *h aspiré* and elides both (`la hache` → "l'hache", `de hampe` →
  "d'hampe"). Never place an elidable word directly before an h-initial noun
  without checking which kind it is.
- **`à le`/`à les` DO fuse correctly** as articles (`ALe` maps them to
  `au`/`aux`, and `à la` never matches), so `à` is a safe preposition to write
  before a `[X_definite]` symbol — `de` is the *only* broken preposition;
  don't generalize the `de le` trap into fearing all of them. But the same
  rewrite fires on an **object pronoun**, not just an article: `à le
  convertir` (meaning "to convert it") is mangled into `au convertir`. Avoid
  an infinitive complement with unstressed `le`/`la` immediately after `à`.
- **Enclitic pronouns after a hyphen are also vulnerable**, because the `\b`
  in `ElisionE`/`ElisionLa` matches right after one: an imperative like
  `Convertissez-la ensuite` becomes **`Convertissez-l'ensuite`**, and
  `Convertissez-le ensuite` the same. Never write `-la`/`-le`/`-ce`/`-te`/
  `-me` immediately before a vowel-initial word; restructure (e.g. "Il faut
  ensuite la convertir…") instead.
- **Quoting a placeholder blocks the elision worker** — a colourized or
  literally-quoted `{0}` presents `<`/`"` to the regex rather than a vowel, so
  `de "{0}"` ships unelided. This is a deliberate escape route when an
  injected value's first letter is unknown, at the cost of the quote marks
  themselves.

**Where `PostProcessed` actually runs (decompile-verified on 1.6.4871,
Shipcracker Warcasket's 2026-09-26 pass; this supersedes the two earlier,
contradictory timing notes).** The assembly has exactly one call site for
`LanguageWorker.PostProcessed` outside the article helpers:
`GrammarResolverSimple.Formatted`, which calls it on the *resolved* string
after `TryResolveInner` has substituted the arguments. There is no load-time
call: `DefInjectionPackage.ProcessedTranslation` only turns `\n` into a
newline, and a bare `"key".Translate()` returns the stored value untouched.
Two consequences:

- **DefInjected def fields are never elided by the worker.** A `label`,
  `description` or comp string is shown to the player exactly as written,
  so write the elided forms by hand (`l'armure`, `d'un`, `qu'il`), as vanilla
  does: Core + Odyssey fr `ThingDef` descriptions carry 918 hand-elided forms
  and zero uncontracted `de/le/que/ne/se/la + vowel` sequences. Hand-elided
  text is also safe wherever the worker does run, since its regexes match
  only the uncontracted forms.
- **Keyed strings are post-processed only through `.Formatted(args)` /
  `.Translate(args)`, and then *after* substitution.** The earlier "runs at
  load, before substitution" note is contradicted by the call site; the
  older "self-repairs across `{0}`" note is what the code says. Still prefer
  restructuring so no elidable particle sits directly before a placeholder:
  `de "{0}"` (quoted) never elides, an injected label may be capitalised or
  h-initial, and a no-arg `.Translate()` skips the worker entirely.

`WithDefiniteArticle`/`WithIndefiniteArticle` are **overridden**, handling
`l'` before a vowel and `le`/`la`/`un`/`une` by gender directly — so the Keyed
`DefiniteForm`/`IndefiniteForm` templates are dead code in French, and
`[X_definite]`/`[X_indefinite]` are otherwise reliable even in a plain Keyed
string. `Pluralize` knows `-al`→`-aux`, `-au`/`-eu`→`+x`, leaves
`s`/`x`/`z` alone and otherwise appends `s` to the whole string; it never
consults the `plural` lookup table (decompile-verified 2026-10-11), so a
mod-shipped `WordInfo/plural.txt` is dead in French and a multi-word noun in
a `{X_plural}` slot (a `chargeNoun`) pluralizes on its last word: give such
a slot a single word. The same garbles any multi-word `def.label` a mod
hands to `Pluralize` or `{X_labelPlural}` ("caisson d'hypersommeil antique"
becomes "...antiques"; decompile-verified 2026-10-18 on 1.7.4981), so phrase
the string around the singular label ("aucun exemplaire inexploré de
{0}"). `OrdinalNumber` gives `1er`, `2e`. There is **no
`TryLookUp` override**, and French ships only `WordInfo/Gender` data — no
`decline.txt`/`Case.txt` — so the `{lookup: …}` function that German and
Russian rely on has nothing to read here and is simply unusable.

**Gender for an injected/mod-coined noun is still a coin flip, because the
`WordInfo/Gender` table is sparse and `ResolveGender` defaults to Male when a
word is absent from it.** Checked against `Core/WordInfo/Gender/`: common
nouns like `arme`, `qualité`, `trait`, `recherche`, `relique`, `épée`,
`marteau`, `mémoire` are **absent**; only a handful (`noyau`, `schéma`,
`atelier`, `composant`) are present, all Male. So `[X_definite]`/an
article-agreement on any noun not already in that small vanilla table
defaults silently to masculine. The reliable fix is the same one Spanish and
German need: restructure so a controlled, invariant head noun carries the
grammar instead of the unknown injected one.

**`[X_possessive]` is structurally wrong in French, and vanilla's own data
proves it.** Core `Keyed/Grammar.xml` sets `Prohis`=`son`, `Proher`=`sa`,
`Proits`=`son/sa` — resolved from the **possessor's** gender — but French
`son`/`sa` must agree with the **possessed** noun instead. The symbol
therefore keys off the wrong entity no matter what. Counting values rather
than `<!-- EN: -->` comments proves vanilla agrees: **1471 occurrences in
comments, 24 in actual shipped values, and all 24 of those are broken**
(Anomaly's `[RECIPIENT_possessive]de son travail` renders the nonsensical
"sonde son travail"; Odyssey's `de [PAWN_possessive]` renders "le visage de
son"). Core's own combat packs write the possessive literally instead
(`[deflecting] son armure`) — do the same rather than using the symbol at
all. (For comparison across the family: Korean drops the symbol entirely,
German keeps and inflects it, Spanish keeps it only before a singular noun —
French is the fourth, distinct answer of replacing it with a literal
possessive agreeing with the possessed noun.)

## RulePackDef gender: rule-level constraints

**French solves rulepack gender with rule-level constraints — one rule per
agreement class, letting the resolver pick — distinct from German's inline
`|M|`/`|F|` noun markers and Spanish's parallel symbol families.** (Upstreamed
from UMW's 2026-07-29 pass; examples and counts re-verified against the 1.6
tar and the constraint claim decompile-verified 2026-08-18.) Core fr uses it
heavily: 271 gendered constraints tree-wide (116 `gender==Female`, 63
`gender!=Female`, 51 `gender==Male`, 41 `gender==None`), across combat logs,
interactions and quest scripts:

```
<li>staggered(p=3,SUBJECT_gender==Male)->est stupéfait</li>
<li>staggered(SUBJECT_gender==Female)->est stupéfaite</li>
<li>staggered(SUBJECT_gender==None)->est mis en échec</li>
<li>verb_genericattack(INITIATOR_gender!=Female)->s'est rué</li>   <!-- shorthand for Male+None -->
```

Constraints compose with `p=` weights and with other constants —
`died(SUBJECT_flesh!=Mechanoid,p=2,SUBJECT_gender==Male)` — so a family can
be both weighted and agreement-split.

**Always cover `None`** (or use `!=Female` where the masculine form serves
both): `SUBJECT_gender` is `None` for mechanoids and other genderless pawns,
and a family whose constraints exclude every rule makes the **whole root
unresolvable**. Decompile-verified consequence (`Verse.Grammar.GrammarResolver.Resolve`):
on a non-English language a failed resolution logs `Failed to resolve text.
Trying again with English.` (`Log.ErrorOnce`) and re-resolves the **entire
string** with the untranslated English rules — the player-visible symptom is a
complete English sentence in the middle of French text plus a red log error,
not a missing word. Core fr itself ships exactly this gap:
`RulePacks_Transitions.xml`'s `collapsed` family has only `gender==Male` /
`gender==Female` branches with no `None` branch and no `flesh!=Mechanoid`
guard, so a collapsing mechanoid's battle-log line silently falls back to
English — a vanilla bug, not a precedent (its neighbouring `died` family shows
the careful pattern, guarding every gendered rule with
`SUBJECT_flesh!=Mechanoid`).

## Style and corpus findings

- **Formality is `vous`, decisively, across every sample taken** — BTG's
  Core+DLC Keyed count is 564 `vous` against **zero** `tu`/`Tu`; PWU's
  independent Core Keyed count agrees (262 `vous` / 171 `votre|vos` vs 3 `tu`
  and 0 `ton|ta|tes`). This is the opposite of German and Spanish, both
  informal. Imperatives are the vous form (`Explorez`, `Faites attention`,
  `Sélectionnez`, `Choisissez`). **`ThoughtDef` stage descriptions are a
  register exception**: first-person present and informal (`Je suis à la
  limite de vaciller.`, `J'ai l'impression d'avoir…`), never vous-form.
- **Two quote systems, split by what is being cited, not interchangeable.**
  ASCII straight double quotes `"{0}"` (or ASCII single `'{0}'`, seen for
  research labels) for a cited def label or an **injected** value — 332+ ASCII
  `"` and effectively zero curly `"`/`"` across the whole tree. **Guillemets
  `« … »` with a plain ASCII space inside** are reserved for a **fixed UI
  element or command the player must go click** (`« Reformer la caravane »`,
  `« Masquer les traits négatifs »`, Odyssey's `sélectionnez « voir la
  planète »`) — never around an injected placeholder (vanilla wraps a
  placeholder in guillemets 0 times). Quoting a placeholder in ASCII also
  incidentally blocks the elision worker (see above).
- **Correction, tree-wide count vs. an earlier Keyed-only reading:**
  guillemets are a real, load-bearing convention, not noise. BTG's 2026-08-10
  tree-wide count found **74 `«` ship across Core+Odyssey, 62 of them in
  DefInjected**, correcting UWU's earlier Keyed-only reading of "14
  guillemets, inconsistently spaced" that had concluded ASCII-everywhere.
  DefInjected is where the *prose* lives (descriptions, letters, scenario
  text) — a Keyed-only count systematically under-samples exactly the
  register a mod's own long-form text is written in. Walk the whole tar, not
  just `Keyed/`, and split by DLC when the two disagree.
- **ASCII apostrophe `'`, not curly `'`** — load-bearing, not cosmetic: the
  elision worker's regexes match only the ASCII apostrophe context, so a
  curly one would not participate correctly. Tree-wide the split is 6896
  ASCII vs 1881 curly, but it is sharply DLC-dependent: **Core** carries 1848
  of the curly occurrences (legacy `BackstoryDef` prose), while **Odyssey is
  decisively ASCII** (1629 vs 37) — the DLC a trading/combat mod's vocabulary
  actually builds on agrees with the ASCII rule. Always emit ASCII `'`.
- **A plain ASCII space precedes `:` `!` `?`**, per French typography — not a
  no-break or narrow space (BTG: 3656 plain vs 9 U+00A0 before a colon; PWU's
  independent count found 3 U+00A0 and 0 U+202F in the whole file set despite
  French typography nominally wanting NBSP — vanilla simply doesn't use it).
  Do **not** put a space before `%` (`{0}%` stays tight) or before a digit's
  `%`. **Semicolons are effectively unused in vanilla fr** (single digits
  either way across every count taken) — prefer a period or restructure into
  two sentences rather than reproducing an English `;`.
- **Dashes exist in French but are vanishingly rare — the earlier "zero
  dashes" reading from three sibling passes was a Keyed-only undercount.**
  BTG's tree-wide count over Core+Odyssey with comments stripped found **13
  em dashes and 15 en dashes in 1.79M characters** — 1.6 per 100k, the lowest
  rate of any language checked that has any dashes at all. `—` appears as a
  parenthetical break (Odyssey's `TheGravship.description`) and `–` as a
  bullet marker (`  – Recherche débloquée :`). The correction is that dashes
  are *rare*, not that they are unavailable — at that rate, adding even one
  dash to a short string overshoots vanilla's density (one earlier draft's 2
  dashes in one string measured 11.3x vanilla's rate before being reflowed).
  Default to reflowing an English `—` into `:` (appositive summary) or `,`
  (contrastive clause), or a restructured sentence; the bar for introducing a
  genuinely new dash is an exact parallel construction in vanilla plus a
  workaround that would read distinctly worse. Ellipsis is always ASCII
  `...` (56 vs 18 curly `…` in one Core Keyed sample).
- **Units are per-unit, not one blanket rule**: `%` ships **tight** (`{0}%`),
  but `W` and `h` are **spaced** (`} W` / `} h`, vastly outnumbering the tight
  forms), and `jours` is spaced. Vanilla has no trailing multiplier-suffix
  convention of its own (its `{0}x` occurrences are all counted quantities
  like `{0}x chemfuel`), so keep an English tight `{0}x` as-is.
- Descriptions end with `.`; labels, buttons, stat fragments and section
  headers take none, and labels are lowercase noun phrases (research labels:
  forge, usinage, fabrication avancée).
- **`JobDef.reportString`s are third-person present indicative and KEEP the
  trailing period** (`nettoie TargetA.`, `construit un bonhomme de neige.`) —
  same register as German and Spanish, unlike Japanese/Korean which drop it.
- **Gender hedging inside a string uses inline word-splitting**, the French
  idiom for a genderable subject: `{0} a été taillad{PAWN_gender ? é : ée :
  é(e)} à mort.`, `{PAWN_gender ? un : une : un(e)}`. Both arities occur — the
  3-value form when a genderless (mechanoid) subject is possible, a 2-value
  form like `détendu{PAWN_gender ? : e}` where it is not. A bare-participle
  label instead takes a capitalized parenthetical: `Déchiqueté(e)`,
  `Perforé(e)`.
- **`labelNoun`-style constructions carry the indefinite article baked in**
  (`une taillade`, `un coup de lame`, `une brûlure`) — a shape French shares
  with German and Spanish, and that Japanese/Korean/Chinese lack.
- **The Keyed-vs-DefInjected sampling-bias lesson, as it applies to fr:** two
  of this family's own style rules were found inverted because they had been
  derived from Core+DLC `Keyed/` alone. French *does* use `—` (13 tree-wide,
  including the exact vanilla def a sibling mod's own scenario prose was
  modelled on), and it *does* use guillemets for a clicked UI command (74
  tree-wide, 62 of them in DefInjected). `DefInjected` is where prose lives —
  descriptions, letters, scenario text — so a Keyed-only count systematically
  under-samples exactly the register a mod's own long-form writing sits in.
  The fix: walk both trees, strip comments first, and split the count per DLC
  when the two disagree (fr's curly-apostrophe legacy is almost entirely
  Core's `BackstoryDef`s, while Odyssey is decisively ASCII) — re-run any such
  comparison after each generation pass rather than trusting an old count.

## Grounded common vocabulary

Vanilla-grounded terms confirmed identically (or reconciled where sources
disagreed) across the family's own generation passes. Source DLC/def is
given for each; rows marked with a **Never** column record a rejected
alternative and why.

| English | Use | Never | Source |
|---|---|---|---|
| trader / orbital trader | commerçant / commerçant orbital | marchand | Core, Odyssey `TradersGuild.description` |
| bulk / exotic goods trader | grossiste / vendeur de produits exotiques | | Core orbital `TraderKindDef`s |
| negotiator | marchand (Keyed `Negotiator` slot) **but** négociateur in the trade-fail message | | Core — the two slots genuinely diverge; pick by which string it is |
| trader guild / guild member(s) | guilde des commerçants / membre(s) de la guilde | guilde commerciale | Odyssey `TradersGuild.*` |
| settlement / orbital settlement | colonie orbitale / base de faction | | Odyssey `SpaceSettlement.label`, Core `Settlement.label` — "colonie" is ambiguous with the player's own colony, lean on context |
| orbital platform / settlement platform | plateforme orbitale / plateforme d'installation | | Odyssey `OrbitalPlatform.label`, `SettlementPlatform.label` |
| gravship / gravlite panel / pilot console | vaisseau gravitationnel / panneau de gravlite / console de pilotage | gravnavire | Odyssey |
| mechhive / orbital relay | ruche mécanoïde / relais orbital | | Odyssey `Mechhive.label`, `OrbitalRelay.label` |
| signal jammer / sentry drone / life support unit | brouilleur de signal / drone sentinelle / unité de survie | | Odyssey |
| [faction] became hostile to you | la faction [faction_name] vous est devenue hostile. | | Core `TradeRequest` — verbatim, lowercase opener and all |
| goodwill | bonne entente | bonne volonté | Core `Goodwill` |
| caravan | caravane | | Core `Caravan.label` |
| shuttle | navette | navette spatiale | Core `Shuttle.label`, Odyssey `Shuttles.label` |
| drop pod vs. cargo pod | capsule de largage vs. capsule de cargo | (don't merge the two) | Core `DropPodIncoming` / `LetterLabelCargoPodCrash` — distinct concepts |
| silver (colour/material) | argent | | Core colour labels |
| market value | valeur marchande (StatDef label) **but** Prix de base (Keyed `MarketValue` slot) | | Core — the two slots diverge; pick by which one the string stands in for |
| hacking (verb / JobDef) | pirater; reportString `pirate TargetA.` | | Core `JobDef`s; Odyssey `AncientHatch` — "a terminé de pirater {SUBJECT_labelNoParenthesisDef}." |
| reportStrings (clean / rescue / tend / feed / hack / open / board) | nettoie TargetA. / porte secours à TargetA. / soigne TargetA. / nourrit le patient TargetB avec TargetA. / pirate TargetA. / ouvre TargetA. / entre dans TargetA. | | Core `JobDef`s — verbatim; note `FeedPatient` inserts "le patient", a word the English has no equivalent for |
| colour labels (general) | lowercase bare nouns/adjectives: or, gris, jade, calcaire | | Core + Odyssey `ColorDef`s |
| quality tiers | horrible · médiocre · normal · bon · excellent · merveille · légendaire | | Core `QualityCategory_*` — identically confirmed across every pass in the family; note Masterwork = **merveille**, a noun sitting among adjectives, and all tiers ship masculine |
| Cancel / Reset / Confirm | Annuler / Réinitialiser / Confirmer | | Core buttons |
| Reset to defaults / Default / None | Réinitialiser les valeurs par défaut / Par défaut / Aucune | | Core `ResetBinding`, `Default`, `None` |
| advanced fabrication (research) | fabrication avancée | | Core `AdvancedFabrication.label` — verbatim (verified 2026-08-18) |
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | mégapascal spelled out in a label | CE 16.7.4 fr Keyed lacks `CE_MPa`/`CE_mmRHA`, so CE's own info card shows the English fallback "MPa"/"mm RHA"; the SI symbols are the same in French |
| blunt armor / sharp armor | Armure - Contondant / Armure - Perforant | | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label` |
| armor penetration | Pénétration d'armure | | CE fr `CE_DescArmorPenetration` — verbatim, the same as the family's existing settings strings |
| flak vest / flak jacket / frag grenade | gilet pare-balles / veste renforcée / grenade à fragmentation | | Core labels — verbatim |
| spacer / spacer-tech (attributive) | spatial / de technologie spatiale | | Core `TechLevel_Spacer` = `spatial`; `de technologie spatiale` for the attributive "spacer-tech" (*native*, Shipcracker Warcasket PR #1) |
| Imperial (adj.) | impérial | | Royalty `Empire.pawnSingular` |
| onboard respirator | respirateur intégré | | **Coined**, plain word: no vanilla French respirator item (Biotech has only `masque à gaz`) |
| sealed (airtight) | étanche | | Odyssey `GravshipHull.description` (`paroi étanche`); plain French, fine without Odyssey |
| plasteel / uranium / chemfuel | plastacier / uranium / chemfuel | | Core labels; `chemfuel` stays untranslated, as vanilla keeps it |
| Off / On (settings) | Désactivé / Activé | | Core Keyed `Off` = `Désactivé(e)`, `On` = `Activé(e)`; a label-only value takes the masculine form |
| settings window phrases (Keyed) | Par défaut : {0}. / (par défaut) / (nécessite Odyssey) | | Core Keyed `Default` = `Par défaut`; French-spaced colon; the DLC keeps its English name |
| cooldown / range / cells / hours | temps de recharge / portée / cases / heures | | Core `FlightCooldown` = `temps de recharge du vol`, Keyed `Range` = `Portée`, `HoursLower` = `heures`; `case` is vanilla's map-tile word (`inspecter les détails d'une case`) |
| Odyssey (DLC name) | Odyssey | | Odyssey `ExpansionDef` label keeps the English name |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | utilise la capacité : {0}. | | VEF ships English only; third-person present like Core's `JobDef.reportString`s, French-spaced colon, trailing period kept (Shipcracker Warcasket, shipped since 2026-09-26) |
| on cooldown (a reloadable comp's `cooldownGerund`) | rechargement | | Shipcracker Warcasket's rendering of vanilla's `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it |

### Medical, tending and ability vocabulary (Core and Odyssey; Medic Warcasket, 2026-11-05)

| English | Use | Never | Why |
|---|---|---|---|
| medic | médecin (`médecin de combat`, `médecin militaire`) | infirmier (a backstory title for "nurse"), aide-soignant | Core backstory `titleShort` for every "medic" (`CombatMedic82`, `MedicSoldier54`, `InfantryMedic6`, `SpaceMarineMedic10`); `VatgrownMedic53.description` `médecin de combat` |
| doctor (work type) / doctor work | Médecin, `labelShort` médecin / la tâche de médecin, `travailler comme médecin` | | Core `Doctor.label`, `Doctor.labelShort`, Keyed `NeedDoctorDesc` |
| caring (work tag) / childcare | soins et surveillance / nourrice (`labelShort`) | | Core Keyed `WorkTagCaring`, Biotech `Childcare.labelShort` |
| Work tab / unassigned | l'onglet « Travail » / non affecté | | Core `Work.label` `travail`, `WorkTab.helpText` `l'onglet TRAVAIL`, Keyed `NotAssigned` |
| trait (cited in prose) | `le trait X` | caractéristique | Core Keyed `TraitLabelWithDesc` `trait {TRAITLABEL}` |
| casting time / line of sight | Temps de réalisation / Ligne de vue requise | | Core Keyed `AbilityCastingTime`, `AbilityRequiresLOS` |
| tend / tend quality / medical tend speed | soigner (`Soigner {0}`) / qualité des soins (stat), Qualité du traitement (Keyed `TendQuality`) / vitesse des soins médicaux | | Core Keyed `Tend`, `TendQuality`, `MedicalTendQuality.label`, `MedicalTendSpeed.label` |
| medicine labels | herbe médicinale (f.) / médicament / médicament avancé | | Core `MedicineHerbal`, `MedicineIndustrial`, `MedicineUltratech`; the herbal label is feminine and h-initial (h muet, so the worker's `d'herbe` is right), so a `{0}` fed a medicine label needs a gender-neutral frame (`ne contient pas de {0}`, `Plus de {0}`, `kits de {0}`) |
| medicine (category) | médicaments | | Core `ThingCategoryDef` `Medicine.label` |
| go-juice / wake-up | Go-Juice / Wake-up, capitalised in prose too | | Core `GoJuice.label`, `WakeUp.label`, `GoJuiceAddiction.description` (`au Go-Juice`) |
| X in the bloodstream (drug hediff description opener) | X dans la circulation sanguine. | | Core `GoJuiceHigh.description`, `WakeUpHigh.description` |
| wearing off (hediff stage) / woozy | se dissipe / vaseux | | Core `Anesthetic.stages.wearing_off.label`, `.woozy.label` |
| heart attack / infection / missing body part | attaque cardiaque / infection / partie manquante | | Core `HeartAttack.label`, `WoundInfection.label`, `MissingBodyPart.label` |
| mechanites / medical skill | mécanites (f.) / compétence en médecine | | Core `FibrousMechanites.label` `mécanites fibreuses`, `SensoryMechanites.label`; `Medicine.skillLabel` `médecine`, prose pattern `compétence en recherche` |
| pain shock / unconscious / manipulation / sight | état de choc à cause de la douleur / inconscient / manipulation / vue | | Core Keyed `PainShock` `Choqué à cause de la douleur`, `Unconscious`, `Manipulation.label`, `Sight.label` |
| raider / ally | pillard / allié | | Core backstories (`RaiderKing38`), Keyed `AllyLower` |
| dose (medical) | dose (f.) | | Core `MechSerumHealer.description` `Une super-dose de mécanites`, Biotech `une dose de sérum` |
| Mote (an inherited mote label) | Particule | | Core `Mote_*.label` (62 entries); Odyssey's own motes ship the English `Mote`, a vanilla inconsistency, so ground on Core |
| colour option labels | bleu / vert; no Core `Pink`, `rose` is plain French | | Core Keyed `Blue`, `Green` |
| Enabled / Disabled (Keyed) | Activé / Désactivé | | Core Keyed `Enabled`, `Disabled` |

## Grounded common vocabulary, VFE Pirates warcasket domain (coined in Shipcracker Warcasket's 2026-09-26 pass, extended by Toxin Warcasket's 2026-10-13 and 2026-10-22 passes; 2026-10-28)

VFE Pirates ships English only, and no community French translation survives
(the "Vanilla Factions Expanded - Pirates [Fr]" Workshop item, id 2725064005,
has been removed), so a French player sees "siegebreaker warcasket" and
"warcasket foundry" in English in-game and every VFEP term here is a family
coinage. "warcasket" is therefore kept untranslated, as vanilla keeps
"chemfuel": Shipcracker Warcasket's native-speaker PR #1 (Joedox) replaced the
earlier "sarcophage", which matched nothing the player sees. Rows marked
*native* were settled by that review and are not reopened. Every warcasket set
in the family (Shipcracker, Toxin, Medic, Overlord) renders these terms alike
so the sets read as one family in-game; a change is made here first and each
set's shipped files follow at its next pass. A set's own name, its Workshop
title and its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket | warcasket (m., pl. warcaskets; invariable as a modifier: `coque warcasket`) | *native*. Untranslated, matching VFEP's English labels in a French game (see above); also the Workshop title anchor. Rejected: sarcophage (came from the removed pack's page, matches nothing in-game). |
| `<set>` warcasket / shoulders / helmet (label pattern) | warcasket `<set>` / épaulières de warcasket `<set>` / casque de warcasket `<set>` | *native* order. Core/Royalty apparel pattern `casque de cataphracte`, `armure de commando` (part `de` class noun); the set adjective stays invariable after the noun. |
| pauldrons / shoulders / shoulder pads | épaulières | **Coined** (no vanilla shoulder apparel; Core only has `épaule` body parts). Ordinary French armor term. Plural label: `[X_definite]` agreement may default masculine singular in vanilla keyed strings. |
| helmet | casque | Core `casque de commando`. |
| warcasket shell (torso) | coque warcasket | *native* (replaced the coined `carapace`); the `warcasket` modifier keeps it apart from a ship's `coque`. |
| warcasket foundry | fonderie de warcaskets | **Coined.** |
| entomb / weld into / welded | souder / soudé dans | Community VFEP Workshop page ("se soudent à l'intérieur"); the Shipcracker glossary's row, not found in the shipped DefInjected or Keyed. |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | « spacer warcaskets » (warcaskets spatiaux) | The English label in guillemets, because that is the clickable project every French player sees (VFEP is untranslated), with the French gloss in parentheses. Render `specialised warcaskets` the same way (not yet shipped anywhere). |
| VFEP set names | Brise-siège (siegebreaker), Brute (brute), Gardien (guardian), Aérien (aerial; in-game prose `pièces de warcasket aériennes`), cataphracte (cataphract; `le modèle cataphracte` in-game), hazard (hazard; `warcasket hazard`, `ensemble Hazard`) | **Coined** pattern, "ensemble" for set. Brise-siège, Brute, Gardien and Aérien are capitalized as proper names on the Workshop pages only; in-game the English label stays (`warcasket siegebreaker`, `warcasket hazard`) because VFEP's own labels are untranslated. cataphracte follows Royalty `Apparel_ArmorCataphract.label` = `armure de cataphracte`. Controller and sarcophagus have no French rendering recorded in any glossary. |
| 7th generation / 10th generation (VFEP's two chassis) | 7e génération / 10e génération (`les warcaskets de 7e génération`, `le châssis spatial de 10e génération`) | Shipcracker's and Toxin's prose; VFEP's dashed aside on the 7th generation becomes `qui, bien qu'interchangeables, fonctionnent mieux en ensemble`. |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | Coque warcasket spécialisée, plus protectrice mais plus lourde. / Épaulières warcasket spécialisées, plus protectrices mais plus lourdes. / Casque warcasket spécialisé, plus protecteur mais plus lourd. | Toxin Warcasket's shipped `shortDescription`s; the participle agrees with the part, the `warcasket` modifier stays invariable. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | Coque warcasket spécialisée de technologie spatiale, offrant une protection standard. (shoulders: Épaulières warcasket spécialisées ...; helmet: Casque warcasket spécialisé ...) | Toxin Warcasket's shipped text; `offrant une protection standard` replaces the 7th-gen `plus protectrice mais plus lourde`. Shipcracker's variant ends `qui disperse mieux les impacts` (a finite relative clause for "improved impact dispersion"). |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | Les warcaskets de 10e génération ont en réalité été adaptés à partir d'équipements pirates capturés, ... même d'une génération à l'autre. | Translated, no pack; the full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/French/`. power armour = `armure motorisée` (Core `Apparel_PowerArmor.description`); single-user dreadnoughts = `cuirassés à un seul pilote`; the rest coined in the 7th-gen paragraph's register. |
| pilot (the wearer) | pilote | Odyssey (`console de pilotage`, `pilote`); Shipcracker's prose. |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | blindage et isolation de niveau spatial / bouclier d'énergie / composants avancés | Core `Apparel_ShieldBelt.label` (`bouclier d'énergie`), `ComponentSpacer.label` (`composants avancés`); blindage and isolation as shipped in Toxin's `TXWC_SpacerTierDesc`. |
| ability description register (VFEP ability text) | third-person present (`Allume les propulseurs...`) | *native*. The majority vanilla form (Royalty 23 third-person vs 8 infinitive); Biotech's infinitive `Longjump` is the outlier. |

Pending native review for the whole family: `fonderie de warcaskets`,
`épaulières`, and the set-name capitalization pattern (Brise-siège, Brute,
Gardien). The set-specific coinages each repo lists stay pending there.

Sibling conflict (Medic Warcasket, 2026-11-05): the `warcasket` row keeps the
word invariable as a modifier, and Toxin ships `Épaulières warcasket
spécialisées`, but Shipcracker's shoulders `shortDescription` and
`description` ship `Épaulières warcaskets spécialisées de technologie
spatiale`; Medic follows this table, and Shipcracker's French follows at its
next pass.

## Pitfalls and lessons

- **Never write `de [X_definite]`** (or any elidable particle directly before
  an injected symbol) — `de le` collapses to `de`, not `du`, and elision does
  not fire across a placeholder anyway (see the resolved timing conflict
  above). Restructure so the entity is a subject, or use `par [X_definite]`,
  which never contracts.
- **`h`-initial nouns are a silent hazard**: the worker's `IsVowel` includes
  `h` (and `æ`/`œ`), so it cannot distinguish *h muet* from *h aspiré* and
  elides both alike. Check which kind of `h` a noun has before placing an
  elidable word in front of it.
- **`à le`/`à les` fuse correctly as articles but wrongly as object
  pronouns** — `à le convertir` (meaning "to convert it") becomes `au
  convertir`. Avoid an infinitive complement with an unstressed pronoun
  directly after `à`.
- **Enclitic pronouns after a hyphen elide too** — `Convertissez-la ensuite`
  becomes `Convertissez-l'ensuite`. Never place `-la`/`-le`/`-ce`/`-te`/`-me`
  immediately before a vowel-initial word; restructure the sentence instead.
- **`[X_possessive]` should never be used** — it resolves from the wrong
  entity's gender in French by construction; write the possessive literally.
- **Gender for any noun outside vanilla's small `WordInfo/Gender` table
  defaults silently to Male** — restructure with a controlled, invariant
  head noun rather than trusting `[X_definite]`/`[X_indefinite]` agreement on
  an unknown or mod-coined noun.
- **There is no `{lookup: …}` support in French** (no `decline.txt`, no
  `Case.txt`, no `TryLookUp` override) — the declension technique used for
  German/Russian simply has nothing to read here.
- **A gendered rulepack family that misses a gender value falls back to
  English for the whole string** — always cover `gender==None` (mechanoids)
  or use `!=Female`; Core fr's own `collapsed` family ships this bug (see the
  rule-level constraints section).
- **Dash and guillemet usage cannot be judged from `Keyed/` alone** — both
  are real but rare/contextual conventions that only show up once
  `DefInjected` prose is included in the count. Always walk the whole tar.
- **Apostrophe style is DLC-dependent, but ASCII is still the load-bearing
  choice everywhere** — Core carries legacy curly apostrophes from
  `BackstoryDef` prose, Odyssey is decisively ASCII, and the elision worker
  only participates correctly with the ASCII form regardless of house style.

- **Biotech ability labels are noun phrases** (`pulvérisation d'acide`,
  `jet de mousse`, `projection de feu`), so a mod ability label is a noun
  phrase too, not an imperative (2026-10-13, Toxin Warcasket).
- Core's `{CHARGENOUN_plural} restants` is masculine-only and fr Keyed never
  switches on `CHARGENOUN_gender`, so a feminine charge noun reads `unités
  restants`; no WordInfo file can help, accept it or coin masculine.
- `ToxicFallout` is `pluie toxique` on the GameConditionDef and IncidentDef
  and `retombée toxique` on the TaleDef; ground on the condition.
- **Vanilla's own multi-word charge nouns prove the single-word rule**
  (Medic Warcasket, 2026-11-05): Core and Biotech French ship `charge de
  mousse` (`Apparel_FirefoampopPack`) and `charge de brûleur`
  (`Gun_Incinerator`, `BioferriteBurner`) as `chargeNoun`s, so
  `{CHARGENOUN_plural}` prints `charge de mousses` and `charge de brûleurs`
  in vanilla itself (`pack tox` survives only because a final `x` is left
  alone). A vanilla precedent is not a reason to ship a multi-word noun.
- **Vanilla French charge nouns are freely feminine** (`charge`, `grenade`,
  `fusée`, against masculine `saut`, `obus`, `bouclier`), and fr Keyed never
  switches on `CHARGENOUN_gender`, so a feminine noun's `restants` / `son
  dernier` mismatch in two reload strings is vanilla's own look, not a mod
  defect. Medic ships `dose` (f.) on that basis (2026-11-05).
- **`cooldownGerund` varies by DLC**: Core and Royalty `rechargement`,
  Anomaly and Odyssey `en cours de recharge` / `en recharge`. The family row
  (`rechargement`) matches Core. And Core Keyed `CooldownTime` (the ability
  gizmo's own stat line) is `Délai de refroidissement`, while the family's
  `temps de recharge` comes from `FlightCooldown`; a string shown beside the
  gizmo's cooldown line should know the gizmo says `Délai de
  refroidissement` (Medic Warcasket, 2026-11-05).

## Generated-text tells

Catalogued in Medic Warcasket's 2026-11-05 pass from the Core + Odyssey French
tars (comments stripped, `{...}` and `[...]` constructs replaced before
counting; "desc" = every DefInjected `.description` outside `BackstoryDef`,
about 333k characters in 2590 entries; "Keyed" about 238k characters). Each
category of `English.md` § 2, as it shows up in French, then calque.

1. **The same sentence frame on every setting.** Vanilla tooltip openers are
   noun-led and few: `Le nombre ...` (24), `La quantité ...` (18), `Ajuste la
   ...` (12), `La valeur ...` (8), `Le type ...` (8). A `Le nombre de` / `La
   quantité de` / `Le temps que` opener is native and may repeat across a
   settings window (the family's `Par défaut : {0}.` closer is a formula, not
   a tell); the tell is a second identical clause appended to every tooltip.
2. **"Que ce soit" / "Détermine si" openers (Whether).** `Détermine si` or
   `Indique si` opens 5 Keyed strings and no description; `Que ce soit`
   appears 10 times in all, almost always mid-sentence and in narrative
   prose (`que ce soit lors du premier essai ...`), and opens a sentence once
   (`Que ce soit dans la salle d'audience des rois ...`). A toggle takes `Si
   activé, ...` (8) or `Lorsqu'activé, ...` (5) in vanilla Keyed, with the
   consequence in the future (`le piège sera remplacé`, `construiront`); the
   family's `Si cette option est activée, ... Si elle est désactivée, ...` is
   the same frame spelt out.
3. **Telegraphese.** French vanilla is short but complete: descriptions
   average 11.0 words per sentence (median 10), 0.9% of sentences exceed 30
   words. Verbless indefinite noun-phrase openers are the native item frame
   (`Un/Une ...` opens 676 of 931 Core + Odyssey `ThingDef` descriptions:
   `Une armure motorisée.`, `Une super-dose de mécanites à usage unique ...`),
   and a drug hediff opens `X dans la circulation sanguine.` The tell is the
   other way: an English-length sentence carried over whole, with two
   relative clauses and a trailing participle.
4. **Balanced tricolons and aphoristic closers in lore.** `non seulement ...
   mais` occurs 0 times in either corpus and `à la fois` 11; three-noun lists
   are plain inventories, never three parallel clauses. `véritable` as an
   intensifier runs 1.5 per 100k in descriptions; more than one per text,
   or a closing line built on it, is the tell. Lore ends on a fact.
5. **Sentence-initial participle clauses.** `Conçu pour`, `Équipé de`, `Doté
   de`, `Fabriqué en`, `Utilisé pour` open 9 description sentences (2.7 per
   100k), most of them the second sentence of an item or bionic entry
   (`Fabriquée en os biosynthétique, ...`, `Utilisée pour raffiner ...`), and
   2 Keyed strings. The `en + -ant` gérondif never opens a description (0)
   and trails one only twice. A participle or gérondif opening a mod's first
   sentence, or a settings tooltip, is the tell; a postposed `, offrant ...`
   / `équipé de ...` after the noun (as the VFEP openers have it) is native.
6. **Coinages and `de` chains.** Hyphen compounds are common in French (90 per
   100k, mostly lexical: `celui-ci`, `au-dessus`, `lance-roquettes`), so the
   tell is not the hyphen but an English noun stack rendered `X de Y de Z
   de W`: three chained `de` phrases run 10.2 per 100k in descriptions; a
   mod's own nouns stack fast (`le système de pansement de mécanites de
   l'armure`), so keep to two and let a relative clause or a possessive carry
   the rest.
7. **Semicolons, colon pivots and parenthetical asides.** In descriptions 2.7
   semicolons, 7.5 spaced colons and 9.3 opening parentheses per 100k (Keyed
   0.8 semicolons; its 140.6 colons are UI `Label : valeur` lines and its
   parentheses are almost all units and `(e)` gender splits). Em and en
   dashes run 1.8 per 100k in descriptions and 2.9 in Keyed (1.76 over the
   whole Core + Odyssey value set). `, ce qui ...` is the native result pivot
   (9.9 per 100k in descriptions), once per text, not per sentence.
8. **Signature phrases repeated across surfaces.** Vanilla repeats only
   formulas (`dans la circulation sanguine`, `Par défaut : {0}.`, `Ligne de
   vue requise`). `permet de` is common (24.0 per 100k in descriptions) but
   is the phrase a generated text leans on in every sentence; a coined
   phrase such as `sur place` or `un peu plus longtemps` should appear once
   across descriptions, ability text and the Workshop page.
9. **Over-explanation.** Core tooltips state the mechanic in one sentence and
   stop (`La résistance de cette créature aux effets négatifs du vide
   spatial.`); a second sentence teaching what the row's value already shows
   is the tell.
10. **Modder vocabulary.** `définition` never reaches a description; `def`,
    a subsystem's own name and English loanwords for UI parts (`tooltip`,
    `gizmo`) never reach player text. Core says `indicateur` (Keyed
    `VisibleMoodDesc`), the family `jauge`; `objet`, `colon`, `personne`
    (for a pawn), `onglet « Travail »`.

**Calque.** The English skeleton under French words shows as: a trailing `,
+ participe présent` result clause on most sentences (vanilla's gérondif
trails 0.6 per 100k in descriptions); `être + participe + par` passives (8.4
per 100k) where vanilla also uses `on` (12.0) and the active voice; a sentence
opened by `Il est` / `Elle est` (23.1 per 100k, native in item descriptions,
but not as a dummy `Il est important de ...`); English adjective-before-noun
order; `tu` (0 in both corpora: vanilla is decisively `vous`); and an English
`after X found that Y` clause kept in English order. Rebuild the sentence from
the subject the French reader expects: `Comme il perdait presque autant de
chirurgiens que de soldats ..., il a conçu le modèle médecin pour ...` rather
than `Le Médecin a été construit pour ..., après que le programme a découvert
que ...`.
