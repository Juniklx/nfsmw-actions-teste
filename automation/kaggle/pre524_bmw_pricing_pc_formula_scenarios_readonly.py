#!/usr/bin/env python3
"""PRE524: pricing *scenario*, not an in-game purchase.

Evaluate the original PC reference CarCustomizeManager formula:
    unlock_level = GetMaxPackages(type) - GetNumPackages(type) + selected_part_level
against original USA FECarPartInfo Level/Cost arrays and authenticated PAL
pvehicle upgrade counters. The synthetic PRE502 BMW 1-level engine is NOT
an installed part, and this scenario is NOT proof that Xbox PAL guest
follows PC source exactly. No binary/asset/save access or modifications.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("/tmp/nfsmw-pre524/report.json")
SOURCE_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
FE_SHA="8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528"
MAXPK={"tires":3,"brakes":4,"chassis":3,"transmission":4,
       "engine":4,"induction":3,"nos":3}
COUNTER={"engine":"engine_upgrades","transmission":"transmission_upgrades",
         "chassis":"chassis_upgrades","brakes":"brakes_upgrades",
         "tires":"tires_upgrades","induction":"induction_upgrades",
         "nos":"nos_upgrades"}
REF="dbalatoni13/nfsmw@80993f35224c61d2f1b135beba76c6f8234c7940"
def audit():
    fe=json.loads(Path("docs/PRE522_USA_FE_CARPARTS_COST_ARRAYS_READONLY.json").read_text())
    src=json.loads(Path("docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json").read_text())
    scratch=json.loads(Path("docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json").read_text())
    if (fe.get("status")!="AUDIT_OK" or fe.get("original_FE_ATTRIB_sha256")!=FE_SHA
        or fe.get("children_with_category_enum_decoded")!=7
        or fe.get("children_with_valid_FECarPartInfo_array")!=21
        or fe.get("actual_original_USA_prices_decoded") is not True
        or fe.get("actual_BMW_shop_cost_or_purchase_verified") is not False
        or src.get("status")!="AUDIT_OK" or src.get("vpak_sha256")!=SOURCE_SHA
        or scratch.get("status")!="AUDIT_OK"
        or scratch.get("original_source_pal_sha256")!=SOURCE_SHA
        or scratch.get("safe_to_build_tuning_APK") is not False
        or scratch.get("source_PAL_resource_ZDIR_row_index")!=806):
        raise ValueError("PRE522, PRE473, PRE518 source proof missing")

    bycat={}
    for child in fe["per_collection_reference_and_typed_metadata"]:
        category=child.get("FE_purchase_category")
        if not category:continue
        raw=child.get("validated_FECarPartInfo_arrays",[])
        if len(raw)!=1:
            raise ValueError("Ambiguous original FE price array "+category)
        catalog={row["level"]:row["cost"] for row in raw[0]["array_elements"]}
        if category in bycat or not all(level in catalog for level in range(1,MAXPK[category]+1)):
            raise ValueError("Missing/duplicate original FE price levels for "+category)
        bycat[category]=catalog
    if set(bycat)!=set(MAXPK):
        raise ValueError("Seven original performance price categories incomplete")
    pvehicle={}
    for rec in src["selected_variants_and_control_records"]:
        if any(x in rec.get("candidate_names",[]) for x in ("bmwm3gtr","punto")):
            name=next(x for x in ("bmwm3gtr","punto") if x in rec["candidate_names"])
            pvehicle[name]=rec["upgrade_counters_original_signed_i32"]
    if set(pvehicle)!={"bmwm3gtr","punto"}:
        raise ValueError("Original BMW/Punto controls absent")

    def scenario(label,counters):
        result=[]
        for category in MAXPK:
            maxpack=MAXPK[category];num=counters[COUNTER[category]]
            if not isinstance(num,int) or not 0<=num<=maxpack:
                raise ValueError("Invalid pvehicle category count for "+category)
            choices=[]
            for part_level in range(1,num+1):
                mapped_level=maxpack-num+part_level
                price=bycat[category][mapped_level]
                choices.append({"display_part_level":part_level,
                                "source_catalog_level":mapped_level,
                                "source_USA_cost":price})
            result.append({"category":category,"class_max_possible_packages":maxpack,
                           "vehicle_available_package_count":num,
                           "packages_from_PC_reference_formula":choices})
        return {"scenario":label,"per_category":result}
    synthetic=dict(pvehicle["bmwm3gtr"])
    if synthetic["engine_upgrades"]!=0 or synthetic["nos_upgrades"]!=3:
        raise ValueError("Source BMW counts differ from PRE473")
    synthetic["engine_upgrades"]=1
    normal=scenario("original_Punto_reference_only",pvehicle["punto"])
    stock=scenario("original_BMW_unchanged_reference_only",pvehicle["bmwm3gtr"])
    test=scenario("BMW_engine_limit1_synthetic_noninstalled_HYPOTHESIS",synthetic)
    test_engine=next(x for x in test["per_category"] if x["category"]=="engine")["packages_from_PC_reference_formula"]
    punto_engine=next(x for x in normal["per_category"] if x["category"]=="engine")["packages_from_PC_reference_formula"]
    if (len(test_engine)!=1 or test_engine[0]["source_catalog_level"]!=4 or
        test_engine[0]["source_USA_cost"]!=98000 or
        punto_engine[0]["source_catalog_level"]!=1 or
        punto_engine[0]["source_USA_cost"]!=5500):
        raise ValueError("PC reference pricing scenario did not reproduce source FE cost rows")
    return {
      "stage":"PRE524_PC_REFERENCE_FE_PACKAGE_PRICE_MAPPING_SCENARIOS_READONLY",
      "status":"AUDIT_OK",
      "public_reference_commit":REF,
      "reference_GameFlow_and_CustomizeManager_original_PC_not_Xbox_guest":True,
      "reference_formula":"catalogueLevel = GetMaxPackages(type) - GetNumPackages(type) + chosenPartLevel",
      "source_original_USA_frontend_sha256":FE_SHA,
      "source_PAL_pvehicle_vpak_sha256":SOURCE_SHA,
      "source_PAL_original_BMW_engine_level_count":0,
      "synthetic_BMW_single_engine_level_count":1,
      "Punto_original_and_BMW_synthetic_calculations":[normal,stock,test],
      "candidate_BMW_single_engine_package_catalogue_level":4,
      "candidate_BMW_single_engine_package_USA_reference_cost":98000,
      "Punto_original_first_engine_package_USA_reference_cost":5500,
      "same_source_resource_PAL_USA_FE_price_identity_verified":False,
      "actual_Xbox_guest_unlock_price_formula_verified":False,
      "BMW_package_purchase_unlock_status_verified":False,
      "BMW_Physics_SetPackage_or_save_roundtrip_verified":False,
      "synthetic_BMW_5percent_torque_is_not_user_selected":True,
      "game_asset_modified_or_published":False,"APK_built":False,
      "save_modified":False,"signing_key_accessed":False,
      "ready_to_enable_BMW_tuning":False
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE524_PC_REFERENCE_FE_PACKAGE_PRICE_MAPPING_SCENARIOS_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
           "game_asset_modified_or_published":False,"APK_built":False,
           "save_modified":False,"signing_key_accessed":False,
           "ready_to_enable_BMW_tuning":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE524_STATUS",r["status"],flush=True)
    print("PRE524_BMW_SYNTHETIC_PRICE",r.get("candidate_BMW_single_engine_package_USA_reference_cost"),flush=True)
    print("PRE524_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
