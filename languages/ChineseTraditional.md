# Traditional Chinese — RimWorld localization mechanics

First grounded by Unique Melee Weapons' (UMW) 2026-08-19 machine-assisted
generation pass, mined from the official zh-Hant tars (Core + Royalty +
Odyssey). **No entry below has had native-speaker review.** RimWorld's
language folder is `ChineseTraditional` (tar: `ChineseTraditional
(繁體中文).tar`) — the same cut-at-`(` folder-name resolution verified for
zh-Hans/ja applies.

## Not a script conversion of Simplified Chinese

The two Chinese localizations are independent translations with different
terminology, and several mappings are exactly inverted — porting a zh-Hans
term (or converting its characters) silently produces wrong zh-Hant. Attested
inversions from the 2026-08-19 pass:

| English | zh-Hans official | zh-Hant official |
|---|---|---|
| unique weapon | 特化武器 (独特武器 forbidden) | 獨特武器 (Odyssey `UniqueWeapon`) |
| plasteel | 玻璃钢 (塑钢 forbidden) | 塑鋼 (Core `Plasteel.label`) |
| mace | 钉头锤 | 錘子 (Core `MeleeWeapon_Mace.label`) |
| knife | 匕首 | 小刀 (Core `MeleeWeapon_Knife.label`) |
| quality tiers | 极差/较差/一般/良好/极佳/大师级/传奇级 | 糟糕/劣質/普通/良好/傑出/大師/傳奇 (`QualityCategory_*`) |
| caravan | 远行队 (商队 forbidden) | 旅隊 (Core `Caravan`) |
| quoting injected labels | curly "{0}" | corner 「{0}」 (see style) |

Always re-ground every term against the zh-Hant tars even when the zh-Hans
table already has an answer.

## Engine mechanics (LanguageWorker)

- **No `LanguageWorker_ChineseTraditional` type exists** (typedef enumeration
  of Assembly-CSharp, 2026-08-19 — the full `LanguageWorker_*` list has no
  Chinese entry of either script), and the zh-Hant `LanguageInfo.xml` declares
  no `languageWorkerClass`, so the base worker runs and only merges repeated
  spaces. Same situation as Japanese: no authoring requirements, no help.
  (This also corrects the zh-Hans file's earlier phrasing that implied a
  `LanguageWorker_ChineseSimplified` type existed and merely did nothing —
  neither Chinese worker type exists at all.)
- zh-Hant translation difficulty is entirely terminology and register, never
  engine mechanics.

## Style and corpus findings (measured 2026-08-19 over Core+Royalty+Odyssey values, comments stripped)

