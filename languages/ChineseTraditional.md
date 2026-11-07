# Traditional Chinese — RimWorld localization mechanics

First grounded by Unique Melee Weapons' (UMW) 2026-08-19 machine-assisted
generation pass, mined from the official zh-Hant tars (Core + Royalty +
Odyssey), and extended by Better Traders Guild's 2026-08-22 pass over the
orbital/trade half of Odyssey and Persona Weapons Unbound's 2026-08-22 pass
over the persona-weapon and crafting half of Royalty. **No entry below has
had native-speaker review.** RimWorld's language folder is `ChineseTraditional` (tar:
`ChineseTraditional (繁體中文).tar`) — the same cut-at-`(` folder-name
resolution verified for zh-Hans/ja applies.

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
| traders guild | 商会 | 商人公會 (Odyssey `TradersGuild.label`) |
| shuttle | 穿梭机 | 太空梭 (Odyssey `PassengerShuttle.label`) |
| sentry drone | 哨兵无人机 | 哨衛無人機 (Odyssey `Drone_Sentry.label`) |
| leader (crew `leaderTitle`) | 领袖 | 領導者 (Odyssey `GravshipCrew`) |
| parentheses | full-width （） | ASCII () (528:0, see style) |
| JobDef reportString | ends with 。 | no trailing 。 (see style) |
| persona weapon label form | Δ' prefix: Δ'单分子剑 | `(羈絆武器)` suffix: 單分子劍(羈絆武器) |
| techprint | 科研蓝图 | 科技藍圖 (Core `ResearchTechprintRequirement`) |
| stopping power | 抑止能力 | 攔截力 (Core `StoppingPower`) |
| burst count | 连射次数 | 連發次數 (Core `BurstShotCount`) |
| Crafting (skill) | 制作 | 手工 (Core `Crafting.skillLabel`) |
| charge weapons | 电荷- (电荷步枪) | 電能- (Core `Gun_ChargeRifle`=電能步槍) |
| flare | 照明弹 | 閃焰彈 (Anomaly `DisruptorFlare`=干擾閃焰彈) |
| ultratech / archotech (tech levels) | 极致科技 / 超凡科技 | 高科技 / 遠古科技 (Core `TechLevel_Ultra`, `TechLevel_Archotech`) |
| fabrication (research/bench) | 精密装配 | 精密製作 (Core `Fabrication`, `FabricationBench`) |

Always re-ground every term against the zh-Hant tars even when the zh-Hans
table already has an answer — the 2026-08-22 BTG pass found six further
inversions in one mod's surface alone, three of them punctuation rules rather
than words, which a character-conversion pass cannot catch at all, and PWU's
zh-Hant pass the same day added the last five above out of Royalty's half of
the corpus. Two of those five are that mod's own central vocabulary
(techprint, the persona-weapon label form), so a converted zh-Hans tree would
have been wrong in its most-repeated strings.

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
  zh-Hant uses 「」 for both slots. **The rule holds per DLC, so a lone curly
  pair is a vanilla slip, not a local convention** (measured 2026-08-22):
  Odyssey on its own runs 35 「 against 1 “ in 89k value-chars, and that
  single “ is `TheGravship.scenario.parts.GameStartDialog.text`'s
  選擇“查看星球”. When reusing a vanilla string that contains the outlier,
  translate the quote to 「」 rather than inheriting it.
- Full-width punctuation in prose（，。、；：……）; descriptions end 。;
  labels/buttons take no trailing period.
- **Parentheses are the exception: ASCII `( )`, never full-width `（ ）`**
  (measured 2026-08-22, correcting this file's earlier blanket
  full-width-punctuation claim) — 528 `(` against **0** `（` across
  Core+Odyssey values, set solid with no surrounding space:
  客運太空梭(正在到達), 殖民地財富(此區域), 目前的友好度：{4}({5})。 This is
  another inversion from zh-Hans, whose vanilla writes （原版）-style
  full-width parens, so converting a zh-Hans string's punctuation produces
  wrong zh-Hant. The colon in the very same slot stays full-width ： — the
  two marks disagree, so never generalize one to the other.
- **Terse label:value templates use full-width ：, not ASCII `: `** — vanilla:
  等級：{0}, 年齡：{0}, 種植：{0}, 查看任務：{0}, 冷卻期使用成本：{HONOR}.
  This is the OPPOSITE of zh-Hans (whose vanilla writes 品质: {0} with an
  ASCII colon); zh-Hant's own `QualityIs` is 品質{0}, colon-free. Another
  slot-rule inversion between the two Chinese localizations.
- **ASCII spaces around embedded Latin acronyms**: 內置 EMP 裝置, 被 EMP
  擊昏了, EMP 抗性 — zh-Hans sets EMP solid, zh-Hant spaces it. Digits still
  attach directly (移動速度增加15%).
  **This spacing is not only cosmetic — it changes tokenization.** Any mod
  feature that splits a label on spaces (UniqueWeaponsUnbound's
  `TraitCostRuleDef.labelKeywords` matcher, for one) sees zh-Hant `EMP 子彈` as
  `{emp, 子彈}` and therefore still matches an English `emp` keyword, while the
  zh-Hans solid `EMP子弹` is one opaque token. Check the spacing before assuming
  a localized label needs a localized keyword.
- **JobDef `reportString`s carry NO trailing 。** (verified 2026-08-22 over
  every Core+Odyssey `reportString`): 清理TargetA, 破解TargetA, 救援TargetA,
  治療TargetA, 給TargetB餵食TargetA, and intransitive ones take 中 instead
  (覓食中, 巡邏中, 引爆中). English sources all end in a period and zh-Hans
  vanilla keeps it, so this is a third slot-rule inversion between the two
  Chinese localizations. SitePartDef `approachOrderString` /
  `approachingReportString` are likewise bare (Odyssey: 調查{0} for both).
