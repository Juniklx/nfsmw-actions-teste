#!/usr/bin/env python3
"""PRE191: authenticated, read-only inspection of NFSMW Android Java edition selection.
Never logs secrets, game resources, full game sources, or any signing material.
Does not compile, patch, change settings, or touch APKs.
"""
from __future__ import annotations

import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre191-java-edition-readonly")
PREFIX = "workspace/android/app/src/main/java/"
WANTED = (
    "io/github/nfsmwrecomp/Ediciones.java",
    "io/github/nfsmwrecomp/GameActivity.java",
    "io/github/nfsmwrecomp/Ajustes.java",
)
TERMS = (
    "ediciones", "edicion", "loadlibrary", "getlibraries", "getmainsharedobject",
    "libmain", "loadso", "sharedpreferences", "getarguments", "sdlactivity",
    "nativeinit", "oncreate", "main_usa", "pal_es", "seleccionar",
    "selectededition", "edition", "getid", "nativolibrary",
)
DENY = ("password", "refresh_token", "client_secret", "private_key",
        "keystore", "credential", "access_token")

def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def select_lines(lines: list[str], relevant: list[int], radius: int = 3) -> list[dict]:
    indexed = set()
    for p in relevant[:120]:
        for k in range(max(0, p - radius), min(len(lines), p + radius + 1)):
            indexed.add(k)
    kept = []
    for k in sorted(indexed):
        line = lines[k].rstrip()[:260]
        if any(x in line.lower() for x in DENY):
            line = "<redacted>"
        kept.append({"line": k + 1, "text": line})
    return kept[:550]

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pre191_java_") as tmp:
        path = Path(tmp) / "pre99.tar.gz"
        download(drive_client(), path)
        digest, _, length = sha_file(path)
        if digest != EXPECTED_SHA256 or length != EXPECTED_BYTES:
            raise ValueError("PRE191: authenticated PRE99 backup hash mismatch")
        candidates = []
        selected = {}
        with tarfile.open(path, "r:gz") as tar:
            for member in tar:
                name = member.name.lstrip("./")
                if not member.isfile() or not name.startswith(PREFIX):
                    continue
                if not name.endswith(".java") or member.size > 300_000:
                    continue
                f = tar.extractfile(member)
                if f is None:
                    continue
                blob = f.read()
                lines = blob.decode("utf-8", "replace").splitlines()
                hits = [i for i, line in enumerate(lines)
                        if any(term in line.lower() for term in TERMS)
                        and not any(term in line.lower() for term in DENY)]
                if hits or name.endswith(WANTED):
                    candidates.append({
                        "path": name,
                        "sha256": sha(blob),
                        "total_lines": len(lines),
                        "matching_lines": len(hits),
                        "context_lines": select_lines(lines, hits, radius=5 if name.endswith(WANTED) else 2),
                    })
                if name.endswith(WANTED):
                    selected[name.split("/")[-1]] = True
        missing = [x for x in WANTED if x.split("/")[-1] not in selected]
        if missing:
            raise ValueError("PRE191: required Java source file missing")
        candidates.sort(key=lambda x: (0 if x["path"].endswith(WANTED) else 1,
                                       -x["matching_lines"], x["path"]))
        report = {
            "stage": "PRE191_AUTHENTICATED_JAVA_RUNTIME_EDITION_SOURCE_AUDIT",
            "read_only": True,
            "pre99_sha256_verified": True,
            "pre99_archive_bytes": length,
            "script_did_not_build_apk": True,
            "script_did_not_modify_source": True,
            "script_did_not_access_release_key": True,
            "source_is_historical_pre99": True,
            "v35_runtime_edition_still_unproven": True,
            "note": "PRE99 Java may have been patched after restore; compare V35 patch chain before inferring runtime behavior.",
            "java_files_matching": len(candidates),
            "sources": candidates[:80],
        }
    output = OUT / "NFSMW_PRE191_JAVA_EDITION_AUDIT.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PRE191_READONLY_SUCCESS")
    print("PRE191_AUTHENTICATED_PRE99_SHA256", EXPECTED_SHA256)
    print("PRE191_JAVA_MATCHING", len(candidates))
    print("PRE191_RUNTIME_EDITION_PROVEN", False)
    print("PRE191_REPORT", output)

if __name__ == "__main__":
    main()
