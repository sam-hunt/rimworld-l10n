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
- Russian is one of the heavy-inflection languages (alongside Polish,
  Turkish, Czech, German) worth decompiling `LanguageWorker_<Language>` for
  before generating, since its authoring requirements (case/numeral
  agreement) are not otherwise obvious from reading the vanilla data alone.
