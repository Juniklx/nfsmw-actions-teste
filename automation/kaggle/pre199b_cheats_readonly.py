#!/usr/bin/env python3
"""PRE199B: audit the authenticated PRE99 source tree without modifying game files."""
import argparse, hashlib, json, re, tarfile, tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre199b")
PATTERNS = {
    "nitro": re.compile(r"nitro|nitrous|\\bn2o\\b|\\bnos\\b",re.I),
    "speedbreaker": re.compile(r"speed.?break|slow.?mo|bullet.?time|time.?dilation",re.I),
    "dinheiro": re.compile(r"money|cash|bankroll|wallet|dinheiro",re.I),
}
PINS = {
    "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp": "046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2",
    "workspace/nativo/app_usa/src/nfsmw_nativo_dibujos.cpp": "92e0a15836217a535c6f81e2461381616f46c331c83201cabd14a71c2d8c2342",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp": "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034",
}
EXT = {".cpp",".c",".cc",".cxx",".h",".hpp",".inl",".ipp",".kt",".java",".json",".cmake",".kts"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    result={"phase":"PRE199B_READ_ONLY","run_id":args.run_id,"status":"FAILED",
            "game_files_modified":False,"apk_compiled":False,"release_signer_accessed":False}
    try:
        with tempfile.TemporaryDirectory() as td:
            archive=Path(td)/"PRE99.tar.gz"
            download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE99 integrity mismatch")
            found={}
            hits={k:[] for k in PATTERNS}
            counts={k:0 for k in PATTERNS}
            scanned=0
            with tarfile.open(archive,"r:gz") as t:
                for m in t:
                    name=m.name.lstrip("./")
                    if not m.isfile() or not name.startswith(("workspace/nativo/","workspace/android/")):
                        continue
                    if Path(name).suffix.lower() not in EXT and Path(name).name!="CMakeLists.txt":
                        continue
                    if m.size>6000000 or any(v in name.lower() for v in ("/build/","/.git/","/outputs/","keystore","secret","password","credential")):
                        continue
                    f=t.extractfile(m)
                    if f is None: continue
                    data=f.read()
                    if len(data)!=m.size: raise ValueError("Truncated file")
                    scanned+=1
                    h=hashlib.sha256(data).hexdigest()
                    if name in PINS: found[name]=h
                    lines=data.decode("utf-8","replace").splitlines()
                    for category,rx in PATTERNS.items():
                        nums=[i for i,line in enumerate(lines,1) if rx.search(line)]
                        if nums:
                            counts[category]+=len(nums)
                            if len(hits[category])<120:
                                hits[category].append({"path":name,"sha256":h,"lines":nums[:12],"count":len(nums)})
            if found != PINS: raise ValueError("Pinned sources mismatch")
            result.update({"status":"AUDIT_OK","backup_sha256_valid":True,
                           "source_pins_valid":True,"sources_scanned":scanned,
                           "count_by_category":counts,"matches":hits})
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    finally:
        (OUT/"PRE199B_REPORT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE199B",result["status"],result.get("count_by_category"),"error",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    raise SystemExit(main())
