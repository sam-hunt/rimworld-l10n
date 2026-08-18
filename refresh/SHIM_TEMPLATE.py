#!/usr/bin/env python3
# Reference template for a consuming repo's
# Scripts/refresh-translation-expectations.py. This file is NOT itself a
# working shim — copy it into the mod repo as
# Scripts/refresh-translation-expectations.py and fill in the placeholders
# below. It is also not imported by anything; it exists purely as a worked
# example kept next to the engine it wires up.
#
# Per-repo rationale comments (which DLCs/mods are pinned and why — hard
# deps, MayRequire gates, family-sibling grouping) live HERE, in the shim,
# not in the shared engine — the engine's own comments only explain the
# mechanism, the general membership rule, and the standing operational
# warnings (lowercase ids, no-contamination pinning). See the delta analysis
# this extraction was based on for the kind of detail expected in each
# rationale (defNames, transitive deps, family framing).
#
# Usage from the mod repo root (unchanged from before the extraction):
#   python3 Scripts/refresh-translation-expectations.py            # launch + refresh
#   python3 Scripts/refresh-translation-expectations.py --no-launch  # reuse the
#     dump already in the probe's Output folder (debugging / probe just ran)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "l10n" / "refresh"))
import refresh_expectations as engine  # noqa: E402  (import after sys.path edit)

# This repo's root, derived from the shim's own location so the refresh
# works from any cwd (as it always has).
engine.REPO_ROOT = Path(__file__).resolve().parent.parent

# This mod's own packageId, from About/About.xml.
# RATIONALE: <none usually needed — this is just the mod's identity>
engine.PACKAGE_ID = "shunter.placeholder"

# The exact list the probe boots with — deterministic expectations need a
# deterministic def graph. Order is load order; the probe's own packageId
# (shunter.l10nprobe) must be last. See the engine's own header comment for
# the general membership rule this list must satisfy; the rationale below is
# specifically why THIS mod's list looks the way it does.
# RATIONALE: <which DLCs are hard-required or MayRequire-gated and by which
# defs; which third-party mods are hard deps (and their own transitive hard
# deps); whether this repo is part of a "family" that boots together and, if
# so, which sibling packageIds ride along and why>
engine.CANONICAL_ACTIVE_MODS = [
    "brrainz.harmony",
    "ludeon.rimworld",
    "shunter.placeholder",
    "shunter.l10nprobe",
]

raise SystemExit(engine.main())
