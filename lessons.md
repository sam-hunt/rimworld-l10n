# Cross-language lessons

Techniques and engine findings that hold across every language, learned the
hard way across the mod family. Per-language specifics live in
`languages/<Language>.md`; mod-specific terminology lives in each repo's own
glossary. Provenance dates and "decompile-verified" labels are preserved from
the originating passes.

- Wrap injected `{0}` def labels in the language's quote marks (JP 「{0}」,
  RU «{0}», zh-Hans "{0}") — injected labels never inflect, and quoting
  sidesteps case and agreement problems. **But the quote mark is per *slot*,
  not per language**: ja's 「」 marks quoted text (note contents, inscriptions)
  while a UI command the player clicks takes ASCII `"…"`, and zh reaches for
  「」 in exactly that second slot. Same two brackets, opposite assignments —
  find the nearest vanilla analog rather than porting a sibling CJK rule.
  **Korean is a harder exception, and porting the ja form actively breaks
  it**: ko solves the same problem mechanically with josa markers, and
  `FindLastChar` looks through only ASCII `'` `"` `)` to find the syllable
  that decides the particle. Curly `" "` and corner `「 」` are not skipped, so
  `「{0}」(을)를` silently ships an unresolved `(을)를`. Inject bare and mark
  the particle instead.
- **Check whether the worker contracts before writing any contraction
  scaffolding — the answer inverts between languages.** Spanish must fuse
  `de`+`el` by hand (in a rulepack or in any `.Translate()` call using
  `[X_definite]`); French needs **no scaffolding at all**, because
  `LanguageWorker_French.PostProcessed` elides and fuses automatically;
  Portuguese is the worst case, where contractions are mandatory and nothing
  supplies them at all — see the German/Spanish/French/PortugueseBrazilian
  language files for the specifics. **French does not "double-apply", though**
  (verified 2026-08-10 by reimplementing its five regexes and running a whole
  mod's fr tree through them: zero rewrites): the regexes match only the
  *uncontracted* forms, so an already-elided `l'accès` or a hand-written `du`
  passes through untouched — which is exactly how vanilla fr authors its own
  data. The worker is a safety net for text assembled at runtime, not a
  reason to write unnatural French; and because it runs at *load*, before
  argument substitution, it can never help across a `{0}` or `[symbol]`
  anyway. Verify a vanilla pattern actually works before copying it;
  frequency is not correctness (both es and fr ship a demonstrably broken
  contraction in their own combat packs).
- **A "no hidden mechanics" worker is itself a finding, not a reason to
  skip the check — and a language may have no worker at all.** Spanish's and
  Portuguese's workers impose few or no authoring requirements, but
  Portuguese's *absence* of a `PostProcessed` override is precisely what
  makes every contraction the author's problem. **Japanese goes further: no
  `LanguageWorker_Japanese` exists** (verified against the assembly's full
  typedef list, and `LanguageInfo.xml` declares no `languageWorkerClass`), so
  the base worker runs and only merges repeated spaces. The *same* absence
  cuts opposite ways in the two languages — it creates the author's problem
  in pt-BR and removes it in ja — because what matters is whether the
  language's own grammar needs the rewriting, not whether the hook is
  missing. Confirm a worker's existence by enumerating the types, not by
  assuming a major language has one, and note that languages can share one
  worker class (`PortugueseBrazilian` and `Portuguese` both use
  `LanguageWorker_Portuguese`).
- **The possessive symbol (`[X_possessive]`/`Prohis`/`Proher`/`Proits`) has
  a different correct answer per language, so never generalize one.**
  Korean drops it, German keeps and inflects it inline, Spanish keeps it
  only before a singular noun, French and Portuguese both must write the
  possessive literally, for two different underlying reasons. Check
  `Keyed/Grammar.xml`'s actual values for the target language rather than
  assuming the symbol inflects.
- **A def field's official label can differ across the def *types* that
  share its name or concept**, and translating from the wrong one is an
  easy, invisible error (es Core's DamageDef `Stab`=`apuñalamiento` vs
  HediffDef `Stab`=`puñalada`, for instance). When a mod patches or reuses a
  vanilla def, confirm which def *type*'s official label you're grounding
  against, not just the term.
- **When two vanilla files disagree, prefer the nearer analog, not the
  more central one.** es Core's generic ColorDefs render purple `morado`,
  but Odyssey's own colour defs — same def type, same purpose — render it
  `púrpura`. In general: when a mod's required DLC and Core disagree on a
  term in the mod's own domain, the DLC wins.
- **Don't spend a vanilla word on the wrong slot.** Map any concept a mod
  needs against vanilla's existing usage of that word *first* (don't reuse a
  word the domain DLC already spends on a specific concept for something
  else), and coin only for what's genuinely left over.
