#!/usr/bin/env python3
# Shared engine that regenerates a mod's Scripts/expected-injections.json —
# the checked-in "sidecar" of every DefInjected key the live game expects for
# that mod — by driving the L10nProbe dev mod. Consumed by each mod repo via
# a thin Scripts/refresh-translation-expectations.py shim that sys.path-
# inserts this file's directory, imports it, assigns the config variables
# below by module attribute (e.g. `engine.PACKAGE_ID = "..."`), and calls
# main().
#
# Config variables a shim MUST set before calling main():
#   PACKAGE_ID            str        this mod's own packageId (About.xml)
#   CANONICAL_ACTIVE_MODS list[str]  pinned probe-boot mod list, load order,
#                                    probe's own packageId last
#   or WORLDS             dict[str, list[str]]  several pinned boots, see below
# Exactly one of CANONICAL_ACTIVE_MODS and WORLDS is set.
#
# The probe source lives beside this engine, at ../probe relative to this
# file (i.e. the rimworld-l10n checkout's probe/ directory) — see
# rimworld_path() below for the deploy check and its build instructions.
#
# The sidecar is what makes unknown localization-gap classes impossible by
# structure: check_translations.py (this engine's checker half) validates
# languages against it and refuses to run against stale expectations (any
# defName in Defs/ it has never seen), so every content change forces a
# regen, and the regen sees everything the game sees (vanilla-inherited
# fields, C# defaults) via the game's own walker,
# Verse.DefInjectionUtility.ForEachPossibleDefInjection.
#
# Flow: launch the game with -l10nprobe (graphical boot, ~1-2 min; the probe
# walks the def graph the moment it is complete and the game has injected
# its translations into it, BEFORE any mod's static constructor runs, writes
# one JSON per configured mod, then quits the game once startup is over),
# fetch this mod's dump from the probe's Output folder, verify it came from
# the pinned boot, rewrite the sidecar, print a key-level diff summary. The
# walk timing is load-bearing: a value another mod assigns to our def from
# its static constructor (VEF's ResearchProjectUtility.AutoAssignRules hands
# its 75-line schematic grammar to every research project with a null
# generalRules) comes after the game's injection passes, so no translation
# of it could ever load; the probe leaves it out, where a late walk charged
# it to the def's owner (PersonaWeaponsUnbound, 2026-10-03).
#
# The probe boots with a PINNED mod list (CANONICAL_ACTIVE_MODS), not
# whatever the user last played with: ModsConfig.xml is swapped for the run
# and restored afterwards. The dump reflects the LIVE def graph, so any
# third-party mod that patches our defs leaks into the expectations — a mod
# that reshuffles our defs' fields or hediff comps would show up in the dump
# even though it is not installed for most players. The pinned list is this
# mod + hard deps + every DLC our defs can MayRequire, matching the
# configuration the sidecar was first verified against.
#
# CANONICAL_ACTIVE_MODS membership rule (the same rule for every consuming
# repo; only the enumeration differs per mod):
#   * Core, plus every DLC the mod hard-requires or gates content behind via
#     MayRequire (a def whose gate is absent never loads, so its keys drop
#     out of the sidecar and its already-shipped translations turn illegal);
#   * hard third-party mod dependencies, and THEIR OWN transitive hard deps
#     (a dependency that itself fails to load properly changes the def graph
#     the probe walks);
#   * this mod, plus family siblings as a convenience: the probe writes one
#     dump per ticked target in a single boot, so while two repos' lists are
#     identical, one launched refresh leaves the other a dump its --no-launch
#     run can consume without a second boot. Each sidecar is only ever
#     validated against ITS OWN mod's content, and a sibling whose list has
#     diverged (UMW pins VEF + VFE Pirates for its warcasket uniques) simply
#     boots its own refresh — load_dump() refuses a dump whose recorded
#     activeMods differ from this list, so the shortcut fails loudly instead
#     of leaking the other boot's mods into this sidecar;
#   * a third-party mod ONLY if this mod's own content gates on it: a
#     MayRequire attribute, or a LoadFolders IfModActive compat root
#     (<version>/Mods/<Mod Name>/ with its own Defs and DefInjected). Gated defs
#     load only with the gate active, so their keys reach the sidecar only
#     if the gate is pinned — one list that includes every gate covers every
#     branch, as long as a branch ADDS defs rather than rewriting the text of
#     a shared key (the game cannot model that either: two DefInjected
#     entries for one key are a duplicate-key error) or adding a field to a
#     def that loads without the gate (see WORLDS).
# Nothing else. The probe filters each dump by packageId, so an extra mod
# adds no keys of its own — but its patches to OUR defs leak straight into
# the expectations (see incident note below).
#
# Operational warnings worth keeping in mind whenever CANONICAL_ACTIVE_MODS
# is edited:
#   * All ids LOWERCASE — the format RimWorld itself writes to ModsConfig.xml.
#     This is load-bearing, not cosmetic: mod *loading* tolerates mixed case,
#     but the MayRequire active-check is case-exact against the ModsConfig
#     strings, so a mixed-case entry here loads the mod yet silently drops
#     every def gated on it. Observed 2026-08-03: VanillaExpanded.VFEPower
#     loaded fine while every VFEPower-gated RecipeDef vanished from the dump.
#   * Pin deliberately, don't reuse a "whatever I was playing with" list: a
#     2026-08-03 run under a Combat Extended play list emitted CE's rebuilt
#     spear tools and reshuffled hediff comps, none of which exist for
#     players without CE — those keys would have shipped in the sidecar (and
#     from there, demanded of every translator) for a mod nobody but the
#     author had installed.
#
# Operational facts (verified against the probe's SPEC + live runs, 2026-07-31):
#   * The game's exit code is 0 even when probing fails — success is judged by
#     the output file, never the exit code.
#   * On per-mod failure the probe guarantees NO output file at that mod's
#     path (a pre-existing one is deleted). We delete the file before
#     launching anyway, so a leftover from an older run can't be mistaken for
#     a fresh result.
#   * meta.generated is the only field that changes between runs on identical
#     content, so it is stripped from the sidecar: an unchanged repo
#     regenerates to a byte-identical file and "git diff is empty" means
#     "nothing changed". meta.gameBuild is kept — a diff in it explains why
#     keys moved when no local def changed (vanilla update).
#   * meta.activeMods is written by the probe (every running mod's packageId
#     in load order, lowercase, Steam postfix stripped) and must equal
#     CANONICAL_ACTIVE_MODS (or its world's WORLDS list) exactly, order
#     included, or load_dump() refuses the dump. On a launched run a
#     mismatch means the pin did not take (an
#     id misspelled or not installed; the game drops unknown ids). With
#     --no-launch it means the dump in Output/ came from some OTHER boot that
#     also had this mod ticked — a sibling repo's refresh on a different list,
#     or a startup smoke test, which deliberately loads integration mods —
#     and reusing it would leak that boot's mods into this sidecar.
#     meta.collectedAfterStartup marks a dump from the probe's settings-window
#     button, taken after the mods' static constructors; refused for the same
#     reason the probe's startup timing exists (see Flow above).
#
# Usage:
#   python3 Scripts/refresh-translation-expectations.py            # launch + refresh
#   python3 Scripts/refresh-translation-expectations.py --no-launch  # reuse the
#     dump already in the probe's Output folder (debugging / probe just ran);
#     refused unless that dump records exactly this repo's pinned mod list
#
# WORLDS: one pinned boot cannot describe a key that exists only in SOME
# configurations — a LoadFolders-gated compat root whose Patches/ add a
# [MustTranslate] field to a main-tree def (the key appears under the
# main-tree def, but only while the gate is active), or a gate that rewrites a
# main-tree field's English. Its translation must live in a root active in
# exactly the configurations where the key exists, which the checker can only
# verify if the sidecar records them. A shim then sets WORLDS instead of
# CANONICAL_ACTIVE_MODS: an ordered {world name: pinned list}, the first entry
# the base world (normally the list CANONICAL_ACTIVE_MODS would hold, without
# the gate), each later one adding or removing gates. Every world follows the
# membership rule above. The engine boots once per world, keeps each verified
# dump as Output/<packageId>.<world>.json (what --no-launch then consumes),
# and merges them (merge_dumps): an entry carries "worlds" only when some
# world lacks it, and "variants" {world: {english/required}} only for worlds
# whose text or required flag differs from the first world that has it;
# meta.worlds records each world's activeMods/activeDlcs. A single-world
# refresh writes exactly the dump, as it always has.

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
from pathlib import Path

