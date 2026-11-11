# PRE692 — C3 and guest watchdog on RADV Xclipse V51 (2026-11-11)

Status: REAL_READONLY_ANALYSIS_PASS; GitHub synthetic CI PASS; cause not determined; no APK or settings modified.

## Proven inputs
- Galaxy S24 FE APK V51, SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, versionCode 51.
- Private NFSMW log, SHA256 44d57cb808e86f828b40dc8ca161d30a772186ced56e478461135f0037b1943c, 1,549,711 bytes, Drive ID 1RMjDqkzTu6mS9PnGXxXmKkruQS31MP-2.
- Ordered RADV presentation capture, SHA256 5fd11328ba20b338bd773bb61dcf550b702a6e0329ba9f825858bfbbd1dec174, Drive ID 1x0CL8OEFsKA3nTdXqXQgLkKUCQvq9rvr.
- PRE692 read-only analyzer: automation/kaggle/pre692_c3_watchdog_log_readonly.py; synthetic gate https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43040102423 COMPLETED/SUCCESS, job 130589281232. CI did NOT upload a private log or run on a device.
- Real audit report https://drive.google.com/file/d/1v62eNKJq0yS6t_u9epiy4jX09KCLhBcy/view; evidence ZIP https://drive.google.com/file/d/1e1lAzzV0rv18aAil29J_xU2nXmd9z-wO/view.

## Three process startups in one private log

1. 10:28:46 RADV v1.8.0, 1920x1080, FPS cap 60; no watchdog in short segment.
2. 11:00:02 RADV v1.8.0, 1920x1080, FPS cap 120; one C3 guard 11:00:25.588.
3. 11:10:29 RADV v1.8.0, 1920x1080, FPS cap 60; C3 guard 11:12:16.746; 7 guest watchdog episodes (6 recovered, one still open at EOF).

## Exact PRE635 diagnostic already in installed V51

Local APK ZIP inspection: lib/arm64-v8a/libmain.so contains markers NFSMW_PRE635_C3_TWOREQUEST_TRACE and NFSMW_PRE194_C3; libmain_usa.so does not. Both markers were logged during the two real RADV sessions, indicating the diagnostic code executed.

Two event signatures identical after excluding absolute frame and epoch: indice=0, en_vuelo=1, offset_primera=0, offset_segunda=51872, mismos_comandos=true, subir=true, trabajo_huella=0, datos_bytes=43648. Same frame and epoch WITHIN each event. First event frame=2291 and second frame=1766. Both PRE194 guards: indice_fuera=false, referencia_distinta=false, copia_duplicada=true. The guard disabled the C3 helper and retained a fallback.

The same command buffer is NOT evidence of identical texture content or a needless second upload. No texture-copy guard removal is justified. C3 duplicate problems were already reported in older APK versions; RADV exclusivity is NOT demonstrated.

## Guest watchdog chronology: 11:10 session

- First alerts at 11:10:43.143, 11:11:30.168, 11:11:43.198, 11:17:58.385, 11:18:24.421, 11:18:37.438, 11:19:02.467.
- Six logged recoveries after 31, 11, 28, 24, 11, and 23 seconds respectively. Last 11:19 alert has no logged recovery (unknown subsequent outcome; NOT a proven crash).
- A 5s warning followed by a 20s warning and recovery is ONE episode, not multiple stalls.
- The first three stalled episodes preceded the C3 guard of 11:12:16; all three had recovered by 11:12:07. Thus C3 shutdown cannot explain the initial stalls, although relationships other than direct temporal causation remain possible.
- During RADV SurfaceFlinger capture 11:13:57 to 11:14:36: no new C3 guard and no watchdog first alert. This does not imply no microstutter; separate PRE691F measurements show irregular presentation intervals.

## PRE693 next gate

Switch the app UI selection back to System/Samsung driver, keep APK V51, same 1920x1080 and 60 FPS cap, preserve every effect, save and controller. Collect fresh NFSMW log for a matched 5–8 minute session and use the PRE692 analyzer to compare event counts and timings. Verify actual GPU driver if logged. If stalls recur on Samsung, prioritize common guest scheduler and synchronization code. If only RADV stalls, collect repeated A/B/A trials before attributing causality. Do not change system drivers, force clocks, bypass thermal protections, clear app data, or rebuild the release from this evidence.

CANONICAL CONTEXTO_NFSMW.md: still pending append with backups. This document and the Drive report are staged evidence, not a claim of canonical sync. No FPS gain proven.
