#!/usr/bin/env python3
# Shared engine for the family's pre-release integration smoke test: boot the
# real game once with a PINNED mod list (this mod + its integration mods +
# their deps), let it reach a fully loaded main menu, then classify every
# error/warning the boot logged by origin. Consumed by each mod repo via a
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
# check. The boot rides the L10nProbe's -l10nprobe flag: the probe dumps
# whatever its settings say (from the first post-load slot, before any mod's
# static ctor), then, from a later ExecuteWhenFinished delegate - i.e. AFTER
# every mod's static ctor, def write, and (for BTG-style deferred passes)
# post-defs patch application has run and logged - writes the game's own
# in-memory log (Verse.Log.Messages) to Output/log-messages.json and shuts
# the game down. Probe dump failures are expected here (the smoke list
# rarely matches the probe's ticked targets) and are classified as tooling
# noise, never gated on. The dumps a smoke boot DOES write record this
# list in meta.activeMods, so a later refresh --no-launch refuses them
# rather than leaking the integration mods into a sidecar.
#
# WHERE LEVELS COME FROM (the 2026-08-28 blindness fix): RimWorld 1.6 on
# Unity 2022.3 writes NO stack trace under Debug.LogError/LogWarning - a
# 1.6 Player.log has zero Verse.Log frames, zero StackTraceUtility frames,
# zero "(Filename: ...)" locators, and not even a blank line between
# messages. A plain Log.Error (an XML PatchOperation failure, an unresolved
# cross-reference, a mod's own Log.Error) is therefore just its message text,
# indistinguishable from a Log.Message in the file. The level IS recorded
# in memory: Verse.Log keeps every message as a LogMessage with its
# LogMessageType, and the probe persists that queue. So:
#   1. PREFERRED: the probe's log dump supplies (type, text, repeats,
#      stackTrace) for everything that went through Verse.Log. Raw unhandled
#      exceptions Unity logs itself never enter that queue, so Player.log
#      exception blocks are merged in on top (deduplicated by head line).
#   2. FALLBACK (dump absent: probe build predates it, or --no-launch against
#      a foreign log): Player.log is split into per-message entries and
#      levelled by the legacy stack-frame shapes plus message-shape
#      heuristics tied to vanilla call sites (ERROR_MESSAGE_PATTERNS). This
#      cannot see a frame-less warning at all and is announced as degraded;
#      under --strict a launched run without the dump fails outright.
#
# Config variables a shim MUST set before calling main():
#   PACKAGE_ID           str        this mod's own packageId (About.xml)
#   SMOKE_ACTIVE_MODS    list[str]  pinned boot list, LOWERCASE, load order,
#                                   probe's packageId (shunter.l10nprobe) last
#   OWN_PATTERNS         list[str]  substrings attributing a log entry to
#                                   this mod (assembly name, log prefix,
#                                   def/key prefix). RimWorld reports XML
#                                   patch/def failures under the About.xml
#                                   DISPLAY NAME - "[Xenogerm Trader Stock]
#                                   Patch operation ... failed" - so
#                                   "[<display name>]" is derived from
#                                   REPO_ROOT/About/About.xml and appended
#                                   automatically; listing it explicitly too
#                                   is fine and self-documenting.
#   INTEGRATION_PATTERNS dict[str, list[str]]  integration mod display name ->
#                                   substrings (namespaces, log prefixes)
# Optional:
#   REPO_ROOT            Path       consuming repo's root; without it the
#                                   display-name pattern cannot be derived
#
# Gate: exit 1 when any ERROR entry is attributed to this mod or an
# integration seam; --strict widens the gate to every non-tooling error.
# Warnings are reported, never gated. Success requires the boot to actually
# complete (the probe's shutdown line must be present) so a hang or crash
# can't read as a pass, and a log dump whose message count hit the game's
# queue capacity (oldest messages dropped) is a failure too - a gate that
# cannot see is a failed gate.
#
# Usage (from the consuming repo):
#   python3 Scripts/integration-smoke-test.py              # boot + scan
#   python3 Scripts/integration-smoke-test.py --no-launch  # rescan the
#     existing Player.log (+ its dump when present) - debugging the scanner,
#     or the game just ran
#   python3 Scripts/integration-smoke-test.py --strict     # any error fails
#
# Tests: python3 -m unittest discover -s smoke -p 'test_*.py' (repo root).

