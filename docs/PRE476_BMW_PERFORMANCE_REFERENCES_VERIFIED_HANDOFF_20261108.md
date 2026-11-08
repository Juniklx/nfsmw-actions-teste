# NFSMW Android — PRE476 handoff (8 Nov 2026)

## Goal
Develop real customizable performance tuning for BMW M3 GTR in the Android Xbox 360 PAL recompile, with the V48 build and MARCEK save preserved. No current mod enabling BMW tuning has been generated.

## Read-only source provenance
- Original user PAL `GLOBAL\\ATTRIBUTES.BIN` from `NFSMW_PAL.zip` was independently authenticated in PRE467 as byte-identical to USA source, SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`.
- PRE473 verified `pvehicle` seven performance counters: BMW `bmwm3gtr` and `m3gtre46careerstart` = engine0, transmission0, chassis0, nos3, tires0, brakes0, induction0. Punto = engine4, transmission4, chassis3, nos3, tires3, brakes4, induction3. Matches runtime V48 PRE455.
- PRE474: for engine/transmission/chassis/tires/brakes, BMW only has one explicit RefSpec (own collection); Punto has two RefSpecs: primary `0xA6EE7A11` and derived `0xA6F0F405`. The array count is **not** number of purchasable levels.
- PRE476 [GitHub Actions #42511463983](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42511463983) **AUDIT_OK**. Report: `docs/PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY.json`. All 2339 collection records indexed; 0 missing referenced targets in checked explicit arrays.
- `0xA6F0F405` exists as an actual collection in **engine, transmission, chassis, tires, brakes, induction** classes. In the first five classes it inherits from Punto primary `0xA6EE7A11`, which inherits `default`. For induction it inherits `0x1BCDB55E` then default. It does not exist as `nos` class; original data does not claim otherwise.
- The regular `bmwm3gtr` engine/transmission/tires/brakes collections inherit `default`; chassis inherits `0x4E085FB3` then default. `m3gtre46careerstart` for those five classes inherits `0x4E085FB3` then default. Nitro original arrays point to two valid class-specific NOS collections.
- PRE476 records `optional_attribute_count:0` for these performance-class collections; **this does not mean their physical parameters are identical**, because actual base layouts are in the BIN section. PRE477 targets that distinction.

## Critical correction of tempting dead-end
PRE470–472 observed `UpgradeSpecs` in BMW pvehicle, but the fields are `ShiftSND` and `TurboSND`: these are audio reference fields. They are not the seven performance category counts or valid purchase catalog items. Original generated `pvehicle.h` lists seven independent signed Int32 counters in the base layout. Do NOT modify ShiftSND/TurboSND arrays to enable performance purchases.

## PRE477 status / fail-closed gate
The script `automation/kaggle/pre477_pal_bmw_punto_physics_layout_compare.py` and workflow `.github/workflows/nfsmw-pre477-pal-physics-layout-compare.yml` are committed and request files submitted for original PAL BMW-vs-Punto BIN physical layout comparison. The workflow was improved to persist a sanitized diagnostic if a run fails. **As of this handoff, neither a PRE477 AUDIT_OK report nor a failure diagnostic had been retrieved; no claims about measured physics differences are justified until one is fetched.**

## Next engineering gates
1. Inspect PRE477 `docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json` or diagnostic; if failure, fix specific source mismatch, rerun only verified/read-only parser. Verify actual base physical class sizes and layout SHA, never assume PC offsets match X360 without checking.
2. Trace `*_current` and `*_upgrades` in original `pvehicle`; verify how valid engine/transmission/chassis/brakes/tires profiles are selected at each level and where price/FE catalog records come from. Distinguish `bmwm3gtr` from `m3gtre46careerstart`.
3. Develop only an isolated reversible BMW-specific proof-of-concept overlay after game original data, actual compatible profiles, catalog, runtime physics and save-persistence have been verified. Flag default OFF; do not copy Punto numeric values blindly.
4. Test on disposable save, verify stability, regression: controls PG-9076, Nitro PRE398, V48 behavior, other cars, shader/graphics, signing. Only thereafter build a signed experimental APK; preserve `MARCEK` and stable V48 at every step.

## No-modification attestation
PRE476 read only original attribute records and wrote *metadata* in private GitHub Actions/docs. No altered PAL archive, game asset exports, APK builds, or save writes.
