#!/usr/bin/env python3
# Regression tests for the startup smoke engine's classification layer - the
# part that went blind on RimWorld 1.6 (2026-08-28): Player.log stopped
# carrying stack frames, so every plain Log.Error read as level None. Run
# from the repo root:
#   python3 -m unittest discover -s smoke -p 'test_*.py'
# Pure classification - nothing here launches the game or reads a real log.

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import startup_smoke as engine  # noqa: E402

# --- Fixtures: real 1.6.4871 shapes -----------------------------------------

# The shipped XTS miss: Verse.PatchOperation.Complete under the About.xml
# display name, second line "file: ...". No frames, no blank line after.
XTS_PATCH_FAILURE = (
    '[Xenogerm Trader Stock] Patch operation Verse.PatchOperationAdd('
    '/Defs/TraderKindDef[defName="Orbital_ExoticGoods"]/stockGenerators) failed\n'
    'file: C:\\Program Files (x86)\\Steam\\steamapps\\common\\RimWorld\\Mods'
    '\\XenogermTraderStock\\1.6\\Patches\\Patches_Traders.xml')

# The probe's expected per-mod failure on a smoke list (ProbeRunner.cs): the
# exception's ToString, RimWorld's [Ref] tag, one Mono frame.
PROBE_FAILED = (
    "[L10nProbe] FAILED probing shunter.bettertradersguild: "
    "System.InvalidOperationException: mod is not in the active mod list\n"
    "[Ref 1D216A9]\n"
    "  at L10nProbe.ProbeRunner.RunAll (System.String reason) [0x0009f] "
    "in <cb4e2c301930487fbc8b7de913d65219>:0 ")

# ProbeRunner.RunAll's summary, logged before the log dump is written; a dump
# without it was taken too early (see load_log_dump).
PROBE_SUMMARY = ("[L10nProbe] probe (-l10nprobe): 3/13 dump(s) written in 0.2s; "
                 "FAILED: shunter.bettertradersguild — see log.")

# A mod's own Log.Warning: in the 1.6 file this is just a line of text.
FRAMELESS_WARNING = "[Xenogerm Trader Stock] no xenogerm stock generator matched Orbital_Exotic"

# A raw unhandled exception Unity logged itself (never enters Verse.Log).
RAW_EXCEPTION = (
    "NullReferenceException: Object reference not set to an instance of an object\n"
    "  at XenogermTraderStock.StockGenerator_Xenogerms.GenerateThings "
    "(System.Int32 forTile, RimWorld.Faction faction) [0x00012] in <abc>:0 \n"
    "  at RimWorld.TraderKindDef.ConfigErrors () [0x00030] in <abc>:0 ")

# The legacy (pre-1.6 / stack-trace-enabled) shape the engine was written
# for: message, then column-0 Unity frames, then the (Filename:) locator.
LEGACY_ERROR = (
    "Could not find a type named Foo.Bar\n"
    "UnityEngine.StackTraceUtility:ExtractStackTrace ()\n"
    "Verse.Log:Error(String, Boolean)\n"
    "Verse.ParseHelper:ParseType(String)\n"
    "SomeOtherMod.Loader:Load()\n"
    " \n"
    "(Filename: C:\\buildslave\\unity\\build\\Runtime/Export/Debug/Debug.bindings.h Line: 39)")
LEGACY_WARNING = (
    "Some mod warning\n"
    "UnityEngine.StackTraceUtility:ExtractStackTrace ()\n"
    "Verse.Log:Warning(String, Boolean)\n"
    "SomeOtherMod.Loader:Load()")
LEGACY_PATCHED_ERROR = (
    "Some error\n"
    "UnityEngine.StackTraceUtility:ExtractStackTrace ()\n"
    "Verse.Log.Error_Patch1(String)\n"
    "SomeOtherMod.Loader:Load()")

# A verbatim stretch of a 1.6 smoke-boot Player.log: no blank lines, no
# frames; three messages plus their continuation lines.
LOG_1_6_CHUNK = "\r\n".join([
    "RimWorld 1.6.4871 rev591",
    "Fallback handler could not load library C:/Program Files (x86)/Steam/steamapps/common/RimWorld/RimWorldWin64_Data/MonoBleedingEdge/data-000001572D463050.dll",
    "[Xenogerm Trader Stock] Mod loaded.",
    XTS_PATCH_FAILURE.split("\n")[0],
    XTS_PATCH_FAILURE.split("\n")[1],
    "Unloading 5 Unused Serialized files (Serialized files now loaded: 1)",
    "[L10nProbe] FAILED probing shunter.bettertradersguild: System.InvalidOperationException: mod is not in the active mod list",
    "[Ref 1D216A9]",
    "  at L10nProbe.ProbeRunner.RunAll (System.String reason) [0x0009f] in <cb4e2c301930487fbc8b7de913d65219>:0 ",
    "[L10nProbe] wrote C:\\Program Files (x86)\\Steam\\steamapps\\common\\RimWorld\\Mods\\L10nProbe\\Output\\shunter.xenogermtraderstock.json",
    "Total: 243.610000 ms (FindLiveObjects: 1.154500 ms CreateObjectMapping: 0.610000 ms MarkObjects: 241.592700 ms  DeleteObjects: 0.252700 ms)",
    "",
])

