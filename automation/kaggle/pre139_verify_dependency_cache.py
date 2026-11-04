#!/usr/bin/env python3
"""PRE139: enforce GitHub cache allowlist: downloaded Gradle dependencies only.

This guard never reads, prints, archives or modifies game source, APK, keystore,
signing properties or native build outputs. The GitHub cache action paths must
be exact caches/modules-2 and wrapper under RUNNER_TEMP/nfsmw-gradle-home.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import tempfile

BANNED_SUFFIXES=(
    ".apk",".aab",".so",".o",".obj",".a",".p12",".pfx",
    ".jks",".keystore",".iso",".nfsp",".obb",".sav",".pem",".key",
)
BANNED_SUBSTRINGS=("nfsmw","most-wanted","need-for-speed")
TARGETS=("caches/modules-2","wrapper")

def scan(root:Path)->dict:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Invalid Gradle cache home")
    seen=set()
    count=bytes_total=0
    for relative in TARGETS:
        p=root/relative
        if p.is_symlink():
            raise ValueError("Unsafe Gradle cache path")
        if not p.exists():continue
        if not p.is_dir():raise ValueError("Unexpected Gradle cache path type")
        for folder,dirs,files in os.walk(p,followlinks=False):
            base=Path(folder)
            if base.is_symlink():raise ValueError("Gradle cache symlink")
            for item in dirs:
                if (base/item).is_symlink():
                    raise ValueError("Gradle cache directory symlink")
            for item in files:
                current=base/item
                name=item.lower()
                if current.is_symlink():
                    raise ValueError("Gradle cache file symlink")
                if name.endswith(BANNED_SUFFIXES) or any(k in name for k in BANNED_SUBSTRINGS):
                    raise ValueError("Sensitive game/key/native output in dependency-only cache")
                if not current.is_file():raise ValueError("Unsupported Gradle cache entry")
                stat=current.stat()
                count+=1
                bytes_total+=stat.st_size
                if count>200000 or bytes_total>7_000_000_000:
                    raise ValueError("Gradle dependency cache size policy exceeded")
    return {"policy":"dependency_only_modules2_wrapper",
            "verified":True,"file_count":count,"bytes":bytes_total,
            "native_objects_cached":False,"game_sources_cached":False,
            "signing_key_cached":False}

def self_test():
    with tempfile.TemporaryDirectory(prefix="nfsmw_cache_policy_test_") as d:
        root=Path(d)
        p=root/"caches/modules-2"
        p.mkdir(parents=True)
        (p/"test-dependency.jar").write_bytes(b"test")
        assert scan(root)["file_count"]==1
        (p/"original.p12").write_bytes(b"private-not-real")
        try:scan(root)
        except ValueError:pass
        else:raise AssertionError("Banned P12 not caught")
        (p/"original.p12").unlink()
        (p/"nfsmw_game.jar").write_bytes(b"game-not-real")
        try:scan(root)
        except ValueError:pass
        else:raise AssertionError("Game-tagged file not caught")
    print("PRE139_CACHE_POLICY_SELFTEST_PASSED")

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--cache-home")
    cli.add_argument("--self-test",action="store_true")
    cli.add_argument("--report")
    args=cli.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.cache_home:raise ValueError("Cache home required")
    root=Path(args.cache_home).absolute()
    if not root.is_absolute() or root.name!="nfsmw-gradle-home":
        raise ValueError("Unexpected cache root")
    runner=Path(os.environ.get("RUNNER_TEMP","/tmp")).resolve()
    if runner not in root.parents:
        raise ValueError("Cache must be under RUNNER_TEMP")
    outcome=scan(root)
    if args.report:
        out=Path(args.report)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(outcome,indent=2)+"\n",encoding="utf-8")
    print("PRE139_GRADLE_DEPENDENCY_CACHE_POLICY_PASS",
          "files",outcome["file_count"],"bytes",outcome["bytes"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
