#!/usr/bin/env python3
"""PRE302: authenticated PRE99 PAL BMW menu branch/option-call trace.
Pure read-only inspection, no source patch, no APK, no signing and no save access.
Bounded excerpts permit human verification of guest PPC control flow.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp"
SOURCE_SHA="26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07"
FN="sub_82578988"
TARGET="__imp__sub_82575370(ctx, base);"
COMPARE="cr6.compare<int32_t>(ctx.r3.s32, 41, xer);"
OUT=Path("/tmp/nfsmw-pre302/PRE302_PAL_MAIN_MENU_BRANCH_CALL_SITES.json")
def sha(b):return hashlib.sha256(b).hexdigest()
def must(x,label):
    if not x:raise AssertionError(label)
def window(lines,n,before=14,after=25):
    return [{"rel_line":i+1,"line":lines[i].strip()[:220]} for i in range(max(0,n-before),min(len(lines),n+after+1))]
def audit(temp:Path):
    archive=temp/"pre99.tar.gz"
    download(drive_client(),archive)
    digest,_,size=sha_file(archive)
    must(digest==EXPECTED_SHA256 and size==EXPECTED_BYTES,"PRE99 fingerprint mismatch")
    with tarfile.open(archive,"r:gz") as tar:
        member=next((m for m in tar if m.isfile() and m.name.lstrip("./")==SOURCE),None)
        must(member is not None and 0<member.size<8_000_000,"PAL source member invalid")
        f=tar.extractfile(member);must(f is not None,"source stream missing")
        raw=f.read()
    must(sha(raw)==SOURCE_SHA,"PAL source fingerprint changed")
    source=raw.decode("utf8")
    body=body_for_function(source,FN)
    lines=body.splitlines()
    cmps=[i for i,s in enumerate(lines) if COMPARE in s]
    calls=[i for i,s in enumerate(lines) if TARGET in s]
    must(len(cmps)==1 and len(calls)==5,"menu anchors changed")
    bne=[i for i,s in enumerate(lines) if "bne cr6,0x825789c0" in s]
    must(len(bne)==1,"BMW branch not unique")
    label=[i for i,s in enumerate(lines) if "loc_825789C0:" in s]
    must(len(label)==1,"branch target absent")
    options=[{"index":k+1,"rel_line":i+1,
              "window":window(lines,i,17,15),
              "preceding_guest_pc":[s.strip() for s in lines[max(0,i-24):i] if "ctx.lr = " in s][-2:]} for k,i in enumerate(calls)]
    # Bounded control-flow evidence, not a claim about runtime branch selection.
    interesting=[i for i,s in enumerate(lines) if re.search(r"(?i)//\s*(?:cmpwi|bne|beq|b\s|li\s+r10|mr\s+r3|lwz)|REX_(?:LOAD|STORE)_U32",s)]
    out={"stage":"PRE302_PAL_BMW_MAIN_MENU_CONTROL_FLOW",
         "status":"AUDIT_OK","pre99_sha256":digest,
         "source_sha256":sha(raw),"function":FN,"source_path":SOURCE,
         "runtime_marker_observed_in_v39":"NFSMW_PRE292_BMW_MENU callsite=0x82578988 type=41 event=1",
         "marker_value_is_pre_branch_or_post_compare":"post_compare_before_branch_resolution",
         "function_lines":len(lines),"menu_add_option_calls":len(calls),
         "comparison_at_line":cmps[0]+1,"compare_context":window(lines,cmps[0],20,36),
         "conditional_branch_at_line":bne[0]+1,
         "conditional_branch_context":window(lines,bne[0],15,28),
         "branch_target_line":label[0]+1,
         "branch_target_context":window(lines,label[0],12,25),
         "option_calls":options,
         "function_control_flow_summary":[{"rel_line":i+1,"line":lines[i].strip()[:200]} for i in interesting[:115]],
         "metadata":{"source_modified":False,"apk_built":False,
                     "signer_accessed":False,"save_modified":False,
                     "menu_branch_forced":False},
         "limitations":[
           "Runtime log confirms model 41 reached this callback, not whether cr6.eq was taken",
           "Presence of five option calls in static function does not prove each executed",
           "Translation of each option call to Visual/Parts/Performance requires separate mapping",
           "Missing customization shop resources cannot yet be claimed causal"
         ]}
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("invalid run ID")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE302_PAL_BMW_MAIN_MENU_CONTROL_FLOW","status":"AUDIT_FAILED","apk_built":False,
            "signer_accessed":False,"save_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre302_") as t:
            result=audit(Path(t))
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    for field in ("status","menu_add_option_calls","comparison_at_line","conditional_branch_at_line","branch_target_line"):
        print("PRE302_"+field.upper(),result.get(field))
    print("PRE302_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
