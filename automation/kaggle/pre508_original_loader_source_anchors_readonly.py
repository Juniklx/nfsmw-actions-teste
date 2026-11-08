#!/usr/bin/env python3
"""PRE508 -- bounded targeted historical Android/guest asset loader source review.

Only authenticated user-owned PRE99 historical sources are read in RAM.
Print short, redacted context excerpts to private Actions logs; report is metadata
only (hashes/line matches/tokens). Never export any source, game asset, APK, save,
key, PIN, token, or live V48 data. This cannot establish V48 loader behavior.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre508/report.json")
ROOT="workspace/"
TARGETS={
 "android_nativo":{
   "path":"android/app/src/main/cpp/nativo/nativo_android.cpp",
   "sha":"0453fea3ec0ca4a5e4ce4e926e3b1d1fd46dc38a402d89ba73a400afc7b7ad73",
   "anchors":[537]},
 "guest_xboxkrnl_io":{
   "path":"nativo/sdk/src/kernel/xboxkrnl/xboxkrnl_io.cpp",
   "sha":"40869526201fbed631b7bb506c83680edc02b2f4a6701f31a19b1a068c622015",
   "anchors":[84,444,445,531]},
 "host_path":{
   "path":"nativo/sdk/src/filesystem/devices/host_path_file.cpp",
   "sha":"7dace8159023592ee8008a3798aea6a1856bc8e003492b9c4cce65346",
   "anchors":[123,160,164,448]},
 "virtual_fs":{
   "path":"nativo/sdk/src/filesystem/virtual_file_system.cpp",
   "sha":"a3e89c5d85f899d9756750fcf2dcc47b21cb5afc96f71c1804fc35544902bc9d",
   "anchors":[20,218,219,220,337]},
}
REDACT=re.compile(r"(?i)(?:password|passphrase|client_secret|refresh_token|private_key|oauth|credential|authorization|kaggle_secret|api[_-]?key)")
KINDS={
 "global_attributes":r"ATTRIBUTES[.\\/]BIN",
 "zdir":r"\bZDIR\b",
 "zzdata":r"ZZDATA",
 "zip_archive":r"\bzip\b|\.zip",
 "file_redirect":r"file.?redirect|redirect.?file|redirect.?hook",
 "fopen":r"\bfopen\s*\(",
 "file_read":r"\b(read|fread|pread|ReadFile|ReadAsync|OpenFile|CreateFile)\s*\(",
 "file_path_mapping":r"ResolvePath|MountPath|device_path|host_path|FileSystem|NormalizePath",
 "android_external":r"getExternalFilesDir|Android|/storage|AAssetManager|AssetManager",
}
REGEX={k:re.compile(v,re.I) for k,v in KINDS.items()}
def protected(line):
    if REDACT.search(line):return "[SENSITIVE SOURCE LINE REDACTED]"
    line=line.replace("\t","  ").strip()
    return line[:158]+("..." if len(line)>158 else "")
def audit():
    history=json.loads(Path("docs/PRE505_PRE99_NATIVE_ASSET_LOADER_PATHS_READONLY.json").read_text())
    if history.get("status")!="AUDIT_OK" or history.get("active_V48_loader_or_live_bundle_verified") is not False:
        raise ValueError("Authenticated PRE505 historical source gate unavailable")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre508_") as td:
        archive=Path(td)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,byte_count=sha_file(archive)
        if (digest,byte_count)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 authenticated archive hash/length mismatch")
        by_path={ROOT+v["path"]:k for k,v in TARGETS.items()}
        sources={}
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if name not in by_path:continue
                key=by_path[name];expected=TARGETS[key]
                if not m.isfile() or not (0<m.size<250000):
                    raise ValueError("Unsafe or oversized source "+key)
                reader=tar.extractfile(m)
                if reader is None:raise ValueError("Missing source stream "+key)
                raw=reader.read()
                if len(raw)!=m.size or hashlib.sha256(raw).hexdigest()!=expected["sha"]:
                    raise ValueError("Source fingerprint differs from PRE505 "+key)
                sources[key]=raw.decode("utf-8","replace").splitlines()
        if set(sources)!=set(TARGETS):
            raise ValueError("One or more PRE505 pinned sources missing")
        result=[]
        for key,expected in TARGETS.items():
            lines=sources[key]
            src_lines=[]
            for line_num in expected["anchors"]:
                if line_num<1 or line_num>len(lines):raise ValueError("Anchor line outside source "+key)
                s=max(1,line_num-5);e=min(len(lines),line_num+5)
                # Print short, redacted context to private ephemeral runner logs.
                print("PRE508_BOUNDED_PRIVATE_CONTEXT",key,"anchor",line_num,"range",s,e,flush=True)
                for n in range(s,e+1):
                    print(f"PRE508_SRC_{key}:{n:05d} {protected(lines[n-1])}",flush=True)
                print("PRE508_END_CONTEXT",key,line_num,flush=True)
                window="\n".join(lines[s-1:e])
                src_lines.append({"line":line_num,
                         "window_start":s,"window_end":e,
                         "window_marker_matches":{k:bool(rx.search(window)) for k,rx in REGEX.items()},
                         "anchor_sha256":hashlib.sha256(lines[line_num-1].encode()).hexdigest()})
            result.append({"key":key,"historical_path":ROOT+expected["path"],
               "sha256_matches_PRE505":True,"historical_source_sha256":expected["sha"],
               "source_line_count":len(lines),"anchor_contexts":src_lines})
        return {"stage":"PRE508_HISTORICAL_ANDROID_GUEST_ASSET_LOADER_SOURCE_CONTEXT",
            "status":"AUDIT_OK",
            "source_snapshot":"PRE99 verified historical snapshot, not V48",
            "snapshot_sha256":digest,
            "target_pinned_source_file_count":len(TARGETS),
            "source_anchor_review":result,
            "excerpt_log_type":"small redacted human-authored source windows in private runner logs only",
            "long_source_or_game_data_exported":False,
            "source_semantics_manually_reviewed":False,
            "actual_V48_loader_or_mount_verified":False,
            "new_engine_collection_runtime_accepted":False,
            "ZDIR_checksum_semantics_verified":False,
            "BMW_tuning_purchase_runtime_verified":False,
            "any_game_asset_modified":False,"APK_built":False,
            "save_modified":False,"signing_accessed":False,"mod_enabled":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as ex:r={
        "stage":"PRE508_HISTORICAL_ANDROID_GUEST_ASSET_LOADER_SOURCE_CONTEXT",
        "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:220],
        "long_source_or_game_data_exported":False,
        "any_game_asset_modified":False,"APK_built":False,"save_modified":False,
        "signing_accessed":False,"mod_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE508_STATUS",r["status"],flush=True)
    print("PRE508_PINNED_SOURCES",r.get("target_pinned_source_file_count"),flush=True)
    print("PRE508_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
