#!/usr/bin/env python3
"""PRE684: read-only V51 static recipe, PAL/USA markers and PRE656 shader-frequency audit.

This is NOT an exact recompile/replay, a live CVAR read, frame pacing test,
per-shader GPU timing test, performance optimization or a release build.
Private APK and runtime log stay in private Drive and the ephemeral runner.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import statistics
import tempfile
import zipfile

APK_ID = "1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws"
APK_BYTES = 47104417
APK_SHA256 = "207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
LOG_ID = "1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
LOG_BYTES = 576129
LOG_SHA256 = "649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
PRIVATE_OUTPUT = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
CERT_SHA256 = "1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
DIR = Path("automation/kaggle")
RECIPE_FILE = DIR / "pre652_build_signed_v51_gpu_shader_counts_diag.py"
PROBE_FILE = DIR / "pre648_v50_shader_pass_counts_arm64_noapk.py"
HEADER_FILE = DIR / "pre648_shader_pass_counter.h"
V50_FILE = DIR / "pre638_build_signed_v50_c3_two_request_diag.py"
V49_FILE = DIR / "pre626_build_signed_v49_bmw_attr_diag.py"
GATE_FILE = Path("docs/PRE651_V51_GPU_RELEASE_PREFLIGHT_VERIFIED.json")
DRAW = re.compile(
    r"PRE648 GPU_SHADER10s draws=(\d+) normal=(\d+) deferred_sky=(\d+) invalid=(\d+) top="
)
TOP = re.compile(r"\[p(\d+) VS(\d+) PS(\d+) n(\d+)\]")
TIMING_CATEGORIES = {
    "scene": "escena", "copies": "copias",
    "cube_and_blur_combined": "320 (cubo y desenfoque)",
    "shadows": "sombras", "reflections": "reflejo",
    "gap_between_works": "hueco entre trabajos",
}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def pin(raw: bytes, expected_size: int, expected_sha256: str, label: str) -> None:
    if len(raw) != expected_size or sha(raw) != expected_sha256:
        raise ValueError("PRE684_PIN_MISMATCH_" + label)

def function(module: ast.Module, name: str) -> ast.FunctionDef:
    matches = [f for f in module.body if isinstance(f, ast.FunctionDef) and f.name == name]
    if len(matches) != 1:
        raise ValueError("PRE684_FUNCTION_MISSING_OR_DUPLICATED_" + name)
    return matches[0]

def assignment(module: ast.Module, name: str):
    candidates = [
        node.value for node in module.body
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        )
    ]
    if len(candidates) != 1:
        raise ValueError("PRE684_RECIPE_CONSTANT_" + name)
    return ast.literal_eval(candidates[0])

def calls(func: ast.FunctionDef, qualified: str) -> list[ast.Call]:
    result = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        receiver = node.func.value
        if isinstance(receiver, ast.Name) and receiver.id + "." + node.func.attr == qualified:
            result.append(node)
    return result

def recipe_audit():
    required = [RECIPE_FILE, PROBE_FILE, HEADER_FILE, V50_FILE, V49_FILE, GATE_FILE]
    for path in required:
        if not path.is_file():
            raise ValueError("PRE684_REQUIRED_PINNED_RECIPE_FILE_MISSING: " + str(path))
    preflight = json.loads(GATE_FILE.read_text(encoding="utf-8"))
    recipe = ast.parse(RECIPE_FILE.read_text(encoding="utf-8"))
    v50 = ast.parse(V50_FILE.read_text(encoding="utf-8"))
    v49 = ast.parse(V49_FILE.read_text(encoding="utf-8"))
    values = {x: assignment(recipe, x) for x in (
        "VERSION", "SOURCE_SHA", "HEADER_SHA", "EXPECTED_CERT", "EXPECTED_PACKAGE"
    )}
    if values["VERSION"] != 51:
        raise ValueError("PRE684_VERSION_MISMATCH")
    if values["EXPECTED_CERT"] != CERT_SHA256 or values["EXPECTED_PACKAGE"] != "io.github.nfsmwrecomp":
        raise ValueError("PRE684_PERMANENT_IDENTITY_MISMATCH")
    if not (
        preflight.get("stage") == "PRE651_V51_GPU_RELEASE_PREFLIGHT"
        and preflight.get("status") == "AUDIT_OK_NO_APK"
        and preflight.get("preflight_approved") is True
        and preflight.get("target_version_code") == 51
        and preflight.get("package_id") == values["EXPECTED_PACKAGE"]
        and preflight.get("certificate_sha256") == values["EXPECTED_CERT"]
        and preflight.get("approved_source_sha256") == values["SOURCE_SHA"]
        and preflight.get("approved_counter_header_sha256") == values["HEADER_SHA"]
        and preflight.get("signing_material_accessed") is False
        and preflight.get("apk_built") is False
        and preflight.get("fps_gain_proven") is False
    ):
        raise ValueError("PRE684_PRE651_GATE_MISMATCH")
    if sha(HEADER_FILE.read_bytes()) != values["HEADER_SHA"]:
        raise ValueError("PRE684_COUNTER_HEADER_PIN_MISMATCH")
    stage = function(recipe, "stage_v51")
    stage_calls = calls(stage, "v50.stage_v50")
    shader_calls = calls(stage, "shader.patch_bytes")
    if len(stage_calls) != 1 or len(shader_calls) != 1 or stage_calls[0].lineno >= shader_calls[0].lineno:
        raise ValueError("PRE684_V50_STAGE_ONCE_BEFORE_GPU_PATCH_NOT_VERIFIED")
    # This is structural auditing of code, not executing or certifying the source tree.
    if assignment(v50, "VERSION") != 50 or assignment(v49, "VERSION") != 49:
        raise ValueError("PRE684_V49_V50_VERSION_CHAIN_MISMATCH")
    for filename in (PROBE_FILE, V50_FILE, V49_FILE):
        ast.parse(filename.read_text(encoding="utf-8"))
    return {
        "pre651_gate_github_run": preflight["github_run_id"],
        "release_recipe_script_sha256": sha(RECIPE_FILE.read_bytes()),
        "pre648_probe_script_sha256": sha(PROBE_FILE.read_bytes()),
        "approved_pre652_candidate_source_sha256": values["SOURCE_SHA"],
        "approved_pre648_header_sha256": values["HEADER_SHA"],
        "pre638_pinned_v50_sha256": assignment(v50, "PIN_PRE635"),
        "pre638_pinned_pre99_sha256": assignment(v50, "PIN_PRE99"),
        "version_chain": [49, 50, 51],
        "v50_staged_before_shader_patch": True,
        "v50_stage_call_count_in_v51": 1,
        "pre648_patch_call_count_in_v51": 1,
        "actual_v51_rebuild_or_source_tree_replay_done": False,
        "signing_key_accessed": False,
    }

def inspect_apk(apk: bytes):
    pin(apk, APK_BYTES, APK_SHA256, "V51_APK")
    with zipfile.ZipFile(io.BytesIO(apk)) as z:
        if z.testzip() is not None:
            raise ValueError("PRE684_BAD_APK_ZIP_CRC")
        so_files = [name for name in z.namelist() if name.endswith(".so")]
        marker = b"PRE648 GPU_SHADER10s"
        occurrences = {
            name: z.read(name).count(marker) for name in so_files
            if z.read(name).count(marker)
        }
        if occurrences != {"lib/arm64-v8a/libmain.so": 1}:
            raise ValueError("PRE684_SIGNED_APK_PRE648_MARKER_SCOPE_CHANGED")
        libs = {}
        for name in ("lib/arm64-v8a/libmain.so", "lib/arm64-v8a/libmain_usa.so"):
            lib = z.read(name)
            libs[name] = {
                "sha256": sha(lib),
                "bytes": len(lib),
                "pre648_marker_count": lib.count(marker),
                "native_graphic_option_names_present": all(
                    key.encode("ascii") in lib for key in (
                        "nfsmw_nativo_sin_desenfoque",
                        "nfsmw_nativo_pcf_barato",
                        "nfsmw_sombras_sin_vegetacion",
                        "nfsmw_nativo_sombras_escala",
                        "nfsmw_sombras_corte",
                    )
                )
            }
            if not libs[name]["native_graphic_option_names_present"]:
                raise ValueError("PRE684_NATIVE_GRAPHIC_FLAGS_MISSING")
    return {"apk_sha256": APK_SHA256, "zip_crc": "PASS", "native_libraries": libs}

def inspect_log(raw: bytes):
    pin(raw, LOG_BYTES, LOG_SHA256, "PRE656_LOG")
    text = raw.decode("utf-8", "replace")
    lines = text.splitlines()
    window_records = []
    top = Counter()
    for line in lines:
        if "PRE648 GPU_SHADER10s" not in line:
            continue
        match = DRAW.search(line)
        if not match:
            raise ValueError("PRE684_UNPARSEABLE_SHADER_FREQUENCY_WINDOW")
        draws, normal, deferred_sky, invalid = map(int, match.groups())
        if draws != normal + deferred_sky + invalid:
            raise ValueError("PRE684_SHADER_WINDOW_ACCOUNTING_MISMATCH")
        pairs = TOP.findall(line)
        if not (1 <= len(pairs) <= 12):
            raise ValueError("PRE684_TOP_PAIR_REPORT_SCHEMA_MISMATCH")
        for category, vs, ps, n in pairs:
            top[(int(category), int(vs), int(ps))] += int(n)
        window_records.append({
            "time": line[1:24], "draws": draws, "normal": normal,
            "deferred_sky": deferred_sky, "invalid": invalid,
            "reported_top_pair_count": len(pairs),
            "reported_top_pair_draw_count": sum(int(n) for _, _, _, n in pairs),
        })
    if len(window_records) != 14:
        raise ValueError("PRE684_EXPECTED_14_GPU_SHADER_WINDOWS")
    count_sum = sum(w["draws"] for w in window_records)
    if count_sum != 14265243 or sum(w["deferred_sky"] for w in window_records) != 7097:
        raise ValueError("PRE684_LOG_COUNT_TOTAL_CHANGED")
    timing_rows = [line for line in lines if "C2: GPU por Swap:" in line]
    if len(timing_rows) != 7:
        raise ValueError("PRE684_C2_TIMING_SAMPLE_COUNT_CHANGED")
    metrics = {}
    for key, label in TIMING_CATEGORIES.items():
        pattern = re.compile(re.escape(label) + r" (\d+\.\d+)")
        values = []
        for line in timing_rows:
            match = pattern.search(line)
            if not match:
                raise ValueError("PRE684_GPU_TIMING_FIELD_MISSING: " + key)
            values.append(float(match.group(1)))
        metrics[key] = {
            "median_ms": round(statistics.median(values), 3),
            "min_ms": min(values),
            "max_ms": max(values),
            "sample_count": len(values),
        }
    top_eight = [
        {"category_id": category, "vs_id": vs, "ps_id": ps, "reported_top8_draws": count}
        for (category, vs, ps), count in top.most_common(8)
    ]
    return {
        "original_log_sha256": LOG_SHA256,
        "pre648_frequency_windows": len(window_records),
        "pre648_total_recorded_draws": count_sum,
        "pre648_normal_draws": sum(w["normal"] for w in window_records),
        "pre648_deferred_sky_draws": sum(w["deferred_sky"] for w in window_records),
        "pre648_invalid_shader_ids": sum(w["invalid"] for w in window_records),
        "pre648_first_last_times": [window_records[0]["time"], window_records[-1]["time"]],
        "pre648_reported_top_pairs_lower_bound_total": sum(top.values()),
        "pre648_pairs_reported_per_window": [w["reported_top_pair_count"] for w in window_records],
        "pre648_most_frequent_reported_pairs": top_eight,
        "c2_gpu_per_swap_samples": len(timing_rows),
        "c2_gpu_per_swap_window_median_ms": metrics,
        "pre648_counter_observed_in_device_log": True,
        "loaded_library_exact_mapping_proved": False,
        "individual_shader_gpu_cost_measured": False,
        "frame_pacing_measured": False,
    }

def client():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    names = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError("PRE684_MISSING_GITHUB_SECRETS: " + ", ".join(missing))
    creds = Credentials(
        token=None, refresh_token=os.environ[names[0]],
        client_id=os.environ[names[1]], client_secret=os.environ[names[2]],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def download(drive, fid):
    from googleapiclient.http import MediaIoBaseDownload
    stream = io.BytesIO()
    request = MediaIoBaseDownload(
        stream, drive.files().get_media(fileId=fid), chunksize=4 * 1024 * 1024
    )
    complete = False
    while not complete:
        _, complete = request.next_chunk()
    return stream.getvalue()

def main():
    static_recipe = recipe_audit()
    drive = client()
    apk = inspect_apk(download(drive, APK_ID))
    log = inspect_log(download(drive, LOG_ID))
    report = {
        "gate": "PRE684_V51_RECIPE_AND_PRE656_SHADER_FREQUENCY_READONLY",
        "status": "PASS_STATIC_RECIPE_PINS_AND_HISTORIC_GPU_LOG",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe": static_recipe,
        "apk": apk,
        "pre656": log,
        "limits": {
            "source_tree_replayed_or_arm64_compiled": False,
            "new_signed_apk": False,
            "gpu_time_per_shader_measured": False,
            "runtime_graphic_cvars_verified": False,
            "full_120fps_or_perceptual_smoothness_measured": False,
            "pixel_fidelity_proven": False,
            "fps_improved": False,
        },
        "next_action": (
            "Prioritize a passive first-start CVar/argv audit; do not reapply "
            "shader or graphics changes before exact staging and signed-release gates."
        ),
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    from googleapiclient.http import MediaFileUpload
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre684_") as tmp:
        name = "NFSMW_PRE684_V51_RECIPE_SHADER_FREQUENCY_" + stamp + ".zip"
        path = Path(tmp) / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("PRE684_REPORT.json", json.dumps(report, indent=2, sort_keys=True))
            z.writestr("PRE684_README.md",
                       "Read-only recipe reference checks, authentic V51 PAL/USA marker split,\n"
                       "and PRE656 14-window GPU draw count analysis.\n"
                       "No exact replay, new APK, per-shader GPU timing or FPS gain.\n")
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError("PRE684_REPORT_ZIP_CRC_MISMATCH")
        item = drive.files().create(
            body={"name": name, "parents": [PRIVATE_OUTPUT]},
            media_body=MediaFileUpload(str(path), mimetype="application/zip", resumable=True),
            fields="id,size",
        ).execute()
        if item.get("size") != str(path.stat().st_size):
            raise ValueError("PRE684_REPORT_UPLOAD_SIZE_MISMATCH")
        if sha(download(drive, item["id"])) != sha(path.read_bytes()):
            raise ValueError("PRE684_PRIVATE_REPORT_READBACK_SHA_MISMATCH")
    print("PRE684_RECIPE_STRUCTURAL_PIN_CHECK=PASS")
    print("PRE684_V51_PAL_ONLY_PRE648_MARKER=CONFIRMED")
    print("PRE684_PRE656_SHADER_14_WINDOWS=PASS")
    print("PRE684_PRIVATE_DRIVE_READBACK=PASS")
    print("PRE684_SOURCE_REPLAY_AND_LIVE_CVARS=NOT_PERFORMED")
    print("PRE684_APK_BUILD_OR_FPS_GAIN=NONE")

if __name__ == "__main__":
    main()
