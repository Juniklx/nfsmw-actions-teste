# PRE554 — V48 Android edition and VFS runtime evidence gate (passive, read-only)

Date: 2026-11-08 (Bahia), 2026-11-09 UTC. Project: NFSMW-Recompiled-Mobile. Goal: enable safe, genuine BMW M3 GTR career performance tuning only after a real guest loader and subsequent purchase/persistence are verified.

## Source-verified checkpoint

- PRE553 GitHub Actions run 42545813805: success. Original canonical CONTEXTO_NFSMW.md Drive ID 1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB backed up with byte-exact prefix/readback, 844481 bytes after append.
- PRE520 had already authenticated 512 original zero-padding bytes in PAL ZZDATA4; PRE551 independently reconfirmed and combined the real reserved PAL sectors with a virtual ZDIR read of the synthetic VPAK, all in RAM.
- PRE511 confirmed that signed V48 binary contains native image-root, missing-root and mount-failure diagnostics. Marker presence does not mean that a specific diagnostic was emitted on the phone.
- PRE515 confirmed compiled GameActivity.getLibraries reads Ediciones.Edicion.libreria. V48 APK contains libmain.so (PAL) and libmain_usa.so (USA); this is not evidence that one of them was actually selected in the user session.
- The privately analyzed PRE455 BMW/Punto menu logs identified the BMW six zero-count performance categories, but did not independently record installed versionCode, a mounted VFS type, or selected guest library.
- PRE551 synthetic BMW collection engine/bmwm3gtr_upgrade_engine_pre499, engine levels 0->1 and +5% test torque: not accepted by real guest loader. No real installation/price/save evidence.

## PRE554 implementation

Metadata gate: automation/kaggle/pre554_v48_mount_evidence_gate.py. GitHub CI verifies prior reports, exact original V48 identity and unchanged PRE553 context; intentionally records device-session edition and VFS branch as unknown. It does not fetch an APK or game data, and does not touch the certificate or any save.

Phone-side helper: automation/device/pre554_v48_mount_probe.sh. A user with authorized ADB shell can copy this script to /sdcard/Download and run it AFTER starting V48 in an existing session:

    adb push automation/device/pre554_v48_mount_probe.sh /sdcard/Download/
    adb shell sh /sdcard/Download/pre554_v48_mount_probe.sh

Only six allowlisted fields are emitted: package, versionCode, process-running status, /proc PID maps access, exact loaded PAL/USA library basename, and a potential VFS log hint. No raw maps, log lines, URI, personal path, or save contents are emitted. Android may deny reading /proc/PID/maps from shell; treat DENIED/UNKNOWN as not proved. The diagnostic IMAGE_ROOT_LOG alone is only a hint, NOT proof that the mount succeeded. A missing IMAGE_ROOT_LOG is not proof of HostPathDevice.

The GitHub Actions worker cannot remotely inspect the phone. A PRE554 AUDIT_OK only means the safe evidence gate is ready, NOT that device selection or runtime loader is verified.

## Mandatory next gate

1. Obtain versionCode=48 directly from device and an unambiguous active libmain.so or libmain_usa.so process map, or otherwise retain edition as UNKNOWN.
2. Prove the successful real Runtime::SetupVfs branch, disc image/URI versus host folder; no branch can be inferred from merely having both device classes compiled.
3. Run a non-transactional guest-loader experiment ONLY against a private, isolated disposable copy of game data and a disposable save, not MARCEK. First validate GLOBAL/ATTRIBUTES.BIN, ZDIR size/checksum and new engine collection import, then separately FE/catalogue, SetPackage, physics, checkout and persistence.
4. Do not create/install V49 by default, modify original PAL/USA ZIP/ISO, expose files or passwords, disable thermal protection, degrade graphics/fx/physics, or disturb Nitro PRE398, touch/PG-9076, V46/V47/V48, signed certificate 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b, 1920x1080 settings and 120 FPS cap.

## Interpretation
PRE554 can finish its offline preparation with AUDIT_OK while remaining blocked on on-device execution. Never report BMW tuning as functional until real loader, package, FE price, installation and persistence are separately verified.
