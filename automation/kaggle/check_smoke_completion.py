#!/usr/bin/env python3
"""PRE101: check Kaggle's *completed* execution and correlate the output with GitHub run ID.

Only reads the isolated Kaggle smoke-test notebook. Never touches the real NFSMW kernel.
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

KERNEL = "juniklx/nfsmw-automacao-smoke-pre100"
MARKER = "NFSMW_PRE100_SMOKE_RESULTADO.json"
TERMINAL_FAILURES = {"ERROR", "CANCEL_REQUESTED", "CANCEL_ACKNOWLEDGED", "FAILED", "CANCELLED", "CANCELED"}


def cli(*arguments: str, timeout: int = 50) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["kaggle", "kernels", *arguments], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, check=False)


def parsed_status(output: str) -> str | None:
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
        raise ValueError("run-id must be digits")

    report_file = Path(args.report)
    output_dir = Path(args.output_dir)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    last_printed = None
    mismatched_output = False
    consecutive_failures = 0
    report: dict = {
        "etapa": "PRE101_KAGGLE_SMOKE_EXECUTION_VERIFY",
        "github_run_id": args.run_id,
        "notebook": KERNEL,
        "kaggle_final_status": "NAO_CONFIRMADO",
        "kaggle_execution_completed": False,
        "result_marker_confirmed": False,
        "resultado": "PENDENTE",
        "timestamp_utc": None,
    }

    try:
        while time.monotonic() - started < args.timeout_seconds:
            check = cli("status", KERNEL)
            state = parsed_status(check.stdout)
            if state != last_printed:
                print(f"Kaggle status: {state or 'DESCONHECIDO'}", flush=True)
                last_printed = state
            if check.returncode != 0 or state is None:
                consecutive_failures += 1
                if consecutive_failures >= 6:
                    raise RuntimeError("Kaggle CLI status indisponivel em seis consultas consecutivas")
                time.sleep(12)
                continue
            consecutive_failures = 0
            report["kaggle_final_status"] = state

            if state in TERMINAL_FAILURES:
                # The CLI may briefly display the previous version; retry to be safe.
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    raise RuntimeError(f"Kaggle returned terminal failure: {state}")
            elif state == "COMPLETE":
                output = cli("output", KERNEL, "-p", str(output_dir), "-o", timeout=120)
                if output.returncode == 0:
                    candidates = list(output_dir.rglob(MARKER))
                    for candidate in candidates:
                        try:
                            data = json.loads(candidate.read_text(encoding="utf-8"))
                        except (ValueError, OSError):
                            continue
                        if str(data.get("github_run_id")) != args.run_id:
                            mismatched_output = True
                            continue
                        if (data.get("etapa") != "PRE100_KAGGLE_AUTOMACAO_SMOKE"
                                or data.get("status") != "EXECUTADO"
                                or data.get("altera_projeto") is not False
                                or data.get("chaves_acessadas") is not False):
                            raise RuntimeError("Smoke marker content failed its safety checks")
                        report.update({
                            "kaggle_final_status": "COMPLETE",
                            "kaggle_execution_completed": True,
                            "result_marker_confirmed": True,
                            "resultado": "VALIDADO",
                            "smoke_output_file": MARKER,
                        })
                        print("PRE101 OK: Kaggle COMPLETE + result marker from current GitHub run", flush=True)
                        return 0
                print("Kaggle terminou, aguardando saida correspondente a esta execucao", flush=True)

            time.sleep(12)

        raise TimeoutError("Tempo limite sem comprovacao de execucao e marcador"
                           + ("; saida antiga detectada" if mismatched_output else ""))
    except Exception as exc:
        report["resultado"] = "NAO_VALIDADO"
        report["erro"] = str(exc)[:500]
        print("PRE101 SEM VALIDACAO:", type(exc).__name__, flush=True)
        return 1
    finally:
        report["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
