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
#     dump already in the probe's Output folder (debugging / probe just ran;
#     with WORLDS, the per-world <packageId>.<world>.json dumps)

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

# ALTERNATIVE, in place of CANONICAL_ACTIVE_MODS (never both): WORLDS, when
# some key exists only in some configurations. The case that needs it: a
# LoadFolders-gated compat root whose Patches/ add a [MustTranslate] field
# to a main-tree def (that key appears under the main-tree def, but only
# while the gate is active), or a gate that rewrites a main-tree field's
# English. One pinned list with the gate would record the key as if it
# always existed, and the checker would demand its translation in the main
# tree, a startup error on every install without the gate. WORLDS boots
# once per entry and records which worlds hold each key, so the checker can
# demand the translation in the root active in exactly those worlds. Order
# matters: the first world is the base (normally the list above, without
# any optional gate); each later world follows the same membership rule.
# Names are file-name safe (letters, digits, '-', '_').
# RATIONALE: <which gate creates world-dependent keys, via which Patch>
# engine.WORLDS = {
#     "base": [
#         "brrainz.harmony",
#         "ludeon.rimworld",
#         "shunter.placeholder",
#         "shunter.l10nprobe",
#     ],
#     "gate": [
#         "brrainz.harmony",
#         "ludeon.rimworld",
#         "author.gatemod",
#         "shunter.placeholder",
#         "shunter.l10nprobe",
#     ],
# }

raise SystemExit(engine.main())
