# Japanese — RimWorld localization mechanics

Consolidated from four sibling mods' `translate` skills. Provenance, oldest to
newest: UniqueWeaponsUnbound's machine-assisted generation (2026-07, no native
review), extended by UniqueMeleeWeapons' melee/quest pass (2026-07),
PersonaWeaponsUnbound's own generation (landed 2026-07-28, no native review),
and BetterTradersGuild's generation pass (2026-08-10), which re-verified the
`LanguageWorker` claim directly against the 1.6 assembly's full typedef list
and issued an explicit correction to a quoting rule the earlier passes had
shared (noted below). As of the latest pass, no native-speaker review has
landed for any of these; several individual findings below are flagged
in-line as still awaiting one.

## Engine mechanics (LanguageWorker)

**There is no `LanguageWorker_Japanese`, and that absence is the finding that
shapes everything else.** Verified 2026-08-10 against the 1.6 assembly's full
typedef list: workers ship for Catalan, Czech, Danish, Default, Dutch,
English, French, German, Hungarian, Italian, Korean, Norwegian, Portuguese,
Romanian, Russian, Spanish, Swedish and Turkish — Japanese is not among them.
`LanguageInfo.xml` declares no `languageWorkerClass` either, so the base
`LanguageWorker` runs, and its `PostProcessed` only calls
`MergeMultipleSpaces()`. No elision, no contraction, no `'s` rewriting, no
particles. Nothing rewrites these strings, so what is authored is what ships
— and equally, nothing will rescue a malformed one.

Japanese also needs no gender, number or case agreement, so every hazard that
organizes the German/Spanish/French/Brazilian-Portuguese sections of the
broader skill (grammatical agreement with an unknown injected noun, mandatory
contractions nothing supplies) simply does not arise for Japanese: a sentence
with an injected symbol can generally keep its English-like shape with the
token dropped in place, where those other languages must restructure it.
Note that a missing `LanguageWorker` is not inherently good or bad — the same
absence that removes the author's problem in Japanese is precisely what
*creates* it in Brazilian Portuguese, where mandatory contractions get no
help from any hook. What matters is whether the language's own grammar needs
the rewriting, not whether the hook exists — confirm a worker's existence by
enumerating the assembly's types, never by assuming a major language has one.

**Folder/tar naming:** RimWorld's language folder is `Japanese` (tar:
`Japanese (日本語).tar`); a mod's language directory must match it exactly.
Decompile-verified against `Verse.LoadedLanguage`: the constructor derives
`legacyFolderName` by cutting the declared name at `(`, and directory
matching accepts either `folderName` or `legacyFolderName` — so a mod folder
literally named `Japanese` loads correctly. (The same mechanism underlies
`Korean`.)

## Style and corpus findings

Counted 2026-08-10 over Core+Odyssey, Keyed **and** DefInjected, comments
stripped — 887k chars of translated values. Earlier passes (2026-07) had
already identified most of these qualitatively from Keyed data alone; the
counts below are the tree-wide confirmation.

- **ASCII `.` and `,`, never `。` or `、`.** Verified tree-wide: zero 。 and
  zero 、 in all 887k chars, against 13,747 ASCII periods and 14,771 ASCII
  commas. Also zero full-width spaces `　` and (bar 2 stray Keyed instances)
  zero full-width parens — ASCII `(` `)` throughout, 603 of them.
- **Corner brackets 「」 and ASCII quotes are different slots; the nearer
  analog decides which to use.** 171 「」 ship tree-wide, but they mark
  quoted *text* — note contents, map inscriptions, prose citations
  (`次の言葉が書かれている ——「[mapText]」`). For a **UI command the player
  clicks**, vanilla's own Odyssey `TheGravship` GameStartDialog uses ASCII
  double quotes instead: `ワールドマップで"惑星を見る"を選択し`. **This
  corrects an earlier sibling-inherited rule** that used 「」 for
  cross-referenced UI labels generally — the corrected version is: 「」 for
  quoted text/labels appearing in descriptive prose, ASCII `"…"` for a
  UI element the player is instructed to click. This is also the *opposite*
  of Simplified Chinese, which reaches for 「」/curly quotes in precisely
  this UI-command slot — do not generalize between the two CJK languages.
  Quality-tier labels follow the "prose" side of this split (take 「」 when
  named in prose) but take no quotes at all in the vanilla compound template
  `{0}以上の品質`.
