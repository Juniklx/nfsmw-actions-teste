#!/usr/bin/env python3
"""PRE596: CI-only counter sensitivity + unresolved guest semantics gate.
This intentionally does NOT generate a new patch or modify game/saves.
It proves PRE591 (phone success reported) vs PRE502 (phone failed) differ by
exactly one big-endian pvehicle engine counter byte, with metadata CRC updates.
It identifies incomplete runtime GetMaxLevel/FE behavior as next research gate.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
OUT=Path("/tmp/nfsmw-pre596/report.json")
P={
 "473":"docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json",
 "474":"docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json",
 "490":"docs/PRE490_PAL_FUNCTION_ARGS_RETURNS_READONLY.json",
 "501":"docs/PRE501_BMW_ENGINE_ONE_LEVEL_COUNTER_SCRATCH.json",
 "502":"docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json",
 "580":"docs/PRE580_PTBR_BMW_MOTOR_ONLY_PRIVATE_CONTROL_METADATA.json",
 "586":"docs/PRE586_PTBR_BMW_UNLINKED_VLT_PRIVATE_METADATA.json",
 "591":"docs/PRE591_BMW_REFSPEC_POINTER_ONLY_PRIVATE_METADATA.json",
 "592":"docs/PRE592_SHEVERY_REFSPEC_POINTER_ONLY_STATIC_PREFLIGHT_RESULT.json",
}
def read():
 r={n:json.loads(Path(path).read_text()) for n,path in P.items()}
 for n,d in r.items():
  if d.get("status")!="AUDIT_OK":raise ValueError("Prior structured evidence failed "+n)
 return r
def audit():
 d=read();p=d["473"];p474=d["474"];p490=d["490"];p501=d["501"]
 comb=d["502"];isol=d["591"];pre586=d["586"];torque=d["580"];sh=d["592"]
 handoff=Path("docs/PRE595_HANDOFF_PRE592_MARCEK_LOAD_SUCCESS_ONE_BYTE_COUNTER_20261109.md").read_text(encoding="utf-8")
 if ("842fbc19031e81adb7988ad3e2fbd2de35850ce19abde581681025c4172ed1b9" not in handoff
     or "Nenhum" not in handoff and "No \\[error\\]" not in handoff and "No \`[error]" not in handoff):
  raise ValueError("Uploaded real-device log summary missing")
 BMW=next(x for x in p["selected_variants_and_control_records"] if x["candidate_names"]==["bmwm3gtr"])
 PUNTO=next(x for x in p["selected_variants_and_control_records"] if x["candidate_names"]==["punto"])
 car=BMW["upgrade_counters_original_signed_i32"]
 punto=PUNTO["upgrade_counters_original_signed_i32"]
 ref=p474["vehicles"]["bmwm3gtr"]["categories_with_explicit_references"]["engine"]
 if (p["field_offsets"]["engine_upgrades"]!=40
     or p["binary_endian"]!="big"
     or car["engine_upgrades"]!=0 or punto["engine_upgrades"]!=4
     or ref["capacity"]!=1 or ref["item_count"]!=1
     or ref["pvehicle_upgrade_limit"]!=0):
  raise ValueError("Original stock/Punto engine reference/counter controls differ")
 if (p501["scratch_engine_counter_bin_relative_offset"]!=256488 or
     p501["scratch_engine_counter_vpak_absolute_offset"]!=256616 or
     p501["synthetic_BMW_engine_upgrade_counter"]!=1 or
     p501["original_BMW_engine_upgrade_counter"]!=0):
  raise ValueError("Source pvehicle 32bit counter candidate differs")
 if (comb["scratch_vpak_bytes"]!=698004 or isol["candidate_VPAK_size"]!=698004
     or comb["source_pal_sha256"]!=p["vpak_sha256"]
     or comb["new_engine_export_id_generated_with_original_class_slash_name_formula"]!="61ade503"
     or comb["new_name_registration_requirement_in_PAL_runtime_unknown"] is not True):
  raise ValueError("Source synthetically enlarged VLT report differs")
 if (isol.get("counter_byte_changed_vs_PRE502")!=[256619] or
     isol.get("pointer_changed_bytes_vs_PRE586")!=[642333,642334,642335]
     or isol.get("active_BMW_pvehicle_refspec_points_to_two_ref_array") is not True
     or isol.get("BMW_pvehicle_motor_upgrade_count_zero") is not True
     or isol.get("candidate_EA_crc32")!="98e13bed"
     or isol.get("new_VLT_engine_collection_preserved") is not True
     or pre586.get("original_BMW_pvehicle_engine_upgrade_counter_retained") is not True
     or pre586.get("original_BMW_pvehicle_ref_fixup_restored") is not True
     or sh.get("actual_device_experiment_executed") is not False):
  raise ValueError("Isolated PRE591 variant or PRE586 ref controls differ")
 if (p490.get("semantic_GetMaxLevel_proven") is not False or
     p490.get("semantic_SetLevel_proven") is not False or
     p490.get("semantic_SetPackage_proven") is not False or
     torque.get("new_engine_collection_added") is not False):
  raise ValueError("Runtime unknowns or successful torque-only control were unexpectedly revised")
 return {
   "stage":"PRE596_BMW_ENGINE_ONE_BYTE_GUEST_COUNTER_SEMANTICS_GATE",
   "status":"AUDIT_OK",
   "source_report_hash_pvehicle":p["vpak_sha256"],
   "original_BMW_engine_upgrade_count":0,
   "original_Punto_engine_upgrade_count":4,
   "original_BMW_engine_RefSpec_count":ref["item_count"],
   "original_BMW_engine_RefSpec_capacity":ref["capacity"],
   "PRE591_active_RefSpec_capacity":2,
   "PRE591_pvehicle_counter_zero":True,
   "PRE502_pvehicle_counter_one":True,
   "counter_32bit_BE_VPAK_absolute_start_offset":256616,
   "single_byte_delta_PRE591_vs_PRE502":[256619],
   "structural_VLT_and_RefSpec_same_except_counter_proven_by_PRE591_builder":True,
   "PRE591_VPAK_sha256":isol["candidate_VPAK_sha256"],
   "PRE502_VPAK_sha256":comb["scratch_vpak_bytes"] and "d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6",
   "PRE591_checksum_EA":isol["candidate_EA_crc32"],
   "PRE502_checksum_EA":"4d05584a",
   "PRE591_device_profile_load_reported_by_user":True,
   "PRE502_combined_device_profile_load_failed_observed_pre573":True,
   "game_runtime_GetMaxLevel_semantics_proven":False,
   "game_runtime_SetLevel_semantics_proven":False,
   "new_collection_StrE_runtime_registration_proven":False,
   "candidate_cause":"motor_level_counter_activation_or_guest_resolve_of_second_RefSpec_entry",
   "causality_fully_proven":False,
   "next_research":"read-only guest GetMaxLevel/SetLevel and new engine name/export lookup trace; do not reapply failed PRE573",
   "recommended_next_device_script_prepared":False,
   "new_game_patch_created":False,
   "phone_game_data_modified":False,
   "save_modified":False,
   "APK_built":False,
   "signing_material_accessed":False
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE596_BMW_ENGINE_ONE_BYTE_GUEST_COUNTER_SEMANTICS_GATE",
  "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
  "new_game_patch_created":False,"phone_game_data_modified":False,
  "save_modified":False,"APK_built":False,"signing_material_accessed":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE596_STATUS",r["status"])
 print("PRE596_ERROR",r.get("error_type","none"),r.get("error",""))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
