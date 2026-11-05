#!/usr/bin/env python3
"""PRE188: read-only audit of runtime edition selection and C3 diagnostic reachability.
No source writes, builds, signing, or thermal changes. Do not print game source bodies.
"""
from __future__ import annotations

import hashlib
import json
import re
import tarfile
import tempfile
import zipfile
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre188-edition-audit")
APK_ID = "1New_ieqealhy_FrXsKH1cgtV57otu4od"
APK_BYTES = 47102145
APK_SHA = "e3b5699e017cb6c8b21baebfa00ea4bb33c731c1f63fff39ee01ef7192a09a13"
C3_SOURCES = {
    "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp":
        "046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2",
    "workspace/nativo/app_usa/src/nfsmw_nativo_dibujos.cpp":
        "92e0a15836217a535c6f81e2461381616f46c331c83201cabd14a71c2d8c2342",
}
TOKENS = (
    "libmain_usa", "libmain.so", "nfsmw.edicion", "ediciones.json",
    "edicion.json", "loadlibrary", "dlopen", "pal_es",
    "load_game_module", "game_module", "libmain_hook",
)
SUFFIXES = {".cpp", ".cc", ".c", ".h", ".hpp", ".kt", ".java", ".json",
            ".kts", ".cmake", ".txt", ".xml", ".toml", ".gradle"}
EXTRA_NAMES = {"CMakeLists.txt", "gradlew", "settings.gradle.kts"}
SENSITIVE = ("password", "secret", "refresh_token", "access_token", "private_key")

def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def download_id(drive, file_id: str, dest: Path) -> None:
    with dest.open("wb") as f:
        dl = MediaIoBaseDownload(
            f, drive.files().get_media(fileId=file_id, supportsAllDrives=True),
            chunksize=8 * 1024 * 1024,
        )
        done = False
        while not done:
            _, done = dl.next_chunk(num_retries=4)

def inspect_apk(path: Path) -> dict:
    if path.stat().st_size != APK_BYTES or sha(path.read_bytes()) != APK_SHA:
        raise ValueError("PRE188: V35 APK bytes/SHA mismatch, refusing audit")
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("PRE188: corrupt APK archive")
        entries = set(z.namelist())
        libs = {}
        for name in ("libmain.so", "libmain_usa.so", "libmain_hook.so", "librexruntime.so"):
            rel = "lib/arm64-v8a/" + name
            if rel not in entries:
                raise ValueError("PRE188: expected runtime library absent: " + name)
            data = z.read(rel)
            libs[name] = {
                "bytes": len(data),
                "sha256": sha(data),
                "contains_C3_original_error": b"indice de textura en vuelo incoherente" in data,
                "has_ASCII_libmain_usa_so": b"libmain_usa.so" in data,
                "has_ASCII_libmain_so": b"libmain.so" in data,
            }
        edition_assets = []
        for name in sorted(entries):
            low = name.lower()
            if ("edicion" in low or "edition" in low) and name.startswith("assets/"):
                info = {"path": name, "bytes": z.getinfo(name).file_size}
                if name.endswith(".json") and info["bytes"] < 8192:
                    try:
                        val = json.loads(z.read(name).decode("utf-8"))
                        info["json_kind"] = type(val).__name__
                        if isinstance(val, list):
                            info["edition_ids"] = [str(x.get("id", ""))[:40]
                                                   for x in val[:10] if isinstance(x, dict)]
                        elif isinstance(val, dict):
                            info["edition_id"] = str(val.get("id", ""))[:40]
                    except (ValueError, UnicodeError):
                        info["json_unreadable"] = True
                edition_assets.append(info)
        return {"apk_sha256_valid": True, "apk_bytes": APK_BYTES,
                "libraries": libs, "edition_assets": edition_assets[:25],
                "runtime_edition_selection_proven": False}

