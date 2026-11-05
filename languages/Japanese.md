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
- **No space after the ASCII `.` and `,`** (Medic Warcasket, 2026-11-05):
  vanilla writes 8,129 `.` and 12,136 `,` directly before kana or kanji,
  against 131 and 69 followed by a space; the family's shipped Keyed already
  does the same.

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
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | メガパスカル in a label | CE 16.7.4 ships no Japanese, so CE's own info card shows the English `CE_MPa`/`CE_mmRHA`; JIS Z 8203 uses the Latin SI symbols |
| blunt armor / sharp armor | アーマー - 打撲系 / アーマー - 突刺系 | 鈍器, 鋭利 | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; ja keeps アーマー for armor |
| flak vest / flak jacket / frag grenade | 防弾チョッキ / 防弾ジャケット / 手榴弾 | 破片手榴弾 | Core labels — verbatim; ja's frag grenade is plain 手榴弾 |
| spacer-tech (attributive) | 宇宙技術を用いた | | Royalty `Apparel_PackJump.description` renders "spacer militaries" as 宇宙技術を用いる一部の軍隊 |
| spacer (tech tier) | 宇宙世紀 | | Core Keyed `TechLevel_Spacer` |
| Imperial | 帝国 / 帝国の | | Royalty `Empire.pawnSingular` 帝国; backstories 帝国教会, 帝国の牧師; `Apparel_ArmorCataphract` 帝国のカタフラクト部隊 |
| respirator / breathing (capacity) | 呼吸装置 / 肺機能 | | 呼吸装置 is a coined plain term (no vanilla respirator item); Core PawnCapacityDef `Breathing.label` is 肺機能 |
| sealed (airtight) | 気密 | | Odyssey `GravshipHull.description` (気密壁) |
| plasteel / uranium / chemfuel | プラスチール / ウラン / バイオ液化燃料 | | Core |
| ability | 能力 | | Royalty Keyed (この能力を獲得しますか) |
| Off / On (settings) | Off / On | | Core Keyed `Off`, `On` (vanilla keeps On/Off in Latin script); Default is the row above |
| cooldown / cells | クールダウン / タイル | | Core Keyed `StatsReport_Cooldown`, `AbilityOnCooldown`; `RoomRequirementArea` ({0}タイル) counts map cells as タイル, no space before the unit (vanilla also uses セル in one Keyed string, pending native review) |
| range / hours (settings slider captions) | 範囲 (タイル) / クールダウン (時間) | | The shipped Shipcracker Warcasket Keyed forms (`SCWC_JumpRange`, `SCWC_Cooldown`); (時間) could read as "(time)", pending native review. 範囲 is the area or jump-distance word; an ability's reach is Core Keyed `Range` = 射程, the word vanilla's ability tooltip prints (Medic Warcasket ships 射程, 2026-11-05) |
| Odyssey (DLC name) | Odyssey | | Core `ExpansionDef` `Odyssey.label` keeps the Latin name; DLC names stay in Latin script (style section above) |
| (requires Odyssey) / (default) suffixes (settings window) | ` (Odysseyが必要)` / ` (デフォルト)` | | ASCII parens with a leading space, as in vanilla Keyed (`使用できない (太陽フレア)`, `{1_label} (死亡)`); が必要 from Core Alerts (`医者が必要`) |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | 能力を使用中: {0} | | VEF ships English only; progressive 〜中 form with no trailing period, per the reportString rule above (Shipcracker Warcasket, shipped since 2026-09-26) |
| on cooldown (a reloadable comp's `cooldownGerund`) | クールダウン中 | | Vanilla's default for `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker Warcasket) |

### Medical, tending and ability vocabulary (Core and Odyssey; Medic Warcasket, 2026-11-05)

| English | Use | Never | Why |
|---|---|---|---|
| herbal / industrial / glitterworld medicine | 薬草 / 医薬品 / 最先端医薬品 | | Core `MedicineHerbal`, `MedicineIndustrial`, `MedicineUltratech` labels |
| medicine (the category) / medicine kit | 薬 / 薬のキット | 医薬品 for the generic | Core ThingCategory `Medicine.label`; 医薬品 is the industrial medicine's own label; キット per Core `MedicineIndustrial.description` (医薬品キット) |
| go-juice / wake-up / heart attack | ゴージュース / ウェイクアップ / 心筋梗塞 | | Core labels |
| mechanites (the particles) | メカナイト | 機械化症 | Core `FibrousMechanites.description`, `SentienceCatalyst.description`; 機械化症 is the hediff (disease) label only |
| tend / tend quality / tend speed / medical skill | 看護 / 看護品質 / 看護速度 / 医術 | | Core Keyed `Tend`, `WorkTagCaring`, `MedicalTendQuality` (看護・品質), `MedicalTendSpeed` (看護・速度), `Medicine.skillLabel`; Keyed `TendQuality` alone says 看病品質 |
| treat (disease) / doctor (work type) | 治療 / 医者 | | Core `Doctor.verb`, `Doctor.gerundLabel` (治療), `Doctor.labelShort` (医者) |
| infection / disease / missing body part / wound | 感染症 / 病気 / 身体欠損 / 傷 | | Core `WoundInfection.label` (傷からの感染症), `Disease_*` letters, `MissingBodyPart.labelNoun`, `WoundInfection.description` |
| pain / pain shock | 痛み / 痛みでショック | | Core Keyed `Pain`, `PainShock`; `PainShockThreshold.description` 痛みによって失神する |
| downed | 倒れた / 倒れている | 失神 in prose | Core `Wait_Downed.reportString`; `Downed.label` 失神 reads as fainting |
| hostile | 敵対 / {0}は敵対しています. | | Core Keyed `Hostile` |
| casting time / range / line of sight required | 詠唱時間 / 射程 / 視線が通ることが必要 | | Core Keyed `AbilityCastingTime`, `Range`, `AbilityRequiresLOS` |
| enabled / disabled (state words) | 有効 / 無効 | | Core Keyed `Enabled`, `Disabled` |
| reload (a reloadable comp) | 充填 | | Core Keyed `Reload` ({GEAR_labelShort} に {AMMO_label}を充填する), `CommandReload_NoAmmo`; verbs' descriptions say 再装填 (`LaunchFragGrenade`) |
| traits (the Bio tab section) | 才能・性格 | 特性 for a pawn trait | Core Keyed `Traits`; 特性 is the unique-weapon trait (`WeaponTraits`) |
| Work tab | 「優先順位」タブ | | Core `WorkTab.helpText`; MainButtonDef `Work.label` 優先順位 |
| veteran(s) | 退役軍人 | | Core `MechWarVeteran77.title` |
| Mote (an inherited `MoteBase` label) | 塵 | | Core `Mote_*` labels, 64 of 64 |
| trait description tokens | `{PAWN_nameDef}は` / `{PAWN_pronoun}が` (or は) / `{PAWN_objective}` bare | | Core trait descriptions; Grammar `ProhimObj` = 彼を, so `{PAWN_objective}` already carries its を and takes no particle |
| Blue / Green / Pink | 青 / 緑 / ピンク | | Core Keyed `Blue`, `Green`; no `Pink` key, `Hair_Pink.label` (ピンク色の髪) |
| "X in the bloodstream." (drug hediff opener) | 血中にXが浸透しています. | | Core `GoJuiceHigh.description`, `WakeUpHigh.description` |

## Grounded common vocabulary, VFE Pirates warcasket domain (coined in Shipcracker Warcasket's 2026-09-26 pass, extended by Toxin Warcasket's 2026-10-13 and 2026-10-22 passes; 2026-10-28)

VFE Pirates ships English only, and no community Japanese translation could
be grounded against: only the noun is attested (the Japanese mod database
rimworld.2game.info tags VFE Pirates content as ウォーキャスケット and marks
VFEP as 日本語化対応, but no translation files were found), so every other
VFEP term here is a family coinage pending native review. A different mod,
Vanilla Armour Expanded, renders "siegebreaker" as シージブレーカー, which is
the basis for keeping set names in katakana. If a community VFEP pack turns
up, re-ground these rows against it and prefer its renderings. Every
warcasket set in the family (Shipcracker, Toxin, Medic, Overlord) renders
these terms alike so the sets read as one family in-game; a change is made
here first and each set's shipped files follow at its next pass. A set's own
name, its Workshop title and its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket | ウォーキャスケット | The community VFEP noun (rimworld.2game.info tagging), the one attested term. Required in the Workshop title. No gender or plural in Japanese. |
| `<set>` warcasket / `<set>` warcasket helmet (label pattern) | `<セット>`・ウォーキャスケット / `<セット>`・ウォーキャスケットヘルメット | Core/Royalty attach ヘルメット and アーマー directly (カタフラクトヘルメット, レコンヘルメット); Biotech/Odyssey separate a katakana modifier from a katakana compound with ・ (メカノイド・ドロップポッド, サブコア・エンコーダー). |
| pauldrons / shoulders / shoulder pads | ショルダーアーマー | Coined; no vanilla shoulder piece exists. Chosen over bare ショルダー (reads as the body part or a bag) and ショルダーパッド (evokes suit or sports padding). Used for the label, the description and the Workshop "shoulder pads"; the resulting label length is pending native review. |
| warcasket shell | ウォーキャスケット外殻 | Coined; plain word for "shell". |
| warcasket foundry | ウォーキャスケット鋳造台 | Coined; also "foundries" in prose as 鋳造台. The Korean community uses 주조대, the same "casting bench" idea. Unattested in Japanese. |
| entomb | 封入 | Coinage, unattested. Shipped by Shipcracker (Workshop) and Medic (trait description, `MDWC_WorkDesc`, Workshop); Toxin's Workshop says 溶接されている間 for the same line and follows at its next pass. Entombing a pawn is 封入; building at the foundry is the next row's 溶接, so the two no longer share one word (Medic Warcasket, 2026-11-05). |
| build / weld at the foundry | ウォーキャスケット鋳造台で溶接 | VFEP's own `VFEP_DoWelding` work giver (verb "weld at", label "welding at warcasket foundry"); both siblings' Workshop FAQ and Medic's. |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | 「宇宙世紀のウォーキャスケット」 / 「特殊なウォーキャスケット」 | Coined; 宇宙世紀 is Core `TechLevel_Spacer` (main table). 「」 for a label cited in descriptive prose, per the quoting rule above. The first is shipped in Toxin Warcasket's Keyed (研究「宇宙世紀のウォーキャスケット」), both appear on its Workshop page. |
| VFEP set names | シージブレーカー (siegebreaker), ブルート (brute), ガーディアン (guardian), エアリアル系 (aerial), カタフラクト (cataphract), ハザード (hazard; ハザード・ウォーキャスケット) | Katakana per the set-name habit; シージブレーカー is attested in Vanilla Armour Expanded's Japanese, the others coined to match, pending native review, except カタフラクト (Royalty `Apparel_ArmorCataphract.label` = カタフラクトアーマー). controller and sarcophagus have no Japanese rendering recorded yet. |
| 7th generation / 10th generation (VFEP's two chassis) | 第7世代 / 第10世代 | Plain generation numbering. VFEP's dashed aside on the 7th generation is reflowed as "パーツの互換性は保ちつつ,". |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | 特殊なウォーキャスケット`<パーツ>`で,防護性能に優れる反面,重量が増しています. | Toxin Warcasket's shipped `shortDescription`s; 特殊な for "specialized" is Shipcracker's description wording, the rest coined. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | 宇宙技術を用いた特殊なウォーキャスケット`<パーツ>`で,標準的な防護性能を備えています. | "宇宙技術を用いた" is spacer-tech (main table); 標準的な防護性能 coined against the 7th-generation 防護性能に優れる. Shipcracker's variant ends "で,衝撃分散性能が向上しています." for its "improved impact dispersion". |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | 第10世代のウォーキャスケットは,実は鹵獲した宙賊の装備を改造したもので,... | Translated, no pack; the full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/Japanese/`. 宙賊 is Core `Pirate.label`; "dreadnoughts" is 弩級の兵器. |
| pilot (the wearer) | パイロット | Odyssey `PilotAssistant` (パイロットアシスタント); Shipcracker's prose. |
| spacer components / shield bubble (what a spacer-tier set carries) | 先進コンポーネント / シールドバブル | Core `ComponentSpacer.label`; Biotech `Mech_Centurion.description`. No rendering recorded for "spacer armor and insulation". |

Pending native review for the whole family: ショルダーアーマー and the
resulting label length, ウォーキャスケット鋳造台 (foundry) and 封入 (entomb),
both unattested, the coined set names (all but カタフラクト), 特殊な for
"specialized", 標準的な防護性能 for "standard protection" and the
10th-generation paragraph's phrasing (no community VFEP rendering exists).
If a community VFEP translation surfaces, align these and the set names to
it. The set-specific coinages each repo lists stay pending there.

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

- Core Keyed `ModSettings` is `Mod 設定` (with a space) while `ModOptions`
  is `MODオプション`: the bare-word MOD rule has that one exception
  (2026-10-13, Toxin Warcasket).
- ja Keyed never switches on `CHARGENOUN_gender`, so no `WordInfo/Gender`
  file is ever needed.
- The ja tree carries an untranslated `ToxicFallout.label` ("toxic fallout",
  a different def type) beside the real `死の灰`, so a bare grep returns
  both; pick by def type.
- **Map distance: セル in def stats, タイル in the family captions** (Medic
  Warcasket's register read, 2026-11-05): vanilla's def stats measure map
  distance in セル (`ShootingAccuracyFactor_*` 40セル / 25セル,
  `PackRadius.formatString` {0}セル; 11 hits), while タイル appears in Keyed
  `RoomRequirementArea` and in a world-tile string (2 hits). The family's
  `範囲 (タイル)` caption stands until a native review rules; a pass writing
  a def stat description should use セル.

## Generated-text tells

Catalogued 2026-11-05 by Medic Warcasket's first ja pass, from the Core and
Odyssey `Japanese (日本語).tar` values with comments stripped (26,843 values,
827k characters). Rates are per 100k characters of description and tooltip
values with backstories excluded (3,178 values, 163k characters, 6,013
sentences averaging 26.8 characters and 0.68 commas) unless noted. Each item
is the `English.md` § 2 category as it shows up in Japanese, with the vanilla
evidence. Mirrored strings are exempt; descriptions, settings tooltips and
Workshop prose are the slots to read.

1. **One frame on every tooltip.** Vanilla tooltips open on the thing and
   close on a noun plus `です.` (`PainShockThreshold` 痛みによって失神する値です.,
   `InjuryHealingFactor` 傷の治る速度に適用される掛け率です.), so a definition
   ending `〜時間です.` is native. The tell is the same definition plus the
   same consequence sentence on every row, or every sentence of a paragraph
   ending on the same verb: vanilla's sentence ends spread over します (654),
   ります (534), います (525), ません (376) and きます (319).
2. **かどうか openers.** The "Whether" calque is `〜かどうかを設定します`:
   3 hits in the whole corpus (`CommandToggleAllowAutoRefuelDesc`), 23
   `かどうか` in all. Vanilla toggles state the effect,
   `有効にすると,…ようになります.無効にすると,….` (`RespectSystemScaling_Tooltip`,
   `SmoothCameraJumpsDesc`; 有効にすると 7, 無効にすると 10, with オンにすると 5 /
   オフにすると 3 on map gizmos such as `CommandAutoRearmDesc`). The
   warcasket family ships 有効にすると / 無効にすると.
3. **Telegraphese.** Descriptions and tooltips are polite です/ます (です. 1,015,
   ます. 1,573); plain である (22.6) and だ. (66.1) live in thoughts and
   backstories. A tooltip sentence cut to a noun stop (体言止め) or a plain
   form reads as a spec sheet; only labels, gizmo labels, floating texts and
   `reportString`s drop the verb and the period. The opposite tell is the
   stiff `〜することができます` on every sentence: vanilla says it 124 times
   against 163 bare `できます`, so vary it.
4. **Chained clauses and aphoristic closers.** The Japanese tricolon is a
   sentence chaining three `〜し,` / `〜て,` clauses, or a list closed by
   `そして` (34.9; vanilla lists join with `,` and と / や). Only 106 of 6,013
   vanilla sentences run past 60 characters with two or more commas; split
   one that does. The closer is a `〜こそ` (1.8), `まさに` (3.1), `真の` (1.8)
   or `〜と言えるでしょう` (0.6) line; vanilla ends on a plain statement of use.
5. **Sentence-initial participles.** The "-ing," opener comes out as
   `〜しながら,` (0.6 in descriptions; its 71 corpus hits are battle logs and
   backstories) or `〜することで,` (22.6) hung on a short abstract subject.
   Native openers are conditions and causes: `〜と,` (108), `〜ため,` (54.5),
   `〜ば,` (41), `〜とき` (41.6), `〜場合,` (34.3).
6. **Coinages and possessive chains.** English possessives and hyphen
   compounds come out as `AのBのCの` runs (71 per 100k for three の inside
   eight characters each) or as a long relative clause split from its head
   noun by a comma (`…送り込む,メカナイト処置装置`), which vanilla never does:
   it keeps the modifier tight or gives it its own sentence. Katakana
   modifier plus katakana compound takes `・` (187 tree-wide). Two `を` in one
   clause (`装備を…アーマーを中心に`) is an English object order; reflow it.
7. **Semicolons, dashes and asides.** Descriptions carry 3.1 `;` and 2.4
   em dashes per 100k, mostly one rule-pack idiom; no en dash, no `―`, no
   `。` `、` `？` `！` or full-width space anywhere in the tree. ASCII `(` (42.8)
   is a unit or label qualifier (インフルエンザ(動物)), not an aside. ASCII `.`
   and `,` take no following space (8,129 `.` and 12,136 `,` directly before
   kana or kanji, against 131 and 69 with a space). A `(…)` aside, a dash or
   a `;` in prose is a tell.
8. **Repeated signature phrases.** The same coined phrase (その場で, もう少し
   長く, 頭が鈍り) in the descriptions, ability text, settings and Workshop page.
   Say it once and plainly elsewhere.
9. **Over-explanation.** A tooltip restating what the row's value or a
   vanilla stat already shows. Vanilla tooltips stop after one or two
   sentences.
10. **Modder vocabulary.** `定義` appears once in the whole tree, never about
    game content; `システム` (17.7) only names in-world machinery; `def`,
    `スイート` or `コンプ` never. Name what the player sees: the item's label,
    ゲージ, 「優先順位」タブ, 才能・性格 (Core `Traits`).
11. **Calque: English clause order under Japanese words.**
    - pronouns the English needs and Japanese drops: 彼 / 彼女 run at 7.3 and
      sentence-initial これは / それは at 16.3 / 15.5 per 100k of item
      descriptions; a `その` or `それ` for every English "it" or a `彼らの` for
      "their" is the English skeleton. Vanilla repeats the noun or drops it.
      "Your" is あなたの sparingly (14.1, mostly letters), or nothing;
    - an abstract agent doing a person's verb (`計画は…に気づきました` for "the
      program found"); vanilla goes agentless (`〜ことが分かりました`) or gives
      the verb to people;
    - English "has" kept as `〜を持っています` (28 corpus hits) where vanilla
      says `〜があります` (219) or `〜を備えています` / `〜を搭載しています`;
    - `たち` / `達` on every plural count noun (兵士たち, 入植者たち): vanilla
      marks plurality on people only where it matters, and a number or
      全員 already does;
    - a head-final sentence rebuilt in English order, the main clause first
      and a `〜ため` or `〜ので` reason trailing after it: vanilla puts the
      reason first (`〜ため,…`, 54.5).
