#!/usr/bin/env python3
# Tests for the checker engine's world model: LoadFolders parsing, per-world
# sidecar views, and main() over fixture repos built in temp dirs. Run from
# the repo root:
#   python3 -m unittest discover -s . -p 'test_*.py'
# Nothing here launches the game; the pin check is skipped via
# L10N_SKIP_PIN_CHECK.

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_translations as engine  # noqa: E402

VGE = "vanillaexpanded.gravship"
BASE_MODS = ["brrainz.harmony", "ludeon.rimworld", "shunter.fixture",
             "shunter.l10nprobe"]
VGE_MODS = ["brrainz.harmony", "ludeon.rimworld", VGE, "shunter.fixture",
            "shunter.l10nprobe"]

DEFS = """<?xml version="1.0" encoding="utf-8"?>
<Defs>
  <ThingDef>
    <defName>FX_Helmet</defName>
    <label>helmet</label>
    <description>A helmet.</description>
  </ThingDef>
</Defs>
"""

CHARGE = "FX_Helmet.comps.0.chargeNoun"


def language_file(entries):
    # entries: [(key, english, translation)] -> a DefInjected file body.
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]
    for key, en, text in entries:
        lines += [f"  <!-- EN: {en} -->", f"  <{key}>{text}</{key}>"]
    return "\n".join(lines + ["</LanguageData>", ""])


def load_folders_xml(extra=""):
    return ('<?xml version="1.0" encoding="utf-8"?>\n<loadFolders>\n'
            "  <v1.6>\n    <li>/</li>\n    <li>1.6</li>\n"
            f"{extra}  </v1.6>\n</loadFolders>\n")


def two_world_sidecar(entries):
    return {
        "meta": {"gameBuild": "1.6.test", "activeDlcs": ["Core"],
                 "modPackageId": "shunter.fixture", "modName": "Fixture",
                 "activeMods": BASE_MODS,
                 "worlds": {"base": {"activeMods": BASE_MODS,
                                     "activeDlcs": ["Core"]},
                            "vge": {"activeMods": VGE_MODS,
                                    "activeDlcs": ["Core"]}}},
        "defInjections": {"ThingDef": entries},
    }


BASE_ENTRIES = {
    "FX_Helmet.description": {"english": "A helmet.", "required": True},
    "FX_Helmet.label": {"english": "helmet", "required": True},
}
MAIN_FRENCH = [("FX_Helmet.label", "helmet", "casque"),
               ("FX_Helmet.description", "A helmet.", "Un casque.")]


class Fixture:
    # A throwaway consumer repo. files: {relative path: text}.
    def __init__(self, files):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text if isinstance(text, str) else
                            json.dumps(text, indent=2), encoding="utf-8")

    def run(self):
        engine.REPO_ROOT = self.root
        engine.REQUIRED_DLCS = set()
        engine.PARITY_EXEMPT_FIELDS = set()
        engine.DEF_TYPE_ALIASES = {}
        engine.ALLOW_NO_KEYED_SURFACE = True
        engine.WORKSHOP_TITLE_KEY = None
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["check"]), \
                mock.patch.dict(os.environ, {"L10N_SKIP_PIN_CHECK": "1"}), \
                contextlib.redirect_stdout(out):
            code = engine.main()
        return code, out.getvalue()

    def close(self):
        self.tmp.cleanup()


class LoadFoldersTest(unittest.TestCase):
    def test_attributes_and_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "LoadFolders.xml").write_text(
                load_folders_xml(
                    '    <li IfModActive="A.One, b_steam">1.6/Mods/Any</li>\n'
                    '    <li IfModActiveAll="a.one,c">1.6/Mods/All</li>\n'
                    '    <li IfModNotActive="d">1.6/Mods/Not</li>\n')
                .replace("</loadFolders>",
                         "  <v1.5>\n    <li>1.5</li>\n  </v1.5>\n</loadFolders>"),
                encoding="utf-8")
            folders = engine.load_folders(root)
            self.assertEqual(set(folders), {
                root, root / "1.6", root / "1.5", root / "1.6/Mods/Any",
                root / "1.6/Mods/All", root / "1.6/Mods/Not"})
            any_ = folders[root / "1.6/Mods/Any"][0]
            self.assertEqual(any_["any"], {"a.one", "b"})
            self.assertEqual(engine.describe_gate(folders[root / "1.6/Mods/Any"]),
                             "a.one, b_steam")
            self.assertIn('IfModNotActive="d"',
                          engine.describe_gate(folders[root / "1.6/Mods/Not"]))
            self.assertIsNone(engine.describe_gate(folders[root / "1.6"]))

            def active(rel, pkgs):
                return any(engine.condition_holds(c, set(pkgs))
                           for c in folders[root / rel])
            self.assertTrue(active("1.6", []))
            self.assertTrue(active("1.6/Mods/Any", ["b"]))
            self.assertFalse(active("1.6/Mods/Any", ["c"]))
            self.assertTrue(active("1.6/Mods/All", ["a.one", "c", "x"]))
            self.assertFalse(active("1.6/Mods/All", ["a.one"]))
            self.assertTrue(active("1.6/Mods/Not", ["a.one"]))
            self.assertFalse(active("1.6/Mods/Not", ["d"]))

    def test_no_load_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(engine.load_folders(Path(tmp)))


