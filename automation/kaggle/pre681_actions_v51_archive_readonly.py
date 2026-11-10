#!/usr/bin/env python3
"""PRE681: audit V51 APK + archived source + PRE656 log without publishing private inputs.
Public source code, private execution inputs. No APK signing or game modification.
This does NOT read Galaxy S24 FE private preferences and proves no FPS improvement.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
import os
import re
import tempfile
import tomllib
import zipfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

INPUTS = {
    "apk": ("1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws", "v51.apk",
            47104417, "207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"),
    "source": ("11jLQdQ7UshqWfQ0xctZhVZdCjGbUWHL_", "source.zip",
               21026481, "0ab7c949e62d377f444fb7b2489bc66d6387bd49b1798f184c4a953314064231"),
    "log": ("1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd", "pre656.log",
            576129, "649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"),
}
OUTPUT_FOLDER = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
ASSET = "assets/nativo/nfsmw.toml"
ASSET_SHA256 = "9602e9f7409eaab83b295521d00fecb95b04d629a8f7cea48911473f77a4f0d2"
PREFIX = "NFSMW-Recompiled-Mobile-main/"
GRAPHIC_KEYS = [
    "nfsmw_nativo_sin_desenfoque",
    "nfsmw_nativo_pcf_barato",
    "nfsmw_sombras_sin_vegetacion",
    "nfsmw_nativo_sombras_escala",
    "nfsmw_sombras_corte",
    "nfsmw_resolucion_interna",
    "nfsmw_limite_fps",
]
JAVA_ANCHORS = {
    "Ajustes.java": [
        'p.getBoolean("desenfoque", false)',
        'p.getString("calidad_sombras", SOMBRAS_RAPIDA)',
        'p.getString("resolucion_interna", "1280x720")',
        'p.getInt("limite_fps", 60)',
    ],
    "MotorNativo.java": [
        '"--nfsmw_nativo_sin_desenfoque=" + !ajustes.desenfoque()',
        '"--nfsmw_nativo_pcf_barato=" + Ajustes.SOMBRAS_RAPIDA.equals(sombras)',
        '"--nfsmw_sombras_sin_vegetacion=" + !Ajustes.SOMBRAS_XBOX.equals(sombras)',
        '"--nfsmw_nativo_sombras_escala=" + ajustes.sombrasEscala()',
        '"--nfsmw_sombras_corte=" + ajustes.sombrasCorte()',
        'new File(ctx.getFilesDir(), "nativo/usuario")',
    ],
}
DEX_MARKERS = [
    "--nfsmw_nativo_sin_desenfoque=",
    "--nfsmw_nativo_pcf_barato=",
    "--nfsmw_sombras_sin_vegetacion=",
    "--nfsmw_nativo_sombras_escala=",
    "--nfsmw_resolucion_interna=",
    "--nfsmw_limite_fps=",
]


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def drive_client():
    secret_names = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    missing = [name for name in secret_names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("PRE681_MISSING_GITHUB_SECRETS: " + ",".join(missing))
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def download_pinned(drive, pin, folder: Path) -> Path:
    file_id, name, expected_size, expected_sha = pin
    dest = folder / name
    with dest.open("wb") as output:
        request = drive.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(output, request, chunksize=4 * 1024 * 1024)
        finished = False
        while not finished:
            _, finished = downloader.next_chunk()
    data = dest.read_bytes()
    if len(data) != expected_size or sha256(data) != expected_sha:
        raise ValueError("PRE681_INPUT_PIN_MISMATCH: " + name)
    return dest


def examine(files: dict[str, Path]) -> dict:
    result = {
        "gate": "PRE681_ACTIONS_V51_ARCHIVE_READONLY",
        "status": "PASS_ARCHIVED_APK_SOURCE_AND_HISTORICAL_LOG_ONLY",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "baseline": {
            "release": "V51 PRE652",
            "package": "io.github.nfsmwrecomp",
            "version_code": 51,
            "permanent_signing_cert_sha256": "1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b",
        },
        "input_integrity": {kind: {"bytes": pin[2], "sha256": pin[3], "verified": True}
                            for kind, pin in INPUTS.items()},
    }
    with zipfile.ZipFile(files["apk"]) as archive:
        if archive.testzip() is not None:
            raise ValueError("PRE681_APK_ZIP_BAD_CRC")
        raw_toml = archive.read(ASSET)
        if sha256(raw_toml) != ASSET_SHA256:
            raise ValueError("PRE681_TOML_SHA256_MISMATCH")
        config = tomllib.loads(raw_toml.decode("utf-8"))
        if len(config) != 121:
            raise ValueError("PRE681_TOML_KEY_COUNT_MISMATCH")
        dex_files = [name for name in archive.namelist() if name.endswith(".dex")]
        if not dex_files:
            raise ValueError("PRE681_APK_DEX_MISSING")
        dex = b"".join(archive.read(name) for name in dex_files)
        if not all(marker.encode("utf-8") in dex for marker in DEX_MARKERS):
            raise ValueError("PRE681_DEX_GRAPHICS_MARKERS_MISSING")
        result["apk"] = {
            "zip_crc": "PASS", "asset": ASSET, "asset_sha256": ASSET_SHA256,
            "toml_key_count": len(config),
            "packaged_defaults_not_device_settings": {key: config.get(key) for key in GRAPHIC_KEYS},
            "dex_markers_present_not_control_flow_proof": True,
        }

    with zipfile.ZipFile(files["source"]) as archive:
        if archive.testzip() is not None:
            raise ValueError("PRE681_SOURCE_ZIP_BAD_CRC")
        if archive.read(PREFIX + "nativo/app/nfsmw_movil.toml") != raw_toml:
            raise ValueError("PRE681_TOML_SOURCE_APK_DIFFER")
        anchors = {}
        for name, markers in JAVA_ANCHORS.items():
            path = PREFIX + "android/app/src/main/java/io/github/nfsmwrecomp/" + name
            body = archive.read(path).decode("utf-8")
            matched = {}
            for marker in markers:
                count = body.count(marker)
                if count != 1:
                    raise ValueError("PRE681_JAVA_ANCHOR_COUNT: " + name)
                matched[marker] = True
            anchors[name] = {"anchors_verified": len(matched)}
        result["archived_java"] = {
            "anchors": anchors,
            "apk_toml_identical_to_archived_source": True,
            "archived_java_is_not_proof_of_apk_bytecode": True,
        }

    loglines = files["log"].read_text(encoding="utf-8", errors="replace").splitlines()
    if len(loglines) < 4:
        raise ValueError("PRE681_LOG_TOO_SHORT")
    match = re.search(
        r"\[ajustes\] resolucion interna (\d+x\d+) y limite de FPS (\d+): "
        r"modo de video (\d+x\d+) a ([\d.]+) Hz",
        loglines[3],
    )
    if not match or match.group(1) != "1920x1080" or match.group(2) != "60":
        raise ValueError("PRE681_LOG_SETTINGS_PIN_MISMATCH")
    result["observed_pre656_session"] = {
        "internal_resolution": match.group(1),
        "fps_limit": int(match.group(2)),
        "video_mode": match.group(3),
        "video_mode_refresh_hz": float(match.group(4)),
    }
    result["limits"] = {
        "galaxy_sharedpreferences_read": False,
        "device_private_toml_read": False,
        "effective_blur_or_shadow_settings_known": False,
        "source_or_apk_modified": False,
        "android_signing_material_accessed": False,
        "new_apk_built": False,
        "fps_improvement_proven": False,
    }
    return result


def upload_private(drive, zipfile_path: Path) -> None:
    media = MediaFileUpload(str(zipfile_path), mimetype="application/zip", resumable=True)
    item = drive.files().create(
        body={"name": zipfile_path.name, "parents": [OUTPUT_FOLDER]},
        media_body=media, fields="id,name,size,md5Checksum",
    ).execute()
    expected = zipfile_path.read_bytes()
    if item.get("size") != str(len(expected)) or item.get("md5Checksum") != hashlib.md5(expected).hexdigest():
        raise ValueError("PRE681_DRIVE_UPLOAD_METADATA_MISMATCH")
    readback = io.BytesIO()
    download = MediaIoBaseDownload(readback, drive.files().get_media(fileId=item["id"]))
    done = False
    while not done:
        _, done = download.next_chunk()
    if sha256(readback.getvalue()) != sha256(expected):
        raise ValueError("PRE681_DRIVE_READBACK_SHA256_MISMATCH")


def main() -> None:
    drive = drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre681_") as tempdir:
        temp = Path(tempdir)
        inputs = {kind: download_pinned(drive, pin, temp) for kind, pin in INPUTS.items()}
        result = examine(inputs)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
        bundle = temp / ("NFSMW_PRE681_ACTIONS_V51_READONLY_" + stamp + ".zip")
        public_summary = (
            "PRE681: arquivo APK V51, TOML, snapshot Java e log PRE656 auditados.\n"
            "Nao confirma preferencias privadas ativas no Galaxy S24 FE, desfoque, "
            "sombras ou ganhos de FPS. Sem patch e sem build.\n"
        )
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("PRE681_REPORT.json", json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            archive.writestr("PRE681_README.md", public_summary)
        with zipfile.ZipFile(bundle) as archive:
            if archive.testzip() is not None:
                raise ValueError("PRE681_OUTPUT_ZIP_BAD_CRC")
        upload_private(drive, bundle)
    print("PRE681_ACTIONS_V51_ARCHIVE_AUDIT=PASS")
    print("PRE681_DRIVE_PRIVATE_UPLOAD_READBACK=PASS")
    print("PRE681_DEVICE_GRAPHICS_SETTINGS=UNKNOWN")
    print("PRE681_APK_PATCH_OR_FPS_GAIN=NONE")


if __name__ == "__main__":
    main()