import argparse
import json
import re
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "refresh"))
import refresh_expectations as refresh  # noqa: E402

PACKAGE_ID = None
SMOKE_ACTIVE_MODS = None
OWN_PATTERNS = None
INTEGRATION_PATTERNS = None
REPO_ROOT = None

# The probe's own log lines (including its expected per-mod dump failures on
# a smoke list), its shutdown marker, and its log-dump marker + location
# (probe/Source/1.6/Core/L10nProbe_Startup.cs, probe/.../Probe/LogDump.cs).
TOOLING_PATTERN = "[L10nProbe]"
BOOT_COMPLETE_MARKER = "-l10nprobe run complete; shutting down"
LOG_DUMP_MARKER = "[L10nProbe] wrote log dump"
# ProbeRunner.RunAll's summary line. The probe writes the log dump AFTER its
# dump pass by design, so a dump without this line was taken too early to
# hold the boot (a probe build whose startup ordering regressed: the first
# cut of the pre-static-ctor timing queued the log dump at slot 0 and a
# three-message dump read as a clean boot, 2026-10-03).
PROBE_SUMMARY_MARKER = "[L10nProbe] probe ("
LOG_DUMP_RELPATH = Path("Mods") / "L10nProbe" / "Output" / "log-messages.json"
LOG_DUMP_SCHEMA = 1
# LogMessageType names as the probe serialises them; Message maps to no level.
LOG_DUMP_LEVELS = {"Error": "error", "Warning": "warning"}

# One levelled log message from either source. `stack` is the probe-captured
# trace (dump) or "" (Player.log); `count` is the dump's `repeats` (a floor
# of 99 when capped) or 1.
Entry = namedtuple("Entry", "level text stack count")

# --- Player.log fallback: level heuristics -------------------------------

# Legacy frame shapes, for builds that DO write stack traces: "Verse.Log:Error"
# (vanilla), "Verse.Log.Error_Patch1" (another mod patched Log.Error).
ERROR_FRAME = re.compile(r"Verse\.Log[:.]Error")
WARNING_FRAME = re.compile(r"Verse\.Log[:.]Warning")
# A raw unhandled exception block: Unity logs the exception's own type name
# as the head line. Also the one thing the dump cannot contain (see header).
EXCEPTION_HEAD = re.compile(r"^[\w.]*Exception(:|\b)")

# Message-shape heuristics for the frame-less 1.6 log. Each pattern names
# the vanilla Log.Error call site that emits it (decompile-verified against
# 1.6.4871 rev591 on 2026-08-28) so it can be pruned when that site changes.
# Checked AFTER WARNING_MESSAGE_PATTERNS so a Log.Warning look-alike is not
# promoted (e.g. the sound-fallback cross-reference message, or "Caught
# exception while loading ...: System.XxxException").
ERROR_MESSAGE_PATTERNS = [
    # Verse.PatchOperation.Complete(string modIdentifier):
    #   $"[{modIdentifier}] Patch operation {this} failed" (+ "\nfile: ...");
    #   called with runningMod.Name, i.e. the About.xml display name.
    re.compile(r"^\[.+\] Patch operation .+ failed$", re.M),
    # Verse.DirectXmlCrossRefLoader: "Could not resolve cross-reference: No
    # {type} named {defName} found to give to ..." and TryResolveDef's
    # "Could not resolve cross-reference to {T} named {defName}".
    re.compile(r"Could not resolve cross-reference"),
    # Verse.XmlToObjectUtils / Verse.XmlInheritance: every "XML error: ..."
    # string (unknown field, Unsaved field, duplicate node name, unresolved
    # or cyclic inheritance, missing parent node).
    re.compile(r"^XML error: ", re.M),
    # Any .NET exception type name, or the word Exception, anywhere: the
    # many Log.Error(ex.ToString()) callers, ModAssemblyHandler "Exception
    # loading {assembly}", DirectXmlToObject "Exception parsing ... to type
    # ..." / "Exception loading from ...", ModContentLoader "Exception
    # loading {T} from file.", ScribeExtractor "Exception parsing node ...",
    # DefDatabase "Exception in ConfigErrors() of ...".
    re.compile(r"\w*Exception\b"),
    # Verse.LoadedModManager "Could not load defs for mod {id}: {ex}",
    # ModAssetBundlesHandler "Could not load asset bundle at {path}",
    # ScribeExtractor "Could not load reference to {T} named {name}",
    # ContentFinder "Could not load {T} at '{path}' in any active mod ...".
    # (NOT "Could not load shader/material" - those are Log.Warning.)
    re.compile(r"Could not load (defs for mod|asset bundle at|reference to|"
               r"\w+ at ')"),
    # Verse.DefDatabase "Failed to find {T} named {defName}. There are N
    # defs of this type loaded.", Graphic_Multi "Failed to find any textures
    # at {path}". (NOT "Failed to find active mod" - Log.Warning.)
    re.compile(r"Failed to find (\S+ named |any textures at )"),
    # Verse.DirectXmlToObject "Could not find type named {name} from node
    # ...", Verse.ParseHelper "Could not find a type named {name}".
    re.compile(r"Could not find (a )?type named "),
    # Verse.DirectXmlCrossRefLoader / DirectXmlToObject "Faulty MayRequire".
    re.compile(r"Faulty MayRequire"),
    # Verse.DefDatabase: "Adding duplicate {T} name: {defName}", "Mod {mod}
    # has multiple {T}s named {defName}. Skipping.", "Config error in {def}:
    # {error}", "Error while resolving references for def {def}: {ex}".
    re.compile(r"Adding duplicate \S+ name: |has multiple \S+s named |"
               r"^Config error in |Error while resolving references for def "),
]

