using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using RimWorld.IO;
using Verse;

namespace L10nProbe;

// Names the errors behind the game's one-line "Translation data for language X has N errors.
// Generate translation report for more info." startup warning, for the log dump
// (LogDump.cs, the `translationLoadErrors` section; smoke engine: startup_smoke.py).
//
// Where the N comes from (decompile-verified, 1.6.4871,
// LoadedLanguage.InjectIntoData_AfterImpliedDefs): the active language's own `loadErrors`
// (Keyed/Strings/folder-layout problems, filled once by LoadData) plus every
// DefInjectionPackage's `loadErrors` (one package per def type; cleared and refilled by each
// InjectIntoDefs pass, so by the time the log dump runs they hold the AfterImpliedDefs
// pass, the one that also reports "Found no <type> named <def>"). The warning itself names
// no file and no mod; each list entry names at most the bare file name
// (DefInjection.fileSource is VirtualFile.Name), never the mod that shipped it.
//
// Attribution is therefore rebuilt here from the same directory walk LoadData does
// (LoadedLanguage.AllDirectories, with its per-mod first-load-folder-wins dedup): every
// language file the active language loaded, indexed by def-type folder and file name. An
// error is charged to every indexed file whose name it quotes; when that leaves more than
// one mod (two mods shipping a DefInjected/ThingDef/Apparel.xml is routine), the files are
// read and only those carrying the key the error names are kept. Best effort, never
// authoritative: a record with several sources is one the reader must look at, and one
// with none quotes a file this walk did not see.
internal static class TranslationLoadErrors
{
    private sealed class LangFile
    {
        public VirtualFile File;
        public string PackageId;
        public string ModName;
        public string RelativePath;   // from the mod's root, forward slashes
        public string DefTypeName;    // null for Keyed/Strings files
    }

    private sealed class Record
    {
        public string Scope;          // "language" or "defInjected"
        public string DefType;        // the package's def type name, defInjected only
        public string Text;
        public List<LangFile> Sources = new List<LangFile>();
    }

    // The key an error text names, in the shapes DefInjectionPackage and LoadedLanguage
    // emit (decompile-verified, same build): "Found no T named D to match K (f)",
    // "Duplicate def-injected translation key: K ...", "Duplicate keyed translation key: K
    // in language L", "key=K", "... at path K, ..." / "at path K. (f)", "Both A and B refer
    // to the same field", "K has elements which are not 'li' (f)".
    private static readonly Regex[] KeyPatterns =
    {
        new Regex(@" to match (?<k>[^\s(]+)", RegexOptions.Compiled),
        new Regex(@"translation key: (?<k>[^\s(]+)", RegexOptions.Compiled),
        new Regex(@"key=(?<k>[^\s(]+)", RegexOptions.Compiled),
        new Regex(@" at path (?<k>[^\s,(]+?)\.?(?=[\s,(]|$)", RegexOptions.Compiled),
        new Regex(@"Both (?<k>[^\s(]+) and ", RegexOptions.Compiled),
        new Regex(@"^(?<k>[^\s(]+) has elements which are not", RegexOptions.Compiled),
    };

    // Appends the section's VALUE (an object, or null when no language is active) to `sb`.
    // Throws on any failure; the caller decides how loud to be.
    public static void AppendJson(StringBuilder sb)
    {
        LoadedLanguage language = LanguageDatabase.activeLanguage;
        if (language == null)
        {
            sb.Append("null");
            return;
        }
        List<Record> records = Collect(language);
        sb.Append("{\n");
        sb.Append("    \"language\": ");
        ProbeJson.AppendString(sb, language.FriendlyNameEnglish);
        sb.Append(",\n");
        sb.Append("    \"count\": ").Append(records.Count).Append(",\n");
        sb.Append("    \"errors\": [");
        bool first = true;
        foreach (Record record in records)
        {
            sb.Append(first ? "\n" : ",\n");
            first = false;
            sb.Append("      {\"scope\": ");
            ProbeJson.AppendString(sb, record.Scope);
            sb.Append(", \"defType\": ");
            ProbeJson.AppendString(sb, record.DefType);
            sb.Append(", \"text\": ");
            ProbeJson.AppendString(sb, record.Text);
            sb.Append(", \"sources\": [");
            bool firstSource = true;
            foreach (LangFile source in record.Sources)
            {
                sb.Append(firstSource ? "" : ", ");
                firstSource = false;
                sb.Append("{\"packageId\": ");
                ProbeJson.AppendString(sb, source.PackageId);
                sb.Append(", \"modName\": ");
                ProbeJson.AppendString(sb, source.ModName);
                sb.Append(", \"path\": ");
                ProbeJson.AppendString(sb, source.RelativePath);
                sb.Append('}');
            }
            sb.Append("]}");
        }
        sb.Append(first ? "]\n" : "\n    ]\n");
        sb.Append("  }");
    }

    private static List<Record> Collect(LoadedLanguage language)
    {
        List<LangFile> files = IndexLanguageFiles(language);
        List<Record> records = new List<Record>();
        foreach (string text in language.loadErrors)
        {
            records.Add(new Record { Scope = "language", Text = text });
        }
        foreach (DefInjectionPackage package in language.defInjections)
        {
            foreach (string text in package.loadErrors)
            {
                records.Add(new Record { Scope = "defInjected", DefType = package.defType.Name, Text = text });
            }
        }
        foreach (Record record in records)
        {
            record.Sources = Attribute(record, files);
        }
        return records;
    }

