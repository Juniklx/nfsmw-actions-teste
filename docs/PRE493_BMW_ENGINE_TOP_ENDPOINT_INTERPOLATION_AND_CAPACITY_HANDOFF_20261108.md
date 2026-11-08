# PRE493 — BMW M3 GTR real-upgrade hypothesis and data-capacity handoff (2026-11-08)

## Purpose and current state
User's objective: unlock physically functional, purchasable performance tuning for the career BMW M3 GTR in the Android Xbox 360 PAL recompiled NFSMW. **Not implemented yet**. Stable APK V48 PRE452, Nitro infinite PRE398 and user save MARCEK remain protected. No patch, replacement APK or game/ROM content modified.

## Confirmed source state
- PRE467 original PAL `GLOBAL\\ATTRIBUTES.BIN` and USA for *this same file* are byte-identical, SHA-256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`.
- PRE473 confirms `bmwm3gtr` and `m3gtre46careerstart` have original per-category upgrade limits zero for engine/transmission/chassis/tires/brakes/induction, NOS remains 3. Original Punto has positive 4/4/3/3/3/4/3 limits.
- PRE474 BMW `bmwm3gtr` engine array is located at BIN relative `256660`, `capacity=1,count=1,element_size=12` with one `RefSpec(engine,bmwm3gtr)`. Other blocked categories also have capacity1. Punto has two-entry arrays with base `punto` and derived profile `0xA6F0F405`.
- PRE477 verifies class-specific original physical blocks, including different Punto base vs fully modified scalar values. PRE481 finds `bmwm3gtr` and `m3gtre46careerstart` as actual named original BMW class collections; **not buyable levels**.

## PRE490: original guest ABI investigation
- Read-only source audit `automation/kaggle/pre490_pal_function_argument_return_trace_readonly.py`, GitHub Action [42517016343](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42517016343), started and running when this handoff was written. **The result of PRE490 has NOT been declared AUDIT_OK here.** Retrieve `docs/PRE490_PAL_FUNCTION_ARGS_RETURNS_READONLY.json`, or sanitized diagnostic, and the Actions run status before making claims.
- Audits 13 selected PAL functions including `sub_823E5B08`, `sub_823E6560`, `sub_823E67E8`, the `sub_823E5988` attribute lookup and menu `sub_82582F70`; records guest PPC callsite/register syntax, returns, and memory write metadata. PRE489 remains the verified predecessor.
- **No Xbox 360 PAL `Physics::Upgrades::SetLevel`, `SetPackage`, `GetMaxLevel` has been conclusively identified yet.** The reverse-engineered PC executable addresses are not the same as PAL Xbox guest addresses.

## PRE491: first documented end-point interpolation hypothesis, OFFLINE ONLY
- Audit [42517561288](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42517561288) `AUDIT_OK`, 25 mathematical checks, report `docs/PRE491_PAL_PC_UPGRADE_INTERPOLATION_HYPOTHESIS.json`. Source data strictly previously authenticated PRE473/PRE474/PRE477 PAL; no new ROM read.
- Independently consulted [MagicIbrar/nfsmw-unity PC v1.3 physics specification](https://github.com/MagicIbrar/nfsmw-unity/blob/336fb872d698377b586cfab75d70c5828c77086c/NFSMW_RE/specs/physics.md), blob `b627fc7db26de515cdbc87d4f2f70331c6596b64`. It describes a `Physics::Upgrades::SetLevel` algorithm based on two `RefSpec` endpoints and interpolation `value(L)=lerp(stock,top,L/N)`, for five categories, and three references in certain NOS/induction cases. **This documentation is derived from the PC v1.3 engine, not verified Xbox PAL runtime behavior.**
- Cross-check with original PAL Punto: the five visible performance categories have stock/derived refs (two) and positive maximum levels. Using reported original PAL scalar endpoints and the *PC model*, Punto transmission `FINAL_GEAR` 3.70 -> 2.50 over four levels gives simulated intermediate 3.40, 3.10, 2.80; Punto brakes `EBRAKE` 350 -> 700 gives 437.5,525,612.5. These intermediate numbers are **offline computed values, not gameplay measurements**.
- The car-specific BMW stock engine has a single RefSpec (N=0), so there is *no* warranted BMW interpolation or tune activation yet. This is not yet a valid inference that adding a top endpoint will work in PAL.

## PRE492: source-validated capacity blocker
- Audit [42517721026](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42517721026) `AUDIT_OK`, report `docs/PRE492_PAL_BMW_REFSPEC_CAPACITY_RELOCATION_GATES.json`.
- Every original blocked `bmwm3gtr` category **engine, transmission, chassis, tires, brakes** has a one-reference **fixed-capacity** RefSpec array `capacity=count=1`, so it cannot gain a second reference by merely increasing `count`. A second valid endpoint requires a *new bounded array allocation* and a verified relocated pointer/fixup entry, plus a new or existing valid BMW-specific physical top endpoint. `bmwm3gtr` has no explicit induction reference, a separate blocker.
- No patch data was written. Raising `*_upgrades` alone or overwriting array boundaries is **unsafe** and does not create actual tuning.

## Implementation focus
**Most economical hypothesis to test:** a BMW-specific, *data-defined*, disabled-by-default engine top endpoint + a new two-reference array + correct VLT PtrN linkage + positive engine upgrade counter. This may let the existing game physics interpolator perform the work without hooking generic AttribSys internals. However, PAL runtime interpolation and loading behavior **must first be proved**; source data layout must be repackable and reversible without touching V48.
1. Confirm actual PRE490 results; if source download is unusually slow, do not claim completion or schedule recurrent huge 875MB downloads.
2. Establish valid pointer relocation/collection creation algorithm with a *scratch in-memory copy* of SHA-pinned VPAK. Validate re-parse, pointer boundaries, class and car identity; do not generate a playable APK.
3. Need actual custom BMW top torque curve and explicit tuning goal; avoid arbitrary power multipliers or recycling a Punto calibration.
4. Validate feature pricing/FE catalog, type41 ↔ `bmwm3gtr` runtime, application, save roundtrip on disposable save, before any signed experimental build.
5. Protect Nitro PRE398, controller PG-9076, shader/performance changes and the user's saved `MARCEK`.

## Results boundary
No V49 created, no gameplay tuning available, no new cheats applied, no save modified, no actual runtime interpolation measured. PRE491 and PRE492 only prove metadata compatibility with a **PC-derived hypothesis** and an original **array-capacity blocker**.