# Vanilla Log.Warning strings that would otherwise trip an error pattern
# above (same decompile pass; every entry is a Warning call site).
WARNING_MESSAGE_PATTERNS = [
    # Verse.DirectXmlCrossRefLoader's sound fallback: the cross-reference
    # message + " (using undefined sound instead)" is a Warning.
    re.compile(r"\(using undefined sound instead\)"),
    # Verse.LoadedModManager "Caught exception while loading mod settings
    # data for {mod}...", Verse.PlayDataLoader "Caught exception while
    # loading play data..." - both carry the exception text.
    re.compile(r"^Caught exception while loading", re.M),
    # ShaderDatabase "Could not load shader {path} ... Using default shader
    # instead.", MatLoader "Could not load material {path}".
    re.compile(r"^Could not load (shader|material) ", re.M),
    # Verse.LoadedModManager "Failed to find active mod {name}({id}) at ...".
    re.compile(r"^Failed to find active mod ", re.M),
    # Verse.Log itself at the 10,000-callback cap.
    re.compile(r"^Reached max messages limit", re.M),
]

# Lines that continue the previous message rather than starting a new one.
# Needed because 1.6 writes no blank line between messages; the only cue
# left is line shape. Order of alternatives is irrelevant.
CONTINUATION_LINE = re.compile(
    r"^\s"                                   # indented: Mono "  at ..." frames,
                                             #   Unity's own detail lines
    r"|^file: "                              # PatchOperation.Complete line 2
    r"|^\[Ref [0-9A-Fa-f]+\]$"               # 1.6 exception reference tag
                                             #   under Log.Error(ex)
    r"|^Parameter name: "                    # ArgumentException.ToString
    r"|^--- End of inner exception"          # nested exception ToString
    r"|^(?:at )?[\w.`<>+,\[\]]+[:.]"         # legacy Unity frame, e.g.
    r"[\w.`<>]+ ?\(.*\)\s*"                  #   "Verse.Log:Error(String)",
    r"(?:\[0x[0-9a-fA-F]+\].*)?$"             #   "UnityEngine.StackTraceUtility:ExtractStackTrace ()"
                                             #   - whole line, so a message that merely
                                             #   starts like a call ("Foo.Bar(x): ok")
                                             #   still starts its own entry
)


def player_log_path():
    logs = sorted(Path("/mnt/c/Users").glob(
        "*/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios"
        "/Player.log"))
    if not logs:
        sys.exit("No Player.log found under /mnt/c/Users - has the game "
                 "ever run on this machine?")
    return logs[-1]


def log_dump_path(rw):
    return Path(rw) / LOG_DUMP_RELPATH


