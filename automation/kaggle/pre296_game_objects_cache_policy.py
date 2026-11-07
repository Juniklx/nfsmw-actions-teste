#!/usr/bin/env python3
"""PRE296 isolated game-object ccache policy; never touches existing PRE140 cache.
This only validates structural metadata; safe-to-persist real objects is NOT proven.
"""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
MARKER=".nfsmw-game-object-cache-policy.json"
POLICY={"version":1,"kind":"ARM64_GAME_OBJECTS_SEPARATE","game_cache_opt_in_default":False,
        "no_signing_material":True,"no_save_files":True,"private_cache_required":True}
MAX_BYTES=2048*1024*1024
MAX_FILES=200000
FORBIDDEN_SUFFIX=(".apk",".aab",".xex",".iso",".zip",".p12",".pfx",".jks",
                  ".keystore",".properties",".pem",".key",".sav",".nfsp",".cpp",".h")
def check(path:Path,seal:bool):
    root=Path(os.environ.get("RUNNER_TEMP","/tmp")).resolve()
    expected=root/"nfsmw-game-objects"
    if path.absolute()!=expected or path.is_symlink():raise ValueError("cache path not private runner")
    if not path.exists():
        if not seal:raise ValueError("no cache to check")
        path.mkdir(mode=0o700)
    if not path.is_dir() or path.is_symlink():raise ValueError("invalid cache type")
    marker=path/MARKER
    if marker.is_symlink():raise ValueError("marker symlink")
    if marker.exists():
        if json.loads(marker.read_text())!=POLICY:raise ValueError("policy mismatch")
    elif seal:marker.write_text(json.dumps(POLICY,sort_keys=True)+"\n")
    else:raise ValueError("missing policy marker")
    count=size=0
    for parent,dirs,files in os.walk(path,followlinks=False):
        folder=Path(parent)
        if folder.is_symlink():raise ValueError("symlink folder")
        for name in dirs:
            if (folder/name).is_symlink():raise ValueError("nested symlink")
        for name in files:
            p=folder/name
            if p.is_symlink() or not p.is_file():raise ValueError("symlink or odd cache file")
            if name!=MARKER:
                forbidden=name.lower().endswith(FORBIDDEN_SUFFIX)
                if forbidden:raise ValueError("forbidden filename in cache")
            count+=1;size+=p.stat().st_size
            if count>MAX_FILES or size>MAX_BYTES:raise ValueError("cache exceeds bound")
    return {"status":"POLICY_OK","file_count":count,"bytes":size,"real_game_cache_approved":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--path",required=True)
    p.add_argument("--mode",choices=["seal","check"],required=True)
    a=p.parse_args()
    r=check(Path(a.path),a.mode=="seal")
    print("PRE296_CACHE_POLICY",r["status"],r["file_count"],r["bytes"])
if __name__=="__main__":main()
