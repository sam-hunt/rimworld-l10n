#!/usr/bin/env python3
# Regression tests for the startup smoke engine's classification layer - the
# part that went blind on RimWorld 1.6 (2026-08-28): Player.log stopped
# carrying stack frames, so every plain Log.Error read as level None - and
# for the 1.7 (Waylith) log, which records the level on every entry. Run
# from the repo root:
#   python3 -m unittest discover -s . -p 'test_*.py'
# Nothing here launches the game or reads a real log: the classification
# tests run over fixture log shapes, and the Launch tests drive launch()
# with the refresh engine's helpers and subprocess.run stubbed.

import contextlib
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

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

# The game's one-line translation warning (LoadedLanguage.InjectIntoData_
# AfterImpliedDefs) and the dump section that names what is behind it
# (TranslationLoadErrors.cs). First entry: the real SOS2 shape on the
# Shipcracker smoke list; second: the same mistake in XTS's own tree; third:
# a language-scope error the walk could not match to a file.
TRANSLATION_WARNING = ("Translation data for language English has 3 errors. "
                       "Generate translation report for more info.")
TRANSLATION_SECTION = {
    "language": "English",
    "count": 3,
    "errors": [
        {"scope": "defInjected", "defType": "ThingDef",
         "text": "Found no Verse.ThingDef named VacskinGland to match VacskinGland.label (VacskinGlandThing.xml)",
         "sources": [{"packageId": "kentington.saveourship2", "modName": "Save Our Ship 2",
                      "path": "1.6/ExpansionPatches/Odyssey/Languages/English/DefInjected/ThingDef/VacskinGlandThing.xml"}]},
        {"scope": "defInjected", "defType": "TraderKindDef",
         "text": "Found no RimWorld.TraderKindDef named XTS_Orbital_Xenogerms to match XTS_Orbital_Xenogerms.label (Traders.xml)",
         "sources": [{"packageId": "shunter.xenogermtraderstock", "modName": "Xenogerm Trader Stock",
                      "path": "1.6/Languages/English/DefInjected/TraderKindDef/Traders.xml"}]},
        {"scope": "language", "defType": None,
         "text": "Duplicate keyed translation key: SomeKey in language English",
         "sources": []},
    ],
}

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

# A RimWorld 1.7 (Waylith) Logs/Player.log: the file header, then one
# timestamped, levelled head line per entry with the message's further
# lines and its "    at ..." frames beneath. The header, the Vulkan WARN
# (a multi-line message before its frames), the two Verse INFO lines and
# the closing line are verbatim from 1.7.4976 rev1043 (frames shortened);
# the ERROR entries are synthesised from the decompiled routing (Verse.Log
# .Error logs at Error under the "Verse" category) in the WARN entry's
# shape, since the verified boot logged no error.
WAYLITH_PATCH_FAILURE_LINE = ("2026-10-13 23:00:55.101  ERROR [Verse] "
                              + XTS_PATCH_FAILURE.split("\n")[0])
