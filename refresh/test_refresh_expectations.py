#!/usr/bin/env python3
# Tests for the refresh engine's world handling: merging per-world dumps into
# one sidecar, the single-world passthrough, config validation and the
# --no-launch per-world file discovery. Run from the repo root:
#   python3 -m unittest discover -s . -p 'test_*.py'
# Nothing here launches the game: rimworld_path() is patched to a temp dir
# holding fixture dumps.

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refresh_expectations as engine  # noqa: E402

PKG = "shunter.fixture"
VGE = "vanillaexpanded.gravship"
BASE_MODS = ["brrainz.harmony", "ludeon.rimworld", PKG, "shunter.l10nprobe"]
VGE_MODS = ["brrainz.harmony", "ludeon.rimworld", VGE, PKG, "shunter.l10nprobe"]


def dump(mods, entries, build="1.6.test", generated=True):
    meta = {"gameBuild": build, "activeDlcs": ["Core"], "modPackageId": PKG,
            "modName": "Fixture — ü", "activeMods": mods}
    if generated:
        meta = {"generated": "2026-01-01T00:00:00Z", **meta}
    return {"meta": meta, "defInjections": entries}


BASE = {
    "StatDef": {"FX_Range.label": {"english": "range", "required": True}},
    "ThingDef": {
        "FX_Helmet.description": {"english": "A helmet.", "required": True},
        "FX_Helmet.label": {"english": "helmet", "required": True},
        "FX_Helmet.tools.0.label": {"english": "head", "normalized":
                                    "FX_Helmet.tools.0.label"},
    },
}


def vge_entries():
    entries = copy.deepcopy(BASE)
    del entries["StatDef"]
    things = entries["ThingDef"]
    things["FX_Helmet.comps.0.chargeNoun"] = {"english": "charge",
                                              "required": True}
    things["FX_Helmet.description"] = {"english": "A sealed helmet.",
                                       "required": True}
    things["FX_Helmet.tools.0.label"]["required"] = True
    return entries


class ConfigMixin:
    def configure(self, canonical=None, worlds=None):
        patches = [mock.patch.object(engine, "PACKAGE_ID", PKG),
                   mock.patch.object(engine, "CANONICAL_ACTIVE_MODS", canonical),
                   mock.patch.object(engine, "WORLDS", worlds)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)


class MergeTest(ConfigMixin, unittest.TestCase):
    def test_single_world_is_the_dump(self):
        d = dump(BASE_MODS, BASE, generated=False)
        self.assertIs(engine.merge_dumps({"canonical": d}), d)

    def test_two_worlds(self):
        merged = engine.merge_dumps({
            "base": dump(BASE_MODS, BASE, generated=False),
            "vge": dump(VGE_MODS, vge_entries(), generated=False)})
        meta = merged["meta"]
        self.assertEqual(meta["activeMods"], BASE_MODS)
        self.assertEqual(list(meta["worlds"]), ["base", "vge"])
        self.assertEqual(meta["worlds"]["vge"],
                         {"activeMods": VGE_MODS, "activeDlcs": ["Core"]})
        self.assertEqual(list(meta), ["gameBuild", "activeDlcs", "modPackageId",
                                      "modName", "activeMods", "worlds"])
        inj = merged["defInjections"]
        self.assertEqual(list(inj), ["StatDef", "ThingDef"])
        self.assertEqual(inj["StatDef"]["FX_Range.label"],
                         {"english": "range", "required": True,
                          "worlds": ["base"]})
        things = inj["ThingDef"]
        self.assertEqual(list(things), sorted(things))
        self.assertEqual(things["FX_Helmet.label"],
                         {"english": "helmet", "required": True})
        self.assertEqual(things["FX_Helmet.comps.0.chargeNoun"],
                         {"english": "charge", "required": True,
                          "worlds": ["vge"]})
        self.assertEqual(things["FX_Helmet.description"],
                         {"english": "A helmet.", "required": True,
                          "variants": {"vge": {"english": "A sealed helmet."}}})
        self.assertEqual(things["FX_Helmet.tools.0.label"],
                         {"english": "head",
                          "normalized": "FX_Helmet.tools.0.label",
                          "variants": {"vge": {"required": True}}})

    def test_key_first_seen_in_a_later_world_takes_its_base_there(self):
        third = copy.deepcopy(vge_entries())
        third["ThingDef"]["FX_Helmet.comps.0.chargeNoun"]["english"] = "oxygen"
        merged = engine.merge_dumps({
            "base": dump(BASE_MODS, BASE, generated=False),
            "vge": dump(VGE_MODS, vge_entries(), generated=False),
            "vge2": dump(VGE_MODS, third, generated=False)})
        self.assertEqual(
            merged["defInjections"]["ThingDef"]["FX_Helmet.comps.0.chargeNoun"],
            {"english": "charge", "required": True, "worlds": ["vge", "vge2"],
             "variants": {"vge2": {"english": "oxygen"}}})

    def test_mixed_game_builds_refused(self):
        with self.assertRaises(SystemExit) as cm:
            engine.merge_dumps({
                "base": dump(BASE_MODS, BASE, generated=False),
                "vge": dump(VGE_MODS, BASE, build="1.6.other", generated=False)})
        self.assertIn("different game builds", str(cm.exception))


