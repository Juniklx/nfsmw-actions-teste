#!/usr/bin/env python3
"""NFSMW PRE104: SHA256 of PRE99 TAR and read-only TAR structure audit.

Only reads PRE99 from Drive. Does not extract, restore, patch, sign or build anything.
The 875 MB archive stays on an ephemeral GitHub runner and is deleted at the end.
No OAuth values or raw file contents are written to the GitHub status report.
"""
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
from pathlib import Path, PurePosixPath

BACKUP_ID = "1qXEY5JXUdvZB4CuqPvXARz8TY-FArdzb"
EXPECTED_BYTES = 874780689
EXPECTED_SHA256 = "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
EXPECTED_MD5 = "95feb430df12bb1c6d9d82885ef9cdce"
EXPECTED_ENTRIES = 28911
EXPECTED_SOURCE_SHA256 = "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"
SOURCE_SUFFIX = "nativo/sdk/src/ui/overlay/settings_overlay.cpp"
SECRETS = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
MAX_ENTRIES = 250000
MAX_SOURCE_BYTES = 4 * 1024 * 1024
DANGEROUS_SUFFIXES = (".p12", ".pfx", ".jks", ".keystore", ".pem", ".key")
DANGEROUS_NAMES = (
    "nfsmw_assinatura_credenciais.properties",
    "nfsmw_assinatura_permanente.p12",
    "kaggle.json",
    "credentials.json",
    "client_secret.json",
)
DANGEROUS_PATTERNS = (
    "refresh_token", "client_secret", "service_account",
    "oauth_token", "assinatura_credenciais",
)


def safe_member_name(value: str) -> bool:
    if not value or "\x00" in value or "\\" in value or value.startswith("/"):
        return False
    parts = PurePosixPath(value).parts
    if any(part in (".", "..") for part in value.split("/")):
        return False
    if not parts or ":" in parts[0]:
        return False
    return True


def looks_sensitive(name: str) -> bool:
    lower = name.lower()
    base = lower.rsplit("/", 1)[-1]
    return (
        base in DANGEROUS_NAMES
        or base.endswith(DANGEROUS_SUFFIXES)
        or any(pattern in base for pattern in DANGEROUS_PATTERNS)
    )