- **Dashes: 56 em dashes in 887k chars (6.3 per 100k), 22 of them doubled
  ——, and zero en dashes.** Most instances repeat one `RulePackDef` idiom
  (treasure-map notes: `次の言葉が書かれている ——「[mapText]」`), so the real
  diversity is far below the raw count. Ellipsis is ASCII `...` (86 hits)
  over `…` (14) — vanilla Keyed uses `...` near-exclusively.
- **Units attach tight, with no per-unit split** — `{0}W`, `{0}%`, `{0}x`,
  `{0}日`, `{0}時間`, `{0}個` are all directly concatenated, no space, no
  split-by-unit-type. This is simpler than fr/es/pt-BR, which each split
  percentages from other units; in Japanese one rule covers everything.
- **Colons are per-slot, not per-rule.** ASCII `:` dominates over full-width
  `：` (442 vs 111 tree-wide) and is used before an injected value
  (`テックプリントが適用された: {PROJECT_label}`, `クエスト失敗:
  [resolvedQuestName]`) — but some vanilla strings use a full-width one
  instead (`注意：このシナリオは…`, `内容物：重力コア`). Copy the exact slot
  from the nearest vanilla analog; don't apply a blanket rule.
- **Register splits by def type, not by a single language-wide choice.**
  Descriptions and tooltips take polite です/ます and end with `.`; labels,
  buttons, section headers and `ScenPartDef` labels take no period.
  `ThoughtDef` stage descriptions are the exception to the です/ます rule:
  plain first-person, no polite form. DLC names stay in Latin script
  (Biotech, Royalty, Odyssey), as does the bare word "MOD".
- **`reportString`s (and other job-report text) carry NO trailing period**
  where the English has one, and take the progressive 〜中 / 〜している form,
  with no subject stated. This matches Russian and Korean, and is the
  *opposite* of German/Spanish/French/Brazilian-Portuguese, which all keep
  the period. `TargetA`/`TargetB` symbols stay bare, unquoted.
- **`traitAdjectives`-style attributive slots must be ATTRIBUTIVE forms that
  read as a prefix on an unknown noun** — vanilla examples end in の (金の,
  探知の), な (正確な), い, or a plain attributive verb (輝く, 灼熱の). A
  namer or rule pack that concatenates such a slot directly against a noun
  with no space will read broken if given a bare noun instead. Because
  Japanese needs no gender/number/case agreement, the noun's identity never
  constrains which attributive form is legal — unlike German, Spanish,
  French or Brazilian Portuguese, where the same slot must agree with an
  unknown noun's gender.
- **`stuffProps.stuffAdjective` is a `〜製` suffix** (鉄製, プラスチール製,
  木製, ヒスイ製), so a generated `[stuff_adjective]の[noun]` composes
  cleanly as long as the の is supplied explicitly in the authoring rule —
  it matches the same の-terminated shape as the attributive adjectives
  above.
- **Name-generation grammar:** no spaces around `[symbol]` tokens; the
  pattern "The X of Y" becomes `[Y]の[X]`; vanilla *keeps*
  `[RECIPIENT_possessive]` in this construction, unlike Simplified Chinese,
  which drops it.
- **Battle-log grammar:** entries end in plain past tense (よけた, 受け流し
  た); vanilla `[skillAdv]` values are adverbials (巧みに, ゆっくりと), so an
  optional `[skillAdvMaybe]` slots directly before the verb. `deathMessage`
  keeps vanilla's literal space after the pawn token: `{0}は 斬られて…`.
