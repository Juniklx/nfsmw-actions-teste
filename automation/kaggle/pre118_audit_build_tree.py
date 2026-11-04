#!/usr/bin/env python3
"""PRE118: SHA256-gated read-only audit of actual PRE99 Android build tree.

- Never fetches private signing material or credential files.
- Never modifies game source, APKs, Drive, or Kaggle workspaces.
- Confirms exact PRE117 proposal from verified PRE92 C++ bytes.
- Summarizes build file presence and public build settings only (not source text).
- Distinguishes PRE99 archive from unknown active Kaggle runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, EXPECTED_ENTRIES, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256
from pre117_one_scroll_android_dryrun import propose

EXPECTED_PRE117_SHA = "8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af"
EXPECTED_DIFF_LINES = 30

# Whitelist only public build definitions and verified settings source.
PUBLIC_FILES = {
    "app_gradle": "workspace/android/app/build.gradle.kts",
    "gradle_wrapper": "workspace/android/gradle/wrapper/gradle-wrapper.properties",
    "android_settings": "workspace/android/settings.gradle.kts",
    "cmake_android": "workspace/android/app/src/main/cpp/CMakeLists.txt",
    "settings_cpp": SOURCE_NAME,
}
SOURCE_MAX_BYTES = 300_000
BUILD_MAX_BYTES = 350_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_public_file_data(tar: tarfile.TarFile, member: tarfile.TarInfo,
                          *, max_bytes: int) -> bytes:
    if not member.isfile() or member.size < 1 or member.size > max_bytes:
        raise ValueError("Unexpected public source member metadata")
    handle = tar.extractfile(member)
    if handle is None:
        raise ValueError("Public member not extractable")
    with handle:
        return handle.read()


def scan_gradle(src: str) -> dict:
    # Never include source text lines (which may contain paths or values).
    return {
        "application_id_expected_literal_present": "io.github.nfsmwrecomp" in src,
        "version_code_numeric_constants": [
            int(x) for x in re.findall(r"(?m)^\s*versionCode\s*=\s*(\d+)\s*$", src)[:5]
        ],
        "version_code_dynamic": bool(re.search(r"\bversionCode\s*=\s*(?!\d+\b)", src)),
        "release_signing_explicit": bool(re.search(
            r"signingConfig\s*=\s*signingConfigs", src
        )),
        "permanent_signing_symbol_reference": "nfsmwPermanente" in src,
        "debug_signing_symbol_reference": "getByName(\"debug\")" in src,
        "min_sdk_constants": [
            int(x) for x in re.findall(r"(?m)^\s*minSdk\s*=\s*(\d+)", src)[:3]
        ],
        "compile_sdk_constants": [
            int(x) for x in re.findall(r"(?m)^\s*compileSdk\s*=\s*(\d+)", src)[:3]
        ],
        "gradle_properties_reference": "Properties()" in src,
        "generated_code_location_reference": bool(re.search(r"generado|generated-android", src)),
        "native_motor_option_reference": "nfsmw.motor" in src,
        "edition_option_reference": "nfsmw.edicion" in src,
        "gradle_signing_validated_for_release": False,  # requires an actual built APK/apksigner
    }


def audited_snapshot(archive: Path) -> dict:
    with tarfile.open(archive, mode="r:gz", errorlevel=2) as tf:
        items = tf.getmembers()
        if len(items) != EXPECTED_ENTRIES:
            raise ValueError("PRE99 TAR member count drift")
        names = {m.name for m in items}
        if len(names) != len(items):
            raise ValueError("Unexpected duplicate path in PRE99")
        layout = {}
        for key, name in PUBLIC_FILES.items():
            layout[key] = name in names

        raw = {}
        for key, name in PUBLIC_FILES.items():
            if name in names:
                raw[key] = safe_public_file_data(
                    tf, tf.getmember(name),
                    max_bytes=SOURCE_MAX_BYTES if key == "settings_cpp" else BUILD_MAX_BYTES
                )

        if "settings_cpp" not in raw or sha(raw["settings_cpp"]) != SOURCE_SHA256:
            raise ValueError("PRE92 settings source SHA mismatch")
        if not layout["app_gradle"]:
            raise ValueError("Android app Gradle file absent in PRE99")

        original = raw["settings_cpp"].decode("utf-8")
        modified, diff = propose(original)
        proposed_sha = sha(modified.encode("utf-8"))
        if proposed_sha != EXPECTED_PRE117_SHA or len(diff.splitlines()) != EXPECTED_DIFF_LINES:
            raise ValueError("PRE117 diff changed compared with verified dry-run")

        # No plaintext content is copied to output, only structural booleans/counts.
        families = {
            "gradle_root_files": sum(p.startswith("workspace/android/") and p.endswith(".gradle.kts") for p in names),
            "native_generated_cpp": sum(p.startswith("workspace/nativo/") and "/generated" in p and p.endswith(".cpp") for p in names),
            "app_generated_cpp": sum(p.startswith("workspace/app/") and ("/generated" in p or "/gerado" in p) and p.endswith(".cpp") for p in names),
            "native_shader_packs_nfsp": sum(p.startswith("workspace/") and p.endswith(".nfsp") for p in names),
            "native_arm64_libraries": sum(p.startswith("workspace/") and p.endswith(".so") and "arm64-v8a" in p for p in names),
            "android_gradle_wrapper_jar_present": any(p.endswith("/gradle/wrapper/gradle-wrapper.jar") for p in names),
            "android_gradlew_present": "workspace/android/gradlew" in names,
            "android_local_properties_present": "workspace/android/local.properties" in names,
            "app_generated_android_folder_present": any(p.startswith("workspace/app/generated-android/") for p in names),
            "native_codegen_rexglue_folder_present": any("rexglue" in p.lower() for p in names),
        }
        wrapper = raw.get("gradle_wrapper", b"").decode("utf-8", errors="replace")
        gradle_version = re.search(r"gradle-(\d+(?:\.\d+){1,2})-(?:all|bin)\.zip", wrapper)
        public_hashes = {k: sha(v) for k, v in raw.items()}
        return {
            "member_count": len(items),
            "public_file_presence": layout,
            "public_file_sha256": public_hashes,
            "source_pre92_sha256_matches_expected": True,
            "pre117_proposal_sha256_matches_expected": True,
            "source_pre92_sha256": SOURCE_SHA256,
            "proposed_pre117_sha256": proposed_sha,
            "pre117_diff_lines": len(diff.splitlines()),
            "build_family_counts": families,
            "gradle_version_from_public_wrapper": gradle_version.group(1) if gradle_version else None,
            "app_gradle_safe_markers": scan_gradle(
                raw["app_gradle"].decode("utf-8", errors="replace")
            ),
            "private_signing_key_opened": False,
            "credential_file_opened": False,
            "private_material_does_not_reside_in_pre99_manifest": True,
            "active_kaggle_workspace_state_confirmed": False,
            "can_release_sign_now": False,
        }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Numeric GitHub run ID expected")
    dst = Path(args.report)
    dst.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE118_AUDIT_PRE99_BUILD_TREE_AND_PRE117",
        "run_id": args.run_id,
        "phase": "INITIAL",
        "status": "NAO_VALIDADO",
        "archive_full_sha256_verified": False,
        "archive_matches_expected_size": False,
        "original_workspace_modified": False,
        "kaggle_main_notebook_modified": False,
        "google_drive_modified": False,
        "apk_built": False,
        "linker_invoked": False,
        "signing_key_accessed": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre118_", dir="/tmp") as td:
            report["phase"] = "GOOGLE_DRIVE_READ_ONLY_AUTH"
            client = drive_client()
            archive = Path(td) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD_BACKUP_READ_ONLY"
            download(client, archive)
            digest, _md5, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 full TAR hash or size mismatch")
            report["archive_full_sha256_verified"] = True
            report["archive_matches_expected_size"] = True
            report["phase"] = "AUDIT_SOURCE_AND_BUILD_TOPOLOGY"
            report["audit"] = audited_snapshot(archive)
            report["status"] = "PRE118_PRE99_BUILD_TREE_AUDITADO_SEM_APLICAR"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE118 could not finish phase:", report["phase"],
              "type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        dst.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("PRE118:", report["status"])
    return 0 if report["status"] == "PRE118_PRE99_BUILD_TREE_AUDITADO_SEM_APLICAR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
