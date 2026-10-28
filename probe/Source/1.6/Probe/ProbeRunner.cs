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
// mod's failure does not stop the others. A target absent from the active mod list is not a
// failure but a skip, logged at Message level with the same stale-output deletion (see RunAll).
public static class ProbeRunner
{
    // Shown in the settings window so a manual run gives feedback without opening the log.
    public static string LastRunSummary;

    // Runs the probe for every configured target and returns a one-line summary (also logged
    // and kept in LastRunSummary). `reason` says which trigger fired, purely for the log.
    // `atStartup` is true only for the slot-1 boot run (L10nProbe_Startup.QueueStartupProbe),
    // the one timing at which the walk sees exactly what the game's translation injection
    // saw; a later run (the settings button) is recorded as such in every dump it writes.
    public static string RunAll(string reason, bool atStartup)
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
        List<string> skipped = new List<string>();
        foreach (string packageId in targets)
        {
            string outPath = settings.OutputPathFor(packageId);
            // A ticked target that is not in this boot's mod list is the normal shape of every
            // family boot, not a failure: a refresh or smoke run pins ONE consumer's minimal
            // list while every sibling stays ticked, so a clean boot used to log one
            // Log.Error per absent sibling (15 on a BionicThumbGuild refresh) and read as
            // broken to anything counting errors. It is a skip at Message level — but its
            // stale output still goes, so a dump from an older boot can never pass as this
            // one's (the refresh engine deletes its own target's file before launching, and
            // refuses any dump whose meta.activeMods is not the pinned list, so the dump SET
            // is never silently short on the consumer's side).
            ModMetaData mod = ModLister.GetActiveModWithIdentifier(packageId);
            if (mod == null)
            {
                skipped.Add(packageId);
                DeleteQuietly(outPath + ".tmp");
                string stale = DeleteQuietly(outPath) ? $"; deleted its stale {outPath}" : "";
                Log.Message($"{L10nProbeMod.LogPrefix} skipped {packageId}: not in the active mod list{stale}");
                continue;
            }
            try
            {
                WriteDump(mod, outPath, collectedAfterStartup: !atStartup);
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
        // "{written}/{active}" counts only the targets this boot could dump; the skipped ones
        // are named so a short set is still visible at a glance, just not as an error.
        string skippedNote = skipped.Count == 0 ? "" : $"; skipped {skipped.Count} inactive: {string.Join(", ", skipped)}";
        string summary = failed.Count == 0
            ? $"probe ({reason}): {written}/{targets.Count - skipped.Count} dump(s) written in {elapsed}s{skippedNote}."
            : $"probe ({reason}): {written}/{targets.Count - skipped.Count} dump(s) written in {elapsed}s{skippedNote}; FAILED: {string.Join(", ", failed)} — see log.";
        Log.Message($"{L10nProbeMod.LogPrefix} {summary}");
        return LastRunSummary = summary;
    }

    private static void WriteDump(ModMetaData mod, string outPath, bool collectedAfterStartup)
    {
        SortedDictionary<string, SortedDictionary<string, InjectionEntry>> byDefType = InjectionCollector.Collect(mod);
        string json = ProbeJson.WriteDocument(mod, byDefType, collectedAfterStartup);

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
