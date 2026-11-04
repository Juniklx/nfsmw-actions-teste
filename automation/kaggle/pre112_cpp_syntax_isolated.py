#!/usr/bin/env python3
"""PRE112: isolated compile/syntax feasibility of exact PRE111, no APK/signing.

Downloads and hashes full PRE99, safely extracts it into ephemeral GitHub /tmp,
verifies original source hash, applies PRE111 only to ephemeral copy, then runs
the *same* host C++ syntax compiler on both baseline and proposal. Includes
a separately labeled C++ fragment check for the new helper and expression.
Host C++ success is not an Android release build or S24 FE runtime validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256
from pre107_restore_isolated import restore
from pre111_dryrun_local_palette import propose

EXPECTED_PRE111_SHA256 = "19102b563eb4cdd6c81d4a6bfa5bbc8cadfbb1e030247f535633cbc11524e069"
EXPECTED_DIFF_LINES = 75
MAX_INCLUDES = 70


def compile_syntax(compiler: str, cpp_path: Path, includes: list[Path],
                   *, timeout: int = 120) -> dict:
    argv = [
        compiler, "-std=c++20", "-fsyntax-only",
        "-Wno-unused-function", "-Wno-unused-variable",
        *(x for include in includes for x in ("-I", str(include))),
        str(cpp_path),
    ]
    try:
        p = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=timeout, check=False,
        )
        # Avoid leaking file text or irrelevant path data in status.
        output = p.stdout.replace(str(cpp_path), "<SOURCE>")
        for root in includes:
            output = output.replace(str(root), "<INCLUDE_ROOT>")
        msg = "\n".join(output.splitlines()[:14])[:1400]
        return {
            "attempted": True, "exit_code": p.returncode,
            "passed": p.returncode == 0,
            "diagnostic_excerpt": msg,
            "missing_include": bool(re.search(r"(file not found|No such file or directory)", msg)),
        }
    except subprocess.TimeoutExpired:
        return {"attempted": True, "passed": False, "error_type": "TimeoutExpired"}


def get_candidate_includes(src_root: Path) -> list[Path]:
    native = src_root / "workspace" / "nativo"
    known = [
        native / "sdk" / "include",
        native / "sdk" / "src",
        native / "sdk",
        native / "third_party",
        native / "third_party" / "imgui",
        native / "third_party" / "imgui" / "backends",
        native / "third_party" / "fmt" / "include",
        native / "sdk" / "third_party",
        native / "sdk" / "third_party" / "imgui",
    ]
    paths = [p for p in known if p.is_dir()]
    for basename in ("imgui.h", "fmt", "spdlog", "SDL3", "absl"):
        for match in native.rglob(basename):
            if not (match.is_file() or match.is_dir()):
                continue
            parent = match.parent
            if parent not in paths and parent.is_relative_to(native):
                paths.append(parent)
            if len(paths) >= MAX_INCLUDES:
                break
    return paths[:MAX_INCLUDES]


def fragment_for_compile(patched: str) -> str:
    start = patched.index("static ImVec4 MobileLifecycleColor(")
    end = patched.index("\n}\n", start) + len("\n}\n")
    helper = patched[start:end]
    marker = "          mobile_layout\n              ? MobileLifecycleColor(entry.lifecycle)"
    expr_start = patched.index(marker)
    expr_end = patched.index(",\n          \"%s\"", expr_start)
    expression = patched[expr_start:expr_end].strip()
    if not (helper.count("case rex::cvar::Lifecycle::") == 3
            and "imgui_drawer()->style().settings" in expression
            and "MobileLifecycleColor(entry.lifecycle)" in expression):
        raise ValueError("Unexpected PRE111 C++ fragment structure")
    prefix = """// Exact PRE111 helper and conditional color expression, with type stubs.
