#!/usr/bin/env python3
"""PRE326 synthetic-only regression: address identity, site overlap and malformed logs."""
from pre326_nitro_address_correlation_readonly import audit_lines

def event(site,addr,bits="3F800000"):
    return f"00:00 [NFSMW_PRE247_CHEATS_DIAG] meter_candidate={site} addr=0x{addr:08X} written_f32_bits=0x{bits}\n"

cases=[
    event(1,0x810000FC),
    event(2,0x810000FC),
    event(3,0x810000FC),
    event(4,0x810000FC),
    event(1,0x820000FC),
    event(6,0x830000FC),  # Speedbreaker: excluded
    "NFSMW_PRE247_CHEATS_DIAG] broken record\n",
    "Unrelated line\n",
]
x=audit_lines(cases)
assert x["status"]=="AUDIT_OK",x
assert x["nitro_events"]==5,x
assert x["distinct_addresses_all_sites"]==2,x
assert x["events_per_site"]=={"1":2,"2":1,"3":1,"4":1,"5":0},x
assert x["address_site_overlap_counts"]["1-2"]==1,x
assert x["address_site_overlap_counts"]["3-4"]==1,x
assert x["multi_site_address_count"]==1,x
assert x["malformed_marker_lines"]==1,x
assert x["owner_verified"] is False,x
no=audit_lines(["no Nitro data"])
assert no["status"]=="NO_NITRO_EVENTS" and not no["owner_verified"]
print("PRE326_MOCK_STATUS AUDIT_OK")
print("PRE326_MOCK_ASSERTIONS 10")
