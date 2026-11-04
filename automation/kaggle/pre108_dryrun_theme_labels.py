#!/usr/bin/env python3
"""PRE108: dry-run-only Android lifecycle-label palette patch, against verified PRE99."""
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

FUNCTION_ANCHOR = "void SettingsDialog::OnDraw(ImGuiIO& /*io*/) {"
OLD_LABEL = """          LifecycleColor(
              entry.lifecycle,
              imgui_drawer()->style().settings),"""
NEW_LABEL = """          mobile_layout
              ? MobileLifecycleColor(entry.lifecycle)
              : LifecycleColor(entry.lifecycle,
                               imgui_drawer()->style().settings),"""
HELPER = """// NFSMW PRE108 (proposta, somente dry-run): cores Android sem verde.
static ImVec4 MobileLifecycleColor(rex::cvar::Lifecycle lc) {
  switch (lc) {
    case rex::cvar::Lifecycle::kHotReload:
      return ImVec4(0.93f, 0.93f, 0.87f, 1.0f);  // live: branco suave
    case rex::cvar::Lifecycle::kRequiresRestart:
      return ImVec4(1.00f, 0.82f, 0.08f, 1.0f);  // restart: ouro
    case rex::cvar::Lifecycle::kInitOnly:
      return ImVec4(1.00f, 0.56f, 0.38f, 1.0f);  // init: coral
  }
  return ImVec4(0.93f, 0.93f, 0.87f, 1.0f);
}

"""

def make_dryrun(source):
    for anchor in (FUNCTION_ANCHOR, OLD_LABEL):
        if source.count(anchor) != 1:
            raise ValueError("Expected unique source anchor not found")
    if "MobileLifecycleColor(" in source:
        raise ValueError("Proposed change appears already present")
    modified = source.replace(FUNCTION_ANCHOR, HELPER + FUNCTION_ANCHOR, 1)
    modified = modified.replace(OLD_LABEL, NEW_LABEL, 1)
    if modified == source:
        raise ValueError("No source delta generated")
    diff = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile="settings_overlay.cpp (PRE92 source verified)",
        tofile="settings_overlay.cpp (PRE108 proposal NOT APPLIED)",
        n=4,
    ))
    if len(diff) > 70:
        raise ValueError("Unexpectedly large patch proposal")
    if modified.count("ImGui::PushStyleColor") != source.count("ImGui::PushStyleColor"):
        raise ValueError("Style stack modifications are not allowed")
    if modified.count("ImGui::PopStyleColor") != source.count("ImGui::PopStyleColor"):
        raise ValueError("Style stack modifications are not allowed")
    return modified, "".join(diff)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid run ID")
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE108_DRYRUN_PALETA_ANDROID",
        "run_id": args.run_id,
        "status": "NAO_VERIFICADO",
        "phase": "START",
        "changes_applied_to_project": False,
        "changes_applied_to_backup": False,
        "apk_compiled": False,
        "new_release": False,
        "permanent_key_accessed": False,
        "touches_desktop_logic": False,
        "source_sha256_before": None,
        "source_sha256_proposed_after": None,
    }
    try:
        report["phase"] = "AUTH_GOOGLE"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre108_") as temp:
            archive = Path(temp) / "pre99.tar.gz"
            report["phase"] = "DOWNLOAD"
            download(drive, archive)
            report["phase"] = "VERIFY_BACKUP"
            digest, _, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 digest mismatch")
            with tarfile.open(archive, "r:gz") as tar:
                member = tar.getmember(SOURCE_NAME)
                if not member.isfile() or member.size > 2000000:
                    raise ValueError("Unexpected C++ source")
                stream = tar.extractfile(member)
                if stream is None:
                    raise ValueError("Source unreadable")
                source_bytes = stream.read()
            source_hash = hashlib.sha256(source_bytes).hexdigest()
            if source_hash != SOURCE_SHA256:
                raise ValueError("Source differs from PRE92")
            report["source_sha256_before"] = source_hash
            report["phase"] = "GENERATE_DIFF_IN_MEMORY"
            source = source_bytes.decode("utf-8")
            proposed, diff = make_dryrun(source)
            report["source_sha256_proposed_after"] = hashlib.sha256(
                proposed.encode("utf-8")
            ).hexdigest()
            report["unified_diff"] = diff
            report["patch_line_count"] = len(diff.splitlines())
            report["android_palette"] = {
                "live": "off-white (0.93, 0.93, 0.87)",
                "restart": "Most Wanted gold (1.00, 0.82, 0.08)",
                "init_only": "warm coral (1.00, 0.56, 0.38)",
            }
            report["notes"] = (
                "Only CVAR label colors are proposed, not the missing header, "
                "window borders or a general UI redesign. Not C++ compiled."
            )
        report["status"] = "DRYRUN_GERADO_SEM_APLICAR"
        report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE108 failed at", report["phase"], type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print("PRE108:", report["status"])
    return 0 if report["status"] == "DRYRUN_GERADO_SEM_APLICAR" else 1

if __name__ == "__main__":
    raise SystemExit(main())
