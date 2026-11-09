# PRE595 — PRE592 real-device MARCEK load + one-byte pvehicle engine counter isolation (2026-11-09)

**Source:** direct user message "Consegui carregar" after applying the PRE592 RefSpec-pointer-only candidate, with uploaded `nfsmw.log` from the Samsung Galaxy S24 FE. The user did **not** paste the exact `PRE592_RESULTADO` application output or on-phone ZDIR/ZZDATA4 checksums. Classify the build/application state as **reported by user**, not independently read back from Android flash.

## Actual uploaded log, inspected locally

- File: `nfsmw.log` attached to this chat. **112,401 bytes**, **675 lines**, SHA-256 **`842fbc19031e81adb7988ad3e2fbd2de35850ce19abde581681025c4172ed1b9`**.
- One session, from `2026-11-09 04:27:55.751` to `04:28:14.945` as logged. Do not merge this session with the older three concatenated sessions from PRE593.
- `04:27:56.513`: VFS mounted `/storage/emulated/0/NFSMW_PTBR` as `\\Device\\Harddisk0\\Partition1`, read-only, **28 entries**. Entry count is not evidence of file identity or on-phone resource checksum.
- `04:27:57.531`: normal direct-file fallback warning `D:\\GLOBAL\\ATTRIBUTES.BIN` -> `0xc000000f`; `04:27:57.574`: explicit IO log of **5,018,060 B from `NFS\\ZZDATA4.BIN` at offset 37,898,240**. **No explicit read of the VPAK at ZZDATA4 offset 0 in this log.** This means successful parsing of the new extra VLT collection/RefSpec cannot be proven from this one runtime IO line alone; user-reported successful game/profile load is stronger on this specific outcome.
- `04:28:07.168, 04:28:07.734, 04:28:07.784, 04:28:10.911`: four `XamContentCreate` operations for `MARCEK` of **62,688 B** in `rmcsave`, all `resultado 00000000`; accompanying file copy to private `saves/MARCEK/actual`. **No proven semantic checksum/upgrade persistence in log**; actual save load success is the user's first-hand result.
- No `[error]`, `[critical]`, or `[fatal]` records; warnings include slow IO and direct-path lookup fallback. No `NFSMW_PRE292_BMW_MENU` or `NFSMW_PRE429_ENTRY` marker in this session: **do not claim the BMW menu was accessed in the PRE592 session**. C3 texture diagnostics alone are not errors.
- Internal resolution **1920×1080**, currently logged FPS cap **60** despite target 120. No change to quality or thermal safeguards and no FPS optimization proven.

## Binary provenance and strongest controlled inference

- PRE591 CI metadata [run 42567684579](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42567684579), `AUDIT_OK`, establishes VPAK candidate SHA256 `b84d1ec037b656063ded48f8ea1e075d6c8425ba438e6366d301fc308c7c9358`, **698,004 B**, EA checksum `98e13bed`. It contains a new `VLT/ExpN/PtrN` engine collection, active pvehicle `RefSpec` pointer to a two-element stock+new array, and **engine-upgrade counter 0**.
- PRE502/572 combined VPAK SHA256 `d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6` and EA checksum `4d05584a` contains the same enlarged VLT and active `RefSpec` pointer, but **engine-upgrade counter 1**. The PRE591 builder verified that the combined VPAK and PRE591 candidate differ **only at absolute VPAK byte offset 256619**, the least significant byte of the 32-bit big-endian counter at VPAK offset **256616** (BIN-relative **256488**). The ZDIR/EA metadata necessarily have different checksums.
- PRE573 / combined with counter 1 caused UI warning `MARCEK está corrompido`; PRE587 / new collection but inactive RefSpec and counter 0 **loaded**; PRE592 / active RefSpec but counter 0 **loaded according to user**. Other relevant tests: PTBR original loaded; PRE581 / torque-only loaded.
- **Strong inference, not deterministic cause proof:** activating the **engine-upgrade counter 0→1** is the remaining isolated candidate for the previous profile-load failure **in this experimental resource construction**, or the trigger for how the game traverses an existing invalid/incomplete newly referenced engine record. This does NOT mean the 0→1 integer is inherently invalid across all cars, nor prove the save was physically corrupt.
- Existing PRE473 shows original BMW engine-upgrades value **0**; original Punto value **4**. Original BMW engine `RefSpec` count/capacity **1**; PRE591 new array count/capacity **2**, pointer active; PRE592 successful load with count 0 does not establish that the guest resolves/validates the second element for motor level 1.
- **Important unresolved:** the synthetic collection's class-qualified hash is new but **name missing original StrE** (PRE502). Whether this affects guest lookup when the counter reaches level 1 is not known. Original guest `GetMaxLevel/SetLevel` semantics, FE part catalogs, purchase/installation and torque effect remain unproven.
- **Do not replay the failing PRE573** just to reconfirm the counter: that test already exists, and PRE591 validates one-byte binary difference. The next gate should inspect guest callsites and actual counter semantics or diagnose the missing collection registration/lookup as the potential cause, preferably read-only/CI before another phone mutation.

## Current active assets and next steps

- The user reports PRE592 currently applied, successful career load. **Do not assume it has been restored yet**, or apply PRE573/PRE587/other fragments on top.
- Before a future device patch, close the V48, then use `pre592_restore_bmw_refspec_pointer_only_shevery.sh` on `/storage/emulated/0/NFSMW_PTBR` and require `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`; keep original files and backup until verified.
- No new APK: V48 PRE452 package `io.github.nfsmwrecomp`, permanent signing SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Preserve Nitro PRE398, PG-9076/touch, 1920×1080, desired cap 120, all shaders/effects/physics, thermal protection. User accepted creating another save but did not ask to delete `MARCEK`.
- All checks of the uploaded log occurred locally in chat, and this written report contains only redacted/limited diagnostic facts. No game assets, APK or user save are changed by logging this checkpoint.

**Status:** PRE592 **career load success reported by user, compatible log**, PRE591 exact binary diff proven via CI; **BMW buyable/installed/tunable and physical +5% NOT proven**. The next experiment should address the counter/second-collection path safely, not conflate loaded saves with completed tunability.