- **Distinguish comment occurrences from value occurrences when mining the
  tar.** Grepping a symbol across a language's files counts English
  `<!-- EN: -->` text too, which can invert the conclusion about whether a
  symbol is actually used in translated values. Strip comments before
  counting.
- **Check for a `LanguageWorker_<Language>` before generating.** It
  post-processes every string, so it can impose authoring requirements no
  amount of reading the vanilla data will reveal as *mandatory* — Korean's
  josa markers are invisible until you find `ReplaceJosa`. Decompile it:
  `ilspycmd "$RIMWORLD_PATH/Assembly-CSharp.dll" -t
  "Verse.LanguageWorker_<Language>"`. Languages with heavy inflection
  (Russian, Polish, Turkish, Czech, German) are the ones to check first. **A
  worker can also do work *for* you**, which is just as important to
  know — French's elides and contracts automatically, so the correct
  authoring there is to write the uncontracted form and leave it alone.
- **Simulate the worker rather than reasoning about it.** Its regexes are
  short enough to reimplement in a few lines of Python, and running your
  actual strings through them catches what eyeballing does not.
- **Know which resolver your strings actually reach** (decompile-verified).
  `"key".Translate(args)` — every plain Keyed string — goes to
  `Verse.GrammarResolverSimple`, *not* the full rulepack `GrammarResolver`,
  and the two support different things. On a plain `string` arg
  `GrammarResolverSimple` gives you `{N_gender ? … : … : …}`,
  `{N_definite}`, `{N_indefinite}`, `{N_plural}` and the pronoun family —
  gender is looked up from the word itself via `LanguageWordInfo`, so no
  `NamedArgument` metadata is needed. **It also implements the `lookup` and
  `replace` *functions*** — a `{name: args}` span (note the colon) is parsed
  as a function call and dispatched to `LanguageWorker.ResolveFunction`, so
  `{lookup: {0}; Case; 3}` / `{lookup: {0}; decline; N}` reach the target
  language's `TryLookUp` and its `WordInfo` tables from a plain Keyed string
  (this corrected an earlier belief that case forms were unreachable from
  Keyed strings in German). What is genuinely unreachable is anything the
  *rulepack* resolver adds on top. A lookup miss returns the key unchanged
  rather than erroring, so the mechanism is safe to use and degrades to
  nominative — but a mod-coined label is never in the table, so
  restructuring is still right when the injected value is mod-owned.
- **A `lookup` miss does not degrade identically across languages — check
  whether the worker overrides `TryLookUp`** (decompile-verified 2026-08-10).
  The base implementation lowercases only its internal probe key and returns
  the caller's `keyName` untouched on a miss, so a mod-coined label keeps its
  capitalization (this is German's behaviour — it overrides only the article
  helpers, `PostProcessed`, `OrdinalNumber`, `Pluralize` and
  `PostProcessThingLabelForRelic`). `LanguageWorker_Russian` *does* override
  `TryLookUp` and lowercases the key before the lookup, so a ru miss can come
  back lowercased. Same construct, different failure mode.
