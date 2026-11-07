#!/usr/bin/env python3
"""PRE265 — authenticated, read-only BMW upgrade paths audit.
No Android build, no patch, no save, no signer. A high-level public decomp
is used only as a hypothesis; this audit checks actual PAL generated functions.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile, subprocess
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre265/PRE265_BMW_PERFORMANCE_MENU_SAFETY.json")
SOURCE_HASHES={
    "workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp":
       "26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07",
    "workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp":
       "0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3"
}
NAMES={"sub_82578988","sub_82582F70"}
CANDIDATE_CALLEES={"sub_8256D2B8","sub_8256F818","sub_8256F9D8",
                   "sub_82579CE0","sub_8256D548","sub_8256BC60",
                   "sub_8256BB10","sub_82587498"}
CALL=re.compile(r"(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx, base\)")
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
MODEL_COMPARE=re.compile(r"cr6\.compare<int32_t>\(ctx\.r3\.s32, 41, xer\);")
EXCERPT_LIMIT=40

def bounded_context(body, trigger, before=14, after=18):
    lines=body.splitlines()
    ids=[i for i,s in enumerate(lines) if trigger in s]
    samples=[]
    for n in ids[:4]:
        samples.append({"line":n+1,"lines":[f"{k+1}: {lines[k].strip()[:180]}"
          for k in range(max(0,n-before), min(len(lines),n+after+1))]})
    return {"occurrences":len(ids),"samples":samples}

def synthetic_safety(root):
    cpp=root/"pre265_menu_safety.cpp"
    cpp.write_text(r"""
