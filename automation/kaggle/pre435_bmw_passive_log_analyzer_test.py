#!/usr/bin/env python3
"""Host-only synthetic PRE435 regression tests; no model identification claims."""
from pre435_bmw_passive_log_analyzer import analyze
E="[NFSMW_PRE429_ENTRY] manager=0x82C5D9E8 tuning_car=0x1234ABCD pvehicle=0xABCD4321"
L="[NFSMW_PRE429_LEVEL] manager=0x82C5D9E8 category={} candidate_count={}"
r=analyze(E+"\n"+L.format(0,4)+"\n"+L.format(4,0),"bmw")
assert r["status"]=="PASSIVE_COUNTS_OBSERVED"
assert r["category_samples"]["0"]["candidate_values"]==[4]
assert r["category_samples"]["4"]["candidate_values"]==[0]
assert not r["category_samples"]["1"]["observed"]
assert not r["car_identity_inferred_from_pointers"]
assert not r["category_levels_verified"]
r=analyze(L.format(1,3),"punto")
assert r["status"]=="LEVELS_WITHOUT_ENTRY" and r["unmatched_level_events"]==1
assert all(not x["observed"] for x in r["category_samples"].values())
r=analyze(E+"\n"+L.format(2,-1)+"\n"+E+"\n"+L.format(2,5),"bmw")
assert r["status"]=="AMBIGUOUS_MULTIPLE_ENTRIES" and r["unmatched_level_events"]==2
r=analyze(E+"\n"+"[NFSMW_PRE429_LEVEL] manager=0x82C5D9E8 category=8 candidate_count=99")
assert r["status"]=="ENTRY_ONLY" and r["malformed_marker_lines"]==1
r=analyze(E+"\n"+L.format(0,1)+"\n"+L.format(0,2))
assert r["category_samples"]["0"]["candidate_values"]==[1,2]
assert r["category_samples"]["0"]["samples"]==2
assert analyze("irrelevant old log")["status"]=="NO_EVENTS"
print("PRE435_HOST_LOG_TRIAGE_TESTS_PASS")
