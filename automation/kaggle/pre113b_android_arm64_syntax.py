#!/usr/bin/env python3
"""PRE113B: true NDK r28.2 Android ARM64 C++23 syntax check of PRE111.

Does not build an APK or access Android signing. Reuses SHA-checked PRE99 and
copies it into an ephemeral runner. Compiles both unpatched and patched
settings_overlay.cpp with Android's aarch64-linux-android26-clang++.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
from pre112_cpp_syntax_isolated import (
    EXPECTED_PRE111_SHA256, EXPECTED_DIFF_LINES, compile_syntax,
    fragment_for_compile, get_candidate_includes
)

NDK_REVISION = "28.2.13676358"
ANDROID_API = 26
HOST = "linux-x86_64"

def locate_toolchain() -> tuple[Path, Path]:
    sdk_candidates = []
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var):
            sdk_candidates.append(Path(os.environ[var]))
    sdk_candidates += [Path("/usr/local/lib/android/sdk"), Path("/opt/android-sdk")]
    checked = set()
    for sdk in sdk_candidates:
        sdk = sdk.resolve()
        if sdk in checked:
            continue
        checked.add(sdk)
        ndk = sdk / "ndk" / NDK_REVISION
        prop = ndk / "source.properties"
        if not prop.is_file():
            continue
        revision = re.search(r"(?m)^Pkg.Revision\s*=\s*(.+?)\s*$",
                             prop.read_text(encoding="utf-8", errors="replace"))
        if revision is None or revision.group(1).strip() != NDK_REVISION:
            continue
        binary = (ndk / "toolchains" / "llvm" / "prebuilt" / HOST / "bin"
                  / f"aarch64-linux-android{ANDROID_API}-clang++")
        if binary.is_file():
            return ndk, binary
    raise FileNotFoundError("NDK r28.2 Android API 26 compiler unavailable")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid GitHub run id")
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE113B_NDK_R28_ANDROID_ARM64_CXX23",
        "github_run_id": args.run_id,
        "status": "NAO_VALIDADO",
        "phase": "INITIAL",
        "required_ndk_revision": NDK_REVISION,
        "target_triple": f"aarch64-linux-android{ANDROID_API}",
        "cpp_standard": "c++23",
        "ndk_found_and_revision_confirmed": False,
        "predefines_aarch64_android_passed": False,
        "snapshot_sha256_verified": False,
        "restoration_to_ephemeral_runner_verified": False,
        "pre92_source_sha256_verified": False,
        "pre111_proposal_sha256_verified": False,
        "android_arm64_fragment": {"attempted": False},
        "android_arm64_baseline": {"attempted": False},
        "android_arm64_proposal": {"attempted": False},
        "original_workspace_modified": False,
        "google_drive_modified": False,
        "apk_compiled": False,
        "linker_invoked": False,
        "signing_key_accessed": False,
        "device_tested": False,
    }
    try:
        report["phase"] = "FIND_NDK_EXACT"
        _ndk, compiler = locate_toolchain()
        report["ndk_found_and_revision_confirmed"] = True
        report["ndk_driver_name"] = compiler.name

        with tempfile.TemporaryDirectory(prefix="nfsmw_pre113b_", dir="/tmp") as td:
            work = Path(td)
            report["phase"] = "VERIFY_ANDROID_ARCH_AND_CXX23"
            target_probe = work / "target_probe.cpp"
            target_probe.write_text(
                "#include <bit>\n#include <cstdint>\n"
                "#ifndef __ANDROID__\n#error NON_ANDROID_COMPILER\n#endif\n"
                "#ifndef __aarch64__\n#error NON_ARM64_COMPILER\n#endif\n"
                "static_assert(std::byteswap((uint32_t)0x11223344) == 0x44332211);\n"
                "int main(){return 0;}\n", encoding="utf-8"
            )
            report["android_target_probe"] = compile_syntax(
                str(compiler), target_probe, [], timeout=45
            )
            if not report["android_target_probe"].get("passed"):
                report["status"] = "NDK_ARM64_CPP23_TARGET_PROBE_FAILED"
                return 1
            report["predefines_aarch64_android_passed"] = True

            if shutil.disk_usage(work).free < 4 * 1024 ** 3:
                raise RuntimeError("Insufficient temporary storage")

            report["phase"] = "AUTH_AND_DOWNLOAD_PRE99"
            drive = drive_client()
            archive = work / "pre99.tar.gz"
            download(drive, archive)
            report["phase"] = "VERIFY_PRE99_FULL_SHA256"
            actual_sha, _md5, actual_bytes = sha_file(archive)
            if actual_sha != EXPECTED_SHA256 or actual_bytes != EXPECTED_BYTES:
                raise ValueError("PRE99 archive checksum/size mismatch")
            report["snapshot_sha256_verified"] = True

            report["phase"] = "RESTORE_TEMPORARY_WORKSPACE"
            extracted = work / "restore_temp"
            extracted.mkdir()
            stats = restore(archive, extracted)
            report["restoration_to_ephemeral_runner_verified"] = True
            report["restored_member_count"] = stats["members_restored"]
            original_cpp = extracted / SOURCE_NAME
            if not original_cpp.is_file():
                raise FileNotFoundError("Settings source missing in ephemeral restore")
            original_bytes = original_cpp.read_bytes()
            if hashlib.sha256(original_bytes).hexdigest() != SOURCE_SHA256:
                raise ValueError("PRE92 source mismatch")
            report["pre92_source_sha256_verified"] = True

            report["phase"] = "VERIFY_EXACT_PRE111_PROPOSAL"
            new_cpp, diff = propose(original_bytes.decode("utf-8"))
            proposed_sha = hashlib.sha256(new_cpp.encode("utf-8")).hexdigest()
            if proposed_sha != EXPECTED_PRE111_SHA256 or len(diff.splitlines()) != EXPECTED_DIFF_LINES:
                raise ValueError("PRE111 proposal hash/diff mismatch")
            report["pre111_proposal_sha256_verified"] = True
            report["original_source_sha256"] = SOURCE_SHA256
            report["proposed_source_sha256"] = proposed_sha

            report["phase"] = "COMPILE_NEW_ANDROID_FRAGMENT"
            snippet = work / "pre111_fragment.cpp"
            snippet.write_text(fragment_for_compile(new_cpp), encoding="utf-8")
            report["android_arm64_fragment"] = compile_syntax(
                str(compiler), snippet, [], timeout=60
            )
            if not report["android_arm64_fragment"].get("passed"):
                report["status"] = "PRE111_NOVO_CODIGO_FALHOU_ANDROID_ARM64"
                return 1

            report["phase"] = "COMPARE_FULL_CPP_ANDROID_ARM64"
            dirs = get_candidate_includes(extracted)
            report["include_directory_count"] = len(dirs)
            report["android_arm64_baseline"] = compile_syntax(
                str(compiler), original_cpp, dirs, timeout=150
            )
            # NOTE: modifies only a file extracted to disposable GitHub runner /tmp.
            original_cpp.write_text(new_cpp, encoding="utf-8")
            if hashlib.sha256(original_cpp.read_bytes()).hexdigest() != EXPECTED_PRE111_SHA256:
                raise ValueError("Ephemeral patched source write mismatch")
            report["android_arm64_proposal"] = compile_syntax(
                str(compiler), original_cpp, dirs, timeout=150
            )

            baseline_ok = report["android_arm64_baseline"].get("passed") is True
            proposal_ok = report["android_arm64_proposal"].get("passed") is True
            if baseline_ok and proposal_ok:
                report["status"] = "SINTAXE_ANDROID_ARM64_CPP23_VALIDADA"
            elif baseline_ok:
                report["status"] = "REGRESSAO_SINTATICA_PRE111_ANDROID_ARM64"
            else:
                report["status"] = "FONTE_COMPLETA_ANDROID_ARM64_INCONCLUSIVA"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        print("PRE113B not completed at phase:", report["phase"],
              "; exception type:", type(exc).__name__)
    finally:
        report["recorded_utc"] = datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("PRE113B:", report["status"],
              "source:", report["android_arm64_baseline"].get("passed"),
              "modified:", report["android_arm64_proposal"].get("passed"))
    return 0 if report["status"] in (
        "SINTAXE_ANDROID_ARM64_CPP23_VALIDADA",
        "FONTE_COMPLETA_ANDROID_ARM64_INCONCLUSIVA"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
