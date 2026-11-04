#!/usr/bin/env python3
"""Generate a private Kaggle notebook that probes only Drive PRE99 metadata.

No backup extraction, no project writes, no APK builds, no credentials in reports.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

KERNEL = "juniklx/nfsmw-pre102-drive-probe"

CELL = r'''
from pathlib import Path
from datetime import datetime, timezone
import json

RUN_ID = __RUN_ID__
BACKUP_ID = "1qXEY5JXUdvZB4CuqPvXARz8TY-FArdzb"
MANIFEST_ID = "1sDPE59rZB6iOWKiBoI6PawluXv-tWA0j"
PROJECT_FOLDER = "1Waam42x_suvBS18b4360HOaBqKxAncvy"
EXPECTED_SIZE = 874780689
EXPECTED_MD5 = "95feb430df12bb1c6d9d82885ef9cdce"
EXPECTED_SHA256 = "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
EXPECTED_SOURCE_SHA256 = "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"

report = {
    "etapa": "PRE102_KAGGLE_DRIVE_PROBE",
    "github_run_id": RUN_ID,
    "status": "NAO_VALIDADO",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "modo": "SOMENTE_LEITURA",
    "backup_restaurado": False,
    "backup_integridade_sha256_recalculada": False,
    "notebook_principal_modificado": False,
    "assinatura_acessada": False,
    "verificacoes": {},
}

try:
    from kaggle_secrets import UserSecretsClient
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    secrets = UserSecretsClient()
    labels = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    secure_values = {}
    for label in labels:
        try:
            value = secrets.get_secret(label)
            if not value:
                raise ValueError("empty secret")
            secure_values[label] = value
        except Exception as exc:
            report["fase_falha"] = "KAGGLE_SECRETS"
            report["secret_label_indisponivel"] = label
            report["erro_tipo"] = type(exc).__name__
            raise

    report["verificacoes"]["kaggle_secrets_disponiveis"] = True
    credentials = Credentials(
        token=None,
        refresh_token=secure_values["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=secure_values["GOOGLE_CLIENT_ID"],
        client_secret=secure_values["GOOGLE_CLIENT_SECRET"],
    )
    report["fase_falha"] = "GOOGLE_OAUTH"
    credentials.refresh(Request())
    report["verificacoes"]["oauth_refresh_funcionou"] = True

    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    report["fase_falha"] = "GOOGLE_DRIVE_METADATA"
    backup_meta = drive.files().get(
        fileId=BACKUP_ID,
        fields="id,name,size,md5Checksum,parents",
        supportsAllDrives=True,
    ).execute()
    manifest_meta = drive.files().get(
        fileId=MANIFEST_ID,
        fields="id,name,size,parents",
        supportsAllDrives=True,
    ).execute()

    manifest_bytes = drive.files().get_media(
        fileId=MANIFEST_ID,
        supportsAllDrives=True,
    ).execute()
    if isinstance(manifest_bytes, str):
        manifest_bytes = manifest_bytes.encode("utf-8")
    manifest = json.loads(manifest_bytes)

    checks = {
        "backup_tamanho_no_drive": int(backup_meta.get("size", -1)) == EXPECTED_SIZE,
        "backup_md5_no_drive": backup_meta.get("md5Checksum", "").lower() == EXPECTED_MD5,
        "backup_na_pasta_projeto": PROJECT_FOLDER in backup_meta.get("parents", []),
        "manifesto_na_pasta_projeto": PROJECT_FOLDER in manifest_meta.get("parents", []),
        "manifesto_sha256_declarado": manifest.get("sha256") == EXPECTED_SHA256,
        "manifesto_md5_declarado": manifest.get("md5") == EXPECTED_MD5,
        "manifesto_tamanho": manifest.get("bytes") == EXPECTED_SIZE,
        "manifesto_staging_pal_usa": manifest.get("staging_pal_usa") is True,
        "manifesto_fonte_pre92": manifest.get("fonte_pre92_sha256") == EXPECTED_SOURCE_SHA256,
        "manifesto_backup_confirmado": manifest.get("status") == "BACKUP_DRIVE_CONFIRMADO",
    }
    report["verificacoes"].update(checks)
    report["backup_drive_id"] = BACKUP_ID
    report["backup_bytes_declarados"] = EXPECTED_SIZE
    report["integridade_ate_aqui"] = "metadados remotos + manifesto; TAR ainda nao baixado"
    report["status"] = "DRIVE_PRE99_METADATA_VALIDADO" if all(checks.values()) else "DIVERGENCIA_METADADOS"
    report["fase_falha"] = None
except Exception as exc:
    # Do NOT write exception strings, traces, credentials or token values into logs.
    if report["status"] == "NAO_VALIDADO":
        report["erro_tipo"] = type(exc).__name__
    print("PRE102 nao validada; fase:", report.get("fase_falha", "INDEFINIDA"),
          "; tipo:", report.get("erro_tipo", "N/A"))
finally:
    output = Path("/kaggle/working/NFSMW_PRE102_DRIVE_PROBE.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PRE102 status:", report["status"])
    print("Relatorio:", output.name)
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid run ID")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    code = CELL.replace("__RUN_ID__", repr(args.run_id))
    notebook_name = "nfsmw_pre102_drive_probe.ipynb"
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "nfsmw-pre102-intro",
                "metadata": {},
                "source": [
                    "# NFSMW PRE102 — Drive metadata probe (read-only)\n",
                    "Verifica secrets e metadados do backup PRE99. Nao baixa nem restaura o TAR; nao acessa assinatura ou projeto.\n",
                ],
            },
            {
                "cell_type": "code",
                "id": "nfsmw-pre102-probe",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": code.splitlines(keepends=True),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    metadata = {
        "id": KERNEL,
        "title": "NFSMW PRE102 Drive Probe",
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    (out / notebook_name).write_text(
        json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "kernel-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("PRE102 notebook privado preparado:", KERNEL)


if __name__ == "__main__":
    main()
