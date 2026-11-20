#!/usr/bin/env python3
"""PRE746: exact USA guest CatchUp routine/callers and global singleton.

Only original PRE99 SHA-pinned. Original code excerpts may be stored ONLY in
private Drive. No game asset, public artifact, signing, build or edits.
"""
import argparse,hashlib,json,re,tarfile,tempfile
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID,EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
SOURCES=re.compile(r"^workspace/nativo/app_usa/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
HOST=re.compile(r"^workspace/nativo/app_usa/src/.*\.(?:cpp|h)$")
FUN=re.compile(rb"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)\s*\{")
TARGET="sub_823328C0"
LIMIT=400*1024*1024
RAW_TARGET_MAX=30000
RAW_CALLER_MAX=40000
CALL=re.compile(rb"(?<![A-Za-z0-9_])(?:__imp__)?sub_823328C0\s*\(ctx,\s*base\)")
VAR=re.compile(rb"g_nfsmw_android_contexto(?:\s*\[\s*11\s*\])?\s*=")
GVAR_LITERAL=re.compile(rb"\b0x82[A-Fa-f0-9]{6}\b")
def digest(b):return hashlib.sha256(b).hexdigest()

def scan(file):
  result={
    "stage":"PRE746_USA_AUTHENTICATED_GUEST_CATCHUP_CONTROLLER_CALL_GRAPH",
    "original_pre99_sha256_verified":True,
    "usa_target":TARGET,
    "usa_target_definition":None,"direct_callers":[],
    "host_singleton_candidate":[],
    "usa_functions_scanned":0,"usa_shards_scanned":0,"byte_count":0,
    "usa_codegen_edition":"app_usa","guest_asset_modified":False,
    "apk_built":False,"signing_accessed":False,"runtime_validation":False,
  }
  with tarfile.open(file,"r:gz",errorlevel=2) as tf:
    for m in tf:
      if not m.isfile():continue
      if HOST.match(m.name) and m.size<=2*1024*1024:
        f=tf.extractfile(m)
        if not f:continue
        with f:d=f.read()
        for match in VAR.finditer(d):
            result["host_singleton_candidate"].append({
             "source_file":m.name,
             "matched_decl":d[match.start():match.start()+520].decode("utf-8","replace"),
             "context":"private_source_only"})
      if not SOURCES.fullmatch(m.name):continue
      if not 0<m.size<=24*1024*1024:raise ValueError("Unexpected source file size")
      result["byte_count"]+=m.size
      if result["byte_count"]>LIMIT:raise ValueError("Scan exceeded budget")
      f=tf.extractfile(m)
      if not f:raise ValueError("Guest source inaccessible")
      with f:data=f.read()
      result["usa_shards_scanned"]+=1
      defs=list(FUN.finditer(data))
      for i,fn in enumerate(defs):
        name=fn.group(1).decode()
        body=data[fn.end():(defs[i+1].start() if i+1<len(defs) else len(data))]
        result["usa_functions_scanned"]+=1
        if name==TARGET:
          if result["usa_target_definition"] is not None:raise ValueError("Duplicate USA target function")
          result["usa_target_definition"]={
            "function":name,"sha256":digest(body),"body_len":len(body),
            "source":m.name,"body":body[:RAW_TARGET_MAX].decode("utf-8","replace")}
        if name==TARGET:continue
        matches=list(CALL.finditer(body))
        if not matches:continue
        result["direct_callers"].append({
          "function":name,"source":m.name,"sha256":digest(body),"body_len":len(body),
          "call_count":len(matches),"body":body[:RAW_CALLER_MAX].decode("utf-8","replace"),
          "truncated":len(body)>RAW_CALLER_MAX
        })
  if not result["usa_target_definition"] or not result["direct_callers"]:
    result["crosswalk_pass"]=False
  else:
    result["crosswalk_pass"]=True
  return result

def main():
  p=argparse.ArgumentParser();p.add_argument("--report",type=Path,required=True)
  o=p.parse_args()
  d=drive_client()
  with tempfile.TemporaryDirectory(prefix="nfsmw-pre746-") as td:
    backup=Path(td)/"PRE99.tar.gz"
    meta=d.files().get(fileId=BACKUP_ID,fields="id,size").execute()
    if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
      raise ValueError("PRE99 Drive metadata mismatch")
    download(d,backup)
    sha,_md5,size=sha_file(backup)
    if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
      raise ValueError("PRE99 archive SHA mismatch")
    result=scan(backup)
  o.report.parent.mkdir(parents=True,exist_ok=True)
  o.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  print("PRE746_USA_TARGET_FOUND="+str(result["usa_target_definition"] is not None))
  print("PRE746_USA_CALLERS="+json.dumps({v["function"]:v["call_count"] for v in result["direct_callers"]}))
  print("PRE746_HOST_SINGLETON_DECLS="+str(len(result["host_singleton_candidate"])))
  print("PRE746_CROSSWALK_PASS="+str(result["crosswalk_pass"]))
  name="NFSMW_PRE746_USA_CATCHUP_CONTROLLER_CALLER_PRIVATE.json"
  up=d.files().create(body={"name":name,"parents":[FOLDER],"mimeType":"application/json"},
        media_body=MediaFileUpload(str(o.report),mimetype="application/json"),
        fields="id,name,parents").execute()
  if up.get("name")!=name or FOLDER not in up.get("parents",[]):
     raise ValueError("Private report identity mismatch")
  print("PRE746_REPORT_DRIVE_ID="+up["id"])
  print("PRE746_NO_PATCH_NO_BUILD_NO_SIGNING")
  if not result["crosswalk_pass"]:raise SystemExit(2)
if __name__=="__main__":main()
