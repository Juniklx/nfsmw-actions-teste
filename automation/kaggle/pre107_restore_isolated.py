#!/usr/bin/env python3
"""PRE107: safe isolated restore-test of PRE99 to ephemeral GitHub Actions storage."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import (
    EXPECTED_BYTES, EXPECTED_SHA256, EXPECTED_ENTRIES, sha_file
)
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256

EXPECTED_FILES = 26994
EXPECTED_DIRECTORIES = 1917
EXPECTED_UNCOMPRESSED = 1795322294

def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check_member(member, root):
    name = member.name
    if not name or name.startswith("/") or "\\" in name or "\x00" in name:
        raise ValueError("Invalid absolute or malformed TAR member")
    segments = name.split("/")
    if any(segment in (".", "..") for segment in segments):
        raise ValueError("Unsafe TAR traversal segment")
    if ":" in segments[0]:
        raise ValueError("Unexpected drive path")
    if not (member.isfile() or member.isdir()):
        raise ValueError("Non-regular TAR entry")
    target = root.joinpath(*segments)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe extraction destination")
    return target

def restore(tar_path, dst):
    counts = Counter()
    total_bytes = 0
    tops = Counter()
    with tarfile.open(tar_path, mode="r:gz", errorlevel=2) as tar:
        for entry in tar:
            counts["members"] += 1
            if counts["members"] > EXPECTED_ENTRIES:
                raise ValueError("Unexpected member count")
            target = check_member(entry, dst)
            tops[entry.name.split("/")[0]] += 1
            if entry.isdir():
                target.mkdir(parents=True, exist_ok=True)
                counts["directories"] += 1
            elif entry.isfile():
                if target.exists():
                    raise ValueError("Duplicate TAR output path")
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = tar.extractfile(entry)
                if stream is None:
                    raise ValueError("Unreadable TAR regular member")
                with stream, target.open("xb") as fd:
                    shutil.copyfileobj(stream, fd, length=4*1024*1024)
                if target.stat().st_size != entry.size:
                    raise ValueError("Restored member size mismatch")
                total_bytes += entry.size
                counts["files"] += 1
                if total_bytes > EXPECTED_UNCOMPRESSED:
                    raise ValueError("Uncompressed TAR total exceeds expectation")
    if (counts["members"] != EXPECTED_ENTRIES or
        counts["directories"] != EXPECTED_DIRECTORIES or
        counts["files"] != EXPECTED_FILES or
        total_bytes != EXPECTED_UNCOMPRESSED):
        raise ValueError("Restored counts differ from PRE104")
    source = dst / SOURCE_NAME
    if not source.is_file() or digest_file(source) != SOURCE_SHA256:
        raise ValueError("Restored PRE92 source mismatch")
    return {
        "members_restored": counts["members"],
        "files_restored": counts["files"],
        "directories_restored": counts["directories"],
        "bytes_restored": total_bytes,
        "source_sha256_verified": True,
        "top_level_member_counts": dict(tops),
        "staging_pre13_file_count": len(list(dst.rglob("*ediciones_DIAG40_PRE13*"))),
        "restored_to_ephemeral_directory": True,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid run ID")
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE107_RESTAURACAO_ISOLADA_PRE99",
        "run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "START",
        "sha256_tar_integral_ok": False,
        "restore_test_success": False,
        "original_kaggle_workspace_modified": False,
        "google_drive_modified": False,
        "apk_built": False,
        "signing_key_accessed": False,
    }
    try:
        report["phase"] = "GOOGLE_OAUTH"
        client = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre107_", dir="/tmp") as temp:
            folder = Path(temp)
            archive = folder / "pre99.tar.gz"
            destination = folder / "restore_test"
            destination.mkdir()
            if shutil.disk_usage(folder).free < 4 * 1024**3:
                raise RuntimeError("Insufficient ephemeral disk for isolated restore")
            report["phase"] = "DOWNLOAD"
            download(client, archive)
            report["phase"] = "VERIFY_FULL_SHA256"
            digest, _md5, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 SHA256/size mismatch")
            report["sha256_tar_integral_ok"] = True
            report["phase"] = "EXTRACT_ISOLATED"
            report["restore"] = restore(archive, destination)
            report["restore_test_success"] = True
            report["status"] = "RESTAURACAO_ISOLADA_VALIDADA"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE107 incomplete at phase:", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print("PRE107:", report["status"])
    return 0 if report["status"] == "RESTAURACAO_ISOLADA_VALIDADA" else 1

if __name__ == "__main__":
    raise SystemExit(main())
