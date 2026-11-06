#!/usr/bin/env python3
"""PRE200: trace game-feature symbols through authenticated PRE99 source, read-only.

No changes to Android, APKs, game saves, key files, or game sources.
All source excerpts remain in private workflow artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre200-audit")
PINS = {
    "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp": "4902e1489464b04172410f9b3235958c944d628c1a2917a42de6ef0fa6fbb78b",
    "workspace/nativo/app_usa/src/nfsmw_recortes_carrera.cpp": "c0c22d9ec794760fe0094b6e6b8671e58d0e91b3e7a76fc96a4e1400d3295591",
    "workspace/android/app/src/main/java/io/github/nfsmwrecomp/TouchControllerView.java": "a438cc868932b0c8bf93d1f6675fbd4ad7f4ff4882a8b1832d651231bbd56e6d",
    "workspace/nativo/sdk/include/rex/input/mnk/mnk_input_driver.h": "b91ac65d89760bdfb1a59d83a5dd2e5c1f1eb3f7d8ea93a514c68c49075fcf9c",
    "workspace/nativo/app/src/nfsmw_app.h": "a8cd99605bc913931356262341d9606a6fb9bb579cc0e7ace33b266b67f8a1f4",
}
LOOK_AT = {
    "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp": [1068,1073,1083,1084,1087,1194,1198,1202,1239],
    "workspace/nativo/app_usa/src/nfsmw_recortes_carrera.cpp": [1068,1073,1083,1084,1087,1194,1198,1202,1239],
    "workspace/android/app/src/main/java/io/github/nfsmwrecomp/TouchControllerView.java": [285,286,287,870,2284,2285,2613,2614,2640],
    "workspace/nativo/sdk/include/rex/input/mnk/mnk_input_driver.h": [80],
    "workspace/nativo/app/src/nfsmw_app.h": [346],
}
FIND = {
    "nitro_native": re.compile(r"nitro|nitrous|n2o", re.I),
    "speedbreaker_native": re.compile(r"speed.?break|time.?dilation", re.I),
    "economy_native": re.compile(r"\b(?:money|cash|bankroll|career|wallet|savegame|profile)\b", re.I),
    "memory_hooks": re.compile(r"(?:guest.?memory|guest.?address|read.?memory|write.?memory|patch.?function|xex|hook.?function|ppc_context)", re.I)
}
EXCLUDE = ("/thirdparty/","/tests/","/test/","/generated/","/build/","/outputs/","/node_modules/", "keystore","password","secret","credential")
SFX = {".cpp",".cc",".c",".h",".hpp",".java",".kt"}
def sha(v:bytes)->str:
    return hashlib.sha256(v).hexdigest()

def numbered_context(lines:list[str], anchors:list[int], radius:int=4, cap:int=140)->list[dict]:
    positions=set()
    for line in anchors:
        positions.update(range(max(1,line-radius),min(len(lines),line+radius)+1))
    return [{"line":i,"text":lines[i-1].strip()[:200]}
            for i in sorted(positions)[:cap]]

def audit()->dict:
    result = {
        "stage":"PRE200_CHEATS_TARGETED_SOURCE_AUDIT",
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "status":"FAILED",
        "read_only":True,
        "apk_built":False,
        "patch_applied":False,
        "signer_accessed":False,
        "game_saves_touched":False,
        "v36_modified":False,
        "important_limitation":"PRE99 source is historical authenticated snapshot, not proof of currently running V36 exact modifications",
    }
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre200_") as temp:
        archive=Path(temp)/"PRE99.tar.gz"
        download(drive_client(),archive)
        digest,_,count=sha_file(archive)
        if digest!=EXPECTED_SHA256 or count!=EXPECTED_BYTES:
            raise ValueError("PRE200 backup hash and byte count mismatch")
        result["pre99_integrity_valid"]=True
        result["pre99_sha256"]=digest
        pinned={}
        scans=0
        counts={cat:0 for cat in FIND}
        candidates={cat:[] for cat in FIND}
        file_inventory=[]
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for member in tar:
                name=member.name.lstrip("./")
                if not member.isfile() or not name.startswith(("workspace/nativo/","workspace/android/")):
                    continue
                if name not in PINS:
                    if any(x in name.lower() for x in EXCLUDE):
                        continue
                    if not name.startswith(("workspace/nativo/app/src/","workspace/nativo/app_usa/src/","workspace/nativo/sdk/src/","workspace/nativo/sdk/include/","workspace/android/app/src/")):
                        continue
                    if Path(name).suffix.lower() not in SFX:
                        continue
                if member.size>4_000_000:
                    continue
                if any(x in name.lower() for x in ("password","secret","credential","keystore")):
                    continue
                f=tar.extractfile(member)
                if f is None:
                    continue
                raw=f.read()
                if len(raw)!=member.size:
                    raise ValueError("Truncated TAR member")
                digest_member=sha(raw)
                scans+=1
                lines=raw.decode("utf-8","replace").splitlines()
                if name in PINS:
                    pinned[name]=digest_member
                    result.setdefault("anchored_source_excerpts",{})[name]={
                        "sha256":digest_member,
                        "lines_total":len(lines),
                        "snippets":numbered_context(lines,LOOK_AT[name],radius=7,cap=180),
                    }
                if len(file_inventory)<180 and re.search(r"recomp|memory|hook|career|save|game|xex|recortes|main",Path(name).name,re.I):
                    file_inventory.append({"path":name,"sha256":digest_member})
                for category,pat in FIND.items():
                    if category=="memory_hooks" and not ("/app/src/" in name or "/sdk/src/" in name): 
                        continue
                    indices=[i for i,s in enumerate(lines,1) if pat.search(s)]
                    counts[category]+=len(indices)
                    if indices and len(candidates[category])<50:
                        candidates[category].append({
                            "path":name,"sha256":digest_member,"count":len(indices),
                            "first_line_numbers":indices[:15],
                            "examples":[{"line":i,"text":lines[i-1].strip()[:160]} for i in indices[:4]]
                        })
        if pinned!=PINS:
            result["pinned_observed"]=pinned
            raise ValueError("PRE200 SHA-pinned source mismatch")
        result.update({
            "pinned_verified":True,
            "source_files_scanned":scans,
            "keyword_counts":counts,
            "candidates":candidates,
            "source_inventory":file_inventory,
            "status":"AUDIT_OK"
        })
    return result

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):
        raise ValueError("Invalid run id")
    OUT.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE200_CHEATS_TARGETED_SOURCE_AUDIT",
            "status":"FAILED","run_id":args.run_id,
            "read_only":True,"apk_built":False,"patch_applied":False,"signer_accessed":False}
    try:
        result=audit()
        result["run_id"]=args.run_id
    except Exception as error:
        result["error_type"]=type(error).__name__
    finally:
        path=OUT/"PRE200_CHEATS_TARGETED_READONLY.json"
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE200_STATUS",result["status"])
        print("PRE200_PRE99_VERIFIED",result.get("pre99_integrity_valid",False))
        print("PRE200_PINS_VERIFIED",result.get("pinned_verified",False))
        print("PRE200_SCANNED",result.get("source_files_scanned"))
        print("PRE200_KEYWORDS",result.get("keyword_counts"))
        if result["status"]!="AUDIT_OK":
            print("PRE200_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
