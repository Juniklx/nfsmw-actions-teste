# PRE554 — Shevery Android real-device read-only observations (2026-11-08, America/Bahia)

## Provenance
Manually provided console outputs by the tester in this conversation. The connected GitHub runner has NOT queried the phone. No raw logcat contents, paths, personal data, game assets or saves were uploaded.

## Device evidence
- ADB/Shevery console command `dumpsys package io.github.nfsmwrecomp | grep -m1 versionCode`: `versionCode=48 minSdk=26 targetSdk=35`. An expected `Broken pipe` came from early grep termination, not evidence of game failure.
- `pidof io.github.nfsmwrecomp`: `7430` during the observations; indicates app process running.
- `/proc/7430/maps` read: `SEM_ACESSO_OU_PROCESSO_ENCERRADO`, with process PID observed concurrently. Therefore cannot identify loaded `libmain.so` vs `libmain_usa.so` from maps.
- `logcat -d --pid=7430 -t 8000` was accessible. App-PID-filtered log contained 140 lines during this sampling.
- No matches in the sampled lines for `game_data_root es una imagen de disco`, `game_data_root is a disk image`, `game_data_root does not exist`, `Failed to initialize game data device`, `Failed to register host path device`.
- Tester reports the installed PT-BR translation is based on PAL, supporting PAL as the *working game-data hypothesis*. It does NOT establish which native library was loaded or whether the runtime mounted a disc image or host path.

## Conservative interpretation
- `phone_versionCode_48_independently_observed=true`.
- `phone_app_process_observed_running=true`.
- `phone_logcat_accessible=true`, `sampled_app_pid_log_lines=140`.
- `device_session_library_maps_observed=false`, `device_session_guest_edition=UNKNOWN`.
- `device_session_vfs_mount_branch_proven=false`, `device_session_vfs_mount_source_proven=false`.
- `actual_game_guest_loader_executed_with_synthetic_vpak=false`.
- `actual_bmw_tuning_available_bought_or_persistent=false`.
- `APK_built=false`, `save_modified=false`, `game_assets_modified=false`.

## Next evidence
Repeat a read-only bounded marker summary immediately following a normal app close-and-relaunch (not a data reset and not clearing logcat), or use UI-confirmed edition/data-selection configuration to constrain hypotheses. Absence of the optional log markers must not be treated as a failed mount. Preserve V48, PAL/USA source, original save MARCEK, Nitro PRE398 and prior controls.

## Subsequent Shevery observation (same device)
Tester attempted to exit/reopen V48, then collected a new logcat sample:
- `PRE554_NOVO_PID=7430`: same PID as before. This does **not confirm** a full process death/restart; the original Android process may have remained alive.
- `PRE554_LINHAS=5`: five lines were accessible in this filtered sample.
- `PRE554_RAIZ=NAO_IDENTIFICADO`
- `PRE554_IMAGEM=NAO_IDENTIFICADO`
- `PRE554_PASTA=NAO_IDENTIFICADO`
- `PRE554_LIB_PAL=NAO_IDENTIFICADO`
- `PRE554_LIB_USA=NAO_IDENTIFICADO`

**Decision:** Do not repeat the same sparse logcat marker probe; pivot to prior authenticated compiled V48 logic. PRE515 proves the static `SetupActivity.edicionAlJugar` → `Ajustes.iso/uriIso/xexIso`/ `IsoXex.mirar` → `Ediciones` selection chain and `GameActivity.getLibraries` reads `Ediciones$Edicion.libreria`. A PAL-based translation constrains the expected game-data edition but is not an active-library trace. The actual source chosen in the device UI remains unobserved. No real VFS mount proof nor BMW loader verification exists. No modification to APK, save or game assets.

## Earlier user-reported runtime setup context (not fresh device trace)
From earlier user conversation on 2026-11-02, user reported opening their fork with original PAL `default.xex` and extracted `NFS`/`Movies` PT-BR directory data, **without an ISO**. This is a strong historical reason to prioritize the extracted-folder/HostPathDevice route in subsequent source inspections, instead of defaulting to DiscImageDevice. This does NOT independently prove what V48 mounted on 2026-11-08, nor establish an exact URI or device path. Separate the known earlier workflow from current unobserved VFS runtime branch.
