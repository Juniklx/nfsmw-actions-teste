#!/usr/bin/env python3
"""PRE290 source-only audit: compare PTBR/PAL known differences and BMW probe placement.
Sources: immutable DIAG41 PRE15/PRE16/PRE18 logs reviewed separately from Drive.
No XEX transfer, APK, patch, credentials, save changes, or build.
"""
from pathlib import Path
import json, hashlib, re
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
OUT=Path("/tmp/nfsmw-pre290/PRE290_PTBR_PAL_BMW_MENU_READONLY.json")
def file(n):
    p=ROOT/n
    b=p.read_bytes()
    return b.decode("utf-8"), hashlib.sha256(b).hexdigest()

def must(ok,label):
    if not ok:raise AssertionError(label)

def main():
    out={"stage":"PRE290_PTBR_PAL_BMW_MENU_SOURCE_ONLY","status":"STARTED",
         "timestamp":datetime.now(timezone.utc).isoformat(),
         "xex_downloaded":False,"patch_applied":False,"apk_built":False,
         "save_modified":False,"signer_accessed":False}
    try:
        diff,hs=file("pre262_bmw_hero_ui_generated_readonly.py")
        gate,hg=file("pre264_bmw_hero_menu_patch_dryrun.py")
        setup,hp=file("pre283_bmw_vtable_target_passive_dryrun.py")
        stage,ha=file("pre284_v37_full_passive_vtable_link_preflight.py")
        v38,hv=file("pre289_build_signed_v38_bmw_passive.py")
        need=[
           ("PRE262 decomp hint main menu", 'CustomizeMain::BuildOptionsList hides Parts+Performance when IsHeroCar' in diff),
           ("PRE262 marks hint as nonproof", 'all mappings remain hypotheses' in diff),
           ("PRE264 menu function", 'FUNCTION="sub_82578988"' in gate),
           ("PRE264 is dryrun/feature-flagged", 'NFSMW_PRE264_BMW_MENU_ENABLE' in gate),
           ("PRE283 setup probe function", 'FN="sub_82582F70"' in setup),
           ("PRE283 tracing flag", 'NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE' in setup),
           ("PRE283 expected runtime marker", 'NFSMW_PRE283_BMW_VTABLE' in setup),
           ("PRE284 stages logger", 'def stage_logger' in stage),
           ("V38 imports staged trace", 'from pre284_v37_full_passive_vtable_link_preflight import stage_logger' in v38),
           ("V38 is versionCode 38", bool(re.search(r'(?m)^VERSION_CODE\s*=\s*38\s*$',v38))),
        ]
        for n,ok in need:must(ok,n)
        out["checks"]={n:ok for n,ok in need}
        out["source_sha256"]={"PRE262":hs,"PRE264":hg,"PRE283":hp,"PRE284":ha,"PRE289":hv}
        out["archive_evidence"]={
          "PTBR_PAL_PRE16_decoded_PE_same_size":13434880,
          "PTBR_PAL_PRE16_decoded_PE_bytes_different":10,
          "PRE16_changed_guest_function":"sub_822C62E0",
          "PRE16_source":"DIAG41 PRE16 Drive log 1_ix_UsPFGR5XpoG00sLURytXb8d2Ivn3",
          "PRE15_distinct_xex_sha256":{
           "PAL":"aad15fc218d034de3131f746e0b763dd8049a40dd676efc87667fcaf4fc72694",
           "PTBR":"684ceef963806ae7ba2f6d0936c267f9ff0134d20da1f85a390862dd9c676c28"
          }
        }
        out["independent_site_addresses"]={
          "translation_delta_site":"0x822C62E0",
          "candidate_main_menu_gate":"0x82578988",
          "V38_probe_setup":"0x82582F70"
        }
        out["conclusions"]=[
          "PTBR and PAL decoded PE differ by only ten bytes in DIAG41 PRE16; no evidence of wholesale function address shifting",
          "The observed Visual-only menu may bypass CustomizePerformance::Setup: absence of V38 trace cannot prove a PAL/PTBR address mismatch",
          "PRE264 documents a main-menu candidate gate, but its model is hypothesis/dry-run and must not be enabled without runtime identity validation",
          "The DIAG41 translation modification is at a different direct guest address; no call graph connection to menu was established"
        ]
        out["limitations"]=[
          "This audit checks repository recipes against archived DIAG41 results, not contemporary XEX decoded byte-by-byte",
          "The test log alone does not independently prove Android versionCode 38 or runtime loaded library",
          "No deterministic call graph between PRE16 PTBR change and candidate menu building was established"
        ]
        out["next"]="Verify actual installed V38/library and trace PAL main-menu BuildOptionsList candidate before unlock experimentation"
        out["status"]="AUDIT_OK"
    except Exception as exc:
        out["status"]="AUDIT_FAILED"
        out["error_type"]=type(exc).__name__
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE290_STATUS",out["status"])
    print("PRE290_CHECKS",len(out.get("checks",{})))
    print("PRE290_MENU_CANDIDATE",out.get("independent_site_addresses",{}).get("candidate_main_menu_gate"))
    print("PRE290_V38_PROBE",out.get("independent_site_addresses",{}).get("V38_probe_setup"))
    print("PRE290_XEX_DOWNLOADED",False)
    print("PRE290_APK_BUILT",False)
    return 0 if out["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
