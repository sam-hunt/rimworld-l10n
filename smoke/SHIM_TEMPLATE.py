#!/usr/bin/env python3
# Reference template for a consuming repo's Scripts/integration-smoke-test.py.
# This file is NOT itself a working shim - copy it into the mod repo as
# Scripts/integration-smoke-test.py and fill in the placeholders. It is not
# imported by anything; it exists purely as a worked example kept next to the
# engine it wires up.
#
# Per-repo rationale comments (why each mod is on the smoke list, which
# integration seams exist) live HERE in the shim, not in the shared engine.
#
# Usage from the mod repo root:
#   python3 Scripts/integration-smoke-test.py              # boot + scan
#   python3 Scripts/integration-smoke-test.py --no-launch  # rescan last log
#   python3 Scripts/integration-smoke-test.py --strict     # any error fails

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "l10n" / "smoke"))
import startup_smoke as engine  # noqa: E402

engine.REPO_ROOT = Path(__file__).resolve().parent.parent

# This mod's own packageId, from About/About.xml.
engine.PACKAGE_ID = "shunter.placeholder"

# The pinned boot list: Core + required DLCs + EVERY optional mod this repo
# integrates with (each one activates conditional patches/reflection that
# never run otherwise - the exact class of code a startup smoke test exists
# to exercise) + those mods' own hard deps. All ids LOWERCASE (MayRequire is
# case-exact against ModsConfig; see the refresh engine's warnings). The
# probe (shunter.l10nprobe) goes last - it supplies the auto-quit.
# RATIONALE: <why each non-obvious entry is here>
engine.SMOKE_ACTIVE_MODS = [
    "brrainz.harmony",
    "ludeon.rimworld",
    "shunter.placeholder",
    "shunter.l10nprobe",
]

# Substrings attributing a Player.log entry to THIS mod: assembly/namespace,
# bracketed log prefix, def/key prefix.
engine.OWN_PATTERNS = ["Placeholder", "[Placeholder Mod]", "PLC_"]

# Integration display name -> substrings (the other mod's namespaces and log
# prefixes). An error mentioning any of these gates the test: it means an
# integration seam regressed, even if the exception fires inside their code
# (the BTG/CWTL incident surfaced as an error inside CWTL's own cctor).
engine.INTEGRATION_PATTERNS = {}

raise SystemExit(engine.main())
