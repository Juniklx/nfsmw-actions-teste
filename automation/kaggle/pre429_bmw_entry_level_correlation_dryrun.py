#!/usr/bin/env python3
"""PRE429 in-memory, fail-closed preview: join tuning-entry and level-count markers.

No Android APK build, no changes on disk to game source, no signer, no save.
"""
import argparse,hashlib,json,re,subprocess,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre429/report.json")
ROOT="workspace/nativo/app/generated/default/"
SOURCES={
 "entry":("nfsmw_recomp.15.cpp","414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a","sub_8256B440"),
 "list":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
}
FEATURE="NFSMW_PRE429_TUNING_LEVEL_TRACE_ENABLE"
ENTRY_DECL='\nextern "C" void NFSMW_PRE429_TRACE_ENTRY(unsigned int, unsigned int, unsigned int) noexcept;\n'
COUNT_DECL='\nextern "C" void NFSMW_PRE429_TRACE_LEVEL(unsigned int, unsigned int, int) noexcept;\n'
ENTRY_ANCHOR="\tREX_STORE_U32(r31.u32 + 8, ctx.r11.u32);\n"
COUNT_ANCHOR="\tr21.u64 = ctx.r3.u64;\n"
ENTRY_CODE=(
 "#if defined("+FEATURE+") && "+FEATURE+"\n"
 "\tNFSMW_PRE429_TRACE_ENTRY(r31.u32, r29.u32, ctx.r11.u32);\n"
 "#endif\n")
COUNT_CODE=(
 "#if defined("+FEATURE+") && "+FEATURE+"\n"
 "\tNFSMW_PRE429_TRACE_LEVEL(r30.u32, r26.u32, r21.s32);\n"
 "#endif\n")
HELPER=r"""#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
// No guest dereference; car is an opaque guest address, not a decoded model.
static std::atomic<std::uint32_t> g_entry_count{0},g_level_count{0};
extern "C" void NFSMW_PRE429_TRACE_ENTRY(unsigned int manager, unsigned int car, unsigned int vehicle) noexcept {
  auto n=g_entry_count.fetch_add(1u,std::memory_order_relaxed);
  if(n>=16u)return;
  REXLOG_INFO("[NFSMW_PRE429_ENTRY] manager=0x{:08X} tuning_car=0x{:08X} pvehicle=0x{:08X}",
              manager,car,vehicle);
}
extern "C" void NFSMW_PRE429_TRACE_LEVEL(unsigned int manager, unsigned int category, int count) noexcept {
  if(category>6u)return;
  auto n=g_level_count.fetch_add(1u,std::memory_order_relaxed);
  if(n>=112u)return;
  REXLOG_INFO("[NFSMW_PRE429_LEVEL] manager=0x{:08X} category={} candidate_count={}",
              manager,category,count);
}
"""
def sha(raw):return hashlib.sha256(raw).hexdigest()
def change(raw,label):
 filename,expected,fn=SOURCES[label]
 if sha(raw)!=expected:raise ValueError("source hash mismatch "+label)
 source=raw.decode("utf-8")
 marker=("NFSMW_PRE429_TRACE_ENTRY" if label=="entry" else "NFSMW_PRE429_TRACE_LEVEL")
 if marker in source or FEATURE in source:raise ValueError("already instrumented "+label)
 body=body_for_function(source,fn)
 anchor,inject,decl=(ENTRY_ANCHOR,ENTRY_CODE,ENTRY_DECL) if label=="entry" else (COUNT_ANCHOR,COUNT_CODE,COUNT_DECL)
 if body.count(anchor)!=1:raise ValueError("ambiguous anchor "+label)
 if label=="entry":
  if body.count("REX_STORE_U32(r31.u32 + 4, r29.u32)")!=1 or body.index("REX_STORE_U32(r31.u32 + 4, r29.u32)")>body.index(anchor):raise ValueError("car stored after entry callback")
 else:
  if body.count("sub_823E5988(ctx, base);")!=2 or body.index("sub_823E5988(ctx, base);")>body.index(anchor):raise ValueError("candidate count not returned")
  if body.count("r26.u64 = ctx.r4.u64")!=1:raise ValueError("category register not proven")
 new_body=body.replace(anchor,anchor+inject,1)
 changed=source.replace(body,new_body,1)
 m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",changed)
 if not m:raise ValueError("missing top-level declaration location")
 changed=changed[:m.start()]+decl+changed[m.start():]
 if changed.replace(decl,"",1).replace(new_body,body,1)!=source:raise ValueError("failed exact round-trip")
 for op in ("DEFINE_REX_FUNC(","REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
            "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64("):
  if source.count(op)!=changed.count(op):raise ValueError("guest memory opcode mismatch "+op)
 return {"path":ROOT+filename,"original_sha256":expected,"preview_sha256":sha(changed.encode()),
         "feature":FEATURE,"enabled_by_default":False,"reversible":True,
         "added_guest_calls":0,"added_guest_reads":0,"added_guest_writes":0,"body_lines":len(body.splitlines())}
