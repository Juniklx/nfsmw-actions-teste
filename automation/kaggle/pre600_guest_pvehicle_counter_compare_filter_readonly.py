#!/usr/bin/env python3
"""PRE600 read-only: refine pvehicle engine-counter PPC access candidates.
Scanner separates 0x28 vtable dispatch and bulk pvehicle-like data copying
from reads that participate in a compare/branch. All candidates remain
unverified until actual base-pointer and guest-value dataflow are proven.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre600/report.json")
PREFIX="workspace/nativo/app/generated/default/"
DEFS=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
PPC=re.compile(r"(?m)^\s*//\s*([a-zA-Z][a-zA-Z0-9.]*)\b(.*)$")
MEM=re.compile(r"^\s*(r\d+),\s*(-?\d+)\((r\d+)\)")
REGB=re.compile(r"(?<![A-Za-z0-9_])r\d+(?![A-Za-z0-9_])")
OFFSETS={40,44,48,52,60,68,72}
BRANCH={"beq","bne","bgt","blt","bge","ble","bdnz","bdz","bso","bns"}
CMP={"cmpwi","cmplwi","cmpw","cmplw","cmpdi","cmpldi"}
TARGETS={"sub_82203AB8","sub_82752E10","sub_82582F70"}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse_body(source,function):
    ppc=[(m.group(1).lower(),m.group(2).strip()) for m in PPC.finditer(source)]
    offsets_by_base={};sites=[]
    for idx,(op,args) in enumerate(ppc):
        if op!="lwz":continue
        m=MEM.match(args)
        if not m or int(m.group(2)) not in OFFSETS:continue
        dst,offset,base=m.group(1),int(m.group(2)),m.group(3)
        offsets_by_base.setdefault(base,set()).add(offset)
        if offset!=40:continue
        following=ppc[idx+1:idx+14]
        dispatch=False;active_cmp=False;branch=False;first_cmp_dist=None;cmp_args=None
        for k,(n,a) in enumerate(following):
            if n=="mtctr" and dst in REGB.findall(a):
                dispatch=any(x=="bctrl" for x,_ in following[k+1:k+4])
            if n in CMP and dst in REGB.findall(a):
                active_cmp=True;first_cmp_dist=k+1;cmp_args=a[:65]
                branch=any(x in BRANCH for x,_ in following[k+1:k+7])
                break
            # Stop when load register is overwritten. Treat it conservatively
            # as a new value rather than making false data-flow claims.
            if (n in ("li","lis","addi","addis","ori","mr","lwz","lhz","lbz","rlwinm","clrlwi")
                and REGB.findall(a) and REGB.findall(a)[0]==dst):
                break
        sites.append({
          "opcode_index":idx,
          "field_offset":40,
          "load_target_reg":dst,
          "base_reg":base,
          "next_4_opcodes":[x for x,_ in following[:4]],
          "vtable_dispatch_shape":dispatch,
          "direct_compare_of_loaded_value_within_13_ppc":active_cmp,
          "comparison_ppc_distance":first_cmp_dist,
          "comparison_operand_signature":cmp_args,
          "conditional_branch_after_comparison":branch,
          "layout_fields_for_same_base_later_or_earlier":[],
          "semantic_pvehicle_pointer_validated":False,
        })
    for item in sites:
        item["layout_fields_for_same_base_later_or_earlier"]=sorted(offsets_by_base.get(item["base_reg"],[]))
    interesting=[s for s in sites if s["direct_compare_of_loaded_value_within_13_ppc"] or s["vtable_dispatch_shape"] or len(s["layout_fields_for_same_base_later_or_earlier"])>=3]
    return {"function":function,"ppc_count":len(ppc),"all_engine_offset_loads":len(sites),
       "vtable_dispatch_shape_count":sum(s["vtable_dispatch_shape"] for s in sites),
       "direct_compare_and_branch_count":sum(s["direct_compare_of_loaded_value_within_13_ppc"] and s["conditional_branch_after_comparison"] for s in sites),
       "multi_field_same_base_count":sum(len(s["layout_fields_for_same_base_later_or_earlier"])>=3 for s in sites),
       "candidate_site_details":interesting[:25],
       "candidate_site_truncated":len(interesting)>25}

def rank(item):
    score=0
    s=item["site"]
    if s["direct_compare_of_loaded_value_within_13_ppc"] and s["conditional_branch_after_comparison"]:score+=9
    if len(s["layout_fields_for_same_base_later_or_earlier"])>=3:score+=4
    if s["vtable_dispatch_shape"]:score-=10
    if item["function"] in TARGETS:score-=2
    return score
def audit():
    prior=json.loads(Path("docs/PRE599_BMW_GUEST_COUNTER_PPC_PROVENANCE_READONLY.json").read_text())
    p473=json.loads(Path("docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json").read_text())
    if(prior.get("status")!="AUDIT_OK" or
       prior.get("source_archive_sha256")!=EXPECTED_SHA256 or
       prior.get("guest_function_count")!=56338 or
       prior.get("exact_GetMaxLevel_identity_proven") is not False or
       p473.get("status")!="AUDIT_OK" or
       p473.get("field_offsets",{}).get("engine_upgrades")!=40):
        raise ValueError("PRE599 provenance or authenticated engine pvehicle offset missing")
    total_sites=0;total_vtbl=0;total_comparisons=0;total_cmp_branch=0;cnt_counter_reads=Counter()
    candidates=[];anchors={}
    nfiles=0;nfunc=0
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre600_") as tmp:
        local=Path(tmp)/"pre99.tar.gz"
        download(drive_client(),local)
        digest,_,size=sha_file(local)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Original generated guest source binary provenance mismatch")
        with tarfile.open(local,"r:gz",errorlevel=2) as tf:
            for member in tf:
                path=member.name.lstrip("./")
                if not(member.isfile() and path.startswith(PREFIX)
                       and re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):])
                       and 0<member.size<=12_000_000):
                    continue
                raw=tf.extractfile(member).read()
                if len(raw)!=member.size:raise ValueError("Source file truncated in archive")
                file_sha=sha(raw);filename=path[len(PREFIX):]
                src=raw.decode("utf-8","replace")
                functions=list(DEFS.finditer(src))
                nfiles+=1;nfunc+=len(functions)
                for j,func in enumerate(functions):
                    name=func.group(1)
                    body=src[func.start():functions[j+1].start() if j+1<len(functions) else len(src)]
                    if ("// lwz" not in body or ",40(" not in body) and name not in TARGETS:
                        continue
                    info=parse_body(body,name)
                    total_sites+=info["all_engine_offset_loads"]
                    total_vtbl+=info["vtable_dispatch_shape_count"]
                    total_cmp_branch+=info["direct_compare_and_branch_count"]
                    total_comparisons+=sum(s["direct_compare_of_loaded_value_within_13_ppc"] for s in info["candidate_site_details"])
                    cnt_counter_reads[name]=info["all_engine_offset_loads"]
                    if name in TARGETS:
                        anchors[name]={"source_sha256":file_sha,"filename":filename,"details":info}
                    for site in info["candidate_site_details"]:
                        if site["direct_compare_of_loaded_value_within_13_ppc"] and site["conditional_branch_after_comparison"] and not site["vtable_dispatch_shape"]:
                            candidates.append({"function":name,"source_file":filename,"source_sha256":file_sha,"site":site})
    if (nfiles,nfunc)!=(129,56338):raise ValueError("PRE99 full file/function inventory changed")
    if set(anchors)!=TARGETS:raise ValueError("Pinned candidate functions not observed")
    # Guard: first two older heuristic candidates show a bulk-copy-like pattern
    for func in ("sub_82203AB8","sub_82752E10"):
        info=anchors[func]["details"]
        if not any(len(s["layout_fields_for_same_base_later_or_earlier"])>=7 for s in info["candidate_site_details"]):
            raise ValueError("Prior 7-field heuristic lost all seven same-base reads")
        if info["direct_compare_and_branch_count"]!=0:
            raise ValueError("Prior 7-field function unexpectedly contains direct field compare-and-branch")
    candidates.sort(key=lambda c:(-rank(c),c["function"],c["site"]["opcode_index"]))
    return {
      "stage":"PRE600_ORIGINAL_GUEST_PVEHICLE_ENGINE_COUNTER_USE_FILTERED",
      "status":"AUDIT_OK",
      "original_PRE99_source_sha256":EXPECTED_SHA256,
      "generated_files_visited":nfiles,"guest_functions_visited":nfunc,
      "engine_counter_offset_40_load_site_count_across_all_56k":total_sites,
      "vtable_dispatch_shape_count":total_vtbl,
      "direct_value_compare_followed_by_branch_count":total_cmp_branch,
      "candidate_direct_compare_branch_non_vtable_count":len(candidates),
      "candidate_ranked_top_30":candidates[:30],
      "candidate_list_truncated":len(candidates)>30,
      "prior_candidate_function_reclassification":{
        f:{"contains_seven_fields_same_base":True,
           "direct_branch_on_loaded_engine_value":False,
           "copy_or_marshalling_shape_hypothesis":True,
           "GetMaxLevel_semantics_proven":False}
         for f in ("sub_82203AB8","sub_82752E10")},
      "frontend_field_40_shape":anchors["sub_82582F70"],
      "candidate_engine_counter_access_is_heuristic_not_dataflow":True,
      "complete_dynamic_object_pointer_tracking_proven":False,
      "exact_GetMaxLevel_function_identified":False,
      "exact_SetLevel_function_identified":False,
      "BMW_second_RefSpec_lookup_verified":False,
      "guest_code_executed":False,
      "game_assets_modified":False,
      "apk_built":False,"save_modified":False,
      "release_key_accessed":False,
      "raw_generated_code_published":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE600_ORIGINAL_GUEST_PVEHICLE_ENGINE_COUNTER_USE_FILTERED",
       "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
       "guest_code_executed":False,"game_assets_modified":False,
       "apk_built":False,"save_modified":False,
       "release_key_accessed":False,"raw_generated_code_published":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE600_STATUS",r["status"])
    print("PRE600_CANDIDATE_COUNT",r.get("candidate_direct_compare_branch_non_vtable_count",0))
    print("PRE600_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