- **ColorDef labels follow the def's `colorType`, not one blanket rule.**
  Vanilla weapon-family ColorDefs (Odyssey `UniqueWeapon_*`) use bare nouns
  (金, 灰, 緑); structure-family ColorDefs (Core `Structure_*`) use 〜色
  compounds (赤褐色, 淡い青色) or katakana. Check which family a given
  ColorDef belongs to before choosing a shape.

**Vanilla Core/Odyssey defs worth checking as near-exact templates before
composing new content in adjacent domains:** Core's `TradeRequest`
QuestScriptDef (description framing, quality-phrase placement, both
failure-letter strings) for any trade/quest-failure text; Odyssey's
`TheGravship` ScenarioDef for gravship-launch/scenario-difficulty prose;
Odyssey's `AncientHatch` for `CompHackable` hack-progress/hacked strings; and
Odyssey's `SpaceSettlement.description` for orbital-settlement flavor text.
Checking these before drafting analogous strings has repeatedly turned up
verbatim-reusable sentences.

## Grounded common vocabulary

All rows below are traced to a specific Core or Odyssey vanilla def (not
mod-coined); several are used identically by every localized mod in this
family and are safe defaults for new work.

| English | Use | Never | Why |
|---|---|---|---|
| Cancel / Reset / Confirm | キャンセル / リセット / 了承 | | Core buttons (Keyed) |
| Randomize | ランダム | | Core Keyed button |
| Reset to defaults / Default / None | デフォルトに戻す / デフォルト / なし | | Core `RestoreToDefaultSettings`, `Default`, `None` |
| quality tiers | 壊れかけ/低品質/標準品/良品/秀品/名品/幻の一品 | | Core `QualityCategory_*` |
| "of normal+ quality" / "(worth [X])" | 標準品以上の品質の / (価値 [X]) | | Core `TradeRequest` — verbatim; ja places the quality phrase BEFORE the item, where a Japanese attributive belongs |
| trader / merchant | 商人 / 貿易商 | | Odyssey `TradersGuild.description` uses 商人 for the guild's people, `GoldInlay.description` 貿易商 for the trade role |
| orbital trader | 軌道上の商人 | | Odyssey `TradersGuild.description` |
| Traders will pay more/less for it. | 貿易商は高値でこれを買い取ります. / 貿易商は低い価格でこれを買い取ります. | | Odyssey `GoldInlay`/`Ugly` — verbatim |
| leader (`leaderTitle`) | リーダー | | Core/Odyssey default across many FactionDefs (`GravshipCrew`, `Ancients`, `Insect`); some Odyssey factions deviate (`TradersGuild`=交易修士, `Salvagers`=ボス) — check the specific FactionDef |
| salvagers (faction) | 略奪者 | 回収業者 | Odyssey `Salvagers.label` (its *pawns* are 宙族) |
| goodwill / caravan / negotiator | 友好値 / キャラバン隊 / 交渉人 | 好感度 | Core `Goodwill`, `Caravan.label`, `Negotiator` |
| silver / steel / market value / comms console / packaged survival meal / vacuum | シルバー / スチール / 標準小売価格 / 通信機 / 非常用食品 / 真空 | | Core |
| garrison / outpost / safe / hatch / medbay / ship's hold | 駐屯地 / 前哨基地 / 金庫 / ハッチ / 医務室 / 船倉 | | Core `AncientGarrison`, Odyssey `Outpost`/`AncientSafe`/`AncientHatch`; 医務室 and 船倉 are vanilla ja words found elsewhere in the tree |
| signal jammer / sentry drone / life support unit | シグナルジャマー / セントリードローン / 生命維持ユニット | | Odyssey |
| requires signal jammer | シグナルジャマーが必要 | | Odyssey `TransportPodDestinationRequiresSignalJammer` — verbatim |
| gravship / gravlite panel / pilot console / gravcore | グラヴシップ / 重力軽量パネル / パイロットコンソール / 重力コア | | Odyssey |
| mechhive / orbital relay | メカハイブ / 軌道リレー | | Odyssey `Mechhive.label`, `OrbitalRelay.label` |
| shuttle | シャトル | 宇宙往還機 | Odyssey `Shuttles.label` (passenger shuttle = 旅客シャトル) |
| drop pod vs transport pod vs cargo pod | ドロップポッド vs 輸送ポッド vs 貨物ポッド | | Core `DropPodIncoming`, `TransportPod`, `CargoPodCrash` — three distinct terms, don't merge |
| orbital platform / settlement platform | 軌道プラットフォーム / 入植用プラットフォーム | | Odyssey `OrbitalPlatform.label`, `SettlementPlatform.label` (a MapGeneratorDef slot) |
| orbital settlement / settlement | 軌道上の入植地 / 入植地 | | Odyssey `SpaceSettlement.label` |
| Quest failed: [resolvedQuestName] | クエスト失敗: [resolvedQuestName] | | Core `TradeRequest` — verbatim |
| [faction_name] became hostile to you. | [faction_name]があなたのコロニーと敵対状態になりました. | | Core `TradeRequest` — verbatim |
| hostile to {0} | {0}と敵対関係 | | shaped from Core `QuestHostileTo` (`{0}と敵対`) |
| No capable negotiator | まともな交渉人がいません | | shaped from Core `CommandTradeFailNoNegotiator` |
| {0} from {1} are attacking your {2}. | {1}の{0}は {2}を攻撃中です. | | every Odyssey `FactionDef` — verbatim, including its internal double space |
| Attack {0} / Attacking {0}. | {0}を攻撃 / {0}を攻撃中 | | Odyssey `Outpost` approach strings — verbatim; ja drops the English's trailing period on both |
| reportStrings (clean/rescue/tend/feed/hack/open/board) | TargetAを掃除中 / TargetAを救助中 / TargetAの看病中 / TargetAをTargetBに給仕中 / TargetAをハッキングしている / TargetAを開封中 / TargetAに乗り込んでいる | | Core+Odyssey `JobDef`s — verbatim. No trailing period, and TargetA/TargetB stay bare |
| advanced fabrication (research) | 先進組立製造 | | Core `AdvancedFabrication.label` — verbatim (verified 2026-08-18) |

