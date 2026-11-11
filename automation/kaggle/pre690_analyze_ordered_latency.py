#!/usr/bin/env python3
"""PRE690 ordered SurfaceFlinger --latency analyzer.

Deduplicates overlapping rolling snapshots. Intervals over 100 ms are
flagged as uncertain gaps, not counted in continuous pacing summaries or
cross-gap adjacent pairs; they may be real pauses OR lost collection history.
Results are per-layer SF timestamps, not optical measurements or proof of cause.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

MAXINT = 2**63 - 1
CONTINUITY_CUTOFF_MS = 100.0  # Diagnostic choice, not proof of missing frames.

def analyze(path: Path):
    data=path.read_bytes()
    lines=data.decode("utf-8").splitlines()
    if not lines or lines[0]!="PRE690_ORDERED_SURFACEVIEW_TIMESTAMPS":
        raise ValueError("PRE690_BAD_CAPTURE_HEADER")
    def lookup(prefix):
        return next((x[len(prefix):] for x in lines if x.startswith(prefix)),None)
    layer=lookup("LAYER=")
    num=lookup("SAMPLES_REQUESTED=")
    if not layer or "SurfaceView[io.github.nfsmwrecomp/" not in layer:
        raise ValueError("PRE690_NOT_EXACT_GAME_SURFACEVIEW")
    if not num or not num.isdigit():
        raise ValueError("PRE690_BAD_REQUESTED_SAMPLE_COUNT")
    wanted=int(num)
    if not lookup("COLLECTION_START=") or not lookup("COLLECTION_END="):
        raise ValueError("PRE690_MISSING_TIME_BOUNDS")
    if lookup("NONEMPTY_SAMPLES=") is None:
        raise ValueError("PRE690_UNFINISHED_CAPTURE")
    samples=[]
    current=None
    found=set()
    duplicates=discarded=0
    refresh=Counter()
    for line in lines:
        f=line.split()
        if not f: continue
        tag=f[0]
        if tag=="SAMPLE_START":
            if current is not None or len(f)!=3:
                raise ValueError("PRE690_BAD_SAMPLE_START")
            current={"index":int(f[1]),"frames":0,"valid":0}
            if current["index"]!=len(samples)+1:
                raise ValueError("PRE690_SAMPLE_INDEX_GAP")
        elif tag=="PERIOD_NS":
            if current is None or len(f)!=2:
                raise ValueError("PRE690_PERIOD_OUTSIDE_SAMPLE")
            p=int(f[1])
            if not 3_000_000<=p<=50_000_000:
                raise ValueError("PRE690_PERIOD_IMPLAUSIBLE")
            refresh[p]+=1
        elif tag=="FRAME":
            if current is None or len(f)!=4:
                raise ValueError("PRE690_FRAME_OUTSIDE_SAMPLE")
            desired,actual,ready=map(int,f[1:])
            current["frames"]+=1
            if 0<actual<MAXINT:
                current["valid"]+=1
                if actual in found: duplicates+=1
                found.add(actual)
            else: discarded+=1
        elif tag=="FRAME_ROWS":
            if current is None or current["frames"]!=int(f[1]):
                raise ValueError("PRE690_FRAME_COUNT_DISAGREEMENT")
        elif tag=="VALID_PRESENT_ROWS":
            if current is None or current["valid"]!=int(f[1]):
                raise ValueError("PRE690_VALID_PRESENT_COUNT_DISAGREEMENT")
        elif tag=="SAMPLE_END":
            if current is None or current["index"]!=int(f[1]):
                raise ValueError("PRE690_SAMPLE_END_DISAGREEMENT")
            samples.append(current)
            current=None
    if current is not None or len(samples)!=wanted:
        raise ValueError("PRE690_INCOMPLETE_CAPTURE")
    valid_samples=sum(x["valid"]>0 for x in samples)
    if valid_samples!=int(lookup("NONEMPTY_SAMPLES=")) or valid_samples<wanted//2:
        raise ValueError("PRE690_INSUFFICIENT_VALID_SAMPLES")
    timestamps=sorted(found)
    if len(timestamps)<100:
        raise ValueError("PRE690_LESS_THAN_100_UNIQUE_PRESENTATIONS")
    interval=[]
    gaps=[]
    very_large_gaps=[]
    for before,after in zip(timestamps,timestamps[1:]):
        ms=(after-before)/1e6
        if ms<=0: raise ValueError("PRE690_NEGATIVE_PRESENT_DELTA")
        if ms>CONTINUITY_CUTOFF_MS:
            gaps.append(round(ms,3))
            if ms>2500: very_large_gaps.append(round(ms,3))
        else: interval.append(ms)
    if len(interval)<100:
        raise ValueError("PRE690_NOT_ENOUGH_ADJACENT_INTERVALS")
    count=Counter(round(v) for v in interval)
    pairs=Counter()
    for t0,t1,t2 in zip(timestamps,timestamps[1:],timestamps[2:]):
        a=(t1-t0)/1e6
        b=(t2-t1)/1e6
        if 0<a<=CONTINUITY_CUTOFF_MS and 0<b<=CONTINUITY_CUTOFF_MS:
            pairs[(round(a),round(b))]+=1
    sorted_deltas=sorted(interval)
    def quantile(p):
        return round(sorted_deltas[int(p*(len(interval)-1))],3)
    return {
      "gate":"PRE690_ORDERED_SURFACEFLINGER_NFSMW_TIMESTAMP_AUDIT",
      "status":"ANALYZED_PER_LAYER_PRESENT_TIMESTAMPS__NO_CAUSE_PROVEN",
      "source_sha256":hashlib.sha256(data).hexdigest(),
      "source_bytes":len(data),
      "layer":layer,
      "sample_count":wanted,
      "samples_with_valid_frames":valid_samples,
      "unique_present_timestamps":len(timestamps),
      "duplicate_rolling_timestamps_discarded":duplicates,
      "invalid_or_pending_timestamps_discarded":discarded,
      "refresh_period_ns_counts":dict(sorted(refresh.items())),
      "uncovered_gaps_over_2_5s_ms":very_large_gaps,
      "uncertain_gaps_over_100ms_ms":gaps,
      "continuity_cutoff_ms":CONTINUITY_CUTOFF_MS,
      "continuous_covered_time_s":round(sum(interval)/1000,3),
      "distinct_adjacent_intervals":len(interval),
      "interval_ms":{"median":round(statistics.median(interval),3),
                     "mean":round(statistics.mean(interval),3),
                     "p95":quantile(.95),"p99":quantile(.99)},
      "rounded_ms_histogram":{str(k):v for k,v in sorted(count.items())},
      "ordered_8_then_24_or_24_then_8":pairs[(8,24)]+pairs[(24,8)],
      "ordered_8_then_25_or_25_then_8":pairs[(8,25)]+pairs[(25,8)],
      "most_common_adjacent_pairs":[{"a_ms":a,"b_ms":b,"count":n}
           for (a,b),n in pairs.most_common(12)],
      "limits":{"uncertain_gaps_may_be_real_pauses_or_unobserved_history":True,
                "timestamps_are_not_optical_display_measurements":True,
                "gameplay_state_needs_same_session_nfsmw_log":True,
                "frame_pacing_cause_proven":False,
                "fps_gain_proven":False,
                "new_apk_built":False},
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    report=analyze(args.source)
    output=args.output or args.source.with_suffix(".analysis.json")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PRE690_ORDERED_LATENCY_AUDIT=PASS")
    print("PRE690_UNIQUE_PRESENTATIONS="+str(report["unique_present_timestamps"]))
    print("PRE690_8_TO_24_PATTERN_COUNT="+str(report["ordered_8_then_24_or_24_then_8"]))
    print("PRE690_8_TO_25_PATTERN_COUNT="+str(report["ordered_8_then_25_or_25_then_8"]))
    print("PRE690_UNCERTAIN_GAPS_OVER_100MS="+str(len(report["uncertain_gaps_over_100ms_ms"])))
    print("PRE690_CAUSE_AND_FPS_GAIN=UNPROVEN")
    print("PRE690_ANALYSIS_REPORT="+str(output))

if __name__=="__main__":main()
