#!/usr/bin/env python3
"""PRE274: passive entry marker and PRE271 levels tracer coexistence dry-run.

Only manipulates authenticated PRE99 generated C++ bytes IN MEMORY. It is not
an executable game patch nor a build. Feature guards default disabled.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre271_bmw_getmaxlevel_passive_logger_dryrun import patch as preview_pre271, SOURCE as LEVEL_SOURCE, PIN as LEVEL_SHA

OUT=Path("/tmp/nfsmw-pre274/PRE274_BMW_TUNING_ENTRY_PASSIVE_DRYRUN.json")
ENTRY_SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.15.cpp"
ENTRY_SHA="414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a"
ENTRY_FUNCTION="sub_8256B440"
PPC_ANCHOR="	REX_STORE_U32(r31.u32 + 8, ctx.r11.u32);\n"
PPC_COMMENT="	// stw r11,8(r31)\n"
FEATURE="NFSMW_PRE274_TUNING_ENTRY_TRACE"
FN="NFSMW_PRE274_TRACE_ENTRY"
DECL='\nextern "C" void '+FN+'(unsigned int, unsigned int, unsigned int) noexcept;\n'
INJECT=(
    "// NFSMW_PRE274 BMW customization entry marker; default-OFF.\n"
    "#if defined("+FEATURE+") && "+FEATURE+"\n"
    "\t"+FN+"(r31.u32, r29.u32, ctx.r11.u32);\n"
    "#endif\n"
)

def sha(data):return hashlib.sha256(data).hexdigest()
def splice_entry(raw:bytes):
    if sha(raw)!=ENTRY_SHA:raise ValueError("PRE273 entry source fingerprint changed")
    source=raw.decode("utf-8")
    if FN in source or FEATURE in source:raise ValueError("Trace already present")
    original=body_for_function(source,ENTRY_FUNCTION)
    if original.count(PPC_ANCHOR)!=1 or original.count(PPC_COMMENT)!=1:
        raise ValueError("Entry pvehicle field store anchor missing or ambiguous")
    if original.index("REX_STORE_U32(r31.u32 + 4, r29.u32)")>original.index(PPC_ANCHOR):
        raise ValueError("TuningCar must be assigned before pvehicle")
    if original.index(PPC_ANCHOR)>original.index("__imp__sub_822CC308(ctx, base);"):
        raise ValueError("pvehicle must be stored before vehicle ride creation")
    replacement=original.replace(PPC_ANCHOR,PPC_ANCHOR+INJECT,1)
    assert replacement.count(FN+"(")==1
    if replacement.replace(INJECT,"",1)!=original:
        raise ValueError("Entry function patch not reversible")
    changed=source.replace(original,replacement,1)
    m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9a-fA-F]{8}\)",changed)
    if not m:raise ValueError("Top level function macro missing")
    changed=changed[:m.start()]+DECL+changed[m.start():]
    if changed.replace(DECL,"",1).replace(replacement,original,1)!=source:
        raise ValueError("Whole CPP patch not reversible")
    for op in ("REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
               "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64("):
        if source.count(op)!=changed.count(op):
            raise ValueError("Extra memory op added: "+op)
    if changed.count("DEFINE_REX_FUNC(")!=source.count("DEFINE_REX_FUNC("):
        raise ValueError("Generated function count changed")
    return {
      "source_before_sha256":sha(raw),
      "candidate_sha256":sha(changed.encode()),
      "function":ENTRY_FUNCTION,
      "marker":FN,
      "feature_guard":FEATURE,
      "guard_enabled_by_default":False,
      "tracked_manager_pvehicle_guest_address_expression":"r31.u32 + 8",
      "captured_tuning_car_guest_address":"r29.u32",
      "captured_guest_pvehicle_field":"ctx.r11.u32",
      "added_guest_memory_accesses":0,
      "existing_game_calls_changed":False,
      "source_reversible":True,
      "build_or_binary_patch":False,
    }
def host_mock(t:Path):
    source=t/"pre274_mock.cpp"
    source.write_text(r"""