## Pitfalls and lessons

- **One Core ja `TradeRequest` string is wrong.** `LetterTextFavorReceiver`
  reads `誰が[X]を持っていると信じるべきですか?` — "who should we believe
  *holds* [X]?" — which inverts the English, where the player is actually
  picking who *receives* the favor. Flagged for native review rather than
  mirrored as-is. Lesson: frequency is not correctness, and this applies to
  vanilla's own shipped data, not just machine-generated mod translations.
- **A missing `LanguageWorker` is a finding to verify, not an assumption to
  make.** Confirm by enumerating the assembly's full typedef list; don't
  infer a worker's existence (or absence) from a language's perceived
  "major" status. The same absence can remove an authoring hazard in one
  language (Japanese: no agreement, no contraction to get wrong) while
  creating one in another (Brazilian Portuguese: mandatory contractions with
  no hook to supply them).
- **A corrected rule should replace, not stack with, the earlier one.** The
  cross-referenced-UI-label quoting rule was revised from "always 「」" to
  "「」 for prose citations, ASCII quotes for a UI command the player must
  click" after checking a second vanilla example (`TheGravship`
  GameStartDialog). When two passes of the same language disagree, treat the
  later, more-evidenced pass as authoritative rather than merging both.
- **Don't carry a CJK convention across languages by analogy.** Simplified
  Chinese uses 「」/curly quotes for the exact UI-command slot where Japanese
  uses ASCII quotes — the two CJK languages diverge here, not converge.
- **Colon and dash usage are corpus facts to look up per string, not rules to
  apply uniformly** — vanilla ja mixes ASCII `:` with full-width `：`, and
  the correct choice is decided by the nearest matching vanilla string, not
  a general policy.