    // Mirrors LoadedLanguage.LoadData's walk: every Keyed, DefInjected and Strings file under
    // each running mod's language folders for this language, skipping a path the same mod
    // already loaded from an earlier (higher-priority) load folder, as TryRegisterFileIfNew
    // does. The def-type folder is resolved exactly as LoadData resolves it (type name, then
    // the name minus a trailing plural 's'); an unresolvable folder is skipped, as the game
    // skips it (and reports it in the language's own loadErrors).
    private static List<LangFile> IndexLanguageFiles(LoadedLanguage language)
    {
        List<LangFile> files = new List<LangFile>();
        Dictionary<ModContentPack, HashSet<string>> seen = new Dictionary<ModContentPack, HashSet<string>>();
        foreach (Tuple<VirtualDirectory, ModContentPack, string> entry in language.AllDirectories)
        {
            VirtualDirectory languageDir = entry.Item1;
            ModContentPack mod = entry.Item2;
            string loadFolder = entry.Item3;
            if (!seen.TryGetValue(mod, out HashSet<string> loaded))
            {
                seen[mod] = loaded = new HashSet<string>();
            }
            foreach (string folder in new[] { "Keyed", "Strings" })
            {
                VirtualDirectory dir = languageDir.GetDirectory(folder);
                if (dir.Exists)
                {
                    AddFiles(files, dir.GetFiles(folder == "Strings" ? "*.txt" : "*.xml", SearchOption.AllDirectories), mod, loadFolder, loaded, null);
                }
            }
            VirtualDirectory defInjected = languageDir.GetDirectory("DefInjected");
            if (!defInjected.Exists)
            {
                continue;
            }
            foreach (VirtualDirectory typeDir in defInjected.GetDirectories("*", SearchOption.TopDirectoryOnly))
            {
                string name = typeDir.Name;
                Type defType = GenTypes.GetTypeInAnyAssembly(name);
                if (defType == null && name.Length > 3)
                {
                    defType = GenTypes.GetTypeInAnyAssembly(name.Substring(0, name.Length - 1));
                }
                if (defType == null)
                {
                    continue;
                }
                AddFiles(files, typeDir.GetFiles("*.xml", SearchOption.AllDirectories), mod, loadFolder, loaded, defType.Name);
            }
        }
        return files;
    }

    private static void AddFiles(List<LangFile> files, IEnumerable<VirtualFile> found, ModContentPack mod, string loadFolder, HashSet<string> loaded, string defType)
    {
        foreach (VirtualFile file in found)
        {
            string fullPath = file.FullPath;
            string loadRelative = fullPath.StartsWith(loadFolder, StringComparison.Ordinal) ? fullPath.Substring(loadFolder.Length) : fullPath;
            if (!loaded.Add(loadRelative))
            {
                continue;
            }
            string rootRelative = fullPath.StartsWith(mod.RootDir, StringComparison.Ordinal) ? fullPath.Substring(mod.RootDir.Length) : fullPath;
            files.Add(new LangFile
            {
                File = file,
                PackageId = ProbeJson.NonUniquePackageId(mod.PackageId),
                ModName = mod.Name,
                RelativePath = rootRelative.TrimStart('/', '\\').Replace('\\', '/'),
                DefTypeName = defType,
            });
        }
    }

    private static List<LangFile> Attribute(Record record, List<LangFile> files)
    {
        // Candidates: files of the error's def type (any file, for a language-scope error)
        // whose full path, or whose bare name as its own token, appears in the text.
        List<LangFile> candidates = files
            .Where(f => record.Scope == "language" ? f.DefTypeName == null : f.DefTypeName == record.DefType)
            .Where(f => record.Text.Contains(f.File.FullPath) || QuotesFileName(record.Text, f.File.Name))
            .ToList();
        if (candidates.Select(c => c.PackageId).Distinct().Count() <= 1)
        {
            return candidates;
        }
        // Several mods ship a file of that name: keep the ones that carry the named key.
        string key = NamedKey(record.Text);
        if (key == null)
        {
            return candidates;
        }
        // A DefInjected key is "<defName>.<field...>" and its element opens "<defName.";
        // a Keyed key is the whole element name.
        string needle = record.Scope == "defInjected" ? "<" + key.Split('.')[0] + "." : "<" + key + ">";
        List<LangFile> narrowed = candidates.Where(c => FileContains(c.File, needle)).ToList();
        return narrowed.Count > 0 ? narrowed : candidates;
    }

    private static bool QuotesFileName(string text, string fileName)
    {
        int at = 0;
        while ((at = text.IndexOf(fileName, at, StringComparison.Ordinal)) >= 0)
        {
            char before = at == 0 ? ' ' : text[at - 1];
            if (!char.IsLetterOrDigit(before) && before != '_' && before != '.' && before != '-')
            {
                return true;
            }
            at += fileName.Length;
        }
        return false;
    }

    private static string NamedKey(string text)
    {
        foreach (Regex pattern in KeyPatterns)
        {
            Match match = pattern.Match(text);
            if (match.Success)
            {
                return match.Groups["k"].Value;
            }
        }
        return null;
    }

    private static bool FileContains(VirtualFile file, string needle)
    {
        try
        {
            return file.ReadAllText().Contains(needle);
        }
        catch (Exception)
        {
            return false;
        }
    }
}