LEGACY_CHUNK = "\n".join([LEGACY_ERROR, "", LEGACY_WARNING, "", "Plain info line", ""])


def configure(own=("XenogermTraderStock", "XTS_"), integration=None):
    engine.OWN_PATTERNS = list(own)
    engine.INTEGRATION_PATTERNS = dict(integration or {})


class ClassifyLevelFallback(unittest.TestCase):
    """Player.log heuristics - what the engine can still tell without the dump."""

    def test_patch_failure_is_error(self):
        self.assertEqual(engine.classify_level(XTS_PATCH_FAILURE), "error")

    def test_probe_failed_probing_is_error(self):
        self.assertEqual(engine.classify_level(PROBE_FAILED), "error")

    def test_raw_exception_block_is_error(self):
        self.assertEqual(engine.classify_level(RAW_EXCEPTION), "error")

    def test_exception_anywhere_is_error(self):
        self.assertEqual(engine.classify_level(
            "Could not load defs for mod shunter.x: System.Xml.XmlException: "
            "'>' is an unexpected token"), "error")

    def test_vanilla_loader_phrasings_are_errors(self):
        for text in [
            "Could not resolve cross-reference: No Verse.ThingDef named Foo found to give to RimWorld.StockGenerator_SingleDef",
            "XML error: <foo>1</foo> doesn't correspond to any field in type ThingDef. Context: <ThingDef>...</ThingDef>",
            "Failed to find Verse.ThingDef named Foo. There are 3000 defs of this type loaded.",
            "Could not find a type named XenogermTraderStock.Missing",
            "Faulty MayRequire at def Foo: ludeon.rimworld.biotch",
            "Adding duplicate Verse.ThingDef name: Foo",
            "Config error in Foo: label is null",
            "Could not load Texture2D at 'Things/Foo' in any active mod or in base resources.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(engine.classify_level(text), "error")

    def test_vanilla_warning_phrasings_are_not_promoted(self):
        for text in [
            "Could not resolve cross-reference: No Verse.SoundDef named Foo found to give to X (using undefined sound instead)",
            "Caught exception while loading mod settings data for shunter.x. Generating fresh settings. The exception was: System.NullReferenceException: x",
            "Could not load shader Foo in resources or mod bundles. Using default shader instead.",
            "Failed to find active mod Foo(shunter.foo) at C:\\x",
            "Reached max messages limit. Stopping logging to avoid spam.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(engine.classify_level(text), "warning")

    def test_frameless_warning_is_invisible_but_not_an_error(self):
        # The documented limitation: without frames or the dump a mod's own
        # Log.Warning is plain text. It must at least not be misread as an
        # error or an info line be promoted.
        self.assertIsNone(engine.classify_level(FRAMELESS_WARNING))
        self.assertIsNone(engine.classify_level("[Xenogerm Trader Stock] Mod loaded."))
        self.assertIsNone(engine.classify_level(
            "[L10nProbe] probe (-l10nprobe): 1/9 dump(s) written in 0.0s; "
            "FAILED: shunter.bettertradersguild - see log."))

    def test_legacy_frame_shapes_still_work(self):
        self.assertEqual(engine.classify_level(LEGACY_ERROR), "error")
        self.assertEqual(engine.classify_level(LEGACY_WARNING), "warning")
        self.assertEqual(engine.classify_level(LEGACY_PATCHED_ERROR), "error")


class SplitEntries(unittest.TestCase):

    def test_1_6_log_splits_per_message_with_continuations(self):
        entries = engine.split_entries(LOG_1_6_CHUNK)
        self.assertIn(XTS_PATCH_FAILURE, entries)
        self.assertIn(PROBE_FAILED, entries)
        self.assertIn("[Xenogerm Trader Stock] Mod loaded.", entries)
        self.assertEqual(len(entries), 8)

    def test_call_shaped_message_starts_its_own_entry(self):
        # A 1.6 message that merely starts like "Type.Method(" is not a frame.
        entries = engine.split_entries("\n".join([
            "[Xenogerm Trader Stock] Mod loaded.",
            "GenSpawn.Spawn(Verse.Thing, Verse.IntVec3, Verse.Map): success",
            "Verse.Log:Error(String, Boolean)",
            "Verse.Foo:Bar (string) [0x00012] in <abc>:0 ",
        ]))
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1].count("\n"), 2)

    def test_legacy_blank_separated_log_drops_locators(self):
        entries = engine.split_entries(LEGACY_CHUNK)
        self.assertEqual(len(entries), 3)
        self.assertNotIn("(Filename:", entries[0])
        self.assertIn("Verse.Log:Error(String, Boolean)", entries[0])
        self.assertEqual(entries[2], "Plain info line")

    def test_levelled_1_6_log(self):
        levels = [(e.level, engine.first_line(e.text))
                  for e in engine.entries_from_player_log(LOG_1_6_CHUNK) if e.level]
        self.assertEqual(levels, [
            ("error", engine.first_line(XTS_PATCH_FAILURE)),
            ("error", engine.first_line(PROBE_FAILED)),
        ])