def launch(rw):
    if refresh.game_is_running():
        sys.exit("RimWorld is already running - the smoke boot needs an "
                 "exclusive launch (mod-list swap). Close the client, then "
                 "rerun this script.")
    log = player_log_path()
    # A stale log or dump must never read as a fresh run.
    log.unlink(missing_ok=True)
    log_dump_path(rw).unlink(missing_ok=True)
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
    # One entry per log message. A blank line always ends an entry (the
    # legacy Unity separator); otherwise a line starts a new entry unless it
    # is shaped like a continuation (CONTINUATION_LINE). The trailing
    # "(Filename: ... Line: ...)" locator is dropped as noise.
    entries = []
    block = []
    for line in text.splitlines():
        if not line.strip():
            if block:
                entries.append("\n".join(block))
                block = []
            continue
        if line.startswith("(Filename:"):
            continue
        if block and not CONTINUATION_LINE.match(line):
            entries.append("\n".join(block))
            block = []
        block.append(line)
    if block:
        entries.append("\n".join(block))
    return entries


def classify_level(entry):
    # Fallback levelling of a Player.log entry (see header). Frames first
    # (authoritative when present), then the message-shape heuristics.
    if ERROR_FRAME.search(entry) or EXCEPTION_HEAD.match(entry):
        return "error"
    if WARNING_FRAME.search(entry):
        return "warning"
    for pattern in WARNING_MESSAGE_PATTERNS:
        if pattern.search(entry):
            return "warning"
    for pattern in ERROR_MESSAGE_PATTERNS:
        if pattern.search(entry):
            return "error"
    return None


def entries_from_player_log(text):
    return [Entry(classify_level(e), e, "", 1) for e in split_entries(text)]


def load_log_dump(path, log_text):
    # Returns (entries, truncated) from the probe's log dump, or (None,
    # reason) when it cannot be used. The dump is trusted only when THIS
    # Player.log says the probe wrote it: both files are per-launch, so the
    # marker line ties the dump on disk to the log being read.
    if LOG_DUMP_MARKER not in log_text:
        return None, (f"Player.log has no '{LOG_DUMP_MARKER}' line - the "
                      f"deployed L10nProbe predates the log dump (rebuild it "
                      f"from the canonical rimworld-l10n checkout), or this "
                      f"is a foreign log")
    path = Path(path)
    if not path.is_file():
        return None, f"{path} is missing although Player.log says it was written"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return None, f"{path} is not valid JSON: {e}"
    try:
        meta = data.get("meta") or {}
        if meta.get("schema") != LOG_DUMP_SCHEMA:
            return None, (f"{path} has log dump schema {meta.get('schema')!r}; "
                          f"this engine reads schema {LOG_DUMP_SCHEMA}")
        entries = [Entry(LOG_DUMP_LEVELS.get(m.get("type")), m.get("text") or "",
                         m.get("stackTrace") or "", int(m.get("repeats") or 1))
                   for m in data.get("messages") or []]
    except (AttributeError, TypeError, ValueError) as e:
        return None, f"{path} is not shaped like a log dump: {e!r}"
    if not any(e.text.startswith(PROBE_SUMMARY_MARKER) for e in entries):
        return None, (f"{path} holds no '{PROBE_SUMMARY_MARKER}...' summary "
                      f"line, which the probe logs before writing the dump - "
                      f"the dump was taken too early to hold the boot "
                      f"(rebuild the probe from the canonical rimworld-l10n "
                      f"checkout)")
    capacity = meta.get("queueCapacity")
    truncated = capacity is not None and len(entries) >= capacity
    return entries, truncated


def merge_player_log_exceptions(dump_entries, player_log_entries):
    # Raw exception blocks Unity logged itself never pass through Verse.Log,
    # so they are missing from the dump; add them, skipping any whose head
    # line the dump already carries (Log.Error(ex.ToString()) shows up in
    # both places with the same first line).
    heads = {first_line(e.text) for e in dump_entries}
    extra = [e for e in player_log_entries
             if EXCEPTION_HEAD.match(e.text) and first_line(e.text) not in heads]
    return list(dump_entries) + extra


def display_name_pattern():
    # RimWorld attributes patch/def failures to a mod by its About.xml <name>
    # (Verse.PatchOperation.Complete is called with runningMod.Name), so the
    # bracketed display name is an OWN pattern every consumer needs; derive
    # it rather than trust each shim to keep it in sync.
    if REPO_ROOT is None:
        return None
    about = Path(REPO_ROOT) / "About" / "About.xml"
    if not about.is_file():
        return None
    m = re.search(r"<name>\s*([^<]+?)\s*</name>",
                  about.read_text(encoding="utf-8-sig", errors="replace"))
    return f"[{m.group(1)}]" if m else None


