#!/usr/bin/env python3
"""PRE123 — audit real Android release prerequisites in SHA-verified PRE99 TAR.

Read-only Drive retrieval; only public build source is opened. No signing files,
Kaggle execution, patch, Gradle, CMake, or APK. Safely checks exact Android
and generated paths without guessing from a previous audit's counts.
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
from pre118_audit_build_tree import EXPECTED_PRE117_SHA, EXPECTED_DIFF_LINES

ANDROID = "workspace/android/"
APP = ANDROID + "app/"
GRADLE = APP + "build.gradle.kts"
GRADLE_SHA = "ef570ba95703cb54df3c0e503fec6bce11aaa0f640e907208bdfb22bd8711230"
PUBLIC = {
    "app_build_gradle": GRADLE,
    "root_build_gradle": ANDROID + "build.gradle.kts",
    "gradle_settings": ANDROID + "settings.gradle.kts",
    "gradle_wrapper": ANDROID + "gradle/wrapper/gradle-wrapper.properties",
    "gradle_wrapper_jar": ANDROID + "gradle/wrapper/gradle-wrapper.jar",
    "gradlew": ANDROID + "gradlew",
    "cmake": APP + "src/main/cpp/CMakeLists.txt",
    "main_manifest": APP + "src/main/AndroidManifest.xml",
    "local_properties": ANDROID + "local.properties",
    "native_settings": SOURCE_NAME,
}
DANGEROUS_EXTS = (".p12", ".jks", ".keystore", ".pem", ".pfx", ".key")
MAX_PUBLIC_FILE = 400_000


def get_public(tf: tarfile.TarFile, paths: dict, name: str) -> bytes:
    member = paths.get(name)
    if member is None or not member.isfile() or member.size > MAX_PUBLIC_FILE:
        raise ValueError("Required public build definition missing or oversized")
    stream = tf.extractfile(member)
    if stream is None:
        raise ValueError("Public file not readable")
    with stream:
        return stream.read()


def inspect_gradle(s: str) -> dict:
    patterns = {
        "application_id_expected": r"io\.github\.nfsmwrecomp",
        "nfsmw_permanent_signing_symbol": r"nfsmwPermanente",
        "signing_config_assignment": r"signingConfig\s*=\s*signingConfigs",
        "release_variant": r"\brelease\b",
        "version_code_dynamic": r"\bversionCode\s*=\s*(?!\d+\b)",
        "version_code_constant": r"\bversionCode\s*=\s*\d+\b",
        "generated_android_reference": r"generated-android",
        "native_cmake_reference": r"externalNativeBuild|cmake",
        "arm64_reference": r"arm64-v8a|arm64",
        "keystore_file_reference": r"storeFile|keyAlias|keyPassword|storePassword",
        "file_path_property_reference": r"Properties\(\)|findProperty|providers\.gradleProperty",
        "gradle_property_motor": r"nfsmw\.motor",
        "gradle_property_edicao": r"nfsmw\.edicion",
    }
    return {key: bool(re.search(rx, s, re.I)) for key, rx in patterns.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d+", args.run_id):
        raise ValueError("Non-numeric runner id")
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "etapa": "PRE123_AUDITORIA_REQUISITOS_BUILD_ANDROID_PRE99",
        "run_id": args.run_id,
        "status": "NAO_VERIFICADO",
        "phase": "INICIO",
        "archive_full_sha256_ok": False,
        "settings_pre92_sha256_ok": False,
        "pre117_reproduced_not_applied": False,
        "gradle_pre99_sha256_ok": False,
        "kaggle_active_session_inspected": False,
        "signing_inputs_opened": False,
        "signing_certificate_verified": False,
        "kaggle_notebook_executed": False,
        "apk_built": False,
        "external_build_modifications": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre123_") as d:
            file = Path(d) / "pre99.tar.gz"
            result["phase"] = "DOWNLOAD_PRE99"
            download(drive_client(), file)
            result["phase"] = "SHA256_PRE99"
            sha, _md5, size = sha_file(file)
            if sha != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 full SHA/size mismatch")
            result["archive_full_sha256_ok"] = True
            result["phase"] = "SCAN_MEMBERS"
            with tarfile.open(file, "r:gz", errorlevel=2) as tf:
                members = tf.getmembers()
                if len(members) != EXPECTED_ENTRIES or len({m.name for m in members}) != len(members):
                    raise ValueError("PRE99 member inventory mismatch")
                paths = {m.name:m for m in members}
                names = tuple(paths)
                result["file_presence"] = {key: name in paths for key, name in PUBLIC.items()}
                gradle = get_public(tf, paths, GRADLE)
                if hashlib.sha256(gradle).hexdigest() != GRADLE_SHA:
                    raise ValueError("PRE99 Gradle source drift")
                result["gradle_pre99_sha256_ok"] = True
                settings = get_public(tf, paths, SOURCE_NAME)
                if hashlib.sha256(settings).hexdigest() != SOURCE_SHA256:
                    raise ValueError("PRE92 Settings source drift")
                result["settings_pre92_sha256_ok"] = True
                modified, diff = propose(settings.decode("utf-8"))
                if hashlib.sha256(modified.encode("utf-8")).hexdigest() != EXPECTED_PRE117_SHA or len(diff.splitlines()) != EXPECTED_DIFF_LINES:
                    raise ValueError("PRE117 proposal mismatch")
                result["pre117_reproduced_not_applied"] = True
                result["gradle_markers"] = inspect_gradle(gradle.decode("utf-8", errors="replace"))
                result["layout"] = {
                    "android_app_generated_android_files": sum(n.startswith(APP+"generated-android/") for n in names),
                    "android_app_src_main_cpp_files": sum(n.startswith(APP+"src/main/cpp/") for n in names),
                    "android_app_src_main_java_files": sum(n.startswith(APP+"src/main/java/") for n in names),
                    "android_app_src_main_kotlin_files": sum(n.startswith(APP+"src/main/kotlin/") for n in names),
                    "native_generated_cpp": sum(n.startswith("workspace/nativo/") and "/generated" in n and n.endswith(".cpp") for n in names),
                    "codegen_rexglue_files": sum("rexglue" in n.lower() for n in names),
                    "nfsp_shaders": sum(n.startswith("workspace/") and n.endswith(".nfsp") for n in names),
                    "arm64_prebuilt_so": sum(n.endswith(".so") and "arm64-v8a" in n for n in names),
                    "android_app_build_output_files": sum(n.startswith(APP+"build/outputs/") for n in names),
                    "android_src_main_assets_files": sum(n.startswith(APP+"src/main/assets/") for n in names),
                    "android_src_main_jniLibs_arm64": sum(n.startswith(APP+"src/main/jniLibs/arm64-v8a/") for n in names),
                    "android_main_app_generated_android_exact_dir": any(n == APP+"generated-android" or n.startswith(APP+"generated-android/") for n in names),
                }
                result["archive_sensitive_filename_count"] = sum(
                    n.lower().endswith(DANGEROUS_EXTS)
                    for n in names
                )
                result["important_build_files_present"] = all(result["file_presence"][k] for k in (
                    "app_build_gradle", "gradle_settings", "gradle_wrapper",
                    "gradle_wrapper_jar", "gradlew", "cmake", "native_settings"
                ))
                result["pre99_missing_signing_material_expected"] = True
                result["signed_release_possible_from_pre99_alone"] = False
                result["version_code_needs_independent_gate"] = True
                result["recommendation"] = (
                    "A PRE99 backup is a reproducible code base for isolated patching; "
                    "a release APK requires a separately verified signing source and versionCode > 26."
                )
                result["status"] = "PRE123_PRE99_BUILD_REQUISITOS_AUDITADOS"
                result["phase"] = "COMPLETO"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        print("PRE123 blocked:", result["phase"], type(exc).__name__)
    finally:
        result["utc"] = datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print("PRE123:",result["status"])
    return 0 if result["status"] == "PRE123_PRE99_BUILD_REQUISITOS_AUDITADOS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