# Per-repo constants. Neutral defaults; the consuming repo's
# Scripts/refresh-translation-expectations.py shim assigns the real values
# after import (module attribute assignment, e.g. `engine.PACKAGE_ID = ...`).
# None is not a legitimate configured value for either — main() fails loudly
# at startup if the shim forgot to set one.
PACKAGE_ID = None
CANONICAL_ACTIVE_MODS = None
WORLDS = None

# The consuming repo's root. Shims set this from their own file location
# (Path(__file__).resolve().parent.parent), which keeps the historical
# behavior of working from any cwd; left None, it falls back to the current
# working directory at main() time. A path derived from THIS file's location
# would be wrong: the engine lives in the shared rimworld-l10n checkout, not
# the consuming repo. ROOT/SIDECAR are resolved from it inside main().
REPO_ROOT = None
ROOT = None
SIDECAR = None

# Where the probe's own source lives relative to this engine file: the
# rimworld-l10n checkout's probe/ directory, a sibling of this engine's own
# directory (refresh/). Used only for the "not deployed" error message below
# — this engine never builds the probe itself.
PROBE_SOURCE_ROOT = Path(__file__).resolve().parent.parent / "probe"

# The two install layouts this engine can drive, told apart by the game
# executable present under RIMWORLD_PATH. RimWorld 1.7 (the Waylith engine
# on .NET 10) is a flat install whose RimWorld.exe hosts RimWorld.dll and
# which writes its log to Logs/Player.log under the user data folder; 1.6
# (Unity) is RimWorldWin64.exe with Player.log at that folder's root. The
# exe decides, so a Steam branch switch needs no configuration. The Waylith
# layout is probed first: a 1.7 install keeps an empty RimWorldWin64_Data/
# folder behind, never the old exe, and a 1.6 install has no RimWorld.exe.
GameLayout = namedtuple("GameLayout", "name exe log_relpath")
GAME_LAYOUTS = (
    GameLayout("waylith", "RimWorld.exe", Path("Logs") / "Player.log"),
    GameLayout("unity", "RimWorldWin64.exe", Path("Player.log")),
)