- **Quoting uses corner brackets 「」, not curly quotes** — 310 「 vs 4 “
  across the three tars, including directly before placeholders (47 hits of
  「{…): injected labels, cited named entities (心靈連結, research names), and
  clicked UI commands (選擇「內容...」) all take 「」. The zh-Hans two-style
  split (curly for placeholders, corner for UI commands) does NOT carry over;
  zh-Hant uses 「」 for both slots.
- Full-width punctuation in prose（，。、；：（）……）; descriptions end 。;
  labels/buttons take no trailing period.
- **Terse label:value templates use full-width ：, not ASCII `: `** — vanilla:
  等級：{0}, 年齡：{0}, 種植：{0}, 查看任務：{0}, 冷卻期使用成本：{HONOR}.
  This is the OPPOSITE of zh-Hans (whose vanilla writes 品质: {0} with an
  ASCII colon); zh-Hant's own `QualityIs` is 品質{0}, colon-free. Another
  slot-rule inversion between the two Chinese localizations.
- **ASCII spaces around embedded Latin acronyms**: 內置 EMP 裝置, 被 EMP
  擊昏了, EMP 抗性 — zh-Hans sets EMP solid, zh-Hant spaces it. Digits still
  attach directly (移動速度增加15%).
- Dash baseline: **13.35 per 100k value-chars** (the no-new-dashes density
  test's 1x reference for zh-Hant).
- Taiwan lexical register: 設定 not 設置, 預設值 not 默認值, 資訊 not 信息,
  品質 not 質量, 傭兵 not 僱傭兵, 鴉片 not 阿片.
- Vanilla zh-Hant is visibly incomplete in places — Odyssey ships empty
  `rulesStrings` for the `OpportunitySite_*` quest rules and untranslated
  English lines elsewhere. Incompleteness is not style guidance.

## Grounded common vocabulary (Core/Royalty/Odyssey, 2026-08-19)

| English | Use | Why |
|---|---|---|
| quality tiers | 糟糕/劣質/普通/良好/傑出/大師/傳奇 | Core `QualityCategory_*` |
| quality (noun) | 品質 | Core `Quality` |
| unique weapon | 獨特武器 | Odyssey `UniqueWeapon` |
| weapon trait | 特質 in stats slots (`Stat_ThingUniqueWeaponTrait_Label`=特質, `StatsReport_WeaponTraits`=武器特質); Keyed `WeaponTraits`=特性 — vanilla is inconsistent, prefer the nearer slot's form | Odyssey Keyed |
| longsword/spear/mace/knife/gladius/axe/warhammer | 長劍/長矛/錘子/小刀/短劍/戰斧/戰錘 | Core/Odyssey/Royalty `MeleeWeapon_*.label` |
| monosword / plasmasword / zeushammer | 單分子劍 / 等離子劍 / 宙斯錘 (prose plasma=電漿, EMP kept spaced) | Royalty labels/descriptions |
| weapon tool labels | 劍柄/劍尖/劍鋒/劍刃/矛柄/刃尖/錘柄/錘頭/刀柄/刀身/刀尖/斧柄/斧刃/握柄 | Core/Royalty `tools.*.label` |
| steel/plasteel/wood/silver/gold/jade/uranium | 鋼鐵/塑鋼/木頭/白銀/黃金/翡翠/鈾 | Core labels |
| stun (DamageDef) / stunned by EMP | 昏迷 / 被 EMP 擊昏了 | Core `Stun.label`, `StunnedByEMP` |
| burn | 燒傷 (deathMessage {0}被燒死了。) | Core `Burn` |
| bleeding rate | 出血率 | Core `BleedingRate` |
| dodge | 閃避 | Core `TextMote_Dodge` |
| melee (skill) / melee weapon / melee hit chance | 格鬥 / 近戰武器 / 近戰命中率 | Core `Melee.skillLabel`, `MeleeHitChance` |
| wielder (stat context) / holder (flavour prose) | 使用者 / 持有者 | Royalty `SpeedBoost` / `OnKill_*` descs |
| trader; "Traders will pay more for it." | 商人；商人會為其支付更多錢。 | Odyssey `GoldInlay.description` verbatim |
| mercenary | 傭兵 | Core backstories |
| bandit camp / item stash | 土匪營地 / 物品藏匿點 | Core sites |
| rough tribe / tribal chief / tribesfolk | 狂野部落 / 酋長 / 部落民 | Core `TribeRough` |
| leader (hidden-faction `leaderTitle`) | 首領 | Core `Ancients.leaderTitle` |
| {0} from {1} are attacking your {2}. | 來自{1}的{0}正在攻擊你的{2}。 | Core `TribeRough.messageDefendersAttacking` verbatim |
| caravan / quest | 旅隊 / 任務 | Core `Caravan`, `Quest` |
| Quest failed/expired: [resolvedQuestName] | 任務失效：[resolvedQuestName] | Core `OpportunitySite_ItemStash` letters |
| mechanoid | 機械族 | Core |
| market value | stat label `MarketValue`=基本價值, tooltip `MarketValueTip`=市場價格 — slot-dependent | Core Keyed |
| Cancel / Confirm / Randomize | 取消 / 確定 / 隨機生成 | Core Keyed |
| reset to defaults | 恢復為預設值 (`RestoreToDefaultSettings`); 回復所有設定為預設值 (`RestoreToDefaultSettingsLabel`) | Core Keyed |
| buildup (toxic etc.) | 累積 (hediff label itself is plain 中毒; prose 毒性累積) | Core `ToxicBuildup` — corpus 累積:積累:積聚 = 12:1:0 |
| ancient (attributive) | 遠古, not 古代 (416:38 in corpus; 古代遺民 is the Ancients *faction* label) | Core/Odyssey |
| ancient (sealed) crate | 密封板條箱 | Odyssey `AncientSealedCrate.label` |
| EMP pulser | EMP 脈衝器 | Odyssey `EMPPulser.label` |
| persona weapon (bladelink) | 羈絆武器 | Royalty trait descs, `place_personalWeapon` |
| Odyssey / Royalty (DLC names) | 「漫遊」/「皇權」 (《…》 for the soundtrack product names) | Core Keyed `SimulateNotOwningRoyalty`, `BuySoundtrack_*` |
| unconscious | 失去意識 | Core `Anesthetic.description` |

Composition note for quest prose: vanilla renders "[discoveryMethod] the
location of X" as `[discoveryMethod][X]的位置。` with **no 了**, but
"[discoveryMethod] an ancient complex…" as `[discoveryMethod]了一座…` — pick
by the English shape, not by preference.

## RulePackDef / name-generation grammar

Official zh-Hant `NamerUniqueWeapon` (Odyssey
`RulePacks_Namers_UniqueWeapons.xml`) is the reference for any weapon-naming
mod:

- Symbols compose with **no spaces**: `[weapon_adjective][weapon_noun]`.
- "The X of Y" → `[Y]之[X]`; person possessives take 的
  (`[ANYPAWN_nameIndef]的[weapon_noun]`); English "The" is dropped.
- Vanilla's own `badass_adjective`-family entries each **end in 之**
  (嚴酷之/永恆之/黑夜之/送葬之/雷鳴之…), so they read as epithets in both
  the [adj][noun] and standalone slots.
- **`traitAdjectives`-style fields stay bare attributive words with no
  trailing 之 or 的** (official Odyssey traits: GoldInlay→黃金/金,
  Ugly→怪異/粗糙/醜陋, Cumbersome→笨拙/笨重/不便) — they must read directly
  prefixed to a weapon noun (黃金長劍).
