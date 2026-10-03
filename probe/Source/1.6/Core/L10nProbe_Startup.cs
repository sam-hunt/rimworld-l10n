using Verse;

namespace L10nProbe;

// The two startup-triggered steps of a probe boot, and WHEN each runs. Both are
// LongEventHandler.ExecuteWhenFinished delegates queued during the play-data load long event
// (PlayDataLoader.DoPlayLoad runs inside it), which the handler executes on the main thread,
// in queue order, once that event finishes. The queue order is the whole design
// (decompile-verified, RimWorld 1.6.4871):
//
//   1. delegates queued by Mod constructors (LoadedModManager.LoadAllActiveMods ->
//      CreateModClasses, early in DoPlayLoad) -- QueueStartupProbe's dump pass goes here;
//   2. DoPlayLoad's own: SolidBioDatabase.LoadAllBios, then
//      LanguageDatabase.activeLanguage.InjectIntoData_AfterImpliedDefs, then
//      StaticConstructorOnStartupUtility.CallAll (every mod's [StaticConstructorOnStartup]),
//      then atlas baking and GC;
//   3. delegates queued by those static constructors -- this class's log dump + shutdown.
//
// The dump pass therefore walks a COMPLETE def graph (all of DoPlayLoad's synchronous work
// -- XML load, patches, implied defs, cross-reference resolution, ResolveReferences, short
// hashes -- is done before any delegate runs) at the point where the game itself has
// finished injecting DefInjected translations into non-generated defs
// (InjectIntoData_BeforeImpliedDefs ran synchronously inside DoPlayLoad; the AfterImpliedDefs
// pass only still has implied defs to fill, which the probe skips as `generated`). What has
// NOT happened yet is any mod's static constructor, so a string another mod assigns to our
// def at that time is not in the dump -- correctly, because the game's injection passes are
// already over by then and no translation of such a key could ever load. The case that
// forced this: Vanilla Expanded Framework's ResearchProjectUtility.AutoAssignRules fills
// every research project's null `generalRules` with its own 75-line schematic grammar from
// a static constructor; a late walk attributed those lines to the project's owner and would
// have demanded them of that mod's translators (PersonaWeaponsUnbound, 2026-10-03).
//
// The in-game translation report (LanguageReportGenerator) walks late and WOULD list such
// post-startup values; this is the one deliberate divergence from it, and it is a timing
// choice, not a filter re-implementation (see CLAUDE.md's hard-won constraints).
//
// Why queue from the Mod constructor rather than run there: at construction time no def
// exists yet (assemblies are still loading). Queueing is what gives slot 1; a
// [StaticConstructorOnStartup] type can only ever queue into slot 3, after CallAll.
//
// Two classes, deliberately: StartupProbe (slot 1, no attribute) is what the Mod constructor
// calls; L10nProbe_Startup (slot 3, the attributed type) must never be referenced from the
// Mod constructor, because touching ANY static member of a type with an explicit static
// constructor runs that constructor right there -- [StaticConstructorOnStartup] only adds a
// later call, it does not defer an earlier one. The first cut had the Mod constructor call a
// static method on the attributed class: its cctor fired inside the Mod constructor, queued
// the log dump + shutdown at slot 0, and the boot log dump came out three lines long
// (observed 2026-10-03).
//
// The log dump stays in slot 3 on purpose: it must contain every mod's static-constructor
// output (the family's startup smoke gate reads levels from it), and the shutdown must be the
// last thing the boot does. Slot 1 can't shut the game down either -- the loading screen
// still owns the frame.
//
// Once per PROCESS, not per play-data load: Mod classes are constructed once
// (CreateModClasses skips types already in runningModClasses) and a type initializer never
// runs twice, so an in-process play-data reload (mid-session language change, dev-mode def
// hot reload) re-runs neither step -- irrelevant here, since the automated path quits
// immediately and the manual path is the settings-window button.

// Slot 1 (see the file comment): the dump pass. No attribute; the Mod constructor calls
// QueueFromModConstructor after settings load.
public static class StartupProbe
{
    // The command-line flag release scripts drive: launch the game with -l10nprobe and it dumps
    // and quits with no user input. GenCommandLine.CommandLineArgPassed matches both the bare
    // key and "-" + key (decompile-verified), so the leading dash is the caller's convention.
    public const string ProbeArg = "l10nprobe";

    public static bool FromCommandLine => GenCommandLine.CommandLineArgPassed(ProbeArg);

    public static bool Triggered => FromCommandLine || L10nProbeMod.Settings.probeOnEveryBoot;

    public static string Trigger => FromCommandLine ? "-" + ProbeArg : "probe-on-boot setting";

    public static void QueueFromModConstructor()
    {
        if (!Triggered)
        {
            return;
        }
        LongEventHandler.ExecuteWhenFinished(() =>
        {
            // LongEventHandler catches a throwing delegate itself and goes on to the next, so
            // slot 3's shutdown is not at risk; catching here only puts our prefix on the
            // line, since the release scripts grep for it.
            try
            {
                ProbeRunner.RunAll(Trigger, atStartup: true);
            }
            catch (System.Exception e)
            {
                Log.Error($"{L10nProbeMod.LogPrefix} FAILED startup probe run: {e}");
            }
        });
    }
}

// Slot 3 (see the file comment): the log dump, then the shutdown. Referenced from nowhere;
// StaticConstructorOnStartupUtility.CallAll is what runs this constructor.
[StaticConstructorOnStartup]
public static class L10nProbe_Startup
{
    static L10nProbe_Startup()
    {
        if (!StartupProbe.Triggered)
        {
            return;
        }
        LongEventHandler.ExecuteWhenFinished(() =>
        {
            // try/finally: the log dump's own failure is logged and swallowed inside
            // WriteLogDump, but an automated run must shut the game down whatever happens --
            // a release script waiting on the process must never hang at the main menu.
            try
            {
                // The boot log dump (LogDump.cs) goes AFTER every mod's static constructor and
                // after the slot-1 probe run, so the runner's own FAILED lines are in it, and
                // BEFORE the shutdown marker, so the smoke gate can treat "marker present, dump
                // line absent" as a probe build that predates the dump.
                WriteLogDump(StartupProbe.Trigger);
            }
            finally
            {
                if (StartupProbe.FromCommandLine)
                {
                    Log.Message($"{L10nProbeMod.LogPrefix} -{StartupProbe.ProbeArg} run complete; shutting down.");
                    Root.Shutdown();
                }
            }
        });
    }

    private static void WriteLogDump(string trigger)
    {
        try
        {
            string path = LogDump.Write(LogDump.DefaultPath, trigger);
            // The smoke engine greps for this exact line; keep it in sync with
            // startup_smoke.py's LOG_DUMP_MARKER.
            Log.Message($"{L10nProbeMod.LogPrefix} wrote log dump {path}");
        }
        catch (System.Exception e)
        {
            Log.Error($"{L10nProbeMod.LogPrefix} FAILED writing log dump: {e}");
        }
    }
}
