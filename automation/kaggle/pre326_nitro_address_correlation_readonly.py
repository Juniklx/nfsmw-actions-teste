#!/usr/bin/env python3
"""PRE326: analyze existing PRE247 nitro addresses in user-provided log (read-only).

No guest memory access, APK, signing, save modification or credential handling.
An address is evidence of a logged destination, NOT player ownership.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

LINE = re.compile(
    r"NFSMW_PRE247_CHEATS_DIAG\].*?meter_candidate=(\d+)"
    r".*?addr=0x([0-9A-Fa-f]{1,8})"
    r".*?written_f32_bits=0x([0-9A-Fa-f]{1,8})"
)
MAX_LINE_BYTES = 8192
NITRO_SITES = (1, 2, 3, 4, 5)


def audit_lines(lines):
    counts = Counter()
    per_site = defaultdict(set)
    by_addr = defaultdict(set)
    total = 0
    parse_errors = 0
    for raw in lines:
        if "NFSMW_PRE247_CHEATS_DIAG" not in raw:
            continue
        if len(raw) > MAX_LINE_BYTES:
            parse_errors += 1
            continue
        m = LINE.search(raw)
        if not m:
            parse_errors += 1
            continue
        site, address, _value = m.groups()
        site = int(site)
        if site not in NITRO_SITES:
            continue
        address = int(address, 16)
        counts[site] += 1
        per_site[site].add(address)
        by_addr[address].add(site)
        total += 1

    overlap = {f"{a}-{b}": len(per_site[a] & per_site[b])
               for a, b in ((1, 2), (3, 4), (1, 3), (2, 4), (2, 3))}
    # Do not include raw guest addresses in archived reports.
    return {
        "stage": "PRE326_PASSIVE_NITRO_ADDRESS_CORRELATION",
        "status": "AUDIT_OK" if total else "NO_NITRO_EVENTS",
        "nitro_events": total,
        "malformed_marker_lines": parse_errors,
        "events_per_site": {str(s): counts[s] for s in NITRO_SITES},
        "distinct_addresses_per_site": {str(s): len(per_site[s]) for s in NITRO_SITES},
        "distinct_addresses_all_sites": len(by_addr),
        "address_site_overlap_counts": overlap,
        "multi_site_address_count": sum(len(sites) > 1 for sites in by_addr.values()),
        "owner_verified": False,
        "note": "No per-session isolation and no proof of player ownership. PRE247 is capped at 12 logs/site per process; absent records are not proof of absent stores.",
        "apk_built": False, "guest_modified": False, "signer_accessed": False
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    with args.log.open("r", encoding="utf-8", errors="replace") as f:
        result = audit_lines(f)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("PRE326_STATUS",result["status"])
    print("PRE326_NITRO_EVENTS",result["nitro_events"])
    print("PRE326_DISTINCT_ADDRESSES",result["distinct_addresses_all_sites"])
    print("PRE326_OWNER_VERIFIED",result["owner_verified"])
    return 0 if result["status"] == "AUDIT_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
