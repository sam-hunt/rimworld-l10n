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

**Resolved timing conflict: `PostProcessed` runs at load, before argument
substitution — elision never fires across an injected placeholder.**
`de {0}` / `de [settlement_label]` sees a literal `{`/`[`, not a vowel, and
ships unelided; vanilla fr's own `TradeRequest.questNameRules` is the tell,
picking only prepositions that never need contracting (`pour`, `avec`, `à
[X]`). **This is BTG's 2026-08-10 finding, re-verified directly against the
assembly, and it reverses UWU's and PWU's earlier 2026-07-29 claim** that
`PostProcessed` runs *after* substitution and that writing `de {0}` /
`la {0}` "self-repairs" at runtime (e.g. "de or" → "d'or"). Per the
latest-wins rule, treat elision as **load-time-only**: restructure a sentence
so no elidable particle sits directly before an injected symbol or
placeholder, rather than relying on the worker to fix it after the fact.

`WithDefiniteArticle`/`WithIndefiniteArticle` are **overridden**, handling
`l'` before a vowel and `le`/`la`/`un`/`une` by gender directly — so the Keyed
`DefiniteForm`/`IndefiniteForm` templates are dead code in French, and
`[X_definite]`/`[X_indefinite]` are otherwise reliable even in a plain Keyed
string. `Pluralize` knows `-al`→`-aux`, `-au`/`-eu`→`+x`, and leaves
`s`/`x`/`z` alone. `OrdinalNumber` gives `1er`, `2e`. There is **no
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
- **Dash and guillemet usage cannot be judged from `Keyed/` alone** — both
  are real but rare/contextual conventions that only show up once
  `DefInjected` prose is included in the count. Always walk the whole tar.
- **Apostrophe style is DLC-dependent, but ASCII is still the load-bearing
  choice everywhere** — Core carries legacy curly apostrophes from
  `BackstoryDef` prose, Odyssey is decisively ASCII, and the elision worker
  only participates correctly with the ASCII form regardless of house style.
