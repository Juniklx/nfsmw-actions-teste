#!/usr/bin/env python3
"""NFSMW PRE98 independent APK binary audit, read-only.

Compare V25 and V26 Android ARM64 native libraries and settings UI text markers.
No extraction to the game workspace, no building, signing, patches or secret output.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

INPUTS = {
    "V25": {
        "id": "1dJOZasd-wYMNIrQer7IG7Mk3k3lYevPz",
        "sha256": "35850d4ac0830d957a7f01e403f905bc8e8a4497904983654d0f608450420610",
    },
    "V26": {
        "id": "1HcWA8UFugXNO4IPPH8kgUcX5CwP4UobW",
        "sha256": "d8aebdaaf75df75739b47148f69ecfcdf1add37422416249375e31eca7812092",
        "bytes": 47065185,
    },
}
MARKERS = {
    "NEED_FOR_SPEED_MOST_WANTED": "NEED FOR SPEED / MOST WANTED",
    "SETTINGS_ANDROID_HEADER": "SETTINGS  /  ANDROID",
    "SAVE_SETTINGS": "SAVE SETTINGS",
}
MAX_ENTRY = 512 * 1024 * 1024
MAX_ENTRIES = 10000


def bytes_sha256(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(8 * 1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def get_drive_client():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def download(drive, file_id: str, target: Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload
    request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    with target.open("wb") as file:
        dl = MediaIoBaseDownload(file, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _progress, done = dl.next_chunk(num_retries=4)


def library_fingerprint(handle: zipfile.ZipFile, entry: zipfile.ZipInfo) -> dict:
    if entry.file_size > MAX_ENTRY:
        raise ValueError("Excessive ELF library size")
    h = hashlib.sha256()
    patterns = {}
    for key, value in MARKERS.items():
        encoded = value.encode("utf-8")
        patterns[key] = [encoded, value.encode("utf-16le"), value.encode("utf-16be")]
    longest = max(len(v) for values in patterns.values() for v in values)
    found = {k: [] for k in patterns}
    tail = b""
    with handle.open(entry) as fp:
        while True:
            chunk = fp.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            haystack = tail + chunk
            for name, variants in patterns.items():
                for i, marker in enumerate(variants):
                    if marker in haystack:
                        fmt = ("utf8", "utf16le", "utf16be")[i]
                        if fmt not in found[name]:
                            found[name].append(fmt)
            tail = haystack[-longest:]
    return {
        "sha256": h.hexdigest(),
        "size": entry.file_size,
        "markers": {name: modes for name, modes in found.items() if modes},
    }


def audit_apk(path: Path) -> dict:
    with zipfile.ZipFile(path, "r", allowZip64=True) as z:
        names = z.infolist()
        if len(names) > MAX_ENTRIES:
            raise ValueError("Too many entries in APK")
        selected = [info for info in names
                    if info.filename.startswith("lib/arm64-v8a/")
                    and info.filename.endswith(".so")]
        if not selected:
            raise ValueError("No ARM64 native libraries in APK")
        results = {}
        for info in selected:
            if info.filename in results:
                raise ValueError("Duplicate ARM64 .so filename")
            results[info.filename] = library_fingerprint(z, info)
        return {
            "zip_entries": len(names),
            "arm64_library_count": len(selected),
            "arm64_libraries": results,
        }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid run id")
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE98_AUDITORIA_BINARIA_APK_V25_V26",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "modo": "SOMENTE_LEITURA",
        "notebook_principal_modificado": False,
        "backup_pre99_modificado": False,
        "apk_modificado": False,
        "compilacao_executada": False,
        "chave_permanente_acessada": False,
        "apks": {},
    }
    try:
        if any(not os.environ.get(name) for name in (
            "GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"
        )):
            raise RuntimeError("Google secrets not configured")
        report["phase"] = "GOOGLE_OAUTH"
        drive = get_drive_client()
        report["phase"] = "DOWNLOAD_AND_VERIFY_APKS"
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre98_", dir="/tmp") as tmp:
            for version, meta in INPUTS.items():
                path = Path(tmp) / (version + ".apk")
                download(drive, meta["id"], path)
                sha, n = bytes_sha256(path)
                if sha != meta["sha256"]:
                    raise ValueError("APK SHA256 mismatch: " + version)
                if "bytes" in meta and n != meta["bytes"]:
                    raise ValueError("APK bytes mismatch: " + version)
                apk = audit_apk(path)
                apk["sha256"] = sha
                apk["bytes"] = n
                apk["drive_id"] = meta["id"]
                report["apks"][version] = apk
        report["phase"] = "COMPARE_NATIVE_LIBRARIES"
        v25 = report["apks"]["V25"]["arm64_libraries"]
        v26 = report["apks"]["V26"]["arm64_libraries"]
        all_names = sorted(set(v25) | set(v26))
        changes = {}
        for name in all_names:
            old = v25.get(name)
            new = v26.get(name)
            changes[name] = ("missing_in_v25" if old is None else
                             "missing_in_v26" if new is None else
                             "changed" if old["sha256"] != new["sha256"] else
                             "identical")
        report["library_changes"] = changes
        report["changed_library_count"] = sum(value == "changed" for value in changes.values())
        report["source_code_linkage_proven"] = False
        report["settings_overlay_executed_proven"] = False
        report["note"] = (
            "Markers found in an ELF show embedded text, not that code executed. "
            "Absent markers can indicate dead-code elimination, alternate formatting or linkage differences."
        )
        report["status"] = "AUDITORIA_BINARIA_CONCLUIDA"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE98 audit not completed; phase:", report["phase"],
              "; error type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print("PRE98 result:", report["status"])
    return 0 if report["status"] == "AUDITORIA_BINARIA_CONCLUIDA" else 1


if __name__ == "__main__":
    raise SystemExit(main())
