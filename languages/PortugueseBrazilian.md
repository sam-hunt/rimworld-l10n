# Brazilian Portuguese — RimWorld localization mechanics

Grounded across the mod family: PersonaWeaponsUnbound (PWU) ran the first
pt-BR pass, 2026-07-29, with no preseed from any sibling; UniqueWeaponsUnbound
(UWU) and UniqueMeleeWeapons (UMW) each ran their own machine-assisted
2026-07-29 passes; Better Traders Guild (BTG) ran the newest pass, 2026-08-10,
explicitly building on top of the three weapon-mod siblings. No native review
of pt-BR content is recorded in any of the four repos — treat everything below
as machine-assisted pending review. RimWorld's language folder is
**`PortugueseBrazilian`** (tar: `PortugueseBrazilian (Português Brasileiro).tar`)
— **not** "BrazilianPortuguese". European Portuguese ships as a wholly
separate language, folder `Portuguese` (tar `Portuguese (Português).tar`); it
shares no data with this one and would need its own grounding pass if a mod
ever adds it. `LanguageInfo.xml` declares `languageWorkerClass`
**`LanguageWorker_Portuguese`** for pt-BR — there is no
`LanguageWorker_PortugueseBrazilian` class at all, so the two Portuguese
languages share one worker.

## Engine mechanics (LanguageWorker)

**The worker does almost nothing, and that is the finding that shapes
everything else** (decompile-verified across all four repos). It overrides
**only** `WithIndefiniteArticle` and `WithDefiniteArticle` (prepending `o `/
`a `/`os `/`as `, `um `/`uma `/`uns `/`umas ` by gender). It has **no
`PostProcessed` override**, so the base `LanguageWorker.PostProcessed` runs —
and that only calls `MergeMultipleSpaces()`. No elision, no contraction, no
`'s` rewriting, no particles. A leading/trailing intentional space in a string
is therefore safe to write by hand.

**So Portuguese is the hard case: its contractions are orthographically
mandatory and nothing supplies them.** `de`+`o`=`do`, `de`+`a`=`da`,
`em`+`o`=`no`, `em`+`a`=`na`, `a`+`o`=`ao`, `a`+`a`=`à`, `por`+`o`=`pelo`
(plus every plural). Consequences for any Keyed prose or rulepack that injects
a definite-article'd symbol:

- **Never write `de` / `em` / `a` / `por` directly before a `[X_definite]`
  symbol.** `_definite` prepends a bare `o `, nothing fuses it, and the
  literal **"de o pirata"** ships — and **vanilla pt-BR ships exactly this
  bug** in its own Core combat rulepacks (`o [destroyed_targets] de
  [RECIPIENT_definite]`, `esquivou de [INITIATOR_definite]`). Frequency is not
  correctness.
- **The clean escapes are `com`, `para`, `contra`, `sem`, `sobre`, `entre`**
  — none of these contract with the article, so `com [X_definite]` is safe.
  Otherwise restructure so the entity is a subject or direct object instead.
- **The idiomatic vanilla technique is to use the bare `[X_label]` and write
  the contracted article yourself, hedged**: Core's ranged combat pack writes
  `do(a) [INITIATOR_label]`, `pelo(a) [projectile]`.
- There are **zero `{replace:}` blocks** anywhere in vanilla pt-BR's
  rulepacks — vanilla never even attempted Spanish's contraction scaffolding.
  Don't invent one; restructure instead.

