#!/usr/bin/env python3
"""PRE492: data-only BMW tuning patch feasibility from authenticated original
PAL RefSpec array metadata, no writing, no binary patch recipes, no APK.
Proves that one-reference arrays cannot be enlarged by changing u16 count.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
OUT=Path("/tmp/nfsmw-pre492/report.json")
PIN="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
CATEGORIES=("engine","transmission","chassis","tires","brakes")
def inspect():
    ref=json.loads(Path("docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json").read_text())
    phys=json.loads(Path("docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json").read_text())
    if (ref.get("status")!="AUDIT_OK" or phys.get("status")!="AUDIT_OK"
        or ref.get("vpak_sha256")!=PIN or phys.get("source_sha256")!=PIN):
        raise ValueError("Original PAL proof mismatch")
    results={}
    for vehicle in ("bmwm3gtr","m3gtre46careerstart","punto"):
        entries=ref["vehicles"][vehicle]["categories_with_explicit_references"]
        arrays={}
        for category,item in entries.items():
            count=item["item_count"]
            capacity=item["capacity"]
            elem=item["element_size"]
            offset=item["bin_array_offset"]
            if (capacity<=0 or count<=0 or count>capacity or elem!=12
                or item["array_header_valid"] is not True or offset<0):
                raise ValueError("Invalid original array "+vehicle+"/"+category)
            total=8+capacity*elem
            arrays[category]={"start":offset,"end":offset+total,
                "capacity":capacity,"count":count,"element_size":elem,
                "physical_bytes":total,"upgrade_limit":item["pvehicle_upgrade_limit"],
                "room_to_append_second_without_relocation":capacity>=2 and count<2}
        intervals=sorted((v["start"],v["end"],k) for k,v in arrays.items())
        for a,b in zip(intervals,intervals[1:]):
            if a[1]>b[0]:raise ValueError("Original arrays overlap")
        results[vehicle]={"categories":arrays,
             "intervals_do_not_overlap":True,
             "metadata_checked":True}
    bmw=results["bmwm3gtr"]["categories"]
    punto=results["punto"]["categories"]
    for typ in CATEGORIES:
        if not (bmw[typ]["capacity"]==bmw[typ]["count"]==1 and
                bmw[typ]["upgrade_limit"]==0 and
                punto[typ]["capacity"]==punto[typ]["count"]==2 and
                punto[typ]["upgrade_limit"]>0):
            raise ValueError("Expected original BMW vs Punto reference configuration changed")
    bmw_induction_missing="induction" not in bmw
    if not bmw_induction_missing:
        raise ValueError("Original BMW induction field had unanticipated explicit references")
    return {"stage":"PRE492_PAL_BMW_REFSPEC_DATA_PATCH_GATES",
        "status":"AUDIT_OK","source_pal_vpak_sha256":PIN,
        "original_arrays":results,
        "bmw_categories_without_room_for_second_ref":list(CATEGORIES),
        "bmw_cannot_gain_valid_second_ref_by_only_changing_u16_count":True,
        "bmw_needs_valid_additional_class_specific_endpoint":True,
        "bmw_needs_relocated_array_and_verified_PtrN_linkage":True,
        "bmw_requires_separate_pvehicle_upgrade_counter_edit":True,
        "bmw_induction_original_explicit_ref_missing":bmw_induction_missing,
        "PAL_engine_automatically_interpolates_two_refs_verified":False,
        "feature_safe_to_enable":False,
        "patch_written":False,"apk_built":False,
        "save_modified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:d=inspect()
    except Exception as ex:d={"stage":"PRE492_PAL_BMW_REFSPEC_DATA_PATCH_GATES",
        "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:230],
        "feature_safe_to_enable":False,"patch_written":False,
        "apk_built":False,"save_modified":False}
    d["run_id"]=a.run_id
    d["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
    print("PRE492_STATUS",d["status"])
    print("PRE492_ORIGINAL_BMW_ARRAYS_NEED_RELOCATION",
       len(d.get("bmw_categories_without_room_for_second_ref",[])))
    print("PRE492_ERROR",d.get("error_type","none"))
    return 0 if d["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
