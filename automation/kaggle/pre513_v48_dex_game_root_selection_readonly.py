#!/usr/bin/env python3
"""PRE513: authenticated, read-only audit of compiled V48 Android DEX entrypoints.

Find the actual Java classes and method invocation families for game selection,
edition and native arguments in original, SHA-pinned V48 APK. Does not assert
which game root a past phone session selected; no source, binary, save or key
export, no APK rebuild and no runtime execution.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tempfile,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre105_read_settings_source import drive_client
OUT=Path("/tmp/nfsmw-pre513/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
APK_BYTES=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
CLASS_PREFIX="Lio/github/nfsmwrecomp/"
TARGET_CLASS_NAMES={
 "GameActivity","SetupActivity","Ajustes","Ediciones","MotorNativo"
}
STR_MARKERS={
 "native_argv_game_root":"--game_root",
 "native_argv_xex_path":"--xex_path",
 "android_content_scheme":"content://",
 "android_document_action":"android.intent.action.OPEN_DOCUMENT",
 "persisted_uri_permissions":"getPersistedUriPermissions",
 "persistable_uri_permission":"takePersistableUriPermission",
 "android_document_file":"androidx/documentfile/provider/DocumentFile",
 "game_editions_pref":"EDICIONES",
 "game_root_literal":"game_data_root",
 "game_paths_name":"NFSMW_PTBR",
 "get_android_extras":"getStringExtra",
 "activity_libraries":"getLibraries",
}
API_REGEX={
 "android_uri":"Landroid/net/Uri;|Landroid/content/ContentResolver;|Landroid/provider/DocumentsContract;",
 "android_document_picker":"ACTION_OPEN_DOCUMENT|takePersistableUriPermission|getPersistedUriPermissions|Landroidx/documentfile",
 "android_intent":"Landroid/content/Intent;|getIntent\\(|getStringExtra\\(|getParcelableExtra\\(",
 "android_preferences":"Landroid/content/SharedPreferences;|getSharedPreferences\\(",
 "android_files":"Ljava/io/File;|getExternalFilesDir\\(|getFilesDir\\(",
 "sdl_library_selection":"getLibraries\\(|getMainSharedObject\\(|getArguments\\(|loadLibrary\\(",
 "edition_selection":"Lio/github/nfsmwrecomp/Ediciones;|Lio/github/nfsmwrecomp/Ajustes;|edicionAlJugar\\(",
 "xex_or_game_data":"xexIso\\(|getGameData\\(|game_data_root|gameRoot|game_root|xex_path",
}
REGEX={k:re.compile(v,re.I) for k,v in API_REGEX.items()}
KEEP_METHODS={"onCreate","getLibraries","getArguments","getMainSharedObject",
              "edicion","edicionAlJugar","xexIso","deXex","paraJugar",
              "getGameRoot","getGamePath","getGameDataRoot","onActivityResult",
              "getUri","seleccionarJuego","onResume"}
NAME_RE=re.compile(r"^[\w$<>-]{1,100}$")
def audit():
    proof=json.loads(Path("docs/PRE511_ORIGINAL_V48_APK_RUNTIME_MARKERS_READONLY.json").read_text())
    if (proof.get("status")!="AUDIT_OK" or
        proof.get("V48_apk_exact_hash_verified") is not True or
        proof.get("original_apk_sha256")!=APK_SHA or
        proof.get("actual_V48_runtime_mount_branch_observed") is not False):
        raise ValueError("PRE511 V48 binary authenticity proof gate failed")
    from androguard.core.dex import DEX
    from loguru import logger
    logger.disable("androguard")
    drive=drive_client()
    meta=drive.files().get(fileId=APK_ID,
                           fields="id,name,size,mimeType",
                           supportsAllDrives=True).execute()
    if (meta.get("id")!=APK_ID or meta.get("name")!=APK_NAME or
        int(meta.get("size",0))!=APK_BYTES):
        raise ValueError("Unexpected V48 Drive APK identity metadata")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre513_") as td:
        archive=Path(td)/"V48_original_readonly.apk"
        with archive.open("wb") as f:
            reader=MediaIoBaseDownload(
                f,drive.files().get_media(fileId=APK_ID,supportsAllDrives=True),
                chunksize=4*1024*1024)
            done=False
            while not done:
                _,done=reader.next_chunk(num_retries=4)
        if archive.stat().st_size!=APK_BYTES:
            raise ValueError("V48 APK byte count changed")
        apk_sha=hashlib.sha256()
        with archive.open("rb") as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b""):
                apk_sha.update(chunk)
        if apk_sha.hexdigest()!=APK_SHA:
            raise ValueError("V48 exact SHA256 changed")
        entries=[];classes=[];string_matches=Counter();total_methods=0; total_invokes=0
        with zipfile.ZipFile(archive,"r") as zip_file:
            names=[item for item in zip_file.infolist()
                   if re.fullmatch(r"classes(?:[2-9][0-9]*)?\.dex",item.filename)]
            if not names or len(names)>10:raise ValueError("Unexpected V48 DEX entry count")
            for item in names:
                if not 10000<item.file_size<=35000000:
                    raise ValueError("Unexpected V48 DEX expanded size")
                blob=zip_file.read(item)
                if len(blob)!=item.file_size or not blob.startswith(b"dex\n"):
                    raise ValueError("V48 DEX header mismatch")
                dex=DEX(blob)
                pool=dex.get_strings()
                # Bounded boolean markers only, never dump string pool.
                for key,token in STR_MARKERS.items():
                    if token in pool: string_matches[key]+=1
                count=0
                for cls in dex.get_classes():
                    name=cls.get_name()
                    if not name.startswith(CLASS_PREFIX):continue
                    short=name[len(CLASS_PREFIX):].split(";")[0]
                    first=short.split("$")[0]
                    if first not in TARGET_CLASS_NAMES:continue
                    count+=1; methods=[]
                    for method in cls.get_methods():
                        total_methods+=1
                        nm=method.get_name()
                        if not NAME_RE.fullmatch(nm):continue
                        code=method.get_code()
                        invocations=Counter()
                        count_ins=0;count_invoke=0
                        if code:
                            for ins in method.get_instructions():
                                count_ins+=1
                                if count_ins>100000:raise ValueError("Excessive method instruction count")
                                if not ins.get_name().startswith("invoke-"):continue
                                count_invoke+=1;total_invokes+=1
                                out=ins.get_output()
                                for category,regex in REGEX.items():
                                    if regex.search(out):invocations[category]+=1
                        if nm in KEEP_METHODS or invocations:
                            methods.append({
                                "name":nm,
                                "bytecode_present":code is not None,
                                "instruction_count":count_ins,
                                "invoke_family_counts":dict(invocations)
                            })
                    classes.append({
                      "dex_entry":item.filename,
                      "class":first,
                      "is_nested_class":"$" in short,
                      "method_names_observed":[m["name"] for m in methods][:90],
                      "target_method_audit":methods[:80],
                    })
                entries.append({"entry":item.filename,"size":len(blob),
                       "sha256":hashlib.sha256(blob).hexdigest(),
                       "target_classes":count})
        if not any(c["class"]=="GameActivity" for c in classes):
            raise ValueError("V48 compiled GameActivity class not found")
        return {
          "stage":"PRE513_ORIGINAL_V48_ANDROID_DEX_GAME_ROOT_SELECTION_READONLY",
          "status":"AUDIT_OK","apk_drive_id":APK_ID,
          "original_v48_apk_sha256":APK_SHA,"authenticated_apk_byte_size":APK_BYTES,
          "apk_sha256_exactly_verified":True,
          "dex_entries":entries,
          "selected_class_names_exist":sorted({c["class"] for c in classes}),
          "selected_class_count":len(classes),
          "selected_method_count":total_methods,
          "selected_invoke_instruction_count":total_invokes,
          "target_class_method_call_families":classes[:22],
          "literal_marker_dex_presence":{k:v>0 for k,v in string_matches.items()},
          "unrecognized_user_string_values_exported":False,
          "static_compiled_code_review_only":True,
          "source_snapshot_comparison_not_runtime_trace":True,
          "actual_phone_selected_game_root_type":None,
          "actual_phone_selected_game_root_path":None,
          "actual_phone_edition_or_shared_object_verified":False,
          "game_file_mount_observed":False,
          "loader_ZDIR_checksum_semantics_verified":False,
          "tuning_purchase_proven":False,
          "apk_or_game_data_modified":False,
          "binary_or_raw_dex_uploaded":False,
          "apk_built":False,"save_modified":False,
          "release_signing_key_accessed":False,"tuning_enabled":False}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    args=parser.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:report=audit()
    except Exception as exc:
        report={"stage":"PRE513_ORIGINAL_V48_ANDROID_DEX_GAME_ROOT_SELECTION_READONLY",
                "status":"FAILED","error_type":type(exc).__name__,
                "error":str(exc)[:250],
                "apk_or_game_data_modified":False,
                "binary_or_raw_dex_uploaded":False,
                "apk_built":False,"save_modified":False,
                "release_signing_key_accessed":False,"tuning_enabled":False}
    report["run_id"]=args.run_id
    report["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE513_STATUS",report["status"],flush=True)
    print("PRE513_CLASSES",report.get("selected_class_names_exist"),flush=True)
    print("PRE513_DEX_MARKERS",report.get("literal_marker_dex_presence"),flush=True)
    print("PRE513_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    raise SystemExit(main())
