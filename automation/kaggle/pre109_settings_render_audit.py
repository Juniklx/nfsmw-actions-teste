#!/usr/bin/env python3
"""PRE109: read-only ImGui Settings window/style flow investigation from verified PRE99.

Verify full snapshot SHA-256 before reading C++ members from TAR. The script does
not extract, modify, compile, sign, or upload any game/source files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256

TARGET_SUFFIXES = (
    "/ui/overlay/settings_overlay.cpp",
    "/ui/overlay/settings_overlay.h",
    "/ui/style.h",
    "/ui/rex_app.cpp",
    "/ui/imgui_drawer.cpp",
    "/ui/imgui_drawer.h",
    "/ui/imgui_dialog.cpp",
    "/ui/imgui_dialog.h",
    "/ui/overlay/overlay.cpp",
)
SEARCH_TERMS = (
    "SettingsDialog",
    "settings_overlay_",
    "SettingsStyle",
    "StyleColors",
    "ImGuiCol_WindowBg",
    "ImGuiCol_Separator",
    "ImGui::NewFrame",
    "ImGui::Render",
    "ImGuiDialog",
    "ImGui::Begin",
    "PushStyleColor",
    "PopStyleColor",
)
MAX_MEMBER_SIZE = 850_000
MAX_MATCHED_FILES = 22
MAX_SELECTED_LINES_PER_FILE = 125
MAX_TARGET_EXCERPT_LINES = 520

def source_preview(blob: bytes, name: str, maxlines: int):
    lines = blob.decode("utf-8", errors="replace").splitlines()
    matches = []
    selected = set()
    for i, line in enumerate(lines):
        if any(term in line for term in SEARCH_TERMS):
            matches.append(i + 1)
            selected.update(range(max(0, i-2), min(len(lines), i+3)))
    # Retain source proof for relevant UI sections even when string search is sparse.
    if name.endswith("/ui/overlay/settings_overlay.cpp"):
        selected.update(range(min(229, len(lines)), min(420, len(lines))))
        selected.update(range(min(715, len(lines)), min(765, len(lines))))
    elif name.endswith("/ui/style.h"):
        selected.update(range(min(55, len(lines)), min(88, len(lines))))
    elif name.endswith("/ui/rex_app.cpp"):
        selected.update(range(min(456, len(lines)), min(483, len(lines))))
    sample = sorted(selected)
    return {
        "path": name,
        "lines_total": len(lines),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "matching_line_numbers": matches[:100],
        "matching_line_count": len(matches),
        "reported_lines": [
            {"line": i+1, "text": lines[i][:300]}
            for i in sample[:maxlines]
        ],
        "excerpt_truncated": len(sample) > maxlines,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run ID")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE109_SETTINGS_RENDER_PATH_AUDIT",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "START",
        "backup_sha256_valid": False,
        "settings_source_sha256_valid": False,
        "sources": [],
        "other_matching_files": [],
        "source_modified": False,
        "apk_compiled": False,
        "backup_extracted": False,
        "signing_key_accessed": False,
        "actual_android_execution_proven": False,
    }
    try:
        report["phase"] = "OAUTH"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre109_") as tmp:
            archive = Path(tmp) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD"
            download(drive, archive)
            report["phase"] = "VERIFY_BACKUP_SHA256"
            actual, _md5, size = sha_file(archive)
            if actual != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("Snapshot hash/size mismatch")
            report["backup_sha256_valid"] = True

            report["phase"] = "SCAN_UI_SOURCES"
            primary_found = False
            with tarfile.open(archive, "r:gz", errorlevel=2) as tf:
                for item in tf:
                    if not item.isfile() or item.size > MAX_MEMBER_SIZE:
                        continue
                    name = item.name
                    if not name.startswith("workspace/nativo/sdk/"):
                        continue
                    if not name.endswith((".cpp", ".cc", ".h", ".hpp")):
                        continue
                    if not (
                        name.endswith(TARGET_SUFFIXES)
                        or "/ui/" in name
                        or name.endswith("/rex_app.cpp")
                    ):
                        continue
                    stream = tf.extractfile(item)
                    if stream is None:
                        continue
                    with stream:
                        blob = stream.read(MAX_MEMBER_SIZE+1)
                    if len(blob) > MAX_MEMBER_SIZE:
                        continue
                    if name == SOURCE_NAME:
                        primary_found = True
                        source_hash = hashlib.sha256(blob).hexdigest()
                        if source_hash != SOURCE_SHA256:
                            raise ValueError("Settings source hash diverges from PRE92")
                        report["settings_source_sha256_valid"] = True
                    hits = sum(blob.count(t.encode("utf-8")) for t in SEARCH_TERMS)
                    is_target = name.endswith(TARGET_SUFFIXES) or name == SOURCE_NAME
                    if is_target or (hits >= 2 and len(report["sources"]) < MAX_MATCHED_FILES):
                        preview = source_preview(
                            blob, name,
                            MAX_TARGET_EXCERPT_LINES if
                            name.endswith(("/ui/overlay/settings_overlay.cpp", "/ui/rex_app.cpp"))
                            else MAX_SELECTED_LINES_PER_FILE,
                        )
                        preview["term_occurrences"] = hits
                        if is_target or len(report["sources"]) < MAX_MATCHED_FILES:
                            report["sources"].append(preview)
            if not primary_found or not report["settings_source_sha256_valid"]:
                raise ValueError("Required original settings source was not read")

        sources = report["sources"]
        main = next(x for x in sources if x["path"] == SOURCE_NAME)
        source_lines = {entry["line"]: entry["text"] for entry in main["reported_lines"]}
        preview_text = "\n".join(x["text"] for x in main["reported_lines"])
        report["static_assertions"] = {
            "mobile_branch_compile_guard_in_excerpt": any(
                "#if defined(__ANDROID__)" in x["text"]
                for x in main["reported_lines"]
            ),
            "header_begin_child_in_excerpt": "##mw_header" in preview_text,
            "header_text_in_excerpt": "NEED FOR SPEED / MOST WANTED" in preview_text,
            "window_style_push_in_excerpt": "ImGuiCol_WindowBg" in preview_text,
            "window_style_pop_in_excerpt": any(
                "PopStyleColor(2)" in v for v in source_lines.values()
            ),
            "android_separator_style_in_excerpt": "ImGuiCol_Separator" in preview_text,
            "android_label_explicit_color_in_excerpt": any(
                "LifecycleColor(" in v for v in source_lines.values()
            ),
            "mobile_save_button_in_excerpt": "SAVE SETTINGS" in preview_text,
        }
        report["status"] = "FONTE_E_CAMINHO_ESTATICO_AUDITADOS"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE109 failed at", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print("PRE109 status:", report["status"])
    return 0 if report["status"] == "FONTE_E_CAMINHO_ESTATICO_AUDITADOS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
