#!/usr/bin/env python3
# Shared engine for the family's pre-release integration smoke test: boot the
# real game once with a PINNED mod list (this mod + its integration mods +
# their deps), let it reach a fully loaded main menu, then parse Player.log
# and classify every error/warning by origin. Consumed by each mod repo via a
# thin Scripts/integration-smoke-test.py shim (see SHIM_TEMPLATE.py) that
# imports this engine, assigns the config variables below, and calls main().
#
# Origin (the incident this exists to catch): BetterTradersGuild v1.1.0
# shipped a Harmony patch on a Choose Where To Land method; applying the
# detour at Mod-ctor time JIT-compiled the target, ran its type's static
# ctor before any defs were loaded, and permanently nulled CWTL's arrival
# mode def - a red startup error plus a broken CWTL for every shared player.
# The error WAS visible in a manual smoke test but drowned in the noise of a
# heavily modded personal save. The fix is structural: boot a MINIMAL pinned
# list where the baseline is a clean log, so any error at all is signal, and
# classify what remains so a regression in our mod or an integration seam is
# never mistaken for third-party API drift.
#
# Mechanics reused from the refresh engine (refresh_expectations.py, imported
# below): RimWorld path detection, ModsConfig pin/restore, running-game
# check. The boot itself rides the L10nProbe's -l10nprobe flag purely for its
# quit-when-loaded behavior - the probe dumps whatever its settings say and
# then shuts the game down from an ExecuteWhenFinished delegate, i.e. AFTER
# every mod's static ctor, def write, and (for BTG-style deferred passes)
# post-defs patch application has run and logged. Probe dump failures are
# expected here (the smoke list rarely matches the probe's ticked targets)
# and are classified as tooling noise, never gated on.
#
# Config variables a shim MUST set before calling main():
#   PACKAGE_ID           str        this mod's own packageId (About.xml)
#   SMOKE_ACTIVE_MODS    list[str]  pinned boot list, LOWERCASE, load order,
#                                   probe's packageId (shunter.l10nprobe) last
#   OWN_PATTERNS         list[str]  substrings attributing a log entry to
#                                   this mod (assembly name, log prefix,
#                                   def/key prefix)
#   INTEGRATION_PATTERNS dict[str, list[str]]  integration mod display name ->
#                                   substrings (namespaces, log prefixes)
# Optional:
#   REPO_ROOT            Path       consuming repo's root (for messages only)
#
# Gate: exit 1 when any ERROR entry is attributed to this mod or an
# integration seam; --strict widens the gate to every non-tooling error.
# Warnings are reported, never gated. Success requires the boot to actually
# complete (the probe's shutdown line must be present) so a hang or crash
# can't read as a pass.
#
# Usage (from the consuming repo):
#   python3 Scripts/integration-smoke-test.py              # boot + scan
#   python3 Scripts/integration-smoke-test.py --no-launch  # rescan the
#     existing Player.log (debugging the scanner / game just ran)
#   python3 Scripts/integration-smoke-test.py --strict     # any error fails

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "refresh"))
import refresh_expectations as refresh  # noqa: E402

PACKAGE_ID = None
SMOKE_ACTIVE_MODS = None
OWN_PATTERNS = None
INTEGRATION_PATTERNS = None
REPO_ROOT = None

# The probe's own log lines (including its expected per-mod dump failures on
# a smoke list) and its shutdown marker.
TOOLING_PATTERN = "[L10nProbe]"
BOOT_COMPLETE_MARKER = "-l10nprobe run complete; shutting down"

# A log entry is an ERROR when its stack shows Verse.Log.Error (vanilla frame
# "Verse.Log:Error", or "Verse.Log.Error_Patch1" when another mod patched
# Log.Error) or when it is a raw unhandled exception block. Warnings ditto.
ERROR_FRAME = re.compile(r"Verse\.Log[:.]Error")
WARNING_FRAME = re.compile(r"Verse\.Log[:.]Warning")
EXCEPTION_HEAD = re.compile(r"^[\w.]*Exception(:|\b)")


def player_log_path():
    logs = sorted(Path("/mnt/c/Users").glob(
        "*/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios"
        "/Player.log"))
    if not logs:
        sys.exit("No Player.log found under /mnt/c/Users - has the game "
                 "ever run on this machine?")
    return logs[-1]


