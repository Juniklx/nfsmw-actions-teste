#!/usr/bin/env python3
"""PRE106: locate the separate SettingsStyle palette in verified PRE99, read-only."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256

KEYWORDS = ("SettingsStyle", "LifecycleColor", "style().settings")
PALETTE_REGEX = re.compile(r"SettingsStyle|LifecycleColor|style\(\)\.settings|kHotReload|kRestart", re.I)

def sections(data: bytes, name: str, limit: int = 100):
    lines = data.decode("utf-8", errors="replace").splitlines()
    at = [i for i, s in enumerate(lines) if PALETTE_REGEX.search(s)]
    use = set()
    for i in at:
        use.update(range(max(0, i-4), min(len(lines), i+6)))
    return {
        "path": name,
        "lines_in_file": len(lines),
        "matched_line_numbers": [i+1 for i in at[:80]],
        "excerpts": [{"line": i+1, "text": lines[i][:300]}
                     for i in sorted(use)[:limit]],
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not args.run_id.isdecimal():
        raise ValueError("Invalid run ID")
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE106_PALETA_SETTINGS_STYLE",
        "run_id": args.run_id,
        "status": "NAO_VERIFICADO",
        "phase": "START",
        "backup_integrity": False,
        "settings_source_integrity": False,
        "sources": [],
        "code_modified": False,
        "backup_extracted": False,
        "apk_compiled": False,
        "signing_key_accessed": False,
    }
    try:
        report["phase"] = "AUTH_GOOGLE"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre106_") as directory:
            archive = Path(directory) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD"
            download(drive, archive)
            report["phase"] = "VERIFY_SHA256"
            sha, _, size = sha_file(archive)
            if sha != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 integrity mismatch")
            report["backup_integrity"] = True
            report["phase"] = "READ_UI_CODE"
            with tarfile.open(archive, "r:gz", errorlevel=2) as tar:
                for member in tar:
                    name = member.name
                    if not member.isfile() or member.size > 350000:
                        continue
                    if name == SOURCE_NAME:
                        f = tar.extractfile(member)
                        if f is None:
                            continue
                        data = f.read()
                        report["settings_source_integrity"] = (
                            hashlib.sha256(data).hexdigest() == SOURCE_SHA256
                        )
                        if not report["settings_source_integrity"]:
                            raise ValueError("settings source hash mismatch")
                        report["sources"].append(sections(data, name, 110))
                        continue
                    if not name.startswith("workspace/nativo/sdk/"):
                        continue
                    if "/ui/" not in name or not name.endswith((".h", ".hpp", ".cpp", ".cc")):
                        continue
                    f = tar.extractfile(member)
                    if f is None:
                        continue
                    data = f.read()
                    if not any(w.encode() in data for w in KEYWORDS):
                        continue
                    report["sources"].append(sections(data, name, 100))
                    if len(report["sources"]) >= 24:
                        break
        report["found_palette_reference"] = any(
            s["path"] != SOURCE_NAME for s in report["sources"]
        )
        report["phase"] = "COMPLETE"
        report["status"] = "PALETA_LOCALIZADA" if report["found_palette_reference"] else "SEM_REFERENCIA_ADICIONAL"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE106 failed in phase:", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        print("PRE106 status:", report["status"])
    return 0 if report["status"] in ("PALETA_LOCALIZADA", "SEM_REFERENCIA_ADICIONAL") else 1

if __name__ == "__main__":
    raise SystemExit(main())