namespace rex { namespace cvar {
enum class Lifecycle { kHotReload, kRequiresRestart, kInitOnly };
}}
struct ImVec4 {
  float x, y, z, w;
  ImVec4(float a, float b, float c, float d) : x(a), y(b), z(c), w(d) {}
};
struct SettingsStyle {};
struct Style { SettingsStyle settings; };
struct Drawer { Style s; const Style& style() const { return s; } };
static Drawer* imgui_drawer() { static Drawer d; return &d; }
static ImVec4 LifecycleColor(rex::cvar::Lifecycle, const SettingsStyle&) {
  return ImVec4(1.f, 1.f, 1.f, 1.f);
}
struct Entry { rex::cvar::Lifecycle lifecycle; };
"""
    return (prefix + helper + "\n"
            + "ImVec4 ValidatePRE111Color(bool mobile_layout, Entry entry) {\n"
            + "  return " + expression + ";\n}\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Run ID must be numeric")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "etapa": "PRE112_TESTE_COMPILABILIDADE_ISOLADO",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "snapshot_sha256_verified": False,
        "pre92_source_verified": False,
        "pre111_proposal_sha256_verified": False,
        "baseline_host_cpp": {"attempted": False},
        "proposal_host_cpp": {"attempted": False},
        "new_cpp_fragment": {"attempted": False},
        "android_compilation": False,
        "apk_built": False,
        "original_workspace_modified": False,
        "google_drive_modified": False,
        "permanent_signing_key_accessed": False,
        "changes_only_in_ephemeral_runner": True,
    }

    try:
        report["phase"] = "PREPARE_HOST_COMPILER"
        compiler = shutil.which("clang++") or shutil.which("g++")
        if compiler is None:
            raise RuntimeError("No C++ compiler on runner")
        report["compiler_basename"] = Path(compiler).name

        report["phase"] = "GOOGLE_OAUTH"
        drive = drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre112_", dir="/tmp") as tmp:
            scratch = Path(tmp)
            if shutil.disk_usage(scratch).free < 4 * 1024 ** 3:
                raise RuntimeError("Not enough ephemeral disk for safe source extraction")
            archive = scratch / "pre99.tar.gz"
            restored = scratch / "restored"
            restored.mkdir()

            report["phase"] = "DOWNLOAD_AND_VERIFY_PRE99"
            download(drive, archive)
            digest, _md5, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 TAR hash mismatch")
            report["snapshot_sha256_verified"] = True

            report["phase"] = "RESTORE_EPHEMERAL_COPY"
            report["restore_check"] = restore(archive, restored)
            cpp = restored / SOURCE_NAME
            if not cpp.is_file() or hashlib.sha256(cpp.read_bytes()).hexdigest() != SOURCE_SHA256:
                raise ValueError("PRE92 source SHA mismatch after extraction")
            report["pre92_source_verified"] = True
            original = cpp.read_text(encoding="utf-8")

            report["phase"] = "VERIFY_PROPOSAL_HASH"
            proposed, diff = propose(original)
            new_hash = hashlib.sha256(proposed.encode("utf-8")).hexdigest()
            if new_hash != EXPECTED_PRE111_SHA256 or len(diff.splitlines()) != EXPECTED_DIFF_LINES:
                raise ValueError("PRE111 proposal drift detected")
            report["pre111_proposal_sha256_verified"] = True
            report["source_sha256_before"] = SOURCE_SHA256
            report["source_sha256_proposed"] = new_hash

            report["phase"] = "COMPILE_FRAGMENT_ONLY"
            snippet = scratch / "pre111_exact_fragment.cpp"
            snippet.write_text(fragment_for_compile(proposed), encoding="utf-8")
            report["new_cpp_fragment"] = compile_syntax(compiler, snippet, [], timeout=30)
            if not report["new_cpp_fragment"].get("passed"):
                report["status"] = "FALHA_SINTAXE_NOVO_CODIGO"
                return 1

            report["phase"] = "COMPILE_FULL_BASELINE_HOST"
            include_dirs = get_candidate_includes(restored)
            report["host_include_directory_count"] = len(include_dirs)
            report["baseline_host_cpp"] = compile_syntax(compiler, cpp, include_dirs, timeout=120)

            report["phase"] = "COMPILE_FULL_PROPOSED_HOST"
            # Only the source inside the disposable extracted sandbox is written.
            cpp.write_text(proposed, encoding="utf-8")
            if hashlib.sha256(cpp.read_bytes()).hexdigest() != EXPECTED_PRE111_SHA256:
                raise ValueError("Ephemeral patched source hash mismatch")
            report["proposal_host_cpp"] = compile_syntax(compiler, cpp, include_dirs, timeout=120)

            if report["baseline_host_cpp"].get("passed") and report["proposal_host_cpp"].get("passed"):
                report["status"] = "SINTAXE_CPP_FONTE_COMPLETA_VALIDADA_NO_HOST"
            elif report["baseline_host_cpp"].get("passed") and not report["proposal_host_cpp"].get("passed"):
                report["status"] = "FALHA_CPP_APENAS_NA_PROPOSTA"
            else:
                report["status"] = "FRAGMENTO_CPP_VALIDO_FONTE_COMPLETA_INCONCLUSIVA"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE112 could not complete phase:", report["phase"],
              "exception type:", type(exc).__name__)
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("PRE112 result:", report["status"],
              "host baseline:", report["baseline_host_cpp"].get("passed"),
              "host modified:", report["proposal_host_cpp"].get("passed"),
              "fragment:", report["new_cpp_fragment"].get("passed"))
    return 0 if report["status"] in (
        "SINTAXE_CPP_FONTE_COMPLETA_VALIDADA_NO_HOST",
        "FRAGMENTO_CPP_VALIDO_FONTE_COMPLETA_INCONCLUSIVA",
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
