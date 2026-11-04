#!/usr/bin/env python3
"""PRE102: wait for the isolated Kaggle Drive probe, validating its output report.

No Drive secrets are supplied by GitHub, and no APK/project is modified.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

KERNEL = "juniklx/nfsmw-pre102-drive-probe"
MARKER = "NFSMW_PRE102_DRIVE_PROBE.json"
BAD_STATES = {"ERROR", "FAILED", "CANCELLED", "CANCELED", "CANCEL_REQUESTED", "CANCEL_ACKNOWLEDGED"}


def kaggle(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["kaggle", "kernels", *args], check=False,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=timeout)


def get_state(output: str) -> str | None:
    match = re.search(r"KernelWorkerStatus\.([A-Z_]+)", output)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=720)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.run_id):
        raise ValueError("Run ID must be numeric")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "etapa": "PRE102_KAGGLE_DRIVE_PROBE",
        "github_run_id": args.run_id,
        "kaggle_final_status": "NAO_CONFIRMADO",
        "kaggle_execution_completed": False,
        "drive_backup_metadata_validated": False,
        "result_marker_confirmed": False,
        "result": "NAO_VALIDADO",
        "probe_result": None,
        "probe_checks": {},
    }
    started = time.monotonic()
    last_state = None
    consecutive_invalid = 0
    last_remote_error = None
    try:
        while time.monotonic() - started < args.timeout_seconds:
            status_run = kaggle("status", KERNEL)
            state = get_state(status_run.stdout)
            if state != last_state:
                print("Kaggle PRE102 state:", state or "UNKNOWN", flush=True)
                last_state = state
            if status_run.returncode != 0 or state is None:
                consecutive_invalid += 1
                if consecutive_invalid >= 6:
                    raise RuntimeError("Kaggle status unavailable (6 consecutive checks)")
                time.sleep(12)
                continue
            consecutive_invalid = 0
            report["kaggle_final_status"] = state
            if state in BAD_STATES:
                raise RuntimeError("Kaggle execution terminated with " + state)

            if state == "COMPLETE":
                output = kaggle("output", KERNEL, "-p", str(out), "-o", timeout=120)
                if output.returncode == 0:
                    for path in out.rglob(MARKER):
                        try:
                            data = json.loads(path.read_text(encoding="utf-8"))
                        except (OSError, ValueError):
                            continue
                        if str(data.get("github_run_id")) != args.run_id:
                            continue
                        report["kaggle_execution_completed"] = True
                        report["result_marker_confirmed"] = True
                        report["probe_result"] = str(data.get("status", "NAO_VALIDADO"))[:100]
                        report["probe_checks"] = data.get("verificacoes", {})
                        report["probe_failure_phase"] = data.get("fase_falha")
                        report["probe_failure_type"] = data.get("erro_tipo")
                        report["probe_missing_secret_label"] = data.get("secret_label_indisponivel")
                        if (data.get("etapa") != "PRE102_KAGGLE_DRIVE_PROBE"
                                or data.get("modo") != "SOMENTE_LEITURA"
                                or data.get("backup_restaurado") is not False
                                or data.get("notebook_principal_modificado") is not False
                                or data.get("assinatura_acessada") is not False):
                            raise RuntimeError("PRE102 report safety/identity mismatch")
                        if data.get("status") != "DRIVE_PRE99_METADATA_VALIDADO":
                            print("PRE102 notebook completed but Drive probe not validated:", report["probe_result"])
                            return 1
                        checks = data.get("verificacoes", {})
                        if not isinstance(checks, dict) or not checks or not all(v is True for v in checks.values()):
                            raise RuntimeError("PRE102 checks not fully true")
                        report["drive_backup_metadata_validated"] = True
                        report["result"] = "VALIDADO"
                        print("PRE102 VERIFIED: Kaggle COMPLETE and Drive metadata+manifest verified", flush=True)
                        return 0
                last_remote_error = "Output absent, unavailable or from another run"

            time.sleep(12)
        raise TimeoutError("Timed out waiting for matching Kaggle report")
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error_phase"] = last_remote_error or "Kaggle status/output"
        print("PRE102 verification not completed:", type(exc).__name__)
        return 1
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
