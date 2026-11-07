# Simplified Chinese — RimWorld localization mechanics

Grounded across the mod family: Unique Melee Weapons' (UMW) 2026-07
machine-assisted generation pass seeded Unique Weapons Unbound's (UWU) own
2026-07 pass, which was itself preseeded into Persona Weapons Unbound's
(PWU) 2026-07-28 pass, and Better Traders Guild's (BTG) 2026-08-09 pass is
the newest and most complete treatment (grounded almost entirely in Core +
Odyssey vanilla data). **No entry below has had native-speaker review** —
every source repo labels its zh glossary "machine-assisted generation" or
"no native review yet," so treat vocabulary choices as well-grounded in the
vanilla corpus but still open to a native reviewer's correction. RimWorld's
language folder is `ChineseSimplified` (Workshop tar: `ChineseSimplified
(简体中文).tar`) — a mod's language folder must match this exactly,
whatever the public mod-roster display name calls the language.

## Engine mechanics (LanguageWorker)

- **Folder-name resolution (UWU, decompile-verified against
  `Verse.LoadedLanguage`):** the constructor derives `legacyFolderName` by
  cutting the display name at the `(` character, and `AllDirectories`
  accepts either the cut name or the full tar name — so a mod folder named
  exactly `ChineseSimplified` loads correctly. The same mechanism holds for
  `Japanese`.
- **No `LanguageWorker_ChineseSimplified` type exists at all** (corrected
  2026-08-19 by UMW's zh-Hant pass, which enumerated the assembly's full
  `LanguageWorker_*` typedef list: no Chinese entry of either script; BTG's
  earlier "imposes no authoring requirements" finding was right about the
  behaviour but implied the type existed). As with Japanese, the base worker
  runs and only merges repeated spaces — no particle insertion, no elision,
  no contraction rewriting. zh's translation difficulty is entirely about
  terminology and register choice, never about engine mechanics.

## Style and corpus findings

Counted or observed against the vanilla zh data (mandatory rules, repeated
consistently across all four source repos unless noted):

- **Full-width punctuation in prose** (，。、；：（）……). Descriptions end
  with 。; labels and buttons carry no trailing period. Placeholders,
  digits, and units stay ASCII. Vanilla labels use full-width parens, e.g.
  锻造台（燃料）, 科研蓝图（{PROJECT_label}）.
- **Quoting named entities — two vanilla-attested styles, split by what is
  being cited.** This rule accumulated across the family and BTG's
  2026-08-09 pass is the fullest statement:
  - Full-width curly quotes (`"{0}"`) for injected placeholders and general
    cited names in prose — vanilla: 任务"{0}" (32 vanilla hits vs. 5 for
    「」, per UWU's count).
  - Corner brackets 「」 for literal UI/building/research names spelled out
    in prose, and for **UI commands the player must click** — vanilla
    research descriptions write 解锁建造「精密装配台」and 研究「基础逆重科技」;
    Odyssey's own game-start dialog writes 请选择飞船控制台，然后点击「发射」
    指令 and 使用「查看星球」.
  - **Only named entities get quoted at all** — common-noun labels stay
    bare, per vanilla `Equip`=装备{0} and `NormalQualityOrBetter`=品质需要
    为一般及以上。 Research/ideoligion/trait *names* are quoted; weapon,
    material, and quality-tier labels are not.
  - Terse stat and job-report templates take no quotes at all
    ({0}伤害, 品质: {0}, 搬运TargetA。).
  - **Lesson (BTG):** when a mod's own UI text has the same shape as an
    existing vanilla analog (e.g. a "select X, then click [Y]" dialog),
    match that nearer analog's punctuation choice rather than defaulting
    to the general prose rule.
- **Terse label templates use an ASCII `: ` separator** (vanilla
  `QualityIs`=品质: {0}, `EffectsAtLevel`=效果: ); full-width ： is reserved
  for use inside prose sentences. (UWU)
- **Job report strings (`reportString` / `JobDriver.GetReport`) are
  verb-first phrases that DO end in 。** — vanilla: 研究中。/ 清理TargetA。
  This is the opposite of Japanese, which takes no period on the same
  string type — do not carry the Japanese rule across languages. (UWU)
- **Em dash handling:** if an English em dash must be carried over, render
  it as a doubled em dash —— (never a single one) — vanilla: 这并不是古老
  的人类科技——而是一个机械族信标. But per the family's general
  no-new-dashes rule, prefer not to introduce a dash where the English
  source has none — a comma （，）carries the same break just as well. One
  repo's zh draft ran at 6.5x vanilla's dash rate before 4 instances were
  reflowed to ，. (BTG)
- **Units attach directly with no space:** `{0}天`, `{0}小时`; a bare Latin
  unit suffix stays ASCII: `{0}W`, `{0}x`. (BTG)
- Vanilla zh files can contain untranslated English values (e.g. Odyssey's
  ancient-mercenaries name symbols) — vanilla incompleteness is not style
  guidance to imitate.
- Some vanilla zh files carry a BOM; a mod's own translated files should
  never add one.
- **Vanilla's own toggle frame is 如果禁用此选项，…将…。** (Royalty's
  quest-reward toggles: 如果禁用此选项，{FACTION_name}将提供其他类型的奖励。),
  and only 4 of 1,877 vanilla tooltips open with 是否. The family's shipped
  启用后，… 禁用后，… (Shipcracker `SCWC_VacuumBurnDesc`) reads naturally and
  stays; this records the vanilla alternative so nobody reaches for 是否.
  (Medic Warcasket, 2026-11-05)

