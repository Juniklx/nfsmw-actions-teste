#!/usr/bin/env python3
"""PRE281: guarded null-selected-part exit, exact C++ source-only dry-run.

The injection in sub_82582A40 runs only when explicitly enabled at compile
time; by default it is OFF. No APK build, signing or save mutation.
Never treat this mock as proof that the vtable points to this function.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre281/PRE281_BMW_NULL_HEADER_GUARD_DRYRUN.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.83.cpp"
PIN="21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4"
TARGET="sub_82582A40"
ANCHOR="\tctx.lr = 0x82582A60;\n\tREX_CALL_INDIRECT_FUNC(ctr.u32);\n"
LATER_DEREF="\tr31.u64 = REX_LOAD_U32(ctx.r11.u32 + 20);"
EPILOGUE="loc_82582F64:"
FEATURE="NFSMW_PRE281_BMW_EMPTY_HEADER_GUARD_ENABLE"
INJECTION=(
  "\t// NFSMW_PRE281: optional null-selection guard before first pointer dereference.\n"
  "#if defined("+FEATURE+") && "+FEATURE+"\n"
  "\tif (ctx.r3.u32 == 0) goto loc_82582F64;\n"
  "#endif\n"
)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def patch_in_memory(raw):
    if sha(raw)!=PIN:raise ValueError("PIN mismatch on source")
    original=raw.decode("utf-8")
    if "NFSMW_PRE281:" in original:raise ValueError("Already applied")
    body=body_for_function(original,TARGET)
    if body.count(ANCHOR)!=1 or body.count(LATER_DEREF)!=1 or body.count(EPILOGUE)!=1:
        raise ValueError("Guest method or first dereference anchor changed")
    if not body.index(ANCHOR)<body.index(LATER_DEREF)<body.index(EPILOGUE):
        raise ValueError("Control-flow ordering invalid")
    if not body.split(EPILOGUE,1)[1].count("ctx.r1.s64 = ctx.r1.s64 + 256;")==1:
        raise ValueError("Expected shared cleanup at epilogue")
    if not body.split(EPILOGUE,1)[1].count("\treturn;")==1:
        raise ValueError("Expected cleanup return")
    changed_body=body.replace(ANCHOR,ANCHOR+INJECTION,1)
    if changed_body.replace(INJECTION,"",1)!=body:
        raise ValueError("Not byte-reversible")
    changed=original.replace(body,changed_body,1)
    if changed.replace(INJECTION,"",1)!=original:
        raise ValueError("Full shard not reversible")
    for op in ["REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
               "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64("]:
        if changed.count(op)!=original.count(op):
            raise ValueError("Guest memory access op count changed: "+op)
    if changed.count("REX_CALL_INDIRECT_FUNC(")!=original.count("REX_CALL_INDIRECT_FUNC("):
        raise ValueError("Guest call count changed")
    if changed.count("DEFINE_REX_FUNC(")!=original.count("DEFINE_REX_FUNC("):
        raise ValueError("Generated function inventory changed")
    return {
      "candidate_source_sha256":sha(changed.encode()),
      "source_original_sha256":PIN,
      "function":TARGET,
      "feature_macro":FEATURE,
      "feature_enabled_by_default":False,
      "selected_part_null_check_before_first_dereference":True,
      "existing_guest_load_store_call_counts_unchanged":True,
      "branch_target":"loc_82582F64 shared cleanup",
      "reverts_to_original_exactly":True,
      "no_files_written":True
    }

def host_test(root):
    f=root/"pre281_host_null.cpp"
    f.write_text(r'''
#include <cassert>
#include <cstdint>
#include <iostream>
// Isolated control-flow model, not compiled guest code.
struct Model {unsigned normal=0,empty=0,derefs=0;};
static void refresh(Model& m,uint32_t selection) noexcept {
    // A normal guest vcall has already happened.
    if(selection==0){++m.empty;return;}
    ++m.derefs; ++m.normal;
}
int main(){
    Model m{};
    for(unsigned i=0;i<256;++i)refresh(m,(i%2)?0x12345678u:0u);
    assert(m.empty==128 && m.normal==128 && m.derefs==128);
    std::cout<<"PRE281_HOST_NULL_GUARD_256_CASES_PASS\n";
}
''',encoding="utf-8")
    exe=root/"pre281_null"
    cc=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O1",
                       str(f),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if cc.returncode:
        return {"passed":False,"phase":"host_compile","stderr":cc.stderr[-700:]}
    rr=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"passed":rr.returncode==0,"result":rr.stdout.strip(),"cases":256,
            "compiled_guest_code":False}

def audit():
    with tempfile.TemporaryDirectory(prefix="pre281_") as dirname:
        tmp=Path(dirname)
        backup=tmp/"pre99.tar.gz"
        download(drive_client(),backup)
        digest,_,size=sha_file(backup)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 snapshot mismatch")
        shard=None
        with tarfile.open(backup,"r:gz",errorlevel=2) as tar:
            for m in tar:
                if not m.isfile() or m.name.lstrip("./")!=SOURCE:continue
                if m.size>7_000_000:raise ValueError("Unexpected shard size")
                fp=tar.extractfile(m)
                if fp is None:raise ValueError("Unreadable source")
                shard=fp.read()
                if len(shard)!=m.size:raise ValueError("Truncated source")
                break
        if shard is None:raise ValueError("Missing source")
        preview=patch_in_memory(shard)
        host=host_test(tmp)
        return {
          "stage":"PRE281_BMW_NULL_SELECTEDPART_GUARD_SOURCE_ONLY",
          "status":"AUDIT_OK" if host["passed"] else "NEEDS_REVIEW",
          "pre99_verified_sha256":digest,
          "null_guard_preview":preview,
          "host_mock":host,
          "vtable_target_proven":False,
          "release_approved":False,
          "important_limitations":[
            "Preview only, source remains unchanged on disk and in all APKs",
            "Virtual RefreshHeader dispatch has not been resolved from guest vtable data",
            "Skipping RefreshHeader on empty option avoids dereference but does not prove proper UI error handling",
            "Selection-null protection does not create BMW upgrade packages",
            "No BMW package count known and no Android gameplay or controller checks",
            "A later build would need to enable guard explicitly, preserve original V37 patches and permanent certificate"
          ],
          "apk_built":False,"user_save_modified":False,"source_persisted":False,
          "signer_accessed":False
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("numeric run id needed")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE281_BMW_NULL_SELECTEDPART_GUARD_SOURCE_ONLY",
            "status":"FAILED","apk_built":False,"source_persisted":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE281_STATUS",result["status"])
    print("PRE281_HOST",result.get("host_mock",{}).get("result"))
    print("PRE281_ENABLED_DEFAULT",result.get("null_guard_preview",{}).get("feature_enabled_by_default"))
    print("PRE281_GUEST_BUILD",result["apk_built"])
    if result["status"]!="AUDIT_OK":print("PRE281_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
