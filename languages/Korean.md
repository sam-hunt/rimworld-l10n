# Korean — RimWorld localization mechanics

Grounded across the mod family, in generation order: PersonaWeaponsUnbound's
(PWU) 2026-07-28 ko pass (no preseed — grounded independently against Core,
Royalty, Ideology and Odyssey tars); UniqueMeleeWeapons' (UMW) 2026-07 pass,
cross-checked the same day against PWU's; UniqueWeaponsUnbound's (UWU) 2026-07
pass (extended through 2026-07-30), which calibrated the josa-marker lint
against the vanilla ko corpus; and Better Traders Guild's (BTG) 2026-08-10
pass, the newest and most complete, which added two decompile-verified
findings absent elsewhere — that colour tags do not break josa-marker
resolution, and a detailed description of the inline josa-simulator lint used
to check authored strings. None of the four mods has had a native Korean
review yet; treat mod-decided/coined terms accordingly. RimWorld's language
folder is `Korean` (tar: `Korean (한국어).tar`); decompile-verified
(`Verse.LoadedLanguage`): the ctor derives `legacyFolderName` by cutting at
`(`, and mod language directories match on *either* `folderName` or
`legacyFolderName` — the same mechanism behind `Japanese`.

## Engine mechanics (josa markers and LanguageWorker)

**Josa (particle) markers are the one hard mechanical rule Korean adds, and
nothing else in this skill family has an equivalent — and it applies to any
Keyed string, not just combat or rulepack text.** Korean particles are
allomorphic: the correct form depends on whether the preceding syllable ends
in a consonant, which is unknowable when the preceding text is an injected
value (a silver amount, a def label, anything from `{0}`).
`Verse.LanguageWorker_Korean.ReplaceJosa` (decompile-verified) resolves
exactly eight tokens, and no others:

```
(이)가   (와)과   (을)를   (은)는   (아)야   (이)어   (으)로   (이)
```

- Every *allomorphic* particle following `{0}`, `[symbol]` or `[TOKEN_x]` MUST
  use a marker. `{0}(을)를 생성` is correct; `{0}를 생성` breaks on
  consonant-final labels. Only five distinctions actually inflect (은/는,
  이/가, 을/를, 와/과, 으로/로); **`에`, `에서` and `의` are invariant** — write
  those bare after a placeholder. A particle after a *fixed* Korean noun
  (nothing to resolve) should likewise be written literally, not as a paren
  pair.
- Never hand-roll `{0}을(를)` — the worker does not recognize it.
- **Spelling is exact, and `(와)과` is asymmetric.** For every token the paren
  holds the post-*consonant* form — except `(와)과`, where `JosaPatternPaired`
  maps to `("과","와")`, so the paren holds the post-*vowel* form. The reversed
  order, `(과)와`, does not match the regex at all and ships as literal
  garbage.
- **A marker resolving off a digit is always wrong.** `HasJong()` falls back
  to `AlphabetEndPattern` = `{b,c,k,l,m,n,p,q,t}` for non-Korean characters,
  which has no digits, so a number always yields the vowel form — right for
  2/4/5/9 (이·사·오·구), wrong for 1(일) 3(삼) 6(육) 7(칠) 8(팔) 0(영). Phrase
  around it, never mark it — this matters directly for any settings window
  with numeric sliders (silver amounts, percentages, counts: `{1} x{2} 예약에
  실패했습니다`, not `x{2}(을)를 예약하지 못했습니다`). The same table means a
  Latin-script tail is treated as consonant-final only for those nine
  letters, so e.g. `Odyssey` → ends in `y` → resolves as vowel-final. A bare
  *invariant* particle after a number is fine (`0으로 설정하면`) since no
  marker means the worker never touches it.
- **Quoting interacts with resolution.** `FindLastChar` skips a preceding `"`,
  `'` or `)` (walking back past the matching `(` and any spaces) to reach the
  real final character, so `"{0}"(을)를` resolves correctly. Curly `" "` and
  corner `「 」` quotes are **not** skipped, so the token is returned
  unresolved and the raw `(은)는` shows on screen. Korean therefore needs no
  defensive quoting at all — josa does the job quoting does in ja/ru/zh.
