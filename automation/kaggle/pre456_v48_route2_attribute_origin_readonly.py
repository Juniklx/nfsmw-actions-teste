#!/usr/bin/env python3
"""PRE456: read-only provenance of V48 BMW/Punto route-2 attribute value.
Authenticated PRE99 source only; no game invocation, no APK, no signing, no saves.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre446_bmw_zero_branch_readonly import ROOT, TARGETS

OUTPUT = Path("/tmp/nfsmw-pre456-out/report.json")
ORDER = ("lookup", "attribute_check", "attribute_value", "builder")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    result = {"stage": "PRE456_ROUTE2_ATTRIBUTE_PROVENANCE_READONLY",
              "status": "NOT_VERIFIED", "run_id": args.run_id,
              "apk_built": False, "save_modified": False,
              "signing_accessed": False, "guest_executed": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre456_") as d:
            archive = Path(d) / "pre99.tar.gz"
            download(drive_client(), archive)
            digest, _, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("Authenticated PRE99 archive hash/size mismatch")
            print("PRE456_PRE99_HASH_OK", True, "PRE456_PRE99_BYTES", size, flush=True)
            names = {ROOT + x[0]: key for key,x in TARGETS.items()}
            found = {}
            with tarfile.open(archive, mode="r:gz", errorlevel=2) as tar:
                for member in tar:
                    key = names.get(member.name.lstrip("./"))
                    if key is None: continue
                    if not member.isfile() or member.size > 7_000_000:
                        raise ValueError("Bad target source member")
                    reader = tar.extractfile(member)
                    if reader is None: raise ValueError("Unreadable source member")
                    raw = reader.read()
                    if hashlib.sha256(raw).hexdigest() != TARGETS[key][1]:
                        raise ValueError("PIN_MISMATCH " + key)
                    body = body_for_function(raw.decode("utf-8"), TARGETS[key][2])
                    found[key] = body.splitlines()
                if set(found) != set(TARGETS):
                    raise ValueError("Missing pinned PAL source")
            lookup = found["lookup"]
            derived = [i + 1 for i, line in enumerate(lookup)
                       if "ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);" in line]
            explicit = [i + 1 for i, line in enumerate(lookup)
                        if "ctx.r3.s64 = 0;" in line]
            if len(derived) != 1 or len(explicit) != 2:
                raise ValueError("PAL return sites have changed")
            sources = {}
            for key in ORDER:
                lines = found[key]
                if len(lines) > 700:
                    raise ValueError("Unexpectedly long function " + key)
                sources[key] = {
                    "filename": TARGETS[key][0], "sha256": TARGETS[key][1],
                    "function": TARGETS[key][2], "total_lines": len(lines),
                    "ctx_r11_uses": [i + 1 for i,line in enumerate(lines)
                                     if "ctx.r11" in line],
                    "guest_calls": [{"line": i+1, "source":line.strip()[:180]}
                                     for i,line in enumerate(lines)
                                     if "__imp__sub_" in line],
                    "full_function_lines": [{"line":i+1, "text":line[:260]}
                                            for i,line in enumerate(lines)]
                }
                print("PRE456_BEGIN_FUNCTION", key, "lines", len(lines), flush=True)
                for i,line in enumerate(lines,1):
                    print(f"PRE456_SRC {key}:{i:03d} {line[:230]}", flush=True)
                print("PRE456_END_FUNCTION", key, flush=True)
            result.update(status="AUDIT_OK", pre99_sha256=digest,
                          source_sha256_all_verified=True,
                          route_2_load_line=derived[0],
                          route_1_3_explicit_zero_lines=explicit,
                          route2_source_semantics_resolved=False,
                          functions=sources)
    except Exception as exc:
        result.update(status="FAILED", error_type=type(exc).__name__,
                      error=str(exc)[:240])
        print("PRE456_ERROR", result["error_type"], result["error"], flush=True)
    result["utc"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("PRE456_STATUS", result["status"], flush=True)
    return 0 if result["status"] == "AUDIT_OK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
