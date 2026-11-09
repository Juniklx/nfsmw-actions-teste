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

## Explicit current-session clarification by tester
Tester explicitly confirmed on 2026-11-08 (Bahia), after both Shevery samples: **"Sim estou executando via pasta extraída"**. Therefore the **configured game-data source on the phone is a folder of extracted game files, NOT an ISO**. This supersedes the previous weaker wording ("historical hypothesis of extracted folder") **for the source selected by the tester**. PAL translation remains tester-provided; selected guest `libmain.so` cannot be independently enumerated through denied `/proc/PID/maps`.

Use these separate confidence levels:
- `user_confirmed_source_type=EXTRACTED_FOLDER` = **YES**, directly confirmed by tester in current conversation.
- `user_confirmed_iso_source=NO` = **YES**.
- `hostpathdevice_runtime_branch_verified_by_instrumentation=NO`: the source choice predicts the folder/HostPathDevice route but is **not** a runtime mount trace.
- `guest_library_pal_loaded_directly_verified=NO`.
- `actual_bmw_upgrade_loader_accepted_synthetic_data=NO`.
- `save_MARCEK_or_original_game_data_modified=NO`.

**Development consequence:** prioritize original/pinned `HostPathDevice` → host physical reads → game asset path (`NFS/ZZDATA4.BIN`, `NFS/ZDIR.BIN`, `GLOBAL/ATTRIBUTES.BIN`) without designing a disc-image-sector patch as if it were the phone's selected source. PRE551's ZIP-sector simulation remains a useful **offline-only** validation, not an implementation proof for extracted folder data. No more identical Android logcat probes requested.
