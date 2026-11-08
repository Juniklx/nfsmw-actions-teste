#!/usr/bin/env python3
"""PRE485: index calls and performance-like offset accesses in authenticated
private PAL static-recompilation source archive. Strictly read-only.

Purpose: find reproducible candidates for physics upgrades GetMaxLevel,
SetLevel and SetPackage; NEVER claim semantic identification from xrefs alone.
No raw generated code published; only filenames, SHA, function labels,
pinned anchors, call relationships and bounded numerical opcode metadata.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre485/report.json")
PREFIX="workspace/nativo/app/generated/default/"
FUNC=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
FIELD=re.compile(r"(?m)^\s*//\s*(?:lwz|stw)\s+r\d+,\s*(-?\d+)\(r\d+\)")
FIELDS=(40,44,48,52,60,68,72)
ANCHORS={
    "package_list_builder":"sub_8256F818",
    "candidate_attribute_lookup":"sub_823E5988",
    "attribute_lookup_check":"sub_8214B858",
    "attribute_resolve_pointer":"sub_8214EDA8"
}
KNOWN_FILE_SHA={
    "nfsmw_recomp.28.cpp":"11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad",
    "nfsmw_recomp.57.cpp":"a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c",
    "nfsmw_recomp.50.cpp":"f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d",
    "nfsmw_recomp.83.cpp":"21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4",
}
def scan():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre485_") as temp:
        local=Path(temp)/"pre99.tar.gz"
        download(drive_client(),local)
        digest,_,bytecount=sha_file(local)
        if (digest,bytecount)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 authenticated archive digest/size changed")
        files=0; functions=0; oversized=0
        function_info={};calls_by_source={};callers=defaultdict(set)
        nearby_offset_candidates=[];known_file_verified={}
        other_relevant_filenames=[]
        with tarfile.open(local,"r:gz",errorlevel=2) as tar:
            for m in tar:
                path=m.name.lstrip("./")
                if m.isfile() and any(x in path.lower() for x in
                       ("symbols","function_map","functions.csv","xex_map")):
                    if len(other_relevant_filenames)<40:
                        other_relevant_filenames.append(path[:180])
                if not(m.isfile() and path.startswith(PREFIX)
                       and path.endswith(".cpp") and
                       re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):])):
                    continue
                if m.size>12_000_000 or m.size<10:
                    oversized+=1
                    continue
                stream=tar.extractfile(m)
                if stream is None:raise ValueError("Unreadable generated source member")
                raw=stream.read()
                if len(raw)!=m.size:raise ValueError("Generated source member truncated")
                h=hashlib.sha256(raw).hexdigest()
                filename=path[len(PREFIX):]
                if filename in KNOWN_FILE_SHA:
                    if h!=KNOWN_FILE_SHA[filename]:
                        raise ValueError("Pinned source sha changed: "+filename)
                    known_file_verified[filename]=h
                src=raw.decode("utf-8","replace")
                definitions=list(FUNC.finditer(src))
                files+=1
                for i,match in enumerate(definitions):
                    name=match.group(1)
                    start=match.start()
                    end=definitions[i+1].start() if i+1<len(definitions) else len(src)
                    body=src[start:end]
                    calls=sorted(set(CALL.findall(body)))
                    for callee in calls:callers[callee].add(name)
                    if name in function_info:
                        raise ValueError("Duplicate guest function "+name)
                    field_hits=Counter(int(v) for v in FIELD.findall(body))
                    distinct=[x for x in FIELDS if field_hits[x]>0]
                    function_info[name]={
                        "generated_file":filename,"generated_file_sha256":h,
                        "generated_function_size_chars":len(body),
                        "incoming_calls_known":False,
                        "call_targets_total":len(calls),
                        "performance_offset_distinct":len(distinct),
                        "performance_offsets":[{"ppc_offset":k,"accesses":field_hits[k]}
                                               for k in distinct],
                    }
                    calls_by_source[name]=calls
                    functions+=1
                    if len(distinct)>=4:
                        nearby_offset_candidates.append((name,len(distinct),sum(field_hits[x] for x in distinct)))
        if len(known_file_verified)!=len(KNOWN_FILE_SHA):
            raise ValueError("Not all four previously pinned generated files verified")
        if files<30 or functions<3000:
            raise ValueError("Insufficient generated PAL function coverage")
        if any(n not in function_info for n in ANCHORS.values()):
            raise ValueError("Known anchor function missing from indexed source")
        for key in function_info:
            function_info[key]["incoming_calls_known"]=True
        edges={}
        for label,guest_name in ANCHORS.items():
            parents=sorted(callers.get(guest_name,set()))
            grandparents=sorted(set(p for parent in parents for p in callers.get(parent,set())))
            edges[label]={
                "guest_function":guest_name,
                "location":function_info[guest_name],
                "direct_caller_count":len(parents),
                "direct_callers":[{"function":x,**function_info[x]} for x in parents[:80]],
                "second_hop_caller_count":len(grandparents),
                "second_hop_callers":[{"function":x,**function_info[x]} for x in grandparents[:60]],
                "all_direct_callers_reported":len(parents)<=80
            }
        hits=sorted(nearby_offset_candidates,key=lambda x:(-x[1],-x[2],x[0]))
        # Allow an investigator to distinguish structural candidates from semantic proof.
        candidates=[{"function":name,
                     "offset_candidate_hit_count":hits_count,
                     **function_info[name],
                     "caller_count":len(callers.get(name,set())),
                     "outgoing_sample":calls_by_source[name][:10],
                     "is_in_known_anchor_neighborhood":any(name==edge["guest_function"] or
                        name in (x["function"] for x in edge["direct_callers"])
                        for edge in edges.values())}
                    for name,n,hits_count in hits[:80]]
        return {
            "stage":"PRE485_ORIGINAL_PAL_UPGRADE_GUEST_CALL_GRAPH_CANDIDATES",
            "status":"AUDIT_OK",
            "original_tar_sha256":digest,"original_tar_size":bytecount,
            "generated_files_read":files,"generated_functions_indexed":functions,
            "generated_files_oversized_skipped":oversized,
            "all_four_prior_source_shas_verified":True,
            "anchor_call_relationships":edges,
            "performance_counter_guest_offsets_interpreted_as_heuristic_only":True,
            "physical_counter_offsets_from_PVEHICLE_PAL":[hex(x) for x in FIELDS],
            "offset_access_candidate_total":len(nearby_offset_candidates),
            "offset_candidate_top80":candidates,
            "other_potential_symbol_map_names":other_relevant_filenames,
            "functions_SetPackage_SetLevel_GetMaxLevel_identified":False,
            "guest_code_executed":False,"game_source_extracted_to_disk":False,
            "apk_built":False,"save_modified":False,"mod_enabled":False,
            "raw_generated_source_published":False
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=scan()
    except Exception as ex:r={
        "stage":"PRE485_ORIGINAL_PAL_UPGRADE_GUEST_CALL_GRAPH_CANDIDATES",
        "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:220],
        "game_source_extracted_to_disk":False,"apk_built":False,
        "save_modified":False,"mod_enabled":False,
        "raw_generated_source_published":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE485_STATUS",r["status"],flush=True)
    print("PRE485_FUNCTION_COUNT",r.get("generated_functions_indexed","none"),flush=True)
    print("PRE485_OFFSETS_CANDIDATES",r.get("offset_access_candidate_total","none"),flush=True)
    print("PRE485_ERROR_TYPE",r.get("error_type","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
