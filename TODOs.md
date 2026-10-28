# TODOs

## Languages

- The VFE Pirates warcasket vocabulary is tagged (v1.7.1, 2026-10-28). Consumer follow-ups at each repo's next pin moment (release or pass start): bump Medic Warcasket's pin before its first translation pass, since its glossaries point at that section; then drop the duplicated "Inherited rows" sections from the Shipcracker, Toxin and Overlord Warcasket glossaries, leaving only their set-specific rows (the Toxin glossaries' VFEP-domain rows outside the inherited section — set names, the openers, `TXWC_SpacerLoreGeneration` — go too). The move surfaced three family splits to settle in Shipcracker at that pass: its French shoulders text pluralises the invariable modifier ("Épaulières warcaskets spécialisées"; Toxin and the glossary rule say "warcasket"), its zh-Hant 10th-generation opener says 戰棺外殼 for "shell" where Toxin and the zh-Hans pack say 戰棺裝甲, and its zh-Hant Keyed ships 空襲型 for the Aerial set where the pack's 突击型 converts to 突擊型

- Re-check the multi-word-label plural finding (landed 2026-10-28 in `lessons.md` and the fr/es/de/pt-BR/ru language files, verified on 1.7.4981) against 1.6.4871 at the next 1.6 branch switch, and drop the "recheck owed" clause from the lesson

## Refresh and smoke

- Per-world mod settings: `pinned_boot` (v1.8.0) runs every pinned mod on its default settings. A consumer that needs a toggled-on world exercised (ToxinWarcasket's `SpacerTier`, which rewrites def stats, costs, research and descriptions) wants a `WORLD_SETTINGS = {world: xml}` dimension beside `WORLDS` plus a second smoke boot, and the checker would then need to know which world holds which English. Build it when the first consumer asks

- The smoke engine attributes an unresolved cross-reference to the consumer when its own XML wants the def (v1.8.0). The integration half of BetterTradersGuild's ledger item is still open: an integration mod's broken reference stays `other`, because the engine does not know the integration mods' folders. `refresh.mod_folders` now maps packageIds to local `Mods/` folders; extending it to Workshop content (`steamapps/workshop/content/294100/<id>`, packageId from About.xml) would let `classify_origin` scan each `INTEGRATION_PATTERNS` mod's XML too

## Tooling notes

- RimWorld 1.7's `-mod=` launch flag was evaluated 2026-10-28 and rejected for the pinned boots (see `lessons.md`'s tooling section for the decompiled mechanics); revisit only if a later unstable build loads Workshop subscriptions and honours an omitted expansion