class SidecarViewTest(unittest.TestCase):
    def test_single_world_view_is_the_sidecar(self):
        data = {"meta": {"activeDlcs": ["Core", "Odyssey"],
                         "activeMods": BASE_MODS},
                "defInjections": {"ThingDef": dict(BASE_ENTRIES)}}
        sidecar = engine.Sidecar(data)
        self.assertEqual(list(sidecar.worlds), ["canonical"])
        view = sidecar.view("canonical")
        self.assertEqual(view.entries, sidecar.entries)
        self.assertEqual(view.active_packages, sidecar.active_packages)
        self.assertIn("ludeon.rimworld.odyssey", view.active_packages)
        self.assertFalse(sidecar.conditional("ThingDef", "FX_Helmet.label"))

    def test_world_view_filters_and_applies_variants(self):
        entries = dict(BASE_ENTRIES)
        entries[CHARGE] = {"english": "charge", "required": True,
                           "worlds": ["vge"]}
        entries["FX_Helmet.description"] = {
            "english": "A helmet.", "required": True,
            "variants": {"vge": {"english": "A sealed helmet."}}}
        sidecar = engine.Sidecar(two_world_sidecar(entries))
        base, vge = sidecar.view("base"), sidecar.view("vge")
        self.assertNotIn(CHARGE, base.entries["ThingDef"])
        self.assertIn(CHARGE, vge.required("ThingDef"))
        self.assertEqual(base.entries["ThingDef"]["FX_Helmet.description"]
                         ["english"], "A helmet.")
        self.assertEqual(vge.entries["ThingDef"]["FX_Helmet.description"]
                         ["english"], "A sealed helmet.")
        self.assertIn(VGE, vge.active_packages)
        self.assertNotIn(VGE, base.active_packages)
        self.assertTrue(vge.conditional("ThingDef", CHARGE))
        self.assertEqual(base.worlds_of("ThingDef", CHARGE), ["vge"])