LOG_1_7_CHUNK = "\n".join([
    "=== RimWorld by Ludeon Studios log ===",
    "Started:   2026-10-13 23:00:48.861 +13:00",
    "Version:   1.0.0.0",
    "OS:        Microsoft Windows 10.0.19045 (X64)",
    "Runtime:   .NET 10.0.10-waylithclr.dev",
    "Process:   pid 52632",
    "Log file:  C:\\Users\\Sam\\AppData\\LocalLow\\Ludeon Studios\\RimWorld by Ludeon Studios\\Logs\\Player.log",
    "Command:   \"C:\\Program Files (x86)\\Steam\\steamapps\\common\\RimWorld\\RimWorld.dll\"",
    "",
    "2026-10-13 23:00:48.389  WARN [Vulkan] [General] [Loader Message] windows_read_data_files_in_registry: Registry lookup failed to get layer manifest files.",
    "Objects: 1",
    "    [0] VkInstance 0x238c8cbe5b0",
    "    at Brutal.Logging.LogCategory.Warning(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Waylith.Graphics.GraphicsDevice+<>c.<.cctor>b__114_1(String s) [0x0]",
    "2026-10-13 23:00:49.363  INFO [Verse] RimWorld 1.7.4976 rev1043",
    "    at Brutal.Logging.LogCategory.Info(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Verse.Log.Message(String text) [0x19]",
    "    at RimWorld.VersionControl.LogVersionNumber() [0x0]",
    "2026-10-13 23:00:52.432  INFO [Verse] Harmony Mod v3.0.0.0; Harmony library v3.0.0.0-rc.2",
    "    at Brutal.Logging.LogCategory.Info(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Verse.Log.Message(String text) [0x19]",
    "    at HarmonyMod.Main..cctor() [0x21E]",
    "2026-10-13 23:00:55.100  INFO [Verse] [Xenogerm Trader Stock] Mod loaded.",
    "    at Brutal.Logging.LogCategory.Info(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Verse.Log.Message(String text) [0x19]",
    WAYLITH_PATCH_FAILURE_LINE,
    XTS_PATCH_FAILURE.split("\n")[1],
    "    at Brutal.Logging.LogCategory.Error(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Verse.Log.Error(String text) [0x19]",
    "    at Verse.PatchOperation.Complete(String modIdentifier) [0x0]",
    "2026-10-13 23:00:55.102  WARN [Verse] " + FRAMELESS_WARNING,
    "    at Brutal.Logging.LogCategory.Warning(LogString`1 message, String sourceMemberName, String sourceFilePath, Int32 sourceLineNumber) [0x0]",
    "    at Verse.Log.Warning(String text) [0x19]",
    "2026-10-13 23:00:55.103  ERROR [Verse] System.NullReferenceException: Object reference not set to an instance of an object",
    "    at XenogermTraderStock.StockGenerator_Xenogerms.GenerateThings(Int32 forTile, Faction faction) [0x12]",
    "2026-10-13 23:00:55.104  INFO [Verse] Caught exception while loading mod settings data for shunter.x. Generating fresh settings.",
    "    at Verse.Log.Message(String text) [0x19]",
    "2026-10-13 23:01:40.000  INFO [Verse] [L10nProbe] wrote log dump C:\\x\\log-messages.json",
    "    at Verse.Log.Message(String text) [0x19]",
    "2026-10-13 23:24:15.353  INFO Log closed.",
    "",
])


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


