#!/usr/bin/env python3
"""PRE121: reconstruct the PRE117 Android single-scroll patch from the verified PRE99 backup.

Read-only Google Drive access; all source work is inside the temporary GitHub runner.
Publishes only an exact patch and sanitized JSON. Never launches Kaggle or signs an APK.
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

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import SOURCE_NAME, SOURCE_SHA256, drive_client, download
from pre117_one_scroll_android_dryrun import propose
from pre118_audit_build_tree import audited_snapshot, EXPECTED_PRE117_SHA, EXPECTED_DIFF_LINES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--patch", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run id")
    report_path = Path(args.report)
    patch_path = Path(args.patch)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE121_PRE117_PATCH_REPRODUZIVEL_PRE99",
        "run_id": args.run_id,
        "phase": "START",
        "status": "NAO_VALIDADO",
        "archive_verified": False,
        "settings_source_verified": False,
        "gradle_verified": False,
        "patch_reproduced": False,
        "active_kaggle_workspace_inspected": False,
        "active_kaggle_workspace_modified": False,
        "original_kaggle_notebook_modified": False,
        "google_drive_modified": False,
        "apk_built": False,
        "signing_key_accessed": False,
        "ready_to_publish_apk": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre121_", dir="/tmp") as tmp:
            archive = Path(tmp) / "pre99.tar.gz"
            report["phase"] = "GOOGLE_DRIVE_DOWNLOAD_READ_ONLY"
            download(drive_client(), archive)
            report["phase"] = "VERIFY_FULL_ARCHIVE_SHA256"
            digest, _, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 archive changed")
            report["archive_verified"] = True

            report["phase"] = "AUDIT_ANDROID_BUILD_DEFINITIONS"
            audit = audited_snapshot(archive)
            report["gradle_verified"] = bool(audit["public_file_presence"].get("app_gradle"))
            report["app_gradle_sha256"] = audit["public_file_sha256"].get("app_gradle")
            report["app_generated_android_present_in_pre99"] = audit["build_family_counts"]["app_generated_android_folder_present"]
            report["native_generated_cpp_count"] = audit["build_family_counts"]["native_generated_cpp"]
            report["gradle_release_signing_reference"] = audit["app_gradle_safe_markers"]["release_signing_explicit"]
            report["gradle_version_code_dynamic"] = audit["app_gradle_safe_markers"]["version_code_dynamic"]

            report["phase"] = "READ_EXACT_PRE92_SOURCE"
            with tarfile.open(archive, "r:gz", errorlevel=2) as tf:
                member = tf.getmember(SOURCE_NAME)
                if not member.isfile() or member.size > 300000:
                    raise ValueError("Unexpected Settings source TAR member")
                stream = tf.extractfile(member)
                if stream is None:
                    raise ValueError("Settings source cannot be extracted")
                with stream:
                    raw = stream.read()
            if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
                raise ValueError("PRE92 source digest mismatch")
            report["settings_source_verified"] = True
            report["phase"] = "REPRODUCE_PRE117_PATCH"
            modified, diff = propose(raw.decode("utf-8"))
            candidate = modified.encode("utf-8")
            candidate_sha = hashlib.sha256(candidate).hexdigest()
            if candidate_sha != EXPECTED_PRE117_SHA or len(diff.splitlines()) != EXPECTED_DIFF_LINES:
                raise ValueError("PRE117 patch drift")
            patch_path.write_text(diff, encoding="utf-8")
            report["pre92_base_sha256"] = SOURCE_SHA256
            report["pre117_candidate_sha256"] = candidate_sha
            report["patch_sha256"] = hashlib.sha256(patch_path.read_bytes()).hexdigest()
            report["patch_lines"] = len(diff.splitlines())
            report["patch_reproduced"] = True
            report["status"] = "PRE121_PATCH_PRE117_REPRODUZIDO_SEM_APLICAR"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE121 blocked in phase", report["phase"], "reason type", type(exc).__name__)
    finally:
        report["utc"] = datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("PRE121", report["status"], "patch_verified", report["patch_reproduced"])
    return 0 if report["patch_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
