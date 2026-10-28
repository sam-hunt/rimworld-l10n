# Russian — RimWorld localization mechanics

Grounded across the mod family: Better Traders Guild's (BTG) 2026-08-10
generation pass (Core + Odyssey vanilla data), consolidated with Unique
Weapons Unbound's (UWU) PR #6 — the one genuine **native review** this
language has had in the family. Russian is community-maintained upstream
(per UWU's non-negotiables); treat any future edits to a contributor's
phrasing the same way, rather than rewriting wholesale without explicit
direction. RimWorld's language folder is `Russian` (tar:
`Russian (Русский).tar`).

## Engine mechanics (LanguageWorker)

**`LanguageWorker_Russian` overrides no `PostProcessed`** (decompile-verified)
— no elision, no contraction, no `'s` rewriting, and `WithDefiniteArticle` /
`WithIndefiniteArticle` fall through to the base (Core `Keyed/Grammar.xml`
sets `DefiniteArticle`/`IndefiniteArticle` empty and `DefiniteForm`/
`IndefiniteForm` to `{0}`), so `[X_definite]` is a pure passthrough and every
contraction lesson that applies to de/es/fr/pt-BR is inapplicable here.
Russian's difficulty is case and numeral agreement, and the worker exposes a
mechanism for each.

- **`{N_numCase ? formOne : formSeveral : formMany}` — numeral agreement, and
  the one construct that *replaces* its placeholder.** `TotalNumCaseCount` is
  3, and `LanguageWorker.ResolveNumCase` returns `number + " " + form`, i.e.
  it **prints the number itself**. So Core ru renders an English `"{0} days"`
  as `{0_numCase ? день : дня : дней}` with **no separate `{0}`** — writing
  both would print the number twice. `GetFormForNumber` picks formOne for
  n%10==1, formSeveral for n%10 in 2–4, formMany otherwise, with the teens
  (n/10%10==1) forced to formMany. Use it wherever a slider or count is
  followed by a noun. Two caveats: it reaches the *string* branch too, where
  a non-integer yields `number + " " + formSeveral` — so an already-formatted
  decimal like `"3.2"` is better written plainly as `{2} дня` (decimals
  always take genitive singular in Russian anyway), which also sidesteps
  `float.TryParse` returning `""` on a culture mismatch. And a bare Latin
  unit never needs it: vanilla writes `{0} ч`, `{0} с`, `{0} Вт`.
- **`{lookup: {N}; Case; I}` — case declension, and it works in plain Keyed
  strings.** `GrammarResolverSimple` parses a `{name: args}` span as a
  *function* call and hands it to `LanguageWorker.ResolveFunction`, which
  implements `lookup` and `replace` (decompile-verified). Russian overrides
  `TryLookUp` to read `WordInfo/Case.txt`, whose rows are `ном; род; дат;
  вин; твор; предл`, so **index 3 is accusative** and 1 is genitive. Core
  ships ~1575 rows and Odyssey 12 more. Vanilla uses it in DefInjected as
  well as Keyed (see the FactionDef/SitePartDef examples in the vocabulary
  table below). **A miss degrades gracefully** — `TryLookUp` returns the
  (lowercased) key unchanged — so a mod-coined label just stays nominative
  rather than erroring. Two limits worth knowing: the checker-style
  placeholder comparison only sees a *nested* `{N}` (`{lookup: {2}; Case; 3}`
  is fine, `{lookup: [some_symbol]; Case; 1}` reads as one spurious
  placeholder and fails), and a mod-coined label is never in `Case.txt`
  anyway — so when the argument is a `[symbol]`, restructure the sentence
  instead of reaching for `lookup`.
- **`LanguageWorker_Russian` *does* override `TryLookUp`, and it lowercases
  the key first** — this is the behavior a `lookup` miss falls back to, and
  it is a genuine cross-language difference: German's base `TryLookUp`
  returns the caller's `keyName` untouched on a miss (capitalization
  intact), so don't assume the same fallback shape applies outside Russian.