def game_layout(rw):
    # The GameLayout installed under rw, or None when neither exe is there.
    for layout in GAME_LAYOUTS:
        if (Path(rw) / layout.exe).is_file():
            return layout
    return None


def rimworld_path():
    rw = os.environ.get("RIMWORLD_PATH")
    if not rw:
        sys.exit("RIMWORLD_PATH is not set (see CLAUDE.md's WSL setup note)")
    rw = Path(rw)
    if game_layout(rw) is None:
        sys.exit(f"No RimWorld.exe (1.7) or RimWorldWin64.exe (1.6) under "
                 f"RIMWORLD_PATH ({rw})")
    if not (rw / "Mods" / "L10nProbe" / "About").is_dir():
        sys.exit(f"L10nProbe is not deployed under {rw / 'Mods'} — build "
                 f"{PROBE_SOURCE_ROOT}/Source/1.6/L10nProbe.csproj -c Release "
                 f"FROM THE CANONICAL rimworld-l10n CHECKOUT (a submodule "
                 f"copy of rimworld-l10n refuses to deploy by design)")
    return rw


def modsconfig_path():
    configs = sorted(Path("/mnt/c/Users").glob(
        "*/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios"
        "/Config/ModsConfig.xml"))
    if not configs:
        sys.exit("No ModsConfig.xml found under /mnt/c/Users — cannot pin "
                 "the probe mod list")
    return configs[-1]


def pinned_modsconfig(original_text, mods):
    # Rebuild only <activeMods>; version and knownExpansions pass through.
    root = ET.fromstring(original_text)
    active = root.find("activeMods")
    for li in list(active):
        active.remove(li)
    for pid in mods:
        ET.SubElement(active, "li").text = pid
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def game_is_running():
    # The probe boot needs the client to itself: a second instance fights
    # over the session, and the ModsConfig swap must not race a live game
    # (which rewrites the file on mod-list edits and on exit). tasklist.exe
    # is reachable from WSL via interop; if it is not, skip the check rather
    # than block the flow. Both layouts' exes are checked: the install under
    # RIMWORLD_PATH says which one THIS flow will launch, not which one the
    # player may still have open from before a branch switch.
    for layout in GAME_LAYOUTS:
        try:
            out = subprocess.run(
                ["tasklist.exe", "/FI", f"IMAGENAME eq {layout.exe}"],
                capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.TimeoutExpired):
            return False
        if layout.exe in out:
            return True
    return False