- **Colour tags do NOT break a marker** (decompile-verified 2026-08-10):
  `ReplaceJosa` first runs `StripTags`, whose `TagOrNodeClosingPattern` =
  `(\(|<)\/\w+(\)|>)` removes *closing* tags only, so a `.Colorize()`d
  argument's trailing `</color>` is gone by the time `FindLastChar` looks
  back — the marker resolves off the value's real last syllable. (The
  surviving *opening* tag sits before the value and never matters.) A marker
  after a colorized argument is therefore safe in principle — though a fixed
  literal noun placed after the colorized value entirely sidesteps the
  question when the value itself is arbitrary text in any script (a faction
  or mod name) and a fixed particle simply cannot be wrong.
- **`reportString`s must carry no josa marker at all, and no trailing
  period.** `TargetA`/`TargetB` are substituted by `JobUtility`'s plain string
  `Replace` *after* the def value was post-processed at load, so a marker
  there resolves against the literal token text, not the eventual label.
  Vanilla ko sidesteps it by using only invariant particles (`TargetB에게
  TargetA 먹여주는 중`) or none. The form is `~하는 중` / `~ 중`, with **no**
  trailing period where English has one.
- The one safe unmarked case is a symbol that always resolves the same way —
  a fixed pronoun (Korean pronouns are always vowel-final, e.g.
  `[some_pronoun]는`). Def labels, pawn names, material words, mod-coined
  terms, and numbers are never safe to leave unmarked.

**A lint for this lives outside any repo's language-agnostic checker.** The
2026-08-10 pass ran an inline Python reimplementation of `ReplaceJosa` (~30
lines: `JosaPatternPaired`, `FindLastChar`, `HasJong`/`HasJongExceptRieul`,
`StripTags`) over the resolved strings — simulating the worker beats
eyeballing the rule, and should be rebuilt rather than trusted from a
read-through. An earlier calibration of the same idea (from the 2026-07 pass)
was tuned to zero false positives against the vanilla ko Keyed corpus plus
Odyssey's WeaponTraitDefs and Core's DamageDefs; four patterns fooled early
drafts of the lint and must stay excluded: `(와)과의` (a valid token plus an
ordinary trailing `의`), `기간 (일)` (a parenthetical unit, not a marker), a
bare `0으로` (no marker present, so untouched and already correct), and
`{2}(으)로` (correct authoring — only a *literal* digit sitting directly
before a marker is provably wrong).

## Style and corpus findings

- ASCII punctuation only (`.` `,`) — full-width `、`/`。` are 0 hits in vanilla
  ko. Descriptions/tooltips take polite formal `-습니다.`/`-입니다.`, ending
  with a period; labels, buttons and stat fragments take none.
- **Register splits by def type — don't pick one voice for the whole
  language.** `ThoughtDef` stage descriptions are casual first-person (`-어`,
  `-지`, `-군`, `-거야`; vanilla `이제 거의 깼어.`). Battle-log `rulesStrings`
  end in the nominalized `-함.`/`-임.` form, not polite form (vanilla
  `Combat_Dodge`: `… [implement](을)를 [skillAdvMaybe] 피함.`). Everything else
  defaults to polite `-습니다.`. Anesthetic-style stage labels (혼미함, 안정됨)
  show the `-됨` hediff-stage family.
- Job report strings (`reportString`, `RecipeDef.jobString`) take the form
  `~ 중` / `~하는 중` with **no** trailing period (`Research`=연구 중,
  `BuildSnowman`=눈사람 만드는 중); `RecipeDef.label` itself is `~ 만들기`.
- Research `generalRules` `subject_story` uses polite past **했습니다** — not
  the plain 했다 that Japanese uses for the same field. This is a per-language
  choice; check it fresh rather than carrying a sibling language's answer
  over.