#include <cassert>
#include <iostream>
static bool category_safe(unsigned model, bool career_owned,
                          bool prologue, bool opt_in,
                          unsigned packages) noexcept {
    if (model != 41u || !career_owned || prologue || !opt_in) return false;
    return packages > 0u;
}
static bool ordinary_car_original(unsigned model) noexcept {
    return model!=41u;
}
int main() {
    unsigned checks=0u;
    for (unsigned model=0; model<82; ++model)
    for (unsigned owned=0;owned<2;++owned)
    for (unsigned intro=0;intro<2;++intro)
    for (unsigned enabled=0;enabled<2;++enabled)
    for (unsigned count=0;count<9;++count) {
        const bool result=category_safe(model,owned,intro,enabled,count);
        const bool wanted=model==41 && owned && !intro && enabled && count>0;
        assert(result==wanted);
        if (count==0 || intro) assert(!result);
        assert(ordinary_car_original(model)==(model!=41));
        ++checks;
    }
    std::cout<<"PRE265_MOCK_GUARD_PASS "<<checks<<"\n";
}
""",encoding="utf-8")
    exe=root/"pre265_mock"
    cc=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",str(cpp),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if cc.returncode:return {"ok":False,"reason":"host_mock_compilation_failed",
                              "diagnostic":cc.stderr[-600:]}
    rr=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    return {"ok":rr.returncode==0,"result":rr.stdout.strip(),"checks":82*2*2*2*9,
            "not_game_code":True}

def audit(root):
    archive=root/"pre99.tar.gz"
    download(drive_client(),archive)
    dig,_md5,sz=sha_file(archive)
    if dig != EXPECTED_SHA256 or sz != EXPECTED_BYTES:
        raise ValueError("PRE99 authenticated snapshot mismatch")
    found={}
    candidates={}
    files_scanned=0
    with tarfile.open(archive,"r:gz",errorlevel=2) as t:
        for m in t:
            if not m.isfile() or not m.name.endswith(".cpp"):continue
            name=m.name.lstrip("./")
            target=name in SOURCE_HASHES
            if not (target or name.startswith("workspace/nativo/app/generated/default/")):
                continue
            if m.size>7_000_000:raise ValueError("Source file too large")
            f=t.extractfile(m)
            if f is None:raise ValueError("Unreadable source file")
            raw=f.read()
            if len(raw)!=m.size:raise ValueError("Truncated source member")
            files_scanned+=1
            sha=hashlib.sha256(raw).hexdigest()
            if target:
                if sha!=SOURCE_HASHES[name]:
                    raise ValueError("Pinned PAL source hash mismatch")
                found[name]=raw.decode("utf-8","replace")
            if b"sub_8256" not in raw and b"sub_82587498" not in raw:
                continue
            source=raw.decode("utf-8","replace")
            for fname in CANDIDATE_CALLEES:
                needle="DEFINE_REX_FUNC("+fname+")"
                if needle not in source:continue
                body=body_for_function(source,fname)
                if len(body)>150_000:raise ValueError("Unexpected huge function")
                calls=CALL.findall(body)
                candidates[fname]={
                    "file":name,"sha256":sha,"body_lines":len(body.splitlines()),
                    "nested_calls":calls[:55],
                    "cmp41":len(MODEL_COMPARE.findall(body)),
                    "count_maxlevel_not_in_source":("GetMaxLevel" not in body),
                    "literal_names_omitted_by_recompiler":True,
                    "opening":body.splitlines()[:13],
                    "zero_checks":bounded_context(body, "// cmplwi cr6,r3,0",before=5,after=8),
                }
    if len(found)!=len(SOURCE_HASHES):raise ValueError("Missing pinned source")
    pal_main=body_for_function(found[next(k for k in found if k.endswith(".5.cpp"))],"sub_82578988")
    pal_perf=body_for_function(found[next(k for k in found if k.endswith(".11.cpp"))],"sub_82582F70")
    if len(MODEL_COMPARE.findall(pal_main))!=1 or len(MODEL_COMPARE.findall(pal_perf))!=2:
        raise ValueError("Unexpected BMW type checks in known UI")
    menu_calls=pal_main.count("__imp__sub_82575370(ctx, base);")
    if menu_calls!=5:raise ValueError("Menu option structure changed")
    if len(candidates)<5:raise ValueError("Too many callee bodies absent")
    mock=synthetic_safety(root)
    return {
      "stage":"PRE265_BMW_UPGRADES_AND_HERO_MENU_READONLY",
      "status":"AUDIT_OK" if mock.get("ok") else "NEEDS_REVIEW",
      "snapshot_sha256_verified":dig,"read_only":True,"generated_pal_files_scanned":files_scanned,
      "pinned_generated_files":SOURCE_HASHES,
      "main_menu":{
          "function":"sub_82578988","model_41_compare_count":1,
          "add_category_calls":menu_calls,
          "guard_originally_hides_parts_and_performance":True,
          "model41_context":bounded_context(pal_main,"// cmpwi cr6,r3,41",6,24)},
      "performance_screen":{
          "function":"sub_82582F70","model_41_compare_count":2,
          "calls_count":len(CALL.findall(pal_perf)),
          "calls":CALL.findall(pal_perf)[:80],
          "model41_context":bounded_context(pal_perf,"// cmpwi cr6,r3,41",18,35),
          "zero_package_guard_unproven":True,
      },
      "candidate_helper_functions":candidates,
      "safe_menu_policy_mock":mock,
      "meaningful_limitations":[
         "Cannot prove Physics::Upgrades::GetMaxLevel( BMW model ) returns any particular value from these functions",
         "The empty public PhysicsUpgrades.cpp provides no implementation of GetMaxLevel",
         "Possible zero package counts require runtime/preset evidence before enabling menu",
         "PPC function names were generated from guest PCs, no debugging symbols",
         "No BMW performance packages or Junkman installs tested on device",
         "No Android APK produced or signed, no patch or save modified",
         "A host-side guard does not make PRE264 patch safe by itself",
         "No evidence that mapped source snapshot is bit-identical to V37 runtime"
      ],
      "approved_for_release":False,"apk_built":False,"signed":False,
      "source_modified":False,"save_modified":False,
      "credentials_accessed":False,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Invalid run-id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    out={"stage":"PRE265_BMW_UPGRADES_AND_HERO_MENU_READONLY","status":"FAILED",
         "read_only":True,"apk_built":False,"source_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre265_") as root:
            out=audit(Path(root))
    except Exception as e:out["error_type"]=type(e).__name__
    out["run_id"]=a.run_id
    out["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE265_STATUS",out["status"])
    print("PRE265_CANDIDATE_HELPERS",len(out.get("candidate_helper_functions",{})))
    print("PRE265_UPGRADE_COUNT_KNOWN",False)
    print("PRE265_MOCK",out.get("safe_menu_policy_mock",{}).get("result"))
    if out["status"]!="AUDIT_OK":print("PRE265_ERROR_TYPE",out.get("error_type"))
    return 0 if out["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    sys.exit(main())
