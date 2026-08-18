#!/usr/bin/env python3
# Reference template for a consuming repo's Scripts/check-translations.py.
# This file is NOT itself a working shim — copy it into the mod repo as
# Scripts/check-translations.py and fill in the placeholders below. It is
# also not imported by anything; it exists purely as a worked example kept
# next to the engine it wires up.
#
# Per-repo rationale comments (why this mod requires the DLCs/aliases it
# does, which fields are parity-exempt and why, etc.) live HERE, in the
# shim, not in the shared engine — the engine's own comments only explain
# the mechanism and carry generic examples. See the delta analysis this
# extraction was based on for the kind of detail expected in each rationale
# (defNames, MayRequire gates, compat-root placement).
#
# Usage from the mod repo root (unchanged from before the extraction):
#   python3 Scripts/check-translations.py
#   python3 Scripts/check-translations.py --strict
#   python3 Scripts/check-translations.py --root /path/to/other/checkout

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "l10n" / "checker"))
import check_translations as engine  # noqa: E402  (import after sys.path edit)

# This repo's root, derived from the shim's own location so the checker
# works from any cwd (as it always has).
engine.REPO_ROOT = Path(__file__).resolve().parent.parent

# Fields whose entries legitimately vary per language (RimWorld's
# [TranslationCanChangeCount]-style matching tokens). Most repos leave this
# empty; a repo with e.g. labelKeywords ([TranslationCanChangeCount]) fields
# should exempt them here.
# RATIONALE: <why this mod's fields are/aren't exempt — name the fields>
engine.PARITY_EXEMPT_FIELDS = set()

# DLCs the sidecar must have been generated with. None is NOT a legal value
# here — an empty set() is the correct way to say "no DLC required". Getting
# this right matters: a DLC omitted here lets a sidecar generated without it
# silently pass, even though MayRequire-gated defs are then absent from it.
# RATIONALE: <which DLCs are hard dependencies vs. MayRequire-gated, and by
# which defs — name them>
engine.REQUIRED_DLCS = {"PLACEHOLDER_DLC"}

# Subclass element tag -> def type the probe's dump actually uses (for defs
# declared via a subclass the game rolls into a base-type database). Empty
# for most repos.
# RATIONALE: <which subclass, which base type, and why>
engine.DEF_TYPE_ALIASES = {}

# True only for a mod with no shipped Languages/Keyed tree yet (DefInjected-
# only translatable surface) — reproduces BionicThumbGuild's note-and-
# continue behavior instead of a hard failure. False for every other repo.
# RATIONALE: <why this mod does or doesn't ship a Keyed surface today>
engine.ALLOW_NO_KEYED_SURFACE = False

# The Keyed key whose per-language value is the localized Steam Workshop
# title (the settings-window header). Enforces the title-coupling rule from
# the toolkit's workshop.md: each .steamworkshop/Description/<Language>.txt
# title line must equal this key's value for that language. None for a mod
# with no Keyed surface (format/coverage checks still run).
engine.WORKSHOP_TITLE_KEY = "PLACEHOLDER_SettingsCategory"

raise SystemExit(engine.main())
