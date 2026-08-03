using System.Collections.Generic;
using UnityEngine;
using Verse;

namespace L10nProbe;

// Mod entry point. Wires up settings; nothing else happens here — the Mod constructor runs
// while mod assemblies are still loading, before any def exists, so all probe work is
// deferred to L10nProbe_Startup (post-def-load).
//
// No Harmony: the probe patches nothing (see the csproj comment for why that is a rule
// rather than an accident).
public class L10nProbeMod : Mod
{
    public static L10nProbeSettings Settings { get; private set; }

    // This mod's own content pack. RootDir is the deployed mod folder, which is the base of
    // the default output path — the only location the probe can write to without being told
    // one (see L10nProbeSettings.DefaultOutputDir).
    public static ModContentPack ContentPack { get; private set; }

    // Prefix for every log line this mod emits, per SPEC.md ("fail loudly"): a release
    // script greps for it, so it is a constant rather than a literal per call site.
    public const string LogPrefix = "[L10nProbe]";

    // "Probe now" result, kept across window redraws (the window is torn down and rebuilt
    // most frames it's open). Seeded from ProbeRunner.LastRunSummary so a summary from an
    // earlier -l10nprobe/boot run — or a previous time this window was open — still shows.
    private string lastRunSummary;

    // Scroll position + last-measured content height for the mod list, per the standard
    // RimWorld settings idiom: the view Rect passed to BeginScrollView needs a height up
    // front, but that height depends on how many rows get drawn, which is only known after
    // drawing them — so each frame draws against last frame's measurement and remeasures.
    private Vector2 modListScrollPosition;
    private float modListViewHeight = 100f;

    public L10nProbeMod(ModContentPack content) : base(content)
    {
        ContentPack = content;
        Settings = GetSettings<L10nProbeSettings>();
    }

    public override void DoSettingsWindowContents(Rect inRect)
    {
        const float resetButtonHeight = 30f;
        const float resetButtonGap = 6f;

        // Reserve the bottom strip for "Reset to defaults" up front so it never overlaps the
        // scrollable content, and keep it half-width + centered so a stray click doesn't land
        // on it while scrolling the mod list above.
        Rect resetRect = new Rect(inRect.x + inRect.width / 4f, inRect.yMax - resetButtonHeight, inRect.width / 2f, resetButtonHeight);
        Rect mainRect = inRect;
        mainRect.height -= resetButtonHeight + resetButtonGap;

        Listing_Standard listing = new Listing_Standard();
        listing.Begin(mainRect);
        listing.maxOneColumn = true;

        listing.CheckboxLabeled("Probe on every game boot (no quit)", ref Settings.probeOnEveryBoot);
        listing.SubLabel("The automated path is the -l10nprobe command-line flag instead.", 1f);
        listing.Gap();

        if (listing.ButtonText("Probe now"))
        {
            lastRunSummary = ProbeRunner.RunAll("manual");
        }
        string summaryToShow = lastRunSummary ?? ProbeRunner.LastRunSummary;
        if (!summaryToShow.NullOrEmpty())
        {
            listing.SubLabel(summaryToShow, 1f);
        }
        listing.GapLine();

        DrawModList(listing, mainRect);

        listing.End();

        if (Widgets.ButtonText(resetRect, "Reset to defaults"))
        {
            Settings.ResetToDefaults();
        }
    }

    // Scrollable, load-ordered checkbox list of active mods (self excluded) plus, below them,
    // any previously-selected packageIds that are no longer active — those are kept in
    // Settings (selections deliberately survive the mod being unloaded) but must stay
    // clean-up-able from here.
    private void DrawModList(Listing_Standard listing, Rect mainRect)
    {
        Rect scrollOutRect = listing.GetRect(mainRect.height - listing.CurHeight);
        Rect scrollViewRect = new Rect(0f, 0f, scrollOutRect.width - 16f, modListViewHeight);

        Widgets.BeginScrollView(scrollOutRect, ref modListScrollPosition, scrollViewRect);
        Listing_Standard modListing = new Listing_Standard();
        modListing.Begin(scrollViewRect);
        modListing.maxOneColumn = true;

        var activePackageIds = new HashSet<string>();
        foreach (ModContentPack pack in LoadedModManager.RunningModsListForReading)
        {
            if (pack.PackageId == ContentPack.PackageId)
            {
                continue; // never offer to probe the probe itself
            }
            activePackageIds.Add(pack.PackageId);
            DrawActiveModRow(modListing, pack);
        }

        // Snapshot: DrawStalePackageRow mutates Settings.targetPackageIds on untick, and this
        // loop must not enumerate the live set while that happens.
        foreach (string packageId in new List<string>(Settings.targetPackageIds))
        {
            if (!activePackageIds.Contains(packageId))
            {
                DrawStalePackageRow(modListing, packageId);
            }
        }

        modListViewHeight = modListing.CurHeight;
        modListing.End();
        Widgets.EndScrollView();
    }

