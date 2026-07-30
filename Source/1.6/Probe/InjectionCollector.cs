using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Verse;

namespace L10nProbe;

// One expected DefInjected key: either a scalar string field or a string-collection field.
// Exactly one of Scalar/Collection is non-null.
internal sealed class InjectionEntry
{
    public string Scalar;
    public List<string> Collection;
    public bool FullListAllowed;

    // The game's own must-translate verdict (DefInjectionUtility.ShouldCheckMissingInjection,
    // public, decompile-verified 2026-07-31): true iff the in-game report would list this key
    // as missing in a language with no translation files. Entries with required=false are
    // still legal injection points the game will load and use (e.g. single-word labels on
    // fields without [MustTranslate], [MayTranslate] fields) — consumers need them to
    // validate translations that exist in practice.
    public bool Required;

    // The walker's normalizedPath, recorded only when it differs from the suggestedPath used
    // as the key: suggestedPath applies TranslationHandleUtility list handles
    // (comps.HediffComp_GetsPermanent.permanentLabel) where existing translation files may
    // use the equally-valid index form (comps.0.permanentLabel). The game dedups injections
    // by normalizedPath, so this is the alias consumers match legacy keys against.
    public string Normalized;

    public bool IsCollection => Collection != null;
}

// Collects the complete expected DefInjected key set for one mod, def type by def type, by
// running the game's own walker (DefInjectionUtility.ForEachPossibleDefInjection) over the
// live DefDatabase.
//
// Emission policy: every walker hit with translationAllowed on a non-generated def and a
// non-empty current value is emitted — that is the full set of injection points the game
// would actually load a translation into. The game's must-translate filter is NOT applied as
// a cut; it is recorded verbatim per entry as InjectionEntry.Required (collections: true iff
// any element passes, mirroring the per-element check in DefInjectionPackage.MissingInjections).
// The def.generated and empty-value skips mirror ShouldCheckMissingInjection's own guard
// clauses: implied defs never load injections and empty fields have nothing to translate.
//
// A collection is emitted as ONE entry at its suggestedPath carrying ALL current elements —
// consumers need the full list because a full-list <li> translation must match the element
// count unless FullListAllowed ([TranslationCanChangeCount]) is set.
//
// Never re-implement any of the game's semantics (CLAUDE.md hard-won constraint): the
// must-translate verdict, the def-type universe (GenDefDatabase.AllDefTypesWithDatabases —
// the same universe TranslationFilesCleaner generates files for) and def-type naming
// (GenTypes.GetTypeInAnyAssembly, the loader's DefInjected folder-name resolution) all come
// from game code.
internal static class InjectionCollector
{
    // Returns defTypeName -> (suggestedPath -> entry), ordinally sorted at both levels so the
    // serialized output is stable across runs (SPEC.md acceptance criterion 4).
    public static SortedDictionary<string, SortedDictionary<string, InjectionEntry>> Collect(ModMetaData mod)
    {
        var byDefType = new SortedDictionary<string, SortedDictionary<string, InjectionEntry>>(StringComparer.Ordinal);
        foreach (Type defType in GenDefDatabase.AllDefTypesWithDatabases())
        {
            string defTypeName = FolderNameFor(defType);
            DefInjectionUtility.ForEachPossibleDefInjection(
                defType,
                (string suggestedPath, string normalizedPath, bool isCollection, string currentValue,
                 IEnumerable<string> currentValueCollection, bool translationAllowed,
                 bool fullListTranslationAllowed, FieldInfo fieldInfo, Def def) =>
                {
                    if (!translationAllowed || def.generated)
                    {
                        return;
                    }
                    InjectionEntry entry;
                    if (!isCollection)
                    {
                        if (currentValue.NullOrEmpty())
                        {
                            return;
                        }
                        entry = new InjectionEntry
                        {
                            Scalar = currentValue,
                            Required = DefInjectionUtility.ShouldCheckMissingInjection(currentValue, fieldInfo, def),
                        };
                    }
                    else
                    {
                        List<string> values = currentValueCollection.ToList();
                        if (!values.Any(v => !v.NullOrEmpty()))
                        {
                            return;
                        }
                        entry = new InjectionEntry
                        {
                            Collection = values,
                            FullListAllowed = fullListTranslationAllowed,
                            Required = values.Any(v => DefInjectionUtility.ShouldCheckMissingInjection(v, fieldInfo, def)),
                        };
                    }
                    if (normalizedPath != suggestedPath)
                    {
                        entry.Normalized = normalizedPath;
                    }

                    if (!byDefType.TryGetValue(defTypeName, out SortedDictionary<string, InjectionEntry> entries))
                    {
                        entries = new SortedDictionary<string, InjectionEntry>(StringComparer.Ordinal);
                        byDefType.Add(defTypeName, entries);
                    }
                    // The game dedups injections by normalizedPath; a suggestedPath collision here
                    // (e.g. via TKeySystem remapping) would silently drop data in a JSON object,
                    // so keep the first occurrence and say so.
                    if (entries.ContainsKey(suggestedPath))
                    {
                        Log.Warning($"{L10nProbeMod.LogPrefix} duplicate suggestedPath '{suggestedPath}' in {defTypeName} ({mod.PackageId}); keeping the first occurrence.");
                        return;
                    }
                    entries.Add(suggestedPath, entry);
                },
                mod);
        }
        return byDefType;
    }

    // The DefInjected/<folder>/ name the game's language loader would resolve back to this
    // def type: LoadedLanguage feeds folder names to GenTypes.GetTypeInAnyAssembly, which
    // only finds short names in the ignored namespaces (Verse, RimWorld, ...) — a custom
    // namespace's def type must use its full name (e.g. UniqueWeaponsUnbound.TraitCostRuleDef).
    // Round-tripping through the game's own resolver instead of hardcoding that rule.
    private static string FolderNameFor(Type defType)
    {
        return GenTypes.GetTypeInAnyAssembly(defType.Name) == defType ? defType.Name : defType.FullName;
    }
}
