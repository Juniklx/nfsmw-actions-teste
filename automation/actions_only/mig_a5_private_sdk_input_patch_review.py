#!/usr/bin/env python3
"""MIG-A5: private SDK input three-way patch review, source-only.

Rebuilds the PRE696 source recipe on a disposable GitHub Actions runner.
Reports only SHA256, sizes, diff hunk counts and git three-way conflict counts.
Never uploads source, merge output, XEX, game assets, APK or signing material.
"""
from __future__ import annotations

import argparse
import difflib
import zipfile
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
PIN_FORK_COMMIT = "16233a34b88f0af3880fb506ba68f6d6c6e137f3"
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



# Only Xenia/ReX SDK input source paths already tracked by the public fork.
# This is NOT a game-code patch dump, nor release. The patch and exact
# restored V51 input SDK files are uploaded solely to the user's private Drive.
PRIVATE_PATHS = (
    "nativo/sdk/include/rex/input/sdl/sdl_input_driver.h",
    "nativo/sdk/src/input/input_system.cpp",
    "nativo/sdk/src/input/sdl/sdl_input_driver.cpp",
)
EXPECTED_HUNKS_V51 = (2, 2, 2)
EXPECTED_HUNKS_FORK = (0, 0, 7)
PRIVATE_PARENT_FOLDER = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
PRIVATE_NAME = "NFSMW_MIG_A5_PRIVATE_SDK_INPUT_REVIEW_20261113.zip"


def checked_source(root: Path, name: str) -> bytes:
    if name not in PRIVATE_PATHS:
        raise ValueError("MIG_A5_PATH_NOT_ALLOWLISTED")
    f = root / name
    if f.is_symlink() or not f.is_file() or f.stat().st_size > 180000:
        raise ValueError("MIG_A5_INPUT_SOURCE_NOT_SAFE")
    data = f.read_bytes()
    if b"\0" in data or not data.strip():
        raise ValueError("MIG_A5_NON_TEXT_SDK_SOURCE")
    data.decode("utf-8-sig")
    return data


