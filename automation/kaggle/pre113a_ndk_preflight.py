#!/usr/bin/env python3
"""PRE113A: GitHub runner NDK r28.2 availability check, no Drive or game files."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TARGET_REVISION = "28.2.13676358"
TARGET_API = 26

def ndk_revision(root: Path) -> str | None:
    p = root / "source.properties"
    if not p.is_file():
        return None
    m = re.search(r"(?m)^Pkg.Revision\s*=\s*([0-9.]+)\s*$", p.read_text(errors="replace"))
    return m.group(1) if m else None

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Invalid run ID")
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "etapa": "PRE113A_NDK_ARM64_PREFLIGHT",
        "run_id": args.run_id,
        "expected_ndk_revision": TARGET_REVISION,
        "project_min_sdk": TARGET_API,
        "status": "NAO_VERIFICADO",
        "ndk_version_found": None,
        "ndk_exact_version": False,
        "cpp23_byteswap_compile_ok": False,
        "android_predefines_ok": False,
        "ndk_installation_attempted": False,
        "game_files_read": False,
        "google_credentials_accessed": False,
        "apk_compiled": False,
        "signing_key_accessed": False,
    }
    try:
        candidates = []
        for key in ("ANDROID_NDK_HOME", "ANDROID_NDK_ROOT"):
            if os.environ.get(key):
                candidates.append(Path(os.environ[key]))
        sdk_bases = []
        for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
            if os.environ.get(key):
                sdk_bases.append(Path(os.environ[key]))
        sdk_bases.extend((Path("/usr/local/lib/android/sdk"), Path("/opt/android-sdk")))
        for sdk in sdk_bases:
            candidates.append(sdk / "ndk" / TARGET_REVISION)
            if (sdk / "ndk").is_dir():
                candidates.extend((sdk / "ndk").iterdir())
        available = []
        for root in candidates:
            version = ndk_revision(root)
            if version and version not in available:
                available.append(version)
            if version == TARGET_REVISION:
                report["ndk_version_found"] = version
                report["ndk_exact_version"] = True
                binpath = root / "toolchains" / "llvm" / "prebuilt" / "linux-x86_64" / "bin"
                compiler = binpath / ("aarch64-linux-android" + str(TARGET_API) + "-clang++")
                if not compiler.is_file():
                    raise FileNotFoundError("Android ARM64 C++ driver missing")
                with tempfile.TemporaryDirectory(prefix="pre113a_") as td:
                    source = Path(td) / "verify.cpp"
                    source.write_text(
                        "#include <bit>\n#include <cstdint>\n"
                        "#ifndef __ANDROID__\n#error NOT_ANDROID\n#endif\n"
                        "#ifndef __aarch64__\n#error NOT_AARCH64\n#endif\n"
                        "static_assert(std::byteswap((uint32_t)0xAABBCCDD) == 0xDDCCBBAA);\n"
                        "int main(){return 0;}\n", encoding="utf-8"
                    )
                    run = subprocess.run(
                        [str(compiler), "-std=c++23", "-fsyntax-only", str(source)],
                        capture_output=True, text=True, timeout=45, check=False
                    )
                    report["cpp23_byteswap_compile_ok"] = run.returncode == 0
                    report["android_predefines_ok"] = run.returncode == 0
                    if run.returncode:
                        report["compile_error_class"] = (
                            "missing_CXX23_byteswap" if "byteswap" in run.stderr
                            else "other_compilation_error"
                        )
                break
        report["installed_ndk_revisions"] = sorted(set(available))
        report["sdkmanager_on_path"] = bool(shutil.which("sdkmanager"))
        report["sdk_roots_present"] = len([x for x in sdk_bases if x.is_dir()])
        report["status"] = (
            "NDK_EXATO_ARM64_CXX23_VALIDADO" if report["cpp23_byteswap_compile_ok"]
            else "NDK_EXATO_CPP23_FALHOU" if report["ndk_exact_version"]
            else "NDK_EXATO_AUSENTE"
        )
    except Exception as exc:
        report["status"] = "PRE113A_ERRO"
        report["error_type"] = type(exc).__name__
        print("PRE113A error class:", type(exc).__name__)
    finally:
        report["recorded_utc"] = datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("PRE113A status:", report["status"])
    # An NDK absence is a valid preflight result; next workflow can install it in ephemeral runner.
    return 0 if report["status"] in (
        "NDK_EXATO_ARM64_CXX23_VALIDADO", "NDK_EXATO_CPP23_FALHOU", "NDK_EXATO_AUSENTE"
    ) else 1

if __name__ == "__main__":
    raise SystemExit(main())
