#!/usr/bin/env python3
"""PRE478: BMW performance mod OFF-by-default feasibility gates + synthetic tests.
No game binaries or saves read/write. Consumes only previously published
metadata reports from authenticated PAL/USA-identical VPAK investigations.
Not a runtime patch, not a V49 build, and not proof of purchasable upgrades.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("docs")
OUT=Path("/tmp/nfsmw-pre478/report.json")
PIN="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
FILES={
    "identity":"PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json",
    "limits":"PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json",
    "references":"PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json",
    "ancestry":"PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY.json",
    "physics":"PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json",
}
BLOCKED_CATS=("engine","transmission","chassis","tires","brakes","induction")
FIELD={"engine":"engine_upgrades","transmission":"transmission_upgrades",
       "chassis":"chassis_upgrades","tires":"tires_upgrades",
       "brakes":"brakes_upgrades","induction":"induction_upgrades"}
TARGET="bmwm3gtr"
BMW_KEY="cd88083f"
GLOBAL_MAX={"engine":4,"transmission":4,"chassis":3,
            "tires":3,"brakes":4,"induction":3,"nos":3}
BAD_NAMES={"option title","20/20","999.999.999"}

@dataclass(frozen=True)
class Candidate:
    vehicle: str
    category: str
    requested_level: int
    displayed_name: str
    source_catalog_proven: bool=False
    physics_profile_proven: bool=False
    frontend_price_proven: bool=False
    persistence_tested_on_disposable_save: bool=False
    runtime_physics_verified: bool=False
    enabled: bool=False
    disposable_save: bool=False

def reject_reasons(c:Candidate)->list[str]:
    issues=[]
    if c.vehicle!=TARGET: issues.append("NON_TARGET_VEHICLE")
    if c.category not in BLOCKED_CATS: issues.append("CATEGORY_UNSUPPORTED")
    if c.category in GLOBAL_MAX and not (1<=c.requested_level<=GLOBAL_MAX[c.category]):
        issues.append("LEVEL_OUT_OF_RANGE")
    if not c.displayed_name or c.displayed_name.strip().lower() in BAD_NAMES:
        issues.append("INVALID_DISPLAY_NAME")
    if not c.enabled:issues.append("FEATURE_OFF")
    if not c.disposable_save:issues.append("NO_ISOLATED_SAVE")
    if not c.source_catalog_proven:issues.append("NO_PROVEN_PERFORMANCE_CATALOG")
    if not c.physics_profile_proven:issues.append("NO_PROVEN_BMW_SPECIFIC_PHYSICS_PROFILES")
    if not c.frontend_price_proven:issues.append("NO_PROVEN_FRONTEND_PRICE")
    if not c.persistence_tested_on_disposable_save:issues.append("NO_PROVEN_SAVE_ROUNDTRIP")
    if not c.runtime_physics_verified:issues.append("NO_RUNTIME_PHYSICS_REGRESSION")
    return issues

class FailClosedTests(unittest.TestCase):
    def make(self,**kw):
        sample=dict(vehicle=TARGET,category="engine",requested_level=1,
             displayed_name="Synthetic validated profile",enabled=True,
             disposable_save=True,source_catalog_proven=True,
             physics_profile_proven=True,frontend_price_proven=True,
             persistence_tested_on_disposable_save=True,runtime_physics_verified=True)
        sample.update(kw)
        return Candidate(**sample)
    def test_synthetic_all_gates_pass(self):
        self.assertEqual(reject_reasons(self.make()),[])
    def test_feature_off(self):
        self.assertIn("FEATURE_OFF",reject_reasons(self.make(enabled=False)))
    def test_other_car(self):
        self.assertIn("NON_TARGET_VEHICLE",reject_reasons(self.make(vehicle="punto")))
    def test_careerstart_not_inadvertently_selected(self):
        self.assertIn("NON_TARGET_VEHICLE",reject_reasons(self.make(vehicle="m3gtre46careerstart")))
    def test_zero_and_overlimit(self):
        for level in (0,5):
            self.assertIn("LEVEL_OUT_OF_RANGE",reject_reasons(self.make(requested_level=level)))
    def test_unverified_catalog(self):
        self.assertIn("NO_PROVEN_PERFORMANCE_CATALOG",reject_reasons(self.make(source_catalog_proven=False)))
    def test_unverified_physics(self):
        self.assertIn("NO_PROVEN_BMW_SPECIFIC_PHYSICS_PROFILES",reject_reasons(self.make(physics_profile_proven=False)))
    def test_invalid_titles(self):
        for val in ("", "Option title","20/20","999.999.999"):
            self.assertIn("INVALID_DISPLAY_NAME",reject_reasons(self.make(displayed_name=val)))
    def test_no_price_or_save(self):
        self.assertIn("NO_PROVEN_FRONTEND_PRICE",reject_reasons(self.make(frontend_price_proven=False)))
        self.assertIn("NO_PROVEN_SAVE_ROUNDTRIP",reject_reasons(self.make(persistence_tested_on_disposable_save=False)))
    def test_no_marcek(self):
        self.assertIn("NO_ISOLATED_SAVE",reject_reasons(self.make(disposable_save=False)))
    def test_nitro_not_modified(self):
        self.assertIn("CATEGORY_UNSUPPORTED",reject_reasons(self.make(category="nos")))

def read_reports():
    docs={}
    for tag,name in FILES.items():
        doc=json.loads((ROOT/name).read_text())
        if doc.get("status")!="AUDIT_OK":
            raise ValueError("Unverified "+tag+" report")
        docs[tag]=doc
    if (docs["identity"].get("pal_target_sha256")!=PIN
        or not docs["identity"].get("pal_resource_identical_to_usa_reference")
        or docs["limits"].get("vpak_sha256")!=PIN
        or docs["references"].get("vpak_sha256")!=PIN
        or docs["ancestry"].get("source_pal_vpak_sha256")!=PIN
        or docs["physics"].get("source_sha256")!=PIN):
        raise ValueError("PAL source SHA proof mismatch")
    return docs

def static_audit():
    docs=read_reports()
    limits={}
    for row in docs["limits"]["selected_variants_and_control_records"]:
        if TARGET in row.get("candidate_names",[]):
            if limits:raise ValueError("Duplicate BMW original counter profile")
            limits=row["upgrade_counters_original_signed_i32"]
    if not limits:raise ValueError("Missing BMW original counters")
    found=docs["references"]["vehicles"][TARGET]["categories_with_explicit_references"]
    p=docs["physics"]["class_models"]
    trees=docs["ancestry"]["vehicles"][TARGET]
    results={}
    for category in BLOCKED_CATS:
        initial=limits[FIELD[category]]
        if initial!=0:raise ValueError("The expected stock zero changed in "+category)
        refs=found.get(category)
        mapped=trees.get(category)
        physical=p.get(category,{}).get("collections",{}).get(TARGET,{})
        valid_original=bool(refs and refs.get("array_header_valid") and
           mapped and mapped.get("explicit_field_found") and
           physical.get("has_bounded_layout"))
        if category=="induction":
            valid_original=bool(not refs and not (mapped or {}).get("explicit_field_found"))
        if not valid_original:
            raise ValueError("Original category data mismatch "+category)
        missing_support = category=="induction" or int(refs.get("item_count",0))==1
        sample=Candidate(vehicle=TARGET,category=category,requested_level=1,
                          displayed_name="UNVERIFIED PROFILE",enabled=False,
                          disposable_save=False)
        reasons=reject_reasons(sample)
        if not reasons:raise ValueError("Fail-closed gate unexpectedly open")
        results[category]={
           "original_upgrade_limit":initial,
           "original_explicit_reference_count":refs.get("item_count",0) if refs else 0,
           "original_BMW_physical_base_verified":bool(physical.get("has_bounded_layout")),
           "missing_BMW_upgrade_profiles_or_reference_coverage":missing_support,
           "synthetic_plan_rejection_reasons":reasons,
           "modification_permitted":False,
        }
    if docs["physics"].get("all_required_bounded_layouts_found") is not True:
        raise ValueError("PRE477 required layout validation false")
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE478_BMW_TUNING_FEATURE_OFF_CONTRACT", "status":"FAILED",
            "mod_enabled":False, "save_modified":False,
            "apk_built":False, "game_assets_modified":False}
    try:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(FailClosedTests)
        import io
        buffer=io.StringIO()
        outcome=unittest.TextTestRunner(stream=buffer,verbosity=0).run(suite)
        if not outcome.wasSuccessful():
            raise ValueError("Synthetic contract rejected: "+buffer.getvalue()[:600])
        results=static_audit()
        report.update({"status":"AUDIT_OK","authenticated_pal_vpak_sha256":PIN,
          "source_reports":FILES,
          "synthetic_tests_passed":outcome.testsRun,
          "synthetic_test_suite_is_not_gameplay_validation":True,
          "target_vehicle":TARGET,"careerstart_not_targeted":True,
          "original_nitro_left_unchanged":True,
          "blocked_categories":results,
          "catalog_of_purchaseable_bmw_upgrades_validated":False,
          "runtime_patch_written":False,
          "ready_for_signed_APK":False})
    except Exception as e:
        report.update({"error_type":type(e).__name__,"error":str(e)[:250]})
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE478_STATUS",report["status"],flush=True)
    print("PRE478_TESTS",report.get("synthetic_tests_passed",0),flush=True)
    print("PRE478_GATE_CLOSED",report.get("ready_for_signed_APK") is False,flush=True)
    print("PRE478_ERROR",report.get("error","none"),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