def private_upload(content: bytes, output_dir: Path) -> dict:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    keys = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    if not all(os.environ.get(k) for k in keys):
        raise ValueError("MIG_A5_DRIVE_OAUTH_NOT_CONFIGURED")
    creds = Credentials(token=None, refresh_token=os.environ[keys[0]],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ[keys[1]],
                        client_secret=os.environ[keys[2]])
    creds.refresh(Request())
    api = build("drive", "v3", credentials=creds, cache_discovery=False)
    body = {"name": PRIVATE_NAME, "mimeType": "application/zip",
            "parents": [PRIVATE_PARENT_FOLDER]}
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/zip",
                              resumable=False)
    new = api.files().create(body=body, media_body=media,
                             fields="id,size,name", supportsAllDrives=True).execute(num_retries=3)
    fid = new["id"]
    actual = api.files().get_media(fileId=fid, supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(actual, bytes) or actual != content:
        raise ValueError("MIG_A5_PRIVATE_DRIVE_READBACK_MISMATCH")
    return {"private_drive_file_id": fid,
            "private_drive_url": "https://drive.google.com/file/d/" + fid + "/view",
            "archive_bytes": len(content), "archive_sha256": digest(content),
            "private_readback_pass": True}


def run(fork_dir: Path, output_dir: Path) -> None:
    from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
    from pre105_read_settings_source import drive_client
    from pre107_restore_isolated import restore
    import pre431_v46_source_dual_trace_compat_readonly as v46
    import pre434_build_signed_v47_bmw_passive_diag as p434
    import pre638_build_signed_v50_c3_two_request_diag as v50
    import pre648_v50_shader_pass_counts_arm64_noapk as p648
    import pre652_build_signed_v51_gpu_shader_counts_diag as p652

    if EXPECTED_SHA256 != PIN_PRE99 or p652.SOURCE_SHA != PIN_V51_RENDERER:
        raise ValueError("MIG_A5_PRE99_OR_V51_PIN_CHANGED")
    commit = subprocess.run(["git", "-C", str(fork_dir), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True, timeout=15).stdout.strip()
    if commit != PIN_FORK_COMMIT:
        raise ValueError("MIG_A5_PUBLIC_FORK_COMMIT_DRIFT")
    tracked = set(collect_public_paths(fork_dir))
    if not set(PRIVATE_PATHS).issubset(tracked):
        raise ValueError("MIG_A5_INPUT_SDK_NOT_TRACKED")
    manifest = json.loads((fork_dir / "tools/ci/v51_pre696_pinned_manifest.json").read_text())
    if [x["path"] for x in manifest["files"]] != list(PATHS):
        raise ValueError("MIG_A5_MANIFEST_SET_DRIFT")
    if manifest["source_artifact"]["sha256"] != PIN_REFERENCE_ZIP:
        raise ValueError("MIG_A5_REFERENCE_MANIFEST_DRIFT")
    if manifest["source_artifact"]["replayed_V51_binaries_equivalent_to_signed_APK"] is not False:
        raise ValueError("MIG_A5_BINARY_EQUIVALENCE_UNSAFE")
    verified = json.loads(Path("docs/PRE652_V51_SIGNED_GPU_SHADER_DIAGNOSTIC_VERIFIED.json").read_text())
    apk = verified.get("apk", {})
    if not (verified.get("status") == "SIGNED_AND_DRIVE_VERIFIED"
            and apk.get("sha256") == PIN_APK and apk.get("version_code") == 51
            and apk.get("permanent_certificate_sha256") == PIN_CERT):
        raise ValueError("MIG_A5_V51_APK_REFERENCE_METADATA_DRIFT")
    v50.require_pre637()
    result = {"stage": "MIG_A5_PRIVATE_SDK_INPUT_THREE_WAY_REVIEW",
              "status": "FAIL_CLOSED", "fork_commit": PIN_FORK_COMMIT,
              "pre99_sha256": PIN_PRE99, "v51_renderer_sha256": PIN_V51_RENDERER,
              "scope": "SDK input only: 3 public-fork-tracked text source paths",
              "raw_source_in_github_artifact": False,
              "source_signed_apk_binary_equivalence_proven": False,
              "source_modified_in_fork": False, "apk_built": False,
              "signing_material_read": False, "fps_gain_proven": False, "files": []}
    with tempfile.TemporaryDirectory(prefix="nfsmw_mig_a5_") as t:
        temp = Path(t)
        arc = temp / "pre99.tar.gz"
        download_pre99(drive_client(), arc, EXPECTED_BYTES)
        arc_sha, _, nbytes = sha_file(arc)
        if (arc_sha, nbytes) != (PIN_PRE99, EXPECTED_BYTES):
            raise ValueError("MIG_A5_PRE99_ARCHIVE_AUTHENTICATION_FAIL")
        stage = temp / "restore"
        stage.mkdir()
        restore(arc, stage)
        arc.unlink(missing_ok=True)
        root = stage / "workspace"
        baseline = {name: checked_source(root, name) for name in PRIVATE_PATHS}
        replay = v46.replay_v46_sources(root, Path.cwd())
        if replay["PRE398"].get("cheat_enabled") is not True:
            raise ValueError("MIG_A5_STAGING_PRE398_UNEXPECTED")
        saved_stage = p434.ORIGINAL_STAGE
        def menu_gate(folder: Path):
            cmake = (folder / "nativo/app/CMakeLists.txt").read_text()
            if cmake.count(v46.PRE292_REGISTER) != 1:
                raise ValueError("MIG_A5_MENU_REGISTER_DRIFT")
            return {"menu_registered_once": True}
        try:
            p434.ORIGINAL_STAGE = menu_gate
            staged = v50.stage_v50(root)
        finally:
            p434.ORIGINAL_STAGE = saved_stage
        if not (staged["pre638_v49_source_recipe_verified"] is True
                and staged["pre638_c3_fallback_bypass"] is False
                and staged["pre638_v49_callbacks_nitro_preserved"] is True
                and staged["pre638_save_modified"] is False):
            raise ValueError("MIG_A5_PRE638_STAGE_GUARD_FAIL")
        renderer = (root / "nativo/app/src/nfsmw_nativo_dibujos.cpp").read_bytes()
        backend = (root / "nativo/app/src/nfsmw_nativo_destinos.cpp").read_bytes()
        if digest(renderer) != PIN_V50_RENDERER or digest(p648.patch_bytes(renderer)) != PIN_V51_RENDERER:
            raise ValueError("MIG_A5_PRE648_RENDERER_RECIPE_DRIFT")
        if digest(p648.HEADER.read_bytes()) != p652.HEADER_SHA or digest(backend) != PIN_BACKEND:
            raise ValueError("MIG_A5_V51_BACKEND_GATE_DRIFT")
        # Independent 7-file canaries from MIG-A3 / MIG-A4
        for ref in manifest["files"]:
            raw = (root / ref["path"]).read_bytes()
            if digest(raw) != ref["sha256"] or len(raw) != ref["bytes"]:
                raise ValueError("MIG_A5_V51_CANARY_DRIFT_" + ref["path"])
        after = {name: checked_source(root, name) for name in PRIVATE_PATHS}
        fork = {name: checked_source(fork_dir, name) for name in PRIVATE_PATHS}
        with io.BytesIO() as buf:
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for i,name in enumerate(PRIVATE_PATHS):
                    old, new, pub = baseline[name], after[name], fork[name]
                    if old == new:
                        raise ValueError("MIG_A5_EXPECTED_INPUT_PATCH_MISSING")
                    # Both old and new are text-only Xenia/ReX SDK source files,
                    # not decompiled generated game code, APKs or key material.
                    with tempfile.TemporaryDirectory(prefix="sdk_input_diff_") as dd:
                        basepath, vpath, fpath = (Path(dd)/k for k in ("base","v51","fork"))
                        basepath.write_bytes(old);vpath.write_bytes(new);fpath.write_bytes(pub)
                        h1 = diff_stats(basepath, vpath)["hunks"]
                        h2 = diff_stats(basepath, fpath)["hunks"]
                        m = merge_conflicts(fpath, basepath, vpath)
                    if (h1,h2) != (EXPECTED_HUNKS_V51[i],EXPECTED_HUNKS_FORK[i]):
                        raise ValueError("MIG_A5_A4_HUNK_COUNTS_NOT_REPRODUCED_" + name)
                    if not m["syntactic_merge_clean"]:
                        raise ValueError("MIG_A5_SDK_INPUT_TEXT_CONFLICT")
                    if i < 2 and pub != old:
                        raise ValueError("MIG_A5_BASE_MATCH_FOR_SAFE_FILES_BROKEN")
                    delta = "".join(difflib.unified_diff(
                        old.decode("utf-8-sig").splitlines(keepends=True),
                        new.decode("utf-8-sig").splitlines(keepends=True),
                        fromfile="a/" + name, tofile="b/" + name))
                    if not delta or len(delta) > 20000:
                        raise ValueError("MIG_A5_SDK_INPUT_PRIVATE_DIFF_UNEXPECTED_SIZE")
                    z.writestr("SDK_PRIVATE_DIFFS/" + name + ".patch", delta)
                    z.writestr("SDK_PRIVATE_V51_SOURCES/" + name, new)
                    result["files"].append({
                        "path": name, "pre99_sha256": digest(old),
                        "v51_sha256": digest(new), "fork_sha256": digest(pub),
                        "hunks_v51": h1, "hunks_fork": h2,
                        "fork_identical_to_pre99": pub == old,
                        "merge_textually_clean": True,
                        "private_diff_bytes": len(delta.encode("utf-8"))
                    })
                z.writestr("README.txt", "Private SDK-only V51 patch review. Never publish ZIP in public GitHub Actions artifacts. No generated game source, ISO/XEX, game assets, signing or APK. Reconstructed source is not proven equal to V51 binary.\n")
            private_zip = buf.getvalue()
        with zipfile.ZipFile(io.BytesIO(private_zip)) as verify:
            if verify.testzip() is not None or len(verify.namelist()) != 7:
                raise ValueError("MIG_A5_PRIVATE_ZIP_CRC_OR_ENTRY_COUNT_FAIL")
        uploaded = private_upload(private_zip, output_dir)
        result["private_archive"] = uploaded
        result["status"] = "PASS_PRIVATE_SDK_INPUT_PATCHES_READBACK"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "MIG_A5_SDK_INPUT_REVIEW_METADATA.json").write_text(json.dumps(result, indent=2)+"\n")
    print("MIG_A5_STATUS=PASS_PRIVATE_SDK_INPUT_PATCHES_READBACK")
    print("MIG_A5_SDK_FILES="+str(len(result["files"])))
    print("MIG_A5_PRIVATE_DRIVE_ID="+result["private_archive"]["private_drive_file_id"])
    print("MIG_A5_PRIVATE_ARCHIVE_BYTES="+str(result["private_archive"]["archive_bytes"]))
    print("MIG_A5_PRIVATE_ARCHIVE_SHA256="+result["private_archive"]["archive_sha256"])
    print("MIG_A5_PRIVATE_DRIVE_READBACK=TRUE")
    print("MIG_A5_PUBLIC_RAW_SOURCE_ARTIFACT=FALSE")
    print("MIG_A5_NO_APK=TRUE")


def self_test() -> None:
    assert len(PRIVATE_PATHS) == 3
    assert len(set(PRIVATE_PATHS)) == 3
    assert all(allowed_public_path(n) and n.endswith((".cpp", ".h")) for n in PRIVATE_PATHS)
    assert (EXPECTED_HUNKS_V51, EXPECTED_HUNKS_FORK) == ((2,2,2),(0,0,7))
    with tempfile.TemporaryDirectory() as td:
        a = Path(td)/"a"; b = Path(td)/"b"; c = Path(td)/"c"
        a.write_text("one\nhello\n")
        b.write_text("one\nworld\n")
        c.write_text("one\nhello\n")
        assert diff_stats(a,b)["hunks"] == 1
        assert merge_conflicts(c,a,b)["syntactic_merge_clean"]
    print("MIG_A5_LOCAL_SDK_PATCH_SELF_TEST=PASS")


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