def classify_origin(entry):
    # `entry` is the message text plus, when known, its stack trace: an
    # error raised inside an integration mod's code but caused by ours (the
    # BTG/CWTL incident) is attributed through the frames.
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


def first_line(text):
    return text.split("\n", 1)[0]


def report(entries):
    # (level, origin, entry) triples for everything levelled.
    findings = []
    for entry in entries:
        if entry.level:
            origin = classify_origin(entry.text + "\n" + entry.stack)
            findings.append((entry.level, origin, entry))

    errors = [f for f in findings if f[0] == "error"]
    warnings = [f for f in findings if f[0] == "warning"]
    gated = [f for f in errors if f[1] != "tooling"]
    hard = [f for f in gated if f[1] != "other"]

    def total(fs):
        return sum(f[2].count for f in fs)

    # Dedup by first line, keeping counts, so a spammed error reads once.
    def dedup(fs):
        seen = {}
        for _, origin, entry in fs:
            key = (origin, first_line(entry.text))
            seen.setdefault(key, [0, entry])[0] += entry.count
        return seen

    print(f"\n{total(errors)} error(s), {total(warnings)} warning(s) in the "
          f"boot log ({total([f for f in errors if f[1] == 'tooling'])} "
          f"tooling error(s) excluded from the gate).")

    if gated:
        print("\n=== ERRORS ===")
        for (origin, head), (count, entry) in dedup(gated).items():
            tag = f" x{count}" if count > 1 else ""
            print(f"\n[{origin}{tag}]")
            print(entry.text)
            if entry.stack:
                print("\n".join("    " + l for l in entry.stack.splitlines()))
    if warnings:
        print("\n=== WARNINGS (not gated) ===")
        for (origin, head), (count, entry) in dedup(warnings).items():
            tag = f" x{count}" if count > 1 else ""
            print(f"  [{origin}{tag}] {head}")

    return hard, gated


def main():
    global OWN_PATTERNS
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
                         "Player.log (and its log dump when present)")
    ap.add_argument("--strict", action="store_true",
                    help="fail on ANY non-tooling error, not just ones "
                         "attributed to this mod or an integration seam; "
                         "also fail a launched run that produced no log dump")
    args = ap.parse_args()

    name = display_name_pattern()
    if name and name not in OWN_PATTERNS:
        OWN_PATTERNS = list(OWN_PATTERNS) + [name]
    elif not name:
        print("warning: could not derive '[<display name>]' from "
              "REPO_ROOT/About/About.xml - patch/def failures RimWorld "
              "reports under the display name will only be attributed to "
              "this mod if OWN_PATTERNS lists it")

    rw = refresh.rimworld_path()
    if not args.no_launch:
        launch(rw)

    log = player_log_path()
    text = log.read_text(encoding="utf-8", errors="replace")
    if BOOT_COMPLETE_MARKER not in text:
        sys.exit(f"Boot did not complete: no '{BOOT_COMPLETE_MARKER}' line "
                 f"in {log} - the game hung, crashed, or the L10nProbe "
                 f"never ran. Treat this as a FAILED smoke test.")

    player_log_entries = entries_from_player_log(text)
    dump_entries, detail = load_log_dump(log_dump_path(rw), text)
    if dump_entries is None:
        print(f"\nWARNING: no usable log dump ({detail}). Falling back to "
              f"Player.log heuristics: a 1.6 log carries no stack traces, "
              f"so frame-less warnings are invisible and errors are "
              f"recognised by message shape only.")
        entries = player_log_entries
        if args.strict and not args.no_launch:
            sys.exit("SMOKE TEST FAILED: --strict requires the probe's log "
                     "dump for a launched run - the gate is blind without "
                     "it. Rebuild and redeploy L10nProbe from the canonical "
                     "rimworld-l10n checkout, then rerun.")
    else:
        if detail:  # truncated
            sys.exit(f"Boot log overflowed the game's message queue "
                     f"({len(dump_entries)} messages, oldest dropped): the "
                     f"pinned list is far too noisy to gate. Treat this as "
                     f"a FAILED smoke test. Full log: {log}")
        entries = merge_player_log_exceptions(dump_entries, player_log_entries)
        print(f"\nLevels from the probe's log dump ({len(dump_entries)} "
              f"messages) plus {len(entries) - len(dump_entries)} raw "
              f"exception block(s) from Player.log.")

    hard, gated = report(entries)

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
