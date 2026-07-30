using Verse;

namespace L10nProbe;

// Runs once on the main thread after all defs are loaded and translations injected — the
// earliest point at which the live DefDatabase is complete, which is the only thing the probe
// looks at. (The Mod constructor is too early: it runs while mod assemblies are still loading,
// before any def exists.)
//
// Once per PROCESS, not per play-data load: StaticConstructorOnStartupUtility.CallAll goes
// through RuntimeHelpers.RunClassConstructor and a type initializer never runs twice. An
// in-process play-data reload (mid-session language change, dev-mode def hot reload) does NOT
// re-run this — irrelevant here, since the automated path quits immediately and the manual path
// is the settings-window button. (Decompile-verified, RimWorld 1.6.)
[StaticConstructorOnStartup]
public static class L10nProbe_Startup
{
    // The command-line flag release scripts drive: launch the game with -l10nprobe and it dumps
    // and quits with no user input. GenCommandLine.CommandLineArgPassed matches both the bare
    // key and "-" + key (decompile-verified), so the leading dash is the caller's convention.
    private const string ProbeArg = "l10nprobe";

    static L10nProbe_Startup()
    {
        bool fromCommandLine = GenCommandLine.CommandLineArgPassed(ProbeArg);
        if (!fromCommandLine && !L10nProbeMod.Settings.probeOnEveryBoot)
        {
            return;
        }

        // Defer past the load long-event rather than probing inside a static constructor: the
        // walker reads the whole def graph, and a shutdown from inside class-initialization
        // would run while the loading screen still owns the main thread.
        LongEventHandler.ExecuteWhenFinished(() =>
        {
            // try/finally, not sequence: ProbeRunner catches per-mod, but an automated run
            // must shut the game down even if the runner itself somehow throws — a release
            // script waiting on the process must never hang at the main menu.
            try
            {
                ProbeRunner.RunAll(fromCommandLine ? "-" + ProbeArg : "probe-on-boot setting");
            }
            finally
            {
                if (fromCommandLine)
                {
                    Log.Message($"{L10nProbeMod.LogPrefix} -{ProbeArg} run complete; shutting down.");
                    Root.Shutdown();
                }
            }
        });
    }
}