def mock(root):
 f=root/"mock.cpp"
 f.write_text(r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
struct Trace {
 unsigned entries=0u,levels=0u; uint32_t last_manager=0u,last_car=0u;
 void enter(uint32_t manager,uint32_t car,uint32_t vehicle) {
   (void)vehicle;if(entries>=16u)return;
   ++entries;last_manager=manager;last_car=car;
 }
 bool level(uint32_t manager,uint32_t category,int value) {
   (void)value;
   if(category>6u||levels>=112u)return false;
   ++levels;return manager==last_manager && last_car!=0u;
 }
};
int main() {
 Trace t;t.enter(0xAC00u,0xC001u,0xBEEF);assert(t.level(0xAC00u,0u,3));
 assert(!t.level(0xCC00u,0u,3));
 t.enter(0xAC00u,0xC002u,0xDEAD);
 for(unsigned n=2;n<112;++n)assert(t.level(0xAC00u,n%7u,(int)n));
 assert(t.levels==112u);assert(!t.level(0xAC00u,0u,0));
 assert(t.entries==2u);
 std::cout<<"PRE429_CORRELATION_MOCK_PASS_114_EVENTS\n";
}
""",encoding="utf-8")
 exe=root/"mock"
 cc=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O1",str(f),"-o",str(exe)],
 capture_output=True,text=True,timeout=30)
 if cc.returncode:return {"ok":False,"phase":"compile","diagnostic":cc.stderr[-400:]}
 run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
 return {"ok":run.returncode==0,"result":run.stdout.strip(),"guest_code_executed":False}
def audit():
 with tempfile.TemporaryDirectory(prefix="pre429_") as d:
  temp=Path(d);archive=temp/"pre99.tar.gz";download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  wanted={ROOT+v[0]:key for key,v in SOURCES.items()};data={}
  with tarfile.open(archive,"r:gz") as tar:
   for m in tar:
    name=m.name.lstrip("./")
    if not m.isfile() or name not in wanted:continue
    if m.size>7_000_000:raise ValueError("oversized source")
    f=tar.extractfile(m)
    if f is None:raise ValueError("unreadable source")
    data[wanted[name]]=f.read()
  if set(data)!=set(SOURCES):raise ValueError("missing source")
  previews={key:change(value,key) for key,value in data.items()}
  test=mock(temp)
  return {"stage":"PRE429_BMW_ENTRY_LEVEL_CORRELATION_OFF_DRYRUN",
   "status":"AUDIT_OK" if test["ok"] else "NEEDS_REVIEW","archive_sha256":digest,
   "preview":previews,"callback_preview_sha256":sha(HELPER.encode()),"host_mock":test,
   "caveats":["Guest car address is not a verified car model ID","Matching manager identifies session context only; owner changes require event ordering",
              "No Android compile, no CMake integration, no actual runtime levels",
              "No purchase or tuning modification approved"],
   "source_modified":False,"apk_built":False,"save_modified":False,"signing_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE429_STATUS",r["status"],"ERROR",r.get("error","none"))
 print("PRE429_PREVIEW",r.get("preview"))
 print("PRE429_HOST",r.get("host_mock"))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