- **RecipeDef `jobString` is bare too, and is byte-identical to the recipe's
  own `label`** (verified 2026-08-22 over Core's RecipeDef tree during PWU's
  pass): `Make_ComponentSpacer` renders BOTH `.label` and `.jobString` as
  製作高級零件, while its `.description` in the same file keeps 製作高級零件。
  Same across 製作麥汁, 製作乾肉餅, 安裝仿生手臂, 移植心臟. English gives the
  three fields three distinct forms (`make X` / `Making X.` / a sentence), so
  the natural instinct to differentiate them in translation is wrong here —
  translate label and jobString once and reuse, and keep 。 only on the
  description. The transitive/intransitive 中 split above applies to
  jobStrings as well.
- Dash baseline: **13.35 per 100k value-chars** (the no-new-dashes density
  test's 1x reference for zh-Hant). Split by DLC it is Core 10.6 and Odyssey
  34.8, the latter almost entirely `——` mirroring an English `-` in the same
  slot (小心——軌道位置極為危險) — mirroring is allowed, but a mod's own tree is
  small enough that one `——` pair alone can blow past the 1x line, so reflow
  into ，or 、unless the source dash is structurally load-bearing.
- Taiwan lexical register: 設定 not 設置, 預設值 not 默認值, 資訊 not 信息,
  品質 not 質量, 傭兵 not 僱傭兵, 鴉片 not 阿片, 機率 not 概率, 倖存 not 幸存
  (Core backstories: 唯一倖存者, 倖存的孩子).
- Latin acronyms do NOT all take the EMP spacing: **`AI` is set solid** in
  vanilla values (Core `ChooseAIStoryteller` = 選擇AI故事敘述者), while EMP is
  spaced. Look each acronym up in the corpus rather than applying the EMP rule
  across the board.
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
| spacer-tech (attributive) | 太空科技 | Core `Synthread.description`; VFEP's "specialized spacer-tech" is 特化型太空科技 (the 太空 of `TechLevel_Spacer`, tech levels row above) |
| Imperial (adj.) | 帝國 | Royalty cataphract descriptions (帝國的甲冑騎士); the faction itself is 破碎帝國 (Empire row below) |
| respirator | 呼吸器 | Odyssey rulestrings (組裝呼吸器) |
| Default: {0}. / (default) / Off / On (settings) | 預設值：{0}。 / (預設) / 關閉 / 開啟 | Core Keyed `Default` 預設, `Off` 關閉, `On` 開啟; 預設值 per the Taiwan register list above; the fullwidth colon is the label:value shape (Shipcracker and Toxin Warcasket, shipped) |
| requires Odyssey (settings suffix) | (需要「漫遊」DLC) | Core `SimulateNotOwning*` 「漫遊」DLC (the DLC brand names row above). ASCII parens set solid, so the suffix drops the English leading space |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | 使用能力：{0} | VEF ships English only; fullwidth-colon label shape like vanilla's 查看任務：{0}, no trailing period (Shipcracker Warcasket, shipped since its first pass; Toxin Warcasket the same) |
| on cooldown (a reloadable comp's `cooldownGerund`) | 冷卻 | Vanilla's default for `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker and Toxin Warcasket) |
| tank (an armor's fuel tank, settings) | 燃料箱 | Odyssey `FuelStorage.label` 燃料箱 (Core Keyed 燃料槽 is the fueling port) |

Composition note for quest prose: vanilla renders "[discoveryMethod] the
location of X" as `[discoveryMethod][X]的位置。` with **no 了**, but
"[discoveryMethod] an ancient complex…" as `[discoveryMethod]了一座…` — pick
by the English shape, not by preference.

## Grounded common vocabulary, orbital / trade domain (Core+Odyssey, 2026-08-22)

Mined during Better Traders Guild's pass; the space-and-trade half of Odyssey
that the melee-weapon pass never touched. The last two rows are Biotech, kept
here because BTG reaches them through a gated compat root rather than because
Biotech is anyone's domain DLC.

| English | Use | Why |
|---|---|---|
| traders guild | 商人公會 (member 公會成員, `leaderTitle` 貿易長官) | Odyssey `TradersGuild.*` — zh-Hans's 商会 is NOT the zh-Hant form |
| salvagers | 打撈者 (`pawnSingular` 海盜, elite 打撈者精英) | Odyssey `Salvagers.*` |
| orbital trader / trade / trade request | 軌道商人 / 貿易 / 交易請求 | Odyssey `TradersGuild.description`, Core `TradeRequestWarning` |
| settlement / orbital settlement | 據點 / 軌道據點 | Odyssey `SpaceSettlement.label` |
| orbital platform / relay / outpost | 軌道平台 / 中繼站 / 前哨站 | Odyssey `OrbitalAncientPlatform`, Core `camp->前哨站` |
| shuttle | 太空梭 (passenger shuttle 客運太空梭, engine 太空梭引擎) | Odyssey `PassengerShuttle.label` — not 穿梭機 |
| gravship / gravcore / gravlite panel / pilot console | 重力船 / 重力核心 / 重力板 / 駕駛控制台 | Odyssey labels |
| mechhive | 機械巢穴 (機巢 appears once; prefer the label form) | Odyssey `Mechhive.label` |
| signal jammer | 信號干擾器 | Odyssey `SpaceSettlement.description` |
| sentry drone | 哨衛無人機 | Odyssey `Drone_Sentry.label` — NOT 哨兵, which zh-Hans uses |
| life support unit | 生命維持單位 | Odyssey `LifeSupportUnit.label` |
| hack (verb, all slots) | 破解 (`Hack.reportString` 破解TargetA; 破解以開啟。) | Core JobDef + Odyssey `CompHackable` strings |
| vacuum / vacsuit / vac barrier | 真空 / 真空服 / 真空屏障 | Odyssey Keyed + `VacBarrier` |
| transport pod / cargo pod | 運輸艙 (also 運輸莢艙) / 貨艙 | Odyssey descs, Core `LetterLabelCargoPodCrash` |
| comms console / survival meal | 通訊台 / 生存食品包 | Core `CommsConsole.label`, `MealSurvivalPack.label` |
| turret / raider / intruder / downed | 砲塔 / 襲擊者 / 入侵者 / 倒地 | Core Keyed + `PainShockThreshold.description` |
| garrison / reinforcements | 駐軍 / 增援部隊 (援軍 for ally aid) | Odyssey `OpportunitySite_AncientGarrison.label` 遠古駐軍地 |
| faction / goodwill | 派系 (ScenPart `PlayerFaction.label` uses 陣營) / 友好度 | Core Keyed |
| negotiator | 會談代表 | Core `Negotiator` |
| storyteller / scenario / inventory | 故事敘述者 / 腳本 / 庫存 | Core Keyed |
| wealth / difficulty / black market | 財富 / 難度 / 黑市 | Core Keyed + backstories |
| leader (crew-scale `leaderTitle`) | 領導者 | Odyssey `GravshipCrew.leaderTitle` (Core's hidden-faction 首領 is a different slot) |
| starting people (ScenPart) / arrival method | 起始人口數 / 抵達方式 | Core `ConfigPage_ConfigureStartingPawns`, `PlayerPawnsArriveMethod` |
| color / apparel | 顏色 / 服裝 | Core Keyed `Color`, `ApparelPolicyTip` |
| xenotype | 異種人 | Biotech Keyed `CreateXenotype` |
| paramedic / cleansweeper / agrihand mech | 醫療者 / 清潔者 / 務農者 | Biotech `Mech_*.label` |
| ColorDef naming | material names take a 色 suffix: 花崗岩色, 砂岩色, 金色 | Core/Odyssey ColorDefs |

Quest-letter reuse: Core `TradeRequest`'s four zh-Hant slateRefs
(任務失敗：[resolvedQuestName], [faction_name]開始敵視你。, the two royal-favor
ones) are byte-identical-English and reusable by any mod copying that quest
shape. Note Core's own 誰應該作為[…]以完成此次交易任務？ is a loose reading of
"Who should be credited with"; reuse it anyway so one English string does not
get two renderings.

## Grounded common vocabulary, persona-weapon / crafting domain (Core+Royalty, 2026-08-22)

Mined during Persona Weapons Unbound's pass; the Royalty half of the corpus
that the melee-weapon and orbital/trade passes never reached. Where a row
disagrees with the zh-Hans file, the zh-Hant form here is the attested one —
see the inversion table above.

| English | Use | Why |
|---|---|---|
| persona weapon / bladelink weapon | 羈絆武器 | Royalty `MeleeWeapon_*Bladelink.label` renders English `persona monosword` as 單分子劍(羈絆武器); also prose (`LetterBladelinkWeaponBondedLabel`). Unlike zh-Hans, zh-Hant HAS a standalone term — no coinage needed |
| persona (the onboard mind, prose) | 人格 (AI人格 in the weapon descriptions, AI set solid) | Royalty `NeverBond.description` 這把武器的人格; weapon descs 這件武器自身具備AI人格 |
| persona weapon trait (stat) | 特性 | Royalty `Stat_Thing_PersonaWeaponTrait_Label`, Core Keyed `Traits`, `BladelinkEquipWarningTraits` — **diverges from Odyssey's 特質** (`Stat_ThingUniqueWeaponTrait_Label`), so pick by the mod's domain DLC. zh-Hans has no such split |
| freewielder (trait label) | 自由 | Royalty `NeverBond.label` — quote as 「自由」特性 when naming it |
| bond (verb/state) / the bond (noun) | 綁定 / 羈絆 | Royalty `BladelinkAlreadyBonded*`, `LetterBladelinkWeaponBonded` |
| persona core | 人格核心 | Core `AIPersonaCore.label` |
| techprint | 科技藍圖 | Core `ResearchTechprintRequirement` — NOT zh-Hans's 科研蓝图 |
| fabrication bench / advanced fabrication | 精密製作桌 / 高級精密製作 | Core `FabricationBench.label`, `AdvancedFabrication.label` |
| advanced component | 高級零件 | Core `ComponentSpacer.label` |
| bill (workbench order) | 工作 (add-bill menu 新增工作) | Core `AddBill`; 訂單 is already spent on `Quest_TradeRequest` 訂單任務, so it is the wrong slot |
| customize (verb + UI command) | 自訂 | Core Keyed `Customize`; `CustomizeIdeoligion` 自訂理念 |
| appearance | 外觀 | Core Keyed `Appearance`; 紋理 is reserved for `TextureCompression` (graphics settings), so do not spend it on a weapon-texture feature |
| Crafting (skill) | 手工 | Core `Crafting.skillLabel` — 製作 is the verb, never the skill name |
| stopping power / burst count / burst speed | 攔截力 / 連發次數 / 射速 | Core `StoppingPower`, `BurstShotCount`, `BurstShotFireRate` |
| Empire (faction) | 破碎帝國 | Royalty `Empire.label` |
| relic / ideoligion | 聖物 / 理念 | Ideology `IdeoRelic`, `CustomizeIdeoligion` |
| machine persuasion (research) | 機械核心 | Core `ShipComputerCore.label` — bears no resemblance to the English label OR to zh-Hans's 飞船电脑核心. A worked case for resolving a translator-comment hint through the tar by defName, never by its English wording |
| DLC brand names | 「皇權」/「漫遊」/「理念」 | Core `SimulateNotOwning*` — zh-Hant localizes them, in corner brackets, as zh-Hans does (most other languages keep English) |

## Grounded common vocabulary, crafting / cost / settings-UI domain (Core+Odyssey+Ideology, 2026-08-26)

Mined during Unique Weapons Unbound's pass: the workbench-and-economy half of
Core plus the settings-dialog register no earlier pass needed. Rows that
disagree with the persona-weapon table above are noted inline.

| English | Use | Why |
|---|---|---|
| workbench (generic) | 工作桌 | Every vanilla bench *description* says 工作桌 (`ElectricSmithy`, `FueledSmithy`, `TableMachining`, `FabricationBench`, `Brewery`, `DrugLab`); 工作台 (12 hits) appears only in generic help prose such as `BillsTab.helpText`, so the bench descriptions are the nearer analog for anything naming a specific bench |
| smithy / machining table | 燃料鍛造桌・電力鍛造桌 / 機械加工桌 | Core `FueledSmithy`, `ElectricSmithy`, `TableMachining` labels |
| Smithing / Machining / Fabrication (research) | 鍛造 / 機械加工 / 精密製作 | Core research labels — note 精密製作, NOT zh-Hans's 精密装配 |
| pulse-charged munitions (`ChargedShot`) | 高能電磁 | Core `ChargedShot.label` — bears no resemblance to the English label; resolve it by defName, never by its English wording |
| beam (weapons) | 光束 | Odyssey `Gun_BeamRepeater`=光束連發槍 |
| charge (the *act* of charging, vs the weapon class) | 充能 (weapon class is 電能-) | Odyssey `ChargeCapacitor`=充能電容, `PulseCharger`=脈衝充能器 vs Core `Gun_ChargeRifle`=電能步槍 — two different words for one English root, so pick by slot |
| tech levels | 原始部落 / 中世紀 / 工業 / 太空 / 高科技 / 遠古科技 | Core `TechLevel_Neolithic`…`_Archotech` |
| components / advanced components | 零件 / 高級零件 | Core `ComponentIndustrial`, `ComponentSpacer` — 零件 is also the generic "part", so 部件 (51 hits) is the word for a physical part in prose, 元件 (8) is rare |
| chemfuel / herbal medicine / thrumbofur / birdskin | 化合燃料 / 草藥 / 獨角獸皮 / 鳥皮 | Core labels |
| steel slag chunk / bioferrite / hemogen pack | 金屬碎片 / 生化鐵氧體 / 血原包 | Core `ChunkSlagSteel`, Anomaly `Bioferrite`, Biotech `HemogenPack` |
| ingredients / stuff | 材料 / 素材 | Core `Ingredients`=材料 and `Stat_Stuff_Name`=材料 collide, so when a string must distinguish them use 素材 for stuff (`FabricationBench.description` 將簡易素材製作成科技結晶) |
| cost | 成本 (an economic cost) / 花費 (a price paid) | Core `Difficulty_MaintenanceCostFactor_Label`=砲塔整備成本 vs `RequestTrader`=請求交易旅隊(花費：{0}友好度). Both attested; pick by slot rather than harmonizing |
| refund | 返還 | Core `Flagstone*.description` 拆除石板路並不會返還資源 — the exact "does not refund resources" slot |
| free (at no cost) | 免費 | Royalty `CommandCallRoyalAidFreeOption` |
| prerequisites | 前置條件 (research 研究前置條件) | Core `Prerequisites`, `ResearchPrerequisites` |
| research project / research window | 研究項目 / 研究視窗 | Core `NeedResearchProject`, `ClickToOpenResearchTab`=點擊打開研究視窗 — **vanilla zh-Hant has no tree metaphor**, so 研究樹 is a coinage, not a translation |
| forbidden / reserved / unreachable / no path | 禁用 / 預留 / 無法接觸 / 沒有路徑 | Core `CommandForbid`, `Reserved`=被預留給其他人。, `CannotReach`, `NoPath` |
| haul / stack | 搬運 / 堆疊 | Core `HaulFromSource`, `OnlyStacksWithCompatibleMeals` |
| accuracy penalty / ignores | 準度懲罰 / 忽略 | Odyssey `AimAssistance.description` 使武器忽略壞天氣和煙霧帶來的準度懲罰 — verbatim, and the nearest analog for any "ignores accuracy penalties" line |
| damage type / extra damage / armor penetration | 傷害類型 / 額外傷害 / 護甲穿透值 | Core `Damage`, `ArmorPenetration`; `DamageType` itself is the formatted {0}傷害 |
| log / palette / menu / right-click / command (gizmo) | 日誌 / 調色盤 / 選單 / 右鍵 / 指令 | Core `LogFileFolder`=日誌資料夾 (記錄 is "to record", a different slot), `StartDevPaletteOn`=開發者調色盤, `BillsTab.helpText`, tips |
| texture | **貼圖 is free to coin** (0 vanilla hits); 紋理 is spent on `TextureCompression`=紋理壓縮 and 材料 on `Stat_Stuff_Name` | Core Keyed |
| none / none (brackets) | 無 / (無) | Core `None`, `NoneBrackets` — the bracket form confirms ASCII parens set solid |
| structure colours (the building-paint palette) | 建築顏色 | Core's `Structure_*` ColorDefs are what `DesignatorPaintBuilding` 粉刷建築 applies; Ideology's Keyed `Structure`=結構 is the *ideoligion*-structure slot and must not be borrowed for it |
| blue (plain colour label) | 藍色 | Core `Structure_Blue.label`; Core Keyed `Blue` is left untranslated English and is not a usable source |
| DLC brand names (full set) | 「皇權」/「理念」/「生機」/「異邪」/「漫遊」 | Core `SimulateNotOwning*` — extends the Royalty/Ideology/Odyssey trio recorded above with Biotech and Anomaly |

## Grounded common vocabulary, Combat Extended domain (CE 16.7.4 shipped zh-Hant + Core, 2026-10-27)

| English | Use | Why |
|---|---|---|
| MPa / mm RHA (Combat Extended units) | 兆帕 / 毫米均質裝甲 | CE 16.7.4 zh-Hant `CE_MPa`/`CE_mmRHA` spell the units out, unlike zh-Hans which keeps MPa/mm RHA; match CE's own info card |
| blunt armor / sharp armor | 防禦 - 鈍擊 / 防禦 - 利刃 | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; CE's `CE_DescBluntPenetration` = 鈍器防護 says 鈍器 where Core's stat says 鈍擊, and Core wins |
| armor penetration | 護甲穿透值 | Core `ArmorPenetration` (see above); CE's `CE_DescArmorPenetration` drops the 值, and Core wins |
| flak vest / flak jacket / frag grenade | 防彈背心 / 防彈夾克 / 手榴彈 | Core labels — verbatim; zh-Hant's frag grenade is plain 手榴彈 |

## Grounded common vocabulary, VFE Pirates warcasket domain (q847633684/Vanilla-Expanded-ZH pack + Core, 2026-10-28)

VFE Pirates ships English only, and the Traditional Chinese pack could not be
read: the Workshop pack "Vanilla Factions Expanded - Pirates - 簡&繁中文漢化包"
(id 2727638702) attests the noun 戰棺 on its page, but its Traditional files
could not be obtained. The zh-Hant renderings are therefore converted from the
zh-Hans pack (GitHub `q847633684/Vanilla-Expanded-ZH`, the `Vanilla Factions
Expanded - Pirates` folder; zh-Hans 战棺 = zh-Hant 戰棺), each term checked
character by character against the zh-Hant Core, Royalty and Odyssey tars
(vocabulary conversion, not a script conversion; see the inversion table
above). Terms marked "derived" are such conversions of the pack's terms. Every
warcasket set in the family (Shipcracker, Toxin, Medic, Overlord) renders
these terms alike so the sets read as one family in-game; a change is made
here first and each set's shipped files follow at its next pass. A set's own
name, its Workshop title and its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket | 戰棺 | Attested on the Workshop pack 2727638702's page; the zh-Hans pack uses 战棺 throughout (`VFEP.RequiresWarcasket`, every set label); the Workshop title anchor. The page's 無畏戰棺 prefix is deliberately not used. |
| `<set>` warcasket / shoulders / helmet (label pattern) | `<set>`型戰棺裝甲 / `<set>`型戰棺護肩 / `<set>`型戰棺頭盔 | Derived from the zh-Hans pack's pattern (`<set>`型战棺装甲 / 护肩 / 头盔). The body piece takes 裝甲 although the English label has no noun, as the pack does. 頭盔 and 裝甲 match vanilla (Core `Apparel_PowerArmorHelmet` 海陸頭盔, 海陸裝甲). |
| pauldrons / shoulder pads | 護肩 | Derived (zh-Hans 护肩, also the foundry UI's `VFEP.Shoulderpads`). No vanilla hit either way. |
| warcasket shell | 外殼 | Core `Shell.label`, Royalty cataphract helmet 防護外殼. Shipcracker ships 戰棺外殼 in its openers, while Toxin ships the pack's 戰棺裝甲 for the same English "shell" (see the 10th-generation opener row). |
| torso piece (Workshop) | 裝甲主體 | Derived from the foundry UI's `VFEP.ArmorFrame` (装甲主体). |
| warcasket foundry | 戰棺鑄造廠 | Derived (zh-Hans 战棺铸造厂); 鑄造廠 is Core `FoundryApprentice76`. |
| warcasket slugthrower | 戰棺霰彈槍 | Derived (zh-Hans `VFEP_WarcasketGun_Slugthrower.label` 战棺霰弹枪); 霰彈槍 matches Core `Gun_PumpShotgun` 泵動霰彈槍. |
| entomb / weld (Workshop) | 封在戰棺內; assembling at the foundry 組裝 | zh-Hans pack's `VFEP.WarcasketText` (封入, 组装) rather than a literal "weld". |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | 「太空戰棺」 / 「特化型戰棺」 | 「太空戰棺」 is cited in Toxin Warcasket's shipped `TXWC_SpacerTierDesc` (Toxin's glossary records Shipcracker's zh-Hant Workshop page as the same); 太空 is Core `TechLevel_Spacer` where the zh-Hans pack writes 太空时代战棺. 「特化型戰棺」 is derived from the pack's `VFEP_SpecialisedWarcaskets.label` 特化型战棺; no shipped file cites it yet. Corner brackets per the Core citation style. |
| VFEP set names | 破襲型 (siegebreaker), 狂怒型 (brute), 聖盾型 (guardian), 空襲型 (aerial), 騎士型 (cataphract), 險境型 (hazard) | Derived from the zh-Hans pack; 騎士型 / 險境型 are the pack's `VFEP_Warcasket_Cataphract.label` 骑士型 and `VFEP_Warcasket_Hazard.label` 险境型 (險境 attested in the zh-Hant tars; Royalty's own cataphract armor is 全覆式裝甲, the set name follows the pack). 空襲型 is coined and shipped in Shipcracker Warcasket's Keyed; the zh-Hans section of its sibling file records the pack's aerial as 突击型, so 空襲型 deviates from the pack's wording (a 突擊型 conversion) and is unverified against the Traditional pack. Controller and sarcophagus: no glossary records the pack's rendering and the pack's files were not available to this pass, so they are unrecorded here; take them from the pack when a set needs them. |
| 7th generation / 10th generation (VFEP's two chassis) | 第七代 / 第十代 | Shipcracker's and Toxin's shipped prose (Toxin 第七代戰棺 and 第十代戰棺), following the pack's paragraphs. |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | 特化型戰棺`<part>`，在增加機體重量的同時大幅提升了防護性。 | zh-Hans pack's Cataphract opener (进阶型→特化型); Toxin Warcasket's shipped `shortDescription`s (戰棺裝甲 / 護肩 / 頭盔). |
| Specialized spacer-tech warcasket shell / pauldrons / helmet (VFEP's 10th-generation opener) | 特化型太空科技戰棺裝甲 / 護肩 / 頭盔 | zh-Hans pack's opening phrase for every 10th-generation part (特化型太空时代级别战棺…), with 太空科技 for the pack's 太空时代级别 (see the spacer-tech row in the main table); 特化型 from the pack's descriptions. Toxin ships 戰棺裝甲 for the shell where Shipcracker ships 戰棺外殼; Medic Warcasket (2026-11-05) ships 戰棺裝甲 too, matching the label pattern's body piece, so the shell slot of this opener is 裝甲 and Shipcracker's 戰棺外殼 follows at its next pass. |
| ... with standard protection (the 10th-generation opener's tail) | ，在不增加機體重量的同時極大幅提升了防護性。 | zh-Hans pack's Siegebreaker / Controller / Sarcophagus openers (在不增加机体重量的同时极大幅提升了防护性), loose for "standard protection" as the pack is; Toxin Warcasket's shipped `TXWC_SpacerShortDescription_*`. Shipcracker's variant ends 強化了衝擊分散性能 for its "improved impact dispersion" (coined, close to the English; the pack's loose rendering was not adopted because it invents a weight claim). |
| 7th-generation paragraph (VFEP's lore paragraph on the 7th-generation chassis) | 由於機體基本性能的強化陷入瓶頸，第七代戰棺的研發重心轉向了創新改進。… | zh-Hans pack's Hazard paragraph, its dash reflowed into ，; 玻璃钢→塑鋼 (zh-Hant Core `Plasteel`); shipped in Toxin Warcasket's descriptions. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | 第十代戰棺有些特殊，它們是用從海盜那裡收繳的設備改造而成的。… | zh-Hans pack's paragraph (repeated on every spacer set; the Siegebreaker, Brute, Guardian, Sarcophagus and Controller descriptions share it), dash reflowed into ，; 兼容性→相容性 (Core `Incompatible` 不相容), 借助→藉助, quotes →「戰棺」. The full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/ChineseTraditional/`. |
| pilot (the wearer) | 駕駛員 | zh-Hant Core/Odyssey `Shuttle.description` (駕駛員的生物特徵); Shipcracker's and Toxin's shipped prose. |
| spacer armor and insulation / shield bubble / spacer components / spacer tier (what a spacer-tier set carries) | 太空級的護甲與隔熱性能 / 一層護盾 / 高級零件 / 太空級 | Toxin Warcasket's shipped `TXWC_SpacerTierDesc`; 護盾 per Core `ShieldBelt.label`, 高級零件 per Core `ComponentSpacer.label` (the advanced component row above). 太空級 is coined (太空 is Core `TechLevel_Spacer`, 級 as in a grade); 隔熱 and 心靈抗性 are coined because the stat labels (隔絕 - 冷/熱) do not read as prose. |

Pending native review for the whole family: every "derived" term above (護肩,
裝甲主體, 戰棺鑄造廠, 破襲型 / 狂怒型 / 聖盾型, 特化型, 騎士型 / 險境型 /
「特化型戰棺」 and the 7th-generation paragraph), converted from the zh-Hans pack
and character-checked against the zh-Hant tars, but the actual Traditional pack
could not be compared; the coined 空襲型, 太空級 and the adopted opener's 極大幅
for "standard protection"; the shell slot (外殼 or 裝甲) in the openers. The
set-specific coinages each repo lists stay pending there.

## Grounded common vocabulary, medical, tending and ability domain (Core, with Royalty and Anomaly where named; Medic Warcasket, 2026-11-05)

| English | Use | Why |
|---|---|---|
| mechanites (healing / drug sense) | 機械分子 | Core `MechSerumHealer`, `MechSerumResurrector`, `Luciferium*` descriptions (19 Core hits, 12 Biotech); 機械蟲 is only the two infection hediffs' descriptions (`FibrousMechanites`, `SensoryMechanites`, whose labels are 肌肉細胞機械化 / 感官細胞機械化). zh-Hans renders both senses 纳米机械, so a converted zh-Hans string gives the wrong word |
| medicine (generic) / herbal / industrial / glitterworld | 藥品 / 草藥 / 醫療包 / 高科技藥品 | Core `ThingCategoryDef` `Medicine.label`, `MedicineHerbal`, `MedicineIndustrial`, `MedicineUltratech`. Industrial medicine's label is 醫療包 ("medical kit"), so any mod noun meaning "kit" or "medkit" must avoid 醫療包; zh-Hans's 医药 has no such collision |
| go-juice / wake-up | 能量果飲 / 醒神劑 | Core `GoJuice.label`, `WakeUp.label` (zh-Hans 活力水 / 清醒丸: not convertible) |
| heart attack | 心臟衰竭 | Core `HeartAttack.label` and `labelNoun` (zh-Hans 心脏病发作: an inversion; stage labels 痛苦 / 衰弱 / 致命) |
| wound infection / missing body part | 傷口感染 / 缺少身體部位 | Core `WoundInfection.label`, `MissingBodyPart.label` |
| tend (job) / tend (Keyed) / tend quality / medical tend quality / medical tend speed | 治療TargetA / 照護{0} / 治療品質 / 醫療品質 / 醫療速度 | Core `TendPatient.reportString`, Keyed `Tend`, `TendQuality`, `MedicalTendQuality.label`, `MedicalTendSpeed.label`; `TendingNotRequired` {0}不需要照護 |
| tended (hediff state) | 已包紮 | Core `*.comps.HediffComp_TendDuration.labelTendedWell` |
| doctor (work type) | 醫護 (label) / 醫生 (labelShort) / 照顧 (verb) / 治療 (gerund) | Core `Doctor.*`; caring work tag 照顧 (`WorkTagCaring`) |
| patient | 患者 | Core `Doctor.description` 幫患者拿食物 |
| manipulation / sight / consciousness | 操作 / 視力 / 意識 | Core capacity labels (操作能力 in prose, `ThrumboRoar.description`) |
| pain / pain shock / unconscious | 疼痛 (Keyed `Pain` 傷痛) / 劇痛休克 / 失去意識 | Core prose, Keyed `PainShock`, `Unconscious` |
| casting time / ability range / ability duration / cooldown | 施放時間 / 距離 / 持續時間 / 冷卻時間 | Core Keyed `AbilityCastingTime`, `Ability_Range.label`, `Ability_Duration.label`, Keyed `CooldownTime`; Keyed `Range` 射程 is the weapon slot |
| enabled / disabled (state words) | 啟用 / 停用 | Core Keyed `Enabled`, `Disabled` |
| Work tab (prose) | 「工作」面板 | Core `WorkTab.helpText` (`WorkTab.label` is 分配工作) |
| combat medic / medic / surgeon / squadmate | 戰地醫護兵 / 醫療兵 / 外科醫生 / 戰友 | Core backstories `CombatMedtech59.title`, `CombatMedic82.title`, `GlitterworldSurgeon15.titleShort`, `OverwatchSniper42.description` |
| adrenaline / injector / inject | 腎上腺素 / 注射器 / 注射{0} | Core `KingOfPirates25`, Royalty `VenomFangs`, Anomaly serum `ingestCommandString`; `X注射` as a hediff noun per Anomaly `MetalbloodInjection` 鐵血注射 |
| Mote (inherited `MoteBase` label) | 塵土 | Core `Mote_*` labels, 52 of 64 |
| colours Blue / Green / Pink | 藍色 / 綠色 / 粉紅色 | Core ColorDefs `Blue`, `Green`, `Pink` (Keyed `Blue` / `Green` are untranslated English) |
| is hostile | {0}是敵對的。 | Core Keyed `ConfirmLandOnHostileFactionBase` |
| x / y counts | {0}/{1}, slash set solid | Core Keyed `MassCarried` 負重：{0}/{1}公斤, `PregnantIconDesc` 懷孕({0}/{1}); the English spaces the slash |

Reload-slot read-aloud for a `chargeNoun` (Core Keyed): `CommandReload_NoCharges`
沒有{CHARGENOUN_plural}。, `Stat_Thing_ReloadChargesRemaining_Name`
{CHARGENOUN_plural}剩餘, `Stat_Thing_ReloadMaxCharges_Desc` 這個物體最多能保持的{CHARGENOUN_plural}數量。,
`Stat_Thing_ReloadPerCharge_Desc` 每裝填一{CHARGENOUN}需要消耗物品的數量。,
`Stat_Thing_ReloadPerCharge_Name` 每{CHARGENOUN}裝填消耗,
`Stat_Thing_ReloadDestroyOnEmpty_Desc` 這個道具會在最後一個{CHARGENOUN}使用完後消失。,
`CommandReload_Cooldown` 需{COOLDOWNGERUND}{TIME}。 (so the family's
`cooldownGerund` 冷卻 reads 需冷卻…), `ChargesRemaining` 剩餘充能. No
`CHARGENOUN_gender` anywhere. The 一{CHARGENOUN} slot takes the noun with no
classifier, which favours a noun that tolerates 一X (Medic ships 藥包 and 針劑).

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

## Pitfalls and lessons

- **A mass-noun charge noun fits every vanilla reload slot; a counted one
  does not** (2026-10-13, Toxin Warcasket): `燃料` reads naturally in
  `沒有燃料。` and `燃料剩餘`, while `單位` would not, so keep the noun a mass
  noun and put the counter in the mod's own strings
  (`需要{COUNT}單位{CHARGENOUN_plural}`).
- Deadlife dust is `死者粉塵` (Core Keyed `DeadlifeDust`, Misc_Gameplay.xml).
- No zh-Hant community VFE Pirates pack is known; the zh-Hans one
  (`q847633684/Vanilla-Expanded-ZH`) is the grounding source, converted to
  this tar's vocabulary (`塑鋼`, not the pack's `玻璃钢`) rather than
  script-converted, per the section above.

## Generated-text tells

Catalogued 2026-11-05 by Medic Warcasket's pass from the zh-Hant Core,
Royalty, Ideology, Biotech, Anomaly and Odyssey tars (values only, comments
stripped; 6026 `description` values, 11608 sentences). The categories are
`English.md` § 2; mirrored vanilla strings are exempt, descriptions, settings
tooltips and Workshop prose are the slots to read. **No entry has had native
review.**

1. **The same sentence frame on every setting.** Vanilla tooltips vary the
   head: stat descriptions open on the subject (此生物…, 此人…, 這個物體…),
   ability descriptions on the verb (發出強力咆哮…, 命令動物…). A Keyed file
   whose every tooltip opens 駕駛員… or ends …的時間。 reads templated; vary the
   head or merge two rows' sentences, and keep 預設值：{0}。 as the only fixed tail.
2. **是否 openers.** The docstring "Whether…" arrives as 是否…: only 7 vanilla
   values open on 是否, all of them yes/no dialog prompts (是否確定要取消訂閱).
   Toggles take 啟用時，…。停用時，…。 (Shipcracker) or Core's 如果禁用此功能，…
   frame, never a 是否 description.
3. **Telegraphese.** Vanilla spends the aspect and modal words: 會 runs 58.6
   per 10k description chars, and consequences are written 會/可以/也會
   (`Apparel_ShieldBelt` 如果被 EMP 衝擊到會無法運作). Bare four-character
   chains with no verb word (藥效消退，疲勞加速) are the clipped-English tell;
   so is dropping 了 on a completed event the English states in the past
   (vanilla 了。 closes 13.4 per 10k).
4. **Balanced tricolons and aphoristic closers.** Vanilla uses 成語 freely
   in single slots (`Tough` 鋼筋鐵骨, `Nimble` 十面埋伏也能安然無恙), so an
   idiom alone is not the tell. The tell is three parallel four-character
   phrases stacked with 、 (only 33 of 6026 vanilla descriptions have one) or a
   closing epigram after the description has said what the thing does
   (…卻是最後一道防線). Vanilla closes item descriptions on use or origin
   (`Apparel_ArmorRecon` 帝國偵查兵、閃耀世界警察常常使用這種裝甲。) and stops.
5. **Sentence-initial participles and fronted frames.** English participle and
   prepositional openers come through as 作為…，/ 隨著…，/ 透過…，/ 憑藉…，;
   vanilla opens with them rarely (作為 18, 隨著 10, 透過 19, 憑藉 3 of 11608
   sentences) and prefers 如果 (142), 雖然 (130), 當 (146) or the bare subject.
   Move the frame after the subject or make it its own clause.
6. **Coinages and possessive chains.** 的 chains of four or more in a short
   sentence (X的Y的Z的W) appear in only 54 vanilla sentences, almost all
   backstory narration; in a label or tooltip they are the English
   "the suite's gauge's colour" read straight. Name the visible item
   (藥品儀表的顏色, not 系統的儀表的顏色). Hyphenated English compounds become
   long attributive stacks (太空級戰鬥醫療型…); vanilla's longest labels are
   two nouns.
7. **Semicolons, colon pivots and asides.** Description prose holds 19 ；
   and 37 ： across 280k characters; a ； or a ： pivot mid-description is
   generated. Parentheses are ASCII and set solid (`PregnantIconDesc`
   懷孕({0}/{1})) and appear in labels and suffixes, not as prose asides.
   Em dashes are mirrored from the English only (13.5 per 100k value chars,
   Odyssey's ——).
8. **Signature phrases across surfaces.** A rendering of one English pet
   phrase repeated in the descriptions, the ability text and the Workshop
   (就地, 多撐一會兒, 遲鈍又緩慢) reads as a template. Say it once; elsewhere
   say it plainly.
9. **Over-explanation.** Vanilla tooltips state the effect and stop
   (`Ability_CastingTime.description` 施放這個能力需要花費的時間。). Spelling out
   units the row already shows (以秒為單位) or restating the slider's value is
   the tell.
10. **Modder vocabulary.** 定義 / 定義檔 for "definitions", 系統 or 模組 for an
    internal subsystem the player never sees labelled, 數值 where vanilla says
    the stat's own name. 模組設定 and 內建數值 (Shipcracker) are the family's
    accepted settings words.

**Calque** (English syntax under native words), the zh-Hant forms:

- **Article calque.** 一個 / 一種 open vanilla item descriptions on purpose
  (一種力場裝置。, 290 and 235 sentence openers), but inside a sentence an
  English "a/an" rendered as 一個 before every noun (注射一個劑量的…) is the
  tell; vanilla counts with the real classifier or drops it (一劑, 一針).
- **Pronoun subjects.** English "it/they" as 它/它們 at every sentence head;
  vanilla does use sentence-initial 它 (237 times, mostly item descriptions
  continuing from a noun opener), but Chinese drops the subject once the
  topic is clear. Two 它 sentences in a row is the tell.
- **Agentive abstractions.** An English abstract subject kept as the agent
  (計畫發現…, 該系統讓…). Vanilla goes subjectless (後來發現…) or names a person.
- **與 for "and".** Vanilla description prose runs 和 1145 to 與 434; a text
  where 與 joins every noun pair reads as formal written translation. Keep
  與 for fixed frames (與…相同, 與…並肩作戰) and the sibling-shipped
  CE/SOS2 lines.
- **被 passives.** Vanilla uses 被 often (32 per 10k, itself a translation
  habit), so a passive alone is not the tell; stacked passives with an
  English "by" agent (被駕駛員所…) are.
- **Mainland vocabulary.** The Taiwan register list in the style section
  (設定, 預設值, 計畫 147:3 over 計劃, 水準 26:1 over 水平, 模組, 內建) is part of the
  read: a mainland form in free prose is the same tell as a calque.