class ConfigTest(ConfigMixin, unittest.TestCase):
    def test_both_set_is_an_error(self):
        self.configure(canonical=BASE_MODS, worlds={"base": BASE_MODS})
        with self.assertRaises(SystemExit) as cm:
            engine.check_config()
        self.assertIn("both", str(cm.exception))

    def test_neither_set_is_an_error(self):
        self.configure()
        with self.assertRaises(SystemExit):
            engine.check_config()

    def test_bad_world_name_is_an_error(self):
        self.configure(worlds={"has space": BASE_MODS})
        with self.assertRaises(SystemExit):
            engine.check_config()


class NoLaunchTest(ConfigMixin, unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.rw = Path(tmp.name) / "RimWorld"
        self.out = self.rw / "Mods" / "L10nProbe" / "Output"
        self.out.mkdir(parents=True)
        self.repo = Path(tmp.name) / "repo"
        (self.repo / "Scripts").mkdir(parents=True)
        for p in (mock.patch.object(engine, "rimworld_path", lambda: self.rw),
                  mock.patch.object(engine, "REPO_ROOT", self.repo),
                  mock.patch.object(sys, "argv", ["refresh", "--no-launch"])):
            p.start()
            self.addCleanup(p.stop)

    def write(self, name, data):
        (self.out / name).write_text(json.dumps(data, indent=2,
                                                ensure_ascii=False) + "\n",
                                     encoding="utf-8")

    def run_main(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            engine.main()
        return out.getvalue()

    def sidecar_text(self):
        return (self.repo / "Scripts" / "expected-injections.json").read_text(
            encoding="utf-8")

    def test_single_world_writes_the_dump_byte_for_byte(self):
        self.configure(canonical=BASE_MODS)
        raw = dump(BASE_MODS, BASE)
        self.write(f"{PKG}.json", raw)
        self.run_main()
        expected = copy.deepcopy(raw)
        expected["meta"].pop("generated")
        self.assertEqual(self.sidecar_text(),
                         json.dumps(expected, indent=2, ensure_ascii=False) + "\n")

    def test_worlds_consume_per_world_files(self):
        self.configure(worlds={"base": BASE_MODS, "vge": VGE_MODS})
        # The plain dump is some other boot's; WORLDS never reads it.
        self.write(f"{PKG}.json", dump(["ludeon.rimworld"], BASE))
        self.write(f"{PKG}.base.json", dump(BASE_MODS, BASE))
        self.write(f"{PKG}.vge.json", dump(VGE_MODS, vge_entries()))
        printed = self.run_main()
        sidecar = json.loads(self.sidecar_text())
        self.assertEqual(list(sidecar["meta"]["worlds"]), ["base", "vge"])
        self.assertNotIn("generated", sidecar["meta"])
        self.assertIn("Sidecar created", printed)
        # A second run on the same dumps is a no-op; a membership change is
        # listed per key.
        self.assertIn("byte-identical", self.run_main())
        moved = vge_entries()
        moved["StatDef"] = copy.deepcopy(BASE["StatDef"])
        self.write(f"{PKG}.vge.json", dump(VGE_MODS, moved))
        self.assertIn("  worlds: StatDef/FX_Range.label: base -> all",
                      self.run_main())

    def test_worlds_missing_file_names_the_world(self):
        self.configure(worlds={"base": BASE_MODS, "vge": VGE_MODS})
        self.write(f"{PKG}.base.json", dump(BASE_MODS, BASE))
        with self.assertRaises(SystemExit) as cm:
            self.run_main()
        self.assertIn("No dump for world vge", str(cm.exception))
        self.assertIn(f"{PKG}.vge.json", str(cm.exception))

    def test_world_file_from_the_wrong_boot_is_refused(self):
        self.configure(worlds={"base": BASE_MODS, "vge": VGE_MODS})
        self.write(f"{PKG}.base.json", dump(BASE_MODS, BASE))
        self.write(f"{PKG}.vge.json", dump(BASE_MODS, BASE))
        with self.assertRaises(SystemExit) as cm:
            self.run_main()
        self.assertIn("pinned boot of world vge", str(cm.exception))
        self.assertIn(f"pinned but not loaded: {VGE}", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
