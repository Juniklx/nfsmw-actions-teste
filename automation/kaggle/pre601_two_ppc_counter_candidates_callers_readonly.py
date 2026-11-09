#!/usr/bin/env python3
"""PRE601 read-only: local PPC dataflow/caller context around two narrowed
pvehicle-like counter tests. Exact function semantics remain unverified.

Uses authenticated PRE99 recompilation archive only. Publishes bounded numeric
PPC comments and callgraph metadata, never full generated source or binaries.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter,defaultdict
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre601/report.json")
PREFIX="workspace/nativo/app/generated/default/"
FUNC=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
PPC=re.compile(r"^\s*//\s*([a-zA-Z][a-zA-Z0-9.]*)\b(.*)$")
LOAD=re.compile(r"^\s*(r\d+),\s*(-?\d+)\((r\d+)\)")
TARGET={
 "sub_8216A928":{"filename":"nfsmw_recomp.59.cpp","sha":"acf7533e6ca052a5107f1cefe98dc89d5a2b2b7a16fc95f603d402fffba5679d"},
 "sub_821EFC18":{"filename":"nfsmw_recomp.31.cpp","sha":"bc41cc424905b78648e903f04ef812d5cb835e3ed4009574e8330cbacb22e165"},
}
FRONTEND={"sub_82582F70","sub_8256F818","sub_823E5988","sub_823E5B08",
          "sub_823E6560","sub_823E67E8"}
ALL=tuple(TARGET)
def sha(b):return hashlib.sha256(b).hexdigest()
def ppc_lines(body):
 return [(idx+1,m.group(1).lower(),m.group(2).strip()) for idx,s in enumerate(body.splitlines()) if (m:=PPC.match(s))]
def summarize(body,filename,digest,name):
 instructions=ppc_lines(body)
 engine_sites=[]
 for i,(line,op,args) in enumerate(instructions):
    m=LOAD.match(args)
    if op!="lwz" or not m or int(m.group(2))!=40:continue
    dst,base=m.group(1),m.group(3)
    before=instructions[max(0,i-10):i]
    after=instructions[i+1:i+19]
    cmp=next(({"ppc_distance":k+1,"op":v[1],"args":v[2][:75]}
              for k,v in enumerate(after)
              if v[1] in ("cmplwi","cmpwi","cmplw","cmpw") and dst in re.findall(r"\br\d+\b",v[2])),None)
    engine_sites.append({
      "generated_function_relative_line":line,
      "loaded_register":dst,"base_register":base,
      "preceding_ppc_sequence":[{"op":n,"operands":a[:90]} for _,n,a in before[-10:]],
      "following_ppc_sequence":[{"op":n,"operands":a[:90]} for _,n,a in after[:18]],
      "direct_loaded_value_comparison":cmp,
      "hypothesis_only_pvehicle_counter":True,
    })
 if not engine_sites:raise ValueError("Expected counter-like read missing in targeted function "+name)
 # Identify simple register source initialization patterns; these are not
 # interprocedural or branch-sensitive dataflow.
 first=[{"op":op,"operands":args[:90]} for _,op,args in instructions[:18]]
 return {"guest_function":name,"original_generated_file":filename,
    "original_file_sha256":digest,"function_source_lines":len(body.splitlines()),
    "guest_calls":CALL.findall(body),
    "engine_offset_40_sites":engine_sites[:6],
    "start_ppc_prologue":first,
    "runtime_semantic_identity_proven":False}
def audit():
 p600=json.loads(Path("docs/PRE600_GUEST_COUNTER_BRANCH_CANDIDATES_READONLY.json").read_text())
 p487=json.loads(Path("docs/PRE487_PAL_PHYSICS_UPGRADE_READ_WRITE_CANDIDATES.json").read_text())
 p599=json.loads(Path("docs/PRE599_BMW_GUEST_COUNTER_PPC_PROVENANCE_READONLY.json").read_text())
 if (any(p.get("status")!="AUDIT_OK" for p in (p600,p487,p599))
     or p600.get("exact_GetMaxLevel_function_identified") is not False
     or p600.get("candidate_direct_compare_branch_non_vtable_count",0)<2
     or p599.get("source_archive_sha256")!=EXPECTED_SHA256):
    raise ValueError("Prior guest ranking evidence not authenticated")
 shortlist=set(x["function"] for x in p600["candidate_ranked_top_30"])
 heur=set(x["function"] for x in p487["GetMaxLevel_heuristic_top80"])
 if not set(TARGET).issubset(shortlist & heur):
    raise ValueError("PRE600 and PRE487 candidates no longer intersect as expected")
 funcs={};callers=defaultdict(list)
 files=0;count=0
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre601_") as d:
    src=Path(d)/"pre99.tar.gz"
    download(drive_client(),src)
    digest,_,size=sha_file(src)
    if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
        raise ValueError("Private original PAL recompilation archive SHA/size mismatch")
    with tarfile.open(src,"r:gz",errorlevel=2) as tf:
        for member in tf:
            path=member.name.lstrip("./")
            if not(member.isfile() and path.startswith(PREFIX)
                and re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):])
                and member.size<=12_000_000):
                continue
            raw=tf.extractfile(member).read()
            if len(raw)!=member.size:raise ValueError("Generated source truncated")
            filename=path[len(PREFIX):]
            fs=sha(raw)
            src_text=raw.decode("utf-8","replace")
            defs=list(FUNC.finditer(src_text))
            files+=1;count+=len(defs)
            for i,m in enumerate(defs):
                name=m.group(1)
                # Fast skip when neither a desired function nor caller references
                # a candidate callee in the original generated C++.
                body=src_text[m.start():defs[i+1].start() if i+1<len(defs) else len(src_text)]
                if name in TARGET:
                    if filename!=TARGET[name]["filename"] or fs!=TARGET[name]["sha"]:
                        raise ValueError("Target function original authenticated identity mismatch")
                    funcs[name]=summarize(body,filename,fs,name)
                if all("__imp__"+f not in body for f in ALL):
                    continue
                matched=[f for f in ALL if f in CALL.findall(body)]
                if matched:
                    for f in matched:callers[f].append({"function":name,"filename":filename,"source_sha256":fs})
 if (files,count)!=(129,56338) or set(funcs)!=set(TARGET):
    raise ValueError("Expected original generated guest source inventory/targets missing")
 for name in TARGET:
    if not funcs[name]["engine_offset_40_sites"][0]["direct_loaded_value_comparison"]:
        raise ValueError("Expected isolated compare after counter-like read missing")
    if len(callers[name])>100:
        raise ValueError("Unexpected fan-in over 100; force analyst inspection")
 return {"stage":"PRE601_ORIGINAL_PAL_GUEST_COUNTER_TWO_NARROWED_FUNCTION_CONTEXT",
   "status":"AUDIT_OK",
   "source_SHA256":EXPECTED_SHA256,
   "authenticated_source_files":files,"authenticated_source_functions":count,
   "targets":funcs,
   "direct_callers":dict(callers),
   "direct_caller_counts":{k:len(callers[k]) for k in TARGET},
   "direct_caller_intersects_frontend_anchors":{k:sorted(set(
      x["function"] for x in callers[k])&FRONTEND) for k in TARGET},
   "GetMaxLevel_identified":False,"SetLevel_identified":False,
   "pvehicle_base_register_proven":False,
   "conditional_branch_sensitive_dataflow_proven":False,
   "engine_second_reference_lookup_verified":False,
   "candidate_annotated_ppc_is_not_dynamic_trace":True,
   "guest_executed":False,"phone_data_modified":False,
   "game_assets_modified":False,"apk_built":False,
   "save_modified":False,"signing_accessed":False,
   "original_generated_source_uploaded":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE601_ORIGINAL_PAL_GUEST_COUNTER_TWO_NARROWED_FUNCTION_CONTEXT",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:270],
      "guest_executed":False,"phone_data_modified":False,
      "game_assets_modified":False,"apk_built":False,"save_modified":False,
      "signing_accessed":False,"original_generated_source_uploaded":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE601_STATUS",r["status"],flush=True)
    print("PRE601_DIRECT_CALLER_COUNTS",r.get("direct_caller_counts",{}),flush=True)
    print("PRE601_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
