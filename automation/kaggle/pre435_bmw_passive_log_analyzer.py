#!/usr/bin/env python3
"""PRE435: offline/passive PRE429 log triage. Never infer model from guest pointers."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ENTRY=re.compile(r"\[NFSMW_PRE429_ENTRY\]\s+manager=0x([0-9a-fA-F]{1,8})\s+tuning_car=0x([0-9a-fA-F]{1,8})\s+pvehicle=0x([0-9a-fA-F]{1,8})")
LEVEL=re.compile(r"\[NFSMW_PRE429_LEVEL\]\s+manager=0x([0-9a-fA-F]{1,8})\s+category=(\d+)\s+candidate_count=(-?\d+)")
MARKER=re.compile(r"\[NFSMW_PRE429_(?:ENTRY|LEVEL)\]")
def analyze(content:str, car_label:str="unknown")->dict:
    entries=[];levels=[];malformed=0
    for num,line in enumerate(content.splitlines(),1):
        if not MARKER.search(line):continue
        m=ENTRY.search(line)
        if m:
            entries.append(tuple(int(v,16) for v in m.groups()))
            continue
        m=LEVEL.search(line)
        if m:
            manager=int(m.group(1),16);category=int(m.group(2));value=int(m.group(3))
            if category>6:malformed+=1
            else:levels.append((num,manager,category,value))
            continue
        malformed+=1
    one_entry=len(entries)==1
    samples={str(i):[] for i in range(7)}
    unmatched=0
    for _,manager,cat,value in levels:
        if one_entry and manager==entries[0][0]:samples[str(cat)].append(value)
        else:unmatched+=1
    category={
        key:{"observed":bool(vals),"candidate_values":sorted(set(vals)),"samples":len(vals)}
        for key,vals in samples.items()
    }
    if not entries and not levels:status="NO_EVENTS"
    elif len(entries)>1:status="AMBIGUOUS_MULTIPLE_ENTRIES"
    elif not entries:status="LEVELS_WITHOUT_ENTRY"
    elif unmatched:status="PARTIAL_UNMATCHED_LEVELS"
    elif not levels:status="ENTRY_ONLY"
    else:status="PASSIVE_COUNTS_OBSERVED"
    return {
      "stage":"PRE435_BMW_TUNING_PASSIVE_LOG_TRIAGE",
      "status":status,"tester_supplied_car":car_label,
      "car_identity_inferred_from_pointers":False,
      "source_label_requires_separate_test_session":True,
      "entry_events":len(entries),"level_events":len(levels),
      "unmatched_level_events":unmatched,"malformed_marker_lines":malformed,
      "category_samples":category,"category_levels_verified":False,
      "meaning":"Candidate counts from existing guest calls, not verified purchasable upgrades",
      "no_event_is_zero":False,"save_or_game_modified":False
    }
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",required=True,type=Path)
    p.add_argument("--car",choices=("bmw","punto","unknown"),default="unknown")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    report=analyze(a.log.read_text(encoding="utf-8",errors="replace"),a.car)
    s=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(s,encoding="utf-8")
    print(s,end="")
    return 0
if __name__=="__main__":raise SystemExit(main())
