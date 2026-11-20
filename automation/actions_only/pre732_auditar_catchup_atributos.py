#!/usr/bin/env python3
"""PRE732: read-only byte-pattern inventory of candidate Catch-Up attributes.

This does NOT decode ISO/XEX, prove Xbox 360 semantics, or modify gameplay.
Do not use raw matches as patch offsets.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ATTRS = {
    "CatchUp": 0x10DB04E6,
    "CatchUpIntegral": 0x4545AB74,
    "CatchUpDerivative": 0x515AA4E4,
    "CatchUpSkill": 0x8069B5A9,
    "CatchUpOverride": 0x9EB17C1E,
    "CatchUpSpread": 0xA18A07BA,
}
EXTS = {".bin", ".bun", ".vpak", ".dat", ".xex", ".cpp", ".h", ".hpp", ".s", ".asm", ".txt"}
BLOCK = 4 * 1024 * 1024


def patterns():
    return [(name, order, struct.pack(fmt, val))
            for name, val in ATTRS.items()
            for order, fmt in (("BE", ">I"), ("LE", "<I"))]


def scan_file(path, block=BLOCK, sample_limit=30):
    if block < 4 or sample_limit < 1:
        raise ValueError("block >=4 and sample_limit >=1 required")
    pats = patterns()
    stats = {(n, e): {"count": 0, "sample_offsets_hex": []} for n, e, _ in pats}
    with Path(path).open("rb") as stream:
        total, tail = 0, b""
        while True:
            chunk = stream.read(block)
            if not chunk:
                break
            joined, base = tail + chunk, total - len(tail)
            for name, order, needle in pats:
                out = stats[name, order]
                at = joined.find(needle)
                while at >= 0:
                    if at + len(needle) > len(tail):
                        out["count"] += 1
                        if len(out["sample_offsets_hex"]) < sample_limit:
                            out["sample_offsets_hex"].append(hex(base + at))
                    at = joined.find(needle, at + 1)
            tail = joined[-3:]
            total += len(chunk)
    return [{"attribute": n, "hash_hex": f"0x{ATTRS[n]:08X}",
             "endianness": e, **v}
            for (n, e), v in sorted(stats.items()) if v["count"]]


def audit(inputs, max_mib=1024, sample_limit=30):
    if max_mib < 1 or sample_limit < 1:
        raise ValueError("limits must be positive")
    result = {
        "schema": "PRE732_x360_catchup_hash_audit_v1",
        "mode": "READ_ONLY",
        "pc_hashes_not_x360_proof": True,
        "files_scanned": 0,
        "files_with_matches": 0,
        "files_skipped": 0,
        "matches": [],
        "gameplay_changed": False,
        "apk_built": False,
        "device_tested": False,
    }
    seen = set()
    for root in map(Path, inputs):
        if not root.exists() or root.is_symlink():
            result["files_skipped"] += 1
            continue
        items = [root] if root.is_file() else root.rglob("*") if root.is_dir() else []
        for path in items:
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTS:
                continue
            canonical = path.resolve()
            if canonical in seen:
                continue
            seen.add(canonical)
            try:
                size = path.stat().st_size
                if size > max_mib * 1024 * 1024:
                    result["files_skipped"] += 1
                    continue
                hits = scan_file(path, sample_limit=sample_limit)
            except OSError:
                result["files_skipped"] += 1
                continue
            result["files_scanned"] += 1
            if hits:
                # Deliberately omit absolute/private paths and binary excerpts.
                result["files_with_matches"] += 1
                result["matches"].append({"name": path.name, "size_bytes": size, "hits": hits})
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", action="append", required=True, type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--max-file-mib", type=int, default=1024)
    cli.add_argument("--max-hits-per-hash", type=int, default=30)
    args = cli.parse_args()
    data = audit(args.input, args.max_file_mib, args.max_hits_per_hash)
    output = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"PRE732 files_scanned={data['files_scanned']} files_with_matches={data['files_with_matches']}")
    else:
        sys.stdout.write(output)
    return 0 if data["files_scanned"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