class ClassifyOrigin(unittest.TestCase):

    def test_xts_patch_failure_is_own(self):
        configure(own=["XenogermTraderStock", "XTS_"])
        self.assertEqual(engine.classify_origin(XTS_PATCH_FAILURE), "own")

    def test_display_name_needed_when_text_lacks_the_assembly_name(self):
        # Display-name-only message (a def-loader error carries no file path).
        text = "[Xenogerm Trader Stock] Patch operation Verse.PatchOperationReplace(/Defs/X) failed"
        configure(own=["XenogermTraderStock", "XTS_"])
        self.assertEqual(engine.classify_origin(text), "other")
        configure(own=["XenogermTraderStock", "[Xenogerm Trader Stock]"])
        self.assertEqual(engine.classify_origin(text), "own")

    def test_probe_failed_is_tooling(self):
        configure()
        self.assertEqual(engine.classify_origin(PROBE_FAILED), "tooling")

    def test_integration_seam_through_stack_frames(self):
        configure(own=["XenogermTraderStock"], integration={"CWTL": ["ChooseWhereToLand"]})
        entry = "NullReferenceException: x\n  at ChooseWhereToLand.Foo.Bar () [0x0] in <a>:0 "
        self.assertEqual(engine.classify_origin(entry), "integration:CWTL")

    def test_display_name_pattern_from_about_xml(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "About").mkdir()
            (Path(d) / "About" / "About.xml").write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n<ModMetaData>\n'
                '  <name>Xenogerm Trader Stock</name>\n'
                '  <packageId>shunter.xenogermtraderstock</packageId>\n'
                '</ModMetaData>\n', encoding="utf-8")
            engine.REPO_ROOT = Path(d)
            try:
                self.assertEqual(engine.display_name_pattern(), "[Xenogerm Trader Stock]")
            finally:
                engine.REPO_ROOT = None
        self.assertIsNone(engine.display_name_pattern())


