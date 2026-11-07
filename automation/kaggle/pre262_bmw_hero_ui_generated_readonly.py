#!/usr/bin/env python3
"""PRE262: authenticated PAL/USA generated PPC immediate-41 discovery only.
No source modifications, no build, no signing, no game saves. Candidate does
not imply identified HeroCar method; all mappings remain hypotheses.
"""
from __future__ import annotations
import argparse, bisect, hashlib, json, re, subprocess, sys, tarfile, tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre262/PRE262_BMW_HERO_UI_PAL_READONLY.json")
ROOTS={
  "PAL":"workspace/nativo/app/generated/default/",
  "USA":"workspace/nativo/app_usa/generated/default/",
}
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
CMP=re.compile(r"(?i)\b(?:cmpwi|cmplwi)\s+(?:(?:cr[0-7]),\s*)?r\d+,\s*(?:0x0*29|41)\b")
CMP_ANY=re.compile(r"(?i)\b(?:cmpwi|cmplwi)\b")
REG41=re.compile(r"(?i)\b(?:0x0*29|41)\b")
LI_BOOLEAN=re.compile(r"(?i)\b(?:li|addi)\s+r3\s*,\s*(?:r0\s*,\s*)?[01]\b")
MAX_REPORT=120
MAX_SRC=7_000_000

def synthetic_policy_test(root:Path)->dict:
    cpp=root/"pre262_mock.cpp"
    cpp.write_text(r"""
#include <cassert>
#include <iostream>
// Isolated menu mock, NOT a game patch. The real identity and ownership API
// remains unknown. Keep the original hero classification untouched.
static bool show_extra_categories(bool original_hero,
                                  bool bmw_model,
                                  bool validated_career_owned,
                                  bool intro_prologue,
                                  bool explicit_toggle) noexcept {
    if (!original_hero) return true;
    return explicit_toggle && bmw_model && validated_career_owned && !intro_prologue;
}
int main() {
    unsigned cases=0;
    for (unsigned bits=0;bits<32;++bits) {
        bool hero=bits&1, bmw=bits&2, own=bits&4, intro=bits&8, enabled=bits&16;
        bool got=show_extra_categories(hero,bmw,own,intro,enabled);
        bool expected=!hero || (enabled && bmw && own && !intro);
        assert(got==expected);
        if (hero && (!enabled || intro || !own || !bmw)) assert(!got);
        if (!hero) assert(got);
        ++cases;
    }
    assert(!show_extra_categories(true,true,true,false,false));
    assert(show_extra_categories(true,true,true,false,true));
    assert(!show_extra_categories(true,true,true,true,true));
    assert(show_extra_categories(false,false,true,false,false));
    std::cout<<"PRE262_MOCK_POLICY_32_CASES_OK\n";
    return 0;
}
""",encoding="utf-8")
    exe=root/"pre262_mock"
    comp=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O1",
                         str(cpp),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if comp.returncode:
        return {"ok":False,"phase":"compile","returncode":comp.returncode,
                "diagnostic":comp.stderr[-1000:]}
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"ok":run.returncode==0,"cases":32,"output":run.stdout.strip()[:100],
            "returncode":run.returncode,"game_code_compiled":False}

