#!/usr/bin/env python3
"""PRE511: authenticate unchanged signed V48 APK and inspect first-party ELF markers.

Read original published APK from private Drive; verify exact size/SHA256,
inspect only zipped ARM64 library names/hashes and bounded static ASCII
markers for the VFS runtime. Never repackage, resign, publish APK/binaries,
enable tuning, execute the game, access a signing key or touch saves.
Presence of binary text is not proof that the branch executed on Android.
"""
from __future__ import annotations
import argparse,hashlib,json,tempfile,zipfile
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre105_read_settings_source import drive_client
OUT=Path("/tmp/nfsmw-pre511/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
APK_SIZE=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
PINS={
 "history_runtime_image_root":b"game_data_root es una imagen de disco",
 "history_runtime_absent_root":b"Runtime::SetupVfs: game_data_root does not exist",
 "history_runtime_path_failed":b"Failed to initialize game data device",
 "history_runtime_host_mount":b"Failed to register host path device",
 "history_hostpath_device":b"HostPathDevice",
 "history_discimage_device":b"DiscImageDevice",
 "history_allow_guest_game_writes":b"allow_game_relative_writes",
 "guest_data_root_symbol":b"game_data_root",
 "archive_zzdata":b"ZZDATA",
 "archive_zdir":b"ZDIR.BIN",
 "archive_attributes":b"ATTRIBUTES.BIN",
 "guest_path":b"game://",
}
TARGET_LIBRARIES={
 "lib/arm64-v8a/librexruntime.so",
 "lib/arm64-v8a/libmain.so",
 "lib/arm64-v8a/libmain_usa.so",
 "lib/arm64-v8a/libfile_redirect_hook.so",
}
def audit():
    client=drive_client()
    metadata=client.files().get(fileId=APK_ID,
       fields="id,name,size,mimeType,md5Checksum",supportsAllDrives=True).execute()
    if (metadata.get("id")!=APK_ID or metadata.get("name")!=APK_NAME
        or int(metadata.get("size",0))!=APK_SIZE
        or metadata.get("mimeType")!="application/vnd.android.package-archive"):
        raise ValueError("V48 original Drive metadata identity mismatch")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre511_") as td:
        p=Path(td)/"original_v48_for_readonly_audit.apk"
        with p.open("wb") as fp:
            request=client.files().get_media(fileId=APK_ID,supportsAllDrives=True)
            downloader=MediaIoBaseDownload(fp,request,chunksize=4*1024*1024)
            done=False
            while not done:
                _,done=downloader.next_chunk(num_retries=4)
        actual_len=p.stat().st_size
        actual_hash=hashlib.sha256(p.read_bytes()).hexdigest()
        if (actual_len,actual_hash)!=(APK_SIZE,APK_SHA):
            raise ValueError("Published V48 APK original SHA256/size failed")
        with zipfile.ZipFile(p,"r") as z:
            entries=z.infolist()
            names={i.filename for i in entries}
            selected=[]
            if "lib/arm64-v8a/librexruntime.so" not in names:
                raise ValueError("V48 cannot verify required librexruntime.so")
            for item in entries:
                if item.filename not in TARGET_LIBRARIES:continue
                if item.file_size<=0 or item.file_size>200_000_000:
                    raise ValueError("Suspicious native shared object size")
                if item.compress_size<=0 or item.file_size>max(item.compress_size,1)*100:
                    raise ValueError("Suspicious library compression expansion")
                data=z.read(item)
                if len(data)!=item.file_size or data[:4]!=b"\x7fELF":
                    raise ValueError("Invalid extracted-in-RAM ELF file")
                markers={k:{"present":v in data,"occurrences":data.count(v)}
                         for k,v in PINS.items()}
                selected.append({"zip_entry":item.filename,
                  "uncompressed_bytes":len(data),
                  "sha256":hashlib.sha256(data).hexdigest(),
                  "target_marker_presence":markers})
            if len(selected)<2:raise ValueError("Missing native ARM64 libraries")
        runtime=next(t for t in selected if t["zip_entry"].endswith("/librexruntime.so"))
        return {"stage":"PRE511_ORIGINAL_V48_APK_NATIVE_VFS_BINARY_MARKER_CROSSCHECK",
         "status":"AUDIT_OK",
         "original_drive_file_id":APK_ID,
         "original_apk_name":APK_NAME,
         "original_apk_size":actual_len,
         "original_apk_sha256":actual_hash,
         "V48_apk_exact_hash_verified":True,
         "apk_zip_member_total":len(entries),
         "available_arm64_library_count":sum(n.startswith("lib/arm64-v8a/") and n.endswith(".so") for n in names),
         "selected_library_count":len(selected),
         "native_library_marker_results":selected,
         "historical_runtime_diagnostic_markers_present":{
              k:runtime["target_marker_presence"][k]["present"] for k in
              ("history_runtime_image_root","history_runtime_absent_root",
               "history_runtime_path_failed","history_runtime_host_mount",
               "history_allow_guest_game_writes")},
         "static_string_search_only_no_disassembly_or_execution":True,
         "presence_not_proof_of_runtime_branch_or_selected_game_folder":True,
         "actual_V48_runtime_mount_branch_observed":False,
         "V48_VPAK_experiment_installed":False,
         "ZDIR_checksum_algorithm_identified":False,
         "BMW_tuning_available_or_bought":False,
         "original_game_or_apk_modified":False,
         "raw_apk_or_native_binary_uploaded":False,
         "APK_built":False,"save_modified":False,
         "signing_key_accessed":False,"tuning_enabled":False}
def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    args=a.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:d=audit()
    except Exception as e:d={"stage":"PRE511_ORIGINAL_V48_APK_NATIVE_VFS_BINARY_MARKER_CROSSCHECK",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
      "original_game_or_apk_modified":False,"raw_apk_or_native_binary_uploaded":False,
      "APK_built":False,"save_modified":False,"signing_key_accessed":False,
      "tuning_enabled":False}
    d["run_id"]=args.run_id;d["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
    print("PRE511_STATUS",d["status"],flush=True)
    print("PRE511_APK_SHA_OK",d.get("V48_apk_exact_hash_verified"),flush=True)
    print("PRE511_RUNTIME_MARKERS",d.get("historical_runtime_diagnostic_markers_present"),flush=True)
    print("PRE511_ERROR",d.get("error_type","none"),d.get("error",""),flush=True)
    return 0 if d["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
