# PRE321 — V41 Nitro full-cycle runtime audit, Galaxy S24 FE — 2026-11-07

## Source and integrity
User-supplied `nfsmw.log`, 2,409,694 bytes, 10,373 lines, SHA-256 `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc`. File includes prior sessions; **new V41 test** is 15:47:58–15:48:47 local log timestamps. PRE316 marker observed 58 times, all in this interval; PRE247 marker appears 336 times across **all** accumulated sessions, not all new. PRE246 marker absent. No literal `SIGSEGV` or `FATAL` string found in this log (not proof of no crash in other sessions).

## Runtime V41 PRE316 Nitrous diagnostics

| Site | Guest function | Runtime events | Count at final event | First | Final last | Aggregate min | Aggregate max | Interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Nitro candidate `sub_82424AF0` +252 | 12 | 150 | 0.99333334 | 0.0000008149 | 0.0000008149 | 0.99333334 | Drain |
| 2 | Same | 12 | 150 | 0.99333334 | 0.0000008149 | 0.0000008149 | 0.99333334 | Drain, duplicate measured sequence |
| 3 | Same | 17 | 2004 | 0.0005555556 | 0.9951883554 | 0.0005555556 | 0.9951883554 | Recharge |
| 4 | Same | 17 | 2004 | 0.0005555556 | 0.9951883554 | 0.0005555556 | 0.9951883554 | Recharge, duplicate measured sequence |
| 5 | Same | 0 | Unknown | — | — | — | — | No PRE316 event |

**Important distinction:** site 1/2 latest minimum corresponds to approximately **0.0000815%**, essentially zero on the game's visual meter, but the raw float is not exactly zero. Site 3/4 maximum corresponds to **99.5188%**, not 100% exactly. PRE316 logs occur at checkpoints and threshold crossings; final full saturation may have occurred after last checkpoint, or a distinct capped site may execute after it. Do **not** assert the true terminal store value was exactly 0 or 1. User described a full drain/refill in earlier controlled tests; the trace supports near-full cycle.

### Timeline of observed new session
- 15:47:58.877: Nitro site 1/2 first recorded `0.99333334` (99.333%).
- 15:48:01.363: Nitro site 1/2 count 150, min `0.0000008149`, near empty.
- 15:48:03.410: Nitro site 3/4 first `0.0005555556` (~0.0556%).
- 15:48:45.270: Nitro site 3/4 count 2004, max `0.9951883554` (~99.52%).
- 58 PRE316 events total: 12 each site 1/2, 17 each site 3/4. No Nitro site 5.
- No proof of FPS improvement/thermal effect/actual infinite Nitro.

## Implications
1. PRE316–PRE318 passive marker **works on real device**. V41 had already passed build/signing/upload, now runtime PRE316 validated.
2. Nitro candidate depletion and recharge confirmed to near limits in runtime. This **does not yet identify the authoritative final guest store per branch**: both 1/2 and 3/4 write matching sequences; 5 is unobserved.
3. Before a mutation (Nitro infinite), inspect PRE312 scoped original PPC context and decide authoritative stores with appropriate guards and OFF state retaining exact original writes.
4. PRE309 remains host-only C++ opt-in gate. Neither Nitro nor Speedbreaker nor money cheats are enabled in V41. No source patches applied from this log audit; don't claim functional cheat or changed save.
5. Retain V39/V40/V41 APKs, same permanent signer (SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`), package `io.github.nfsmwrecomp`, MARCEK, controls and 1920×1080 graphics.
