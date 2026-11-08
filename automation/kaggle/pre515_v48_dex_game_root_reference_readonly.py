#!/usr/bin/env python3
"""PRE515: method-level DEX reference audit of V48 Android game-root routing.

Uses authenticated PRE513 V48 APK fingerprint and Androguard to list only
bounded, sanitized method/field reference metadata from relevant app methods.
No source or binary redistribution; no app execution, keys, APK patch or save
writes. Static bytecode cannot prove runtime selected URI versus folder.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tempfile,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre105_read_settings_source import drive_client
OUT=Path("/tmp/nfsmw-pre515/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_BYTES=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
TARGETS={
 "Ajustes":{"uriIso","argumentos","edicion","iso"},
 "Ediciones":{"deXex","paraJugar"},
 "GameActivity":{"getArguments","getLibraries","openContentFd","onCreate"},
 "MotorNativo":{"argumentos"},
 "SetupActivity":{"edicionAlJugar","onActivityResult","onCreate","lanzarJuego",
                  "jugar","abrirIso","seleccionarIso"},
}
TOKENS={
 "uri_class":r"Landroid/net/Uri;|Landroid/content/ContentResolver;",
 "saf_picker":r"DocumentsContract;|takePersistableUriPermission|getPersistedUriPermissions",
 "android_activity_intent":r"Landroid/content/Intent;|->getIntent\(|->getStringExtra\(",
 "file_path":r"Ljava/io/File;|Landroidx/documentfile",
 "edition_dataflow":r"Lio/github/nfsmwrecomp/Ediciones;|Lio/github/nfsmwrecomp/Ajustes;",
 "native_args":"Lio/github/nfsmwrecomp/MotorNativo;|getArguments\\(|getLibraries\\(",
 "platform_environment":r"getExternalFilesDir|getFilesDir|openFileDescriptor",
}
RX={k:re.compile(v,re.I) for k,v in TOKENS.items()}
REF_RE=re.compile(r"(L(?:io/github/nfsmwrecomp|android|androidx|java/io|org/libsdl)/[A-Za-z0-9_/$]+;->(?:[A-Za-z0-9_$<>]{1,80}))")
SECRET_RE=re.compile(r"(?i)(?:secret|password|token|credential|authorization|passphrase|key_store|signing)")
def audit():
    p13=json.loads(Path("docs/PRE513_ORIGINAL_V48_ANDROID_DEX_GAME_ROOT_SELECTION_READONLY.json").read_text())
    if (p13.get("status")!="AUDIT_OK" or
        p13.get("original_v48_apk_sha256")!=APK_SHA or
        p13.get("apk_sha256_exactly_verified") is not True or
        p13.get("game_file_mount_observed") is not False):
        raise ValueError("PRE513 authenticated compiled-source boundary proof missing")
    from androguard.core.dex import DEX
    from loguru import logger
    logger.disable("androguard")
    client=drive_client()
    meta=client.files().get(fileId=APK_ID,fields="id,size,name",supportsAllDrives=True).execute()
    if meta.get("id")!=APK_ID or int(meta.get("size",0))!=APK_BYTES:
        raise ValueError("V48 APK Drive identity or size changed")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre515_") as td:
        archive=Path(td)/"v48_original_readonly.apk"
        with archive.open("wb") as fp:
            d=MediaIoBaseDownload(fp,client.files().get_media(fileId=APK_ID,
                      supportsAllDrives=True),chunksize=4*1024*1024)
            finished=False
            while not finished:
                _,finished=d.next_chunk(num_retries=4)
        if archive.stat().st_size!=APK_BYTES:
            raise ValueError("APK size mismatch")
        h=hashlib.sha256()
        with archive.open("rb") as fp:
            for b in iter(lambda: fp.read(4*1024*1024),b""):
                h.update(b)
        if h.hexdigest()!=APK_SHA: raise ValueError("V48 SHA-256 mismatch")
        results=[]
        with zipfile.ZipFile(archive,"r") as z:
            dex_entries=[x for x in z.infolist() if re.fullmatch(r"classes(?:[2-9]\d*)?\.dex",x.filename)]
            if not 1<=len(dex_entries)<=12: raise ValueError("Unexpected DEX count")
            for dex_entry in dex_entries:
                raw=z.read(dex_entry)
                if len(raw)!=dex_entry.file_size or len(raw)>35000000:
                    raise ValueError("DEX expansion or read mismatch")
                dex=DEX(raw)
                for cls in dex.get_classes():
                    name=cls.get_name()
                    if not name.startswith("Lio/github/nfsmwrecomp/") or "$" in name:
                        continue
                    short=name.split("/")[-1].rstrip(";")
                    if short not in TARGETS:continue
                    for method in cls.get_methods():
                        meth=method.get_name()
                        if meth not in TARGETS[short]:continue
                        instrs=method.get_instructions()
                        invokes=Counter();fields=Counter();families=Counter();bytecodes=0
                        for ins in instrs:
                            bytecodes+=1
                            if bytecodes>20000:raise ValueError("Method too large")
                            opcode=ins.get_name()
                            if not opcode.startswith(("invoke-","iget-","iput-","sget-","sput-")):
                                continue
                            output=ins.get_output()
                            for k,rx in RX.items():
                                if rx.search(output):families[k]+=1
                            for candidate in REF_RE.findall(output):
                                if SECRET_RE.search(candidate):continue
                                if len(candidate)>165:continue
                                if opcode.startswith("invoke-"):invokes[candidate]+=1
                                else:fields[candidate]+=1
                        results.append({"class":short,"method":meth,
                           "bytecode_instruction_count":bytecodes,
                           "known_call_family_counts":dict(families),
                           "invoked_safe_methods":[{"target":k,"count":v}
                               for k,v in invokes.most_common(90)],
                           "referenced_safe_fields":[{"field":k,"count":v}
                               for k,v in fields.most_common(90)]})
    if not any(x["class"]=="GameActivity" and x["method"]=="getLibraries"
               for x in results):
        raise ValueError("Missing V48 GameActivity.getLibraries bytecode")
    if not any(x["class"]=="Ajustes" and x["method"]=="uriIso"
               for x in results):
        raise ValueError("Missing V48 Ajustes.uriIso bytecode")
    return {
      "stage":"PRE515_AUTHENTICATED_V48_JAVA_GAME_ROOT_METHOD_REFERENCE_AUDIT",
      "status":"AUDIT_OK","v48_apk_sha256":APK_SHA,
      "exact_apk_hash_verified_again":True,
      "dex_mapped_methods_reviewed":len(results),
      "method_level_source_reference_evidence":results,
      "method_targets_limited_to_static_allowlist":True,
      "original_app_uses_uri_capable_java_routines":True,
      "actual_android_session_game_root_path":None,
      "actual_android_session_mount_type":None,
      "selected_game_edition_runtime_proven":False,
      "kernel_vfs_branch_executed_proven":False,
      "BMW_runtime_VPAK_loaded":False,"BMW_tuning_usable":False,
      "apk_or_game_resources_modified":False,
      "dex_or_apk_contents_published":False,
      "apk_built":False,"save_modified":False,
      "signing_key_accessed":False
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE515_AUTHENTICATED_V48_JAVA_GAME_ROOT_METHOD_REFERENCE_AUDIT",
           "status":"FAILED","error_type":type(exc).__name__,
           "error":str(exc)[:250],
           "apk_or_game_resources_modified":False,
           "dex_or_apk_contents_published":False,
           "apk_built":False,"save_modified":False,
           "signing_key_accessed":False}
    r["run_id"]=a.run_id;r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE515_STATUS",r["status"],flush=True)
    print("PRE515_METHODS",r.get("dex_mapped_methods_reviewed"),flush=True)
    print("PRE515_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
