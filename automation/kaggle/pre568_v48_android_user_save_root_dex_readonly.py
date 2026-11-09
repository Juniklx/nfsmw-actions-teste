#!/usr/bin/env python3
"""PRE568: read-only save-root versus game-data-root path audit of exact V48 DEX.
No APK rebuild, device queries, save reads, binary publication, or log of paths.
This is static Android bytecode only and cannot prove safe runtime isolation.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tempfile, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre568/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
APK_BYTES=47104233
TARGETS={
 "MotorNativo":{"carpetaUsuario","carpetaCache","argumentos"},
 "Ajustes":{"carpetaDatos","carpetaLogs","gamertag","guardarMisAjustes","argumentos"},
 "GameActivity":{"getArguments","getLibraries","onCreate"},
}
CALLS={
 "external_app_files":r"getExternalFilesDir\b",
 "private_files":r"getFilesDir\b",
 "cache_files":r"getCacheDir\b|getExternalCacheDir\b",
 "files_constructor":r"Ljava/io/File;-><init>|Ljava/io/File;->getAbsolutePath",
 "file_create_dirs":r"Ljava/io/File;->mkdirs",
 "android_preferences":r"Landroid/content/SharedPreferences;",
 "native_args":r"Lio/github/nfsmwrecomp/MotorNativo;->argumentos",
 "native_user_root":r"Lio/github/nfsmwrecomp/MotorNativo;->carpetaUsuario",
 "native_cache_root":r"Lio/github/nfsmwrecomp/MotorNativo;->carpetaCache",
 "app_data_root":r"Lio/github/nfsmwrecomp/Ajustes;->carpetaDatos",
 "app_log_root":r"Lio/github/nfsmwrecomp/Ajustes;->carpetaLogs",
 "game_library_selector":r"getLibraries\b|Lio/github/nfsmwrecomp/Ediciones;",
 "content_uri":r"ContentResolver;|Landroid/net/Uri;|openContentFd",
}
REGEX={k:re.compile(v) for k,v in CALLS.items()}
# Only predeclared, harmless argument strings are reported; no dynamic path.
SAFE_FLAGS=("--user_dir","--user-dir","--user_data_root",
            "--content_root","--storage_root","--save_dir",
            "--game_data_root","--data_root","--profile")

def sha_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for data in iter(lambda: f.read(4*1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def audit():
    prev=json.loads(Path("docs/PRE515_V48_DEX_GAME_ROOT_METHOD_REFS_READONLY.json").read_text())
    if (prev.get("status")!="AUDIT_OK" or prev.get("v48_apk_sha256")!=APK_SHA
        or prev.get("selected_game_edition_runtime_proven") is not False):
        raise ValueError("PRE515 V48 DEX boundary missing")
    from androguard.core.dex import DEX
    from loguru import logger
    logger.disable("androguard")
    gd=drive_client()
    meta=gd.files().get(fileId=APK_ID,fields="id,name,size",supportsAllDrives=True).execute()
    if meta.get("id")!=APK_ID or int(meta.get("size",0))!=APK_BYTES:
        raise ValueError("Exact V48 source APK identity or size unexpected")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre568_") as folder:
        dst=Path(folder)/"verified_v48.apk"
        with dst.open("wb") as f:
            request=gd.files().get_media(fileId=APK_ID,supportsAllDrives=True)
            download=MediaIoBaseDownload(f,request,chunksize=4*1024*1024)
            done=False
            while not done:
                _,done=download.next_chunk(num_retries=3)
        if dst.stat().st_size!=APK_BYTES or sha_file(dst)!=APK_SHA:
            raise ValueError("V48 hash differs from authenticated PRE513")
        matches=[]
        reverse=Counter()
        static_flags=Counter()
        with zipfile.ZipFile(dst,"r") as z:
            dex_entries=[x for x in z.infolist() if re.fullmatch(r"classes(?:[2-9]\d*)?\.dex",x.filename)]
            if not dex_entries or len(dex_entries)>12:
                raise ValueError("V48 DEX entry count ambiguous")
            for dexinfo in dex_entries:
                dex=DEX(z.read(dexinfo))
                for cls in dex.get_classes():
                    path=cls.get_name()
                    if not path.startswith("Lio/github/nfsmwrecomp/") or "$" in path:
                        continue
                    short=path.rsplit("/",1)[-1].rstrip(";")
                    for m in cls.get_methods():
                        name=m.get_name()
                        selected=short in TARGETS and name in TARGETS[short]
                        if not selected and short not in ("MotorNativo","Ajustes","GameActivity","SetupActivity"):
                            continue
                        counts=Counter()
                        ins_count=0
                        for ins in m.get_instructions():
                            ins_count+=1
                            if ins_count>18000: raise ValueError("Unexpected huge Android method")
                            opcode=ins.get_name()
                            if opcode.startswith("invoke-"):
                                op=ins.get_output()
                                for k,rx in REGEX.items():
                                    if rx.search(op):counts[k]+=1
                                if "Lio/github/nfsmwrecomp/MotorNativo;->carpetaUsuario" in op:
                                    reverse[(short,name,"user_root")]+=1
                                if "Lio/github/nfsmwrecomp/Ajustes;->carpetaDatos" in op:
                                    reverse[(short,name,"game_data_root")]+=1
                            elif selected and opcode.startswith("const-string"):
                                # No arbitrary strings or paths in output.
                                for flag in SAFE_FLAGS:
                                    if flag in ins.get_output():
                                        static_flags[flag]+=1
                        if selected:
                            matches.append({
                                "class":short,"method":name,
                                "instruction_count":ins_count,
                                "call_family_counts":dict(counts)
                            })
    present={(x["class"],x["method"]) for x in matches}
    must={("MotorNativo","carpetaUsuario"),("MotorNativo","carpetaCache"),
          ("Ajustes","carpetaDatos"),("Ajustes","gamertag"),
          ("Ajustes","argumentos"),("GameActivity","getArguments")}
    if not must.issubset(present):
        raise ValueError("Missing relevant current V48 save/game path class methods")
    user=[x for x in matches if x["class"]=="MotorNativo" and x["method"]=="carpetaUsuario"]
    game=[x for x in matches if x["class"]=="Ajustes" and x["method"]=="carpetaDatos"]
    return {
      "stage":"PRE568_EXACT_V48_ANDROID_USER_ROOT_VS_GAME_ROOT_STATIC_DEX",
      "status":"AUDIT_OK",
      "exact_original_v48_apk_sha256":APK_SHA,
      "exact_original_v48_apk_bytes":APK_BYTES,
      "targeted_class_methods_found":len(matches),
      "selected_methods":matches,
      "recognized_safe_literal_flags":dict(static_flags),
      "referencing_callers": [
        {"class":k[0],"method":k[1],"reference":k[2],"calls":v}
        for k,v in sorted(reverse.items())
      ],
      "current_v48_native_user_root_method_exists":len(user)>0,
      "current_v48_game_data_root_method_exists":len(game)>0,
      "current_v48_user_root_source_uses_private_or_external_dir_apis":
         any(x["call_family_counts"].get("private_files",0)>0 or
             x["call_family_counts"].get("external_app_files",0)>0 for x in user),
      "actual_android_game_data_root_observed":False,
      "actual_android_save_root_observed":False,
      "save_profile_MARCEK_read":False,
      "safe_disposable_profile_isolation_proven":False,
      "same_package_separate_profile_testing_safe":False,
      "guest_loader_executed":False,
      "BMW_tuning_enabled":False,
      "APK_built":False,
      "original_apk_modified":False,
      "save_modified":False,
      "game_assets_modified":False,
      "credential_accessed":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE568_EXACT_V48_ANDROID_USER_ROOT_VS_GAME_ROOT_STATIC_DEX",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
           "actual_android_save_root_observed":False,
           "safe_disposable_profile_isolation_proven":False,
           "guest_loader_executed":False,"BMW_tuning_enabled":False,
           "APK_built":False,"original_apk_modified":False,
           "save_modified":False,"game_assets_modified":False}
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE568_STATUS",r["status"],flush=True)
    print("PRE568_USER_ROOT_METHOD",r.get("current_v48_native_user_root_method_exists",False),flush=True)
    print("PRE568_SAVE_ISOLATION_PROVEN",r.get("safe_disposable_profile_isolation_proven",False),flush=True)
    print("PRE568_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