    private void DrawActiveModRow(Listing_Standard modListing, ModContentPack pack)
    {
        string packageId = pack.PackageId;
        bool isTargeted = Settings.targetPackageIds.Contains(packageId);
        bool wasTargeted = isTargeted;
        modListing.CheckboxLabeled(pack.Name, ref isTargeted);
        if (isTargeted != wasTargeted)
        {
            if (isTargeted)
            {
                Settings.targetPackageIds.Add(packageId);
                // Ticking a mod here is the memorable half of onboarding it into the l10n
                // flow; the forgettable half is the pinned mod list in each consuming repo's
                // refresh script. Say so at the memorable touchpoint, every time - this is a
                // dev tool, one dialog per tick is cheap and the refresh script's unpinned-
                // target warning is the only other guard.
                Find.WindowStack.Add(new Dialog_MessageBox(
                    $"'{pack.Name}' will now be included in probe dumps.\n\n" +
                    "If a repo's release flow consumes this dump, check CANONICAL_ACTIVE_MODS " +
                    "in its Scripts/refresh-translation-expectations.py: the probe boots on " +
                    "that pinned mod list, and a mod absent from it is simply not loaded, so " +
                    "its dump FAILS. Any DLC or mod the content MayRequires must be pinned " +
                    "too, or the gated defs' keys silently drop out of the expectations."));
            }
            else
            {
                Settings.targetPackageIds.Remove(packageId);
            }
        }
        modListing.SubLabel(packageId, 1f);

        if (isTargeted)
        {
            DrawOutputPathRow(modListing, packageId);
        }
        modListing.Gap(6f);
    }

    // Indented output-path override field for one checked mod. An empty/whitespace field
    // means "no override" and must not persist as an empty string (L10nProbeSettings.
    // OutputPathFor already treats an empty override the same as absent, but storing one
    // anyway would be pointless clutter that survives a ResetToDefaults-free session).
    private void DrawOutputPathRow(Listing_Standard modListing, string packageId)
    {
        modListing.Indent(28f);
        Settings.outputPathOverrides.TryGetValue(packageId, out string overridePath);
        string edited = modListing.TextEntryLabeled("Output path override:", overridePath ?? "");
        if (edited.Trim().Length == 0)
        {
            Settings.outputPathOverrides.Remove(packageId);
        }
        else
        {
            Settings.outputPathOverrides[packageId] = edited;
        }
        if (overridePath.NullOrEmpty())
        {
            modListing.SubLabel("Default: " + Settings.OutputPathFor(packageId), 1f);
        }
        modListing.Outdent(28f);
    }

    // A packageId still in targetPackageIds whose mod isn't currently loaded. Shown greyed
    // out with an explicit "(not active)" marker; unticking removes it from the selection.
    private void DrawStalePackageRow(Listing_Standard modListing, string packageId)
    {
        Color previousColor = GUI.color;
        GUI.color = Color.grey;
        bool stillTargeted = true;
        modListing.CheckboxLabeled(packageId + " (not active)", ref stillTargeted);
        GUI.color = previousColor;
        if (!stillTargeted)
        {
            Settings.targetPackageIds.Remove(packageId);
        }
    }

    // Deliberately not localized: this mod is a local dev tool and never ships, so its own
    // UI strings are plain literals rather than Keyed lookups (SPEC.md non-goals).
    public override string SettingsCategory() => "L10n Probe (dev tool)";
}
