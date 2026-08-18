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
  `ilspycmd "$RIMWORLD_PATH/RimWorldWin64_Data/Managed/Assembly-CSharp.dll" -t
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
