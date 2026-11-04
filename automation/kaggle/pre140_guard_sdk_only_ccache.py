#!/usr/bin/env python3
"""PRE140 private SDK C++ cache guard (no secret or game-object scan via content).

The wrapper pins eligible C/C++ units to nativo/sdk/src. This script ensures
the persistent ccache storage is a bounded, symlink-free directory under
RUNNER_TEMP and is sealed with the expected configuration. It NEVER reads
compiler artifacts as text, prints their contents, nor inspects credentials.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

EXPECTED={
    "format_version":1,
    "scope":"only nativo/sdk/src compiler invocations via pre140 wrapper",
    "launcher_git_blob_sha1":"c4949a0adbb788c82b621c7c39fa29baba02b4ae",
    "target_abi":"arm64-v8a",
    "ndk_version":"28.2.13676358",
    "ccache_compiler_check":"content",
    "game_translation_sources_cached":False,
    "signing_material_cached":False,
}
MARKER=".pre140_sdk_only_policy.json"
MAX_BYTES=1536*1024*1024
MAX_FILES=150000
FORBIDDEN=(".p12",".pfx",".jks",".keystore",".apk",".aab",".iso",".obb",
           ".nfsp",".properties",".pem",".key",".sav")
FORBIDDEN_WORDS=("nfsmw", "mostwanted", "most_wanted", "game_usa", "game_pal")

def check(cache_dir:Path,seal:bool)->dict:
    temp=Path(os.environ.get("RUNNER_TEMP","/tmp")).resolve()
    root=cache_dir.absolute()
    if root!=temp/"nfsmw-ccache-sdk-only" or root.is_symlink():
        raise ValueError("ccache path outside dedicated runner temp directory")
    if not root.exists():
        if not seal:raise FileNotFoundError("Warm cache absent")
        root.mkdir(mode=0o700)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("ccache cache is not a regular directory")
    marker=root/MARKER
    if marker.exists() and marker.is_symlink():
        raise ValueError("Untrusted cache marker symlink")
    if marker.exists():
        parsed=json.loads(marker.read_text(encoding="utf-8"))
        if parsed!=EXPECTED:
            raise ValueError("Cache scope marker does not match pinned SDK-only wrapper")
    elif seal:
        marker.write_text(json.dumps(EXPECTED,indent=2)+"\n",encoding="utf-8")
    else:
        raise ValueError("Restored compiler cache lacks scope marker")
    files=0
    total=0
    for current, dirs, names in os.walk(root,followlinks=False):
        folder=Path(current)
        if folder.is_symlink():
            raise ValueError("Unsafe cache directory symlink")
        for name in dirs:
            if (folder/name).is_symlink():
                raise ValueError("Unsafe nested cache directory symlink")
        for name in names:
            path=folder/name
            if path.is_symlink() or not path.is_file():
                raise ValueError("Unsafe cache entry type")
            if name!=MARKER:
                low=name.lower()
                if low.endswith(FORBIDDEN) or any(x in low for x in FORBIDDEN_WORDS):
                    raise ValueError("Forbidden game or signing filename inside ccache")
            files+=1
            total+=path.stat().st_size
            if files>MAX_FILES or total>MAX_BYTES:
                raise ValueError("Cache exceeds SDK-only size policy")
    return {"stage":"PRE140_SDK_ONLY_CCACHE_POLICY",
            "status":"PASS","scope":EXPECTED["scope"],
            "file_count":files,"bytes_total":total,
            "launcher_blob_sha1":EXPECTED["launcher_git_blob_sha1"],
            "game_translation_sources_cached":False,
            "signing_material_cached":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cache-dir",required=True)
    p.add_argument("--mode",choices=("check","seal"),required=True)
    p.add_argument("--report")
    a=p.parse_args()
    report=check(Path(a.cache_dir),seal=a.mode=="seal")
    if a.report:
        out=Path(a.report)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PRE140_SDK_CCACHE_POLICY_PASS",a.mode,
          "files",report["file_count"],"bytes",report["bytes_total"])

if __name__=="__main__":
    main()
