#!/usr/bin/env python3
"""PRE240: verify already-read old balances at PAL money store sites, read-only.

Purely synthetic UINT32 non-decrease policy test; never patch, sign or build game.
"""
from __future__ import annotations
import hashlib
import json
import random
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import TARGETS, body_for_function, COMMENT, STORE

OUT=Path("/tmp/nfsmw-pre240/NFSMW_PRE240_PAL_OLD_VALUE_AND_LOGGER_AUDIT.json")
EXPECTED_HASHES={
 "workspace/nativo/app/generated/default/nfsmw_recomp.103.cpp":
 "88d866e93ccbb448186e45cb106fd16d42e033b7c3f9959105ceeea430c3abef",
 "workspace/nativo/app/generated/default/nfsmw_recomp.7.cpp":
 "0f423d5906ebadf38209a4e9c7e43449573b6f37f02f3df6528f5bef1251daa6",
}
OLD={
 "sub_8256BFC8":["r9","r9","r3"],
 "sub_82564D80":["r8","r10","r10","r10","r10"],
}
LOGFILES={
 "workspace/nativo/sdk/include/rex/logging.h",
 "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp",
 "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp",
}
LOG_PATTERN=re.compile(r"(?i)(?:\b(?:rexlog|rex::log|rex::logging|logger|logging|log_info|log_warn|log_error|spdlog|log::)\b|#\s*(?:include|define).*log)")
MAX_LEN=3_000_000

def inspect_old(src,target,expected,old_names):
    body=body_for_function(src,target)
    lines=body.splitlines()
    hits=[]
    for i,line in enumerate(lines):
        cm=COMMENT.match(line)
        if cm and i+1<len(lines) and STORE.match(lines[i+1]):
            hits.append(i)
    if len(hits)!=len(expected["stores"]) or len(hits)!=len(old_names):
        raise ValueError("Store count mismatch")
    samples=[]
    for ordinal,(i,old_name) in enumerate(zip(hits,old_names),1):
        comment=lines[i].strip()
        st=lines[i+1].strip()
        # Check an existing PPC guest load of the OLD value, strictly before the store.
        prefix=lines[max(0,i-120):i]
        load_re=re.compile(r"^\s*(?:ctx\.)?"+re.escape(old_name)+r"\.u64\s*=\s*REX_LOAD_U32\s*\(")
        matches=[k for k,row in enumerate(prefix) if load_re.search(row)]
        if not matches:
            # A register containing a pre-existing amount is not proof of balance.
            samples.append({"ordinal":ordinal,"comment":comment,"store":st,
              "old_candidate":old_name,"prior_old_load_found":False})
            continue
        last_idx=matches[-1]
        intervening=prefix[last_idx+1:]
        assignment=re.compile(r"^\s*(?:ctx\.)?"+re.escape(old_name)+r"\.(?:u64|s64|u32|s32)\s*=")
        changed=[row.strip()[:180] for row in intervening if assignment.search(row)]
        samples.append({
           "ordinal":ordinal,
           "comment":comment,
           "store":st,
           "old_candidate":old_name,
           "prior_old_load_found":True,
           "old_load_snippet":prefix[last_idx].strip()[:280],
           "intervening_assignment_count":len(changed),
           "intervening_assignments":changed[:6],
           "no_additional_guest_load_proposed":True
        })
    return samples

