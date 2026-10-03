using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using RimWorld;
using Verse;

namespace L10nProbe;

// Hand-rolled serializer for the probe's output document (SPEC.md §3). Hand-rolled because
// there is no JSON library to use: RimWorld's Managed/ ships no Newtonsoft, and
// UnityEngine.JsonUtility is class-shaped (no dictionaries).
//
// Output contract (consumers diff dumps in git, so this is load-bearing):
//   - byte-identical across runs on an unchanged game+mod set, meta.generated aside:
//     ordinally pre-sorted input, "\n" newlines, two-space indent, invariant culture;
//   - meta.activeDlcs uses ExpansionDef.defName ("Core", "Royalty", ...) in DefDatabase
//     order — defNames are language-independent where labels are not, and database order is
//     the canonical release order rather than an alphabetical resort;
//   - meta.activeMods is every running mod's packageId (lowercase, Steam "_steam" postfix
//     stripped, Core and DLCs included, the probe itself last) in load order — the boot
//     configuration the dump reflects. The refresh engine compares it to the consuming
//     repo's pinned list and refuses a dump from any other boot (a sibling repo's refresh,
//     a smoke test), since a mod that is loaded but not pinned can patch or assign into the
//     probed mod's defs and leak into its expectations;
//   - meta.collectedAfterStartup is emitted only when true: the walk ran after the mods'
//     static constructors (the settings window's "Probe now"), so values other mods assign
//     at runtime may be present. Consumers refuse such a dump; see L10nProbe_Startup;
//   - flag fields ("isCollection", "fullListAllowed", "required") are emitted only when
//     true and "normalized" only when it differs from the entry's key — absent means
//     false/same. See InjectionEntry for what each one carries.
internal static class ProbeJson
{
    public static string WriteDocument(ModMetaData mod, SortedDictionary<string, SortedDictionary<string, InjectionEntry>> byDefType, bool collectedAfterStartup)
    {
        StringBuilder sb = new StringBuilder();
        sb.Append("{\n");

        sb.Append("  \"meta\": {\n");
        sb.Append("    \"gameBuild\": ");
        AppendString(sb, VersionControl.CurrentVersionStringWithRev);
        sb.Append(",\n");
        sb.Append("    \"activeDlcs\": [");
        bool firstDlc = true;
        foreach (ExpansionDef expansion in ModLister.AllExpansions.Where(e => e.Status == ExpansionStatus.Active))
        {
            if (!firstDlc)
            {
                sb.Append(", ");
            }
            AppendString(sb, expansion.defName);
            firstDlc = false;
        }
        sb.Append("],\n");
        sb.Append("    \"modPackageId\": ");
        AppendString(sb, mod.PackageId);
        sb.Append(",\n");
        sb.Append("    \"modName\": ");
        AppendString(sb, mod.Name);
        sb.Append(",\n");
        // After modName and before generated: the refresh engine strips generated and keeps
        // the rest in this order, so a regenerated sidecar stays byte-identical to the ones
        // written when the engine appended activeMods itself.
        sb.Append("    \"activeMods\": [");
        bool firstMod = true;
        foreach (ModContentPack pack in LoadedModManager.RunningModsListForReading)
        {
            if (!firstMod)
            {
                sb.Append(", ");
            }
            AppendString(sb, NonUniquePackageId(pack.PackageId));
            firstMod = false;
        }
        sb.Append("],\n");
        if (collectedAfterStartup)
        {
            sb.Append("    \"collectedAfterStartup\": true,\n");
        }
        sb.Append("    \"generated\": ");
        AppendString(sb, DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture));
        sb.Append("\n  },\n");

        sb.Append("  \"defInjections\": {");
        bool firstType = true;
        foreach (KeyValuePair<string, SortedDictionary<string, InjectionEntry>> typePair in byDefType)
        {
            sb.Append(firstType ? "\n" : ",\n");
            firstType = false;
            sb.Append("    ");
            AppendString(sb, typePair.Key);
            sb.Append(": {");
            bool firstEntry = true;
            foreach (KeyValuePair<string, InjectionEntry> entryPair in typePair.Value)
            {
                sb.Append(firstEntry ? "\n" : ",\n");
                firstEntry = false;
                sb.Append("      ");
                AppendString(sb, entryPair.Key);
                sb.Append(": ");
                AppendEntry(sb, entryPair.Value);
            }
            sb.Append("\n    }");
        }
        sb.Append(firstType ? "}\n" : "\n  }\n");

        sb.Append("}\n");
        return sb.ToString();
    }

    private static void AppendEntry(StringBuilder sb, InjectionEntry entry)
    {
        sb.Append("{ \"english\": ");
        if (entry.IsCollection)
        {
            sb.Append('[');
            for (int i = 0; i < entry.Collection.Count; i++)
            {
                if (i > 0)
                {
                    sb.Append(", ");
                }
                AppendString(sb, entry.Collection[i]);
            }
            sb.Append("], \"isCollection\": true");
            if (entry.FullListAllowed)
            {
                sb.Append(", \"fullListAllowed\": true");
            }
        }
        else
        {
            AppendString(sb, entry.Scalar);
        }
        if (entry.Required)
        {
            sb.Append(", \"required\": true");
        }
        if (entry.Normalized != null)
        {
            sb.Append(", \"normalized\": ");
            AppendString(sb, entry.Normalized);
        }
        sb.Append(" }");
    }

    // ModContentPack.PackageId is already lowercase but carries ModMetaData.SteamModPostfix
    // ("_steam") when a local copy of the same mod is also installed; the pinned lists are
    // written without it, and which copy loaded is not what the comparison is about.
    private static string NonUniquePackageId(string packageId)
    {
        string postfix = ModMetaData.SteamModPostfix;
        return packageId.EndsWith(postfix, StringComparison.Ordinal)
            ? packageId.Substring(0, packageId.Length - postfix.Length)
            : packageId;
    }

    // Emits a JSON string literal (or the null token). Non-ASCII passes through raw — the
    // file is written as UTF-8, and unescaped text diffs better than \u sequences.
    internal static void AppendString(StringBuilder sb, string s)
    {
        if (s == null)
        {
            sb.Append("null");
            return;
        }
        sb.Append('"');
        foreach (char c in s)
        {
            switch (c)
            {
                case '"':
                    sb.Append("\\\"");
                    break;
                case '\\':
                    sb.Append("\\\\");
                    break;
                case '\n':
                    sb.Append("\\n");
                    break;
                case '\r':
                    sb.Append("\\r");
                    break;
                case '\t':
                    sb.Append("\\t");
                    break;
                default:
                    if (c < ' ')
                    {
                        sb.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                    }
                    else
                    {
                        sb.Append(c);
                    }
                    break;
            }
        }
        sb.Append('"');
    }
}