def warn_unpinned_probe_targets(worlds):
    # Ticking a mod in L10nProbe's settings is the memorable onboarding step;
    # adding it to CANONICAL_ACTIVE_MODS above is the forgettable one. Catch
    # the gap before the boot: a ticked mod absent from every pinned list is
    # simply not loaded during the run, so its dump is guaranteed to fail.
    cfg = modsconfig_path().parent / "Mod_L10nProbe_L10nProbeMod.xml"
    if not cfg.is_file():
        return
    try:
        node = ET.parse(cfg).getroot().find(".//targetPackageIds")
    except ET.ParseError:
        return
    pinned = {pid for mods in worlds.values() for pid in mods}
    where = "CANONICAL_ACTIVE_MODS" if WORLDS is None else "any WORLDS list"
    for li in node if node is not None else []:
        pid = (li.text or "").strip().lower()
        if pid and pid not in pinned:
            print(f"warning: {pid} is ticked for probing in L10nProbe's "
                  f"settings but is not in {where} — it will "
                  f"not be loaded during this boot and its dump WILL fail",
                  file=sys.stderr)


def launch_probe(rw, dump_path, mods, world=None):
    if game_is_running():
        sys.exit("RimWorld is already running — the probe needs an exclusive "
                 "boot (mod-list swap + -l10nprobe). Close the client, then "
                 "rerun this script.")
    dump_path.unlink(missing_ok=True)
    mc = modsconfig_path()
    original = mc.read_bytes()
    mc.write_text(pinned_modsconfig(original.decode("utf-8-sig"), mods),
                  encoding="utf-8")
    print("Launching RimWorld with -l10nprobe on the pinned mod list "
          + (f"of world {world} " if world else "")
          + "(graphical boot, ~1-2 min)...")
    try:
        # WSL interop blocks until the Windows process exits; the probe
        # quits the game itself after writing its dumps.
        subprocess.run([f"./{game_layout(rw).exe}", "-l10nprobe"], cwd=rw,
                       check=False)
    finally:
        # Always hand the player's own mod list back, byte-identical.
        mc.write_bytes(original)
        print(f"Restored {mc}")


def load_dump(dump_path, mods, world=None):
    if not dump_path.is_file():
        sys.exit(f"Probe wrote no dump at {dump_path} — absence of the file "
                 f"IS the failure marker; check Player.log for a "
                 f"'[L10nProbe] FAILED probing' line")
    dump = json.loads(dump_path.read_text(encoding="utf-8"))
    meta = dump.get("meta", {})
    if meta.get("modPackageId") != PACKAGE_ID:
        sys.exit(f"{dump_path} is not a {PACKAGE_ID} dump")
    verify_boot(meta, dump_path, mods, world)
    meta.pop("generated", None)
    return dump


def load_world_dumps(out_dir, worlds):
    # {world: dump} from the per-world files a launched WORLDS run keeps,
    # each re-verified against its own world's list.
    dumps = {}
    for name, mods in worlds.items():
        path = world_dump_path(out_dir, name)
        if not path.is_file():
            sys.exit(f"No dump for world {name} at {path} — rerun without "
                     f"--no-launch to boot every world")
        dumps[name] = load_dump(path, mods, name)
    return dumps


def verify_boot(meta, dump_path, mods, world=None):
    # The dump must describe THIS repo's pinned boot — see the header's
    # operational facts for what each mismatch means. The checker also reads
    # meta.activeMods to resolve def-level MayRequire gates against what was
    # active, so the list has to be the real one, not a label we stamp on.
    if meta.get("collectedAfterStartup"):
        sys.exit(f"{dump_path} was taken by the probe's settings-window "
                 f"'Probe now' button, after every mod's static constructor; "
                 f"it may carry values other mods assigned at runtime that no "
                 f"translation could target. Sidecars come from a -l10nprobe "
                 f"boot: rerun this script without --no-launch.")
    recorded = meta.get("activeMods")
    if recorded is None:
        sys.exit(f"{dump_path} records no meta.activeMods — the deployed "
                 f"L10nProbe predates it. Rebuild and deploy the probe from "
                 f"the canonical rimworld-l10n checkout "
                 f"(dotnet build probe/L10nProbe.sln -c Release), then rerun.")
    if recorded == mods:
        return
    extra = [m for m in recorded if m not in mods]
    missing = [m for m in mods if m not in recorded]
    lines = [f"{dump_path} was not produced by this repo's pinned boot"
             + (f" of world {world}." if world else ".")]
    if extra:
        lines.append(f"  loaded but not pinned: {', '.join(extra)}")
    if missing:
        lines.append(f"  pinned but not loaded: {', '.join(missing)}")
    if not extra and not missing:
        lines.append(f"  same mods, different load order: {recorded}")
    lines.append("  With --no-launch: the dump in Output/ came from another "
                 "boot that also dumps this mod (a sibling repo's refresh on "
                 "its own pinned list, or a startup smoke test); rerun "
                 "without --no-launch to boot this repo's list.")
    lines.append("  On a launched run: the pin did not take — check each id "
                 "against About.xml (lowercase; the game silently drops ids "
                 "it cannot resolve) and that the mod is installed.")
    sys.exit("\n".join(lines))


