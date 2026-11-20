#!/usr/bin/env python3
"""PRE745: original PRE99 PAL/USA guest provenance before Catch-Up native hook.

Read ONLY. PRE741-743B scanned nativo/app (PAL) and must NOT be treated as USA
proof. Scans both edition-specific codegen trees by function signatures.
No generated source, game assets, credentials, or snippets enter public CI.
Full metadata-only evidence is saved in private Drive.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path
from collections import Counter
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID,EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
SOURCES=re.compile(r"^workspace/nativo/(app|app_usa)/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
FUNC=re.compile(rb"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)\s*\{")
CALL=re.compile(rb"(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\)")
STORES=re.compile(rb"// stfs [A-Za-z0-9]+,0\(r\d+\)")
OFFSET=re.compile(rb"// lwz [a-z0-9]+,6700\(r\d+\)")
CATCH_HASH_HI=b"// lis r4,4315"
CATCH_HASH_LO=b"// ori r4,r4,1254"
TARGET="sub_82332898"
TARGET_CALLER="sub_821060A8"
CANONICAL_GVAR=0x82A2CB18
LIMIT=650*1024*1024

def digest(v):return hashlib.sha256(v).hexdigest()
def entry(fn,body,member):
    # names & hashes only, not original guest implementation text.
    flag=(CATCH_HASH_HI in body and CATCH_HASH_LO in body)
    offset=bool(OFFSET.search(body))
    career=(b"// cmpwi cr6," in body and b",2" in body and offset)
    ret=b"// li r3,0" in body and b"// li r3,1" in body
    writes=len(STORES.findall(body))
    calls=Counter(v.decode() for v in CALL.findall(body))
    return {
       "symbol":fn,"member":member,"body_size":len(body),
       "body_sha256":digest(body),
       "context_offset_6700":offset,"career_compare_2":career,
       "catchup_hash_0x10DB04E6":flag,"bool_return_0_and_1":ret,
       "guest_store_zero_offset_count":writes,
       "calls":dict(calls)
    }

def run(archive):
    report={
      "stage":"PRE745_PAL_USA_GUEST_CATCHUP_PROVENANCE_READONLY",
      "sha_pinned_pre99_verified":True,
      "editions":{"app":{"label":"PAL","functions":0,"cpp_sources":0,"target":None,"target_caller":None,
                         "candidates":[],"catchup_hash_functions":[]},
                  "app_usa":{"label":"USA","functions":0,"cpp_sources":0,"target":None,"target_caller":None,
                         "candidates":[],"catchup_hash_functions":[]}},
      "bytes_scanned":0,"cmake_sources":{},"static_game_data_modified":False,
      "release_code_modified":False,"gameplay_patch_applied":False,"apk_built":False,
      "signing_accessed":False,"runtime_effect_verified":False,
    }
    all_calls={"app":Counter(),"app_usa":Counter()}
    with tarfile.open(archive,"r:gz",errorlevel=2) as tf:
      for m in tf:
        if not m.isfile():continue
        name=m.name
        if name in ("workspace/nativo/app/CMakeLists.txt","workspace/nativo/app_usa/CMakeLists.txt"):
            fp=tf.extractfile(m)
            if fp is not None:
                with fp:content=fp.read()
                report["cmake_sources"][name]={"exists":True,"sha256":digest(content),"bytes":len(content)}
                continue
        found=SOURCES.fullmatch(name)
        if not found:continue
        which=found.group(1)
        if not 0<m.size<=24*1024*1024:raise ValueError("Unexpected generated shard size")
        report["bytes_scanned"]+=m.size
        if report["bytes_scanned"]>LIMIT:raise ValueError("Guest scan exceeded limit")
        fd=tf.extractfile(m)
        if fd is None:raise ValueError("Guest shard unreadable")
        with fd:data=fd.read()
        edition=report["editions"][which]
        edition["cpp_sources"]+=1
        headers=list(FUNC.finditer(data))
        for i,h in enumerate(headers):
            fn=h.group(1).decode()
            body=data[h.end():(headers[i+1].start() if i+1<len(headers) else len(data))]
            edition["functions"]+=1
            record=entry(fn,body,name)
            if fn==TARGET:edition["target"]=record
            if fn==TARGET_CALLER:edition["target_caller"]=record
            if record["catchup_hash_0x10DB04E6"]:
                edition["catchup_hash_functions"].append({k:record[k] for k in
                  ("symbol","member","body_sha256","body_size")})
            if record["context_offset_6700"] and record["career_compare_2"] and record["bool_return_0_and_1"] and record["guest_store_zero_offset_count"]>=2:
                edition["candidates"].append({k:record[k] for k in
                    ("symbol","member","body_sha256","body_size","context_offset_6700",
                     "career_compare_2","bool_return_0_and_1","guest_store_zero_offset_count")})
            for call,count in record["calls"].items():
                if call==TARGET:all_calls[which][fn]+=count
    for which,edition in report["editions"].items():
        edition["direct_target_callers"]=dict(all_calls[which])
        t=edition["target"]
        if t:t.pop("calls",None)
        c=edition["target_caller"]
        if c:
            c["target_call_count"]=all_calls[which].get(TARGET_CALLER,0)
            c.pop("calls",None)
        edition["candidate_count"]=len(edition["candidates"])
        edition["hash_function_count"]=len(edition["catchup_hash_functions"])
    report["pal_is_usa_codegen"]=False  # provenance established from two manifest paths PRE218
    report["usa_target_same_symbol_as_pal"]=(
        report["editions"]["app"]["target"] is not None and report["editions"]["app_usa"]["target"] is not None)
    if report["usa_target_same_symbol_as_pal"]:
        report["pal_usa_target_same_body_sha"]=(
          report["editions"]["app"]["target"]["body_sha256"] ==
          report["editions"]["app_usa"]["target"]["body_sha256"])
    return report

def main():
  p=argparse.ArgumentParser()
  p.add_argument("--report",required=True,type=Path)
  opts=p.parse_args()
  d=drive_client()
  with tempfile.TemporaryDirectory(prefix="nfsmw-pre745-") as td:
    f=Path(td)/"PRE99.tar.gz"
    meta=d.files().get(fileId=BACKUP_ID,fields="id,size").execute()
    if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
        raise ValueError("PRE99 metadata mismatch")
    download(d,f)
    sha,_md5,size=sha_file(f)
    if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
        raise ValueError("PRE99 full archive SHA mismatch")
    report=run(f)
  opts.report.parent.mkdir(parents=True,exist_ok=True)
  opts.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  for ed,stats in report["editions"].items():
      print("PRE745_EDITION="+ed+" FUNCTIONS="+str(stats["functions"])+" SHARDS="+str(stats["cpp_sources"])+" TARGET="+str(bool(stats["target"]))+" CANDIDATES="+str(stats["candidate_count"]))
      print("PRE745_"+ed.upper()+"_CALLERS="+json.dumps(stats["direct_target_callers"],sort_keys=True))
  print("PRE745_MATCHED_SAME_ADDRESS="+str(report["usa_target_same_symbol_as_pal"]))
  print("PRE745_MATCHED_SAME_CODE="+str(report.get("pal_usa_target_same_body_sha",None)))
  name="NFSMW_PRE745_PAL_USA_CATCHUP_GUEST_CROSSWALK_PRIVATE.json"
  uploaded=d.files().create(body={"name":name,"mimeType":"application/json","parents":[FOLDER]},
            media_body=MediaFileUpload(str(opts.report),mimetype="application/json"),
            fields="id,name,parents").execute()
  if uploaded.get("name")!=name or FOLDER not in uploaded.get("parents",[]):
      raise ValueError("PRE745 private report upload validation failed")
  print("PRE745_REPORT_DRIVE_ID="+uploaded["id"])
  print("PRE745_NO_PATCH_NO_APK_NO_SIGNING")
if __name__=="__main__":
  main()
