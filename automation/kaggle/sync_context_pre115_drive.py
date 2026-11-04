#!/usr/bin/env python3
"""Append the verified PRE115 chronology to canonical Drive Markdown safely.

Preserve every original byte, make an immutable-in-practice timestamped Drive
copy first, update the original file ID only after checksum checks, and verify
readback. Never touches game archives, APKs, signing keys or credential values.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

CONTEXT_ID = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
PARENT_ID = "1Waam42x_suvBS18b4360HOaBqKxAncvy"
APPEND_FILE = Path("automation/kaggle/ADENDO_CONTEXTO_PRE115_20261104.md")
STAGE_MARKER = "## 99. Atualização consolidada PRE98–PRE115:"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_client():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    auth = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    auth.refresh(Request())
    return build("drive", "v3", credentials=auth, cache_discovery=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run id")
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE115_CONTEXT_CANONICAL_SYNC",
        "github_run_id": args.run_id,
        "target_drive_id": CONTEXT_ID,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "original_content_preserved": False,
        "backup_created": False,
        "game_workspace_modified": False,
        "apk_built": False,
        "signing_key_accessed": False,
        "secrets_logged": False,
    }
    try:
        report["phase"] = "VERIFY_EVIDENCE"
        r112 = json.loads(Path("automation/kaggle/status/pre112_cpp_syntax.json").read_text(encoding="utf-8"))
        r111 = json.loads(Path("automation/kaggle/status/pre111_dryrun_palette.json").read_text(encoding="utf-8"))
        if (r112.get("status") != "SINTAXE_CPP_FONTE_COMPLETA_VALIDADA_NO_HOST"
            or r112.get("host_cpp_standard") != "c++23"
            or not r112.get("baseline_host_cpp", {}).get("passed")
            or not r112.get("proposal_host_cpp", {}).get("passed")
            or not r112.get("snapshot_sha256_verified")
            or r111.get("status") != "PRE111_DIFF_VALIDADO_NAO_APLICADO"
            or r111.get("patch_applied") is not False):
            raise ValueError("PRE111/PRE112 evidence does not pass validation")

        r113 = json.loads(Path("automation/kaggle/status/pre113b_android_arm64.json").read_text(encoding="utf-8"))
        r114 = json.loads(Path("automation/kaggle/status/pre114_header_scroll.json").read_text(encoding="utf-8"))
        r115 = json.loads(Path("automation/kaggle/status/pre115_scroll_dryrun.json").read_text(encoding="utf-8"))
        r103 = json.loads(Path("automation/kaggle/status/pre103_github_drive.json").read_text(encoding="utf-8"))
        if (r113.get("status") != "SINTAXE_ANDROID_ARM64_CPP23_VALIDADA"
            or not r113.get("android_arm64_baseline", {}).get("passed")
            or not r113.get("android_arm64_proposal", {}).get("passed")
            or r114.get("status") != "HEADER_SCROLL_CLIP_ESTATICO_AUDITADO"
            or r114.get("audit", {}).get("header_comes_before_search") is not True
            or r115.get("status") != "PRE115_PROPOSTA_SCROLL_ARM64_VALIDADA_NAO_APLICADA"
            or r115.get("original_cpp_arm64_passed") is not True
            or r115.get("proposed_cpp_arm64_passed") is not True
            or r115.get("active_workspace_modified") is not False
            or r115.get("apk_built") is not False
            or r103.get("drive_status") != "DRIVE_PRE99_METADATA_VALIDADO"):
            raise ValueError("Latest PRE103/PRE113/PRE114/PRE115 evidence not validated")

        appendix = APPEND_FILE.read_bytes()
        if STAGE_MARKER.encode("utf-8") not in appendix:
            raise ValueError("Expected context appendix marker missing")
        if len(appendix) < 1000 or len(appendix) > 15000:
            raise ValueError("Unexpected appendix size")

        report["phase"] = "GET_DRIVE_CONTEXT"
        drive = get_client()
        meta = drive.files().get(
            fileId=CONTEXT_ID,
            fields="id,name,size,mimeType,md5Checksum,parents",
            supportsAllDrives=True,
        ).execute()
        if (meta.get("name") != "CONTEXTO_NFSMW.md"
            or PARENT_ID not in meta.get("parents", [])
            or meta.get("mimeType", "").startswith("application/vnd.google-apps")
            or int(meta.get("size", 0)) < 200_000):
            raise ValueError("Unexpected canonical Drive file metadata")

        content = drive.files().get_media(fileId=CONTEXT_ID, supportsAllDrives=True).execute()
        if isinstance(content, str):
            content = content.encode("utf-8")
        md5 = hashlib.md5(content).hexdigest()
        if int(meta.get("size", -1)) != len(content) or meta.get("md5Checksum", "").lower() != md5:
            raise ValueError("Canonical Drive file size/md5 mismatch")
        decoded = content.decode("utf-8")
        if not decoded.startswith("# CONTEXTO DO PROJETO"):
            raise ValueError("Canonical context header does not match")
        if STAGE_MARKER in decoded:
            report["status"] = "ADENDO_JA_EXISTENTE"
            report["original_content_preserved"] = True
            return 0

        report["old_bytes"] = len(content)
        report["old_sha256"] = sha256(content)
        # Prior copy was independently made through the connected Drive app and
        # compared byte-for-byte. Verify it again before any in-place update.
        report["phase"] = "VERIFY_EXISTING_DRIVE_BACKUP"
        verified_backup_id = "1fcbDBOvCB4Cxb89yrP26hh6vfz4-by-Q"
        backup = drive.files().get(
            fileId=verified_backup_id,
            fields="id,name,size,md5Checksum,parents",
            supportsAllDrives=True,
        ).execute()
        report["backup_drive_id"] = verified_backup_id
        if (backup.get("name") != "CONTEXTO_NFSMW_BACKUP_ANTES_PRE115_20261104_1132UTC.md"
            or PARENT_ID not in backup.get("parents", [])
            or int(backup.get("size", -1)) != len(content)
            or backup.get("md5Checksum", "").lower() != md5):
            raise ValueError("Verified Drive backup differs from original")
        report["backup_verified"] = True

        report["phase"] = "VERIFY_NO_CONCURRENT_EDITS"
        latest = drive.files().get(
            fileId=CONTEXT_ID, fields="size,md5Checksum",
            supportsAllDrives=True
        ).execute()
        if (int(latest.get("size", -1)) != len(content)
            or latest.get("md5Checksum", "").lower() != md5):
            raise RuntimeError("Canonical context changed since initial read")

        report["phase"] = "APPEND_CANONICAL"
        updated = content + (b"\n" if not content.endswith(b"\n") else b"") + b"\n" + appendix
        from googleapiclient.http import MediaIoBaseUpload
        upload = MediaIoBaseUpload(
            io.BytesIO(updated), mimetype=meta.get("mimeType") or "text/plain",
            resumable=False,
        )
        drive.files().update(
            fileId=CONTEXT_ID,
            media_body=upload,
            supportsAllDrives=True,
            fields="id,name,size,md5Checksum",
        ).execute()
        report["phase"] = "VERIFY_CANONICAL_READBACK"
        readback = drive.files().get_media(fileId=CONTEXT_ID, supportsAllDrives=True).execute()
        if isinstance(readback, str):
            readback = readback.encode("utf-8")
        if readback != updated:
            raise RuntimeError("Updated Drive Markdown readback differs from expected")
        if not readback.startswith(content) or STAGE_MARKER.encode("utf-8") not in readback:
            raise RuntimeError("History preservation or appendix marker mismatch")
        report["original_content_preserved"] = True
        report["new_bytes"] = len(readback)
        report["new_sha256"] = sha256(readback)
        report["status"] = "CONTEXTO_CANONICO_ATUALIZADO_VALIDADO"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        resp = getattr(exc, "resp", None)
        if resp is not None:
            # Numeric status only; never print URLs, headers or token-bearing errors.
            report["google_http_status"] = getattr(resp, "status", None)
        print("PRE115 context sync not confirmed, phase:", report["phase"],
              "error type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("PRE115 canonical context sync:", report["status"])
    return 0 if report["status"] in (
        "CONTEXTO_CANONICO_ATUALIZADO_VALIDADO", "ADENDO_JA_EXISTENTE"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
