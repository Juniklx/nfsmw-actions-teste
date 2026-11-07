#!/usr/bin/env python3
"""PRE291: pinned source-only BMW MAIN MENU trace recipe; no APK, patch or signer.
The PRE283/V38 probe belongs to performance Setup, not menu construction.
An in-memory guarded callback observes model type at exactly one PAL PPC site.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, tarfile, tempfile, re
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre264_bmw_hero_menu_patch_dryrun import SOURCE,SOURCE_SHA,FUNCTION,MODEL_CMP,ANCHORS

OUT=Path("/tmp/nfsmw-pre291/PRE291_BMW_MAIN_MENU_PASSIVE_TRACE_DRYRUN.json")
TRACE_FLAG="NFSMW_PRE291_BMW_MAIN_MENU_TRACE_ENABLE"
TRACE_CALLBACK="NFSMW_PRE291_BMW_MAIN_MENU_TRACE"
MARKER="NFSMW_PRE291_BMW_MENU_PASSIVE"
PROTOTYPE='\nextern "C" void '+TRACE_CALLBACK+'(unsigned int,unsigned int) noexcept;\n'
INJECTION=(
 "\t// "+MARKER+": passive model/type at exact PAL menu compare.\n"
 "#if defined("+TRACE_FLAG+") && "+TRACE_FLAG+"\n"
 "\t"+TRACE_CALLBACK+"(ctx.r3.u32,0x82578988u);\n"
 "#endif\n"
)
def sha(data):return hashlib.sha256(data).hexdigest()
def check(ok,msg):
    if not ok:raise ValueError(msg)

def audit():
    with tempfile.TemporaryDirectory(prefix="pre291_readonly_") as tmp:
        archive=Path(tmp)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        check(digest==EXPECTED_SHA256 and size==EXPECTED_BYTES,"authenticated PRE99 archive mismatch")
        raw=None
        with tarfile.open(archive,"r:gz",errorlevel=2) as t:
            for mem in t:
                if not mem.isfile() or mem.name.lstrip("./")!=SOURCE:continue
                check(mem.size<5_000_000,"source size outside bound")
                f=t.extractfile(mem)
                check(f is not None,"unreadable source")
                raw=f.read()
                check(len(raw)==mem.size,"truncated source")
                break
        check(raw is not None,"missing generated menu source")
        check(sha(raw)==SOURCE_SHA,"PAL source unexpected fingerprint")
        text=raw.decode("utf8")
        body=body_for_function(text,FUNCTION)
        check(body.count(MODEL_CMP)==1,"unique model41 comparison absent")
        check(all(body.count(a)==1 for a in ANCHORS),"known PPC context changed")
        check(body.count("__imp__sub_82575370(ctx, base);")==5,"expected option calls changed")
        check(body.count("ctx.lr = 0x825789B0;\n\t__imp__sub_822CC740(ctx, base);")==1,"known gettype call absent")
        check(MARKER not in text and TRACE_CALLBACK not in text,"trace already present")
        guest_compare=body.find(MODEL_CMP)
        guest_typecall=body.find("ctx.lr = 0x825789B0;")
        check(0<=guest_typecall<guest_compare,"type-call not before model comparison")
        revised=body.replace(MODEL_CMP,MODEL_CMP+INJECTION,1)
        m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",text)
        check(m is not None,"cannot place callback prototype")
        modified=text.replace(body,revised,1)
        modified=modified[:m.start()]+PROTOTYPE+modified[m.start():]
        check(modified.count(TRACE_CALLBACK+"(")==2,"expected one prototype and one callback")
        check(modified.count(MARKER)==1,"marker duplicated")
        check(modified.replace(PROTOTYPE,"",1).replace(revised,body,1)==text,"nonlocal changes")
        for name in ["REX_LOAD_U32(","REX_STORE_U32(","__imp__sub_82575370(ctx, base);"]:
            check(modified.count(name)==text.count(name),"original guest operation changed")
        return {
            "stage":"PRE291_BMW_MAIN_MENU_PASSIVE_TRACE_IN_MEMORY",
            "status":"AUDIT_OK","PRE99_sha256":digest,
            "pal_source":SOURCE,"pal_sha256":SOURCE_SHA,
            "function":FUNCTION,"candidate_main_menu_guest_pc":"0x82578988",
            "different_V38_setup_probe":"0x82582F70",
            "probe_site":"one source location immediately after model-type compare",
            "probe_event_values":["PPC model/type r3","fixed source function identifier"],
            "not_capturing":["user save","session credentials","other models telemetry in release"],
            "feature_macro":TRACE_FLAG,"feature_enabled_by_default":False,
            "new_logger_required_before_native_build":True,
            "menu_add_option_calls":5,
            "dryrun_source_sha256":sha(modified.encode("utf8")),
            "exact_reversible":True,
            "no_game_guest_reads_added":True,
            "no_game_guest_writes_added":True,
            "not_a_menu_unlock":True,"ready_to_build_apk":False,
            "apk_built":False,"game_source_written":False,
            "signer_accessed":False,"save_modified":False,
            "limitations":[
              "Confirmed structural PPC compare in generated PAL source, but menu function identity remains a candidate",
              "This callback sees model 41 comparisons if flow reaches function; it will not itself add categories",
              "No runtime call count, identity of loaded library or actual upgrade inventory is yet proven",
              "The PTBR vs PAL XEX PE 10-byte delta from DIAG41 is independent; mapping to V38 build not proven"
            ]
        }

def main():
    pa=argparse.ArgumentParser();pa.add_argument("--run-id",required=True);a=pa.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE291_BMW_MAIN_MENU_PASSIVE_TRACE_IN_MEMORY","status":"FAILED",
            "apk_built":False,"save_modified":False,"signer_accessed":False}
    try:
        result=audit()
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    result["run_id"]=a.run_id
    result["timestamp"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PRE291_STATUS",result["status"])
    print("PRE291_MAIN_MENU",result.get("function","NONE"))
    print("PRE291_DEFAULT_OFF",not result.get("feature_enabled_by_default",False))
    print("PRE291_SOURCE_ONLY",not result.get("game_source_written",False))
    print("PRE291_APK_BUILT",False)
    if result["status"]!="AUDIT_OK":print("PRE291_FAILURE_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
