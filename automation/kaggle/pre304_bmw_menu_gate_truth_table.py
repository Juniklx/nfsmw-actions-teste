#!/usr/bin/env python3
"""PRE304: verify both original PAL BMW menu branches from exact PRE302 evidence.
Uses final authenticated PRE302 metadata only; no game archive, APK or signing.
"""
import argparse, json, hashlib, sys
from pathlib import Path
OUT=Path("/tmp/nfsmw-pre304/PRE304_BMW_MENU_GATE_TRUTH_TABLE.json")
def check(x,label):
 if not x:raise ValueError(label)
def source_lines(report):
 d={}
 for section in ("compare_context","conditional_branch_context","branch_target_context"):
  for row in report[section]:d[row["rel_line"]]=row["line"]
 for option in report["option_calls"]:
  for row in option["window"]:d[row["rel_line"]]=row["line"]
 return d
def main():
 p=argparse.ArgumentParser();p.add_argument("--input",required=True);a=p.parse_args()
 result={"stage":"PRE304_BMW_MENU_GATE_TRUTH_TABLE","status":"AUDIT_FAILED",
         "game_code_patched":False,"apk_built":False,"save_modified":False,
         "signer_accessed":False,"hero_override_enabled":False}
 try:
  data=Path(a.input).read_bytes();source=json.loads(data);d=source_lines(source)
  check(source["status"]=="AUDIT_OK","PRE302 not approved")
  check(source["source_sha256"]=="26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07","PAL source changed")
  guards={36:"if (!cr6.eq) goto loc_825789C0;",38:"ctx.r10.s64 = 1;",
   49:"if (!cr6.eq) goto loc_82578A30;",55:"if (!cr6.eq) goto loc_82578A24;",
   98:"goto loc_82578A84;",105:"if (!cr6.eq) goto loc_82578A7C;",
   92:"loc_82578A24:",99:"loc_82578A30:",140:"loc_82578A7C:",145:"loc_82578A84:"}
  for k,v in guards.items():check(d.get(k)==v,"PPC guard mismatch line "+str(k))
  for n,expected in [(1,2049),(2,2050),(3,2049),(4,2050),(5,2051)]:
   row=source["option_calls"][n-1]
   check(any("ctx.r7.s64 = "+str(expected)+";" in x["line"] for x in row["window"]), "option code mismatch "+str(n))
  check(len(source["option_calls"])==5,"unexpected option calls")
  table=[]
  for model in [0,40,41,42,81]:
   for global_flag in (0,1):
    hero=int(model==41)
    if global_flag==0:sites=[] if hero else [1,2]
    else:sites=[] if hero else [3,4]
    sites.append(5)
    codes=[(2049 if site in (1,3) else 2050 if site in (2,4) else 2051) for site in sites]
    table.append({"model":model,"global_flag":global_flag,"hero_flag":hero,
       "source_option_call_sites":sites,"option_codes":codes})
    check(codes==([2051] if hero else [2049,2050,2051]),"truth table inconsistent")
  result.update({"status":"AUDIT_OK","pre302_sha256":hashlib.sha256(data).hexdigest(),
    "gate_uses_model_type_41":True,"gate_is_branch_relevant":True,
    "both_global_modes_evaluated":True,"option_codes_special_car":[2051],
    "option_codes_other_car":[2049,2050,2051],"truth_table":table,
    "observed_20261107_model_41":True,
    "not_proven":["category localization for 2049/2050/2051",
                  "menu items usable for HeroCar after bypass",
                  "save/ownership validation for customizing special car",
                  "global flag value in actual runtime"],
    "next":"Passive V40 logs menu option IDs/branch, no override"})
 except Exception as exc:result["failure_type"]=type(exc).__name__
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2)+"\n")
 print("PRE304_STATUS",result["status"])
 print("PRE304_GATE_CONFIRMED",result.get("gate_is_branch_relevant"))
 print("PRE304_HERO_CODES",result.get("option_codes_special_car"))
 print("PRE304_OTHER_CODES",result.get("option_codes_other_car"))
 print("PRE304_FAILURE_TYPE",result.get("failure_type"))
 return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
