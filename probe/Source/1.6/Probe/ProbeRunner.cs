using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Verse;

namespace L10nProbe;

// Orchestrates a probe run: one dump per configured target mod, each written atomically and
// failed loudly (SPEC.md §5). Public because it is the single entry point both triggers call —
// the settings window's "Probe now" button and the startup path (-l10nprobe / probe-on-boot).
//
// Failure contract, per mod: any exception logs an error with the [L10nProbe] prefix (release
// scripts grep for it) and leaves NO output file at that mod's path — the dump is written to a
// temp name and renamed only on success, and a pre-existing file at the target is deleted even
// when the run fails, so a stale-but-complete dump can never masquerade as a fresh one. One
// mod's failure does not stop the others.
public static class ProbeRunner
{
    // Shown in the settings window so a manual run gives feedback without opening the log.
    public static string LastRunSummary;

    // Runs the probe for every configured target and returns a one-line summary (also logged
    // and kept in LastRunSummary). `reason` says which trigger fired, purely for the log.
    public static string RunAll(string reason)
    {
        System.Diagnostics.Stopwatch stopwatch = System.Diagnostics.Stopwatch.StartNew();
        L10nProbeSettings settings = L10nProbeMod.Settings;
        List<string> targets = settings.targetPackageIds.OrderBy(id => id, StringComparer.Ordinal).ToList();
        if (targets.Count == 0)
        {
            string none = "no target mods configured — nothing probed. Tick mods in the L10n Probe settings.";
            Log.Warning($"{L10nProbeMod.LogPrefix} {none}");
            return LastRunSummary = none;
        }

        int written = 0;
        List<string> failed = new List<string>();
        foreach (string packageId in targets)
        {
            string outPath = settings.OutputPathFor(packageId);
            try
            {
                // A configured target that is not active means the dump SET is silently short —
                // exactly the failure mode the probe exists to eliminate — so it is an error,
                // not a skip.
                ModMetaData mod = ModLister.GetActiveModWithIdentifier(packageId)
                    ?? throw new InvalidOperationException("mod is not in the active mod list");
                WriteDump(mod, outPath);
                written++;
                Log.Message($"{L10nProbeMod.LogPrefix} wrote {outPath}");
            }
            catch (Exception e)
            {
                failed.Add(packageId);
                Log.Error($"{L10nProbeMod.LogPrefix} FAILED probing {packageId}: {e}");
                DeleteQuietly(outPath + ".tmp");
                if (DeleteQuietly(outPath))
                {
                    Log.Error($"{L10nProbeMod.LogPrefix} deleted stale {outPath} — a failed probe must not leave output that looks fresh.");
                }
            }
        }

        // Invariant culture so the seconds figure never grows a comma decimal separator.
        string elapsed = stopwatch.Elapsed.TotalSeconds.ToString("F1", System.Globalization.CultureInfo.InvariantCulture);
        string summary = failed.Count == 0
            ? $"probe ({reason}): {written}/{targets.Count} dump(s) written in {elapsed}s."
            : $"probe ({reason}): {written}/{targets.Count} dump(s) written in {elapsed}s; FAILED: {string.Join(", ", failed)} — see log.";
        Log.Message($"{L10nProbeMod.LogPrefix} {summary}");
        return LastRunSummary = summary;
    }

    private static void WriteDump(ModMetaData mod, string outPath)
    {
        SortedDictionary<string, SortedDictionary<string, InjectionEntry>> byDefType = InjectionCollector.Collect(mod);
        string json = ProbeJson.WriteDocument(mod, byDefType);

        // Plain System.IO throughout: per SPEC.md this must also work when the path override
        // points at a WSL UNC path (\\wsl.localhost\...); if that ever proves flaky the
        // fallback is the default Output/ folder, not a different IO stack.
        string dir = Path.GetDirectoryName(outPath);
        if (!dir.NullOrEmpty())
        {
            Directory.CreateDirectory(dir);
        }
        string tmpPath = outPath + ".tmp";
        File.WriteAllText(tmpPath, json, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        if (File.Exists(outPath))
        {
            File.Delete(outPath);
        }
        File.Move(tmpPath, outPath);
    }

    private static bool DeleteQuietly(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
                return true;
            }
        }
        catch (Exception e)
        {
            Log.Error($"{L10nProbeMod.LogPrefix} could not delete {path}: {e.Message}");
        }
        return false;
    }
}
