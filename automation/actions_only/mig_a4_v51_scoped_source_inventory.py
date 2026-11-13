#!/usr/bin/env python3
"""MIG-A4: safe inventory of V51 recipe differences vs public fork, source-only.

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
PIN_FORK_COMMIT = "6cc6d679b9b844a2a798981f4f47095df381be17"
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
        raise RuntimeError("MIG_A4_DIFF_COMMAND_FAILED_" + str(p.returncode))
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



# MIG-A4 only inventories source paths already tracked in the *public* fork.
# Private build outputs, game recompilation, vendor/shader blobs and signing files
# are not part of the candidate set, even if present in PRE99.
ALLOWED_SOURCE_SUFFIXES = (".cpp", ".cc", ".c", ".h", ".hpp", ".java", ".kt", ".kts")
EXCLUDED_COMPONENTS = {
    "third_party", "vendor", "external", "generated", "assets", "shader",
    "shaders", "game", "game_usa", "app_usa", "build", "obj", "libs",
    "jniLibs", "testdata", "rom", "iso", "xex",
}
MAX_SOURCE_BYTES = 768 * 1024
MAX_CANDIDATES = 2200
VIRTUAL_RENDERER_PATH = "nativo/app/src/nfsmw_nativo_dibujos.cpp"


def allowed_public_path(name: str) -> bool:
    if not (name.startswith("nativo/app/src/nfsmw_")
            or name.startswith("nativo/app/include/nfsmw_")
            or name.startswith("nativo/sdk/src/")
            or name.startswith("nativo/sdk/include/rex/")
            or name.startswith("android/app/src/main/java/io/github/nfsmwrecomp/")):
        return False
    if not name.endswith(ALLOWED_SOURCE_SUFFIXES):
        return False
    if any(p.lower() in {s.lower() for s in EXCLUDED_COMPONENTS} for p in Path(name).parts):
        return False
    return True


def collect_public_paths(fork_dir: Path) -> list[str]:
    p = subprocess.run(["git", "-C", str(fork_dir), "ls-files", "-z"],
                       check=True, capture_output=True, timeout=30)
    names = [v.decode("utf-8", errors="strict") for v in p.stdout.split(b"\0") if v]
    selected = sorted({n for n in names if allowed_public_path(n)})
    if not (VIRTUAL_RENDERER_PATH in selected and
            set(PATHS).issubset(set(selected)) and 7 <= len(selected) <= MAX_CANDIDATES):
        raise ValueError("MIG_A4_TRACKED_CANDIDATES_INCOMPLETE_OR_EXCESSIVE")
    return selected


def protected_snapshot(root: Path, names: list[str]) -> dict[str, bytes | None]:
    out = {}
    for n in names:
        p = root / n
        if not p.exists():
            out[n] = None
        elif p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_SOURCE_BYTES:
            # Fail closed: exclusions are counted but not read; do not follow symlinks.
            out[n] = None
        else:
            out[n] = p.read_bytes()
    return out


def fingerprint(data: bytes | None) -> dict | None:
    return ({"bytes": len(data), "sha256": digest(data)} if data is not None else None)


def classify_change(baseline: bytes | None, v51: bytes | None, fork: bytes | None) -> str:
    if baseline is None and v51 is not None:
        return "RECIPE_ADDED_PUBLIC_PATH"
    if baseline is not None and v51 is None:
        return "RECIPE_REMOVED_PUBLIC_PATH"
    if v51 is None:
        return "NO_V51_DATA_IN_SCOPED_PATH"
    if fork is None:
        return "FORK_PUBLIC_PATH_NOT_READABLE"
    if fork == v51:
        return "V51_CHANGE_ALREADY_IDENTICAL_IN_FORK"
    if fork == baseline:
        return "V51_CHANGE_FORK_STILL_BASELINE"
    return "BOTH_CHANGED_REQUIRE_FUNCTION_REVIEW"


def inventory_change(name: str, baseline: bytes | None,
                     v51: bytes | None, fork: bytes | None, scratch: Path) -> dict:
    result = {
        "path": name,
        "pre99": fingerprint(baseline),
        "v51_recipe": fingerprint(v51),
        "fork": fingerprint(fork),
        "classification": classify_change(baseline, v51, fork),
        "publishable_source_contents": False,
        "requires_manual_review": True,
    }
    if baseline is not None and v51 is not None and fork is not None:
        if any(b"\0" in d for d in (baseline, v51, fork)):
            raise ValueError("MIG_A4_NON_TEXT_SOURCE_ABORT_" + name)
        temp = scratch / "candidate"
        temp.mkdir(parents=True, exist_ok=True)
        base_path, v51_path, fork_path = temp / "base", temp / "v51", temp / "fork"
        for p, d in ((base_path, baseline), (v51_path, v51), (fork_path, fork)):
            p.write_bytes(d)
        result["hunks_pre99_to_v51"] = diff_stats(base_path, v51_path)["hunks"]
        result["hunks_pre99_to_fork"] = diff_stats(base_path, fork_path)["hunks"]
        result["hunks_v51_to_fork"] = diff_stats(v51_path, fork_path)["hunks"]
        if fork != baseline and fork != v51:
            m = merge_conflicts(fork_path, base_path, v51_path)
            result["merge_syntactically_clean"] = m["syntactic_merge_clean"]
            result["conflicts_capped_127"] = m["merge_conflict_count_capped_127"]
    return result


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
        tracked = collect_public_paths(fork_dir)
        baseline = protected_snapshot(root, tracked)
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
        after = protected_snapshot(root, tracked)
        # PRE648 changed the renderer in-memory; the patch was NOT persisted to
        # nativo/app/src at this point in PRE696 and must not be silently omitted.
        after[VIRTUAL_RENDERER_PATH] = p648.patch_bytes(renderer)
        if digest(after[VIRTUAL_RENDERER_PATH]) != PIN_V51_RENDERER:
            raise ValueError("MIG_A4_RENDERER_VIRTUAL_PATCH_MISMATCH")
        fork_files = protected_snapshot(fork_dir, tracked)
        for ref in refs:
            name = ref["path"]
            if after[name] is None or digest(after[name]) != ref["sha256"]:
                raise ValueError("MIG_A4_PRE696_CANARY_SHA_DRIFT_" + name)
            if after[name] != baseline[name]:
                raise ValueError("MIG_A4_PRE696_7_CANARIES_CHANGED_UNEXPECTEDLY_" + name)
        changed = []
        for name in tracked:
            old, new, pub = baseline[name], after[name], fork_files[name]
            if new == old:
                continue
            if old is None and new is None:
                continue
            if (old is not None and len(old) > MAX_SOURCE_BYTES) or (new is not None and len(new) > MAX_SOURCE_BYTES):
                raise ValueError("MIG_A4_OVERSIZED_PATCH_SOURCE")
            row = inventory_change(name, old, new, pub, temp / "diff_buffers")
            changed.append(row)
        result["files"] = changed
        result["status"] = "PASS_AUTHENTICATED_SCOPED_INVENTORY"
        result["stage"] = "MIG_A4_PRE99_V51_FORK_SCOPED_SOURCE_CHANGE_INVENTORY"
        result["scope"] = ("Only public-fork-tracked source paths under nativo/app/src/nfsmw_, "
                           "nativo/app/include/nfsmw_, nativo/sdk/src, nativo/sdk/include/rex, "
                           "android/app/src/main/java/io/github/nfsmwrecomp; "
                           "no private/untracked, generated game code or app_usa")
        result["renderer_p648_patch_injected_in_memory"] = True
        result["candidate_count"] = len(tracked)
        result["counts"] = {
            "candidate_public_source_paths": len(tracked),
            "source_paths_changed_pre99_to_v51_recipe": len(changed),
            "v51_changed_fork_still_baseline": sum(
                x["classification"] == "V51_CHANGE_FORK_STILL_BASELINE" for x in changed),
            "v51_change_already_identical": sum(
                x["classification"] == "V51_CHANGE_ALREADY_IDENTICAL_IN_FORK" for x in changed),
            "both_changed_need_review": sum(
                x["classification"] == "BOTH_CHANGED_REQUIRE_FUNCTION_REVIEW" for x in changed),
            "recipe_added_public_paths": sum(
                x["classification"] == "RECIPE_ADDED_PUBLIC_PATH" for x in changed),
            "recipe_removed_public_paths": sum(
                x["classification"] == "RECIPE_REMOVED_PUBLIC_PATH" for x in changed),
            "syntactic_conflict_files": sum(
                x.get("merge_syntactically_clean") is False for x in changed),
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "MIG_A4_SCOPED_SOURCE_INVENTORY.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    notes = [
        "# MIG-A4 — Inventário de patches da receita V51 no escopo público do fork",
        "",
        "**PASS_AUTHENTICATED_SCOPED_INVENTORY** — GitHub Actions exclusivo, sem Kaggle.",
        "",
        "Todos os resultados são metadados: SHA-256, tamanhos e contagem de hunks.",
        "Não inclui texto do jogo, código modificado privado, assets ou assinatura.",
        "",
        "**Não é um diff de toda a árvore:** somente caminhos-fonte já rastreados no fork",
        "e prefixos restritos; fontes geradas, app_usa e caminhos privados excluídos.",
        "O patch PRE648 do renderizador é aplicado apenas em memória para análise.",
        "A receita V51 reconstruída não prova equivalência binária com a APK assinada.",
        "",
        "## Contagens",
    ]
    notes += ["- " + k + ": " + str(v) for k,v in result["counts"].items()]
    notes.extend(["", "## Arquivos alterados pela receita V51 dentro do escopo"])
    notes.extend(["- " + x["path"] + ": " + x["classification"]
                  + ", hunks V51=" + str(x.get("hunks_pre99_to_v51", "n/a"))
                  + ", hunks fork=" + str(x.get("hunks_pre99_to_fork", "n/a"))
                  + ", conflito=" + str(x.get("conflicts_capped_127", "n/a"))
                  for x in result["files"]])
    notes.extend(["", "Recomendação: revisão manual das mudanças específicas sem sobrescrever",
                  "o código do upstream; não portar até validar semântica e build.",
                  "Sem apk, sem teste de smartphone, sem ganho FPS comprovado."])
    (output_dir / "MIG_A4_SCOPED_SOURCE_INVENTORY.md").write_text(
        "\n".join(notes)+"\n")
    print("MIG_A4_STATUS=PASS_AUTHENTICATED_SCOPED_INVENTORY")
    for k,v in result["counts"].items():
        print("MIG_A4_" + k.upper() + "=" + str(v))
    print("MIG_A4_RAW_SOURCE_EXPORTED=FALSE")
    print("MIG_A4_APK_MODIFIED=FALSE")


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
    assert allowed_public_path(VIRTUAL_RENDERER_PATH)
    assert not allowed_public_path("nativo/app_usa/src/nfsmw_nativo_dibujos.cpp")
    assert not allowed_public_path("nativo/app/src/game_recompiled.cpp")
    assert allowed_public_path("android/app/src/main/java/io/github/nfsmwrecomp/Test.java")
    print("MIG_A4_LOCAL_SELF_TEST=PASS")


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
