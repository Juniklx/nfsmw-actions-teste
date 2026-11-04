#!/usr/bin/env python3
"""PRE110: exact ImGui global-vs-local palette coverage, read-only verified PRE99.

Only reads three C++ members from verified TAR, computes static color coverage.
A local PushStyleColor declared in source is not proof that a given widget used it.
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
from pre105_read_settings_source import drive_client, download

SOURCES = {
    "workspace/nativo/sdk/src/ui/imgui_drawer.cpp":
        "1a62d13e81af3aac4837af06e90281b64bd282c78e6e5ce079d6ca930e8a5c24",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp":
        "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034",
    "workspace/nativo/sdk/include/rex/ui/style.h":
        "2731e68defeb544153f57ae74f4f27080fd26f1e45c627284d12c3733ad1ea91",
}

GLOBAL_RGB = re.compile(
    r"style\s*\.\s*Colors\s*\[\s*ImGuiCol_(\w+)\s*\]\s*=\s*"
    r"ImVec4\s*\(\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*,"
    r"\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*\)",
    re.M,
)
LOCAL_PUSH = re.compile(
    r"ImGui::PushStyleColor\s*\(\s*ImGuiCol_(\w+)", re.M,
)
LIFECYCLE_RGB = re.compile(
    r"ImVec4\s+(\w+)\s*\{\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*,"
    r"\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*\}",
    re.M,
)

def line_no(source, offset):
    return source.count("\n", 0, offset) + 1

def excerpts(source, name, begin, end):
    lines = source.splitlines()
    return {
        "source": name,
        "excerpt_start": begin,
        "excerpt_end": min(end, len(lines)),
        "lines": [
            {"line": i+1, "text": lines[i][:330]}
            for i in range(begin - 1, min(end, len(lines)))
        ],
    }

def inspect(source_map):
    drawer_name = "workspace/nativo/sdk/src/ui/imgui_drawer.cpp"
    overlay_name = "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp"
    settings_name = "workspace/nativo/sdk/include/rex/ui/style.h"
    drawer = source_map[drawer_name]
    overlay = source_map[overlay_name]
    settings = source_map[settings_name]

    globals = {}
    for m in GLOBAL_RGB.finditer(drawer):
        key = m.group(1)
        value = [float(m.group(i)) for i in (2,3,4,5)]
        globals[key] = {"rgba": value, "line": line_no(drawer, m.start())}
    if len(globals) < 15:
        raise ValueError("Global ImGui palette not properly parsed")
    declared = {}
    for m in LOCAL_PUSH.finditer(overlay):
        declared.setdefault(m.group(1), []).append(line_no(overlay, m.start()))
    if len(declared) < 12:
        raise ValueError("Settings local PushStyleColor entries not properly parsed")

    # Green vs red & blue. Color significance is conditional on alpha and use.
    green = {}
    for key, val in globals.items():
        r, g, b, a = val["rgba"]
        if g >= 0.18 and g > r * 1.28 and g > b * 1.28 and a > 0.01:
            green[key] = {
                **val,
                "settings_local_override_declared": key in declared,
                "override_lines": declared.get(key, []),
                "might_be_inherited_by_settings": key not in declared,
            }
    lifecycle = {}
    for m in LIFECYCLE_RGB.finditer(settings):
        if m.group(1).startswith("lifecycle_") or m.group(1) == "warning":
            lifecycle[m.group(1)] = {
                "rgba": [float(m.group(i)) for i in (2,3,4,5)],
                "line": line_no(settings, m.start()),
            }

    return {
        "global_imgui_colors_parsed": len(globals),
        "settings_local_push_names": declared,
        "global_green_tinted_colors": green,
        "green_colors_with_no_settings_local_push": sorted(
            k for k,v in green.items() if v["might_be_inherited_by_settings"]
        ),
        "settings_lifecycle_palette": lifecycle,
        "global_style_function_excerpt": excerpts(drawer, drawer_name, 35, 135),
        "settings_window_and_header_excerpt": excerpts(overlay, overlay_name, 245, 365),
        "lifecycle_definition_excerpt": excerpts(settings, settings_name, 65, 84),
        "notes": [
            "Static analysis; does not prove these UI colors were visible on the device.",
            "A local push appearing in source may apply only to part of the render flow.",
            "Do not modify global palette without analyzing other overlays.",
            "This report never applies a patch or compiles an APK.",
        ],
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"\d+", args.run_id):
        raise ValueError("Invalid GitHub run ID")
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE110_GLOBAL_SETTINGS_THEME_COVERAGE",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "backup_sha256_verified": False,
        "source_hashes_verified": False,
        "workspace_restored": False,
        "source_modified": False,
        "apk_compiled": False,
        "signing_key_accessed": False,
    }
    try:
        report["phase"] = "GOOGLE_AUTH"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre110_") as tmp:
            archive = Path(tmp) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD"
            download(drive, archive)
            report["phase"] = "VERIFY_TAR"
            digest, _md5, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("Backup integrity mismatch")
            report["backup_sha256_verified"] = True
            report["phase"] = "READ_UI_MEMBERS"
            found = {}
            with tarfile.open(archive, "r:gz", errorlevel=2) as tf:
                for entry in tf:
                    if entry.name not in SOURCES:
                        continue
                    if not entry.isfile() or entry.size > 1_000_000:
                        raise ValueError("Unexpected UI source metadata")
                    stream = tf.extractfile(entry)
                    if stream is None:
                        raise ValueError("Unable to read UI member")
                    with stream:
                        data = stream.read()
                    if hashlib.sha256(data).hexdigest() != SOURCES[entry.name]:
                        raise ValueError("UI source does not match PRE109")
                    if entry.name in found:
                        raise ValueError("Duplicate UI source")
                    found[entry.name] = data.decode("utf-8")
            if set(found) != set(SOURCES):
                raise ValueError("One or more required UI sources not found")
            report["source_hashes_verified"] = True
            report["phase"] = "COMPARE_COLOR_COVERAGE"
            report["audit"] = inspect(found)
        report["status"] = "COBERTURA_DE_CORES_ANALISADA"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE110 failed at", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print("PRE110 status:", report["status"])
    return 0 if report["status"] == "COBERTURA_DE_CORES_ANALISADA" else 1

if __name__ == "__main__":
    raise SystemExit(main())