def inspect_pre99(tar_path: Path) -> dict:
    scanned = 0
    hits = []
    source_hashes = {}
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar:
            name = member.name.lstrip("./")
            if not member.isfile():
                continue
            if name in C3_SOURCES:
                f = tar.extractfile(member)
                if f is None:
                    raise ValueError("PRE188: missing C3 source bytes")
                blob = f.read()
                source_hashes[name] = sha(blob)
                if source_hashes[name] != C3_SOURCES[name]:
                    raise ValueError("PRE188: C3 PRE99 source differs: " + name)
            if not (name.startswith("workspace/android/") or
                    name.startswith("workspace/nativo/sdk/") or
                    name.startswith("workspace/nativo/app/") or
                    name.startswith("workspace/nativo/app_usa/")):
                continue
            p = Path(name)
            if p.suffix.lower() not in SUFFIXES and p.name not in EXTRA_NAMES:
                continue
            if member.size > 2_000_000:
                continue
            if any(seg in name.lower() for seg in ("/build/", "/.git/", "/.gradle/",
                                                   "/outputs/", "/node_modules/")):
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            blob = f.read()
            scanned += 1
            lines = blob.decode("utf-8", "replace").splitlines()
            matches = []
            for i, line in enumerate(lines):
                lower = line.lower()
                if any(token in lower for token in TOKENS) and not any(s in lower for s in SENSITIVE):
                    matches.append({"line": i + 1, "text": line.strip()[:250]})
                if len(matches) >= 12:
                    break
            if matches:
                hits.append({"path": name, "sha256": sha(blob),
                             "match_lines_capped": matches})
            if len(hits) >= 120:
                raise ValueError("PRE188: too many matching source files; refine audit")
    if set(source_hashes) != set(C3_SOURCES):
        raise ValueError("PRE188: incomplete C3 source coverage")
    return {"pre99_sha256_valid": True, "source_files_scanned": scanned,
            "matching_files": hits, "c3_source_hashes": source_hashes}

def inspect_builder() -> dict:
    path = Path("automation/kaggle/pre180_build_signed_v35_sdl_wait_fix.py")
    b = path.read_bytes()
    content = b.decode("utf-8")
    required = ["-Pnfsmw.edicion=pal_es", 'root/"nativo/app_usa',
                'v30["lib/arm64-v8a/libmain_usa.so"]']
    # The precise staging syntax can be expressed without a v30[...] lookup.
    checks = {
        "sets_pal_es_gradle_property": "-Pnfsmw.edicion=pal_es" in content,
        "stages_usa_library_from_old_v30": (
            'v30["lib/arm64-v8a/libmain_usa.so"]' in content
            and 'bundle/"jniLibs/arm64-v8a/libmain_usa.so"' in content
        ),
        "stage_precedes_gradle": content.index("STAGE_VERIFIED_USA_FROM_V30")
            < content.index("ANDROID_SDK_CONFIGURATION")
    }
    if not all(checks.values()):
        raise ValueError("PRE188: builder assumptions changed")
    return {"sha256": sha(b), "checks": checks,
            "runtime_selection_determined_by_builder": False}

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "stage": "PRE188_RUNTIME_EDITION_C3_REACHABILITY_READONLY",
        "read_only": True, "apk_built": False, "patch_applied": False,
        "release_key_accessed": False, "runtime_edition_proven": False,
        "note": "Static code/packaging evidence cannot prove which edition was active on device.",
    }
    with tempfile.TemporaryDirectory(prefix="pre188_audit_") as tmp:
        tmp = Path(tmp)
        drive = drive_client()
        tar_path = tmp / "pre99.tar.gz"
        download(drive, tar_path)
        digest, _, length = sha_file(tar_path)
        if digest != EXPECTED_SHA256 or length != EXPECTED_BYTES:
            raise ValueError("PRE188: PRE99 archive integrity failure")
        report["pre99"] = inspect_pre99(tar_path)
        apk_path = tmp / "v35.apk"
        download_id(drive, APK_ID, apk_path)
        report["v35_apk"] = inspect_apk(apk_path)
        report["v35_builder"] = inspect_builder()
    result = OUT / "PRE188_RUNTIME_EDITION_C3_READONLY.json"
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PRE188_READONLY_SUCCESS")
    print("PRE188_SOURCE_FILES_SCANNED", report["pre99"]["source_files_scanned"])
    print("PRE188_MATCHING_SOURCE_FILES", len(report["pre99"]["matching_files"]))
    print("PRE188_APK_SHA256", APK_SHA)
    print("PRE188_RUNTIME_EDITION_PROVEN", report["runtime_edition_proven"])
    print("PRE188_REPORT", result)

if __name__ == "__main__":
    main()