def cpp_policy_test(root):
    src=root/"policy.cpp"
    src.write_text(r"""
#include <cstdint>
#include <limits>
#include <random>
#include <cassert>
#include <iostream>
static std::uint32_t policy(bool enabled, std::uint32_t original_old,
                            std::uint32_t proposed) noexcept {
  if (!enabled || proposed >= original_old) return proposed;
  return original_old;
}
int main() {
  std::mt19937 engine(0xBEA528u);
  for (int i = 0; i < 40000; ++i) {
    auto a = static_cast<std::uint32_t>(engine());
    auto b = static_cast<std::uint32_t>(engine());
    assert(policy(false,a,b)==b);
    assert(policy(true,a,b)>=a);
    if (b>=a) assert(policy(true,a,b)==b);
    else assert(policy(true,a,b)==a);
  }
  assert(policy(true,0u,0u)==0u);
  assert(policy(true,10u,0u)==10u);
  assert(policy(true,10u,15u)==15u);
  assert(policy(false,10u,0u)==0u);
  std::cout << "PRE240_POLICY_SYNTHETIC_40000_OK\n";
  return 0;
}
""",encoding="utf-8")
    exe=root/"policy"
    build=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",str(src),"-o",str(exe)],
       capture_output=True,text=True,timeout=25)
    if build.returncode!=0: return {"compiled":False,"returncode":build.returncode}
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    return {"compiled":True,"returncode":run.returncode,
        "result":run.stdout.strip()[:100],
        "cases_synthetic":40000,"game_code_compiled":False}

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    out={"stage":"PRE240_PAL_OLD_MONEY_VALUE_READONLY",
       "status":"FAILED","phase":"START",
       "source_modified":False,"game_build":False,"apk_built":False,
       "savedata_touched":False,"signing_material_accessed":False,
       "extra_guest_reads":False,"cheats_enabled":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre240_") as td:
            root=Path(td)
            out["phase"]="DOWNLOAD_PINNED_PRE99"
            archive=root/"pre99.tar.gz"
            download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("Backup integrity mismatch")
            out["pre99_verified"]=True
            contents={}
            requested=set(EXPECTED_HASHES)|LOGFILES
            out["phase"]="READ_EXACT_SOURCES"
            with tarfile.open(archive,"r:gz") as t:
                for m in t:
                    name=m.name.lstrip("./")
                    if not m.isfile() or name not in requested:continue
                    if m.size>MAX_LEN:raise ValueError("Unexpected member size")
                    f=t.extractfile(m)
                    if f is None:raise ValueError("Cannot read member")
                    dat=f.read()
                    digest=hashlib.sha256(dat).hexdigest()
                    if name in EXPECTED_HASHES and digest!=EXPECTED_HASHES[name]:
                        raise ValueError("Generated source hash unexpectedly changed")
                    contents[name]={"digest":digest,"text":dat.decode("utf-8","replace")}
            if not all(k in contents for k in EXPECTED_HASHES):
                raise ValueError("Missing generated sources")
            out["phase"]="VERIFY_PRESTORE_OLD_VALUE"
            out["functions"]=[]
            for target,spec in TARGETS.items():
                src=contents[spec["filename"]]
                samples=inspect_old(src["text"],target,spec,OLD[target])
                out["functions"].append({"function":target,"file_sha256":src["digest"],
                  "preserve_original_store":True,"old_value_candidates":samples})
            samples=sum((x["old_value_candidates"] for x in out["functions"]),[])
            out["sites"]=len(samples)
            out["prior_loads_found"]=sum(bool(x["prior_old_load_found"]) for x in samples)
            out["prior_loads_unchanged"]=sum(bool(x["prior_old_load_found"]) and not x.get("intervening_assignment_count") for x in samples)
            out["phase"]="LOG_API_EXCERPTS"
            out["logging_sources"]=[]
            for name in sorted(LOGFILES):
                if name not in contents:continue
                src=contents[name]
                lines=src["text"].splitlines()
                rows=[{"line":i+1,"text":line.strip()[:230]}
                   for i,line in enumerate(lines) if LOG_PATTERN.search(line)]
                out["logging_sources"].append({
                    "filename":name,"sha256":src["digest"],
                    "match_count":len(rows),
                    "samples":rows[:45],
                    "first_header_lines":[{"line":i+1,"text":s[:230]}
                        for i,s in enumerate(lines[:110])]
                        if name.endswith("/rex/logging.h") else []
                })
            out["phase"]="SYNTHETIC_POLICY_UNIT_TEST"
            out["synthetic_policy"]=cpp_policy_test(root)
            out["limitations"]=[
             "Matched prior loads are static register dataflow candidates, not proof of live money transactions.",
             "The synthetic comparison is unsigned uint32 and does not prove the actual in-game signedness.",
             "No game or SDK compilation and no Android runtime executed.",
             "The codegen .cpp files are generated; do not edit them directly in a release.",
             "Do not enable the policy until safe per-edition patch-integration and rollback are verified."
            ]
            out["status"]="AUDIT_OK" if out["sites"]==8 and out["prior_loads_unchanged"]==8 and out["synthetic_policy"]["returncode"]==0 else "NEEDS_REVIEW"
            out["phase"]="COMPLETE"
    except Exception as ex:
        out["error_type"]=type(ex).__name__
        out["failed_phase"]=out["phase"]
        print("PRE240_ERROR",type(ex).__name__,out["phase"])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE240_STATUS",out["status"])
    print("PRE240_OLD_LOADS",out.get("prior_loads_found",0),out.get("prior_loads_unchanged",0),"/",out.get("sites",0))
    return 0 if out["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    sys.exit(main())
