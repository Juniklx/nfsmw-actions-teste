#!/usr/bin/env python3
"""PRE491: contrast PC-v1.3 reverse-engineered interpolation hypothesis with
authenticated original PAL positive-level Punto and zero-level BMW data.

No original game assets are read. No guest, Android, save, APK or code mutation.
This is OFFLINE MODEL COMPARISON, not PAL engine runtime verification.
"""
from __future__ import annotations
import argparse, json, math
from datetime import datetime,timezone
from pathlib import Path

DIR=Path("docs")
OUT=Path("/tmp/nfsmw-pre491/report.json")
PIN="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
REF_PAL="PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json"
PHY_PAL="PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json"
COUNT_PAL="PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json"
MODEL_URL="https://github.com/MagicIbrar/nfsmw-unity/blob/336fb872d698377b586cfab75d70c5828c77086c/NFSMW_RE/specs/physics.md"
MODEL_BLOB_SHA="b627fc7db26de515cdbc87d4f2f70331c6596b64"
MODEL_STATUS="PC v1.3 reverse-engineering report; NOT Xbox PAL runtime proof"
SCALARS={
  "transmission":("FINAL_GEAR",4),
  "brakes":("EBRAKE",4),
  "chassis":("AERO_COEFFICIENT",3),
  "tires":("STEERING",3),
  "engine":("MAX_RPM",4)
}
def lerp(a,b,t):
    if not (math.isfinite(a) and math.isfinite(b) and 0 <= t <= 1):
        raise ValueError("Invalid mathematical interpolation")
    return a+(b-a)*t

def parse_sources():
    r=json.loads((DIR/REF_PAL).read_text())
    p=json.loads((DIR/PHY_PAL).read_text())
    c=json.loads((DIR/COUNT_PAL).read_text())
    if not all(d.get("status")=="AUDIT_OK" for d in (r,p,c)):
        raise ValueError("PAL source report no longer approved")
    if (r.get("vpak_sha256")!=PIN or
        p.get("source_sha256")!=PIN or
        c.get("vpak_sha256")!=PIN):
        raise ValueError("PAL VPAK provenance mismatch")
    return r,p,c

def audit():
    refs,physical,count=parse_sources()
    records=count["selected_variants_and_control_records"]
    counters={}
    for item in records:
        for name in item["candidate_names"]:
            counters[name]=item["upgrade_counters_original_signed_i32"]
    if any(x not in counters for x in ("bmwm3gtr","punto","m3gtre46careerstart")):
        raise ValueError("Expected original BMW/Punto physical counter records missing")
    results={}
    checks=0
    for cls,(field,expected_N) in SCALARS.items():
        puntorefs=refs["vehicles"]["punto"]["categories_with_explicit_references"][cls]
        bmwrefs=refs["vehicles"]["bmwm3gtr"]["categories_with_explicit_references"][cls]
        careerrefs=refs["vehicles"]["m3gtre46careerstart"]["categories_with_explicit_references"][cls]
        current_field=cls+"_upgrades"
        if (puntorefs["item_count"]!=2 or
            puntorefs["pvehicle_upgrade_limit"]!=expected_N or
            counters["punto"][current_field]!=expected_N):
            raise ValueError("Positive-level Punto original reference mismatch "+cls)
        if (bmwrefs["item_count"]!=1 or careerrefs["item_count"]!=1 or
            bmwrefs["pvehicle_upgrade_limit"]!=0 or
            careerrefs["pvehicle_upgrade_limit"]!=0 or
            counters["bmwm3gtr"][current_field]!=0 or
            counters["m3gtre46careerstart"][current_field]!=0):
            raise ValueError("Original BMW zero-level controls unexpectedly changed "+cls)
        original=puntorefs["items"]
        if ([x["collection_hash"].lower() for x in original]
            !=["a6ee7a11","a6f0f405"]):
            raise ValueError("Punto reference order not the authenticated original")
        model=physical["class_models"][cls]
        pbase=model["collections"]["punto_base"]
        ptop=model["collections"]["punto_derived"]
        bmw=model["collections"]["bmwm3gtr"]
        if not all(x.get("has_bounded_layout") for x in (pbase,ptop,bmw)):
            raise ValueError("A claimed original physical layout is unbounded")
        a=pbase["scalar_f32_be_from_generated_pc_header"][field]
        b=ptop["scalar_f32_be_from_generated_pc_header"][field]
        if not (isinstance(a,(int,float)) and isinstance(b,(int,float))):
            raise ValueError("No scalar field found in original PAL source")
        steps=[{"simulated_level":i,"normalized_t":i/expected_N,
                "modeled_scalar":lerp(a,b,i/expected_N)}
               for i in range(expected_N+1)]
        if abs(steps[0]["modeled_scalar"]-a)>1e-7 or abs(steps[-1]["modeled_scalar"]-b)>1e-7:
            raise ValueError("Simulated interpolation endpoints failed")
        lo,hi=min(a,b),max(a,b)
        if any(not (lo-1e-7<=s["modeled_scalar"]<=hi+1e-7) for s in steps):
            raise ValueError("Simulated interpolation exited endpoint bounds")
        checks+=5
        results[cls]={
            "field":field,
            "source_class_and_field_from_authenticated_PAL":True,
            "punto_stock_collection":original[0]["collection_hash"],
            "punto_top_collection":original[1]["collection_hash"],
            "punto_upgrade_limit":expected_N,
            "punto_original_stock_value":a,
            "punto_original_top_value":b,
            "pc_hypothesis_mathematical_levels":steps,
            "BMW_stock_collection":bmwrefs["items"][0]["collection_hash"],
            "BMW_stock_field_original_value":
               bmw["scalar_f32_be_from_generated_pc_header"][field],
            "BMW_current_upgrade_limit":0,
            "BMW_original_reference_count":1,
            "BMW_simulation_allowed":False,
        }
    # Precondition of original nominal 0-level remains unmodified; no
    # synthetic level for BMW, including a gratuitous "same as stock" level.
    if checks!=25 or len(results)!=5:
        raise ValueError("Incomplete original data/mathematical checks")
    return {
       "stage":"PRE491_PAL_VS_PC_PERFORMANCE_INTERPOLATION_HYPOTHESIS",
       "status":"AUDIT_OK",
       "pal_vpak_sha256":PIN,
       "hypothesis_origin":MODEL_URL,
       "hypothesis_origin_blob_sha":MODEL_BLOB_SHA,
       "hypothesis_scope":MODEL_STATUS,
       "original_PAL_structurally_compatible_with_two_endpoint_model":True,
       "engine_behavior_PAL_runtime_verified":False,
       "math_test_count":checks,
       "Punto_original_data_with_model_levels":results,
       "BMW_original_upgradeable":False,
       "BMW_second_performance_reference_exists":False,
       "BMW_new_physics_profiles_proven":False,
       "BMW_buyable_upgrade_catalog_proven":False,
       "safe_to_enable_feature":False,
       "generated_apk":False,
       "save_changed":False,
       "game_assets_modified":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    args=parser.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as ex:r={
      "stage":"PRE491_PAL_VS_PC_PERFORMANCE_INTERPOLATION_HYPOTHESIS",
      "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:250],
      "safe_to_enable_feature":False,"generated_apk":False,
      "save_changed":False,"game_assets_modified":False}
    r["run_id"]=args.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE491_STATUS",r["status"],flush=True)
    print("PRE491_MATH_CHECKS",r.get("math_test_count",0),flush=True)
    print("PRE491_BMW_ACTIVATION_ALLOWED",r.get("safe_to_enable_feature",False),flush=True)
    print("PRE491_ERROR",r.get("error_type","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