def audit(root:Path)->dict:
    backup=root/"pre99.tar.gz"
    download(drive_client(),backup)
    digest,_md5,size=sha_file(backup)
    if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
        raise ValueError("PRE99 archive fingerprint mismatch")
    counts={ed:{"files":0,"bytes":0,"cmp_instructions":0,"literal_41_cmp":0,
                 "matched_functions":0} for ed in ROOTS}
    candidates=[]
    per_file=[]
    with tarfile.open(backup,"r:gz",errorlevel=2) as tar:
        for m in tar:
            if not m.isfile() or not m.name.endswith(".cpp"):continue
            n=m.name.lstrip("./")
            ed=next((key for key,p in ROOTS.items() if n.startswith(p)),None)
            if ed is None:continue
            if m.size>MAX_SRC:raise ValueError("Generated source exceeds bounded size")
            f=tar.extractfile(m)
            if f is None:raise ValueError("Unreadable generated member")
            b=f.read()
            if len(b)!=m.size:raise ValueError("Truncated member")
            counts[ed]["files"]+=1
            counts[ed]["bytes"]+=len(b)
            src=b.decode("utf-8","replace")
            cmps=list(CMP_ANY.finditer(src))
            matches=list(CMP.finditer(src))
            counts[ed]["cmp_instructions"]+=len(cmps)
            counts[ed]["literal_41_cmp"]+=len(matches)
            if not matches:continue
            defs=list(DEF.finditer(src))
            offsets=[p.start() for p in defs]
            per_fun={}
            for match in matches:
                j=bisect.bisect_right(offsets,match.start())-1
                if j<0:continue
                fun=defs[j].group(1)
                start=defs[j].start()
                end=defs[j+1].start() if j+1<len(defs) else len(src)
                item=per_fun.setdefault(fun,{"function":fun,"file":n,"edition":ed,
                   "file_sha256":hashlib.sha256(b).hexdigest(),
                   "function_chars":end-start,"cmp_41_count":0,
                   "excerpts":[],"score_hint":0})
                item["cmp_41_count"]+=1
                if len(item["excerpts"])<2:
                    a=max(start,match.start()-420)
                    z=min(end,match.end()+420)
                    excerpt=src[a:z].splitlines()
                    item["excerpts"].append({"relative_byte_offset":match.start()-start,
                                             "comment":match.group(0),
                                             "nearby_lines":[line.strip()[:180] for line in excerpt[:28]]})
                if item["function_chars"]<2200:item["score_hint"]+=2
                if item["function_chars"]<5000:item["score_hint"]+=1
                block=src[max(start,match.start()-500):min(end,match.end()+500)]
                if LI_BOOLEAN.search(block):item["score_hint"]+=3
                if re.search(r"(?i)\b(?:bl|blr|beq|bne)\b",block):item["score_hint"]+=1
            counts[ed]["matched_functions"]+=len(per_fun)
            per_file.append({"file":n,"edition":ed,"matched_functions":len(per_fun),
                             "literal_41_cmp":len(matches)})
            candidates.extend(per_fun.values())
    candidates.sort(key=lambda x:(x["edition"]!="PAL",-x["score_hint"],
                                  x["function_chars"],x["function"]))
    mock=synthetic_policy_test(root)
    return {
      "stage":"PRE262_BMW_HERO_UI_PAL_IMMEDIATE_DISCOVERY",
      "status":"AUDIT_OK" if mock["ok"] and sum(s["files"] for s in counts.values())>100 else "NEEDS_REVIEW",
      "pre99_fingerprint_verified":True,
      "pre99_sha256":digest,
      "counts":counts,
      "matching_function_candidates_total":len(candidates),
      "candidate_function_samples":candidates[:MAX_REPORT],
      "matching_file_summary":per_file[:160],
      "synthetic_host_policy":mock,
      "cross_version_reference":{
        "decomp_repo":"dbalatoni13/nfsmw",
        "IsHeroCar_definition":"CarCustomizeManager::IsHeroCar returns BMWM3GTRE46 type == 41",
        "menu_block":"CustomizeMain::BuildOptionsList hides Parts+Performance when IsHeroCar",
        "status":"PUBLIC_SOURCE_ONLY_NOT_MATCHED_TO_V37"
      },
      "limitations":[
        "Constant 41 is a broad pattern; candidate rank does NOT identify HeroCar or a patch site",
        "PPC generated code may express a comparison via other opcode, constant or inlined logic",
        "No guest function PC proven against the V37 binary",
        "PRE99 source is a pinned snapshot and might predate current V37 patch tree",
        "A visible menu does not guarantee BMW has valid performance upgrade packages",
        "Synthetic C++ is mock-only, not integrated with guest code or APK",
        "No Android build, signing, release key access, save editing or runtime test"
      ],
      "apk_built":False,"release_signed":False,"game_sources_modified":False,
      "save_modified":False,"credentials_accessed":False,"candidate_patch_proven":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("run-id must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"status":"FAILED","phase":"BOOT","read_only":True,
            "apk_built":False,"game_sources_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre262_") as tmp:
            result=audit(Path(tmp))
    except Exception as e:
        result["error_type"]=type(e).__name__
        result["phase"]="STATIC_READ_ONLY_SCAN_OR_MOCK"
    result["github_run_id"]=args.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE262_STATUS",result["status"])
    print("PRE262_COUNT",result.get("counts"))
    print("PRE262_CANDIDATES",result.get("matching_function_candidates_total"))
    print("PRE262_HOST_POLICY",result.get("synthetic_host_policy"))
    if result["status"] not in ("AUDIT_OK",):
        print("PRE262_ERROR",result.get("error_type"),result.get("phase"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    sys.exit(main())