- **`Pluralize` reads the `plural` table first, then an ending-based
  fallback on the last character, and a mod can ship both tables**
  (decompile-verified 2026-10-11). A multi-word coined noun in a
  `{X_plural}` slot (a `chargeNoun` such as `единица топлива`) gets the
  fallback applied to the whole string and its `{lookup: ...; Case; 1}`
  misses, so the mod ships `Languages/Russian/WordInfo/plural.txt`
  (`единица топлива;единицы топлива`) and `case.txt` rows for both numbers
  (six forms, nominative key); the tables are assembled from every mod's
  language folder with lowercased keys. Name the files lowercase: the
  loader asks for `plural.txt`/`case.txt`, and Core's capitalised
  `Plural.txt`/`Case.txt` resolve only through the tar's case-insensitive
  lookup. A multi-word `def.label` a mod hands to `Pluralize` or
  `{X_labelPlural}` pluralizes correctly only when Core's table lists it
  (it does for `AncientCryptosleepCasket`; decompile-verified 2026-10-18 on
  1.7.4981).

## Style and corpus findings

Counted against the vanilla ru data (mandatory rules):

- **Guillemets `«…»`** for cited names and UI commands — vanilla writes
  `Задание провалено: «[resolvedQuestName]»` and `выберите «Просмотр
  планеты»`. Never `"` or `„…"`.
- **Em dash `—` is the most common of any language surveyed in this family
  (27.4 per 100k), but that does not license introducing a new one.** The
  no-new-dashes rule (a dash the English source does not have must not
  appear in a translation; reflow into that language's ordinary punctuation
  instead) still applies — one mod's Russian ran 3.4x vanilla's dash rate
  before its instances were reflowed. Russian is the language where the
  temptation is strongest, because the dash is genuinely mandatory in a
  nominal sentence with an omitted copula and in verb gapping (`а сделка —
  повыгоднее`). Both have clean rewrites that are *better* Russian, not
  merely dash-free: use the `Чем …, тем …` correlative for an "X = Y"
  equivalence, and repeat the elided verb (`а сделка стала повыгоднее`)
  instead of gapping. Ellipsis is ASCII `...`. Descriptions end `.`; labels,
  buttons and stat fragments take none, and labels are lowercase noun
  phrases.
- **`ё` is written**, not folded to `е` (паёк, всё, ещё, налёт).
- **`reportString`s take no trailing period and are 3rd-person present
  verbs** — `убирает TargetA`, not a noun phrase and not `убирает
  TargetA.`. This is the opposite of German, which keeps the trailing
  period on report strings. (This refines an earlier family note that had
  filed "job report strings → noun phrases" as a Russian rule; that
  convention actually belongs to *inspect* strings, a different string
  type — see the vocabulary table below.)
- Units attach with a space and stay Cyrillic where vanilla has one:
  `{0} ч`, `{0} Вт`. Some vanilla ru files carry a BOM; a mod's own should
  not.
- Formality is `вы`/`ваш` throughout.

## Grounded common vocabulary

Core/DLC-grounded terms usable by any mod in the family (verbatim vanilla
strings unless noted):

