#!/usr/bin/env python3
"""PRE458: authenticated PRE99 metadata inventory for a safe BMW M3 GTR tuning mod.
No source/game assets exported, no guest calls, no APK, no saved-game changes.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tarfile, tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, looks_sensitive, safe_member_name, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre446_bmw_zero_branch_readonly import ROOT, TARGETS

OUT=Path("/tmp/nfsmw-pre458/report.json")
MENU=ROOT+"nfsmw_recomp.11.cpp"
PINS={ROOT+x[0]:(key,x[1],x[2]) for key,x in TARGETS.items()}
MATCH={
 "bmw_car_asset": r"(bmwm3|m3gtr|bmw.?m3|m3gtre46)",
 "performance_data": r"(upgrad|perform|tuning|tune|vlt|attrib|physics)",
 "car_data": r"(?:^|[/\\])(cars?|vehicle)(?:[/\\]|$)",
 "global_or_frontend": r"(?:^|[/\\])(global|frontend)(?:[/\\]|[._])",
 "disc_resource": r"\.(?:lzc|bin|bndl|xex|vlt|nfs|dat)$",
}
RE={k:re.compile(v,re.I) for k,v in MATCH.items()}
CATEGORIES={4:"engine",3:"transmission",2:"suspension",6:"nitrous",0:"tires",1:"brakes",5:"induction"}

def synthetic_contract():
    def allowed(enabled,car,cat,count,part_id,known):
        return (enabled and car==41 and cat in CATEGORIES and count>0 and
                part_id is not None and part_id in known)
    tests={
      "off_rejects": not allowed(False,41,4,4,11,{11}),
      "zero_rejects": not allowed(True,41,4,0,11,{11}),
      "unknown_part_rejects": not allowed(True,41,4,4,999,{11}),
      "other_car_rejects": not allowed(True,74,4,4,11,{11}),
      "synthetic_known_part_passes": allowed(True,41,4,4,11,{11}),
    }
    if not all(tests.values()):raise ValueError("Synthetic fail-closed gate")
    return tests

def audit():
    contract=synthetic_contract()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre458-") as tmp:
        arc=Path(tmp)/"pre99.tar.gz"
        download(drive_client(),arc)
        digest,_,size=sha_file(arc)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 fingerprint mismatch")
        samples={k:[] for k in MATCH}
        counts=Counter()
        source={}
        pin_status={}
        total_files=0
        with tarfile.open(arc,"r:gz",errorlevel=2) as tar:
            for m in tar:
                if not m.isfile():continue
                total_files+=1
                name=m.name.lstrip("./")
                if not safe_member_name(name):raise ValueError("Unsafe archive path")
                if looks_sensitive(name) or not name.startswith("workspace/"):continue
                for k,pattern in RE.items():
                    if pattern.search(name):
                        counts[k]+=1
                        if len(samples[k])<90 and "generated/default/nfsmw_recomp." not in name:
                            samples[k].append({"path":name[:250],"bytes":m.size})
                if name in PINS:
                    key,pin,fn=PINS[name]
                    if m.size>7_000_000:raise ValueError("Oversized PAL "+key)
                    fp=tar.extractfile(m)
                    if fp is None:raise ValueError("Missing PAL "+key)
                    raw=fp.read()
                    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError("PIN_MISMATCH "+key)
                    source[key]=body_for_function(raw.decode("utf-8"),fn)
                    pin_status[key]=pin
                elif name==MENU:
                    if m.size>7_000_000:raise ValueError("Oversized PAL menu")
                    fp=tar.extractfile(m)
                    if fp is None:raise ValueError("Missing PAL menu")
                    raw=fp.read()
                    source["menu"]=body_for_function(raw.decode("utf-8"),"sub_82582F70")
                    pin_status["menu_sha256"]=hashlib.sha256(raw).hexdigest()
        if set(source)!=(set(TARGETS)|{"menu"}):
            raise ValueError("Source function missing: "+str(sorted(source)))
        look,build,menu=source["lookup"],source["builder"],source["menu"]
        checks={
          "lookup_reads_category": "ctx.r4.s32" in look,
          "lookup_resolves_attribute": "__imp__sub_8214B858(ctx, base);" in look,
          "lookup_has_fallback": "-2100953088" in look and "-2672" in look,
          "builder_first_lookup": "ctx.lr = 0x8256F83C;" in build,
          "builder_skips_nonpositive": "if (!cr6.gt) goto loc_8256F990;" in build,
          "menu_builder_call": "__imp__sub_8256F818(ctx, base);" in menu,
        }
        if not all(checks.values()):raise ValueError("Unexpected PAL control flow "+str(checks))
        return {
          "stage":"PRE458_BMW_TUNING_CATALOG_INVENTORY_READONLY","status":"AUDIT_OK",
          "pre99_sha256":digest,"pre99_bytes":size,"total_files":total_files,
          "pinned_source_sha256":pin_status,"source_control_flow":checks,
          "inventory_counts":dict(counts),"inventory_filename_samples":samples,
          "synthetic_contract":contract,
          "bmw_car_type_from_v48_logs":41,"punto_car_type_from_v48_logs":74,
          "parts_or_catalog_validated":False,
          "bmw_mod_enabled":False,
          "safe_to_enable_performance_purchases":False,
          "game_assets_exported":False,"game_source_exported":False,
          "guest_executed":False,"save_modified":False,"signed_apk_built":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: result=audit()
    except Exception as e:
        result={"stage":"PRE458_BMW_TUNING_CATALOG_INVENTORY_READONLY",
                "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
                "save_modified":False,"signed_apk_built":False}
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE458_STATUS",result["status"],flush=True)
    print("PRE458_CONTROL_FLOW",result.get("source_control_flow",{}),flush=True)
    print("PRE458_INVENTORY_COUNTS",result.get("inventory_counts",{}),flush=True)
    print("PRE458_ERROR",result.get("error_type","none"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