def launch(rw):
    if refresh.game_is_running():
        sys.exit("RimWorld is already running - the smoke boot needs an "
                 "exclusive launch (mod-list swap). Close the client, then "
                 "rerun this script.")
    log = player_log_path()
    log.unlink(missing_ok=True)  # a stale log must never read as a fresh run
    mc = refresh.modsconfig_path()
    original = mc.read_bytes()
    mc.write_text(refresh.pinned_modsconfig(original.decode("utf-8-sig")),
                  encoding="utf-8")
    print("Launching RimWorld on the pinned smoke mod list "
          "(graphical boot, ~1-2 min; the probe quits the game itself)...")
    try:
        import subprocess
        subprocess.run(["./RimWorldWin64.exe", "-l10nprobe"], cwd=rw,
                       check=False)
    finally:
        mc.write_bytes(original)
        print(f"Restored {mc}")


def split_entries(text):
    # Unity separates log entries with blank lines; the trailing
    # "(Filename: ... Line: ...)" locator line is dropped as noise.
    entries = []
    block = []
    for line in text.splitlines():
        if line.strip():
            if not line.startswith("(Filename:"):
                block.append(line)
        elif block:
            entries.append("\n".join(block))
            block = []
    if block:
        entries.append("\n".join(block))
    return entries


def classify_level(entry):
    if ERROR_FRAME.search(entry) or EXCEPTION_HEAD.match(entry):
        return "error"
    if WARNING_FRAME.search(entry):
        return "warning"
    return None


def classify_origin(entry):
    if TOOLING_PATTERN in entry:
        return "tooling"
    for pattern in OWN_PATTERNS:
        if pattern in entry:
            return "own"
    for name, patterns in INTEGRATION_PATTERNS.items():
        for pattern in patterns:
            if pattern in entry:
                return f"integration:{name}"
    return "other"


def first_line(entry):
    return entry.split("\n", 1)[0]


def report(entries):
    # (level, origin, entry) triples for everything classified.
    findings = []
    for entry in entries:
        level = classify_level(entry)
        if level:
            findings.append((level, classify_origin(entry), entry))

    errors = [f for f in findings if f[0] == "error"]
    warnings = [f for f in findings if f[0] == "warning"]
    gated = [f for f in errors if f[1] != "tooling"]
    hard = [f for f in gated if f[1] != "other"]

    # Dedup by first line, keeping counts, so a spammed error reads once.
    def dedup(fs):
        seen = {}
        for _, origin, entry in fs:
            key = (origin, first_line(entry))
            seen.setdefault(key, [0, entry])[0] += 1
        return seen

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) in the "
          f"boot log ({sum(1 for f in errors if f[1] == 'tooling')} "
          f"tooling error(s) excluded from the gate).")

    if gated:
        print("\n=== ERRORS ===")
        for (origin, head), (count, entry) in dedup(gated).items():
            tag = f" x{count}" if count > 1 else ""
            print(f"\n[{origin}{tag}]")
            print(entry)
    if warnings:
        print("\n=== WARNINGS (not gated) ===")
        for (origin, head), (count, entry) in dedup(warnings).items():
            tag = f" x{count}" if count > 1 else ""
            print(f"  [{origin}{tag}] {head}")

    return hard, gated


def main():
    if None in (PACKAGE_ID, SMOKE_ACTIVE_MODS, OWN_PATTERNS,
                INTEGRATION_PATTERNS):
        sys.exit("startup_smoke engine misconfigured: the shim must assign "
                 "PACKAGE_ID, SMOKE_ACTIVE_MODS, OWN_PATTERNS and "
                 "INTEGRATION_PATTERNS after importing this engine")
    # The refresh engine's pin/restore helpers read its own module globals.
    refresh.PACKAGE_ID = PACKAGE_ID
    refresh.CANONICAL_ACTIVE_MODS = SMOKE_ACTIVE_MODS

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-launch", action="store_true",
                    help="skip launching the game; rescan the existing "
                         "Player.log")
    ap.add_argument("--strict", action="store_true",
                    help="fail on ANY non-tooling error, not just ones "
                         "attributed to this mod or an integration seam")
    args = ap.parse_args()

    rw = refresh.rimworld_path()
    if not args.no_launch:
        launch(rw)

    log = player_log_path()
    text = log.read_text(encoding="utf-8", errors="replace")
    if BOOT_COMPLETE_MARKER not in text:
        sys.exit(f"Boot did not complete: no '{BOOT_COMPLETE_MARKER}' line "
                 f"in {log} - the game hung, crashed, or the L10nProbe "
                 f"never ran. Treat this as a FAILED smoke test.")

    hard, gated = report(split_entries(text))

    failing = gated if args.strict else hard
    if failing:
        print(f"\nSMOKE TEST FAILED: {len(failing)} gating error(s). "
              f"Full log: {log}")
        return 1
    ignored = len(gated) - len(hard)
    suffix = (f" ({ignored} third-party error(s) reported above, not "
              f"gated - rerun with --strict to gate them)" if ignored else "")
    print(f"\nSMOKE TEST PASSED: clean startup on the pinned "
          f"list{suffix}. Full log: {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
