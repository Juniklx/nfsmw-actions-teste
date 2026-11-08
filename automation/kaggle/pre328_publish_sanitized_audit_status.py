#!/usr/bin/env python3
"""PRE328: publish allowlisted CI audit status to the GitHub repository.

No credential, file name, memory address, exception text, raw scan hits,
user log, backup content, or signing data is included in committed summary.
Requires GITHUB_TOKEN issued to this GitHub Actions run.
"""
from __future__ import annotations
import argparse
import base64
import datetime
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

SCHEMA = {
    "PRE325": {
        "status", "pal_shards_scanned", "other_source_files_scanned",
        "matches_truncated", "owner_verified", "indirect_dispatch_verified",
    },
    "PRE388": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE373": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE369": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE356": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE354": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE345": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE342": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE339": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE338": {"status", "owner_verified"},
    "PRE337": {"status", "owner_verified"},
    "PRE336": {"status", "owner_verified"},
    "PRE335": {"status", "readback", "backup_created", "backup_unchanged", "context_bytes"},
    "PRE334": {"status", "pal_shards_scanned", "functions_qualified", "nitro_shaped_candidates", "owner_verified"},
    "PRE333": {"status", "pal_shards_scanned", "candidate_count", "candidate_functions", "candidates_truncated", "owner_verified"},
    "PRE332": {"status", "methods_found", "nitro_present", "owner_verified"},
    "PRE327": {
        "status", "files_inspected", "bytes_inspected",
        "oversize_or_budget_skips", "matches_truncated",
        "owner_verified", "dispatch_verified",
    },
}
NUMBERS = {"pal_shards_scanned", "other_source_files_scanned", "files_inspected",
           "bytes_inspected", "oversize_or_budget_skips", "methods_found", "candidate_count", "candidate_functions", "functions_qualified", "nitro_shaped_candidates", "context_bytes"}
BOOLEANS = {"matches_truncated", "owner_verified", "indirect_dispatch_verified",
            "dispatch_verified", "nitro_present", "candidates_truncated", "readback", "backup_created", "backup_unchanged"}
VALID_STATUSES = {"AUDIT_OK", "FAILED", "SYNC_OK", "ALREADY_PRESENT"}


def sanitized_report(stage: str, source: object, run_id: str, commit: str) -> dict:
    result = {
        "stage": stage, "status": "NO_REPORT",
        "github_run_id": run_id, "source_commit": commit,
        "read_only": stage not in ("PRE335", "PRE339", "PRE342", "PRE345", "PRE354", "PRE356", "PRE369", "PRE373", "PRE388"), "apk_built": False,
        "owner_proven": False, "result_is_not_player_owner_proof": True,
    }
    if not isinstance(source, dict):
        return result
    result["status"] = source.get("status") if source.get("status") in VALID_STATUSES else "INVALID_STATUS"
    for name in sorted(SCHEMA[stage] - {"status"}):
        value = source.get(name)
        if name in NUMBERS and type(value) is int and 0 <= value <= 10**10:
            result[name] = value
        if name in BOOLEANS and type(value) is bool:
            result[name] = value
    # Never promote underlying audit's owner flags to positive evidence here.
    result["owner_proven"] = False
    return result


def publish(repo: str, branch: str, path: str, token: str, payload: dict) -> None:
    endpoint = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "nfsmw-pre328-audit-status",
    }
    existing_sha = None
    get = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(get, timeout=20) as response:
            existing_sha = json.load(response).get("sha")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    raw = (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()
    data = {
        "message": f"PRE328 publish sanitized {payload['stage']} audit status [skip ci]",
        "branch": branch,
        "content": base64.b64encode(raw).decode("ascii"),
    }
    if existing_sha:
        data["sha"] = existing_sha
    put = urllib.request.Request(endpoint, headers=headers,
              data=json.dumps(data).encode(), method="PUT")
    with urllib.request.urlopen(put, timeout=30) as response:
        if response.status not in (200, 201):
            raise RuntimeError("Status publish failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=sorted(SCHEMA), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raw = None
    if args.report.is_file() and args.report.stat().st_size <= 1024 * 1024:
        try:
            raw = json.loads(args.report.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            raw = None
    runid = os.environ["GITHUB_RUN_ID"]
    sha = os.environ["GITHUB_SHA"]
    summary = sanitized_report(args.stage, raw, runid, sha)
    path = f"docs/generated/PRE328_{args.stage}_SANITIZED_STATUS.json"
    publish(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_REF_NAME"], path,
            os.environ["GITHUB_TOKEN"], summary)
    print("PRE328_PUBLISH", args.stage, summary["status"], path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
