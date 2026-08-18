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
