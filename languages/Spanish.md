# Spanish (Castellano) — RimWorld localization mechanics

Grounded across the mod family: Unique Weapons Unbound's (UWU) and Persona
Weapons Unbound's (PWU) machine-assisted generation passes (2026-07-29, no
native review), Unique Melee Weapons' (UMW) own pass the same day (adds the
`RulePackDef` name-grammar findings), and Better Traders Guild's (BTG)
2026-08-10 pass, which re-verified the shared `LanguageWorker_Spanish`
findings and layered on its own Core+Odyssey vocabulary. As of the latest
pass, no native-speaker review has landed for any of these. RimWorld ships
**two** Spanish languages: `Spanish (Español(Castellano)).tar` and
`SpanishLatin (Español(Latinoamérica)).tar`. The family's target is
Castilian, so the mod folder is `Spanish` — decompile-verified against
`Verse.LoadedLanguage`, `legacyFolderName` cuts the declared name at `(`, so
the nested-paren tar name still resolves to a folder literally named
`Spanish` (same mechanism as `Japanese`/`Korean`). `SpanishLatin` is a
**separate** language with its own tar and its own `WordInfo/Gender` data
(it ships an extra `Other.txt`) — never assume a term or a rule carries
across; it needs its own grounding pass.

## Engine mechanics (LanguageWorker)

**`LanguageWorker_Spanish` is decompile-verified and imposes no hidden
authoring requirement** — no `PostProcessed` override (unlike German), no
particle system (unlike Korean). It overrides only `WithIndefiniteArticle`
(un/una/unos/unas), `WithDefiniteArticle` (el/la/los/las), `OrdinalNumber`
(renders `N.º`) and `Pluralize` (full rules plus a `plural.txt` lookup); it
returns names unchanged. So unlike German/Korean there is no silent
string-rewrite to trip over — but also no runtime agreement help. Spanish's
difficulty is gender, not case, and it shows up in two independent places:

- **Contractions are not automatic and must be hand-written.**
  `WithDefiniteArticle` is plain `"el "`/`"la "` concatenation — it does not
  contract, and does not handle the "el agua" class (feminine nouns that
  take `el`). So `de {0_definite}` renders **"de el ..."** instead of
  **"del"**, and `a {0_definite}` renders **"a el"** instead of **"al"**.
  This must be fixed by hand wherever `de`/`a` sits directly before an
  injected `[X_definite]` symbol — including in a plain `.Translate()` call,
  not just inside a `RulePackDef`. Core es fixes this 89 times with the
  colour code baked into the search pattern:

  ```
  {replace: de [RECIPIENT_definite]; "de &lt;color=#D09B61FF>el "-"&lt;color=#D09B61FF>del "}
  {replace: a [RECIPIENT_definite]; "a &lt;color=#D09B61FF>el "-"&lt;color=#D09B61FF>al "}
  ```

  Feminine (`de la pirata`) and named entities simply don't match and pass
  through untouched, which is correct. **Core es also ships a shorter,
  buggy variant** (`{replace: de [X]; ">el "-">del "}`, 20 uses in
  `RulePacks_CombatRanged`) that leaves the literal `de ` outside the match
  and renders "de del proyectil" — copy the full form only, or restructure
  so no `de`/`a` precedes a `_definite` symbol.

