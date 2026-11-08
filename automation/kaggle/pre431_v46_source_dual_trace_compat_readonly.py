#!/usr/bin/env python3
"""PRE431: authenticated PRE99 -> V46-equivalent PAL source staging + PRE429 callbacks.

Source-only verification. No Gradle, APK, signer, saves, credentials for signing,
or assertion of bit-identical V46. Do not edit original repository game sources.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
from pre284_v37_full_passive_vtable_link_preflight import (
    replay_v37,PAL_SOURCE,PAL_FEATURE,PAL_DECL)
from pre317_nitro_cycle_staging import apply as apply_pre317
from pre337_nitro_diversity_staging import apply as apply_pre337
from pre349_nitro_slot_value_staging import apply as apply_pre349
from pre389_nitro_lr_slot_staging import apply as apply_pre389
from pre398_global_nitro_full_staging import apply as apply_pre398
from pre364_xinput_user0_passive_staging import apply as apply_pre364
from pre292_bmw_main_menu_native_link_nosign import stage_trace as stage_menu_trace, REGISTER as PRE292_REGISTER
from pre291_bmw_main_menu_passive_trace_dryrun import TRACE_FLAG as MENU_FEATURE, PROTOTYPE as MENU_DECL
from pre264_bmw_hero_menu_patch_dryrun import SOURCE as MENU_SOURCE, MODEL_CMP as HERO_MODEL_CMP, INJECTION as HERO_MENU_INJECTION
from pre239_pal_money_probe_recipe_readonly import body_for_function
import pre398_global_nitro_full_staging as nitro
import pre429_bmw_entry_level_correlation_dryrun as probe
OUT=Path("/tmp/nfsmw-pre431/report.json")
MODULE="nativo/app/src/nfsmw_bmw_trace_pre431.cpp"
CMAKE="nativo/app/CMakeLists.txt"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_trace_pre431.cpp)"
FEATURE=probe.FEATURE

def sha(blob:bytes)->str:return hashlib.sha256(blob).hexdigest()

def replay_v46_sources(root:Path,repo:Path):
    stages={"PRE117_to_PRE247":replay_v37(root,repo)}
    for label,func in [("PRE317",apply_pre317),("PRE337",apply_pre337),
                       ("PRE349",apply_pre349),("PRE389",apply_pre389),
                       ("PRE398",apply_pre398),("PRE364",apply_pre364)]:
        stages[label]=func(root)
    nit=stages["PRE398"]
    if not (nit.get("status")=="STAGED_GLOBAL_NITRO_ALL_CARS" and
            nit.get("nitro_stores_modified")==5 and
            nit.get("guest_store_count_delta")==0 and
            nit.get("extra_guest_loads")==0 and
            nit.get("reverse_exact") is True and
            nit.get("cheat_enabled") is True):
        raise ValueError("PRE398 Nitro preservation invariant failed")
    stages["PRE292_MENU_TRACE"]=stage_menu_trace(root)
    if stages["PRE292_MENU_TRACE"].get("menu_registered_once") is not True:
        raise ValueError("PRE292 CMake registration missing")
    # Exact V46 PRE401 source-enablement logic; NOT signing/build.
    pal=root/PAL_SOURCE.removeprefix("workspace/")
    text=pal.read_text(encoding="utf-8")
    if text.count(PAL_DECL)!=1 or "#define "+PAL_FEATURE in text:
        raise ValueError("PRE401 PAL vtable trace flag unexpected")
    text=text.replace(PAL_DECL,"#define "+PAL_FEATURE+" 1\n"+PAL_DECL,1)
    pal.write_text(text,encoding="utf-8")
    menu=root/MENU_SOURCE.removeprefix("workspace/")
    old=menu.read_text(encoding="utf-8")
    if old.count(MENU_DECL)!=1 or "#define "+MENU_FEATURE in old:
        raise ValueError("PRE401 menu trace flag unexpected")
    updated=old.replace(MENU_DECL,"#define "+MENU_FEATURE+" 1\n"+MENU_DECL,1)
    if (updated.count(HERO_MODEL_CMP)!=1 or
            "NFSMW_PRE264_BMW_MENU_LOCAL" in updated or
            "NFSMW_PRE264_BMW_MENU_ENABLE" in updated):
        raise ValueError("PRE401 BMW model gate source unexpected")
    updated=updated.replace(HERO_MODEL_CMP,HERO_MODEL_CMP+HERO_MENU_INJECTION,1)
    updated=updated.replace(MENU_DECL,"#define NFSMW_PRE264_BMW_MENU_ENABLE 1\n"+MENU_DECL,1)
    directive="#define NFSMW_PRE264_BMW_MENU_ENABLE 1"
    if (updated.splitlines().count(directive)!=1 or
            directive+r"\n" in updated or
            updated.count("NFSMW_PRE264_BMW_MENU_LOCAL")!=1):
        raise ValueError("PRE401 BMW gate directive/macro mismatch")
    if updated.replace("#define NFSMW_PRE264_BMW_MENU_ENABLE 1\n","",1).replace(
            HERO_MODEL_CMP+HERO_MENU_INJECTION,HERO_MODEL_CMP,1)!=old.replace(
            MENU_DECL,"#define "+MENU_FEATURE+" 1\n"+MENU_DECL,1):
        raise ValueError("PRE401 BMW menu source not reversible")
    menu.write_text(updated,encoding="utf-8")
    nitro_source=(root/nitro.PAL_REL).read_text(encoding="utf-8")
    nitro_body=body_for_function(nitro_source,nitro.FUNCTION)
    if (nitro_body.count("PRE398 global Nitro refill site")!=5 or
            nitro_body.count("REX_STORE_U32(r31.u32 + 252, 0x3F800000u);")!=5):
        raise ValueError("PRE398 Nitro native source markers missing")
    stages["V46_MENU_SOURCE"]={"pal_vtable_flag_on":True,"menu_trace_flag_on":True,
      "model41_gate_enabled":True,"source_path":MENU_SOURCE,
      "menu_sha256":sha(menu.read_bytes())}
    stages["V46_NITRO_SOURCE"]={"site_count":5,"stores_full_bits":5,
      "nitro_source_sha256":sha((root/nitro.PAL_REL).read_bytes())}
    return stages

def install_probe(root:Path):
    revisions={}
    for label in ("entry","list"):
        filename,pin,func=probe.SOURCES[label]
        f=root/"nativo/app/generated/default"/filename
        original=f.read_bytes()
        valid=probe.change(original,label)
        body=body_for_function(original.decode("utf-8"),func)
        anchor,code,decl=(probe.ENTRY_ANCHOR,probe.ENTRY_CODE,probe.ENTRY_DECL) if label=="entry" else (
            probe.COUNT_ANCHOR,probe.COUNT_CODE,probe.COUNT_DECL)
        amended=body.replace(anchor,anchor+code,1)
        source=original.decode("utf-8").replace(body,amended,1)
        marker=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",source)
        if marker is None:raise ValueError("PRE429 guest declaration marker missing")
        source=source[:marker.start()]+decl+source[marker.start():]
        if sha(source.encode())!=valid["preview_sha256"]:
            raise ValueError("PRE429 guest preview mismatch for "+label)
        f.write_text(source,encoding="utf-8")
        if sha(f.read_bytes())!=valid["preview_sha256"]:
            raise ValueError("PRE429 guest source readback mismatch")
        revisions[label]={"source_file":filename,"before_sha256":pin,
          "after_sha256":valid["preview_sha256"],"reversible":True}
    module=root/MODULE
    if module.exists():raise ValueError("PRE431 logger module unexpectedly exists")
    module.parent.mkdir(parents=True,exist_ok=True)
    module.write_text(probe.HELPER,encoding="utf-8")
    if sha(module.read_bytes())!=sha(probe.HELPER.encode()):
        raise ValueError("PRE431 logger module readback mismatch")
    cmake=root/CMAKE
    current=cmake.read_text(encoding="utf-8")
    if current.count(PRE292_REGISTER)!=1 or REGISTER in current:
        raise ValueError("PRE431 CMake anchor absent or duplicate")
    addition="\n    "+REGISTER
    new=current.replace(PRE292_REGISTER,PRE292_REGISTER+addition,1)
    if new.replace(addition,"",1)!=current:raise ValueError("PRE431 CMake not reversible")
    cmake.write_text(new,encoding="utf-8")
    if cmake.read_text(encoding="utf-8").count(REGISTER)!=1:
        raise ValueError("PRE431 registration not present")
    return {"source_reviews":revisions,"native_module":MODULE,"module_sha256":sha(module.read_bytes()),
      "cmake_registration_count":1,"feature":FEATURE,"feature_enabled_by_default":False,
      "native_code_compiled":False,"source_modified_in_temp_only":True}

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre431_") as d:
        temp=Path(d);arc=temp/"pre99.tar.gz";download(drive_client(),arc)
        digest,_,size=sha_file(arc)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 fingerprint mismatch")
        restored=temp/"restore";restored.mkdir()
        restore(arc,restored);arc.unlink(missing_ok=True)
        root=restored/"workspace"
        stages=replay_v46_sources(root,Path(__file__).resolve().parents[2])
        review=install_probe(root)
        return {"stage":"PRE431_V46_SOURCE_REPLAY_BMW_DUAL_TRACE_READONLY",
          "status":"AUDIT_OK","pre99_sha256":digest,"v46_source_stages":stages,
          "pre429_v46_compatibility":review,"v46_source_sequence_replayed":True,
          "original_v46_apk_bytes_reproduced":False,
          "native_library_built":False,"apk_built":False,"signer_accessed":False,
          "save_modified":False,
          "warnings":["V46 source patch sequence only, no V46 APK build or on-device test",
                      "No proof the selected car has actual performance levels",
                      "PRE429 marker flag OFF; native compile of two shards is a later step"]}
def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True);args=a.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230]}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE431_STATUS",r["status"],"ERROR_TYPE",r.get("error_type","none"))
    print("PRE431_ERROR",r.get("error","none"))
    stages=r.get("v46_source_stages",{})
    for item in ("PRE317","PRE337","PRE349","PRE389","PRE398","PRE364"):
        print("PRE431_STAGE",item,stages.get(item,{}).get("status"))
    print("PRE431_NITRO",stages.get("V46_NITRO_SOURCE",{}))
    print("PRE431_MENU",stages.get("V46_MENU_SOURCE",{}))
    print("PRE431_DUAL",r.get("pre429_v46_compatibility",{}).get("source_reviews"))
    print("PRE431_NO_APK",True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
