#!/usr/bin/env python3
"""PRE426: dry-run, default-off passive logging of the already-returned level count.
No source changes on disk, guest call injection, APK, signing or save access.
"""
import argparse,hashlib,json,re,subprocess,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre426/report.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.57.cpp"
PIN="a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c"
FUNC="sub_8256F818"
FEATURE="NFSMW_PRE426_BMW_COUNTS_ENABLE"
NAME="NFSMW_PRE426_TRACE_BMW_COUNT"
DECL='\nextern "C" void '+NAME+'(unsigned int, int) noexcept;\n'
ANCHOR="\tr21.u64 = ctx.r3.u64;\n"
INJECT=(
 "#if defined("+FEATURE+") && "+FEATURE+"\n"
 "\t"+NAME+"(r26.u32, r21.s32);\n"
 "#endif\n"
)
HELPER=r"""#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
// No guest pointer dereference, no guest state writes. Output is per session.
static std::atomic<std::uint32_t> g_pre426_count{0};
extern "C" void NFSMW_PRE426_TRACE_BMW_COUNT(unsigned int type, int returned_count) noexcept {
  std::uint32_t seen=g_pre426_count.load(std::memory_order_relaxed);
  while (seen<64u && !g_pre426_count.compare_exchange_weak(
      seen,seen+1u,std::memory_order_relaxed,std::memory_order_relaxed)) {}
  if (seen>=64u) return;
  REXLOG_INFO("[NFSMW_PRE426_BMW_COUNT] type={} count={}",type,returned_count);
}
"""
def sha(data):return hashlib.sha256(data).hexdigest()
def preview(raw):
 if sha(raw)!=PIN:raise ValueError("source fingerprint mismatch")
 source=raw.decode("utf-8")
 if NAME in source or FEATURE in source:raise ValueError("already instrumented")
 body=body_for_function(source,FUNC)
 if body.count(ANCHOR)!=1:raise ValueError("ambiguous post-result anchor")
 if body.count("sub_823E5988(ctx, base);")!=2:raise ValueError("candidate helper call count changed")
 if body.index("r26.u64 = ctx.r4.u64")>body.index(ANCHOR):
  raise ValueError("category register not set before logging")
 if body.index("sub_823E5988(ctx, base);")>body.index(ANCHOR):
  raise ValueError("count callback precedes existing helper call")
 changed=body.replace(ANCHOR,ANCHOR+INJECT,1)
 if changed.replace(INJECT,"",1)!=body:raise ValueError("not reversible in body")
 modified=source.replace(body,changed,1)
 m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",modified)
 if not m:raise ValueError("top-level function marker missing")
 modified=modified[:m.start()]+DECL+modified[m.start():]
 if modified.replace(DECL,"",1).replace(changed,body,1)!=source:raise ValueError("not reversible in file")
 for token in ("DEFINE_REX_FUNC(","REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64(",
               "REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64("):
  if modified.count(token)!=source.count(token):raise ValueError("guest operation count changed: "+token)
 return {"status":"PREVIEW_OK","source_sha256":PIN,"candidate_sha256":sha(modified.encode()),
  "guest_calls_added":0,"guest_memory_reads_added":0,"guest_memory_writes_added":0,
  "post_existing_helper_result":True,"capture_fields":["performance_type","existing_return_count"],
  "car_identity_capture":False,"feature_flag":FEATURE,"feature_enabled_by_default":False,
  "source_reversible":True,"helper_preview_sha256":sha(HELPER.encode()),
  "helper_cpp_linked":False,"source_written_to_disk":False}
def mock(root):
 path=root/"test.cpp";path.write_text(r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <iostream>
struct Logger {
 std::atomic<unsigned> seen{0u};
 bool trace(unsigned type,int count) {
  (void)type;(void)count;
  auto value=seen.load(std::memory_order_relaxed);
  while(value<64u&&!seen.compare_exchange_weak(value,value+1u,std::memory_order_relaxed)) {}
  return value<64u;
 }
};
int main(){
 Logger x;
 for(unsigned i=0;i<64;++i)assert(x.trace(513u+(i%7),i==0?-1:(int)i));
 for(unsigned i=0;i<64;++i)assert(!x.trace(i,0));
 assert(x.seen.load()==64u);
 std::cout<<"PRE426_PASSIVE_BOUNDED_HOST_MOCK_128_CASES_PASS\n";
}
""",encoding="utf-8")
 exe=root/"test";cc=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",str(path),"-o",str(exe)],
 capture_output=True,text=True,timeout=30)
 if cc.returncode:return {"passed":False,"error_type":"COMPILE","stderr":cc.stderr[-350:]}
 res=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
 return {"passed":res.returncode==0,"result":res.stdout.strip(),"game_executed":False}
def audit():
 with tempfile.TemporaryDirectory(prefix="pre426_") as d:
  root=Path(d);arch=root/"pre99.tar.gz";download(drive_client(),arch)
  digest,_,size=sha_file(arch)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 archive hash/size mismatch")
  with tarfile.open(arch,"r:gz") as tar:
   m=next((x for x in tar if x.isfile() and x.name.lstrip("./")==SOURCE),None)
   if m is None or m.size>7_000_000:raise ValueError("missing/oversized source")
   f=tar.extractfile(m)
   if f is None:raise ValueError("unreadable source")
   raw=f.read()
  p=preview(raw);t=mock(root)
  return {"stage":"PRE426_PASSIVE_LEVEL_RETURN_PROBE_DRYRUN",
   "status":"AUDIT_OK" if t["passed"] else "NEEDS_REVIEW",
   "archive_sha256":digest,"preview":p,"host_mock":t,"apk_built":False,
   "game_source_changed":False,"save_changed":False,"signing_key_or_password_accessed":False,
   "limits":["No actual BMW/Fiat runtime counts measured",
             "The returned value is a candidate package count, not yet linked to a specific car",
             "No production CMake integration or Android binary created",
             "Feature must stay disabled absent separate build review and baseline source verification"]}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PRE426_STATUS",r["status"],"ERROR",r.get("error","none"))
 print("PRE426_PREVIEW",r.get("preview"))
 print("PRE426_HOST",r.get("host_mock"))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