- **Gender agreement on injected nouns is a genuine landmine, and the
  resolver's coverage is worse than it looks.** `GrammarResolverSimple` (the
  path a plain `.Translate(args)` reaches) resolves an injected symbol's
  gender from `WordInfo/Gender/{Male,Female,Neuter}.txt`, and vanilla es
  *does* lean on this freely (20 `{0_gender ? o : a}`, 18 `{0_indefinite}`,
  9 `{0_definite}` in Core+Royalty Keyed; tables are well populated: Female
  2771 / Male 1771 / Neuter 163 lines). But those tables cover **vanilla
  nouns only**, and `ResolveGender`'s `defaultGender` is **Male** on a miss.
  A concrete check across several common injected nouns (`arma`, `calidad`,
  `característica`, `investigación`, `núcleo`, `tecnoplano`, `reliquia`)
  found **none** present in the tables — each would silently resolve
  masculine, which is wrong for every one of them (all grammatically
  feminine). Net rule, same shape as German's case problem with "gender"
  substituted for "case": **restructure so no article or agreeing
  adjective has to agree with an injected/unknown-gender value.** Leading
  with an invariant head noun works (`Personalización de {0}
  interrumpida: ...` — `Personalización` is always feminine regardless of
  what lands in `{0}`), as does dropping the article entirely (`de {0}` /
  `requiere {0}`, the es counterpart of German's `von`-frame), or quoting
  the injected value so no surrounding word needs to inflect against it
  (`requiere calidad "{0}" o mejor`). An inflected article is only safe
  when `{0}` is hard-bound to one specific, known-gender vanilla label
  (e.g. `en la {1}` where `{1}` always resolves to a feminine noun) —
  never generalize that to an unpinned placeholder.

- **`[RECIPIENT_possessive]` resolves to `su` and has NO plural form.** Core
  `Keyed/Grammar.xml` sets `Prohis`/`Proher`/`Proits` all to `su`. Spanish
  `su` agrees in number with the *possessed* noun, so the symbol is only
  safe directly before a **singular** noun (`[RECIPIENT_possessive]
  gavilanes` would ship "su gavilanes" every roll). Use the definite
  article for plurals instead (`los gavilanes`) — which is also the more
  idiomatic Spanish for referring to one's own equipment.

- **RulePackDef name-grammar gender is solved by splitting parallel symbol
  families, not by tagging nouns with inline markers.** Where German uses
  inline `|M|`/`|F|`/`|N|` markers stripped per syntactic slot, Spanish
  `NamerUniqueWeapon`-style rulepacks instead keep two parallel families —
  one masculine, one feminine (e.g. `concept` vs `conceptF`) — and write one
  full rule per gender (`[X] del [concept]` / `[X] de la [conceptF]`).
  Consequences: (1) a `namerLabels`-style symbol referenced by *both*
  genders must be a bare lowercase noun with no article or agreeing
  adjective attached, since its own gender is unknowable at the point it's
  used; and (2) any adjective that postposes onto that noun (`[X]
  [trait_adjective]`) must be **gender-invariant** — either an invariant
  ending (`-e`, `-al`, `-ar`, `-z`, `-ista`, `-ble`, `-il`: torpe, elegante,
  ornamental, ágil, veloz, brillante) or a prepositional phrase (`de oro`,
  `de jade`, `de gran tamaño`). A bare `-o`/`-a` adjective is silently wrong
  half the time. This technique generalizes to any `RulePackDef` that
  generates a name from a noun of unknown gender, not just weapons.

## Style and corpus findings

Counted against the vanilla es data (mandatory rules, confirmed
independently across the family's generation passes):

- **ASCII straight double quotes** for cited def/UI labels — vanilla writes
  `La misión se llama "{0}".` and `el botón "ordenar mods"`. Counts run as
  high as 7689 ASCII `"` against **7** curly `"` and **zero** guillemets
  `«»` in one Core+DLC sweep. Never port ja's 「」, ru's «», or zh's "".
- **Inverted opening marks are required**: `¿…?`, `¡…!` (168 / 433 hits in
  one Core sweep; ~50–60 each in narrower slices). `¿Continuar?` is
  vanilla's own exact phrasing.
- **Zero dashes.** Core+DLC contain no em dashes and no en dashes (as low
  as 2–3 hits across an entire dataset, i.e. effectively unused), so an
  English `—` must be **reflowed** into a colon, comma or new sentence —
  never converted to `–`. This is the opposite of German, which mandates
  `–`. Keep the original dash verbatim inside any `<!-- EN: -->` comment.
- Ellipsis is ASCII `...` (`…` is effectively 0).
- Descriptions/prose end with `.`; labels, buttons, stat fragments and
  section headers take none. Labels and research labels are lowercase
  noun phrases.
- **Informal `tú` with imperatives, decisively**, in settings prose and
  throughout: `Explora` 12 / `Explore` 0, `Asegúrate` 41 / `Asegúrese` 0,
  `tu colonia` 61 / `su colonia` 3, `Puedes` 40 / `Puede usted` 0, `Haz` 22
  / `Haga` 0. Never `usted`.
- **`JobDef.reportString` is a subject-less gerund WITH a terminal
  period** (`construyendo un muñeco de nieve.`, `desarmando TargetA.`;
  180/196 Core entries end in `.`) — matches zh-Hans in taking a period,
  is the opposite of ja/ko, and differs from German's third-person form.
  Verbatim Core examples worth reusing for any NPC-safe job copy:
  `limpiando TargetA.` / `rescatando a TargetA.` / `tratando a TargetA.` /
  `alimentando a TargetB con TargetA.` / `hackeando TargetA.` /
  `abriendo TargetA.` / `entrando en TargetA.` — keep the trailing period,
  and note the personal `a` appears only before *animate* targets.
- **`RecipeDef` fields each have a distinct shape**: `label` is a lowercase
  infinitive with **no article** (`fabricar fusil de asalto`);
  `description` is third-person present **with** article and a period
  (`Fabrica un fusil de asalto.`); `jobString` is a capitalized gerund
  **with** period (`Fabricando fusil de asalto.`). Like German, and unlike
  ja/ko, es job/recipe strings take terminal periods.
- **Units are per-unit, not one blanket rule** (counted over Core+Odyssey
  Keyed): percentages tight (`{0}%`), `x` tight (`{0}x`), but watts spaced
  (`{0} W`) and days/hours spaced (`{0} días`). Copy the convention per
  unit rather than generalizing from one.
- **Quality tiers are gender-inconsistent in vanilla itself** (`bueno` is
  masculine, `legendaria` is feminine) — reproduce them as-shipped; they
  are injected labels and are never expected to agree with anything.
- **Adjectives postpose and agree in gender + number** as the default
  Spanish order (`arma única`, not `única arma`).
- **Castellano spells "cost" as `coste`**, not `costo` (29 vs 1 in one
  Core sweep); pluralize as `costes`.

## Grounded common vocabulary

Core/DLC-grounded terms usable by any mod in the family (verbatim vanilla
strings unless noted):

| English | Use | Never | Why |
|---|---|---|---|
| Cancel / Reset / Confirm / Default / None / Randomize | Cancelar / Restablecer / Confirmar / Por defecto / Ninguno / Aleatorizar | | Core buttons |
| Reset to defaults | Restablecer valores por defecto | | Core collapses harder than German here: plain `Reset` **and** `RestoreToDefaultSettings` are both `Restablecer`, and `ResetBinding` = `Restablecer teclas` is keybinding-specific only — compose the "to defaults" phrase from `Default` = `Por defecto` |
| quality tiers | horrible · mediocre · normal · bueno · excelente · obra maestra · legendaria | pobre, malo | Core `QualityCategory_*` |
| trader / orbital trader | comerciante / comerciante orbital | mercader | Core, Odyssey `AsteroidLetterText` |
| bulk / exotic goods trader | mayorista / comerciante de productos exóticos | | Core orbital `TraderKindDef`s |
| goodwill / caravan / negotiator | reputación / caravana / negociador | buena voluntad | Core `Goodwill`, `Caravan.label`, `Negotiator` |
| silver / market value (running prose) / comms console / packaged survival meal | plata / valor de mercado / consola de comunicaciones / raciones de supervivencia envasadas | | Core narrative/quest text (e.g. `TradeRequest`) |
| market value (the **StatDef label**) | **Precio base** | valor de mercado | Core `StatDef MarketValue` — a real trap: the literal translation is wrong for this specific field. Narrative prose about "market value" as a concept is `valor de mercado` (row above); the StatDef's own displayed label is `Precio base`. Check which field you're filling before picking one |
| raid | asalto | incursión | Core `RaidEnemy.label`, Keyed `Raid` (`incursión` is reserved for `RaidFriendly`) |
| quest | misión | búsqueda | Core `Quest`, MainButton `Quests.label` = `misiones` |
| Quest failed: [resolvedQuestName] | Misión fallida: [resolvedQuestName] | | Core `TradeRequest` — verbatim |
| [faction_name] became hostile to you. | La facción [faction_name] se ha vuelto hostil. | | Core `TradeRequest` — verbatim |
| hostile to {0} | Relaciones hostiles con {0} | | shaped from Core `QuestHostileTo` |
| hostile / enemy / colonist | Hostil / enemigo / colono | | Core `Hostile`, `Enemy`, `Colonist` |
| No capable negotiator | No hay ningún negociador capaz | | shaped from Core `CommandTradeFailNoNegotiator` |
| shuttle | transbordador | lanzadera | Core `Shuttle.label`, Odyssey `AsteroidLetterText` |
| transport/drop pod vs cargo pod | cápsula de transporte / cápsula de desembarco vs cápsula de carga | | Core `TransportPod`, `DropPodIncoming`, `CargoPodCrash` — distinct defs, don't merge |
| orbital platform / settlement platform | plataforma orbital / plataforma de asentamiento | | Odyssey `OrbitalPlatform.label`, `SettlementPlatform.label` |
| orbital settlement / settlement / colony | asentamiento orbital / asentamiento / colonia | | Odyssey `SpaceSettlement.label`; Core `Settlement.label` is `colonia`, but running prose (e.g. `TradeRequest`'s "un asentamiento cercano") uses `asentamiento` for a faction settlement |
| signal jammer / sentry drone / life support unit | inhibidor de señales / dron centinela / unidad de soporte vital | | Odyssey (supersedes Core's older singular "inhibidor de señal") |
| gravship / gravlite panel / pilot console | gravinave / panel de gravilita / consola de piloto | gravnave | Odyssey `TheGravship` |
| mechhive / orbital relay | mecacolmena / repetidor orbital | | Odyssey `TheGravship.description` |
| steel / vacuum / safe / reinforcements / hatch / vault (sealed-valuables sense) | acero / vacío / caja fuerte / refuerzos / escotilla / bóveda | | Core, Odyssey (`AncientHatch`, `AncientSafe`) |
| garrison / outpost | guarnición / puesto de avanzada | | Core `AncientGarrison.label`, `Outpost.description` |
| colour labels (general rule) | lowercase, gender-invariant where possible: dorado, gris, jade | | Core + Odyssey `ColorDef`s |
| **purple (weapon-adjacent colour)** | **púrpura** | morado | Landmine: Core's generic `ColorDef`s say `morado`, but Odyssey's own item-specific colour defs say `púrpura` — match the nearer/more specific file, not the generic one |
| wood / plasteel / uranium / jade / steel / silver / gold | madera / **plastiacero** / uranio / jade / acero / plata / oro | plasacero, plasteel | Core labels + `stuffAdjective` — plasteel is counterintuitive, always check |
| chemfuel | **biocombustible** | químicombustible, combustible químico | Core `Chemfuel` — counterintuitive, like German's `Sprit` |
| components / advanced components | componentes / componentes avanzados | piezas | `ComponentIndustrial`, `ComponentSpacer` |
| tech levels (enum labels) | neolítico / medieval / industrial / era espacial / ultra / arqueoteca | espacial, ultratech, arquitec- | Core `TechLevel_*` — archotech = `arqueoteca`, ultratech = plain `ultra`, neither transliterates |
| ultratech / archotech (attributive, in prose only) | ultratecnológico / arqueotecnológico | | vanilla prose attests these; the "never ultratech" ban applies to the enum labels only |
| Structure (architect category) | estructuras | estructura | `Structure.label` is plural, exactly as in German |
| relic / ideoligion | reliquia / **ideoligión** | ideología | Ideology `Relic`, `RelicOf`, `IdeoligionOf` — es coins the portmanteau, like Russian, unlike ja/zh/de |
| techprint | tecnoplano | plano técnico, tecnoimpresión | Core `TechprintLabel` |
| research tree | árbol de investigaciones | árbol de investigación | Core `ResearchScreen` — note the plural |
| **disarm** | quitarle el arma a … | **desarmar** | Landmine: in vanilla es `desarmar` means *deconstruct/dismantle* (`Deconstruct.label` = desarmar estructuras). `DisarmedTime` = Desarmado is the only weapon sense; phrase the verb with `quitar` instead |
| haul / hauling | transporte | acarrear, acarreo | Core `Haul.label` |
| forbidden / cannot reach / reserved by | prohibido / no puede alcanzar / reservado para | | Core `ForbiddenLower`, `CannotReach`, `IsReservedBy` |
| reportStrings (clean/rescue/tend/feed/hack/open/board) | limpiando TargetA. / rescatando a TargetA. / tratando a TargetA. / alimentando a TargetB con TargetA. / hackeando TargetA. / abriendo TargetA. / entrando en TargetA. | | Core `JobDef`s — verbatim; keep the trailing period and the personal `a` before animate targets |
| starting people (ScenPart) | personas iniciales | | Core `ConfigPage_ConfigureStartingPawns.label` — identical English source, reuse verbatim |
| fueled / electric smithy vs machining table vs fabrication bench vs generic workbench | forja de leña / forja eléctrica vs mesa de maquinado vs mesa de ensamblaje vs mesa de trabajo | banco de trabajo, estación de trabajo (generic); mesa de fabricación, mesa de mecanizado (specific benches) | Core building labels — each specific bench has its own name; only the *generic* concept is `mesa de trabajo`. `Smithing` the **skill**/WorkType is `Forja` while `Smithing` the **research project** is `herrería` — same defName pattern, two different defs, two different words; check the def type before reusing a lookup |

## Pitfalls and lessons

- **Gender resolution is the load-bearing trap, not contraction.** The
  contraction rule (`de el`→`del`, `a el`→`al`) is mechanical and easy to
  apply once known. The harder, easier-to-miss problem is that vanilla's
  gender tables simply don't cover most nouns a mod would inject (`arma`,
  `calidad`, `investigación`, etc. all miss and silently default
  masculine) — always restructure around an unknown-gender injected value
  rather than trusting `{0_gender}`/`{0_definite}` to resolve correctly.
- **Two independent findings agree market value is a trap, but they
  describe two different fields — this was reconciled, not merged
  blindly.** One pass recorded plain narrative "market value" as `valor de
  mercado` (grounded in `TradeRequest`-style prose); another recorded the
  `MarketValue` **StatDef's own label** as `Precio base`, flagging the
  literal translation as wrong. Both are correct for their respective
  field — the vocabulary table above keeps them as two separate rows so
  neither is lost or silently overwritten.
- **`de`/`a` + `[X_definite]` contraction and the `su`-has-no-plural rule
  are corroborated independently by three separate generation passes**
  (UWU/PWU's shared investigation, UMW's own, and BTG's later
  re-verification) — high confidence, safe to treat as settled.
- Spanish needing gender-invariant postposed adjectives for
  `RulePackDef`-generated names (see Engine mechanics) is the same
  underlying constraint German solves with inline `|M|`/`|F|` markers and
  Japanese doesn't need at all — the fix is language-specific even though
  the underlying problem (a noun of unknown grammatical gender) is not.
