#!/usr/bin/env python3
"""PRE505: read-only search for original native Android / Xbox asset loader paths.

Authenticates private PRE99 snapshot from Drive. Scans selected first-party
non-generated source files; publishes only capped filenames, source SHA256 and
counts/line numbers for predefined marker families, never source snippets.
PRE99 is an older snapshot: this report cannot verify active V48 loader.
No game assets, APKs, keys, saves, runtime memory or original sources changed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import (
    EXPECTED_SHA256,EXPECTED_BYTES,sha_file,safe_member_name,looks_sensitive
)
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre505/report.json")
PREFIX="workspace/"
INCLUDE=(".cpp",".c",".cc",".cxx",".h",".hpp",".hh",".java",".kt",".kts",".py")
SKIP_SEGMENTS=("/thirdparty/","/generated/","/.git/","/build/","/node_modules/","/tests/","/test/")
MAX_SOURCE_BYTES=2_500_000
MAX_TOTAL_SOURCE_BYTES=150_000_000
MAX_MEMBERS=35000
MAX_FILES_REPORTED=50
# Exact resource marks get priority; broader routing hints are only candidate references.
PATTERNS={
 "attributes_resource":re.compile(r"ATTRIBUTES[./\\]+BIN|GLOBAL[./\\]+ATTRIBUTES",re.I),
 "zdir_resource":re.compile(r"ZDIR(?:[./\\]+BIN)?",re.I),
 "zzdata_resource":re.compile(r"ZZDATA(?:\d+)?(?:[./\\]+BIN)?",re.I),
 "file_redirect_symbols":re.compile(r"file[_ ]?redirect|redirect[_ ]?file|redirect[_ ]?hook",re.I),
 "native_file_calls":re.compile(r"\bfopen\s*\(|\bopen\s*\(|\bSDL_IOFromFile\s*\(|\bCreateFile[AW]?\s*\(",re.I),
 "android_asset_loader":re.compile(r"AAssetManager|AAsset_open|AssetManager|SDL_GetAndroidInternalStoragePath",re.I),
 "guest_disc_path":re.compile(r"game:\\|game:/|XamContent|XContent|XexGet|XexLoad|DiscFile",re.I),
 "game_data_routing":re.compile(r"game[_ ]?data[_ ]?(?:path|dir)|resource[_ ]?(?:path|dir)|game[_ ]?root|base[_ ]?path",re.I),
}
PRIORITY=("attributes_resource","zdir_resource","zzdata_resource","file_redirect_symbols",
          "android_asset_loader","guest_disc_path","game_data_routing","native_file_calls")
def eligible(name,size):
    if not safe_member_name(name) or looks_sensitive(name):return False
    if not name.startswith(PREFIX) or not name.lower().endswith(INCLUDE):return False
    if not (0<size<=MAX_SOURCE_BYTES):return False
    l=name.lower()
    if any(s in l for s in SKIP_SEGMENTS):return False
    # Only first-party trees; PRE99 not the current V48 working tree.
    return l.startswith(("workspace/nativo/app/","workspace/nativo/sdk/src/",
                         "workspace/android/","workspace/nativo/android/",
                         "workspace/nativo/app/src/","workspace/ios/"))
def audit():
    proof=json.loads(Path("docs/PRE504_ORIGINAL_STRE_VLT_COLLECTION_NAME_COVERAGE_READONLY.json").read_text())
    if (proof.get("status")!="AUDIT_OK"
        or proof.get("new_loader_collection_acceptance_proven") is not False
        or proof.get("safe_to_build_tuning_APK") is not False):
        raise ValueError("PRE504 safe source boundary proof not available")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre505_") as scratch:
        archive=Path(scratch)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,bytes_total=sha_file(archive)
        if (digest,bytes_total)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Authenticated PRE99 source archive fingerprint mismatch")
        examined=0;matched=0;read_bytes=0;members=0;hit_rows=[]
        families=Counter();filetype=Counter();bounded_out=False
        with tarfile.open(archive,mode="r:gz",errorlevel=2) as tar:
            for member in tar:
                members+=1
                if members>MAX_MEMBERS:raise ValueError("Unexpected TAR member count")
                if not member.isfile():continue
                name=member.name.lstrip("./")
                if not eligible(name,member.size):continue
                if read_bytes+member.size>MAX_TOTAL_SOURCE_BYTES:
                    bounded_out=True
                    break
                f=tar.extractfile(member)
                if f is None:raise ValueError("Unreadable first-party source")
                raw=f.read()
                if len(raw)!=member.size:raise ValueError("Truncated first-party source")
                read_bytes+=len(raw);examined+=1
                filetype[name.rsplit(".",1)[-1].lower()]+=1
                lines=raw.decode("utf-8","replace").splitlines()
                hits={}
                for label,regex in PATTERNS.items():
                    found=[i+1 for i,line in enumerate(lines) if regex.search(line)]
                    if found:
                        families[label]+=1
                        hits[label]={"matched_line_count":len(found),
                                     "first_lines":found[:12]}
                if hits:
                    matched+=1
                    # filenames, hashes and line indices only: no raw generated source.
                    score=sum((len(PRIORITY)-i)*bool(label in hits)
                              for i,label in enumerate(PRIORITY))
                    hit_rows.append((score,name,{
                        "relative_path":name[:240],
                        "source_sha256":hashlib.sha256(raw).hexdigest(),
                        "source_bytes":len(raw),
                        "marker_families":hits
                    }))
        hit_rows.sort(key=lambda x:(-x[0],x[1]))
        return {
            "stage":"PRE505_PRE99_NATIVE_ASSET_LOADER_SOURCE_PATH_CANDIDATES_READONLY",
            "status":"AUDIT_OK",
            "authenticated_snapshot":"PRE99 (historical; NOT current V48)",
            "authenticated_PRE99_sha256":digest,
            "authenticated_PRE99_bytes":bytes_total,
            "tar_members_examined":members,
            "first_party_files_scanned":examined,
            "first_party_source_bytes_read":read_bytes,
            "bounded_before_full_tree":bounded_out,
            "file_extensions_scanned":dict(filetype),
            "matching_source_files":matched,
            "matching_filenames_reported":min(matched,MAX_FILES_REPORTED),
            "hit_file_counts_by_marker_family":dict(families),
            "first_party_source_candidates":[r for _,_,r in hit_rows[:MAX_FILES_REPORTED]],
            "markers_are_static_text_search_not_loader_semantics":True,
            "active_V48_loader_or_live_bundle_verified":False,
            "BMW_new_ExpN_resolution_in_runtime_verified":False,
            "new_engine_name_registration_required":None,
            "FE_catalog_price_and_purchase_verified":False,
            "game_source_exported":False,"game_assets_exported":False,
            "game_executed":False,"modified_VPAK_written":False,
            "APK_built":False,"save_modified":False,"signing_accessed":False,
            "tuning_enabled":False
        }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    args=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try: report=audit()
    except Exception as ex:
        report={"stage":"PRE505_PRE99_NATIVE_ASSET_LOADER_SOURCE_PATH_CANDIDATES_READONLY",
                "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:240],
                "game_source_exported":False,"game_assets_exported":False,
                "modified_VPAK_written":False,"APK_built":False,
                "save_modified":False,"signing_accessed":False,"tuning_enabled":False}
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE505_STATUS",report["status"],flush=True)
    print("PRE505_SCANNED",report.get("first_party_files_scanned"),flush=True)
    print("PRE505_HIT_FILES",report.get("matching_source_files"),flush=True)
    print("PRE505_HIT_FAMILIES",report.get("hit_file_counts_by_marker_family"),flush=True)
    print("PRE505_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