## Grounded common vocabulary

### Trade, settlement, faction, and space (Core/Odyssey)

The most directly reusable table for the family — grounded almost entirely
in Odyssey, which already ships zh for nearly everything a trading/space
mod builds on (BTG, 2026-08-09):

| English | Use | Never | Why |
|---|---|---|---|
| quality tiers | 极差/较差/一般/良好/极佳/大师级/传奇级 | | Core `QualityCategory_*` |
| "of normal+ quality" | 一般品质以上的 | | Core `TradeRequest` quest rules |
| traders guild | 商会 | 贸易公会 | Odyssey `TradersGuild.label` |
| salvagers | 打捞者 | 拾荒者 | Odyssey `Salvagers.label` (its *pawns* are 海盗) |
| trader / merchant | 商人 | | Odyssey `GoldInlay.description` |
| orbital trader | 轨道贸易商 | | Core `CommsConsole.description` |
| Traders will pay more for it. | 商人会支付更高的价格。 | | Odyssey `GoldInlay` — verbatim; 压价收购 is the "pay less" counterpart (`Ugly`) |
| leader (`leaderTitle`) | 领袖 | | Odyssey `GravshipCrew.leaderTitle` |
| {0} from {1} are attacking your {2}. | 来自{1}的{0}正在攻击你的{2}。 | | every Odyssey `FactionDef` — verbatim |
| shuttle | 穿梭机 | | Odyssey |
| gravship / gravlite panel / pilot console | 逆重飞船 / 逆重板 / 飞船控制台 | | Odyssey (`PilotConsole.label`; the Keyed UI's 驾驶台 is a different slot) |
| drop/transport pod vs cargo pod | 运输舱 vs 货舱 | | Core `DropPodIncoming` / `CargoPodCrash` — distinct, don't merge |
| orbital platform | 轨道设施 | 轨道平台 | Odyssey `OrbitalPlatform.label` — so "settlement platform" → 定居点设施 |
| space settlement / settlement | 轨道定居点 / 派系定居点 | | Odyssey `SpaceSettlement.label`, Core `Settlement.label` |
| signal jammer | 信号干扰器 | | Odyssey |
| sentry drone | 哨兵无人机 | 哨戒无人机 | Odyssey `Drone_Sentry.label` |
| life support unit | 生命维持单元 | | Odyssey `LifeSupportUnit.label` |
| mechhive / orbital relay | 机械主巢 / 轨道中继站 | | Odyssey `TheGravship.description` (the namer's 机械巢 is a different slot) |
| goodwill / caravan / negotiator | 好感度 / 远行队 / 谈判者 | | Core |
| market value / silver / packaged survival meal / comms console | 市场价值 / 白银 / 包装生存食物 / 通讯台 | | Core |
| Quest failed: [resolvedQuestName] | 任务失败：[resolvedQuestName] | | Core `TradeRequest` — verbatim |
| [faction_name] became hostile to you. | [faction_name]开始与你敌对了。 | | Core `TradeRequest` — verbatim |
| Attack {0} / Attacking {0}. | 进攻{0} / 正在进攻{0}。 | | Core site approach strings — verbatim |
| reportStrings (clean/rescue/tend/feed/hack/open) | 清理TargetA。/ 救援TargetA。/ 治疗TargetA。/ 将TargetA喂给TargetB吃。/ 骇入TargetA。/ 打开TargetA。 | | Core `JobDef`s — verbatim; NPC-safe copies of these JobDefs can reuse them 1:1 |
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | 兆帕, 毫米均质装甲 | CE 16.7.4 zh-Hans `CE_MPa`/`CE_mmRHA` keep the Latin symbols, so match CE's own info card; the spelled-out forms are zh-Hant's |
| blunt armor / sharp armor | 护甲 - 钝器 / 护甲 - 利器 | | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label`; CE's `CE_DescBluntPenetration` = 钝器穿透 uses the same 钝器/利器 classes |
| flak vest / flak jacket / frag grenade | 防弹背心 / 防弹夹克 / 破片手榴弹 | | Core labels — verbatim |
| plasteel / uranium (uranium only; plasteel is bulleted above) | 玻璃钢 / 铀 | | Core labels |
| respirator / breathing | 呼吸器 / 呼吸能力 | | Respirator is coined (no vanilla respirator item or gene in the zh tars), a plain everyday word, pending native review; Core `Breathing.label` = 呼吸能力 |
| Imperial (adj.) | 帝国 | | Royalty adjective use (帝国逃兵, 帝国穿梭机, 帝国的甲胄骑士); the faction noun stays 破碎帝国 per the Empire bullet below |
| Off / On / default / Default: on (settings) | 关 / 开 / 默认 / 默认：启用 | | Core Keyed `Off`, `On`, `Default`, `Enabled`. Where a file also writes `Default: off.`, use the On/Off pair 默认：开 / 默认：关 (Toxin Warcasket, shipped); 默认：启用 is Shipcracker Warcasket's on-by-default flag |
| settings suffixes (requires Odyssey / default) | （需要奥德赛） / （默认） | | Full-width parens with no leading space, as vanilla 锻造台（燃料）; shipped by Shipcracker and Toxin Warcasket |
| cooldown | 冷却时间 | | Core Keyed `CooldownTime`; settings label 冷却时间（小时） |
| Royalty / Odyssey (DLC names) | 皇权 / 奥德赛 | | Core `ExpansionDefs`; ground Biotech's name the same way (Toxin Warcasket's Workshop page leaves it English, its in-game name is 生物技术) |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | 使用{0}。 | | VEF ships English only; trailing period kept like Core's `JobDef.reportString`s (Shipcracker Warcasket, shipped since 2026-09-26; Toxin Warcasket's abilities too) |
| on cooldown (a reloadable comp's `cooldownGerund`) | 冷却中 | | Vanilla's default for `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker and Toxin Warcasket) |

Also confirmed independently by UWU: **caravan / quest / forbidden / cannot
reach** → 远行队 / 任务 / 已禁用 / 无法到达, never 商队 for caravan (Core
`Caravan`, `Quest`, `ForbiddenLower`, `CannotReach`) — reinforces 远行队
above. And **haul / carrying capacity / market value** → 搬运 / 携带能力 /
市场价值 (Core `Haul.label`, `CarryingCapacity`, `MarketValue`) —
reinforces market value above.

### Quality, materials, and tech levels (Core)

- quality tiers: 极差/较差/一般/良好/极佳/大师级/传奇级 (Core
  `QualityCategory_*`) — identical across all four source repos.
- "requires X quality or better": 品质需要为{0}及以上 (Core
  `NormalQualityOrBetter`=品质需要为一般及以上。)
- quality (the noun): 品质, never 质量 (Core `Quality`/`QualityIs`)
- plasteel: 玻璃钢, never 塑钢 — counterintuitive, always check (Core
  `Plasteel`)
- ultratech (attributive): 极致科技, never 超科技 (`TechLevel_Ultra`=
  极致时代; `BodyPartsUltra`=极致科技)
- archotech (attributive): 超凡科技 (recurs throughout Anomaly/Ideology
  prose)
- tech levels: 石器时代/中世纪/工业时代/太空时代/极致时代/超凡时代 (Core
  `TechLevel_*`)
- tech level (the gating concept): 科技等级, never 科技水平 (Core
  `CantSendMilitaryAidInTime` uses 科技等级 for the mechanical sense)
- wood / components / advanced components: 原木 / 零部件 / 高级零部件,
  never 木材/元件 (Core `WoodLog`, `ComponentIndustrial`, `ComponentSpacer`)
- chemfuel / herbal medicine / silver: 化合燃料 / 草药 / 白银, never
  化学燃料 — vanilla uses 化合, not 化学 (Core labels)
- bioferrite / thrumbofur / birdskin / steel slag chunk: 活铁 / 敲击兽皮 /
  鸟皮 / 钢渣块, never 生物铁 (Anomaly `Bioferrite`; Core `Leather_Thrumbo`,
  `Leather_Bird`, `ChunkSlagSteel`)
- mechanoid: 机械族, never 机械体 (Core)

### Ideoligion and relics (Ideology DLC)

- ideoligion: 文化 (also 文化形态), never 意识形态 — a plain word, no
  portmanteau (Ideology Keyed `ButtonShowAllIdeoligions`, `IdeoligionOf`,
  `ReformIdeoligion`)
- relic: 圣物 (relic of X = X的圣物) (Ideology `<Relic>`, `RelicOf`,
  `RelicTip`)

### UI, jobs, crafting, and general templates (Core/Royalty)

- Cancel / Reset / Confirm / Randomize / Reset to defaults: 取消 / 重设 /
  确定 / 随机 / 还原默认设置 (Core Keyed buttons). **Distinct from**
  Reset to default(s) / Default / None: 重置为默认值 / 默认 / 无, which is
  specifically `ResetBinding` (keybinding-specific), while
  `RestoreToDefaultSettings`=还原默认设置 is the general settings-page
  reset verb — don't use 重置为默认值 outside a keybinding context.
- customize: 自定义, never 定制 (Core `CustomizeIdeoligion`=自定义文化;
  float-menu register matches `Equip`=装备{0})
- fueled / electric smithy: 锻造台（燃料） / 锻造台（电力）, never 铁匠铺
  (Core building labels)
- machining table: 机械加工台 (Core `TableMachining`; `Machining`
  research=机械加工)
- fabrication bench: 精密装配台, never 制造台 (Core `FabricationBench.label`)
- smithing (research): 锻造 (Core `Smithing`)
- advanced fabrication (research): 高级精密装配 (Core
  `AdvancedFabrication.label`, verified 2026-08-18)
- Crafting (the skill): 手工, never 制作 — 制作 is the verb, never the
  skill name (Core `Crafting.label`)
- bill (work bill): 清单, never 工单/账单 — the common community rendering
  工单 is not vanilla (Core `AddBill`=添加清单)
- techprint: 科研蓝图, never 技术图纸 (Royalty `TechprintLabel`=
  科研蓝图（{PROJECT_label}）)
- Empire (faction): 破碎帝国, never 帝国 alone (Royalty `Empire.label`)
- item stash / bandit camp / ancient mercenaries: 物品藏匿点 / 匪徒营地 /
  古代雇佣兵 (Core sites, Odyssey quest)
- ancient (sealed) crate: 密封储物箱 (Odyssey `AncientSealedCrate`)
- tribesfolk / tribal chief: 部众 / 酋长 (Core `TribeRough`)
- scrap / mod / log / save: 废料 / 模组 / 日志 / 存档 (Core
  `CubeMaterialScrap`, `ScenPart_Error`, `OpenLogOnWarnings`,
  `SaveGameDataFolder`)

### Medical, tending and ability vocabulary (Core, with Royalty, Anomaly and Combat Extended where named; Medic Warcasket, 2026-11-05)

| English | Use | Never | Why |
|---|---|---|---|
| mechanite(s) | 纳米机械 | 机械体, 机械微粒 | Core `FibrousMechanites.label` 肌纤维纳米机械感染, `SensoryMechanites.label` 感官纳米机械感染 (Medic Warcasket, 2026-11-05) |
| medicine labels (herbal / industrial / glitterworld) | 草药 / 医药 / 闪耀世界医药 | 医药 for generic medicine in prose | Core `MedicineHerbal`, `MedicineIndustrial`, `MedicineUltratech`; 医药 is the industrial item's own label, so generic "medicine" in prose reads as 药品 (Medic Warcasket) |
| go-juice / wake-up / heart attack / infection | 活力水 / 清醒丸 / 心脏病发作 / 感染 | | Core `GoJuice`, `WakeUp`, `HeartAttack`, `WoundInfection` labels |
| tend (action) / tend quality / tend speed | 治疗 / 治疗质量 / 治疗速度 | 质量 alone | Core `TendPatient.reportString` 治疗TargetA。, `MedicalTendQuality`, `MedicalTendSpeed`, Keyed `TendQuality`; the float-menu verb is 照料 (`Tend` 照料{0}, `TendingNotRequired` 不需要照料) |
| doctor (work type) / caring work tag / Work tab | 医生 / 医疗工作 / 「工作」面板 | | Core `Doctor.labelShort`, Keyed `WorkTagCaring`, `WorkTab.helpText` |
| manipulation / sight / pain / pain shock / downed | 操作能力 / 视觉能力 / 疼痛 / 因疼痛而休克 / 倒地不起 | 击倒 for the pawn state | Core `Manipulation`, `Sight`, Keyed `Pain`, `PainShock`, `Wait_Downed.reportString`, `DownedCannotCrawl`; 击倒 is the `TaleDef` `Downed.label`, not the pawn state, so a `Downed.label` grep misleads |
| casting time / range / requires line of sight | 释放时间 / 射程 / 目标必须可视 | | Core Keyed `AbilityCastingTime`, `Range`, `AbilityRequiresLOS` |
| severity | 严重程度 | 严重性 | Core Keyed `ConfigurableSeverity` 严重程度：{0} |
| Mote (a mote def's inherited label) | 特效 | 微粒 | Core `Mote_Clean`, `Mote_Stun` and most other `Mote_*` labels (a few sparks are 尘埃) |
| Blue / Green / Red (Keyed color words) | 蓝 / 绿 / 红 | | Core Keyed `Blue`, `Green`, `Red`; Core has no `Pink` key (粉 follows `Structure_Pink` 淡粉, `Hair_Pink` 粉发) |
| injector / injection serum | 注射器 / 注射针剂 | | Royalty `VenomFangs.description`, Anomaly serum descriptions |
| trait description pawn tokens | keep `{PAWN_nameDef}`, `{PAWN_pronoun}`, `{PAWN_objective}` in place | | Core `Wimp` (一点小伤小疼就能让{PAWN_objective}晕过去), `Tough` |
| suppressability (Combat Extended) | 压制敏感度 | | CE's own zh-Hans `Suppressability.label` |

## Grounded common vocabulary, VFE Pirates warcasket domain (q847633684/Vanilla-Expanded-ZH pack + Core, 2026-10-28)

VFE Pirates ships English only; its terms are grounded against the community
Vanilla Expanded Simplified Chinese pack (GitHub
`q847633684/Vanilla-Expanded-ZH`, the `Vanilla Factions Expanded - Pirates`
folder: its 1.6 `DefInjected/VFEPirates.WarcasketDef/VFEPirates.WarcasketDef.xml`
WarcasketDef ThingDef injections, Keyed UI and ResearchProjectDef files), which
carries the Siegebreaker, Cataphract and Hazard sets and the 7th- and
10th-generation paragraphs; vanilla terms are grounded against the Core,
Royalty, Odyssey and Biotech `ChineseSimplified (简体中文).tar`. Every warcasket
set in the family (Shipcracker, Toxin, Medic, Overlord) renders these terms
alike so the sets read as one family in-game; a change is made here first and
each set's shipped files follow at its next pass. A set's own name, its
Workshop title and its own coinages stay in that repo's glossary.

| English | Use | Why |
|---|---|---|
| warcasket | 战棺 | Community VFEP pack throughout (`VFEP.RequiresWarcasket` = 需要战棺, every set label); the Workshop title anchor. |
| `<set>` warcasket / shoulders / helmet (label pattern) | `<set>`型战棺装甲 / `<set>`型战棺护肩 / `<set>`型战棺头盔 | Community pattern (`VFEP_Warcasket_Siegebreaker.label` = 破袭型战棺装甲 and siblings). The body piece takes 装甲 although the English label has no noun, exactly as the pack does. |
| warcasket foundry | 战棺铸造厂 | Community `VFEP_WarcasketFoundry.label`. |
| warcasket slugthrower | 战棺霰弹枪 | Community `VFEP_WarcasketGun_Slugthrower.label` (fetched 2026-11-07). Medic Warcasket names it as the gun its stranger in black carries. |
| weld on / entomb (Workshop) | 在战棺铸造厂完成改造; 封在战棺里 | Community renders entomb loosely (进入铸造厂, 战棺改造 in `VFEPirates.EntombingWarning`); the Workshop follows that looseness. |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | 「太空时代战棺」 / 「特化型战棺」 | Community `VFEP_SpacerWarcaskets.label` and `VFEP_SpecialisedWarcaskets.label`; corner brackets per vanilla research-name citation (研究「基础逆重科技」). Shipcracker's and Toxin's shipped text cites 「太空时代战棺」; no shipped file cites 「特化型战棺」 yet. |
| VFEP set names | 破袭型 (siegebreaker), 狂怒型 (brute), 圣盾型 (guardian), 突击型 (aerial), 骑士型 (cataphract), 险境型 (hazard) | Community pack labels (`VFEP_Warcasket_Aerial.label` = 突击型战棺装甲, `VFEP_Warcasket_Cataphract.label` = 骑士型战棺装甲, `VFEP_Warcasket_Hazard.label` = 险境型战棺装甲); 骑士 also matches Royalty's 骑士装甲. The third-party 无畏 prefix (WarCasket Expanded) is not used; the VFEP pack has none. Controller and sarcophagus: no glossary records the pack's rendering and the pack's files were not available to this pass, so they are unrecorded here; take them from the pack when a set needs them. |
| 7th generation / 10th generation (VFEP's two chassis) | 第七代 / 第十代 | Shipcracker's and Toxin's shipped prose (第七代战棺, 第十代太空时代机体), following the pack's paragraphs. |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | 特化型战棺`<part>`，在增加机体重量的同时大幅提升了防护性 | Community pack: superior = 大幅 (Shock), worse weight = 增加机体重量 (Barrage); Toxin Warcasket's shipped `shortDescription`s. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet (VFEP's 10th-generation opener) | 特化型太空时代级别战棺装甲/护肩/头盔 | Community pack's opening phrase for every 10th-generation part, verbatim (Shipcracker and Toxin Warcasket, shipped). |
| ... with standard protection (the 10th-generation opener's tail) | ，在不增加机体重量的同时极大幅提升了防护性 | Community pack's Siegebreaker / Controller / Sarcophagus openers, every "standard protection" part (loose, as the pack is); Toxin Warcasket's shipped `TXWC_SpacerShortDescription_*`. |
| 7th-generation paragraph (VFEP's lore paragraph on the 7th-generation chassis) | 由于机体基本性能的强化陷入瓶颈，第七代战棺的研发重心转向…… | Community pack's Hazard/Barrage/Shock text verbatim, its —— reflowed to a comma; shipped in Toxin Warcasket's descriptions. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | 第十代战棺有些特殊，它们是用从海盗那里收缴的设备改造而成的…… | Community pack's Siegebreaker text verbatim (loose, as the pack is; the pack's Siegebreaker / Brute / Guardian / Sarcophagus / Controller descriptions share it), its —— reflowed to a comma; the full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/ChineseSimplified/`. |
| spacer tier / spacer (armor, costs) | 太空时代级别 | Community pack's 10th-gen opener (特化型太空时代级别…); vanilla `TechLevel_Spacer` = 太空时代. Toxin's toggle 毒素型战棺升级为太空时代级别 is declarative like 险境型战棺可抵御真空. |
| pilot (the wearer) | 驾驶员 | Community Keyed/lore (成为驾驶员的殖民者); Shipcracker's and Toxin's shipped prose. |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | 太空时代级别的护甲与隔温 / 能量护盾 / 高级零部件 | Toxin Warcasket's shipped `TXWC_SpacerTierDesc`; 能量护盾 per Core `Apparel_ShieldBelt.description` (单人用的能量护盾装置); 高级零部件 per Core `ComponentSpacer.label`. The glossaries record no Core row for 隔温. |

Pending native review for the whole family: 呼吸器 (coined, no vanilla or
community source). Everything else in this section is the community pack's own
rendering or a vanilla term; the set-specific coinages each repo lists stay
pending there.

## Pitfalls and lessons

- **Quoting-rule documentation drifted across repos, and the newest,
  fullest statement wins.** UMW's original 2026-07 rule was curly quotes
  only. UWU's 2026-07 pass (built on UMW) split this into two vanilla
  styles by citation type and added the "only named entities get quoted"
  and ASCII-colon findings. PWU's 2026-07-28 pass preseeded UMW's simpler
  rule verbatim and did not carry UWU's refinement forward — treat that as
  PWU's documentation lagging, not as a competing rule. BTG's 2026-08-09
  pass is the newest and adds the "UI commands the player must click"
  case plus the "pick the nearer analog" meta-lesson; it is the authority
  used above, layered on top of UWU's two-style split rather than
  replacing it.
- **A translator comment describing an English label is not the defName —
  resolve hints through the tar, never by translating the described
  English text.** PWU's landmine: a `{2}` hint's translator comment
  described a research label in English prose, but the actual def
  (`ShipComputerCore`) renders in zh as something with no resemblance to
  that English description at all, and no def literally named after the
  described English phrase exists to grep for. When a hint's comment
  describes what a referenced def "is" in English, look up the real
  defName's zh value in the vanilla tar rather than translating the
  comment's English words directly.
- All four repos flag their zh glossaries as machine-assisted with no
  native review yet (the one native-review pass in the family, UWU PR #6,
  covered Russian, not zh) — treat every mapping above as well-grounded
  but still a candidate for native correction.
- ideoligion's exact rendering (文化 vs. 文化形态) is attested both ways
  across repos with no stated resolution rule between the two forms;
  pick per-context (bare noun vs. compound) rather than treating either
  as strictly wrong.

- **A mass-noun charge noun fits every vanilla reload slot; a counted one
  does not** (2026-10-13, Toxin Warcasket): `燃料` reads naturally in
  `没有燃料。` and `燃料剩余`, while `单位` would not, so keep the noun a mass
  noun and put the counter in the mod's own strings
  (`需要{COUNT}单位{CHARGENOUN_plural}`).
- The community pack (`q847633684/Vanilla-Expanded-ZH`) is on GitHub with a
  1.6 `DefInjected/VFEPirates.WarcasketDef/VFEPirates.WarcasketDef.xml`; its
  shared 7th-generation paragraph carries a `——` to reflow into `，`.

## Excluded from this reference (mod-specific, not consolidated here)

- **BTG:** cargo vault 货物保险库 (and hatch variants), shuttle bay
  穿梭机库, smuggler's den 走私巢穴, threat points 威胁点数, orbital
  steel/rust 轨道钢/锈色, independent traders 独立商人, Exiled Traders
  流放商人, cargo claim 货物提取权, the localized Workshop title 强化商会,
  and the `traitAdjectives` bare-attributive-word grammar rule (BTG has no
  weapon-naming system of its own; refers to UMW).
- **UMW:** weapon trait/unique-weapon vocabulary (特性, 特化武器), weapon
  type labels (monosword/plasmasword/zeushammer/longsword/spear/mace/
  knife/gladius/axe/warhammer), `traitAdjectives` composition rules
  (的-less attributive words, weak-character avoidance), name grammar (的/
  之 linking, "The X of Y"→Y之X, material compounding), battle-log grammar
  ([skillAdv] 地-ending, RECIPIENT_possessive dropping), wielder/bearer
  stat-context terms, stun/EMP, and the full mod-decided-pending-review
  list (格挡/战团/战帮/剑格/十字护手/撼地/鼓舞呐喊/士气大振/传世/打桩头/阿片/
  珐琅/无回弹, WeaponCategoryDef labels).
- **UWU:** weapon trait/unique-weapon vocabulary, charge/beam weapon
  vocabulary, toxic/incendiary/EMP ammo vocabulary, flare, inlay/grip/
  ornamental/lightweight weapon-mod vocabulary, accuracy-penalty weapon
  stat phrasing, and the full mod-decided-pending-review list (research
  trio 特化武器锻造/机械加工/精密装配, haul planner modes, haul plan, net
  refund/cost, texture tab, vanilla-behavior suffix, disarm-from-hostile
  phrasing, progression section header, gizmo button, "武器def", 稀有度,
  太空时代特性最低成本).
- **PWU:** persona-weapon Δ' label prefix and grammar, persona/persona-core
  prose vocabulary, persona weapon trait stat term, freewielder trait
  label, the bladelink-customization coinage (智能人格定制) and its native-
  review flag, and the ShipComputerCore/persona-core specifics of the
  landmine noted above (generalized into a methodology lesson, kept
  above; the mod-specific defName mapping itself is excluded).

## Generated-text tells

Catalogued 2026-11-05 by Medic Warcasket's first zh pass, from the Core,
Royalty, Ideology, Biotech, Anomaly and Odyssey `ChineseSimplified (简体中文).tar`
values with comments stripped (47,586 values, 1.15M characters; rates are per
100k characters). Each item is the `English.md` § 2 category as it shows up in
Chinese, with the vanilla evidence. Mirrored strings are exempt; descriptions,
settings tooltips and Workshop prose are the slots to read.

1. **One frame on every tooltip.** Vanilla stat descriptions open with a
   bare noun-phrase definition (`MedicalTendSpeed` 此人作为一名医生治疗伤患和病人的速度。),
   so that opener is native; the tell is the same opener plus the same
   trailing consequence clause (……，超出部分会被清除。) on every row. Vary or
   cut the second sentence.
2. **是否 openers.** The "Whether" calque. Only 4 of 1,877 vanilla `*Desc` /
   `*Tip` / `*Info` tooltips open with 是否 (Royalty's quest-reward toggles).
   Toggles take 启用后，… 禁用后，… (the family frame) or vanilla's own
   如果禁用此选项，…将…。 (Royalty `*Desc` reward toggles), never 是否.
3. **Telegraphese.** Clipped clauses with no 会 / 可以 / 能 / 也: 技能定节奏。
   Vanilla descriptions spend the modal (会 538, 可以 246 per 100k in item,
   ability and hediff descriptions) and write consequences as 会…, so a
   string with no modal anywhere reads as a spec sheet.
4. **Stacked four-character closers.** The tricolon-and-aphorism tell in
   Chinese is a lore paragraph that ends on two or three parallel 四字格 phrases
   (攻守兼备，进退自如。). Vanilla uses idioms singly and mid-sentence (Royalty
   `Apparel_ArmorLocust` 差强人意 … 首屈一指, the one hit for 首屈一指 in the
   whole corpus) and ends on a plain statement of use (像这样的装甲通常由执行快速突击任务的太空陆战队员使用。).
5. **当…时 and 随着… openers on every sentence.** The participle-clause
   calque. Vanilla has them (当 810 and 随着 135 hits overall) but spread
   thin; two in one tooltip, or one opening each sentence of a paragraph, is
   the tell. A bare topic or a 时 / 后 clause (启用后，释放期间，) is shorter.
6. **的-chains and stacked modifiers.** A …的…的…的 run inside one clause
   occurs 8 times per 100k in vanilla descriptions. English hyphen compounds
   and possessives ("the shoulders' injector", "medicine-laden") come out as a
   long pre-noun modifier; name the visible item (护肩的肾上腺素注射器 → 肾上腺素注射器)
   or move the modifier into its own clause.
7. **Semicolons, dashes and parenthetical asides.** Vanilla runs ； at 2,
   —— at 36 and （ at 64 per 100k overall, （ at 15 in item/ability/hediff
   descriptions (most of them label qualifiers such as 锻造台（燃料）). A
   ； or a （…） aside in a description or tooltip is a tell; split the
   sentence or use ，. A 冒号 pivot inside prose (……：……) is rare outside
   `默认：{0}。` and list headers.
8. **Repeated signature phrases.** The same coined phrase (就地, 多撑一阵,
   迟钝缓慢) in the descriptions, the ability text, the settings and the
   Workshop page. Say it once and plainly elsewhere.
9. **Over-explanation.** A tooltip restating what the row's value or a
   vanilla stat already shows. Vanilla tooltips stop after one or two
   sentences (mean sentence 23.7 characters, 0.59 commas per sentence in
   descriptions); a sentence over about 40 characters with three or more ，
   is worth splitting.
10. **Modder vocabulary.** 定义 (defs) appears in vanilla only in the
    custom-difficulty and transporter UI (27 hits, none about game content),
    and never 子系统, def or 套件 for an internal subsystem. Name what the
    player sees: the item's label, 计量表, 「工作」面板.
11. **Calque: English clause order under Chinese words.** The pass's own
    misses, each a native word on an English skeleton:
    - an abstract agent doing a person's verb: 计划发现…… ("the program
      found"); Chinese gives the verb to people (项目组发现……);
    - a trailing English participle or adverbial tacked on after the main
      clause: 就地治疗其伤口，从最严重的伤口开始。; Chinese puts the manner
      before the verb (就地从最严重的伤口开始逐一治疗。);
    - "any other way" kept as a modifier: 无法以其他方式继续服役;
      a native writer says 除此之外再也无法服役;
    - pronouns the English needs and Chinese drops (他们, 它, 其 every
      clause): vanilla 他们/它们 runs at 204 per 100k in descriptions,
      mostly where the subject changes;
    - 一个 / 一名 before every count noun as an English article: vanilla
      opens item descriptions with 一套 / 一种 once (一套标准动力装甲),
      not on every noun.