- **The checker compares argument placeholders, not grammar constructs,
  and that distinction is deliberate.** `{0}`/`{PAWN_labelShort}`-style
  placeholders are supplied by the C# call site and must match English
  exactly; `{PAWN_gender ? o : a}` is inflection the target language needs
  and uninflected English never has. The checker excludes any `{...}`
  containing `?` before comparing (see the comment on
  `GRAMMAR_CONSTRUCT_RE`). Confirm the named argument actually exists at
  the call site before relying on one. **Two constructs are special-cased
  and both are worth knowing before you write one:** `{N_numCase ? … : … : …}`
  is rewritten back to `{N}` first, because it is the only ?-construct that
  prints its argument and therefore legitimately *replaces* the bare
  placeholder (see `NUM_CASE_RE`); and `{lookup: …}` is **not** handled — a
  nested `{lookup: {2}; Case; 3}` compares correctly only because the regex
  finds the inner `{2}`, while `{lookup: [some_symbol]; Case; 1}` reads as one
  invented placeholder and fails. Restructure rather than fight it.
- When an English string is reworded, refresh the EN comments in every
  language **in the same commit** — the checker reports the mismatch as
  STALE either way, but batching avoids churn.
- **Localized acronyms are an easy miss.** es and pt-BR render EMP as PEM
  and fr as IEM, while ja/zh/ko/de keep EMP — look up every acronym as a
  term in its own right rather than passing it through.
- **Register does not transfer, and is not predictable from the language
  family.** Formality level, and the tense/aspect/punctuation conventions of
  job report strings and inspect strings, each have a per-language answer
  that must be read from the target language's own vanilla data — check every
  register axis independently rather than porting a sibling language's rule
  (the per-language files record what each pass found).
- **Counterintuitive material and technical nouns are worth a dedicated
  pass.** chemfuel, plasteel and their kin get non-obvious nativized forms
  per language, and no two languages agree on which get nativized — a single
  mis-grounded technical noun silently poisons every string that restates it.
  (A sharper case of the "don't spend a vanilla word on the wrong slot" and
  portmanteau lessons.)
- Coined vanilla terms may be a portmanteau in one language and a plain
  word in another — always check, never extrapolate between languages.
- Mod-coined terms recur across Keyed prose that restates them. When
  generation is chunked across files or subagents, reconcile those terms
  across the whole language before committing.
- **Two load roots of one mod must never carry the same language-relative
  file path** (decompile-verified 2026-08-19, UMW's zh-Hant pass:
  `Verse.LoadedLanguage.TryRegisterFileIfNew` dedups files per
  ModContentPack by their path under `Languages/<Lang>/`, silently skipping
  the duplicate — and the winner is not determined by LoadFolders order).
  A gated compat root that mirrors the main tree's file names therefore
  shadows whole files with zero errors: UMW's unreleased tree carried 9
  languages whose
  main-tree ThingDef/WeaponTraitDef/ColorDef injections never loaded in-game
  because the Royalty compat root reused `Weapons_Unique.xml`,
  `WeaponTraits.xml` and `Colors.xml`. Neither the game's own load errors,
  the sidecar (it walks defs, not files), nor content-level checks can see
  it — only a file-path collision check can, and the checker engine now has
  one. The in-game tell: one load root's strings translated, the other
  root's English, split exactly along def ownership.

