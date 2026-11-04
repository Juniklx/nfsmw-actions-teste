#!/usr/bin/env python3
"""PRE103: Google Drive PRE99 *metadata-only* probe from GitHub Actions.

Reads OAuth inputs only from GitHub Actions Secrets. Never prints credentials.
Does not download, extract, restore or upload any backup or APK.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

FOLDER_ID = "1Waam42x_suvBS18b4360HOaBqKxAncvy"
BACKUP_ID = "1qXEY5JXUdvZB4CuqPvXARz8TY-FArdzb"
MANIFEST_ID = "1sDPE59rZB6iOWKiBoI6PawluXv-tWA0j"
BACKUP_BYTES = 874780689
BACKUP_MD5 = "95feb430df12bb1c6d9d82885ef9cdce"
BACKUP_SHA256 = "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
PRE92_SHA256 = "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"
SECRET_NAMES = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE103_GITHUB_DRIVE_PROBE",
        "github_run_id": args.run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "modo": "SOMENTE_LEITURA",
        "status": "NAO_VALIDADO",
        "checks": {},
        "backup_restaurado": False,
        "integridade_sha256_tar_recalculada": False,
        "notebook_principal_modificado": False,
        "chave_permanente_acessada": False,
        "fase_falha": None,
    }
    try:
        missing = [label for label in SECRET_NAMES if not os.environ.get(label)]
        if missing:
            report["fase_falha"] = "GITHUB_ACTIONS_SECRETS"
            report["secrets_ausentes"] = missing  # labels only, NEVER secret values
            raise ValueError("Missing GitHub secret labels")

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        report["fase_falha"] = "GOOGLE_OAUTH"
        creds = Credentials(
            token=None,
            refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        )
        creds.refresh(Request())
        report["checks"]["refresh_google_oauth"] = True

        report["fase_falha"] = "GOOGLE_DRIVE"
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        bk = drive.files().get(
            fileId=BACKUP_ID, fields="id,name,size,md5Checksum,parents",
            supportsAllDrives=True,
        ).execute()
        mf = drive.files().get(
            fileId=MANIFEST_ID, fields="id,name,size,parents",
            supportsAllDrives=True,
        ).execute()
        manifest_blob = drive.files().get_media(
            fileId=MANIFEST_ID,
            supportsAllDrives=True,
        ).execute()
        if isinstance(manifest_blob, str):
            manifest_blob = manifest_blob.encode("utf-8")
        manifest = json.loads(manifest_blob)
        checks = {
            "backup_bytes": int(bk.get("size", -1)) == BACKUP_BYTES,
            "backup_md5_metadados": bk.get("md5Checksum", "").lower() == BACKUP_MD5,
            "backup_na_pasta": FOLDER_ID in bk.get("parents", []),
            "manifesto_na_pasta": FOLDER_ID in mf.get("parents", []),
            "manifesto_sha256_declarado": manifest.get("sha256") == BACKUP_SHA256,
            "manifesto_md5": manifest.get("md5") == BACKUP_MD5,
            "manifesto_bytes": manifest.get("bytes") == BACKUP_BYTES,
            "manifesto_staging_pal_usa": manifest.get("staging_pal_usa") is True,
            "manifesto_fonte_pre92": manifest.get("fonte_pre92_sha256") == PRE92_SHA256,
            "manifesto_upload_confirmado": manifest.get("status") == "BACKUP_DRIVE_CONFIRMADO",
        }
        report["checks"].update(checks)
        report["backup_id"] = BACKUP_ID
        report["status"] = "DRIVE_PRE99_METADATA_VALIDADO" if all(checks.values()) else "DIVERGENCIA_METADADOS"
        if report["status"] == "DRIVE_PRE99_METADATA_VALIDADO":
            report["fase_falha"] = None
    except Exception as exc:
        report["erro_tipo"] = type(exc).__name__  # never report exception text
        print("PRE103 verificação não aprovada. Fase:", report["fase_falha"],
              "Tipo:", type(exc).__name__)
    finally:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print("PRE103 status:", report["status"])
    return 0 if report["status"] == "DRIVE_PRE99_METADATA_VALIDADO" else 1


if __name__ == "__main__":
    sys.exit(main())
