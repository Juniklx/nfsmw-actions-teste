#!/usr/bin/env python3
"""PRE393: SHA-pinned PAL source-only Nitro +296 reference dataflow audit.
No modifications of guest memory, source tree, APK, signing, or saves.
"""
from pathlib import Path
import hashlib,json,re,sys,tarfile,tempfile
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS
OUT=Path("/tmp/nfsmw-pre393/PRE393_NITRO_296_DATAFLOW.json")
TARGET=TARGETS["nitro"]
BASE296=re.compile(r"REX_LOAD_U32\(\s*r31\.(?:u32|u64|s32|s64)\s*\+\s*296\s*\)")
OFFSET252=re.compile(r"REX_(?:LOAD|STORE)_U32\(\s*r31\.(?:u32|u64|s32|s64)\s*\+\s*252\s*[,)]")
REG_LHS=re.compile(r"^\s*([A-Za-z_][A-Za-z_0-9]*\.(?:u32|u64|s32|s64))\s*=\s*REX_LOAD_U32\(")
CONTEXT_TERMS=re.compile(r"(?i)\b(?:r3|r31|r4|r5|r6|r7|r8|r9|r10|r11|r12|ctr|lr|temp)\.(?:u32|u64|s32|s64)|REX_CALL_INDIRECT_FUNC|REX_LOAD|REX_STORE")
def cap(line):return line.strip()[:220]
def audit(source:str)->dict:
    body=body_for_function(source,TARGET["function"])
    rows=body.splitlines()
    matches=[i for i,line in enumerate(rows) if BASE296.search(line)]
    if len(matches)!=3:raise ValueError("Expected three Nitro +296 loads in authenticated PAL function")
    loads=[]
    for i in matches:
        lo=max(0,i-14);hi=min(len(rows),i+65)
        # Only a bounded lexical slice: register dataflow may have aliases not resolved.
        forward=[]
        for j in range(i+1,hi):
            if CONTEXT_TERMS.search(rows[j]):
                forward.append({"relative_line":j+1,"code":cap(rows[j])})
        loads.append({"relative_line":i+1,"code":cap(rows[i]),
          "preceding":[{"relative_line":j+1,"code":cap(rows[j])} for j in range(lo,i)],
          "following_window":[{"relative_line":j+1,"code":cap(rows[j])} for j in range(i+1,hi)],
          "candidate_register_uses":forward[:32]})
    return {"function":TARGET["function"],"function_lines":len(rows),
      "field296_loads":loads,
      "field252_access_count":sum(bool(OFFSET252.search(x)) for x in rows),
      "limitation":"Local source windows only; no semantic typing or full alias analysis. Pointer +296 is not classified as player vehicle."}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE393_NITRO_296_SOURCE_DATAFLOW","status":"FAILED",
       "read_only":True,"owner_verified":False,"vehicle_reference_verified":False,
       "cheat_enabled":False,"apk_built":False,"game_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre393_") as td:
            path=Path(td)/"pre99.tar.gz";download(drive_client(),path)
            digest,_,size=sha_file(path)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
            with tarfile.open(path,"r:gz") as tf:
                m=tf.getmember(TARGET["file"])
                stream=tf.extractfile(m)
                if stream is None:raise ValueError("target shard stream absent")
                data=stream.read()
            if hashlib.sha256(data).hexdigest()!=TARGET["sha256"]:
                raise ValueError("Nitro PAL shard SHA mismatch")
            result.update(audit(data.decode("utf-8","replace")))
            result.update({"status":"AUDIT_OK","snapshot_sha256":digest,"source_sha256":TARGET["sha256"]})
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE393_STATUS",result["status"])
    print("PRE393_LOAD_296",len(result.get("field296_loads",[])))
    print("PRE393_OWNER_VERIFIED",False)
    print("PRE393_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
