#!/usr/bin/env python3
"""PRE105: read-only inspection of the PRE92 Settings overlay from verified PRE99."""
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

from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file

SOURCE_NAME = "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp"
SOURCE_SHA256 = "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"
SECONDARY_SUFFIX = "/nativo/sdk/src/ui/rex_app.cpp"
PATTERNS = {
    "imgui_style": r"ImGuiCol_|PushStyle|PopStyle|GetStyle|StyleColors|style\.Colors",
    "window": r"ImGui::Begin|ImGui::End|BeginChild|EndChild|SetNextWindow|OnDraw|OnOpen",
    "labels": r"NEED FOR SPEED|MOST WANTED|SETTINGS|SAVE SETTINGS|SaveConfig",
    "colors": r"ImVec4|ImColor|ColorConvert|ColorButton|Separator",
}
CTX = 2
MAX_LINES = 260

def drive_client():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    c = Credentials(token=None,
                    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["GOOGLE_CLIENT_ID"],
                    client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive", "v3", credentials=c, cache_discovery=False)

def download(drive, path):
    from googleapiclient.http import MediaIoBaseDownload
    with path.open("wb") as fp:
        d = MediaIoBaseDownload(
            fp, drive.files().get_media(fileId=BACKUP_ID, supportsAllDrives=True),
            chunksize=16 * 1024 * 1024)
        done = False
        while not done:
            _, done = d.next_chunk(num_retries=4)

def source_excerpt(content, filename, max_lines):
    lines = content.decode("utf-8", errors="replace").splitlines()
    matches = {}
    keep = set()
    for name, rx in PATTERNS.items():
        indices = [i for i, line in enumerate(lines) if re.search(rx, line, flags=re.I)]
        matches[name] = {"count": len(indices), "numbers": [i + 1 for i in indices[:80]]}
        for i in indices:
            keep.update(range(max(0, i - CTX), min(len(lines), i + CTX + 1)))
    selection = sorted(keep)
    return {
        "file": filename,
        "line_count": len(lines),
        "selection_truncated": len(selection) > max_lines,
        "match_summary": matches,
        "lines": [{"line": i + 1, "text": lines[i][:280]}
                  for i in selection[:max_lines]],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not re.fullmatch("[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run ID")
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE105_SOURCE_REVIEW",
        "run_id": args.run_id,
        "status": "NAO_VERIFICADO",
        "phase": "START",
        "snapshot_sha256_valid": False,
        "source_sha256_valid": False,
        "restore_executed": False,
        "patch_executed": False,
        "apk_built": False,
        "key_accessed": False,
    }
    try:
        report["phase"] = "GOOGLE_AUTH"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre105_") as tmp:
            archive = Path(tmp) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD"
            download(drive, archive)
            report["phase"] = "VERIFY_ARCHIVE"
            digest, _md5, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 digest mismatch")
            report["snapshot_sha256_valid"] = True
            report["phase"] = "READ_MEMBERS"
            with tarfile.open(archive, "r:gz", errorlevel=2) as tar:
                members = {m.name: m for m in tar
                           if m.isfile() and
                           (m.name == SOURCE_NAME or m.name.endswith(SECONDARY_SUFFIX))}
                primary = members.get(SOURCE_NAME)
                if primary is None or primary.size > 2_000_000:
                    raise ValueError("Unexpected settings source member")
                f = tar.extractfile(primary)
                if f is None:
                    raise ValueError("Unable to read settings source")
                content = f.read()
                source_hash = hashlib.sha256(content).hexdigest()
                report["source_sha256"] = source_hash
                if source_hash != SOURCE_SHA256:
                    raise ValueError("PRE92 source hash mismatch")
                report["source_sha256_valid"] = True
                report["settings_source"] = source_excerpt(content, SOURCE_NAME, MAX_LINES)
                secondaries = []
                for name, member in members.items():
                    if name == SOURCE_NAME or member.size > 2_000_000:
                        continue
                    stream = tar.extractfile(member)
                    if stream is None:
                        continue
                    secondary = stream.read()
                    secondaries.append(source_excerpt(secondary, name, 75))
                report["other_ui_sources"] = secondaries[:2]
        report["status"] = "FONTE_VERIFICADA_E_ANALISADA"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE105 failed in phase:", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print("PRE105:", report["status"])
    return 0 if report["status"] == "FONTE_VERIFICADA_E_ANALISADA" else 1

if __name__ == "__main__":
    raise SystemExit(main())
