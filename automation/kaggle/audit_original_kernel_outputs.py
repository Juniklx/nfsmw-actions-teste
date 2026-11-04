#!/usr/bin/env python3
"""PRE103A: list saved outputs of the original Kaggle notebook without downloading files.

No credentials are printed. No notebook, Drive file or APK is changed.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

KERNEL = "juniklx/nfsmw"


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["kaggle", "kernels", *args], capture_output=True,
                          text=True, timeout=120, check=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    status = command("status", KERNEL)
    output = command("files", KERNEL, "-v", "--page-size", "200")
    records = []
    parsed = list(csv.reader(io.StringIO(output.stdout)))
    for row in parsed[1:]:
        if not row:
            continue
        text = " ".join(row)
        # Only report file names related to the NFSMW backup, never arbitrary file names.
        if re.search(r"PRE99|NFSMW_V2[56]|NFSMW_APK_EXPERIMENTAIS", text, re.I):
            records.append(text[:280])
    worker = re.search(r"KernelWorkerStatus\.([A-Z_]+)", status.stdout)
    report = {
        "etapa": "PRE103A_AUDITAR_OUTPUT_KAGGLE_ORIGINAL",
        "notebook": KERNEL,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status_query_exit_code": status.returncode,
        "kaggle_worker_status": worker.group(1) if worker else None,
        "file_listing_exit_code": output.returncode,
        "file_listing_first_page_rows": max(len(parsed) - 1, 0),
        "files_page_size": 200,
        "all_output_pages_checked": False,
        "matching_output_files": records,
        "pre99_in_first_page": any("PRE99" in x.upper() for x in records),
        "original_notebook_modified": False,
        "downloaded_files": False,
        "drive_credentials_accessed": False,
    }
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PRE103A: consulta de saidas concluida; linhas da primeira pagina:",
          report["file_listing_first_page_rows"])
    print("PRE103A: correspondencias PRE99 encontradas:", len(records))
    print("PRE103A: status da API:", output.returncode)


if __name__ == "__main__":
    main()