# Per-entry fields a later world may override (merge_dumps' "variants"),
# with the value the probe's omission of the field means.
VARIANT_FIELDS = (("english", None), ("required", False))
WORLD_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def configured_worlds():
    # {world name: pinned list}, base world first. A CANONICAL_ACTIVE_MODS
    # shim is the single world "canonical" (the name a world-less sidecar
    # carries on the checker side too).
    if WORLDS is None:
        return {"canonical": CANONICAL_ACTIVE_MODS}
    return dict(WORLDS)


def world_dump_path(out_dir, world):
    return out_dir / f"{PACKAGE_ID}.{world}.json"


def merge_dumps(dumps):
    # dumps: {world name: loaded dump}, base world first. One world is the
    # sidecar as it always was: the dump itself, byte for byte. Several
    # merge per (defType, key): the first world holding the key supplies the
    # entry as dumped, "worlds" lists the worlds holding it only when some
    # world lacks it, and "variants" holds, per later world, only the
    # VARIANT_FIELDS whose value differs from that base. Both levels stay
    # ordinally sorted like the probe's own output.
    names = list(dumps)
    if len(names) == 1:
        return dumps[names[0]]
    builds = {w: d["meta"].get("gameBuild") for w, d in dumps.items()}
    if len(set(builds.values())) > 1:
        sys.exit(f"World dumps come from different game builds: {builds} — "
                 f"rerun without --no-launch so every world boots the same "
                 f"install")
    meta = dict(dumps[names[0]]["meta"])
    meta["worlds"] = {w: {"activeMods": d["meta"].get("activeMods", []),
                          "activeDlcs": d["meta"].get("activeDlcs", [])}
                      for w, d in dumps.items()}
    merged = {}
    def_types = sorted({dt for d in dumps.values() for dt in d["defInjections"]})
    for dt in def_types:
        per_world = {w: d["defInjections"].get(dt, {}) for w, d in dumps.items()}
        out = merged[dt] = {}
        for key in sorted({k for entries in per_world.values() for k in entries}):
            present = [w for w in names if key in per_world[w]]
            entry = dict(per_world[present[0]][key])
            if len(present) < len(names):
                entry["worlds"] = present
            variants = {}
            for w in present[1:]:
                other = per_world[w][key]
                diff = {f: other.get(f, default) for f, default in VARIANT_FIELDS
                        if other.get(f, default) != entry.get(f, default)}
                if diff:
                    variants[w] = diff
            if variants:
                entry["variants"] = variants
            out[key] = entry
    return {"meta": meta, "defInjections": merged}


def key_set(dump):
    return {(dt, k) for dt, keys in dump["defInjections"].items() for k in keys}


def membership(dump, dt, k):
    worlds = dump["defInjections"][dt][k].get("worlds")
    return ", ".join(worlds) if worlds else "all"


def summarize_worlds(old, new, old_keys, new_keys):
    # World-membership deltas, printed only when either side records worlds:
    # the configured worlds themselves, each added key that exists in only
    # some worlds, and each kept key whose membership moved.
    old_worlds = old["meta"].get("worlds")
    new_worlds = new["meta"].get("worlds")
    if not old_worlds and not new_worlds:
        return
    old_names = list(old_worlds or ["canonical"])
    new_names = list(new_worlds or ["canonical"])
    if old_names != new_names:
        print(f"worlds: {', '.join(old_names)} -> {', '.join(new_names)}")
    for name in new_names:
        if old_worlds and new_worlds and name in old_worlds \
                and old_worlds[name] != new_worlds[name]:
            print(f"worlds: {name}'s mod/DLC list changed")
    for dt, k in sorted(new_keys):
        now = membership(new, dt, k)
        if (dt, k) not in old_keys:
            if now != "all":
                print(f"  worlds: {dt}/{k}: only {now}")
        elif membership(old, dt, k) != now:
            print(f"  worlds: {dt}/{k}: {membership(old, dt, k)} -> {now}")