class WaylithLog(unittest.TestCase):
    """The 1.7 log: levels come from the file, frames go to the stack."""

    def test_detection(self):
        self.assertTrue(engine.is_waylith_log(LOG_1_7_CHUNK))
        # A log whose header changed still qualifies by its first head line.
        self.assertTrue(engine.is_waylith_log(
            LOG_1_7_CHUNK.split("\n", 9)[9] + "\n"))
        self.assertFalse(engine.is_waylith_log(LOG_1_6_CHUNK))
        self.assertFalse(engine.is_waylith_log(LEGACY_CHUNK))
        self.assertFalse(engine.is_waylith_log(""))

    def test_entries_strip_the_prefix_and_split_frames(self):
        entries = engine.waylith_entries(LOG_1_7_CHUNK)
        self.assertEqual(len(entries), 10)
        vulkan, version, harmony, loaded, patch, warning, raw, settings, dump, closed = entries
        self.assertEqual(vulkan.level, "warning")
        self.assertEqual(vulkan.text.split("\n"), [
            "[General] [Loader Message] windows_read_data_files_in_registry: "
            "Registry lookup failed to get layer manifest files.",
            "Objects: 1", "    [0] VkInstance 0x238c8cbe5b0"])
        self.assertTrue(vulkan.stack.startswith("at Brutal.Logging.LogCategory.Warning("))
        self.assertEqual((version.level, version.text), (None, "RimWorld 1.7.4976 rev1043"))
        self.assertEqual(loaded.text, "[Xenogerm Trader Stock] Mod loaded.")
        # The message is exactly what the game logged: what the dump holds
        # and what OWN_PATTERNS and the dedup by head line compare against.
        self.assertEqual((patch.level, patch.text, patch.count),
                         ("error", XTS_PATCH_FAILURE, 1))
        self.assertEqual(patch.stack.split("\n")[1], "at Verse.Log.Error(String text) [0x19]")
        self.assertEqual((warning.level, warning.text), ("warning", FRAMELESS_WARNING))
        self.assertEqual(raw.level, "error")
        self.assertTrue(engine.EXCEPTION_HEAD.match(raw.text))
        self.assertEqual((closed.level, closed.text, closed.stack), (None, "Log closed.", ""))

    def test_levels_are_the_files_not_the_heuristics(self):
        # An INFO entry whose text would trip the 1.6 heuristics stays info;
        # an ERROR entry with innocuous text is an error.
        entries = engine.entries_from_player_log(LOG_1_7_CHUNK)
        by_text = {engine.first_line(e.text): e.level for e in entries}
        self.assertIsNone(by_text["Caught exception while loading mod settings data "
                                  "for shunter.x. Generating fresh settings."])
        self.assertEqual(by_text[engine.first_line(XTS_PATCH_FAILURE)], "error")
        self.assertEqual([e.level for e in entries if e.level],
                         ["warning", "error", "warning", "error"])

    def test_origin_and_merge_work_on_1_7_entries(self):
        configure(own=["XenogermTraderStock", "[Xenogerm Trader Stock]", "XTS_"])
        entries = engine.entries_from_player_log(LOG_1_7_CHUNK)
        patch = next(e for e in entries if e.text == XTS_PATCH_FAILURE)
        self.assertEqual(engine.classify_origin(patch.text + "\n" + patch.stack), "own")
        # With the dump present only raw exception blocks are merged in, and
        # one the dump already carries is not duplicated.
        dump = [engine.Entry("error", "System.NullReferenceException: Object reference "
                             "not set to an instance of an object", "trace", 1)]
        merged = engine.merge_player_log_exceptions(dump, entries)
        self.assertEqual(len(merged), 1)
        merged = engine.merge_player_log_exceptions([], entries)
        self.assertEqual([engine.first_line(e.text) for e in merged],
                         ["System.NullReferenceException: Object reference not set "
                          "to an instance of an object"])

    def test_markers_are_found_in_a_1_7_log(self):
        self.assertIn(engine.LOG_DUMP_MARKER, LOG_1_7_CHUNK)


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

    # --- unresolved cross-references: attributed by the wanted defName -----

    WANTER_ERROR = ("Could not resolve cross-reference: No Verse.ThingDef named "
                    "Apparel_PrestigeArmor found to give to "
                    "RimWorld.StockGenerator_SingleDef RimWorld.StockGenerator_SingleDef")
    TRYRESOLVE_ERROR = ("Could not resolve cross-reference to Verse.ThingDef "
                        "named Apparel_PrestigeArmor (wanter=Foo)")

    def repo(self, files):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        for rel, text in files.items():
            path = Path(d.name) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        engine._own_xml_texts_cache.clear()
        engine.REPO_ROOT = Path(d.name)
        self.addCleanup(setattr, engine, "REPO_ROOT", None)
        self.addCleanup(engine._own_xml_texts_cache.clear)
        return Path(d.name)

    PATCH = ('<?xml version="1.0" encoding="utf-8"?>\n<Patch><Operation Class="PatchOperationAdd">'
             '<xpath>/Defs/TraderKindDef/stockGenerators</xpath><value><li>'
             '<thingDef>Apparel_PrestigeArmor</thingDef></li></value></Operation></Patch>\n')

    def test_cross_ref_wanted_def_in_own_patch_is_own(self):
        configure()
        self.repo({"Patches/Armor.xml": self.PATCH})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "own")
        # The stack trace appended after the message does not matter.
        self.assertEqual(engine.classify_origin(
            self.WANTER_ERROR + "\nVerse.Log:Error(String)"), "own")

    def test_cross_ref_try_resolve_def_shape_is_own(self):
        configure()
        self.repo({"Patches/Armor.xml": self.PATCH})
        self.assertEqual(engine.classify_origin(self.TRYRESOLVE_ERROR), "own")

    def test_cross_ref_li_and_defname_elements_count(self):
        configure()
        self.repo({"Defs/A.xml": "<Defs><ThingDef><defName>Apparel_PrestigeArmor</defName></ThingDef></Defs>"})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "own")
        self.repo({"Defs/A.xml": "<Defs><TraderKindDef><li>  Apparel_PrestigeArmor </li></TraderKindDef></Defs>"})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "own")

    def test_cross_ref_not_referenced_stays_other(self):
        configure()
        self.repo({"Patches/Armor.xml": self.PATCH.replace("Apparel_PrestigeArmor", "Apparel_Other")})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "other")
        # Substrings do not count: the element text must be exactly the defName.
        self.repo({"Patches/Armor.xml": self.PATCH.replace(
            "Apparel_PrestigeArmor", "Apparel_PrestigeArmor_Extra")})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "other")

    def test_cross_ref_referenced_only_in_languages_or_l10n_stays_other(self):
        configure()
        self.repo({
            "Languages/German/DefInjected/ThingDef/A.xml": self.PATCH,
            "1.6/Languages/French/Keyed/K.xml": self.PATCH,
            "l10n/probe/Dump.xml": self.PATCH,
            ".git/x.xml": self.PATCH,
        })
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "other")

    def test_cross_ref_scan_skips_unparseable_files(self):
        configure()
        self.repo({"Patches/Broken.xml": "<Patch><unclosed>",
                   "Patches/Armor.xml": self.PATCH})
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "own")

    def test_cross_ref_without_repo_root_stays_other(self):
        configure()
        engine.REPO_ROOT = None
        self.assertEqual(engine.classify_origin(self.WANTER_ERROR), "other")

    def test_non_cross_ref_error_is_not_attributed_by_defname(self):
        configure()
        self.repo({"Patches/Armor.xml": self.PATCH})
        self.assertEqual(engine.classify_origin(
            "Failed to find Verse.ThingDef named Apparel_PrestigeArmor."), "other")

    def test_cross_ref_matching_own_pattern_skips_the_scan(self):
        configure(own=["XenogermTraderStock"])
        engine.REPO_ROOT = Path("/nonexistent-repo-root")
        self.addCleanup(setattr, engine, "REPO_ROOT", None)
        with mock.patch.object(engine, "own_xml_texts",
                               side_effect=AssertionError("scanned")):
            self.assertEqual(engine.classify_origin(
                self.WANTER_ERROR + "\n at XenogermTraderStock.Foo"), "own")

    def test_cross_ref_scan_is_cached_per_repo_root(self):
        configure()
        self.repo({"Patches/Armor.xml": self.PATCH})
        with mock.patch.object(engine.ET, "parse", wraps=ET.parse) as parse:
            engine.classify_origin(self.WANTER_ERROR)
            engine.classify_origin(self.TRYRESOLVE_ERROR)
        self.assertEqual(parse.call_count, 1)