def sha_file(path: Path) -> tuple[str, str, int]:
    sha, md5 = hashlib.sha256(), hashlib.md5()
    count = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(16 * 1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
            md5.update(chunk)
            count += len(chunk)
    return sha.hexdigest(), md5.hexdigest(), count


def tar_audit(archive: Path) -> dict:
    stats = Counter()
    seen = set()
    duplicates = 0
    unsafe_names = 0
    unsafe_links = 0
    sensitive_names = 0
    suspicious_types = 0
    candidate_sources: list[dict] = []
    total_declared_uncompressed = 0
    with tarfile.open(archive, mode="r:gz", errorlevel=2) as tf:
        for member in tf:
            stats["members"] += 1
            if stats["members"] > MAX_ENTRIES:
                raise ValueError("Excessive TAR member count")
            name = member.name
            if not safe_member_name(name):
                unsafe_names += 1
            if name in seen:
                duplicates += 1
            seen.add(name)
            if looks_sensitive(name):
                sensitive_names += 1
            if member.isdir():
                stats["directories"] += 1
            elif member.isfile():
                stats["regular_files"] += 1
                total_declared_uncompressed += member.size
                if name.endswith(SOURCE_SUFFIX):
                    if member.size > MAX_SOURCE_BYTES:
                        raise ValueError("Oversized settings_overlay.cpp")
                    data = tf.extractfile(member)
                    if data is None:
                        raise ValueError("Unable to read settings_overlay.cpp")
                    digest = hashlib.sha256()
                    read_bytes = 0
                    with data:
                        for piece in iter(lambda: data.read(1024 * 1024), b""):
                            digest.update(piece)
                            read_bytes += len(piece)
                    candidate_sources.append({
                        "relative_path": name[:350],
                        "bytes": read_bytes,
                        "sha256": digest.hexdigest(),
                        "matches_pre92_expected": digest.hexdigest() == EXPECTED_SOURCE_SHA256,
                    })
            elif member.issym() or member.islnk():
                stats["links"] += 1
                # TAR link names may be relative to the containing directory. Do not follow.
                if not safe_member_name(member.linkname):
                    unsafe_links += 1
            else:
                suspicious_types += 1
    return {
        "member_count": stats["members"],
        "member_count_matches_manifest": stats["members"] == EXPECTED_ENTRIES,
        "regular_files": stats["regular_files"],
        "directories": stats["directories"],
        "links_without_following": stats["links"],
        "unsafe_paths": unsafe_names,
        "duplicate_paths": duplicates,
        "unsafe_link_targets": unsafe_links,
        "special_entries": suspicious_types,
        "sensitive_filenames_detected": sensitive_names,
        "uncompressed_member_bytes": total_declared_uncompressed,
        "source_overlay_candidates": candidate_sources[:12],
        "source_overlay_candidate_count": len(candidate_sources),
        "source_overlay_pre92_hash_found": any(
            c["matches_pre92_expected"] for c in candidate_sources
        ),
        "contains_suspicious_archive_entries": any(
            (unsafe_names, duplicates, unsafe_links, suspicious_types, sensitive_names)
        ),
        "extracted_files": False,
    }


def run(report: dict, scratch: Path) -> None:
    if any(not os.environ.get(k) for k in SECRETS):
        raise RuntimeError("Google OAuth secret labels not configured")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    creds = Credentials(
        token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    report["phase"] = "GOOGLE_OAUTH"
    creds.refresh(Request())
    report["oauth_refresh_succeeded"] = True
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    report["phase"] = "GOOGLE_DRIVE_METADATA"
    md = drive.files().get(fileId=BACKUP_ID,
                           fields="id,name,mimeType,size,md5Checksum",
                           supportsAllDrives=True).execute()
    if int(md.get("size", -1)) != EXPECTED_BYTES:
        raise ValueError("Remote backup size differs from expected PRE99")
    if md.get("md5Checksum", "").lower() != EXPECTED_MD5:
        raise ValueError("Remote backup MD5 differs from expected PRE99")
    report["drive_metadata_matches_pre99"] = True

    available = shutil.disk_usage(scratch).free
    report["free_bytes_before_download"] = available
    if available < EXPECTED_BYTES + 2 * 1024 * 1024 * 1024:
        raise RuntimeError("Not enough free runner disk for safe TAR audit")

    archive = scratch / "nfsmw_pre99_audit_only.tar.gz"
    report["phase"] = "DOWNLOAD_PRE99"
    request = drive.files().get_media(fileId=BACKUP_ID, supportsAllDrives=True)
    with archive.open("wb") as stream:
        downloader = MediaIoBaseDownload(stream, request, chunksize=16 * 1024 * 1024)
        done = False
        while not done:
            _status, done = downloader.next_chunk(num_retries=4)
    report["download_finished"] = True
    report["phase"] = "VERIFY_FULL_DIGEST"
    sha, md5, size = sha_file(archive)
    report["actual_bytes"] = size
    report["actual_sha256"] = sha
    report["actual_md5"] = md5
    report["full_sha256_matches_pre99"] = (sha == EXPECTED_SHA256)
    report["full_md5_matches_pre99"] = (md5 == EXPECTED_MD5)
    report["full_size_matches_pre99"] = (size == EXPECTED_BYTES)
    if not all((report["full_sha256_matches_pre99"],
                report["full_md5_matches_pre99"],
                report["full_size_matches_pre99"])):
        raise ValueError("Full backup digest/size verification failed")

    report["phase"] = "READ_ONLY_TAR_AUDIT"
    report["tar_audit"] = tar_audit(archive)
    report["phase"] = "COMPLETE"
    audit = report["tar_audit"]
    if audit["contains_suspicious_archive_entries"]:
        report["result"] = "INTEGRIDADE_VALIDA_COM_RISCOS_NO_TAR"
    elif not audit["member_count_matches_manifest"]:
        report["result"] = "INTEGRIDADE_VALIDA_CONTAGEM_DIVERGENTE"
    else:
        report["result"] = "BACKUP_INTEGRO_E_AUDITADO"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run identifier")
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE104_INTEGRIDADE_TAR_PRE99",
        "github_run_id": args.run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backup_drive_id": BACKUP_ID,
        "expected_bytes": EXPECTED_BYTES,
        "expected_sha256": EXPECTED_SHA256,
        "expected_md5": EXPECTED_MD5,
        "result": "NAO_VALIDADO",
        "phase": "INITIAL",
        "oauth_refresh_succeeded": False,
        "drive_metadata_matches_pre99": False,
        "download_finished": False,
        "full_sha256_matches_pre99": False,
        "restoration_performed": False,
        "source_modified": False,
        "apk_modified": False,
        "signing_key_accessed": False,
        "secrets_printed": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre104_", dir="/tmp") as root:
            run(report, Path(root))
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        # Avoid exception messages: some Google API errors include URLs or sensitive metadata.
        print("PRE104 not approved; phase:", report["phase"],
              "; exception type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print("PRE104:", report["result"], "phase:", report["phase"],
              "full_sha256_ok:", report["full_sha256_matches_pre99"])
    return 0 if report["result"] == "BACKUP_INTEGRO_E_AUDITADO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