class LogDump(unittest.TestCase):

    def write_dump(self, d, messages, capacity=1000, schema=1):
        path = Path(d) / "log-messages.json"
        path.write_text(json.dumps({
            "meta": {"schema": schema, "gameBuild": "1.6.4871 rev591",
                     "trigger": "-l10nprobe", "messageCount": len(messages),
                     "queueCapacity": capacity, "generated": "2026-08-28T00:00:00Z"},
            "messages": messages}), encoding="utf-8")
        return path

    MESSAGES = [
        {"type": "Message", "repeats": 1, "text": "[Xenogerm Trader Stock] Mod loaded.", "stackTrace": "No stack trace."},
        {"type": "Error", "repeats": 1, "text": XTS_PATCH_FAILURE, "stackTrace": "Verse.Log:Error(String)\nVerse.PatchOperation:Complete(String)"},
        {"type": "Warning", "repeats": 3, "text": FRAMELESS_WARNING, "stackTrace": "Verse.Log:Warning(String)"},
        {"type": "Error", "repeats": 1, "text": PROBE_FAILED, "stackTrace": "Verse.Log:Error(String)"},
        {"type": "Message", "repeats": 1, "text": PROBE_SUMMARY, "stackTrace": "No stack trace."},
    ]
    LOG_WITH_MARKER = "boot...\n[L10nProbe] wrote log dump C:\\x\\log-messages.json\n"

    def test_dump_levels_by_type_and_carries_repeats(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, self.MESSAGES)
            entries, truncated = engine.load_log_dump(path, self.LOG_WITH_MARKER)
        self.assertFalse(truncated)
        self.assertEqual([e.level for e in entries], [None, "error", "warning", "error", None])
        self.assertEqual(entries[2].count, 3)
        self.assertEqual(entries[1].stack, "Verse.Log:Error(String)\nVerse.PatchOperation:Complete(String)")

    def test_dump_requires_marker_in_this_log(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, self.MESSAGES)
            entries, reason = engine.load_log_dump(path, "boot...\n-l10nprobe run complete; shutting down.\n")
            self.assertIsNone(entries)
            self.assertIn("predates the log dump", reason)
            entries, reason = engine.load_log_dump(Path(d) / "missing.json", self.LOG_WITH_MARKER)
            self.assertIsNone(entries)
            self.assertIn("missing", reason)
            (Path(d) / "odd.json").write_text('{"meta": null, "messages": null}', encoding="utf-8")
            entries, reason = engine.load_log_dump(Path(d) / "odd.json", self.LOG_WITH_MARKER)
            self.assertIsNone(entries)
            self.assertIn("schema", reason)
            (Path(d) / "odd2.json").write_text('{"meta": {"schema": 1}, "messages": [null]}', encoding="utf-8")
            entries, reason = engine.load_log_dump(Path(d) / "odd2.json", self.LOG_WITH_MARKER)
            self.assertIsNone(entries)
            self.assertIn("not shaped", reason)
            path = self.write_dump(d, self.MESSAGES, schema=2)
            entries, reason = engine.load_log_dump(path, self.LOG_WITH_MARKER)
            self.assertIsNone(entries)
            self.assertIn("schema", reason)

    def test_dump_without_probe_summary_is_too_early_to_trust(self):
        # The probe logs its run summary before writing the log dump; a dump
        # that lacks it was taken before the boot it claims to describe.
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, self.MESSAGES[:-1])
            entries, reason = engine.load_log_dump(path, self.LOG_WITH_MARKER)
        self.assertIsNone(entries)
        self.assertIn("too early", reason)

    def test_dump_at_queue_capacity_is_flagged_truncated(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, self.MESSAGES, capacity=5)
            entries, truncated = engine.load_log_dump(path, self.LOG_WITH_MARKER)
        self.assertTrue(truncated)
        self.assertEqual(len(entries), 5)

    def test_player_log_exceptions_merge_without_duplicates(self):
        dump = [engine.Entry("error", "System.NullReferenceException: x\n  at A.B () [0x0] in <a>:0 ", "trace", 1)]
        player_log = engine.entries_from_player_log("\n".join([
            "System.NullReferenceException: x",             # same head: already in the dump
            "  at A.B () [0x0] in <a>:0 ",
            RAW_EXCEPTION,                                   # Unity-only: must be added
            "[Xenogerm Trader Stock] Mod loaded.",           # info: never added
            XTS_PATCH_FAILURE,                               # heuristic error: dump is authoritative, not added
        ]))
        merged = engine.merge_player_log_exceptions(dump, player_log)
        self.assertEqual([engine.first_line(e.text) for e in merged], [
            "System.NullReferenceException: x",
            "NullReferenceException: Object reference not set to an instance of an object",
        ])


class Report(unittest.TestCase):

    def run_report(self, entries):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hard, gated = engine.report(entries)
        return hard, gated, out.getvalue()

    def test_end_to_end_gating_and_summary(self):
        configure(own=["XenogermTraderStock", "[Xenogerm Trader Stock]", "XTS_"])
        entries = [
            engine.Entry(None, "[Xenogerm Trader Stock] Mod loaded.", "", 1),
            engine.Entry("error", XTS_PATCH_FAILURE, "", 1),
            engine.Entry("warning", FRAMELESS_WARNING, "", 3),
            engine.Entry("error", PROBE_FAILED, "", 1),
            engine.Entry("error", PROBE_FAILED.replace("bettertradersguild", "uniquemeleeweapons"), "", 1),
            engine.Entry("error", "Adding duplicate Verse.ThingDef name: SomeOtherModsDef", "", 2),
        ]
        hard, gated, out = self.run_report(entries)
        self.assertEqual([f[1] for f in hard], ["own"])
        self.assertEqual([f[1] for f in gated], ["own", "other"])
        self.assertIn("5 error(s), 3 warning(s) in the boot log (2 tooling error(s) excluded from the gate).", out)
        self.assertIn("[own]\n" + XTS_PATCH_FAILURE, out)
        self.assertIn("[other x2]", out)
        self.assertIn("[own x3] " + FRAMELESS_WARNING, out)

    def test_clean_boot_with_only_tooling_errors_passes(self):
        configure()
        entries = [engine.Entry("error", PROBE_FAILED, "", 1)] * 8
        hard, gated, out = self.run_report(entries)
        self.assertEqual((hard, gated), ([], []))
        self.assertIn("8 error(s), 0 warning(s) in the boot log (8 tooling error(s) excluded from the gate).", out)


if __name__ == "__main__":
    unittest.main()
