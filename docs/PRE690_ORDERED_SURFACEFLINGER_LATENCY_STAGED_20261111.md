# PRE690 — ordered per-layer SurfaceFlinger frame pacing (2026-11-11)

## Current validated baseline

PRE689 user clarified **they exited the game normally** after PRE688; user did not experience a freeze. PRE688's watchdog 5s line occurred around 00:36:36, after the 00:34:18–00:35:48 capture. Do not describe this as independent in-game deadlock. PRE689 canonic-context correction was verified in GitHub Actions run **42957215450**, Drive context SHA-256 `e57f0135196d2475970da058041cd95690018c9b4e2f90ee09a6265a7a6e1efa`.

PRE688 genuine observed frame pacing mismatch:
- SurfaceFlinger SurfaceView `io.github.nfsmwrecomp`, ~120Hz, 5,412 intervals, average 62.226FPS; 8ms=597, 16ms=4,184, 24–25ms=569.
- Engine C2: 4,800 internal swap intervals in four windows, 4,685 at 15–18ms and no >25ms; game's FPS cap=60, internal 1920×1080.
- Aggregated histograms do NOT prove that a short interval is followed immediately by a long one, nor do they isolate a driver, game, thermal, scheduling or rendering root cause.

## Important finding from primary sources

Perfetto's official FrameTimeline documentation states that **SurfaceView support is not guaranteed** and explicitly warns that SurfaceViews are not supported by that data source in the documented implementation. The NFSMW produces its graphics in a SurfaceView. Do not promise FrameTimeline will reveal ordered app frames. https://perfetto.dev/docs/data-sources/frametimeline

AOSP SurfaceFlinger has per-layer `--latency`, `--latency-clear`, and `--list` interfaces, and each layer's FrameTracker stores a bounded circular history (~128 records) of `desiredPresentTime`, `actualPresentTime` and `frameReadyTime`. The recent `Layer::dumpFrameStats` outputs triplets as desired/actual/ready. These are Android's internal timestamps, not an optical measurement of panel pixels. Both support and semantics require device validation.
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/SurfaceFlinger.cpp
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/Layer.cpp
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/FrameTracker.h

## PRE690 staged — no real device capture yet

- `automation/termux/nfsmw_pre690_ordered_latency_adb.sh`: launches a worker via already paired *wireless ADB from Termux*, waits 110s by default, discovers exactly one NFSMW SurfaceView, clears **only that layer's** frame history, samples `dumpsys SurfaceFlinger --latency '<exact layer>'` once per second for 60s, saves only the target game's timestamp rows to Downloads (or Termux home). Its status is separate. No calls to Shevery, Shizuku or rish. No APK, settings, root, thermal override, renderer, controls, shaders, physics, saves or keys touched.
- AOSP per-layer history usually covers ~127 recent frames. To avoid losing frame order, capture repeats every ~1s; **do not add per-sample counters**, since consecutive outputs overlap. The analyzer deduplicates by `actual_present_ns`, sorts timestamps, separates uncovered gaps, and computes interval transitions. Row tuples can contain unknown/pending times, and these must be discarded.
- `automation/kaggle/pre690_analyze_ordered_latency.py`: offline read-only parser; produces a JSON containing timestamp distribution and actual adjacency counts `8->24` and `24->8` rather than assuming alternation from prior aggregated data. The parser needs a corresponding `nfsmw.log` from the same session for gameplay-state verification.
- **Local tests (mocked Android ADB only):** shell `bash -n` passed, exact-layer mock produced 20 samples and the deduplicator reconstructed 240 synthetic timestamps from 1,428 repeated rows; a two-game-layer scenario failed closed before saving any frame data. The full local test used a local analyzer; the published Python analyzer is separately checked for syntax and mocked outputs in CI. Mock tests are NOT real S24 FE evidence.
- Synthetic GitHub Actions workflow `.github/workflows/nfsmw-pre690-ordered-latency-synthetic.yml` created and requested through `automation/run_requests/PRE690_VERIFY_20261111_ORDERED_LATENCY_01.txt`, trigger commit `3762df7136758432b1ea9c91271bb3ff741b96b7`. The GitHub Actions run result **has not yet been confirmed**; do not call this workflow PASS based on the request/commit.
- No new APK, no performance change, no code patch to game, no new signing access.

## Real-phone gate

1. In Termux, check paired ADB remains functional; run `preflight`. `PRE690_PREFLIGHT=PASS_INTERFACE_ONLY` confirms basic shell and numeric SurfaceFlinger refresh-period response, NOT that the app's layer is readable.
2. Run `arm 110 60`; open current V51 in normal graphics mode and leave car stationary for the capture. Do not switch apps or open Shevery. Worker will write `NFSMW_PRE690_ORDERED_PRESENT_*.txt` and `NFSMW_PRE690_CAPTURE_*.status.txt` if the device supports the interface.
3. With matching `nfsmw.log`, check timestamp row structure, layer identity, continuity of rolling samples, gaps, repeated timestamps, and the game state. If the data source returns no actual time or the exact SurfaceView is not available, fail closed and design a different source; DO NOT invent time-ordered observations.
4. Assess whether temporal sequences show 8/24ms compensating intervals and whether they align with native Swaps. Only after this decide a reversible, separately signed build (versionCode >51) is necessary.

Reference APK V51 PRE652, package `io.github.nfsmwrecomp`, certificate SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, graphics 1920x1080, live cap 60, max objective 120. No user data or signing material put in public GitHub.

Status: PRE689_USER_NORMAL_EXIT_CONFIRMED; PRE688_AUDIT_PASS; PRE690_ORDERED_COLLECTOR_STAGED; PRE690_LOCAL_SYNTHETIC_TEST_PASS; PRE690_GITHUB_CI_UNVERIFIED; PRE690_DEVICE_TEST_PENDING; NO_APK; NO_FPS_GAIN.
