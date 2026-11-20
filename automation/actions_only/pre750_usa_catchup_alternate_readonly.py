#!/usr/bin/env python3
"""PRE750: verify alternate USA Catch-Up attribute paths/callers, read-only.

PRE749 builds one USA dynamic controller hook, but GetCatchupCheat and
data-driven CatchUp evaluation may still contribute. Do not claim complete
rubber-band removal without checking alternate consumers and runtime.
Only private Drive report receives guest source snippets.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from pathlib import Path
from collections import Counter
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID,EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
SOURCES=re.compile(r"^workspace/nativo/app_usa/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
FUNC=re.compile(rb"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)\s*\{")
TARGETS={
  "usa_dynamic_catchup": "sub_823328C0",
  "usa_catchup_attr_getter": "sub_82338A90",
  "usa_catchup_hash_reader_1": "sub_8233BC80",
  "usa_catchup_hash_reader_2": "sub_822C4FB8",
  "usa_catchup_hash_reader_3": "sub_82327460",
  "usa_dynamic_catchup_caller": "sub_821060A8",
  "usa_career_branch_helper_1": "sub_82338B08",
  "usa_career_branch_helper_2": "sub_82337D20",
}
CALL=re.compile(rb"\b(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\)")
MAX_BYTES=400*1024*1024
MAX_CALLER_EXCERPTS=12
def sha(b):return hashlib.sha256(b).hexdigest()

def scan(file):
  report={"stage":"PRE750_USA_CATCHUP_ALTERNATE_CALLERS_READONLY",
    "original_pre99_sha256_verified":True,
    "target_definitions":{},"target_caller_graph":{},
    "files":0,"functions":0,"read_bytes":0,
    "guest_original_unchanged":True,"game_assets_modified":False,
    "apk_built":False,"signing_accessed":False,
    "runtime_complete_catchup_elimination_verified":False}
  targets={x.upper():label for label,x in TARGETS.items()}
  callers={label:[] for label in TARGETS}
  with tarfile.open(file,"r:gz",errorlevel=2) as tf:
    for member in tf:
      if not member.isfile() or not SOURCES.fullmatch(member.name):continue
      if member.size<0 or member.size>25*1024*1024:
        raise ValueError("Unexpected generated USA codegen size")
      report["read_bytes"]+=member.size
      if report["read_bytes"]>MAX_BYTES:raise ValueError("USA scan byte budget exceeded")
      f=tf.extractfile(member)
      if f is None:raise ValueError("Cannot read USA generated source")
      with f:data=f.read()
      report["files"]+=1
      matches=list(FUNC.finditer(data))
      for i,m in enumerate(matches):
        fn=m.group(1).decode()
        b=data[m.end(): (matches[i+1].start() if i+1<len(matches) else len(data))]
        report["functions"]+=1
        if fn.upper() in targets:
          name=targets[fn.upper()]
          if name in report["target_definitions"]:
            raise ValueError("Duplicate USA target definition")
          report["target_definitions"][name]={
            "function":fn,"source_member":member.name,"sha256":sha(b),
            "size":len(b),"body_excerpt":b[:20000].decode("utf-8","replace"),
            "body_excerpt_truncated":len(b)>20000,
            "mentions_context_6700":b"6700(" in b,
            "mentions_catchup_hash":b"// ori r4,r4,1254" in b,
          }
        seen=Counter(g.decode().upper() for g in CALL.findall(b))
        for called,count in seen.items():
          if called not in targets:continue
          name=targets[called]
          if len(callers[name])<MAX_CALLER_EXCERPTS:
            callers[name].append({
              "caller":fn,"source_member":member.name,
              "body_size":len(b),"body_sha256":sha(b),
              "direct_call_count":count,
              "body_excerpt":b[:16000].decode("utf-8","replace"),
              "body_excerpt_truncated":len(b)>16000,
            })
  for label in TARGETS:
    arr=callers[label]
    report["target_caller_graph"][label]={
      "stored_callers":len(arr),
      "caller_excerpts_private_only":arr,
      "truncated_at_max_callers":len(arr)==MAX_CALLER_EXCERPTS
    }
  return report

def main():
  ap=argparse.ArgumentParser();ap.add_argument("--report",type=Path,required=True)
  opts=ap.parse_args()
  d=drive_client()
  with tempfile.TemporaryDirectory(prefix="nfsmw-pre750-") as td:
    file=Path(td)/"pre99.tar.gz"
    meta=d.files().get(fileId=BACKUP_ID,fields="id,size").execute()
    if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
      raise ValueError("PRE99 Drive metadata mismatch")
    download(d,file)
    dg,_md5,sz=sha_file(file)
    if dg!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:
      raise ValueError("Original PRE99 hash mismatch")
    report=scan(file)
  opts.report.parent.mkdir(parents=True,exist_ok=True)
  opts.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  for label in TARGETS:
    print("PRE750_TARGET_"+label.upper()+"="+str(label in report["target_definitions"]))
    print("PRE750_DIRECT_CALLERS_"+label.upper()+"="+str(report["target_caller_graph"][label]["stored_callers"]))
  name="NFSMW_PRE750_USA_ALTERNATE_CATCHUP_CALLERS_PRIVATE.json"
  up=d.files().create(body={"name":name,"parents":[FOLDER],"mimeType":"application/json"},
     media_body=MediaFileUpload(str(opts.report),mimetype="application/json"),
     fields="id,name,parents").execute()
  if up.get("name")!=name or FOLDER not in up.get("parents",[]):
    raise ValueError("PRE750 private report readback invalid")
  print("PRE750_REPORT_DRIVE_ID="+up["id"])
  print("PRE750_READONLY_NO_APK_NO_SIGNING")
if __name__=="__main__":main()
