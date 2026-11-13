#!/usr/bin/env python3
"""MIG-A3: authenticated V51 vs PRE99 vs fixed public fork, source-only.

Rebuilds the PRE696 source recipe on a disposable GitHub Actions runner.
Reports only SHA256, sizes, diff hunk counts and git three-way conflict counts.
Never uploads source, merge output, XEX, game assets, APK or signing material.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

PIN_PRE99 = "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
PIN_V50_RENDERER = "1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
PIN_V51_RENDERER = "9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
PIN_BACKEND = "b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
PIN_APK = "207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
PIN_CERT = "1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
PIN_FORK_COMMIT = "13373b70642a19adf232cd9ba39fc7ecb2275dc8"
PIN_REFERENCE_ZIP = "d06e06d4dda54d4b50924ec5a404ef396c91cef2166f7b9e055f4b5910154075"
PATHS = (
    "nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp",
    "nativo/sdk/include/rex/ui/vulkan/presenter.h",
    "nativo/app/src/nfsmw_ajustes_graficos.cpp",
    "nativo/app/src/nfsmw_nativo_sistema.cpp",
    "nativo/app/src/nfsmw_nativo_destinos.cpp",
    "android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java",
    "android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java",
)
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_cmd(argv: list[str], timeout: int = 90) -> subprocess.CompletedProcess:
    p = subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
    if p.returncode not in (0, 1):
        raise RuntimeError("MIG_A3_DIFF_COMMAND_FAILED_" + str(p.returncode))
    return p


def diff_stats(old_path: Path, new_path: Path) -> dict:
    result = run_cmd(["git", "diff", "--no-index", "--unified=0", "--",
                      str(old_path), str(new_path)])
    if result.returncode == 0:
        return {"hunks": 0, "base_lines_removed": 0, "new_lines_added": 0}
    raw = result.stdout.decode("utf-8", errors="replace")
    spans = [(int(a), int(b or 1), int(c), int(d or 1))
             for a, b, c, d in HUNK_RE.findall(raw)]
    if not spans:
        raise ValueError("MIG_A3_UNEXPECTED_DIFF_NO_HUNKS")
    return {
        "hunks": len(spans),
        "base_lines_removed": sum(x[1] for x in spans),
        "new_lines_added": sum(x[3] for x in spans),
    }


def merge_conflicts(fork_path: Path, base_path: Path, v51_path: Path) -> dict:
    # -p: write merged content to stdout only, never modify inputs.
    # Any stdout is deliberately discarded, never put in logs or artifact.
    p = subprocess.run(
        ["git", "merge-file", "-p", "-L", "fork", "-L", "base", "-L", "v51",
         str(fork_path), str(base_path), str(v51_path)],
        capture_output=True, check=False, timeout=90,
    )
    if p.returncode < 0 or p.returncode > 127 or b"error:" in p.stderr.lower():
        raise RuntimeError("MIG_A3_MERGE_ENGINE_ERROR")
    # Git's exit code is conflict count, capped at 127, not a semantic verdict.
    return {"merge_file_exit_code": p.returncode,
            "syntactic_merge_clean": p.returncode == 0,
            "merge_conflict_count_capped_127": p.returncode}


def classify(base: bytes, v51: bytes, fork: bytes, merge: dict) -> str:
    if fork == v51 == base:
        return "IDENTICAL_ALL_THREE"
    if fork == v51:
        return "SAME_CHANGE_RELATIVE_TO_PRE99"
    if v51 == base:
        return "V51_UNCHANGED_FORK_CHANGED"
    if fork == base:
        return "V51_CHANGED_FORK_UNCHANGED"
    return ("BOTH_CHANGED_MERGE_CLEAN_CANDIDATE"
            if merge["syntactic_merge_clean"] else "BOTH_CHANGED_MERGE_CONFLICT")


def analyze_source(base: bytes, v51: bytes, fork: bytes,
                   ref: dict, folder: Path, name: str) -> dict:
    if len(v51) != ref["bytes"] or digest(v51) != ref["sha256"]:
        raise ValueError("MIG_A3_AUTHENTICATED_V51_SOURCE_MISMATCH_" + name)
    if not all(x and b"\x00" not in x for x in (base, v51, fork)):
        raise ValueError("MIG_A3_BINARY_OR_EMPTY_SOURCE_" + name)
    target = folder / name
    target.mkdir(parents=True, exist_ok=True)
    base_file, v51_file, fork_file = (
        target / "baseline", target / "v51", target / "fork")
    for path, data in ((base_file, base), (v51_file, v51), (fork_file, fork)):
        path.write_bytes(data)
    baseline_v51 = diff_stats(base_file, v51_file)
    baseline_fork = diff_stats(base_file, fork_file)
    v51_fork = diff_stats(v51_file, fork_file)
    merge = merge_conflicts(fork_file, base_file, v51_file)
    out = {
        "path": name,
        "sha256_pre99": digest(base),
        "sha256_v51": digest(v51),
        "sha256_fork": digest(fork),
        "bytes_pre99": len(base),
        "bytes_v51": len(v51),
        "bytes_fork": len(fork),
        "pre99_to_v51": baseline_v51,
        "pre99_to_fork": baseline_fork,
        "v51_to_fork": v51_fork,
        "three_way_git_merge": merge,
        "classification": classify(base, v51, fork, merge),
        "manual_review_required": fork != v51,
    }
    return out


def download_pre99(drive, destination: Path, expected_bytes: int) -> None:
    from googleapiclient.http import MediaIoBaseDownload
    from pre104_verify_backup_tar import BACKUP_ID
    request = drive.files().get_media(fileId=BACKUP_ID, supportsAllDrives=True)
    with destination.open("wb") as stream:
        transfer = MediaIoBaseDownload(stream, request, chunksize=8 * 1024 * 1024)
        consecutive = 0
        while True:
            try:
                _, complete = transfer.next_chunk(num_retries=4)
            except (http.client.IncompleteRead, ConnectionResetError,
                    ConnectionAbortedError, BrokenPipeError, TimeoutError, OSError) as exc:
                consecutive += 1
                if consecutive > 9:
                    raise RuntimeError("MIG_A3_PRE99_CHUNK_RETRIES_EXHAUSTED") from exc
                time.sleep(min(2 ** consecutive, 20))
                continue
            consecutive = 0
            if complete:
                break
    if destination.stat().st_size != expected_bytes:
        raise ValueError("MIG_A3_PRE99_SIZE_MISMATCH")


def run(fork_dir: Path, output_dir: Path) -> None:
    from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
    from pre105_read_settings_source import drive_client
    from pre107_restore_isolated import restore
    import pre431_v46_source_dual_trace_compat_readonly as v46
    import pre434_build_signed_v47_bmw_passive_diag as p434
    import pre638_build_signed_v50_c3_two_request_diag as v50
    import pre648_v50_shader_pass_counts_arm64_noapk as p648
    import pre652_build_signed_v51_gpu_shader_counts_diag as p652

    manifest = json.loads((fork_dir / "tools/ci/v51_pre696_pinned_manifest.json").read_text())
    refs = manifest["files"]
    if [x["path"] for x in refs] != list(PATHS):
        raise ValueError("MIG_A3_MANIFEST_PATH_SET_MISMATCH")
    if manifest["source_artifact"]["sha256"] != PIN_REFERENCE_ZIP:
        raise ValueError("MIG_A3_REFERENCE_ZIP_MISMATCH")
    if manifest["source_artifact"]["replayed_V51_binaries_equivalent_to_signed_APK"] is not False:
        raise ValueError("MIG_A3_UNSAFE_EQUIVALENCE_CLAIM")
    if EXPECTED_SHA256 != PIN_PRE99 or p652.SOURCE_SHA != PIN_V51_RENDERER:
        raise ValueError("MIG_A3_SOURCE_PIN_MISMATCH")
    if not (fork_dir / ".git").exists():
        raise ValueError("MIG_A3_FORK_CHECKOUT_MISSING")
    result_commit = subprocess.run(
        ["git", "-C", str(fork_dir), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=15).stdout.strip()
    if result_commit != PIN_FORK_COMMIT:
        raise ValueError("MIG_A3_FORK_COMMIT_DRIFT")
    gate = json.loads(Path("docs/PRE652_V51_SIGNED_GPU_SHADER_DIAGNOSTIC_VERIFIED.json").read_text())
    apk = gate.get("apk", {})
    if not (gate.get("status") == "SIGNED_AND_DRIVE_VERIFIED"
            and apk.get("sha256") == PIN_APK and apk.get("version_code") == 51
            and apk.get("permanent_certificate_sha256") == PIN_CERT):
        raise ValueError("MIG_A3_SIGNED_BASELINE_METADATA_MISMATCH")
    v50.require_pre637()
    result = {
        "stage": "MIG_A3_PRE99_V51_FORK_THREE_WAY_SOURCE_AUDIT",
        "status": "FAIL_CLOSED",
        "pre99_sha256": PIN_PRE99,
        "pre696_reference_zip_sha256": PIN_REFERENCE_ZIP,
        "fork_commit": PIN_FORK_COMMIT,
        "source_signed_apk_binary_equivalence_proven": False,
        "source_code_exported": False,
        "source_modified_in_fork": False,
        "apk_built": False,
        "signing_material_read": False,
        "fps_gain_proven": False,
        "files": [],
    }
    with tempfile.TemporaryDirectory(prefix="nfsmw_mig_a3_") as td:
        temp = Path(td)
        arc = temp / "pre99.tar.gz"
        download_pre99(drive_client(), arc, EXPECTED_BYTES)
        download_hash, _, download_bytes = sha_file(arc)
        if (download_hash, download_bytes) != (PIN_PRE99, EXPECTED_BYTES):
            raise ValueError("MIG_A3_PRE99_HASH_FAILED")
        stage = temp / "restore"
        stage.mkdir()
        restore(arc, stage)
        arc.unlink(missing_ok=True)
        root = stage / "workspace"
        baseline = {p: (root / p).read_bytes() for p in PATHS}
        replay = v46.replay_v46_sources(root, Path.cwd())
        if replay["PRE398"].get("cheat_enabled") is not True:
            raise ValueError("MIG_A3_STAGE_PRE398_MISSING")
        prev = p434.ORIGINAL_STAGE
        def check_menu(folder: Path):
            cmake = (folder / "nativo/app/CMakeLists.txt").read_text()
            if cmake.count(v46.PRE292_REGISTER) != 1:
                raise ValueError("MIG_A3_MENU_REGISTER_NOT_EXACTLY_ONCE")
            return {"menu_registered_once": True}
        try:
            p434.ORIGINAL_STAGE = check_menu
            staged = v50.stage_v50(root)
        finally:
            p434.ORIGINAL_STAGE = prev
        if not (staged["pre638_v49_source_recipe_verified"] is True
                and staged["pre638_c3_fallback_bypass"] is False
                and staged["pre638_v49_callbacks_nitro_preserved"] is True
                and staged["pre638_save_modified"] is False):
            raise ValueError("MIG_A3_V50_STAGE_GUARDS_FAILED")
        renderer = (root / "nativo/app/src/nfsmw_nativo_dibujos.cpp").read_bytes()
        backend = (root / "nativo/app/src/nfsmw_nativo_destinos.cpp").read_bytes()
        if digest(renderer) != PIN_V50_RENDERER or digest(p648.patch_bytes(renderer)) != PIN_V51_RENDERER:
            raise ValueError("MIG_A3_V51_RENDERER_RECIPE_FAILED")
        if digest(p648.HEADER.read_bytes()) != p652.HEADER_SHA or digest(backend) != PIN_BACKEND:
            raise ValueError("MIG_A3_V51_HEADER_OR_BACKEND_FAILED")
        for ref in refs:
            name = ref["path"]
            data_v51 = (root / name).read_bytes()
            data_fork = (fork_dir / name).read_bytes()
            row = analyze_source(baseline[name], data_v51, data_fork,
                                 ref, temp / "diff_buffers", name)
            result["files"].append(row)
        result["status"] = "PASS_THREE_WAY_SOURCE_ONLY"
        result["counts"] = {
            "same_v51_fork": sum(r["sha256_v51"] == r["sha256_fork"] for r in result["files"]),
            "v51_changed_since_pre99": sum(r["sha256_pre99"] != r["sha256_v51"] for r in result["files"]),
            "fork_changed_since_pre99": sum(r["sha256_pre99"] != r["sha256_fork"] for r in result["files"]),
            "merge_conflict_files": sum(not r["three_way_git_merge"]["syntactic_merge_clean"] for r in result["files"]),
            "merge_clean_files": sum(r["three_way_git_merge"]["syntactic_merge_clean"] for r in result["files"]),
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "MIG_A3_THREE_WAY_SOURCE_REPORT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    notes = [
        "# MIG-A3 — PRE99 × receita V51 × fork público",
        "",
        "**PASS_THREE_WAY_SOURCE_ONLY** — executor GitHub Actions, sem Kaggle e sem fontes brutas em artifacts.",
        "",
        "**ATENÇÃO:** a receita V51 não é prova de equivalência binária com a APK assinada.",
        "Merge limpo significa apenas que Git conseguiu mesclar textos, nunca validação semântica ou de build.",
        "",
    ]
    for row in result["files"]:
        notes.append("- " + row["path"] + ": " + row["classification"]
                     + " (hunks V51=" + str(row["pre99_to_v51"]["hunks"])
                     + ", fork=" + str(row["pre99_to_fork"]["hunks"])
                     + ", conflitos do merge=" +
                     str(row["three_way_git_merge"]["merge_conflict_count_capped_127"]) + ")")
    notes += ["", "Nenhum código, game asset, APK, assinatura, save ou configuração alterado.",
              "Próximo: revisar semântica por função nos arquivos com patches exclusivos antes de portar."]
    (output_dir / "MIG_A3_THREE_WAY_SOURCE_REPORT.md").write_text("\n".join(notes) + "\n")
    print("MIG_A3_STATUS=PASS_THREE_WAY_SOURCE_ONLY")
    for k, v in result["counts"].items():
        print("MIG_A3_" + k.upper() + "=" + str(v))
    print("MIG_A3_RAW_SOURCE_EXPORTED=FALSE")
    print("MIG_A3_NO_NEW_APK=TRUE")


def self_test() -> None:
    assert digest(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    with tempfile.TemporaryDirectory() as td:
        b = b"line1\nline2\nmiddle\nline3\n"
        v = b"line1\nv51\nmiddle\nline3\n"
        f = b"line1\nline2\nmiddle\nfork\n"
        ref = {"sha256": digest(v), "bytes": len(v)}
        row = analyze_source(b, v, f, ref, Path(td), "fixture")
        assert row["pre99_to_v51"]["hunks"] == 1
        assert row["pre99_to_fork"]["hunks"] == 1
        assert row["three_way_git_merge"]["syntactic_merge_clean"] is True
        assert row["classification"] == "BOTH_CHANGED_MERGE_CLEAN_CANDIDATE"
    print("MIG_A3_LOCAL_SELF_TEST=PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fork-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    opt = parser.parse_args()
    if opt.self_test:
        self_test()
    else:
        if not opt.fork_dir or not opt.output_dir:
            parser.error("--fork-dir and --output-dir are required")
        run(opt.fork_dir.resolve(), opt.output_dir.resolve())
