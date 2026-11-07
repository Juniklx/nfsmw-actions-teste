#!/usr/bin/env python3
"""PRE346: authenticated PRE99 native source search for independently named player-car references.
No changes to guest code, APK, credentials, keys, or save. No raw secrets in report.
"""
from __future__ import annotations
import hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre346/PRE346_PLAYER_CAR_SOURCE_REFERENCES.json")
EXT=(".cpp",".hpp",".h",".cc",".cxx",".c")
SKIP_SEGMENTS=("/generated/","/thirdparty/","/third_party/","/external/",
               "/build/","/vendor/","/test/","/tests/","/examples/")
ROOTS=("workspace/nativo/app/","workspace/nativo/sdk/","workspace/android/app/src/main/cpp/",
       "workspace/nativo/app_usa/")
EXPLICIT=re.compile(r"(?i)\b(?:get_?player_?(?:car|vehicle|ride)|player_?(?:car|vehicle|ride)(?:_?ptr)?|"
                    r"(?:local|human|controlled)_?player_?(?:car|vehicle)|"
                    r"(?:local|human|controlled)_?(?:car|vehicle)|"
                    r"(?:car|vehicle)_?controlled_?by_?player|is_?player_?(?:car|vehicle)|"
                    r"playercar|playervehicle)\b")
COOCCUR=re.compile(r"(?i)(?:\bplayer\b.{0,80}\b(?:car|vehicle|driver)\b|"
                   r"\b(?:car|vehicle|driver)\b.{0,80}\bplayer\b)")
MAX_LINES=4
MAX_GLOBAL=120
def select_lines(text:str):
    rows=[]
    for n,line in enumerate(text.splitlines(),1):
        if len(line)>3500 or not line.strip():continue
        clean=line.strip()
        if clean.startswith(("//","/*","*","#")):continue
        tag=("explicit" if EXPLICIT.search(line) else
             "cooccur" if COOCCUR.search(line) else None)
        if tag is None:continue
        # Never export arbitrary code line strings: count and line only.
        rows.append({"line":n,"tag":tag})
        if len(rows)>=MAX_LINES:break
    return rows
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE346_PLAYER_CAR_NAMED_SOURCE_SEARCH","status":"FAILED",
            "apk_built":False,"guest_modified":False,"owner_verified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre346_") as td:
            arc=Path(td)/"pre99.tar.gz"
            download(drive_client(),arc)
            sha,_,size=sha_file(arc)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 integrity mismatch")
            scanned=0;matched=0;hits=[];truncated=False
            with tarfile.open(arc,"r:gz") as tar:
                for member in tar:
                    name=member.name.lstrip("./")
                    if (not member.isfile() or not name.endswith(EXT)
                        or not name.startswith(ROOTS)
                        or any(x in name.lower() for x in SKIP_SEGMENTS)
                        or any(x in name.lower() for x in ("secret","keystore","credential","password","signing"))):
                        continue
                    if member.size>1_000_000:continue
                    scanned+=1
                    stream=tar.extractfile(member)
                    if stream is None:continue
                    data=stream.read()
                    rows=select_lines(data.decode("utf-8",errors="replace"))
                    if not rows:continue
                    matched+=1
                    if len(hits)<MAX_GLOBAL:
                        hits.append({"source":name,"rows":rows,
                            "sha256":hashlib.sha256(data).hexdigest()})
                    else:truncated=True
            if scanned<5:raise ValueError("insufficient native source inventory")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "source_files_scanned":scanned,"files_with_candidate_terms":matched,
                "bounded_file_hits":hits,"matches_truncated":truncated,
                "interpretation":"Lexical leads only. Matching identifiers are not proof of a player pointer or Nitro owner; code control flow must be independently checked."})
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE346_STATUS",result["status"])
    print("PRE346_SCANNED",result.get("source_files_scanned",0))
    print("PRE346_FILES_MATCHED",result.get("files_with_candidate_terms",0))
    print("PRE346_OWNER_VERIFIED",False)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
