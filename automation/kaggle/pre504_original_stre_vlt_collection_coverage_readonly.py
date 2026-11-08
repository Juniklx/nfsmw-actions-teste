#!/usr/bin/env python3
"""PRE504 original PAL/USA StrE coverage of pre-existing VLT collections.

Read-only check whether collection hashes in original VLT require names in BIN
StrE. Compares existing imported collections and the PRE502 independent BMW
candidate. Does NOT prove the game's loader accepts any new collection.
No original, modified VPAK, ISO, APK, save, or private game bytes are emitted.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32,get_names,chunks
from pre476_pal_performance_reference_resolution_readonly import collect_rows

OUT=Path("/tmp/nfsmw-pre504/report.json")
CANDIDATE="bmwm3gtr_upgrade_engine_pre499"
def audit():
    proof=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    if (proof.get("status")!="AUDIT_OK" or
        proof.get("source_pal_sha256")!=EXPECTED_VPAK_SHA or
        proof.get("new_collection_name")!=CANDIDATE or
        proof.get("new_collection_name_missing_original_StrE") is not True or
        proof.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE502 authenticated evidence or feature-OFF guard mismatch")
    reader,position=locate()
    raw=reader.read(position["absolute_offset"],position["size"])
    if len(raw)!=697856 or hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("Authenticated original VPAK changed")
    _,bl,vl,bo,vo=struct.unpack_from("<IIIII",raw,16)
    if (bl,vl,bo,vo)!=(354959,342720,128,355136):
        raise ValueError("Original resource layout changed")
    B=raw[bo:bo+bl];V=raw[vo:vo+vl]
    names=get_names(B,chunks(B,"BIN")[0])
    name_hashes={hash32(n) for n in names}
    collections,counts=collect_rows(V)
    if len(collections)!=2339 or sum(len(x) for x in collections.values())!=2339:
        raise ValueError("Original VLT collection count not confirmed")
    class_count=sum(counts.values())
    if class_count!=2339:raise ValueError("Original class collection counters differ")
    known=sum(1 for (cls,name) in collections if name in name_hashes)
    missing=len(collections)-known
    engine=hash32("engine")
    sample={}
    for name in ("bmwm3gtr","m3gtre46careerstart","punto"):
        key=(engine,hash32(name))
        sample[name]={
            "original_engine_collection_exists":len(collections.get(key,[]))==1,
            "collection_hash_in_original_StrE":hash32(name) in name_hashes
        }
    if not all(v["original_engine_collection_exists"] for v in sample.values()):
        raise ValueError("Missing BMW/Punto control engine collection")
    candidate_hash=hash32(CANDIDATE)
    if (engine,candidate_hash) in collections or candidate_hash in name_hashes:
        raise ValueError("Candidate collision or unexpected StrE presence")
    return {
        "stage":"PRE504_ORIGINAL_STRE_VLT_COLLECTION_HASH_COVERAGE_READONLY",
        "status":"AUDIT_OK","source_vpak_sha256":EXPECTED_VPAK_SHA,
        "original_StrE_ASCII_token_count":len(names),
        "original_StrE_distinct_name_hash_count":len(name_hashes),
        "original_VLT_collection_count":len(collections),
        "original_VLT_collections_with_name_hash_in_StrE":known,
        "original_VLT_collections_without_name_hash_in_StrE":missing,
        "original_name_coverage_fraction":round(known/len(collections),6),
        "sample_original_engine_collection_names":sample,
        "candidate_new_BMW_engine_collection_hash":f"{candidate_hash:08x}",
        "candidate_name_in_original_StrE":False,
        "candidate_class_collection_pair_already_exists":False,
        "original_Collections_without_StrE_names_exist":missing>0,
        "original_loader_initializes_existing_collections":True,
        "new_loader_collection_acceptance_proven":False,
        "new_name_registration_required_in_PAL_loader":None,
        "gameplay_tuning_or_purchase_verified":False,
        "safe_to_build_tuning_APK":False,
        "modified_VPAK_written":False,
        "ISO_modified":False,"APK_built":False,"save_modified":False,
        "runtime_tuning_enabled":False,
        "source_bytes_read":reader.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE504_ORIGINAL_STRE_VLT_COLLECTION_HASH_COVERAGE_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
           "modified_VPAK_written":False,"ISO_modified":False,
           "APK_built":False,"save_modified":False,"runtime_tuning_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE504_STATUS",r["status"],flush=True)
    print("PRE504_COVERAGE",r.get("original_VLT_collections_with_name_hash_in_StrE"),
          r.get("original_VLT_collections_without_name_hash_in_StrE"),flush=True)
    print("PRE504_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