- **CJK labels are single tokens to any keyword matcher.** CJK scripts have
  no word boundaries (no spaces, no hyphens), so any consumer that does
  keyword or substring matching against a CJK label sees the entire label as
  one indivisible token — there is no way to match a "root" or "half" of a
  label the way an English keyword like `bladed` can. Any tool or cross-mod
  integration built on English `labelKeywords`-style matching needs the full
  CJK label as its own list entry per language, and relabeling breaks that
  entry silently: nothing in either side's checker can see the coupling
  (2026-08-26, UWU's zh-Hant `TraitCostRuleDef` rules matching UMW's shipped
  trait labels — UMW's glossary now lists the 21 labels UWU depends on).

- **`LanguageWorker.PostProcessed` runs in exactly one place:
  `GrammarResolverSimple.Formatted`, after argument substitution**
  (decompile-verified on 1.6.4871). Nothing post-processes DefInjected def
  fields or a no-argument `.Translate()`; `DefInjectionPackage` only
  converts `\n`. So every worker rewrite a language relies on (French
  elision, any `PostProcessed` override) applies to formatted Keyed output
  only, and a def label or description must be written in its final form by
  hand. Check `languages/French.md` for the worked case.
- **Free prose is where generated text leaks English syntax; mirrored
  strings do not.** The family's first native-player complaint (Russian,
  LocalMineralScanner, 2026-09-19) called the text rigid and machine-like.
  On review, every in-game string mirrored from a vanilla analog was clean,
  and the complaint traced entirely to the sentences that have no vanilla
  analog to mirror (descriptions, Workshop blurb and FAQ): native words on an
  English skeleton, in Russian's case stacked passives, participial phrases
  and noun chains where a native writer uses a finite active verb and their
  own clause order. Terminology grounding catches vocabulary, never syntax,
  so treat register as a separate gate: after generating, re-read every
  free-prose sentence on its own and ask whether a native writer would have
  built it that way; rewrite with the meaning unchanged. Labels and verbatim
  vanilla reuse are exempt; descriptions, Workshop text and any FAQ or letter
  prose are the slots to check. Each language file records that language's
  own tells as they are found (Russian's are in `languages/Russian.md`).
- **A `{X_plural}` slot resolves through `LanguageWorker.Pluralize`, and
  whether a mod can repair a bad plural depends on whether that worker
  consults the `plural` lookup table** (decompile-verified 2026-10-11 on
  1.6.4871, from a charge-noun relabel in Shipcracker Warcasket).
  `LanguageWordInfo.RegisterLut` assembles each lookup table (`plural`,
  `case`, `decline`, ...) from `WordInfo/<table>.txt` in *every* directory
  of the active language, a mod's own `Languages/<Language>/` folder
  included, keys lowercased, first definition wins; so a mod can ship
  `WordInfo/plural.txt` lines (`singular;plural`) or `case.txt` rows for a
  noun it coined. The loader asks for the lowercased table name plus
  `.txt`, so name the files lowercase (`plural.txt`, `case.txt`): Core's
  Russian `Plural.txt`/`Case.txt` resolve through the tar's case-insensitive
  lookup, which a mod's on-disk file on a case-sensitive filesystem does
  not get. Which workers read the table: English, Spanish and Russian look
  it up before their rules; German delegates to the English worker (lookup,
  else `+s`, so a coined compound like `Treibstoffeinheit` ships as
  `Treibstoffeinheits` without a line, and Core's German `plural.txt` is
  thin, not even `Sprung`); Portuguese overrides no `Pluralize`, so the base
  one runs (lookup, else the word *unchanged*); **French never reads the
  table** (rule-only: `-al`→`-aux`, `-au`/`-eu`→`+x`, s/x/z unchanged, else
  `+s` on the whole string), so a multi-word French noun pluralizes on its
  last word and the only fix is a single-word noun; Japanese, Korean and
  Chinese fall to the base `Pluralize` (lookup, else unchanged), so one
  noun serves every slot. The canonical surface is a reloadable comp's
  `chargeNoun`, which vanilla shows only through `{CHARGENOUN_plural}` and
  `{lookup: ...}` slots in five Keyed strings, where a word-for-word
  "unit of fuel" is the trap. The checker cannot see any of this; the
  glossary row of the noun names the lookup file it relies on.

- **The injection walker reflects the def's runtime type, so a vanilla base
  class's private field is invisible for every subclass def**
  (decompile-verified 2026-10-13 on 1.6.4871, Toxin Warcasket's "spray gas"
  verb). `DefInjectionUtility.FieldsInDeterministicOrder` calls
  `type.GetFields(Instance | Public | NonPublic)` on the def's own type, and
  .NET returns a base class's *private* fields only when asked on that base.
  `ThingDef.verbs` is private, so a plain `ThingDef`'s `verbs.<handle>.label`
  is a key (Biotech's `Apparel_PackTox.verbs.deploy_tox_pack.label`) while
  the same verb on a `VFEPirates.WarcasketDef` never is: the sidecar did not
  list it, a live refresh confirmed it, and the command read English in every
  language. Any mod def that subclasses a vanilla def type inherits this for
  each private `[MustTranslate]` field of the base. The fix is to carry the
  string on something the walker does reach (a comp's own `[MustTranslate]`
  field) and copy it onto the verb in `CompProperties.ResolveReferences`;
  `InjectIntoData_BeforeImpliedDefs` has already injected the mod's own
  defs by then, so the copy carries the translated text.
- **A coined `chargeNoun` may need a Gender line as well as a plural one.**
  Vanilla's German and Castilian reload tooltips switch on
  `{CHARGENOUN_gender ? … : … : …}` (de `Stat_Thing_ReloadPerCharge_Desc`
  and `Stat_Thing_ReloadDestroyOnEmpty_Desc`, es the latter). The game
  resolves the gender from `WordInfo/Gender/{Male,Female,Neuter}.txt` in
  every active language directory, mods included (`LanguageWordInfo.LoadFrom`,
  lowercased lookup, masculine on a miss), and Core's tables list vanilla's
  own nouns (`giftladung`) but never a mod's. So a feminine or neuter coined
  noun ships `1.6/Languages/<Language>/WordInfo/Gender/Female.txt` (one
  lowercased noun per line, no comment lines: `TryLoadFromFile` registers
  every non-empty line verbatim). French, Portuguese, Russian, Korean,
  Japanese and both Chinese Keyed never switch on it (grep
  `CHARGENOUN_gender` over the tar's Keyed before deciding), so no file helps
  there; pt-BR's frames hard-code masculine (`um {CHARGENOUN}`), so prefer a
  masculine coinage. The checker cannot see this; the glossary row of the
  noun names the file. (Shipcracker's `Treibstoffeinheit` and `unidad de
  combustible` shipped without it until 2026-10-13.)
- **Community Vanilla Expanded translation packs are fetchable from GitHub,
  which matters because VFE Pirates ships English only** (Toxin Warcasket's
  nine-language pass, 2026-10-13). Known packs with warcasket files: zh-Hans
  `q847633684/Vanilla-Expanded-ZH` (1.6
  `DefInjected/VFEPirates.WarcasketDef/VFEPirates.WarcasketDef.xml`, also the
  source the zh-Hant pass converts from), ko RimWorldKorea's RMK (`Data/Vanilla
  Expanded/Vanilla Factions Expanded - Pirates - 2723801948/1.6/Languages/Korean
  (한국어)/`), ru `OneCodeUnit/VanillaRussianExpanded`, es Cito2310's pack
  (the Pirates files sit under a `Tribal_Translate/` folder), pt-BR
  `RafaelNaymaier/Traducao-Vanilla-Expanded-PT-BR`
  (`Languages/PortugueseBrazilian/DefInjected/{ThingDef,ResearchProjectDef}/VFE_Pirates_*.xml`).
  German and French have none. Fetch only the two warcasket files with
  `gh api repos/<owner>/<repo>/contents/<path> --jq .content | base64 -d`
  into a scratch directory outside the repo and grep them. The pack's text
  wins for VFEP's own set names and the shared 7th-generation paragraph, so
  the mod reads like VFEP in-game; a vanilla Core term wins over the pack's
  (pt-BR tar `plastiaço` over the pack's `plastoaço`); and a pack's own
  errors are corrected, not copied (es `7ta` is a Latin American ordinal,
  Castilian is `7.ª`).

RulePackDef-specific lessons — which part of speech a
`traitAdjectives`/`namerLabels`-style field needs per language, the several
techniques for solving name-grammar gender (German's inline markers, Spanish's
parallel symbol families, French's rule-level constraints, Portuguese's
literal hedge), and material-neutral trait-adjective phrasing — only apply to
mods that ship RulePackDefs or generate names (UniqueWeaponsUnbound,
UniqueMeleeWeapons, PersonaWeaponsUnbound). They are recorded in the
per-language files here where generic, and in those repos' own skills where
tied to their def types. One pointer worth keeping visible: Core ships
curated word corpora under `Strings/Words/` — check them before coining a
name-grammar noun for any mod that adds name generation.

- **Combat Extended jargon is grounded in CE's own shipped `Languages/`, and
  that ground is patchy.** CE 16.7.4 ships Keyed sets for zh-Hans, zh-Hant,
  fr, ko, pt-BR, ru and es, nothing for ja, and a `German/Keyed/Text.xml`
  that is a stray Achtung! file; fr and ko lack the unit keys
  `CE_MPa`/`CE_mmRHA`. A player in those languages sees CE's own info card
  in English for the units, so a mod's MPa text matches the card by using
  the Latin SI symbol everywhere except zh-Hant (兆帕 / 毫米均質裝甲) and ru
  (МПа / мм RHA). Where CE's wording and Core's differ for a vanilla concept
  (es blindaje vs Core Armadura, zh-Hant 鈍器 vs Core 鈍擊, ko 보호구 관통 vs
  the family's 관통력), Core wins, as for any pack. Per-language rows sit
  under "Grounded common vocabulary". (2026-10-27, Shipcracker Warcasket's
  CE root.)

## Tooling lessons (cross-mod, not language-specific)

- **A RimWorld 1.6 Player.log carries no stack traces, so a `Log.Error` is
  just its message lines.** On 1.6.4871 (Unity 2022.3.35f1, Windows player)
  a full boot log has zero `Verse.Log` frames, zero `StackTraceUtility`
  frames, zero `(Filename: ...)` locators — and no blank line between
  messages either, since that separator came after the trace. Nothing in
  `Assembly-CSharp` calls `SetStackTraceLogType`; it is the player build's
  setting, not a pref. Any tool that infers a log level from frames (the
  family's startup smoke gate did) reads every plain error as info and
  passes a broken XML patch silently — XenogermTraderStock shipped a
  `PatchOperationAdd` against the non-existent `Orbital_ExoticGoods` for its
  whole life while the gate reported a clean boot (found 2026-08-27, fixed
  2026-08-28). The level IS in memory: `Verse.Log.Messages` keeps every
  message as a `LogMessage` with its `LogMessageType`, `repeats` and a
  RimWorld-captured stack trace, and L10nProbe now dumps that queue to
  `Output/log-messages.json` at the end of a `-l10nprobe` boot for the
  smoke engine to read. Player.log is a fallback with message-shape
  heuristics only; a raw unhandled exception Unity logs itself is the one
  thing only Player.log has. (1.6 only: the next lesson has the 1.7 log.)
- **RimWorld 1.7 (the Waylith engine) changed the install layout and the
  log; the game exe present tells the two apart** (verified 2026-10-13 on
  1.7.4976 rev1043, Steam `unstable`). The install is flat: `RimWorld.exe`
  hosts `RimWorld.dll` on .NET 10, `Assembly-CSharp.dll`, `UnityStubs.dll`
  and `Waylith.dll` sit in the install root, and an empty
  `RimWorldWin64_Data/` is left behind; `ilspycmd
  "$RIMWORLD_PATH/Assembly-CSharp.dll" -t <Type>` decompiles it (ilspycmd
  10.1 reads the .NET 10 assembly). The log is `Logs/Player.log` under the
  user data folder, and every entry is a timestamped head line carrying the
  level the game logged at (`Verse.Log.Error` logs `ERROR [Verse] ...`,
  decompile-verified) followed by its stack frames, so the 1.6 heuristics
  above are not needed there; the probe's dump is still the only source of
  the translation load errors. A net472 mod assembly built against the 1.6
  references runs unchanged: `RimWorld.runtimeconfig.json` maps every
  `UnityEngine*` assembly reference onto `UnityStubs` and binds laxly, so
  the probe and the family's 1.6 builds load as-is. The engines read the
  layout from the exe (`refresh.GAME_LAYOUTS`); after a Steam branch switch
  both logs exist on disk, and the install decides which one is read.
- **The game's `Translation data for language X has N errors` warning
  names nothing; the N errors and their files have to be dumped from
  memory.** `LoadedLanguage.InjectIntoData_AfterImpliedDefs` (1.6.4871)
  sums the language's `loadErrors` and every `DefInjectionPackage`'s and
  logs the count alone, pointing at the in-game translation report; the
  underlying strings quote at most a bare file name (`fileSource` is
  `VirtualFile.Name`), never the mod. On ShipcrackerWarcasket's smoke list
  the four behind the warning were Save Our Ship 2's English DefInjected
  entries for `VacskinGland` in its Odyssey expansion-patch root, whose defs
  carry a Royalty `MayRequire` the boot did not satisfy, and the gate could
  only report "4 errors, third-party, probably" (2026-10-05). The probe now
  writes the lists as `translationLoadErrors` in the log dump and attributes
  each to the mod file(s) of that name under the active language (narrowed
  by the named key when several mods share a file name); the smoke engine
  reports each as an error entry of its own, gated by the usual origin
  patterns.
  That is the right level, not the game's Warning: an own-attributed one is
  exactly the unconditional-folder mistake for a gated def, red in every
  player's log.
- **A translation expectation is only real if the game's injection could
  reach it, so walk the def graph before static constructors and refuse a
  dump from a boot you did not pin.** Vanilla Expanded Framework's
  `ResearchProjectUtility.AutoAssignRules` (a `[StaticConstructorOnStartup]`
  pass) hands its 75-line schematic grammar to every non-Anomaly research
  project whose `generalRules` is null; the game's walker charges a field to
  the def's owner, so a late walk made PWU's `PWU_BladelinkCustomization`
  owe 75 `[MustTranslate]` rule strings in eight languages that no
  translation file could ever fill (DefInjected injection is over before
  `CallAll` runs). The dump only reached PWU through `--no-launch` reusing
  a dump from another boot that had VEF active (UMW's refresh pins VEF for
  its warcasket uniques; PWU's own smoke test boots VEF too) while the
  engine stamped PWU's own pinned list onto it. Since 2026-10-03 the probe
  walks from a delegate its `Mod` constructor queues (complete graph, before
  any static constructor), records the real `meta.activeMods`, and the
  refresh engine refuses a dump whose list differs from the repo's pin.
  General rule: every gate a repo's content loads under (MayRequire,
  LoadFolders IfModActive) must be in a pinned boot. Gates that only ADD defs
  can share one list; a gate that adds a field to, or rewrites the text of,
  a def that also loads without it needs a world of its own (next two
  lessons).
- **A compat-root Patch that adds a `[MustTranslate]` field to a main-tree
  def creates a key that exists only behind the gate.** The key sits under
  the main-tree def (ShipcrackerWarcasket's VGE root adds an oxygen comp
  whose `chargeNoun` lands on the main-tree helmet), so def ownership places
  it in the main tree, where it would be a "found no def" startup error on
  every install without the gate. The probe sees the key only in a boot
  with the gate active, and its translation belongs in the gate's own root.
  A refresh shim models this with `WORLDS` (one boot per configuration);
  the checker then demands the key in the root active in exactly the worlds
  that have it.
- **A DefInjected key may be translated in only one load root per
  configuration.** Two roots that load together and carry the same key are
  a logged duplicate, last file wins in an unstable order. So a main-tree
  field whose English differs behind a gate cannot simply get a second
  translation in the gate's root: either the gated text moves to a separate
  field the code selects at runtime, or a replace patch rewrites it and the
  translations split across an `IfModActive`/`IfModNotActive` root pair,
  exactly one of which loads in any configuration.
- **RimWorld attributes patch and def failures to a mod by its About.xml
  display name, not its packageId or assembly**:
  `Verse.PatchOperation.Complete(runningMod.Name)` logs
  `[Xenogerm Trader Stock] Patch operation ... failed`, with the file path
  on a second `file:` line. A smoke shim's `OWN_PATTERNS` therefore needs
  `"[<display name>]"`; the engine now derives it from
  `REPO_ROOT/About/About.xml` (BTG and XTS already listed it; UMW, UWU and
  PWU did not), so the derivation is the safety net and an explicit entry is
  documentation.
- **The smoke engine imports the refresh engine's pin helpers, so a refresh
  signature has a caller outside `refresh/`.** v1.3.0 gave
  `pinned_modsconfig` a `mods` argument and updated every caller in
  `refresh/` but not `smoke/startup_smoke.py`'s `launch()`; on that tag
  every consumer's `integration-smoke-test.py` crashed with a `TypeError`
  after it had already deleted Player.log, and the log lookup, which
  globbed for the file itself, then refused to run until the game had
  written a new one. The suites did not catch it because nothing drove
  `launch()`. Grep all three engine directories for a changed name, and
  keep every cross-engine entry point under a test (the smoke suite's
  `Launch` class drives `launch()` with the game stubbed).
