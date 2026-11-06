#!/usr/bin/env python3
"""PRE203 exhaustive game-generated C++/header keyword audit of authenticated PRE99.
Reads only data from a temporary verified backup. No patch, build, or signing.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre203")
PFX=("workspace/nativo/app/generated/","workspace/nativo/app_usa/generated/")
PATTERNS={
"nitro":re.compile(r"\b(?:nitro|nitrous|nitrous_oxide|n2o)\b",re.I),
"speedbreaker":re.compile(r"\b(?:speed.?breaker|speed.?break|time.?dilation)\b",re.I),
"money":re.compile(r"\b(?:money|cash|wallet|bankroll|career_cash)\b",re.I),
}
def audit():
    with tempfile.TemporaryDirectory(prefix="pre203_") as temp:
        p=Path(temp)/"PRE99.tar.gz"
        download(drive_client(),p)
        actual,_,size=sha_file(p)
        if actual!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 SHA and byte size must match")
        counts={ed:{k:0 for k in PATTERNS} for ed in ("pal","usa")}
        hits={ed:{k:[] for k in PATTERNS} for ed in ("pal","usa")}
        totals={ed:{"files_scanned":0,"bytes_scanned":0} for ed in ("pal","usa")}
        with tarfile.open(p,"r:gz",errorlevel=2) as t:
            for m in t:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.startswith(PFX):
                    continue
                if Path(name).suffix.lower() not in (".cpp",".h",".json",".cmake"):
                    continue
                if m.size>5_000_000:raise ValueError("Unexpected generated file size")
                stream=t.extractfile(m)
                if stream is None:raise ValueError("Cannot read generated file")
                raw=stream.read()
                if len(raw)!=m.size:raise ValueError("Short generated source read")
                ed="usa" if name.startswith(PFX[1]) else "pal"
                totals[ed]["files_scanned"]+=1
                totals[ed]["bytes_scanned"]+=len(raw)
                lines=raw.decode("utf-8","replace").splitlines()
                for key,rx in PATTERNS.items():
                    found=[(i,v) for i,v in enumerate(lines,1) if rx.search(v)]
                    counts[ed][key]+=len(found)
                    if found and len(hits[ed][key])<35:
                        hits[ed][key].append({"file":name,"sha256":hashlib.sha256(raw).hexdigest(),
                            "occurrences":len(found),
                            "first_hits":[{"line":i,"text":v.strip()[:160]} for i,v in found[:6]]})
        return {"stage":"PRE203_EXHAUSTIVE_GENERATED_GAME_SOURCE_KEYWORD_READONLY",
            "status":"AUDIT_OK",
            "pre99_sha256_verified":True,"pre99_sha256":actual,
            "read_only":True,"patch":False,"build":False,"signer":False,
            "source_mutated":False,"saves_mutated":False,
            "totals":totals,"occurrences":counts,"matching_files":hits,
            "limitation":"Text keyword search only: zero matches does not prove no game feature, source functions are address-named"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Invalid run id")
    OUT.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE203_EXHAUSTIVE_GENERATED_GAME_SOURCE_KEYWORD_READONLY",
            "status":"FAILED","read_only":True,"build":False,"patch":False,"signer":False}
    try:result=audit()
    except Exception as ex:result["error_type"]=type(ex).__name__
    result["run_id"]=a.run_id
    (OUT/"PRE203_GENERATED_KEYWORDS_READONLY.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE203",result["status"],"TOTALS",result.get("totals"),
        "COUNTS",result.get("occurrences"))
    if "error_type" in result:print("PRE203_ERROR_TYPE",result["error_type"])
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