**Gender resolution on ordinary nouns is effectively dead, which is why
hedging/restructuring is mandatory rather than optional.** `WithDefiniteArticle`
is plain `"o "`/`"a "` concatenation with no contraction step, and
`GrammarResolverSimple`'s gender lookup only resolves for nouns actually
present in the language's gender word lists — decompile-verified against
`Verse.LanguageWordInfo`: pt-BR ships `WordInfo/Gender/Female.txt` with just
**14** lines and `Male.txt` with just **9**, all livestock and nobility terms
(amazona, baronesa, cabra, condessa, duquesa, égua, galinha, ovelha, bode
íbex, carneiro, garanhão, touro, …) — not a single common noun. Larger files
like `Singular.txt`/`Plural.txt`/`new_words.txt` exist but are never read for
gender (`Plural.txt` is read by `Pluralize`: `LanguageWorker_Portuguese`
overrides only the article helpers, so the base `Pluralize` runs, a `plural`
table lookup and otherwise the word *unchanged*; a mod ships its own
`WordInfo/plural.txt` line for a coined noun in a `{X_plural}` slot, see
`lessons.md`, 2026-10-11). `ResolveGender`'s `defaultGender` is **Male**, so `{0_gender ? … : …}`
and `{0_definite}` against essentially any mod-injected noun (arma, bancada,
espada, assentamento, caravana, …) is a silent coin flip, not a resolved
value. (Vanilla itself uses the resolver freely for *pawn* gender, which is a
different, always-known input — that case is fine.)

**Gender hedging is a distinct technique from every other language checked in
this family, and pt-BR applies it to the surface text itself**, pervasively —
articles, participles, contractions and possessives alike get a literal
**`(a)`**: `O(a)`, `um(a)`, `do(a)`, `pelo(a)`, `danificado(a)`. Which shape
applies depends on the field, not a blanket rule:

- Plain Keyed prose or rulepack/def surface text takes the **literal `(a)`**.
- A `.Translate()` call or a templated string (e.g. a `deathMessage`) instead
  takes the **inline resolver split**: `{PAWN_gender ? o : a}`. Vanilla ships
  no 3-arg genderless fallback for these fields, so don't invent one.
- Vanilla writes a sloppy `seu(ua)` in places; write the corrected `seu(sua)`
  if you need the construction.

**The complementary technique is to restructure so nothing has to agree with
an injected value in the first place** — lead with an invariant head noun you
control, the same escape German/Spanish/French all use, but with no partial
shortcut available here since neither gender nor contraction resolves.
Concretely: prefer an infinitive, a bare noun phrase, or a clause with its own
fixed subject over any participle whose subject is an injected value of
unknown gender (a trait, an item, a weapon). A fixed feminine head noun (e.g.
a process or action name) lets a trailing participle agree safely with *it*
instead of with the unknown injected value.

**`[X_possessive]` is unusable here too, for a different reason than
French.** Core `Keyed/Grammar.xml` sets `Prohis`=`o`, `Proher`=`a`,
`Proits`=`o(a)` — a bare **definite article**, not a possessive pronoun,
keyed off the **possessor's** gender, while Portuguese possessives must agree
with the **possessed** noun instead. Write the possessive literally, as
French does, though for a distinct underlying reason — check
`Keyed/Grammar.xml`'s actual values for the target language rather than
assuming the symbol inflects correctly.

## Style and corpus findings

Mandatory rules, corroborated across all four repos' independent corpus
counts (comments/`<!-- EN: -->` annotations stripped before counting, since
raw greps otherwise pick up English):

