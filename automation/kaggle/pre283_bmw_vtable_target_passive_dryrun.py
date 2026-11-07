#!/usr/bin/env python3
"""PRE283: default-off passive virtual target logger at PAL performance Setup.

In an authenticated PRE99 C++ copy in memory, insert a feature-gated native
callback just before the already-existing vtable+12 call in sub_82582F70.
The callback only receives previously loaded guest values (ctr.u32, r29).
No new guest reads, writes or function calls; no signing or APK is involved.
This is not a build or a runtime proof of the vtable method's identity.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, tarfile, tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre283/PRE283_BMW_VTABLE_TARGET_PASSIVE_DRYRUN.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp"
PIN="0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3"
FN="sub_82582F70"
CALL_SITE="0x825837D4"  # PPC bctrl, LR is return address 0x825837D8
FEATURE="NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE"
CALLBACK="NFSMW_PRE283_VTABLE_TARGET_TRACE"
DECL='\nextern "C" void '+CALLBACK+'(unsigned int, unsigned int, unsigned int) noexcept;\n'
INJECTION=(
  "\t// NFSMW_PRE283: observe existing virtual call target; feature OFF by default.\n"
  "#if defined("+FEATURE+") && "+FEATURE+"\n"
  "\t"+CALLBACK+"(ctr.u32, r29.u32, 0x825837D4u);\n"
  "#endif\n"
)
ANCHOR="\tctx.lr = 0x825837D8;\n\tREX_CALL_INDIRECT_FUNC(ctr.u32);"
PPC_CONTEXT=(
  "// lwz r9,0(r29)",
  "ctx.r9.u64 = REX_LOAD_U32(r29.u32 + 0);",
  "ctx.r3.u64 = r29.u64;",
  "ctx.r8.u64 = REX_LOAD_U32(ctx.r9.u32 + 12);",
  "ctr.u64 = ctx.r8.u64;",
)
HOST_LOGGER_PREVIEW=r'''#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
// Preview only: not linked into Android or generated game source.
static std::atomic<unsigned> g_pre283_seen{0};
extern "C" void NFSMW_PRE283_VTABLE_TARGET_TRACE(
    unsigned target, unsigned screen_guest, unsigned guest_callsite) noexcept {
  unsigned n = g_pre283_seen.fetch_add(1u, std::memory_order_relaxed);
  if (n >= 12u) return;
  REXLOG_INFO("[NFSMW_PRE283_BMW_VTABLE] callsite=0x{:08X} target=0x{:08X} screen_guest=0x{:08X}",
              guest_callsite, target, screen_guest);
}
'''

def sha(v:bytes):return hashlib.sha256(v).hexdigest()

def patch(raw:bytes):
    if sha(raw)!=PIN:raise ValueError("Pinned PRE99 PAL shard changed")
    src=raw.decode("utf-8")
    if CALLBACK in src or FEATURE in src:raise ValueError("Probe already present")
    body=body_for_function(src,FN)
    if body.count(ANCHOR)!=1:raise ValueError("Virtual slot 12 call anchor non-unique")
    anchorpos=body.index(ANCHOR)
    previous=body[max(0,anchorpos-600):anchorpos]
    for expr in PPC_CONTEXT:
        if expr not in previous:raise ValueError("Missing verified vtable+12 guest register flow: "+expr)
    if body.count("ctx.lr = 0x825837C4;")!=1:
        raise ValueError("Previous virtual callsite 0x825837C0 missing")
    if body.index("ctx.lr = 0x825837C4;")>=anchorpos:
        raise ValueError("First virtual call must precede second")
    patched_body=body.replace(ANCHOR,INJECTION+ANCHOR,1)
    patched=src.replace(body,patched_body,1)
    m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",patched)
    if m is None:raise ValueError("Missing function declaration anchor")
    patched=patched[:m.start()]+DECL+patched[m.start():]
    if patched.replace(DECL,"",1).replace(patched_body,body,1)!=src:
        raise ValueError("Insertion not exactly reversible")
    for term in ("REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
                 "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64(",
                 "REX_CALL_INDIRECT_FUNC(","DEFINE_REX_FUNC(",
                 "__imp__sub_8256F818(ctx, base);"):
        if patched.count(term)!=src.count(term):
            raise ValueError("Guest calls or guest memory operations changed")
    if patched.count(CALLBACK+"(")!=2:  # one prototype, one call
        raise ValueError("Unexpected trace callback insertion count")
    if patched.count("#if defined("+FEATURE+") && "+FEATURE)!=1:
        raise ValueError("Feature must be guarded and default-OFF")
    return {
      "base_sha256":PIN,
      "candidate_sha256":sha(patched.encode("utf-8")),
      "function":FN,
      "slot_offset_bytes":12,
      "caller_guest_pc":CALL_SITE,
      "trace_callback":CALLBACK,
      "feature_macro":FEATURE,
      "feature_enabled_by_default":False,
      "function_source_reversible":True,
      "no_guest_reads_stores_calls_added":True,
      "native_preview_logger_sha256":sha(HOST_LOGGER_PREVIEW.encode("utf-8")),
      "logging_limit":12,
      "no_source_written":True,
    }

def mock(root):
    src=root/"pre283_mock.cpp"
    src.write_text(r'''
#include <cassert>
#include <cstdint>
#include <iostream>
struct Observer {
  unsigned seen=0, saved=0, limit=12;
  void call(uint32_t target, uint32_t screen, uint32_t pc) noexcept {
    assert(target!=0 && screen!=0 && pc==0x825837D4u);
    ++seen;
    if(seen<=limit)++saved;
  }
};
int main(){
  Observer x;
  for(unsigned i=0;i<200;i++)
    x.call(0x82582A40u+(i%3)*4u,0x10004000u,0x825837D4u);
  assert(x.seen==200 && x.saved==12);
  std::cout<<"PRE283_VTABLE_TRACE_MOCK_200_CASES_12_MAX_OK\n";
}
''',encoding="utf-8")
    exe=root/"pre283_mock"
    cp=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",
                       str(src),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if cp.returncode:return {"ok":False,"phase":"host_mock_compile","stderr":cp.stderr[-600:]}
    res=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"ok":res.returncode==0,"message":res.stdout.strip(),
            "events_simulated":200,"bounded_logs":12,"guest_code_compiled":False}

def audit():
    with tempfile.TemporaryDirectory(prefix="pre283_") as path:
      root=Path(path)
      backup=root/"pre99.tar.gz"
      download(drive_client(),backup)
      digest,_,size=sha_file(backup)
      if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
        raise ValueError("PRE99 backup authenticity mismatch")
      original=None
      with tarfile.open(backup,"r:gz",errorlevel=2) as tar:
        for m in tar:
          if not m.isfile() or m.name.lstrip("./")!=SOURCE:continue
          if m.size>7_000_000:raise ValueError("Source size bound exceeded")
          f=tar.extractfile(m)
          if f is None:raise ValueError("Unreadable source")
          original=f.read()
          if len(original)!=m.size:raise ValueError("Short source read")
          break
      if original is None:raise ValueError("No PAL source")
      plan=patch(original)
      tampered=bytearray(original);tampered[-200]^=1
      try:patch(bytes(tampered))
      except ValueError:bad_sha_rejected=True
      else:bad_sha_rejected=False
      test=mock(root)
      if not bad_sha_rejected:raise ValueError("Tampered input not rejected")
      return {
        "stage":"PRE283_BMW_PAL_VTABLE_TARGET_PASSIVE_SOURCE_DRYRUN",
        "status":"AUDIT_OK" if test["ok"] else "NEEDS_REVIEW",
        "PRE99_authenticated_sha256":digest,
        "logger_injection":plan,
        "mock_test":test,
        "tampered_source_rejected":bad_sha_rejected,
        "runtime_target_observed":False,
        "refreshheader_target_proven":False,
        "release_approved":False,
        "noteworthy_limits":[
          "This is an in-memory source-only recipe; neither native helper nor guest code was built",
          "A future diagnostic build must link a matching native logger if the macro is explicitly enabled",
          "The guest target may be a thunk, which requires one more resolution step",
          "No BMW-specific ownership or GetMaxLevel values are established by a virtual target alone",
          "The trace does not activate the BMW tuning menu or the PRE264/PRE281 patches",
          "No installed game changes, personal save access, or signing key use"
        ],
        "apk_built":False,"source_persisted":False,"user_save_touched":False,
        "signer_accessed":False,
      }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("run-id must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE283_BMW_PAL_VTABLE_TARGET_PASSIVE_SOURCE_DRYRUN",
       "status":"FAILED","apk_built":False,"source_persisted":False}
    try:r=audit()
    except Exception as e:r["error_type"]=type(e).__name__
    r["github_run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE283_STATUS",r["status"])
    print("PRE283_GUEST_CALLSITE",r.get("logger_injection",{}).get("caller_guest_pc"))
    print("PRE283_REVERSED",r.get("logger_injection",{}).get("function_source_reversible"))
    print("PRE283_HOST",r.get("mock_test",{}).get("message"))
    print("PRE283_ACTUAL_TARGET_KNOWN",r.get("runtime_target_observed"))
    if r["status"]!="AUDIT_OK":print("PRE283_ERROR",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