class LogDump(unittest.TestCase):

    def write_dump(self, d, messages, capacity=1000, schema=1, translation=None):
        path = Path(d) / "log-messages.json"
        dump = {
            "meta": {"schema": schema, "gameBuild": "1.6.4871 rev591",
                     "trigger": "-l10nprobe", "messageCount": len(messages),
                     "queueCapacity": capacity, "generated": "2026-08-28T00:00:00Z"},
            "messages": messages}
        if translation is not None:
            dump["translationLoadErrors"] = translation
        path.write_text(json.dumps(dump), encoding="utf-8")
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

    def test_translation_load_errors_become_attributed_error_entries(self):
        messages = self.MESSAGES + [
            {"type": "Warning", "repeats": 1, "text": TRANSLATION_WARNING, "stackTrace": "Verse.Log:Warning(String)"}]
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, messages, translation=TRANSLATION_SECTION)
            entries, truncated = engine.load_log_dump(path, self.LOG_WITH_MARKER)
        self.assertFalse(truncated)
        # The queue's own warning is still there; the three synthesised errors follow it.
        self.assertEqual([e.level for e in entries[-4:]], ["warning", "error", "error", "error"])
        sos2, xts, keyed = entries[-3:]
        self.assertEqual(sos2.text.split("\n"), [
            "Translation load error (English, DefInjected/ThingDef): Found no Verse.ThingDef "
            "named VacskinGland to match VacskinGland.label (VacskinGlandThing.xml)",
            "  file: 1.6/ExpansionPatches/Odyssey/Languages/English/DefInjected/ThingDef/VacskinGlandThing.xml "
            "(Save Our Ship 2, kentington.saveourship2)"])
        self.assertTrue(xts.text.startswith("Translation load error (English, DefInjected/TraderKindDef): "))
        self.assertEqual(keyed.text.split("\n"), [
            "Translation load error (English, Keyed/Strings): Duplicate keyed translation key: "
            "SomeKey in language English",
            "  file: not matched to any active mod's language files"])
        self.assertEqual((keyed.stack, keyed.count), ("", 1))

    def test_translation_section_is_optional_and_does_not_count_toward_capacity(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write_dump(d, self.MESSAGES)              # older probe: no section
            entries, _ = engine.load_log_dump(path, self.LOG_WITH_MARKER)
            self.assertEqual(len(entries), len(self.MESSAGES))
            path = self.write_dump(d, self.MESSAGES, translation=None)
            (Path(d) / "null.json").write_text(
                path.read_text(encoding="utf-8").replace('"messages"', '"translationLoadErrors": null, "messages"'),
                encoding="utf-8")
            entries, _ = engine.load_log_dump(Path(d) / "null.json", self.LOG_WITH_MARKER)
            self.assertEqual(len(entries), len(self.MESSAGES))    # probe failed to collect: null
            # Five messages at a capacity of six: not truncated, however many
            # translation errors ride along.
            path = self.write_dump(d, self.MESSAGES, capacity=6, translation=TRANSLATION_SECTION)
            entries, truncated = engine.load_log_dump(path, self.LOG_WITH_MARKER)
        self.assertFalse(truncated)
        self.assertEqual(len(entries), len(self.MESSAGES) + 3)

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

    def test_translation_load_errors_gate_by_their_attributed_source(self):
        # The SOS2 entry is third-party (reported, not gated); the XTS one is
        # own (its def prefix is in the text, and so are its mod name and
        # packageId) and gates; the unmatched keyed one is other.
        configure(own=["XenogermTraderStock", "[Xenogerm Trader Stock]", "XTS_"])
        entries = [engine.Entry("warning", TRANSLATION_WARNING, "", 1)]
        entries += engine.translation_error_entries(TRANSLATION_SECTION)
        hard, gated, out = self.run_report(entries)
        self.assertEqual([f[1] for f in hard], ["own"])
        self.assertEqual([f[1] for f in gated], ["other", "own", "other"])
        self.assertIn("3 error(s), 1 warning(s) in the boot log", out)
        self.assertIn("3 of the errors are the translation load errors behind the game's", out)
        self.assertIn("[own]\nTranslation load error (English, DefInjected/TraderKindDef)", out)
        self.assertIn("  file: 1.6/Languages/English/DefInjected/TraderKindDef/Traders.xml "
                      "(Xenogerm Trader Stock, shunter.xenogermtraderstock)", out)
        self.assertIn("[other] " + TRANSLATION_WARNING, out)

    def test_integration_mod_translation_error_gates_through_its_name(self):
        configure(own=["XenogermTraderStock", "XTS_"],
                  integration={"SOS2": ["SaveOurShip2", "kentington.saveourship2"]})
        hard, gated, out = self.run_report(engine.translation_error_entries(TRANSLATION_SECTION)[:1])
        self.assertEqual([f[1] for f in hard], ["integration:SOS2"])

    def test_clean_boot_with_only_tooling_errors_passes(self):
        configure()
        entries = [engine.Entry("error", PROBE_FAILED, "", 1)] * 8
        hard, gated, out = self.run_report(entries)
        self.assertEqual((hard, gated), ([], []))
        self.assertIn("8 error(s), 0 warning(s) in the boot log (8 tooling error(s) excluded from the gate).", out)



class Launch(unittest.TestCase):
    # launch() is the one path the fixture tests cannot reach, and the one
    # that broke: it pins the mod list through the refresh engine's helpers,
    # so a signature change there has a caller outside refresh/. These stub
    # the game and check what reached ModsConfig.xml and what was restored.

    ORIGINAL = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<ModsConfigData>\n"
        "  <version>1.6.4871 rev591</version>\n"
        "  <activeMods>\n"
        "    <li>ludeon.rimworld</li>\n"
        "    <li>some.personal.mod</li>\n"
        "  </activeMods>\n"
        "  <knownExpansions>\n"
        "    <li>ludeon.rimworld.odyssey</li>\n"
        "  </knownExpansions>\n"
        "</ModsConfigData>\n")
    SMOKE_LIST = ["brrainz.harmony", "ludeon.rimworld",
                  "shunter.xenogermtraderstock", "shunter.l10nprobe"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.rw = d / "rw"
        (self.rw / "Mods" / "L10nProbe" / "Output").mkdir(parents=True)
        self.dump = engine.log_dump_path(self.rw)
        self.dump.write_text("stale dump", encoding="utf-8")
        user = d / "user"
        (user / "Config").mkdir(parents=True)
        self.mc = user / "Config" / "ModsConfig.xml"
        self.mc.write_text(self.ORIGINAL, encoding="utf-8")
        # A 1.6 install unless a test says otherwise: the exe decides.
        (self.rw / "RimWorldWin64.exe").touch()
        self.user = user
        self.log = user / "Player.log"
        self.log.write_text("stale log", encoding="utf-8")
        engine.SMOKE_ACTIVE_MODS = list(self.SMOKE_LIST)

    def tearDown(self):
        self.tmp.cleanup()

    def run_launch(self, fake_run):
        with mock.patch.object(engine.refresh, "game_is_running", lambda: False), \
                mock.patch.object(engine.refresh, "modsconfig_path", lambda: self.mc), \
                mock.patch.object(engine.subprocess, "run", fake_run), \
                contextlib.redirect_stdout(io.StringIO()):
            engine.launch(self.rw, self.log)

    def test_launch_pins_the_smoke_list_and_restores_the_original(self):
        seen = {}

        def fake_run(cmd, cwd=None, check=False):
            seen["cmd"], seen["cwd"] = cmd, cwd
            seen["pinned"] = self.mc.read_text(encoding="utf-8")
            seen["stale_log_gone"] = not self.log.exists()
            seen["stale_dump_gone"] = not self.dump.exists()

        self.run_launch(fake_run)
        root = ET.fromstring(seen["pinned"])
        self.assertEqual([li.text for li in root.find("activeMods")], self.SMOKE_LIST)
        self.assertEqual(root.find("version").text, "1.6.4871 rev591")
        self.assertEqual([li.text for li in root.find("knownExpansions")],
                         ["ludeon.rimworld.odyssey"])
        self.assertEqual(seen["cmd"], ["./RimWorldWin64.exe", "-l10nprobe"])
        self.assertEqual(seen["cwd"], self.rw)
        self.assertTrue(seen["stale_log_gone"])
        self.assertTrue(seen["stale_dump_gone"])
        self.assertEqual(self.mc.read_bytes(), self.ORIGINAL.encode("utf-8"))

    def test_launch_sets_the_pinned_mods_settings_aside(self):
        # The settings dimension of the pinned boot reaches launch() through
        # the refresh engine's context manager, like the mod list does.
        about = self.rw / "Mods" / "XenogermTraderStock" / "About"
        about.mkdir(parents=True)
        (about / "About.xml").write_text(
            "<ModMetaData><packageId>shunter.xenogermtraderstock</packageId>"
            "</ModMetaData>", encoding="utf-8")
        cfg = self.user / "Config" / "Mod_XenogermTraderStock_XenogermTraderStockMod.xml"
        cfg.write_text("<toggled/>", encoding="utf-8")
        seen = {}

        def fake_run(cmd, cwd=None, check=False):
            seen["cfg_gone"] = not cfg.exists()

        self.run_launch(fake_run)
        self.assertTrue(seen["cfg_gone"])
        self.assertEqual(cfg.read_text(encoding="utf-8"), "<toggled/>")

    def test_launch_restores_the_original_when_the_game_fails_to_start(self):
        def fake_run(cmd, cwd=None, check=False):
            raise OSError("WSL interop unavailable")

        with self.assertRaises(OSError):
            self.run_launch(fake_run)
        self.assertEqual(self.mc.read_bytes(), self.ORIGINAL.encode("utf-8"))

    def test_player_log_path_does_not_need_the_file_to_exist(self):
        self.log.unlink()
        with mock.patch.object(engine.refresh, "modsconfig_path", lambda: self.mc):
            self.assertEqual(engine.player_log_path(self.rw), self.log)

    def test_a_1_7_install_launches_its_exe_and_reads_logs_player_log(self):
        # After a branch switch both exes' logs can exist on disk; the
        # install under RIMWORLD_PATH decides, never the newer file.
        (self.rw / "RimWorldWin64.exe").unlink()
        (self.rw / "RimWorld.exe").touch()
        (self.user / "Logs").mkdir()
        with mock.patch.object(engine.refresh, "modsconfig_path", lambda: self.mc):
            log = engine.player_log_path(self.rw)
        self.assertEqual(log, self.user / "Logs" / "Player.log")
        seen = {}

        def fake_run(cmd, cwd=None, check=False):
            seen["cmd"] = cmd

        self.run_launch(fake_run)
        self.assertEqual(seen["cmd"], ["./RimWorld.exe", "-l10nprobe"])

    def test_launched_run_that_wrote_no_log_is_a_failed_boot(self):
        configure()

        def fake_launch(rw, log):
            log.unlink(missing_ok=True)

        out = io.StringIO()
        with mock.patch.object(engine, "PACKAGE_ID", "shunter.xenogermtraderstock"), \
                mock.patch.object(engine, "REPO_ROOT", None), \
                mock.patch.object(engine.refresh, "rimworld_path", lambda: self.rw), \
                mock.patch.object(engine.refresh, "modsconfig_path", lambda: self.mc), \
                mock.patch.object(engine, "launch", fake_launch), \
                mock.patch.object(sys, "argv", ["smoke"]), \
                contextlib.redirect_stdout(out), \
                self.assertRaises(SystemExit) as cm:
            engine.main()
        self.assertIn("Boot did not complete", str(cm.exception))
        self.assertIn("never written", str(cm.exception))
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