- Quote cited def labels and cross-referenced UI labels with **ASCII single
  quotes** — vanilla writes `연구 프로젝트 '{PROJECT_label}'`. Never `「 」`,
  never curly quotes. Pawn names are not quoted. (This is a separate
  convention from the josa-marker quoting behavior above — it's about which
  citations get quoted at all, not about how `FindLastChar` walks back
  through a quote that's already there.)
- **Korean uses spaces**, unlike Japanese and Chinese, which concatenate. Any
  RulePackDef-driven composition should treat Korean word tokens as
  space-delimited, the same as English, rather than porting a concatenative
  language's spacing rules.
- **Korean omits possessive pronouns.** Vanilla ko's combat rulePacks contain
  12 textual occurrences of `[RECIPIENT_possessive]`, all inside `<!-- EN:
  -->` comments and **none** in the actual Korean values — the pattern
  generalizes: prefer dropping a possessive-pronoun symbol in Korean output
  rather than rendering a literal 그의/그녀의.
- Units attach with no space: `{0}시간`, `{0}일`, `{0}칸`. Some vanilla ko
  files carry a BOM; a mod's own should not.

## Grounded common vocabulary

Core/Odyssey-grounded terms usable by any mod in the family (verbatim vanilla
strings unless noted):

| English | Use | Never | Why |
|---|---|---|---|
| Cancel | 취소 | | Core Keyed — identical across every mod in the family |
| Reset / Reset all | 초기화 / 모두 초기화 | | Core Keyed |
| Confirm | 확인 | | Core Keyed |
| Randomize | 섞기 | 무작위 | Core `Randomize` |
| Reset to defaults / Restore defaults | 기본값 복원 | 기본값으로 재설정 | Core `RestoreToDefaultSettings`; `기본값으로 재설정` is `ResetBinding`, a **different**, keybinding-specific key — don't conflate the two |
| Default / None | 기본값 / 없음 | | Core `Default`, `None` |
| quality tiers | 끔찍 / 빈약 / 평범 / 상급 / 완벽 / 걸작 / 전설적 | | Core `QualityCategory_*` |
| "of normal+ quality" / "(worth [X])" | 평범 품질 이상의 / (가치: [X]) | | Core `TradeRequest` — verbatim |
| trader / orbital trader | 상인 / 궤도 상인 | | Core, Odyssey |
| bulk / exotic goods trader | 원자재 상선 / 희귀품 상선 | | Odyssey orbital `TraderKindDef`s — the *caravan* kinds are 상인, the orbital ones 상선 |
| Traders will pay more/less for it. | 상인들이 더 높은 값을 쳐줍니다. / 상인들은 더 적은 돈을 쳐줍니다. | | Odyssey `GoldInlay`/`Ugly` descs — verbatim, reused unchanged across the whole family |
| goodwill / negotiator / caravan | 우호도 / 협상가 / 상단 | 호감도 | Core `Goodwill`, `Negotiator`, `TradeRequest` |
| silver / market value | 은 / 시장 가치 | | Core |
| comms console / packaged survival meal | 통신기 / 보존 식량 | | Core |
| steel / vacuum / reinforcements / hatch / safe | 강철 / 진공 / 증원군 / 해치 / 금고 | | Core, Odyssey |
| shuttle | 왕복선 | 셔틀 | Core `Shuttle`, Odyssey `Shuttles` |
| transport/drop pod vs. cargo pods | 수송 포드 vs. 화물 낙하기 | | Core `DropPodIncoming*` / `CargoPodCrash` — distinct concepts, don't merge |
| orbital platform / settlement platform | 궤도 플랫폼 / 정착지 플랫폼 | | Odyssey `OrbitalPlatform`, `SettlementPlatform` |
| orbital settlement / settlement / colony | 궤도 정착지 / 정착지 / 정착지 | | Odyssey `SpaceSettlement`, Core `Settlement`, `PlayerColony` — colony and settlement share 정착지, disambiguate with 내 when both appear together |
| traders guild / guild member(s) | 교역 조합 / 조합원(들) | 상인 길드 | Odyssey `TradersGuild.*` — the faction's own label |
| signal jammer / sentry drone / life support unit | 신호 교란기 / 센트리 드론 / 생명 유지 장치 | | Odyssey |
| gravship / gravlite panel / pilot console | 중력부양선 / 중력감응판 / 조종석 | | Odyssey |
| mechhive / orbital relay | 메카노이드 군락 / 궤도 중계기 | | Odyssey `TheGravship.description` |
| [faction_name] became hostile to you. | [faction_name](이)가 적대로 돌아섰습니다. | | Core `TradeRequest` — verbatim |
| {0} from {1} are attacking your {2}. | {1}의 {0}(이)가 당신의 {2}(을)를 공격하고 있습니다. | | every Odyssey `FactionDef` — verbatim |
| Attack {0} / Attacking {0}. | {0} 공격 / {0} 공격 중 | | Core site-approach strings — verbatim, no trailing period |
| Quest failed: [resolvedQuestName] | 임무 실패: [resolvedQuestName] | | Core `TradeRequest` — quest = 임무 |
| colour labels | `~색` (은색, 회색) | | Core `ColorDef`s |
| reportStrings (clean/rescue/tend/feed/open/hack) | TargetA 청소 중 / TargetA 구조 중 / TargetA 간호 중 / TargetB에게 TargetA 먹여주는 중 / TargetA 여는 중 / {TargetA} 해킹 중 | | Core `JobDef`s — verbatim. Core's own `Hack.reportString` keeps braces around `{TargetA}`; drop them when reusing the pattern in a mod's own def, since the English `TargetA` symbol has no braces and a placeholder-parity checker reads the retained braces as an invented placeholder |
| advanced fabrication (research) | 고급 부품 | 고급 제작 | Core `AdvancedFabrication.label` — verbatim; vanilla ko deliberately names the research identically to the advanced-component item, don't "fix" it (verified 2026-08-18) |
| MPa / mm RHA (Combat Extended units) | MPa / mm RHA | 메가파스칼 in a label | CE 16.7.4 ko Keyed lacks `CE_MPa`/`CE_mmRHA`, so CE's own info card shows the English fallback; KS A ISO 80000 uses the Latin symbols |
| blunt armor / sharp armor | 방어도 - 둔탁함 / 방어도 - 날카로움 | | Core `ArmorRating_Blunt.label`/`ArmorRating_Sharp.label` |
| armor penetration | 관통력 | 보호구 관통 | CE ko `CE_DescArmorPenetration` says 보호구 관통; the family's existing settings strings use 관통력, keep it |
| flak vest / flak jacket / frag grenade | 방탄조끼 / 방탄재킷 / 파편 수류탄 | | Core labels — verbatim |
| spacer-tech / spacer | 우주시대 기술 / 우주시대 | | RMK VFEP descriptions (`우주시대 기술로 특화된`); Core `TechLevel_Spacer` = `우주` |
| Imperial (adj.) | 제국 (bare prefix) | | Royalty backstories: `제국 부대`, `제국 사제`, `제국군` |
| respirator / breathing | 내장 호흡 장치 (호흡 장치 when shortened) / 호흡 | | Coined around Core `Breathing.label` = `호흡`; Shipcracker ships the full form, Toxin the shortened one |
| sealed (airtight helmet) | 밀폐형 | | `밀폐` is the usual word for an airtight suit; Core's `AncientSealedContainer` family uses `밀봉` for sealed containers, which is why the helmet does not |
| chemfuel / plasteel / uranium | 화학연료 / 플라스틸 / 우라늄 | | Core / Odyssey labels |
| Off (slider value at 0) / on (toggle) | 없음 / 켜짐 | 끄기 | Core Keyed `None` = `없음`; Core `Off` = `끄기` is a toggle verb and reads wrong as a value |
| cooldown (slider caption) / radius | 재사용 대기 / 범위 | | Core Keyed `StatsReport_Cooldown` = `재사용 대기시간` with `시간` dropped so the caption does not repeat a `(시간)` unit; `AbilityEffectRadius` = `효과 범위` |
| Odyssey (DLC name) / (requires Odyssey) | 오디세이 / (오디세이 필요) | | Core `ExpansionDef` `Odyssey.label` = `오디세이`; suffix shape after Core `BlockedByTerrain` (`({0_label} 필요)`) |
| fuel tank (settings) | 탱크 / 연료 탱크 | | Shipcracker Warcasket's shipped Workshop and settings text (`연료 탱크`); Toxin keeps `탱크` for its gas tank |
| Using ability: {0} (VEF `AbilityDef.jobReportString`) | {0} 능력 사용 중 | | VEF ships English only; Shipcracker Warcasket's rendering, shipped by Shipcracker and Toxin Warcasket (no trailing period) |
| on cooldown (a reloadable comp's `cooldownGerund`) | 재사용 대기 중 | | Core Keyed `ShieldOnCooldown` = `재사용 대기 중`; the field is vanilla's `CompProperties_ApparelReloadable.cooldownGerund`, which a mod's DefInjected carries whenever the probe lists it (Shipcracker and Toxin Warcasket) |

### Medical, tending and ability vocabulary (Core and Odyssey; Medic Warcasket, 2026-11-05)

| English | Use | Never | Why |
|---|---|---|---|
| herbal / industrial / glitterworld medicine | 생약 / 약품 / 번화계 약품 | | Core `MedicineHerbal`, `MedicineIndustrial`, `MedicineUltratech` labels; all three consonant-final, so a marker after an injected medicine label resolves to the 이 / 을 / 으로 side |
| medicine (the category) | 의약품 | 약품 for the generic | Core ThingCategory `Medicine.label`; 약품 is the industrial medicine's own label |
| go-juice / wake-up / heart attack | 고주스 / 웨이크업 / 심근경색 | | Core labels |
| mechanites | 기계입자 | | Core `FibrousMechanites` (근섬유질 기계입자), `SensoryMechanites`, `MechSerumResurrector` |
| tend / tend quality / tend speed / medical skill | 치료 / 치료 품질 / 치료 속도 / 의학 | | Core Keyed `Tend`, `TendQuality`, `MedicalTendQuality`, `MedicalTendSpeed`, `Medicine.skillLabel` |
| doctor (work type) / caring (work tag) | 치료 / 치료 | | Core `Doctor.labelShort` and Keyed `WorkTagCaring` are the same word, so "doctor work" and "caring work" render alike |
| infection / disease / missing body part / wound | 감염 / 질병 / 신체 누락 / 상처 | | Core `WoundInfection.label`, `Disease_*` letters, `MissingBodyPart.label`, `WoundInfection.description` |
| pain (stat) / pain shock | 통증 / 고통에 의한 실신 | | Core Keyed `Pain`, `PainShock`; Core's `Pain` hediff stages say 고통 (가벼운 고통), so both words are vanilla |
| downed / hostile | 쓰러짐 (쓰러진) / 적대 | | Core `Downed.label`, Keyed `Hostile` |
| casting time / range / line of sight required | 시전 시간 / 사거리 / 시야 필요 | | Core Keyed `AbilityCastingTime`, `Range`, `AbilityRequiresLOS` |
| power armor (in prose) | 동력 갑옷 | 파워 아머 | Core `Apparel_PowerArmor.description`; the item's label is 해병대 갑옷 |
| Mote (an inherited `MoteBase` label) | 모트 | | Odyssey `Mote_*` labels, 7 of 7; Core leaves all 59 of its `Mote_*` labels in English, so Odyssey's is the only Korean form vanilla ships |
| trait description tokens | `{PAWN_nameDef}(은)는` / `{PAWN_pronoun}는` / `{PAWN_objective}` bare | | Core trait descriptions; Grammar `ProhimObj` = 그를, so `{PAWN_objective}` already carries its 를 and takes no particle |
| Blue / Green / Pink | 파란색 / 녹색 / 분홍색 | | Core Keyed `Blue`, `Green`; no `Pink` key, `Hair_Pink.label` (분홍색 머리카락) |

## Grounded common vocabulary, VFE Pirates warcasket domain (RimWorldKorea RMK pack + Core, 2026-10-28)

VFE Pirates ships English only. The community translation these terms were
grounded against is the RimWorldKorea `RMK` pack (GitHub RimWorldKorea/RMK,
its VFE Pirates folder under `Data/Vanilla Expanded/`, Workshop id 2723801948,
`1.6/Languages/Korean (한국어)/`): VFE Pirates' ThingDef, WarcasketDef and
Keyed files. Its warcasket set labels follow `<bare set prefix> 워캐스킷 [어깨|헬멧]`
and every set description opens with `우주시대 기술로 특화된 워캐스킷
...입니다.`; the family copies both patterns, so the sets read like VFEP's own.
Every warcasket set in the family (Shipcracker, Toxin, Medic, Overlord)
renders these terms alike so the sets read as one family in-game; a change is
made here first and each set's shipped files follow at its next pass. A set's
own name, its Workshop title and its own coinages stay in that repo's
glossary.

| English | Use | Why |
|---|---|---|
| warcasket | 워캐스킷 | RMK VFEP, every warcasket label. No separate word for "shell": RMK drops it (`...워캐스킷입니다.`), and so does the family. |
| `<set>` warcasket / shoulders / helmet (label pattern) | `<prefix>` 워캐스킷 / `<prefix>` 워캐스킷 어깨 / `<prefix>` 워캐스킷 헬멧 | RMK `VFEP_Warcasket*_*.label`; the prefix is the bare set name (돌격, 수호, ...). |
| pauldrons / shoulders / shoulder pads | 워캐스킷 어깨 | RMK `VFEP_WarcasketShoulders_*.label`; "pauldrons" in a description is rendered the same way (`워캐스킷 어깨입니다.`). |
| helmet (warcasket helmet) | 워캐스킷 헬멧 | RMK `VFEP_WarcasketHelmet_*.label`. |
| warcasket shell | 워캐스킷 (no separate word) | RMK drops "shell" (see the warcasket row); the torso piece reads as the bare 워캐스킷, and Toxin's shipped prose says `워캐스킷의 탱크` where it must tell the shell from the set. |
| warcasket foundry | 워캐스킷 주조대 | RMK `VFEP_WarcasketFoundry.label`; bare "foundries" in lore is `주조대`. |
| entomb / weld on | 안치 (워캐스킷에 안치) | RMK `VFEPirates.EntombInWarcasket`; the Workshop's "welded into" / "weld it on" both use 안치. |
| spacer warcaskets / specialised warcaskets (VFEP research labels, cited in prose) | 우주시대 워캐스킷 / 전문화 워캐스킷 | 전문화 워캐스킷 is RMK `VFEP_SpecialisedWarcaskets.label`; 우주시대 워캐스킷 is Shipcracker's Workshop wording (Core `TechLevel_Spacer` = `우주`). Cited as `'우주시대 워캐스킷' 연구` in ASCII single quotes per this file's research-citation rule. |
| VFEP set names (siegebreaker / brute / guardian / cataphract / hazard / aerial) | 돌격 / 야수 / 수호 / 중무장 / 재해 / 충격 (each as the bare prefix: `돌격 워캐스킷`) | RMK set prefixes (`VFEP_Warcasket_Cataphract.label`, `_Hazard`, `_Aerial`). Aerial is `충격` and Shock is `강습`, which read swapped against their meaning but are what players see in-game; Royalty's `근위대 갑옷` is the vanilla Cataphract armor, not the VFEP set. Controller and sarcophagus are not rendered in any family glossary yet; take RMK's labels when one is needed. |
| 7th generation / 10th generation (VFEP's two chassis); chassis | 7세대 워캐스킷 / 10세대 워캐스킷 (10세대 우주시대 프레임); 프레임 | RMK `10세대 워캐스킷`, and its foundry text `워캐스킷 프레임` for "chassis". |
| Specialized warcasket shell / pauldrons / helmet with superior protection and worse weight (VFEP's 7th-generation opener) | `무게는 늘어났지만 뛰어난 방어력을 갖춘 특화형 워캐스킷[ 어깨\| 헬멧]입니다.` | RMK Cataphract opener `무게는 늘어났지만 뛰어난 방어력을 갖춘 신형 워캐스킷입니다.` with 특화형 for "specialized" (RMK's 7th-gen sets use `특화되었습니다`); Toxin Warcasket's shipped `shortDescription`s. 특화형 is the family's one deviation from the pack's text. |
| Specialized spacer-tech warcasket shell / pauldrons / helmet with standard protection (VFEP's 10th-generation opener) | `우주시대 기술로 특화된 표준적인 방어력의 워캐스킷[ 어깨\| 헬멧]입니다.` | RMK `VFEP_Warcasket*_Siegebreaker.shortDescription`, verbatim (the pack's opening phrase `우주시대 기술로 특화된 워캐스킷 ...입니다.`); Toxin Warcasket's shipped spacer-tier `shortDescription`s. Shipcracker's variant keeps the opener and adds RMK's `개선된 충격 분산 능력` (Guardian/Brute, "improved impact dispersion"). |
| the 7th-generation paragraph (VFEP's lore paragraph on 7th-gen sets) | `7세대 워캐스킷은 기존 성능을 개선하기 위한 연구가 난관에 봉착하자, ...취급되곤 했습니다.` | RMK Aerial/Hazard/Shock descriptions, verbatim; it already reflows the dashed aside into 모듈 방식, no dashes. Toxin Warcasket's shipped 7th-gen descriptions in `1.6/Languages/Korean/`. |
| the 10th-generation paragraph (VFEP's lore paragraph shared by every spacer-tier description) | `10세대 워캐스킷은 사실 노획한 해적 장비를 ...더 자유로운 편입니다.` | RMK 1.6 WarcasketDef, every spacer set's description (Siegebreaker, Guardian, Brute, Controller, Sarcophagus), verbatim; no dashes. The full text is Toxin Warcasket's shipped Keyed `TXWC_SpacerLoreGeneration` in `1.6/Languages/Korean/`. |
| pilot (the wearer) | 조종사 | RMK `VFEP_WarcasketHelmet_Shock` (`조종사의 반응 시간`); every shipped description. |
| spacer armor and insulation / shield bubble / spacer components (what a spacer-tier set carries) | 우주시대 수준의 방어도 / 단열 / 보호막 / 고급 부품 | Core `Insulation_Cold.label` = `단열`, `ShieldBelt.label` (RMK uses 보호막 throughout), `ComponentSpacer.label` = `고급 부품`; the armor phrase is coined around them (the Workshop says 우주시대 수준의 장갑). |

Pending native review for the whole family: nothing open for the RMK rows
(they are the pack's own). The family's deviations from the pack are 특화형
in the 7th-generation opener (Toxin) and the coined 우주시대 수준의 방어도
phrase; the set-specific coinages each repo lists stay pending there.

## Pitfalls and lessons

- **Ground new vocabulary independently — a sibling mod's word for an
  adjacent concept does not automatically transfer.** PWU's and UMW's ko
  passes landed the same week (2026-07-28 / 2026-07) and were cross-checked
  against each other; two terms genuinely diverged between them because each
  was grounded against a different subset of the vanilla tars, even though
  both passes were careful and decompile-informed. Treat a same-family answer
  as a strong hint, not a substitute for checking the actual tar for a mod's
  own domain.
- **The digit-josa fallback is the highest-risk spot in any settings-heavy
  mod.** Because `AlphabetEndPattern` has no digits, a marker placed directly
  after an injected count, percentage, or currency amount silently resolves
  wrong for six digits out of ten (1, 3, 6, 7, 8, 0). Phrase the sentence so
  no particle sits directly against the number, rather than trying to guess
  or special-case it.
- **Curly and corner quotes silently swallow josa resolution.** Because
  `FindLastChar` only skips ASCII `"`, `'` and `)`, wrapping an injected value
  in `" "` or `「 」` and then attaching a marker leaves the raw `(은)는` (or
  similar) visible on screen with no error or warning anywhere in the
  pipeline — this is a purely visual bug that a placeholder-parity checker
  cannot catch, since the placeholder itself is still syntactically intact.
- **No native Korean review exists yet anywhere in the family** as of the
  dates above. Every mod-decided or coined term (as opposed to the
  vanilla-grounded rows in this file) should be flagged for review rather
  than shipped with confidence, and a future native pass should be checked
  against all four mods' own skills, not just this consolidated file, since
  each retains domain-specific vocabulary this file deliberately excludes.

- The RimWorldKorea pack (RMK) carries VFE Pirates under `Data/Vanilla
  Expanded/Vanilla Factions Expanded - Pirates - 2723801948/1.6/Languages/Korean
  (한국어)/` and is fetchable from GitHub; its set names are `중무장`
  (Cataphract), `재해` (Hazard), and it labels Aerial `충격` and Shock `강습`,
  which read swapped against their meaning but are what players see in-game,
  so follow them (2026-10-13, Toxin Warcasket).
- ko Keyed never switches on `CHARGENOUN_gender`, so no `WordInfo/Gender`
  file is ever needed.
- **Toggle frame, family versus vanilla** (Medic Warcasket, 2026-11-05): the
  warcasket family ships `켜면 …. 끄면 …. 기본값: 켜짐.` (Shipcracker
  `SCWC_VacuumBurnDesc`, Toxin, Medic). Vanilla Core/Odyssey tooltips use
  `활성화하면 …. 비활성화하면 ….` (`RespectSystemScaling_Tooltip`,
  `SmoothCameraJumpsDesc`; 활성화하면 18 and 비활성화하면 11 hits against 켜면 1,
  끄면 0), and Core's state words are `Enabled` 활성화됨 / `Disabled` 사용 안 함
  (`On` 켜기 and `Off` 끄기 are toggle verbs). The family frame reads natively,
  so nothing is broken; a native review should rule whether the family moves
  to vanilla's frame. If it does, the change is made here first and every
  warcasket set's toggles follow.

## Generated-text tells

Catalogued 2026-11-05 by Medic Warcasket's first ko pass, from the Core and
Odyssey `Korean (한국어).tar` values with comments stripped (25,968 values,
729k characters; 3,971 description and tooltip values, 285k characters).
Rates are per 100k characters of description and tooltip values unless
noted. Each item is the `English.md` § 2 category as it shows up in Korean,
with the vanilla evidence. Mirrored strings are exempt; descriptions,
settings tooltips and Workshop prose are the slots to read.

1. **One frame on every tooltip.** Vanilla tooltips open on the thing
   itself and close on `-입니다.` (`PainShockThreshold` 심한 고통으로 정신을
   잃는 한계입니다.), so a noun-phrase definition is native. The tell is the
   same definition plus the same trailing consequence sentence on every row
   (…초과분은 사라집니다. on each slider). Vary or cut the second sentence.
2. **여부 openers.** The "Whether" calque is `~할지 여부를 설정합니다`. Vanilla
   has 12 `여부` hits in the whole corpus, 2 of them in toggle tooltips
   (`CommandFireAtWillDesc` 사격 여부를 설정합니다., `CommandToggleAllowAutoRefuelDesc`).
   Vanilla toggles state the effect: `활성화하면 …합니다. 비활성화하면 …합니다.`
   (`RespectSystemScaling_Tooltip`, `SmoothCameraJumpsDesc`; 활성화하면 18,
   비활성화하면 11 hits against 켜면 1). The warcasket family ships `켜면 …. 끄면 ….`
   for the same frame; either reads native, a 여부 opener does not.
3. **Telegraphese.** Two shapes. Nominal endings (`-함.`, `-음.`, `-됨.`)
   in a tooltip or description: vanilla has 0 of 690 Keyed tooltip sentences
   in that form and 0 `함.` in any description; it belongs to battle-log
   `rulesStrings` and stage labels only. And sentences with the modal
   stripped: vanilla spends `수 있습니다` (199) and `것입니다` (25), so a
   paragraph of bare `-합니다.` statements with no `수 있습니다`, `도` or
   `-게 됩니다` reads as a spec sheet.
4. **Chained clauses and aphoristic closers.** The Korean tricolon is a
   sentence that strings three `-고,` / `-며,` clauses before one `-습니다.`
   (vanilla descriptions average 34.9 characters and 0.24 commas per
   sentence; a sentence over about 60 characters with two or more commas is
   worth splitting). The closer is a `~야말로 ~입니다` or `~그 자체입니다` line
   (야말로 4, 그 자체 1 in all of vanilla's descriptions). Vanilla ends on a
   plain statement of use.
5. **Sentence-initial adverbial clauses.** The participle calque is a
   `~하면서,` / `~함으로써,` / `~한 채,` opener hung on a short abstract
   subject (vanilla: 하면서, 3.9, 함으로써 2.1, 한 채 2.1). `~면` and `~ㄹ 때`
   (82.6) are the native openers; use them, or start on the subject.
6. **의-chains and stacked modifiers.** English possessives and hyphen
   compounds come out as `A의 B의 C` (vanilla 8.1 per 100k for a 의…의 run)
   or a long pre-noun relative clause. Name the visible item (어깨의
   아드레날린 주입기, not 어깨에 장착된 워캐스킷의 주입기) or give the modifier its
   own sentence.
7. **Semicolons, dashes and asides.** Vanilla descriptions have 0 `;`, 0
   em or en dashes, and 13.4 non-josa `(` per 100k (most are unit or label
   qualifiers such as 독감 (동물)); the `(이)가`-style markers are 325 and are
   not asides. A `;`, a dash or a `(…)` aside in prose is a tell; split the
   sentence or use `,`. A colon pivot inside prose is rare outside `기본값: {0}.`
   and list heads.
8. **Repeated signature phrases.** The same coined phrase (그 자리에서,
   조금 더 오래, 둔하고 느려지며) in the descriptions, ability text, settings
   and Workshop page. Say it once and plainly elsewhere.
9. **Over-explanation.** A tooltip restating what the row's value or a
   vanilla stat already shows. Vanilla tooltips stop after one or two
   sentences.
10. **Modder vocabulary.** `정의` (definitions) appears in vanilla 15 times,
    never about game content; `def`, `시스템` or `스위트` for an internal
    subsystem never. Name what the player sees: the item's label, 게이지,
    작업 탭.
11. **Calque: English clause order under Korean words.**
    - pronouns the English needs and Korean drops: 그의/그녀의 run at 1.9
      and 그것 at 3.8 per 100k overall, almost all in backstories;
      `그들이 살려야 할`, `그것은`, `당신의` in item or settings prose are
      English subjects carried over. Vanilla's "your" is 내 (34 per 100k in
      descriptions) or nothing;
    - an abstract agent doing a person's verb (이 계획은 …을 알게 되었습니다
      for "the program found"); Korean gives the verb to people (사업단은
      …을 깨달았습니다);
    - English "has" and "through" kept as verbs: `가지고 있습니다` (5.1) and
      `~을 통해` (7.3) where vanilla says `~이 있습니다` or uses the
      instrumental `~(으)로`;
    - `에 의해` passives (6.7) for an English by-agent; vanilla prefers the
      active verb with the agent as subject;
    - plural `들` on every count noun as an English plural (병사들, 부상자들);
      Korean marks plurality only where it matters, and a number or 모두
      already does;
    - `그리고` mid-sentence after a comma to join two conditions (높을수록,
      그리고 …하면): an English "and"; Korean splits the sentence or uses `-고`
      / `-며`.
