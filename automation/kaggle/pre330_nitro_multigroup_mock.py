#!/usr/bin/env python3
"""PRE330 synthetic separation and owner-gating checks."""
from pre330_nitro_multigroup_readonly import analyze

def ev(t,site,addr):
    return f"[2026-11-07 {t}] [info] [NFSMW_PRE247_CHEATS_DIAG] meter_candidate={site} addr=0x{addr} written_f32_bits=0x3F800000"

cases=[
ev("10:00:00.000",1,"AAAA0000"),
ev("10:00:00.001",2,"AAAA0000"),
ev("10:02:00.000",1,"BBBB0000"),
ev("10:02:00.001",2,"BBBB0000"),
]
r=analyze(cases)
assert r["status"]=="AUDIT_OK"
assert r["group_count"]==2
assert r["nitro_events"]==4
assert not r["same_destination_in_all_groups"]
assert not r["owner_verified"]
assert not r["independent_android_processes_verified"]
assert analyze(["no marker"])["status"]=="NO_EVENTS"
print("PRE330_MOCK_STATUS AUDIT_OK")
print("PRE330_MOCK_ASSERTIONS 7")