class MainTest(unittest.TestCase):
    def check(self, files):
        fx = Fixture(files)
        self.addCleanup(fx.close)
        return fx.root, *fx.run()

    def single_world_files(self, french):
        return {
            "LoadFolders.xml": load_folders_xml(),
            "1.6/Defs/Things.xml": DEFS,
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(french),
            "Scripts/expected-injections.json": {
                "meta": {"gameBuild": "1.6.test", "activeDlcs": ["Core"],
                         "activeMods": BASE_MODS},
                "defInjections": {"ThingDef": dict(BASE_ENTRIES)}},
        }

    def test_single_world_passes(self):
        _, code, out = self.check(self.single_world_files(MAIN_FRENCH))
        self.assertEqual(code, 0, out)
        self.assertIn("0 error(s), 0 warning(s)", out)
        self.assertNotIn("[worlds:", out)

    def test_single_world_missing_has_no_world_suffix(self):
        _, code, out = self.check(self.single_world_files(MAIN_FRENCH[:1]))
        self.assertEqual(code, 1)
        self.assertIn("ERROR   [French/DefInjected/ThingDef]: missing "
                      "<FX_Helmet.description> (EN: 'A helmet.')\n", out)

    def conditional_files(self, french_files, vge_root=True):
        entries = dict(BASE_ENTRIES)
        entries[CHARGE] = {"english": "charge", "required": True,
                           "worlds": ["vge"]}
        extra = f'    <li IfModActive="{VGE}">1.6/Mods/VGE</li>\n' \
            if vge_root else ""
        files = {"LoadFolders.xml": load_folders_xml(extra),
                 "1.6/Defs/Things.xml": DEFS,
                 "1.6/Mods/VGE/Patches/HelmetOxygen.xml": "<Patch/>\n",
                 "Scripts/expected-injections.json": two_world_sidecar(entries)}
        files.update(french_files)
        return files

    def test_conditional_key_in_gated_root_passes(self):
        _, code, out = self.check(self.conditional_files({
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(MAIN_FRENCH),
            "1.6/Mods/VGE/Languages/French/DefInjected/ThingDef/Things_VGE.xml":
                language_file([(CHARGE, "charge", "charge")]),
        }))
        self.assertEqual(code, 0, out)

    def test_conditional_key_in_main_tree_is_illegal_without_the_gate(self):
        _, code, out = self.check(self.conditional_files({
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(MAIN_FRENCH + [(CHARGE, "charge", "charge")]),
        }))
        self.assertEqual(code, 1)
        lines = [l for l in out.splitlines() if l.startswith("ERROR")]
        self.assertEqual(len(lines), 1, out)
        self.assertIn(f"<{CHARGE}>: not an injection point in this "
                      f"configuration", lines[0])
        self.assertIn("exists only in worlds vge", lines[0])
        self.assertIn("1.6/Mods/VGE/Languages/French", lines[0])
        self.assertTrue(lines[0].endswith("[worlds: base]"), lines[0])

    def test_conditional_key_missing_names_the_gated_root(self):
        root, code, out = self.check(self.conditional_files({
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(MAIN_FRENCH),
        }))
        self.assertEqual(code, 1)
        self.assertIn(f"ERROR   [French/DefInjected/ThingDef]: missing <{CHARGE}> "
                      f"(EN: 'charge') — belongs under "
                      f"{root / '1.6/Mods/VGE/Languages/French'} "
                      f"[worlds: vge]\n", out)

    def test_conditional_key_missing_without_a_root_names_the_gate(self):
        _, code, out = self.check(self.conditional_files({
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(MAIN_FRENCH),
        }, vge_root=False))
        self.assertEqual(code, 1)
        self.assertIn(f"no load root is active in exactly worlds vge; it "
                      f"belongs in a compat root gated "
                      f'IfModActive="{VGE}"', out)

    def variant_files(self, main_copy):
        entries = dict(BASE_ENTRIES)
        entries["FX_Helmet.description"] = {
            "english": "A helmet.", "required": True,
            "variants": {"vge": {"english": "A sealed helmet."}}}
        main = MAIN_FRENCH[:1] + (MAIN_FRENCH[1:] if main_copy else [])
        return {
            "LoadFolders.xml": load_folders_xml(
                f'    <li IfModActive="{VGE}">1.6/Mods/VGE</li>\n'
                f'    <li IfModNotActive="{VGE}">1.6/Mods/NoVGE</li>\n'),
            "1.6/Defs/Things.xml": DEFS,
            "1.6/Languages/French/DefInjected/ThingDef/Things.xml":
                language_file(main),
            "1.6/Mods/NoVGE/Languages/French/DefInjected/ThingDef/Things_NoVGE.xml":
                language_file([("FX_Helmet.description", "A helmet.",
                                "Un casque.")]),
            "1.6/Mods/VGE/Languages/French/DefInjected/ThingDef/Things_VGE.xml":
                language_file([("FX_Helmet.description", "A sealed helmet.",
                                "Un casque étanche.")]),
            "Scripts/expected-injections.json": two_world_sidecar(entries),
        }

    def test_variant_pair_passes(self):
        _, code, out = self.check(self.variant_files(main_copy=False))
        self.assertEqual(code, 0, out)

    def test_variant_pair_with_main_tree_copy_errors(self):
        _, code, out = self.check(self.variant_files(main_copy=True))
        self.assertEqual(code, 1)
        dupes = [l for l in out.splitlines() if "duplicate key" in l]
        self.assertEqual(len(dupes), 2, out)
        self.assertTrue(any(l.endswith("[worlds: base]") for l in dupes))
        self.assertTrue(any(l.endswith("[worlds: vge]") for l in dupes))

    def test_unlisted_root_is_reported(self):
        files = self.single_world_files(MAIN_FRENCH)
        files["1.6/Mods/Stray/Languages/French/DefInjected/ThingDef/X.xml"] = \
            language_file([("FX_Helmet.label", "helmet", "casque")])
        root, code, out = self.check(files)
        self.assertEqual(code, 1)
        self.assertIn(f"ERROR   [LoadFolders.xml]: {root / '1.6/Mods/Stray'} "
                      f"holds Languages/ but is listed in no <li>", out)
        self.assertNotIn("duplicate key", out)

    def test_gate_no_world_activates_is_checked_and_named(self):
        files = self.single_world_files(MAIN_FRENCH)
        files["LoadFolders.xml"] = load_folders_xml(
            f'    <li IfModActive="{VGE}">1.6/Mods/VGE</li>\n')
        files["1.6/Mods/VGE/Defs/Extra.xml"] = DEFS.replace("FX_Helmet", "FX_Extra")
        _, code, out = self.check(files)
        self.assertEqual(code, 1)
        self.assertIn(f"gated on {VGE}, which was not active during the probe "
                      f"boot — add the gate to CANONICAL_ACTIVE_MODS", out)


class MergeWorldsTest(unittest.TestCase):
    def test_merge_marks_partial_lines(self):
        a, b, into = engine.Report(), engine.Report(), engine.Report()
        a.error("p", "both")
        a.error("p", "only a")
        b.error("p", "both")
        b.warn("p", "only b")
        into.merge_worlds([("a", a), ("b", b)])
        self.assertEqual(into.errors, ["p: both", "p: only a [worlds: a]"])
        self.assertEqual(into.warnings, ["p: only b [worlds: b]"])

    def test_single_world_merge_keeps_duplicates_and_order(self):
        a, into = engine.Report(), engine.Report()
        for msg in ("x", "y", "x"):
            a.error("p", msg)
        into.merge_worlds([("canonical", a)])
        self.assertEqual(into.errors, ["p: x", "p: y", "p: x"])


if __name__ == "__main__":
    unittest.main()