#include <cassert>
#include <cstdint>
#include <iostream>
struct Tracker {
  uint32_t owner=0, car=0, pv=0;
  unsigned seen=0;
  void enter(uint32_t manager,uint32_t car_rec,uint32_t field) noexcept {
    owner=manager+8u;car=car_rec;pv=field;seen=0u;
  }
  bool trace(uint32_t pvehicle,uint32_t category,int value) noexcept {
    (void)value;
    if(!owner || pvehicle!=owner || category>=7u || seen>=56u)return false;
    ++seen;return true;
  }
};
int main() {
  Tracker x;
  assert(!x.trace(0x1018u,0u,0));
  x.enter(0x1010u,0x4141u,0xBEEFu);
  assert(x.owner==0x1018u && x.car==0x4141u);
  assert(!x.trace(0x1010u,0u,0));
  assert(!x.trace(0x1018u,7u,0));
  for(unsigned i=0;i<56u;++i)assert(x.trace(0x1018u,i%7u,-1));
  assert(!x.trace(0x1018u,0u,1));
  x.enter(0x2020u,0x8282u,0xCAFEu);
  assert(!x.trace(0x1018u,0u,1));
  assert(x.trace(0x2028u,4u,0));
  std::cout<<"PRE274_ENTRY_GETMAXLEVEL_CORRELATION_HOST_PASS\n";
}
""",encoding="utf-8")
    exe=t/"pre274_mock"
    cc=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O1",str(source),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if cc.returncode:
        return {"ok":False,"phase":"HOST_COMPILE","diagnostic":cc.stderr[-650:]}
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"ok":run.returncode==0,"result":run.stdout.strip(),
            "game_code_compiled":False,"mock_only":True}
def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre274_") as d:
        tmp=Path(d)
        archive=tmp/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,length=sha_file(archive)
        if digest!=EXPECTED_SHA256 or length!=EXPECTED_BYTES:
            raise ValueError("PRE99 snapshot fingerprint mismatch")
        needed={ENTRY_SOURCE:ENTRY_SHA,LEVEL_SOURCE:LEVEL_SHA}
        src={}
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if not m.isfile() or name not in needed:continue
                if m.size>7_000_000:raise ValueError("Unexpected source size")
                f=tar.extractfile(m)
                if f is None:raise ValueError("Unreadable source")
                data=f.read()
                if len(data)!=m.size or sha(data)!=needed[name]:
                    raise ValueError("Unexpected exact-source digest")
                src[name]=data
        if len(src)!=len(needed):raise ValueError("Source shards missing")
        entry=splice_entry(src[ENTRY_SOURCE])
        levels=preview_pre271(src[LEVEL_SOURCE])
        if levels.get("three_return_exits_instrumented")!=3:
            raise ValueError("PRE271 callback preflight no longer valid")
        mock=host_mock(tmp)
        return {
            "stage":"PRE274_TUNING_ENTRY_PLUS_BMW_LEVELS_PASSIVE_DRYRUN",
            "status":"AUDIT_OK" if mock["ok"] else "NEEDS_REVIEW",
            "pre99_sha256_authenticated":digest,
            "entry":entry,"levels":levels,
            "host_correlation_mock":mock,
            "no_patches_written_to_disk":True,
            "build_started":False,"key_accessed":False,"user_save_touched":False,
            "release_ready":False,
            "limitations":[
                "This is an in-memory source transformation, not a compiled game or APK",
                "PPC source-mapping is structural and not measured at V37 runtime",
                "Passive entry marker alone does not prove BMW identity; user selection/context still required",
                "GetMaxLevel might not be invoked for BMW while performance menu is hidden",
                "Mock correlation relies on same guest address passed by GetPerformancePartsList",
                "No PPC guest function calls added and no performance data read from device",
                "Do not enable HeroCar menu until empty category handling proven",
            ],
        }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("run ID must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE274_TUNING_ENTRY_PLUS_BMW_LEVELS_PASSIVE_DRYRUN",
        "status":"FAILED","build_started":False,"key_accessed":False}
    try:report=audit()
    except Exception as e:report["error_type"]=type(e).__name__
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE274_STATUS",report["status"])
    print("PRE274_ENTRY",report.get("entry",{}).get("function"))
    print("PRE274_PRE271_RETURNS",report.get("levels",{}).get("three_return_exits_instrumented"))
    print("PRE274_MOCK",report.get("host_correlation_mock",{}).get("result"))
    if report["status"]!="AUDIT_OK":print("PRE274_ERROR",report.get("error_type"))
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