| English | Use | Never | Why |
|---|---|---|---|
| Cancel (button) | Отменить | Отмена | vanilla `Cancel`; buttons use infinitive verbs |
| inspect strings | noun phrases | finite verbs | matches inspect-pane convention (but see reportStrings above — a different string type) |
| Reset to defaults / Default / None / Reset | Восстановить по умолчанию / По умолчанию / Нет / Сбросить | | Core `RestoreToDefaultSettings`, `Default`, `None`, `Reset` |
| quality tiers | ужасно/плохо/нормально/хорошо/отлично/шедевр/легенда | | Core `QualityCategory_*` |
| trader / orbital trader | торговец / орбитальный торговец | | Core; Odyssey orbital TraderKinds are **plural** (оптовые торговцы, торговцы экзотикой) |
| goodwill / caravan | репутация / караван | доброжелательность | Core `GoodwillTip` |
| shuttle | челнок | шаттл | Core `Shuttle.label` |
| silver / market value / comms console / packaged survival meal | серебро / рыночная стоимость / консоль связи / сухой паёк | | Core |
| "of normal+ quality" / "(worth [X])" | качеством от нормального и выше / (стоимостью [X]) | | Core `TradeRequest` — verbatim |
| drop/transport pod | транспортная капсула | | Core `DropPodIncoming` |
| traders guild | гильдия торговцев | | Odyssey `TradersGuild.label` |
| salvagers | сталкеры | пираты (that's the faction's pawn word, not its name) | Odyssey `Salvagers.label` |
| orbital platform / settlement platform | орбитальная платформа / платформа поселения | | Odyssey `OrbitalPlatform.label` / `SettlementPlatform.label` |
| orbital settlement / settlement | орбитальное поселение / поселение фракции | | Odyssey `SpaceSettlement.label`, Core `Settlement.label` |
| gravship / gravlite panel / pilot console | гравикорабль / панель из гравлита / пульт пилота | | Odyssey |
| mechhive / orbital relay | мехрой / орбитальный ретранслятор | | Odyssey `TheGravship.description` |
| signal jammer / sentry drone / life support unit | глушитель сигналов / дрон-дозорный / блок жизнеобеспечения | | Odyssey |
| {0} from {1} are attacking your {2}. | {0} из фракции {1} атакуют ваших {lookup: {2}; Case; 3}. | | every Odyssey `FactionDef` — verbatim; demonstrates the `lookup`/Case mechanism above |
| Attack {0} / Attacking {0}. | Напасть на {lookup: {0}; Case; 3} / Нападает на {lookup: {0}; Case; 3} | | Core SitePartDef approach strings — verbatim, no trailing period |
| Quest failed: [resolvedQuestName] | Задание провалено: «[resolvedQuestName]» | | Core `TradeRequest` — verbatim |
| [faction_name] became hostile to you. | Фракция [faction_name] теперь враждебна к вам. | | Core `TradeRequest` — verbatim |
| starting people (ScenPart) | людей в начале | | Core `ConfigPage_ConfigureStartingPawns.label` — identical English source, reuse verbatim |
| reportStrings (clean/rescue/tend/feed/hack/open) | убирает TargetA / спасает TargetA / лечит TargetA / скармливает TargetA TargetB / взламывает TargetA / открывает TargetA | | Core `JobDef`s — verbatim; a mod's NPC-safe copies of these JobDefs can reuse them 1:1. Odyssey's `Open`/`EnterTransporter` wrap TargetA in `{lookup: {TargetA}; Case; 3}` — **don't copy that**, the bare English `TargetA` has no braces so a placeholder-parity checker reads the wrapper as an invented placeholder |
| advanced fabrication (research) | сверхвысокоточное производство | высокоточное производство | Core `AdvancedFabrication.label` — verbatim; the сверх- prefix is required, the shorter form reads as the fabrication-bench root (высокоточный станок) (verified 2026-08-18) |
| MPa / mm RHA (Combat Extended units) | МПа / мм RHA | MPa in Latin | CE 16.7.4 ru `CE_MPa`/`CE_mmRHA` — verbatim (GOST 8.417 МПа; RHA stays Latin) |
| blunt armor / sharp armor | Броня: Удар / Броня: Проникновение | | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; CE's `CE_DescBluntPenetration`/`CE_DescSharpPenetration` reuse Удар/Проникновение |
| armor penetration | Бронепробитие | | CE ru `CE_DescArmorPenetration` — verbatim, the same as the family's existing settings strings |
| flak vest / flak jacket / frag grenade | бронежилет / бронекуртка / осколочные гранаты | | Core labels — verbatim; the grenade label is plural |
| spacer-tech (attributive) | космического уровня | | Core `TechLevel_Spacer` = `космический`; the community VFEP pack's spacer sets say `сделанная по технологиям космического уровня` |
| Imperial (adj.) | имперский | | Royalty (`имперский дезертир`, `имперский торговец`) |
| plasteel / uranium / chemfuel | пласталь / уран / химтопливо | | Core; short form as in Odyssey and the community VFEP pack (`химтоплива`) |
| Off / Default: {0}. / (default) / When enabled (settings) | Выкл / По умолчанию: {0}. / (по умолчанию) / Если включено | | Core Keyed `Off`, `Default`, `default`; `Если включено` per Core's tooltips (Toxin's glossary), `Если отключено` as shipped; the "Default: on" value reads `По умолчанию: включено.` / `выключено.` |
| cooldown / range / cells and hours (settings units) | перезарядка / дальность / `(в клетках)`, `(в часах)`, `(%)` | | Core Keyed `CooldownTime`, `Range`; counts are written to avoid numeral agreement (`Клеток ...: {1}`) |
| Odyssey (DLC name) / (requires Odyssey) | Odyssey / (требуется Odyssey) | | Core `ExpansionDef` keeps `Odyssey` in Latin; `требуется` as in Core `SkillNeededForConstructing` |
| quantities with a named resource, tank capacity (settings) | `{0} ед. ({1})`, `Ёмкость бака ({0})` | | Core uses `{0} ед.` for mass quantities (`LowMedicineDesc`, `StatsReport_ReloadMarketValue`); the resource name stays nominative in parentheses, so no numeral or case agreement is needed |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | применяет способность «{0}» | | VEF ships English only; third-person present like Core's `JobDef.reportString`s, no trailing period, guillemets around the label (Shipcracker Warcasket, shipped since 2026-09-26) |
| on cooldown (a reloadable comp's `cooldownGerund`) | перезаряжается | | Shipcracker Warcasket's rendering of vanilla's `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it; Core's nearest string, Keyed `ShieldOnCooldown`, is `Восстанавливается`, so a native reviewer may prefer it |

## Grounded common vocabulary, VFE Pirates warcasket domain (OneCodeUnit/VanillaRussianExpanded pack + Core, 2026-10-28)

VFE Pirates ships English only. The community Russian translation of it,
OneCodeUnit/VanillaRussianExpanded on GitHub (Vanilla Russian Expanded), is
the grounding source: its warcasket is `броня мертвеца`, and its set pattern
is an adjective on `броня мертвеца`, with a named set's shoulders and helmet
dropping `мертвеца`. Every VFEP term below that cites a pack label was
grounded against that pack as the Shipcracker and Toxin glossaries record it;
the pack's files are not checked out beside the family repos, so a row not
marked as pack-grounded is a family coinage. Every warcasket set in the
family (Shipcracker, Toxin, Medic, Overlord) renders these terms alike so the
sets read as one family in-game; a change is made here first and each set's
shipped files follow at its next pass. A set's own name, its Workshop title
and its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket (also "warcasket shell") | броня мертвеца (f.; gen. брони мертвеца, acc. броню мертвеца, dat. броне мертвеца) | Community VFEP pack (`VFEP_Warcasket_Warcasket.label`). No separate word for "shell": it is dropped in the part descriptions, as the pack does. Case forms as shipped: `заковать в броню мертвеца`, `наплечники брони мертвеца`, `Даёт защитной броне мертвеца`. Research labels that name the warcasket in the plural use the singular collective (`Космическая броня мертвеца`). |
| `<set>` warcasket / shoulders / helmet (label pattern; pauldrons / shoulders, helmet) | `<set adj.>` броня мертвеца / наплечники `<set adj. gen.>` брони / шлем `<set adj. gen.>` брони | Pack pattern for named sets (Siegebreaker: `прорывная броня мертвеца`, `наплечники прорывной брони`, `шлем прорывной брони`). In descriptions the unnamed parts read `Специализированные наплечники брони мертвеца` / `Специализированный шлем брони мертвеца` (pack Hazard `shortDescription`s). |
| chassis (the warcasket frame) | каркас | The pack's word for the warcasket frame (shipped in Shipcracker as `на космическом каркасе десятого поколения`). |
| warcasket foundry | цех мертвеца | Community VFEP pack (`VFEP_WarcasketFoundry.label`). Foundries in general are `цеха`. |
| entomb / weld into (the set) | заковать в броню мертвеца | Community VFEP pack (`VFEPirates.EntombInWarcasket`). Shipcracker uses it on its Workshop page for "weld it on" and "welded into the set". |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | «Космическая броня мертвеца» / «Специализированная броня мертвеца» | Pack `VFEP_SpacerWarcaskets.label` (`космическая броня мертвеца`) and `VFEP_SpecialisedWarcaskets.label`, capitalised in guillemets as a cited project label; Russian quotes cited labels on its own convention, not because the English did. The pack's spacer label confirms Shipcracker's earlier coined row. |
| VFEP set names | прорывная (siegebreaker) / беспощадная (brute) / охранная (guardian) / катафрактарская (cataphract) / защитная (hazard) / воздушная (aerial), each as `<adj.> броня мертвеца` | Siegebreaker, Brute, Guardian: community pack set adjectives. Cataphract: pack `VFEP_Warcasket_Cataphract.label` `катафрактарская броня мертвеца`, agreeing with Royalty `Apparel_ArmorCataphract.label` (not used in Toxin's shipped Russian text). Hazard: pack `VFEP_Warcasket_Hazard.label` `защитная броня мертвеца` (shipped in Toxin's settings). Aerial: Shipcracker's Workshop and settings usage, shipped as `детали воздушной брони мертвеца`; the pack's own Aerial adjective was not available to check. The pack's Shock set is `штурмовая`, which is why Shipcracker avoids it. Sarcophagus and Controller: the glossaries record no Russian rendering (only that the pack has them); take the pack's adjective when a set first needs one. |
| 7th generation / 10th generation (VFEP's two chassis) | `Седьмое поколение` (pack's 7th-generation paragraph) / `Броня мертвеца десятого поколения` (pack lore), `каркас десятого поколения` (Shipcracker's prose) | Pack lore wording; `каркас` per the chassis row. |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | Специализированная броня мертвеца / Специализированные наплечники брони мертвеца / Специализированный шлем брони мертвеца с превосходной защитой ценой большего веса | The `Специализированная ...` head is the pack's Hazard `shortDescription`s; `с превосходной защитой ценой большего веса` is Toxin's coinage, pending native review. Shipped in Toxin's DefInjected `shortDescription`s. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | Специализированная броня мертвеца / Специализированные наплечники брони мертвеца / Специализированный шлем брони мертвеца со стандартными защитными характеристиками, сделанная / сделанные / сделанный по технологиям космического уровня. | Pack verbatim: `VFEP_Warcasket_Siegebreaker.shortDescription`, `VFEP_WarcasketShoulders_Siegebreaker.shortDescription`, `VFEP_WarcasketHelmet_Siegebreaker.description`; shipped in Toxin's Keyed `TXWC_SpacerShortDescription_*`. Shipcracker's variant replaces the protection clause: `космического уровня с улучшенным рассеиванием энергии ударов`, from the pack's Guardian (`с продвинутым рассеиванием энергии ударов`) with `улучшенным` for "improved". |
| the 7th-generation paragraph (VFEP's lore paragraph shared by every 7th-generation description) | Седьмое поколение стало результатом смены направления разработки. ... | Pack verbatim (its Aerial / Barrage / Hazard / Shock descriptions); of its two variants (comma after `Также` or not) the comma-less one, and its own comma in `вместо полной взаимозаменяемости, разные` is kept. The full text is the tail of Toxin Warcasket's shipped DefInjected descriptions in `1.6/Languages/Russian/`. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | Броня мертвеца десятого поколения была создана на основе образцов, найденных на захваченных пиратских судах. ... с меньшими потерями производительности. | Pack verbatim (its Siegebreaker / Guardian / Controller / Sarcophagus / Brute descriptions, `VFEPirates.WarcasketDef/Apparel_Various.xml`); of its two variants (comma after `подчиняющихся правительству` or not) the one with the comma, which closes the participial phrase, and the pack's `привело` (for a compound subject) is kept verbatim. The full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/Russian/`. |
| pilot (the wearer) | пилот | Pack (`Пилот может с комфортом...`); Shipcracker's prose; shipped in both sets. |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | защита и изоляция космического уровня / силовой щит / продвинутые компоненты | Core `Insulation_Cold` (`Изоляция`) and `ComponentSpacer.label`; `силовой щит` is the pack's word (Shipcracker's ranged shield), and Core's shield-belt tutor text frames it as stopping ranged attacks. |

Pending native review for the whole family: nothing in the pack-grounded rows
is open. Family coinages not checked against the pack: `воздушная` (aerial,
the pack's Aerial adjective was not available) and `с превосходной защитой
ценой большего веса`; the Sarcophagus and Controller adjectives are not yet
recorded. Shipcracker's open question about the spacer research label is
settled by the pack's own `VFEP_SpacerWarcaskets.label` row above. The
set-specific coinages each repo lists stay pending there.

## Pitfalls and lessons

- **Native review provenance: UWU PR #6.** The one general (non-weapon)
  correction it produced was **Cancel (button) → Отменить, never Отмена** —
  buttons use the infinitive verb, matching vanilla `Cancel`. (Its other
  finding, the weapon-trait word свойство vs черта, is domain vocabulary
  that stays with the weapon mods that need it.)
- **A `lookup` miss does not degrade identically across languages — check
  whether the worker overrides `TryLookUp`.** The base implementation
  lowercases only its internal probe key and returns the caller's `keyName`
  untouched on a miss (this is German's behavior). `LanguageWorker_Russian`
  *does* override `TryLookUp` and lowercases the key before the lookup, so a
  ru miss can come back lowercased. Same construct, different failure mode —
  don't generalize the fallback shape from one language to the other.
- **Resolved conflict:** an earlier family note filed "job report strings"
  under Russian as taking noun-phrase form (e.g. `Настройка {0}`). A later
  decompile-verified pass established that `reportString`s are actually
  3rd-person present-tense finite verbs with no trailing period (`убирает
  TargetA`), and that the noun-phrase convention belongs to a different
  string type — *inspect* strings. The decompile-verified finding wins; both
  conventions are kept above under their correct labels.
- **Calque tells in free prose (the family's first native-player complaint,
  LocalMineralScanner's Workshop page, 2026-09-19).** A Russian player called
  the mod's text rigid and machine-like. Every in-game string mirrored from a
  vanilla analog was clean; the complaint traced entirely to the mod's own
  sentences (Workshop blurb and FAQ, the building description), where the
  English skeleton survived under Russian words: stacked reflexive passives
  and participial phrases (`жилу, размещённую генерацией карты`),
  genitive/instrumental noun chains carrying an English subject-verb-object
  order (`трудозатраты на находку совпадают с`), and abstract nouns where
  Russian reaches for a verb (`Весь код проверяется и тестируется вручную`).
  The native rewrites use finite active verbs and the ordinary spoken clause
  order (`жилу, уже существующую на карте`; `требует столько же труда,
  сколько`; `благодаря двум пультам сканировать могут сразу два оператора`;
  `Я вручную проверяю и тестирую весь код`). Before committing, read every
  description and Workshop sentence for this on its own, separately from the
  vocabulary check; grounding catches words, not syntax.
- Russian is one of the heavy-inflection languages (alongside Polish,
  Turkish, Czech, German) worth decompiling `LanguageWorker_<Language>` for
  before generating, since its authoring requirements (case/numeral
  agreement) are not otherwise obvious from reading the vanilla data alone.

- **Vanilla ru ability labels are noun phrases** (`выброс пламени`,
  `распыление пены`), not verbs (2026-10-13, Toxin Warcasket).
- **A `{COUNT} {CHARGENOUN_plural}` slot cannot inflect an injected noun
  with `numCase`.** Restructure around a genitive lookup plus a
  parenthetical count: `Недостаточно {lookup: {CHARGENOUN_plural}; Case; 1}
  в баке (нужно {COUNT}).`, which needs the mod's `WordInfo/case.txt` row
  for the plural form (the lookup key is the pluralized noun).
- The community pack (`OneCodeUnit/VanillaRussianExpanded`) is on GitHub;
  its shared 7th-generation paragraph exists in two variants (with and
  without a comma after «Также»), so pick one and record it in the glossary.
