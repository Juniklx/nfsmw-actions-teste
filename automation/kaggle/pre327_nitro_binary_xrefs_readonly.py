#!/usr/bin/env python3
"""PRE327: read-only binary references to Nitro PAL entry in verified PRE99.

A byte occurrence may be arbitrary data; never infer dispatch or player owner
from an uncorroborated hit. No APK, guest writes, signer or save access.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import sys
import tarfile
import tempfile

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, looks_sensitive, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre327/NFSMW_PRE327_NITRO_BINARY_XREFS.json")
ADDRESS = 0x82424AF0
MAX_MEMBER_BYTES = 80 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_SAMPLES = 32
EXTENSIONS = (".xex", ".bin", ".xbe", ".elf", ".dat", ".rdata")
PATTERNS = {
    "big_endian": ADDRESS.to_bytes(4, "big"),
    "little_endian": ADDRESS.to_bytes(4, "little"),
}


def count_occurrences(data: bytes, needle: bytes):
    offsets = []
    start = 0
    count = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        count += 1
        if len(offsets) < MAX_SAMPLES:
            offsets.append(i)
        start = i + 1
    return count, offsets


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "stage": "PRE327_NITRO_BINARY_XREF_READONLY",
        "status": "FAILED",
        "apk_built": False,
        "guest_modified": False,
        "signer_accessed": False,
        "owner_verified": False,
        "dispatch_verified": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre327_") as tmp:
            archive = Path(tmp) / "pre99.tar.gz"
            download(drive_client(), archive)
            digest, _, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 archive integrity mismatch")
            inspected = []
            skipped_oversize = 0
            total = 0
            hits = []
            with tarfile.open(archive, mode="r:gz", errorlevel=2) as tf:
                for member in tf:
                    if not member.isfile():
                        continue
                    name = member.name.lstrip("./")
                    lower = name.lower()
                    if not lower.startswith("workspace/") or not lower.endswith(EXTENSIONS) or looks_sensitive(name):
                        continue
                    if member.size > MAX_MEMBER_BYTES or total + member.size > MAX_TOTAL_BYTES:
                        skipped_oversize += 1
                        continue
                    datafile = tf.extractfile(member)
                    if datafile is None:
                        continue
                    raw = datafile.read(MAX_MEMBER_BYTES + 1)
                    if len(raw) != member.size:
                        raise ValueError("incomplete candidate member")
                    total += len(raw)
                    inspected.append({"file": name[:260], "bytes": len(raw),
                                      "sha256": hashlib.sha256(raw).hexdigest()})
                    for endian, pattern in PATTERNS.items():
                        count, positions = count_occurrences(raw, pattern)
                        if count:
                            hits.append({"file": name[:260], "byte_order": endian,
                                         "count": count, "sample_offsets": positions})
            result.update({
                "status": "AUDIT_OK",
                "snapshot_sha256": digest,
                "files_inspected": len(inspected),
                "bytes_inspected": total,
                "oversize_or_budget_skips": skipped_oversize,
                "file_metadata": inspected[:100],
                "file_metadata_truncated": len(inspected) > 100,
                "binary_matches": hits[:100],
                "matches_truncated": len(hits) > 100,
                "result_scope": "Only candidate binary file extensions in verified PRE99. Empty results neither disprove indirect dispatch nor object ownership. Hits are untyped byte matches, not proven vtable entries.",
            })
    except Exception as error:
        result["error_type"] = type(error).__name__
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PRE327_STATUS", result["status"])
    print("PRE327_FILES", result.get("files_inspected", 0))
    print("PRE327_MATCHING_FILES", len(result.get("binary_matches", [])))
    print("PRE327_OWNER_VERIFIED", result["owner_verified"])
    print("PRE327_ERROR_TYPE", result.get("error_type"))
    return 0 if result["status"] == "AUDIT_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