- **ASCII straight double quotes**, **zero em/en dashes** (reflow an English
  `—` into a colon, comma, or new sentence — the opposite of German, which
  mandates `–`, and matching Spanish/French's reflow), ASCII ellipsis `...`
  and ASCII apostrophe `'`. One corpus count (BTG, 2026-08-10): Core 1.20M
  chars carries 0 em, 0 en, 202 ASCII `"`, 1 curly pair, 1 `…`; Odyssey 209k
  carries 0 em, 2 en, 3 curly apostrophes — this is the *lowest* dash profile
  of any language checked in the family. A separate weapon-domain count
  (UWU) independently found 0 em/en dashes and 47 ASCII `...` vs 0 `…`.
- **Placeholder quoting (`'{0}'` vs `"{0}"`) is inherited from the English
  source, not independently chosen.** One corpus check found `'{0}'` and
  `"{0}"` nearly tied, with every instance sitting exactly where the English
  source put that same mark — there is no pt-BR-native preference to
  discover here, unlike most other style questions. Follow whichever mark
  the English key already uses rather than picking a "pt-BR house style".
- **Semicolons are effectively unused** in vanilla Keyed data. Where the
  English source uses `;`, split into two sentences instead (the same move
  French makes).
- **No space before `:` `;` `!` `?`** — the exact opposite of French, and the
  two languages are otherwise close enough that this is an easy
  cross-contamination to make by accident.
- No `¿`/`¡` — that punctuation is Spanish only.
- **Formality is `você`, decisively** — zero `tu`/`teu` anywhere in the
  corpus. Imperatives take the você form (`Clique`, `Selecione`, `Escolha`,
  `Certifique-se`, `Faça`, `Ative`, `Desative`). Note this register is
  functionally informal even though *você* is grammatically third person —
  it is neither German/Spanish's informal tu-forms nor French's formal
  *vous*; it's simply the only register pt-BR has.
- Descriptions/tooltips end with `.`; labels, buttons, stat fragments and
  float-menu reasons take none. Most def labels and research labels are
  lowercase noun phrases.
- **Casing is per def type, and it is the one convention that differs most
  from every other language in this family** — most of which use lowercase
  noun phrases across the board for def labels. Vanilla `FactionDef` labels,
  pawn nouns and `leaderTitle`s are **Title Case**, as are `PawnKindDef`,
  `MapGeneratorDef` and `ScenPartDef` labels — but `SitePartDef`,
  `WorldObjectDef`, `ColorDef` and most `ThingDef` labels are **lowercase**.
  Match the def type actually being translated, not a blanket rule.
- **`JobDef.reportString` is a subject-less lowercase gerund (-ndo) WITH a
  terminal period** (the large majority of Core's entries both start
  lowercase and end in `.`) — this matches Spanish exactly and is the
  opposite of Japanese/Korean, which drop the period.
- **Units are per-unit, not one rule** (counted over Core+Odyssey): `%` is
  **tight** (`{0}%`), but `W` and `h` are **spaced** (`} W`, `} h`) and
  `dias` is spaced (`} dias`). `x` is mixed in vanilla, so default to
  matching the English source's spacing for it.
- **Vanilla pt-BR files carry a UTF-8 BOM** (one count found it in all but
  one of 1543 vanilla files); mod-authored files never should.

## Grounded common vocabulary

All rows below are vanilla-attested (Core, Odyssey, or Royalty), not
mod-coined, and several are independently corroborated by more than one repo.

| English | Use | Never | Why |
|---|---|---|---|
| Cancel / Reset / Reset to defaults / Default / None / **Confirm** | Cancelar / Redefinir / Restaurar padrão(ões) / Padrão / Nenhum / **Aceitar** | Confirmar for Confirm | Core buttons — corroborated identically across all four repos. **Vanilla crosses the accept/cancel pair**: `Confirm`=`Aceitar` but the separate key `AcceptButton`=`Confirmar`, so don't "correct" one by grepping the other |
| quality tiers | horrível · pobre · normal · bom · excelente · obra-prima · lendário | `ruim` for poor | Core `QualityCategory_*`, corroborated across all four repos. `obra-prima` (masterwork) is a noun sitting among adjectives; vanilla is itself gender-inconsistent across the seven tiers, so don't assume they all agree with one gender |
| EMP (acronym) | **PEM** | EMP | Core/Royalty/Odyssey — pt-BR localizes the acronym (as Spanish does with PEM and French with IEM; German/ja/zh/ko all keep `EMP`) |
| market value | **valor de mercado** (StatDef) / **Preço base** (Keyed) | | `MarketValue.label`=valor de mercado but the Keyed `MarketValue`=Preço base — pick by which sense the string stands in for, the same split Spanish and French carry |
| traders guild / guild member(s) | Guilda dos Mercadores / Membro(s) da Guilda | Guilda Comercial | Odyssey `TradersGuild.*` |
| trader / merchant | comerciante / mercador | | Odyssey `TradersGuild.description` uses both: "comerciantes orbitais" for the trade role, "mercadores" for the guild's people |
| bulk / exotic goods trader | comerciantes de produtos variados / comerciantes de produtos exóticos | | Core orbital `TraderKindDef`s — plural |
| salvagers (faction) | Salteadores | Saqueadores | Odyssey `Salvagers.label` — its *pawns* are Piratas, and *saqueadores* is only the descriptive word used inside its own description, not the faction label |
| gold/silver inlay (trait) | incrustação de ouro / incrustação de prata | | Odyssey `GoldInlay.label` — a noun phrase |
| Traders will pay more/less for it. | Comerciantes pagarão mais por ela. / Comerciantes pagarão menos por ela. | | Odyssey trait descriptions — reused verbatim across all four repos |
| leader (`leaderTitle`) | Líder | | Core/Odyssey — the neutral slot when a faction has no bespoke title |
| goodwill / caravan / negotiator | Boa vontade / caravana / negociador | reputação | Core `Goodwill`, `Caravan.label`, `Negotiator` — pt-BR keeps the literal "boa vontade" that German/Spanish/French all reject |
| raid / reinforcements | invasão / reforços | | Core `Raid`, `RaidEnemy.label` |
| {0} from {1} are attacking your {2}. | {0} de {1} estão atacando seu(s) {2}. | | Every Odyssey `FactionDef` — verbatim, literal `(s)` number hedge included |
| Quest failed: [resolvedQuestName] | A missão falhou: [resolvedQuestName] | | Core — verbatim |
| [faction_name] became hostile to you. | [faction_name] tornou-se hostil a você. | | Core — verbatim |
| No capable negotiator | Nenhum negociador capaz | | Core |
| orbital platform / settlement platform | plataforma orbital / Plataforma de Assentamento | | Odyssey — lowercase `WorldObjectDef` vs Title Case `MapGeneratorDef` |
| orbital settlement / settlement | assentamento orbital / assentamento | colônia | Odyssey `SpaceSettlement.label`, Core `Settlement.label` — colônia is the *player's* colony specifically |
| shuttle | ônibus espacial | transporte | Core `Shuttle.description`, Odyssey `Shuttles.label`; Core's own `Shuttle.label` "transporte imperial" is the Royalty-specific def, don't generalize from it |
| transport/drop pod vs cargo pod | cápsula de transporte vs cápsula de carga | | Distinct vanilla concepts — don't merge |
| signal jammer / sentry drone / life support unit | bloqueador de sinal / drone sentinela / unidade de suporte de vida | | Odyssey |
| gravship / gravlite panel / pilot console | gravinave / painel de gravilita / console do piloto | | Odyssey `TheGravship` def labels |
| mechhive / orbital relay | mecholmeia / retransmissor orbital | | Odyssey `Mechhive.label`, `OrbitalRelay.label` |
| hatch / safe / garrison / outpost | alçapão / cofre / guarnição / posto avançado | escotilha | Odyssey/Core |
| silver / steel / market value / comms console / packaged survival meal / vacuum | prata / aço / valor de mercado / console de comunicação / refeição de sobrevivência embalada / vácuo | | Core |
| colour labels | lowercase adjectives (dourado, cinza, jade) | | Core + Odyssey `ColorDef`s |
| reportStrings (clean/rescue/**hack**/open/board) | limpando TargetA. / resgatando TargetA. / **hackeando TargetA.** / abrindo TargetA. / entrando em TargetA. | | Core+Odyssey `JobDef`s — verbatim gerund phrases that KEEP the trailing period (matches Spanish/French, unlike Russian/Korean) |
| starting people (ScenPart) | Pessoas Iniciais | | Core `ConfigPage_ConfigureStartingPawns.label` |
| advanced fabrication (research) | fabricação avançada | | Core `AdvancedFabrication.label` — verbatim (verified 2026-08-18) |
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | megapascal spelled out in a label | CE 16.7.4 pt-BR `CE_MPa`/`CE_mmRHA` — verbatim |
| blunt armor / sharp armor | Resistência - Contundente / Resistência - Cortante | Armadura - … | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; pt-BR's armor stat is "Resistência" |
| armor penetration | Penetração de armadura | | CE pt-BR `CE_DescArmorPenetration` — verbatim, the same as the family's existing settings strings |
| flak vest / flak jacket / frag grenade | colete de artilharia / jaqueta de artilharia / granadas de fragmentação | colete antibalas | Core labels — verbatim; the grenade label is plural |
| spacer-tech (attributive, VFEP) | de tecnologia espacial (`Carcaça de guerra de tecnologia espacial especializada ...`) | | Verbatim in the community VFEP pack's 10th-generation openers; Core Keyed `TechLevel_Spacer` = "Espacial" is the tier word (VFEP section, "spacer tier") |
| Imperial (adj.) | imperial (lowercase adjective) | | Royalty `Empire.pawnSingular`; in-text "flotilha imperial", "catafratas imperiais" |
| respirator (onboard) | respirador de bordo | | Pack's `telemetria de bordo` for "onboard"; Shipcracker ships `respirador de bordo`, Toxin's shipped descriptions use the bare `respirador` where its English has no "onboard" |
| sealed (helmet) | selado | | Shipped by Shipcracker and Toxin Warcasket helmet descriptions ("selado e equipado com um respirador de bordo", "selado por um respirador"); no Core attestation recorded in the glossaries |
| wearer | portador | | Core `Apparel_ShieldBelt.description`; the sets' shipped text says "piloto" for the warcasket's wearer (VFEP section) |
| plasteel / uranium / chemfuel | plastiaço / urânio / combustível químico | plastoaço | Core material labels. The community VFEP pack writes "plastoaço" in lore; vanilla's label wins because it is what the cost list shows |
| Off / On (settings) | Desligado / Ligado | | Core Keyed `Off`, `On`; mirrored in "Padrão: desligado." / "Padrão: ligado." (Default itself is the Default row above) |
| cooldown / cells / radius / range / hours (settings units) | tempo de recarga / células / raio / alcance / horas | Esfriamento | Royalty Keyed `Cooldown`; Core's `CooldownTime` "Esfriamento" is the weapon sense, not an ability's. Core Keyed `MapSizeDesc` "Células", `AbilityEffectRadius` "Raio do efeito". "alcance" and "horas" are as Shipcracker and Toxin ship them (`Alcance (células)`, `Tempo de recarga (horas)`); no Core key recorded for them |
| Odyssey (DLC name) | Odyssey | | Core `ExpansionDef` `Odyssey.label` keeps the English name |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | usando habilidade: {0}. | | VEF ships English only; subject-less lowercase gerund with the trailing period kept, like Core's `JobDef.reportString`s (Shipcracker Warcasket, shipped since 2026-09-26) |
| on cooldown (a reloadable comp's `cooldownGerund`) | em recarga | | Vanilla's default for `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker Warcasket) |

## Grounded common vocabulary, VFE Pirates warcasket domain (RafaelNaymaier/Traducao-Vanilla-Expanded-PT-BR pack + Core, 2026-10-28)

VFE Pirates ships English only. A community pt-BR translation exists and was
grounded against: RafaelNaymaier's "Tradução Vanilla Expanded PT-BR" (GitHub
`RafaelNaymaier/Traducao-Vanilla-Expanded-PT-BR`, Workshop 3643091941),
confirmed from its ThingDef, ResearchProjectDef and Keyed files; it carries the
Siegebreaker, Brute, Guardian, Cataphract and Hazard sets and the 7th- and
10th-generation paragraphs. Where the pack and Core disagree, Core wins
(plastiaço over the pack's plastoaço, main table). Every warcasket set in the
family (Shipcracker, Toxin, Medic, Overlord) renders these terms alike so the
sets read as one family in-game; a change is made here first and each set's
shipped files follow at its next pass. A set's own name, its Workshop title and
its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket (the noun, "shell" in the English first line folded in) | carcaça de guerra (f.), pl. carcaças de guerra | Community VFEP pack throughout (`VFEP_Warcasket_*.label`, `VFEP.RequiresWarcasket`). "shell" in the English first line folds into the same noun, as the pack does, so there is no separate "warcasket shell" row. |
| `<set>` warcasket / shoulders / helmet (label pattern) | carcaça de guerra `<set>` / ombreiras de carcaça de guerra `<set>` / capacete de carcaça de guerra `<set>` | Pack label pattern (`carcaça de guerra quebra-cerco`, `ombreiras de carcaça de guerra quebra-cerco`, `capacete de carcaça de guerra quebra-cerco`). The set name follows invariably or as an adjective (set-names row). Workshop titles are Title Case: `Carcaça de Guerra <Set>`. |
| pauldrons / shoulders | ombreiras | Pack uses `ombreiras` for both the label and the "pauldrons" in descriptions. |
| warcasket foundry | fundição de carcaças de guerra | Pack's `VFEP_WarcasketFoundry` label. |
| entomb / welded into (Workshop) | integrar (em carcaça de guerra) | Pack's `VFEPirates.EntombInWarcasket` = "Integrar em carcaça de guerra". "welded" uses the same verb, since "soldado" reads as "soldier". |
| spacer warcaskets / specialised warcaskets (VFEP research labels) | carcaças de guerra espaciais / carcaças de guerra especializadas | Pack `VFEP_SpacerWarcaskets.label` / `VFEP_SpecialisedWarcaskets.label`. Cited in prose as an ASCII double-quoted lowercase label, `a pesquisa "carcaças de guerra espaciais"`: no vanilla precedent, pt-BR research labels are lowercase, so the quotes do the job the English's Title Case does (Toxin Warcasket's shipped Keyed text; the "specialised" label is not cited in any shipped text yet). |
| VFEP set names | Quebra-cerco (siegebreaker), Bruto (brute), Guardião (guardian), catafrática (cataphract), de risco (hazard), aérea (aerial) | Pack's lore paragraphs ("A série Quebra-cerco", "A série Bruto", "A série Guardião", `A série de Risco`, "O design catafrática") and labels (`VFEP_Warcasket_Cataphract.label` = `carcaça de guerra catafrática`, `VFEP_Warcasket_Hazard.label` = `carcaça de guerra de risco`, `VFEP_Warcasket_Aerial.label` = `carcaça de guerra aérea`). Quebra-cerco/Bruto/Guardião are nouns, catafrática/de risco/aérea adjectives agreeing with carcaça (f.). Toxin Warcasket's glossary records the Aerial label as pack-grounded, Shipcracker's as "not checked"; the pack-grounded reading is kept (both ship `carcaça de guerra aérea`). Sarcophagus and controller: the pack carries them, but no glossary records their renderings, so they are not set here. |
| 7th generation / 10th generation (VFEP's two chassis) | de 7ª geração / de 10ª geração (`carcaças de guerra de 7ª geração`, `no nível espacial de 10ª geração`) | Pack's shared 7th- and 10th-generation lore paragraphs. |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | Carcaça de guerra especializada / Ombreiras de carcaça de guerra especializadas / Capacete de carcaça de guerra especializado, com proteção superior e peso elevado | Pack `VFEP_WarcasketShoulders_Cataphract.description` for the phrase "proteção superior e peso elevado", on its Cataphract line; Toxin Warcasket's shipped `shortDescription`s, agreement switched per part (especializada, especializadas for ombreiras, especializado for capacete). |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | Carcaça de guerra de tecnologia espacial especializada com proteção padrão / Ombreiras de carcaça de guerra de tecnologia espacial especializadas com proteção padrão / Capacete de carcaça de guerra de tecnologia espacial especializado com proteção padrão | Verbatim opening of the pack's 10th-generation descriptions (`VFEP_Warcasket_Siegebreaker`, `VFEP_WarcasketShoulders_Siegebreaker`, `VFEP_WarcasketHelmet_Siegebreaker`), agreement switched per part as above. Shipcracker's variant ends "com dispersão de impacto aprimorada" for its "improved impact dispersion". |
| the 7th-generation paragraph (VFEP's lore paragraph shared by every 7th-generation description) | As carcaças de guerra de 7ª geração surgiram após resultados insatisfatórios em melhorar ainda mais o desempenho básico, ... | Pack `VFEP_Warcasket_Hazard.description` paragraph 2, its "— embora intercambiáveis —" reflowed into commas ("que, embora intercambiáveis, funcionam melhor como um conjunto") and its "plastoaço" replaced by Core's `plastiaço`. The full text is Toxin Warcasket's shipped DefInjected `TXWC_Warcasket_Toxin.description`, paragraph 2, in `1.6/Languages/PortugueseBrazilian/`. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | As carcaças de guerra de 10ª geração foram, na verdade, adaptadas de equipamentos piratas capturados, ... mesmo entre gerações. | Pack `VFEP_Warcasket_Siegebreaker.description` paragraph 2, verbatim (no dashes to reflow; its English "dreadnoughts" kept as the pack has it); the pack's Siegebreaker / Brute / Guardian / Sarcophagus / Controller descriptions share it. The full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/PortugueseBrazilian/`. |
| pilot (the wearer) | piloto | Core backstories (`CargoPilot58.titleShort` "Piloto"); the shipped descriptions of Shipcracker and Toxin say "o piloto" where the English says "the pilot". |
| spacer tier (settings and prose) | nível espacial (`é de nível espacial`, `no nível espacial de 10ª geração`, suffix ` (parte do nível espacial)`) | Core Keyed `TechLevel_Spacer` "Espacial"; the suffix avoids a participle that would have to agree with an unnamed setting (Toxin Warcasket). |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | blindagem e isolamento de nível espacial / uma bolha de escudo / componentes avançados | Core `ComponentSpacer.label` "componente avançado"; "blindagem de nível espacial" and "bolha de escudo" are coined (Toxin Warcasket; Shipcracker uses "bolha de escudo" on its Workshop page and "escudo contra ataques à distância" from the pack's Brute lore for the ranged shield). |

The glossaries list nothing as pending native review for these rows: they are
the community pack's wording (the pack-grounded ones above) or Core-grounded.
The coined ones (nível espacial, blindagem de nível espacial, bolha de escudo)
are noted as coined in their rows; no glossary flags them as open.

## Pitfalls and lessons

- **Restructuring beats hedging whenever the injected symbol can be moved
  out of a fusing preposition's path entirely.** The reflex should be: check
  whether the symbol can land as a subject or direct object (no preposition
  needed) before reaching for the hedged `do(a)`/`pelo(a)` spelling — both
  vanilla's own idiom and every worked fix in this family land there.
- **Vanilla pt-BR itself ships broken or careless translations — frequency
  is not correctness.** Two documented cases worth checking against before
  copying a vanilla string as a template: Core's `TendPatient` reportString
  has a stray mid-string capital no other reportString carries, and its
  `FeedPatient` reportString translates as "carrying TargetA to TargetB"
  rather than "feeding" — it simply doesn't render the English source.
  Separately, `AppearedDaysAgo` doubles "ago" (renders literally as "Appeared
  {0} days ago ago"); prefer whichever sibling string renders the concept
  correctly instead of assuming a vanilla precedent is safe to imitate.
- **Confirm this glossary against the version of `Keyed/Grammar.xml` and the
  `WordInfo/Gender/*.txt` files actually shipping**, not against memory of
  another language's shape — pt-BR's possessive-symbol and gender-table
  behavior are both unusually severe compared to the rest of the family, and
  assuming a milder shape (like Spanish's, which at least resolves gender
  for ~2700 nouns) will under-hedge real strings.

- **pt-BR Keyed never switches on `CHARGENOUN_gender`, and its reload frames
  hard-code masculine** (`um {CHARGENOUN}`, `seu último {CHARGENOUN}`), so a
  feminine charge noun reads "um unidade" and no `WordInfo/Gender` line can
  fix it: prefer a masculine coinage (2026-10-13, Toxin Warcasket).
- `Miscellaneous` has no vanilla key; the nearest is `MiscRecordsCategory` =
  `Outros`. Core's `Vent` building is `saída de ventilação` (the temperature
  vent), so a gas vent should not reuse it (`válvulas` there).
- The community pack (`RafaelNaymaier/Traducao-Vanilla-Expanded-PT-BR`) is
  on GitHub; its VFE Pirates set names are adjectives (`catafrática`, `de
  risco`, `aérea`) and its shared 7th-generation paragraph carries em dashes
  and `plastoaço`, both to normalize (commas; the tar's `plastiaço`).