def summarize(old, new):
    if old is None:
        print(f"Sidecar created: {sum(len(k) for k in new['defInjections'].values())} "
              f"entries across {len(new['defInjections'])} def types")
        return
    if old["meta"].get("gameBuild") != new["meta"].get("gameBuild"):
        print(f"gameBuild: {old['meta'].get('gameBuild')} -> "
              f"{new['meta'].get('gameBuild')} (vanilla-sourced English may "
              f"have changed even where no local def did)")
    if old["meta"].get("activeDlcs") != new["meta"].get("activeDlcs"):
        print(f"activeDlcs: {old['meta'].get('activeDlcs')} -> "
              f"{new['meta'].get('activeDlcs')}")
    old_keys, new_keys = key_set(old), key_set(new)
    for label, keys in (("added", new_keys - old_keys),
                        ("removed", old_keys - new_keys)):
        for dt, k in sorted(keys):
            print(f"  {label}: {dt}/{k}")
    changed = [(dt, k) for dt, k in sorted(old_keys & new_keys)
               if old["defInjections"][dt][k] != new["defInjections"][dt][k]]
    for dt, k in changed:
        print(f"  changed: {dt}/{k}")
    summarize_worlds(old, new, old_keys, new_keys)
    if old == new:
        print("No changes — sidecar is byte-identical.")
    else:
        print(f"{len(new_keys - old_keys)} added, {len(old_keys - new_keys)} "
              f"removed, {len(changed)} changed. New keys need translating in "
              f"every language (/translate) before check-translations.py "
              f"passes.")


def check_config():
    if PACKAGE_ID is None or (CANONICAL_ACTIVE_MODS is None and WORLDS is None):
        sys.exit("refresh_expectations engine misconfigured: PACKAGE_ID "
                 "and/or CANONICAL_ACTIVE_MODS is None — the consuming "
                 "repo's Scripts/refresh-translation-expectations.py shim "
                 "must assign both after importing this engine (or WORLDS "
                 "in place of CANONICAL_ACTIVE_MODS)")
    if CANONICAL_ACTIVE_MODS is not None and WORLDS is not None:
        sys.exit("refresh_expectations engine misconfigured: both "
                 "CANONICAL_ACTIVE_MODS and WORLDS are set — a shim pins "
                 "one boot (CANONICAL_ACTIVE_MODS) or several (WORLDS, whose "
                 "first entry is the base world), never both")
    if WORLDS is not None:
        if not WORLDS:
            sys.exit("refresh_expectations engine misconfigured: WORLDS is "
                     "empty")
        for name, mods in WORLDS.items():
            if not WORLD_NAME_RE.match(name) or not mods:
                sys.exit(f"refresh_expectations engine misconfigured: WORLDS "
                         f"entry {name!r} needs a name of letters, digits, "
                         f"'-' or '_' (it names a dump file) and a non-empty "
                         f"mod list")


def main():
    check_config()

    global ROOT, SIDECAR
    ROOT = REPO_ROOT or Path.cwd()
    SIDECAR = ROOT / "Scripts" / "expected-injections.json"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-launch", action="store_true",
                    help="skip launching the game; consume the dump already "
                         "in the probe's Output folder")
    args = ap.parse_args()

    rw = rimworld_path()
    out_dir = rw / "Mods" / "L10nProbe" / "Output"
    dump_path = out_dir / f"{PACKAGE_ID}.json"
    worlds = configured_worlds()
    if WORLDS is None:
        if not args.no_launch:
            warn_unpinned_probe_targets(worlds)
            launch_probe(rw, dump_path, CANONICAL_ACTIVE_MODS)
        new = load_dump(dump_path, CANONICAL_ACTIVE_MODS)
    else:
        if not args.no_launch:
            # One boot per world. Each dump is verified against its own
            # world's list before it is kept under the world's name, and the
            # previous run's world files go first, so a run that fails
            # midway never leaves a mix for --no-launch to merge.
            warn_unpinned_probe_targets(worlds)
            for name in worlds:
                world_dump_path(out_dir, name).unlink(missing_ok=True)
            for name, mods in worlds.items():
                launch_probe(rw, dump_path, mods, name)
                load_dump(dump_path, mods, name)
                shutil.copyfile(dump_path, world_dump_path(out_dir, name))
        new = merge_dumps(load_world_dumps(out_dir, worlds))

    old = json.loads(SIDECAR.read_text(encoding="utf-8")) \
        if SIDECAR.is_file() else None
    # Match the probe's own formatting (two-space indent, LF, UTF-8 no BOM,
    # trailing newline) so the sidecar diffs cleanly against raw dumps.
    SIDECAR.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    summarize(old, new)
    print(f"Wrote {SIDECAR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
