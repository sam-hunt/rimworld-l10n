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
- **`LanguageWorker_ChineseSimplified` imposes no authoring requirements at
  all** (BTG) — no particle insertion, no elision, no contraction
  rewriting, nothing analogous to the numeral/case machinery other
  languages need. zh's translation difficulty is entirely about
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
