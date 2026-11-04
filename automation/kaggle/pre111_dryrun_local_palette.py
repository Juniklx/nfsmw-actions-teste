#!/usr/bin/env python3
"""PRE111: combined Android-only Settings color dry-run; no files patched.

Verifies the complete PRE99 TAR SHA-256, then PRE92 Settings source SHA-256.
Reuses PRE108's labels and adds five local PushStyleColor overrides only
inside the Android mobile_layout branch; matches PopStyleColor count (25).
Does not alter the global ImGui palette or non-Android branches.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256
from pre108_dryrun_theme_labels import make_dryrun as make_pre108

ANCHOR = """    ImGui::PushStyleColor(
        ImGuiCol_TitleBgActive,
        ImVec4(0.14f, 0.14f, 0.12f, 1.0f));
  }

  if (mobile_layout) {"""

MOBILE_ADD = """    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarBg,
        ImVec4(0.11f, 0.12f, 0.13f, 0.59f));
    ImGui::PushStyleColor(
        ImGuiCol_SliderGrabActive,
        ImVec4(1.00f, 0.82f, 0.08f, 1.00f));
    ImGui::PushStyleColor(
        ImGuiCol_TextSelectedBg,
        ImVec4(0.95f, 0.73f, 0.05f, 0.28f));
    ImGui::PushStyleColor(
        ImGuiCol_SeparatorHovered,
        ImVec4(0.85f, 0.69f, 0.07f, 1.00f));
    ImGui::PushStyleColor(
        ImGuiCol_SeparatorActive,
        ImVec4(0.95f, 0.78f, 0.08f, 1.00f));
"""

POP_BEFORE = "ImGui::PopStyleColor(mobile_layout ? 20 : 11);"
POP_AFTER = "ImGui::PopStyleColor(mobile_layout ? 25 : 11);"

def propose(source: str):
    """Produce strictly bounded diff; rejects different or already-patched inputs."""
    if source.count(ANCHOR) != 1:
        raise ValueError("PRE92 Android style anchor missing or duplicated")
    if source.count(POP_BEFORE) != 1:
        raise ValueError("PRE92 style stack count anchor missing or duplicated")
    if any(f"ImGuiCol_{name}" in source for name in (
        "ScrollbarBg", "SliderGrabActive", "TextSelectedBg",
        "SeparatorHovered", "SeparatorActive",
    )):
        # These names may exist in source only if a new override is already present.
        raise ValueError("Unexpected pre-existing target override in Settings source")
    stage1, _pre108_diff = make_pre108(source)
    if stage1.count(ANCHOR) != 1:
        raise ValueError("Pre108 changed the style insertion anchor")
    replacement = ANCHOR.replace("  }\n\n  if (mobile_layout) {",
                                 MOBILE_ADD + "  }\n\n  if (mobile_layout) {")
    if replacement.count("ImGui::PushStyleColor") != 6:
        raise ValueError("Wrong number of proposed color overrides")
    stage2 = stage1.replace(ANCHOR, replacement, 1)
    stage3 = stage2.replace(POP_BEFORE, POP_AFTER, 1)
    if stage3.count("ImGui::PushStyleColor") - source.count("ImGui::PushStyleColor") != 5:
        raise ValueError("Unexpected PushStyleColor count delta")
    if stage3.count("ImGui::PopStyleColor") != source.count("ImGui::PopStyleColor"):
        raise ValueError("PopStyleColor call structure changed")
    if stage3.count(POP_AFTER) != 1 or stage3.count("mobile_layout ? 20 : 11") != 0:
        raise ValueError("Unbalanced mobile style stack")
    if stage3.count("ImGui::PushStyleVar") != source.count("ImGui::PushStyleVar"):
        raise ValueError("StyleVar modifications are not allowed")
    if stage3.count("ImGui::PopStyleVar") != source.count("ImGui::PopStyleVar"):
        raise ValueError("StyleVar modifications are not allowed")
    diff = "".join(difflib.unified_diff(
        source.splitlines(keepends=True),
        stage3.splitlines(keepends=True),
        fromfile="settings_overlay.cpp PRE92 (SHA256 verified)",
        tofile="settings_overlay.cpp PRE111 PROPOSTA NAO APLICADA",
        n=4,
    ))
    if not 50 <= len(diff.splitlines()) <= 115:
        raise ValueError("Unexpected PRE111 diff size")
    return stage3, diff

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("GitHub run ID must be numeric")
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE111_DRYRUN_PALETA_ANDROID_COMPLEMENTAR",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "backup_full_sha256_verified": False,
        "source_pre92_sha256_verified": False,
        "patch_applied": False,
        "game_workspace_restored": False,
        "global_imgui_theme_modified": False,
        "desktop_branch_modified": False,
        "apk_built": False,
        "signing_key_accessed": False,
        "source_sha256_before": None,
        "proposed_source_sha256_after": None,
    }
    try:
        report["phase"] = "GOOGLE_OAUTH"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre111_") as tmp:
            backup = Path(tmp) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD_PRE99"
            download(drive, backup)
            report["phase"] = "VERIFY_TAR_SHA256"
            tar_sha256, _md5, size = sha_file(backup)
            if tar_sha256 != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 TAR hash/size mismatch")
            report["backup_full_sha256_verified"] = True
            report["phase"] = "READ_PRE92_SETTINGS_SOURCE"
            with tarfile.open(backup, "r:gz", errorlevel=2) as tf:
                member = tf.getmember(SOURCE_NAME)
                if not member.isfile() or member.size > 2_000_000:
                    raise ValueError("Settings source member has unexpected metadata")
                stream = tf.extractfile(member)
                if stream is None:
                    raise ValueError("Settings source unreadable")
                with stream:
                    blob = stream.read()
            original_sha = hashlib.sha256(blob).hexdigest()
            if original_sha != SOURCE_SHA256:
                raise ValueError("PRE92 source SHA256 mismatch")
            report["source_pre92_sha256_verified"] = True
            report["source_sha256_before"] = original_sha
            report["phase"] = "GENERATE_DIFF_ONLY_IN_MEMORY"
            updated, diff = propose(blob.decode("utf-8"))
            report["proposed_source_sha256_after"] = hashlib.sha256(updated.encode("utf-8")).hexdigest()
            report["unified_diff"] = diff
            report["diff_lines"] = len(diff.splitlines())
            report["new_local_imgui_overrides"] = [
                "ScrollbarBg", "SliderGrabActive", "TextSelectedBg",
                "SeparatorHovered", "SeparatorActive",
            ]
            report["new_local_push_count"] = 5
            report["mobile_pop_count_before"] = 20
            report["mobile_pop_count_proposed"] = 25
            report["desktop_pop_count_unchanged"] = 11
            report["lifecycle_colors"] = {
                "live": "white, RGBA (0.93, 0.93, 0.87, 1.0)",
                "restart": "gold, RGBA (1.0, 0.82, 0.08, 1.0)",
                "init_only": "coral, RGBA (1.0, 0.56, 0.38, 1.0)",
            }
            report["limitations"] = (
                "Static dry-run only; does not prove C++ compilation or actual "
                "menu rendering. No fix for an absent header is claimed."
            )
        report["status"] = "PRE111_DIFF_VALIDADO_NAO_APLICADO"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE111 not validated, phase:", report["phase"],
              "type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("PRE111:", report["status"])
    return 0 if report["status"] == "PRE111_DIFF_VALIDADO_NAO_APLICADO" else 1

if __name__ == "__main__":
    raise SystemExit(main())
