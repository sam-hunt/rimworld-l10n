using System.Collections.Generic;
using System.IO;
using Verse;

namespace L10nProbe;

// Mod settings: which mods to probe, and where each one's dump goes.
//
// To add a setting:
//  1. declare a public field here (with its default as the initializer),
//  2. persist it in ExposeData with Scribe_Values.Look (pass the same default so an unset
//     value loads correctly), or Scribe_Collections.Look for a collection — which leaves the
//     field NULL on an absent or empty entry, so re-create it after the call,
//  3. restore it in ResetToDefaults,
//  4. surface it in L10nProbeMod.DoSettingsWindowContents.
//
// Everything here is keyed by packageId rather than by ModMetaData/ModContentPack, so a
// stored selection survives a session with that mod unloaded.
public class L10nProbeSettings : ModSettings
{
    // --- Settings fields ---------------------------------------------------

    // packageIds of the mods to dump. Default empty: the probe does nothing until told what
    // to look at. On this machine the family's three mods (shunter.uniquemeleeweapons,
    // shunter.uniqueweaponsunbound, shunter.personaweaponsunbound) are ticked once by hand.
    public HashSet<string> targetPackageIds = new HashSet<string>();

    // packageId -> absolute output file path, overriding DefaultOutputPathFor. The point is
    // writing straight into the probed mod's SOURCE repo rather than its deployed copy; from
    // the Windows-side game that means a WSL UNC path
    // (\\wsl.localhost\<distro>\home\shunt\dev\<Repo>\Scripts\expected-injections.json).
    public Dictionary<string, string> outputPathOverrides = new Dictionary<string, string>();

    // Run the probe on every boot (without quitting), for iterating on the probe itself.
    // The automated path is the -l10nprobe command-line flag instead; see L10nProbe_Startup.
    public bool probeOnEveryBoot;

    public override void ExposeData()
    {
        base.ExposeData();
        Scribe_Collections.Look(ref targetPackageIds, "targetPackageIds", LookMode.Value);
        Scribe_Collections.Look(ref outputPathOverrides, "outputPathOverrides", LookMode.Value, LookMode.Value);
        // Scribe_Collections nulls the field when the stored entry is absent or empty — which
        // is the default state (nothing selected, nothing overridden) — so restore the empty
        // collections rather than carrying a null into the probe.
        targetPackageIds ??= new HashSet<string>();
        outputPathOverrides ??= new Dictionary<string, string>();
        Scribe_Values.Look(ref probeOnEveryBoot, "probeOnEveryBoot", false);
    }

    // Restores every setting to its shipped default. Keep in sync with the field
    // initializers above (and the Scribe_Values.Look defaults).
    public void ResetToDefaults()
    {
        targetPackageIds.Clear();
        outputPathOverrides.Clear();
        probeOnEveryBoot = false;
    }

    // Where dumps go when a mod has no path override: this mod's own deployed folder. Note the
    // local build redeploys by wiping the staged content — the csproj's StageMod target spares
    // Output/ specifically so a dump here survives a rebuild.
    public static string DefaultOutputDir => Path.Combine(L10nProbeMod.ContentPack.RootDir, "Output");

    public string OutputPathFor(string packageId)
    {
        return outputPathOverrides.TryGetValue(packageId, out string overridePath) && !overridePath.NullOrEmpty()
            ? overridePath
            : Path.Combine(DefaultOutputDir, packageId + ".json");
    }
}
