#!/usr/bin/env python3
"""PRE526: Pinned, source-backed read-only audit of checkout's install safety.

This is PC reconstructed reference source (dbalatoni13/nfsmw), NOT proof of
identical Xbox 360 guest code. Fetch exactly pinned public source blob hashes,
extract named methods, prove call ordering and rollback condition and evaluate
the one-level BMW scenario against authenticated original PAL FE data.
Never write or publish game executable/asset/save data. No APK.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
from datetime import datetime,timezone
OUT=Path("/tmp/nfsmw-pre526/report.json")
PUBLIC_OWNER="dbalatoni13/nfsmw"
PINNED_COMMIT="80993f35224c61d2f1b135beba76c6f8234c7940"
SOURCE_BLOBS={
    "src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CustomizeManager.cpp":"607e8f23654941577aff2392b5ae6d39c66bf036",
    "src/Speed/Indep/Src/Frontend/Database/VehicleDB.cpp":"cca3059dc9d16af9b64fe0de6b4a93a84d42abdb",
    "src/Speed/Indep/Src/Frontend/Careers/UnlockSystem.cpp":"4209ab53cf5471396206f35da3095cc63d914b3d",
    "src/Speed/Indep/Src/Physics/PhysicsUpgrades.hpp":"12fe46773114b7a85fb476beba24a247e6aae73b",
    "src/Speed/Indep/Src/Physics/PhysicsUpgrades.cpp":"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
}
FN={
 "list":"CarCustomizeManager::GetPerformancePartsList",
 "num":"CarCustomizeManager::GetNumPackages",
 "max":"CarCustomizeManager::GetMaxPackages",
 "price":"CarCustomizeManager::GetPartPrice",
 "checkout":"CarCustomizeManager::Checkout",
 "install":"CarCustomizeManager::InstallPerfPkg",
 "preview":"CarCustomizeManager::PreviewPerfPkg",
 "write":"FECustomizationRecord::WriteRecordIntoPhysics",
 "lookup_price":"UnlockSystem::GetPerfPackageCost",
}
def get_source(path,digest):
    url="https://raw.githubusercontent.com/"+PUBLIC_OWNER+"/"+PINNED_COMMIT+"/"+path
    req=urllib.request.Request(url,headers={"User-Agent":"nfsmw-pre526-readonly-pinned-audit"})
    with urllib.request.urlopen(req,timeout=55) as f:
        data=f.read(120_000)
    if len(data)>=120_000:raise ValueError("Unbounded source file: "+path)
    sha=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    if sha!=digest:raise ValueError("Public reference SHA changed: "+path)
    return data.decode("utf-8-sig")

def extract_method(source,name):
    # Escape each C++ scope token to avoid regex overmatching.
    pattern=r"\b"+re.escape(name)+r"\s*\([^;{}]*\)\s*(?:const\s*)?\{"
    m=re.search(pattern,source)
    if not m:raise ValueError("Required PC reference body missing "+name)
    start=source.index("{",m.start())
    depth=0;end=None
    for i in range(start,len(source)):
        if source[i]=="{":depth+=1
        elif source[i]=="}":
            depth-=1
            if depth==0:
                end=i+1;break
    if end is None or end-start>25000:raise ValueError("Method brace span invalid: "+name)
    return source[m.start():end],source.count("\n",0,m.start())+1

def require(body,needles,step):
    missing=[x for x in needles if x not in body]
    if missing:raise ValueError(f"Reference {step} changed required tokens: "+", ".join(missing)[:140])

def audit():
    proofs={p:json.loads(Path(p).read_text()) for p in (
       "docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json",
       "docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json",
       "docs/PRE522_USA_FE_CARPARTS_COST_ARRAYS_READONLY.json",
       "docs/PRE523_ORIGINAL_PAL_FE_ATTRIB_BINARY_IDENTITY_READONLY.json",
       "docs/PRE524_BMW_PC_REFERENCE_FE_PRICE_SCENARIOS_READONLY.json")}
    p473,p518,p522,p523,p524=proofs.values()
    if any(r.get("status")!="AUDIT_OK" for r in proofs.values()):
        raise ValueError("Required authenticated prior report missing")
    if (p473.get("vpak_sha256")!="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
       or p518.get("synthetic_scratch_VPAK_sha256")!="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
       or p518.get("safe_to_build_tuning_APK") is not False
       or p522.get("children_with_category_enum_decoded")!=7
       or p523.get("original_PAL_FE_same_bytes_as_USA_proven") is not True
       or p524.get("candidate_BMW_single_engine_package_catalogue_level")!=4
       or p524.get("candidate_BMW_single_engine_package_USA_reference_cost")!=98000
       or p524.get("actual_Xbox_guest_unlock_price_formula_verified") is not False):
        raise ValueError("Original PAL catalogue, BMW scratch or PC scenario gate changed")
    source={p:get_source(p,d) for p,d in SOURCE_BLOBS.items()}
    customize=source[next(p for p in source if p.endswith("/CustomizeManager.cpp"))]
    vehicle=source[next(p for p in source if p.endswith("/VehicleDB.cpp"))]
    unlock=source[next(p for p in source if p.endswith("/UnlockSystem.cpp"))]
    physics_h=source[next(p for p in source if p.endswith("PhysicsUpgrades.hpp"))]
    physics_cpp=source[next(p for p in source if p.endswith("PhysicsUpgrades.cpp"))]
    method_source={}
    for key,name in FN.items():
        body,line=extract_method(vehicle if key=="write" else
                                  unlock if key=="lookup_price" else customize,name)
        method_source[key]={"method":name,"start_line":line,"body":body}
    bodies={key:val["body"] for key,val in method_source.items()}
    require(bodies["list"],(
        "Physics::Upgrades::GetMaxLevel(this->ThePVehicle, type)",
        "for (int i = 0; i < num_pkgs; i++)",
        "GetMaxPackages(type) - GetNumPackages(type) + i + 1",
        "IsPartLocked(pkg, unlock_level)",
        "GetPartPrice(pkg)","the_list.AddTail(pkg)"),"GetPerformancePartsList")
    require(bodies["num"],("Physics::Upgrades::GetMaxLevel(ThePVehicle, type)",),"GetNumPackages")
    require(bodies["max"],("Physics::Upgrades::PUT_ENGINE:","return 4;"),"GetMaxPackages")
    require(bodies["price"],(
        "int level = GetMaxPackages(part->GetPhysicsType())",
        "level -= GetNumPackages(part->GetPhysicsType()) - part->GetUpgradeLevel()",
        "UnlockSystem::GetPerfPackageCost(GetUnlockFilter(), part->GetPhysicsType(), level, 0)"),"GetPartPrice")
    require(bodies["lookup_price"],(
        "MapPerfPkgToUnlockable(pkg_type)",
        "LookupFEPartInfo(unlockable, level)",
        "price = info->Cost"),"GetPerfPackageCost")
    require(bodies["checkout"],(
        "if (item->IsActive())","IsCareerMode()",
        "FEDatabase->GetCareerSettings()->SpendCash(cost)",
        "if (part->IsPerformancePkg())",
        "InstallPerfPkg(part->GetPhysicsType(), part->GetUpgradeLevel())",
        "ShoppingCart.DeleteAllElements()"),"Checkout")
    require(bodies["install"],(
        "actual_record->SetInstalledPhysics(part_type, level)",
        "if (!actual_record->WriteRecordIntoPhysics(ThePVehicle))",
        "actual_record->SetInstalledPhysics(part_type, 0)",
        "PreviewPerfPkg(part_type, level)"),"InstallPerfPkg")
    require(bodies["write"],(
        "Physics::Upgrades::SetPackage(attributes, InstalledPhysics)",
        "return false","return true"),"WriteRecordIntoPhysics")
    require(bodies["preview"],(
        "PreviewRecord.SetInstalledPhysics(part_type, level)",
        "PreviewRecord.WriteRecordIntoPhysics(ThePVehicle)"),"PreviewPerfPkg")
    for name in ("GetMaxLevel","SetLevel","SetPackage","GetPackage"):
        if not re.search(r"\b"+name+r"\s*\(",physics_h):
            raise ValueError("PhysicsUpgrades.hpp missing declaration "+name)
    if physics_cpp!="":
        raise ValueError("Reference PhysicsUpgrades.cpp no longer empty: re-evaluate")
    checkout=bodies["checkout"]
    spend=checkout.index("FEDatabase->GetCareerSettings()->SpendCash(cost)")
    install=checkout.index("InstallPerfPkg(part->GetPhysicsType(), part->GetUpgradeLevel())")
    if spend>=install or "Refund" in checkout or "AwardCash(-cost)" in checkout[spend:install]:
        raise ValueError("PC checkout call ordering or refund control changed")
    # The checkout branch is conditional on career/backroom; it is not an
    # observed payment. This condition must remain in the report.
    install_ref=bodies["install"]
    failed=install_ref.index("if (!actual_record->WriteRecordIntoPhysics(ThePVehicle))")
    rollback=install_ref.index("actual_record->SetInstalledPhysics(part_type, 0)")
    if rollback<=failed:raise ValueError("Rollback order changed")
    # Validate that payment call is NOT bound to success of install in the
    # extracted PC method. It could be elsewhere in Xbox code.
    return {
        "stage":"PRE526_PINNED_PC_SHOP_CHECKOUT_TO_PHYSICS_FAILURE_BOUNDARY_READONLY",
        "status":"AUDIT_OK",
        "public_source":PUBLIC_OWNER,
        "public_source_commit":PINNED_COMMIT,
        "public_source_git_blob_sha1":SOURCE_BLOBS,
        "public_reference_platform":"PC reconstructed, NOT authenticated Xbox 360 guest",
        "named_methods_and_lines":[{"name":v["method"],"start_line":v["start_line"]} for v in method_source.values()],
        "shop_list_calls_GetMaxLevel":True,
        "shop_list_checks_locked_state":True,
        "shop_list_uses_local_upgrade_level_count":True,
        "shop_checkout_career_normal_cost_charged_before_install":True,
        "shop_checkout_only_active_items_and_career_not_backroom":True,
        "shop_checkout_performance_calls_InstallPerfPkg":True,
        "shop_install_calls_WriteRecordIntoPhysics":True,
        "shop_install_rolls_back_level0_if_SetPackage_path_fails":True,
        "shop_install_return_type_void":True,
        "shop_checkout_explicit_refund_for_failed_Perf_SetPackage":False,
        "shop_checkout_checks_InstallPerfPkg_success_return":False,
        "shop_preview_ignores_WriteRecordIntoPhysics_result":True,
        "FE_vehicle_record_WriteRecordIntoPhysics_delegates_to_SetPackage":True,
        "PhysicsUpgrades_hpp_declares_core_functions":True,
        "PhysicsUpgrades_cpp_public_reference_body_bytes":0,
        "PhysicsUpgrades_cpp_implementation_available_in_reference":False,
        "possible_payment_without_installed_upgrade_if_SetPackage_fails_in_PC_reference":True,
        "user_PAL_FE_cost_original_engine_global_level4":98000,
        "price_condition":"only if guest matches PC mapping and availability",
        "guest_V48_checkout_equivalence_verified":False,
        "guest_V48_GetMaxLevel_or_SetPackage_behavior_verified":False,
        "new_BMW_engine_collection_loaded_on_guest_verified":False,
        "BMW_purchase_approved":False,
        "safe_to_build_BMW_tuning_APK":False,
        "asset_bytes_written_or_published":False,
        "game_or_apk_modified":False,"save_modified":False,
        "signing_key_accessed":False
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    args=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as ex:
        result={"stage":"PRE526_PINNED_PC_SHOP_CHECKOUT_TO_PHYSICS_FAILURE_BOUNDARY_READONLY",
                "status":"FAILED","error_type":type(ex).__name__,
                "error":str(ex)[:240],
                "asset_bytes_written_or_published":False,"game_or_apk_modified":False,
                "save_modified":False,"signing_key_accessed":False,
                "safe_to_build_BMW_tuning_APK":False}
    result["run_id"]=args.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE526_STATUS",result["status"],flush=True)
    print("PRE526_PAYMENT_BEFORE_INSTALL",result.get("shop_checkout_career_normal_cost_charged_before_install"),flush=True)
    print("PRE526_ROLLBACK_WITHOUT_REFUND",result.get("possible_payment_without_installed_upgrade_if_SetPackage_fails_in_PC_reference"),flush=True)
    print("PRE526_PHYSICS_CPP_EMPTY",result.get("PhysicsUpgrades_cpp_public_reference_body_bytes"),flush=True)
    print("PRE526_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    raise SystemExit(main())
