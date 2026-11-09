#!/usr/bin/env python3
"""PRE570: inspect V48 copiarArbol, prepare and root callgraph, authenticated DEX.
This is only callgraph evidence; never handles game saves or original data.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tempfile,zipfile
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre105_read_settings_source import drive_client
OUT=Path("/tmp/nfsmw-pre570/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
APK_BYTES=47104233
TARGET={
 "MotorNativo":{"traerPartidas","preparar","carpetaUsuario","argumentos","copiarArbol","copiarAsset"},
 "Ajustes":{"carpetaDatos"}
}
SAFE_REF=re.compile(r"(L(?:io/github/nfsmwrecomp|java/io|java/nio/file|android/content|android/net)/[A-Za-z0-9_/$]+;->[A-Za-z0-9_$<>]{1,72})")
def sha_file(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def audit():
 p569=json.loads(Path("docs/PRE569_V48_SAVE_IMPORT_STATIC_READONLY.json").read_text())
 if(p569.get("status")!="AUDIT_OK" or
    p569.get("V48_sha256")!=APK_SHA or
    p569.get("MARCEK_save_isolation_proven") is not False):
  raise ValueError("PRE569 anchored V48 save import code not verified")
 from androguard.core.dex import DEX
 from loguru import logger
 logger.disable("androguard")
 d=drive_client()
 meta=d.files().get(fileId=APK_ID,fields="id,name,size",supportsAllDrives=True).execute()
 if meta.get("id")!=APK_ID or int(meta.get("size",0))!=APK_BYTES:raise ValueError("APK identity changed")
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre570_") as td:
  dst=Path(td)/"orig_v48.apk"
  with dst.open("wb") as f:
   dl=MediaIoBaseDownload(f,d.files().get_media(fileId=APK_ID,supportsAllDrives=True),chunksize=4*1024*1024)
   done=False
   while not done:_,done=dl.next_chunk(num_retries=4)
  if dst.stat().st_size!=APK_BYTES or sha_file(dst)!=APK_SHA:raise ValueError("V48 SHA mismatch")
  result=[]
  with zipfile.ZipFile(dst,"r") as z:
   names=[n for n in z.namelist() if re.fullmatch(r"classes(?:[2-9]\d*)?\.dex",n)]
   if len(names)!=1:raise ValueError("V48 DEX count changed")
   dex=DEX(z.read(names[0]))
   for cls in dex.get_classes():
    full=cls.get_name()
    if not full.startswith("Lio/github/nfsmwrecomp/") or "$" in full:continue
    short=full.rsplit("/",1)[-1].rstrip(";")
    if short not in TARGET:continue
    for method in cls.get_methods():
     name=method.get_name()
     if name not in TARGET[short]:continue
     ins_count=0;call_edges={};safe_literal_signals=[]
     for ins in method.get_instructions():
      ins_count+=1
      if ins_count>15000:raise ValueError("Method exceeds bounded static inspection")
      opcode=ins.get_name()
      if opcode.startswith("invoke-"):
       for edge in SAFE_REF.findall(ins.get_output()):
        if edge not in call_edges:call_edges[edge]=0
        call_edges[edge]+=1
      elif opcode.startswith("const-string"):
       text=ins.get_output().lower()
       for label in ("save","partida","profile","game_data","user_data","--game_data_root","--user_data_root"):
        if label in text and label not in safe_literal_signals:safe_literal_signals.append(label)
     result.append({"class":short,"method":name,"instructions":ins_count,
       "safe_calls":[{"target":k,"count":v} for k,v in sorted(call_edges.items())],
       "literal_signal_labels":safe_literal_signals})
 must={("MotorNativo","traerPartidas"),("MotorNativo","carpetaUsuario"),
       ("MotorNativo","argumentos"),("MotorNativo","copiarArbol"),("Ajustes","carpetaDatos")}
 if not must.issubset({(r["class"],r["method"]) for r in result}):
  raise ValueError("V48 target save import or root method absent")
 transfer=[r for r in result if r["class"]=="MotorNativo" and r["method"]=="traerPartidas"]
 targets=[c["target"] for c in transfer[0]["safe_calls"]]
 return {
  "stage":"PRE570_ORIGINAL_V48_COPIARARBOL_CALLS_STATIC_READONLY",
  "status":"AUDIT_OK","V48_sha256":APK_SHA,
  "methods":result,
  "partidas_method_present":True,
  "partidas_references_app_game_data_root":any("Ajustes;->carpetaDatos" in x for x in targets),
  "partidas_references_native_user_root":any("MotorNativo;->carpetaUsuario" in x for x in targets),
  "partidas_method_actual_save_transfer_proven":False,
  "copy_tree_method_present":True,
  "copy_tree_overwrite_semantics_proven":False,
  "safe_to_run_with_MARCEK":False,
  "V48_active_save_root_on_phone_observed":False,
  "MARCEK_save_isolation_proven":False,
  "guest_loader_executed":False,"BMW_tuning_enabled":False,
  "original_game_or_apk_modified":False,"save_modified":False,"signing_accessed":False
 }
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True);a=ap.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE570_ORIGINAL_V48_COPIARARBOL_CALLS_STATIC_READONLY",
  "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
  "partidas_method_actual_save_transfer_proven":False,
  "copy_tree_overwrite_semantics_proven":False,
  "safe_to_run_with_MARCEK":False,
  "MARCEK_save_isolation_proven":False,
  "guest_loader_executed":False,"BMW_tuning_enabled":False,
  "original_game_or_apk_modified":False,"save_modified":False,"signing_accessed":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE570_STATUS",r["status"],flush=True)
 print("PRE570_TRAERPARTIDAS",r.get("partidas_method_present",False),flush=True)
 print("PRE570_SAVE_ISOLATED",r["MARCEK_save_isolation_proven"],flush=True)
 print("PRE570_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
