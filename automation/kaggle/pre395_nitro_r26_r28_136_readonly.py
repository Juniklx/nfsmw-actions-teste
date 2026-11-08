#!/usr/bin/env python3
"""PRE395: authenticated static reference-origin evidence for r26/r28 and Nitro +136.
This is source-only lexical analysis. No game, APK, save, signing changes.
"""
from pathlib import Path
import hashlib,json,re,tarfile,tempfile,sys
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre242_pal_float_dataflow_readonly import TARGETS
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre395/PRE395_NITRO_REFERENCE_ORIGINS.json")
SPEC=TARGETS["nitro"]
TERMS={
 "field136":re.compile(r"REX_(?:LOAD|STORE)_U32\(\s*r31\.(?:u32|u64|s32|s64)\s*\+\s*136\b"),
 "r26_assignment":re.compile(r"^\s*r26\.(?:u32|u64|s32|s64)\s*="),
 "r28_assignment":re.compile(r"^\s*r28\.(?:u32|u64|s32|s64)\s*="),
 "r26_load":re.compile(r"\bREX_LOAD_U32\(\s*r26\.(?:u32|u64|s32|s64)"),
 "r28_load":re.compile(r"\bREX_LOAD_U32\(\s*r28\.(?:u32|u64|s32|s64)"),
}
def study(src):
    rows=body_for_function(src,SPEC["function"]).splitlines()
    found={}
    for tag,regex in TERMS.items():
        ids=[i for i,row in enumerate(rows) if regex.search(row)]
        if tag=="field136" and len(ids)<2:raise ValueError("Expected field +136 references not found")
        if tag.endswith("_assignment") and not ids:raise ValueError("Expected source register assignment missing")
        windows=[]
        for i in ids[:26]:
            lo=max(0,i-8);hi=min(len(rows),i+12)
            windows.append({"line":i+1,"rows":[{"n":j+1,"code":rows[j].strip()[:230]} for j in range(lo,hi)]})
        found[tag]={"count":len(ids),"line_indices":[i+1 for i in ids[:64]],"windows":windows}
    return {"function":SPEC["function"],"body_lines":len(rows),"evidence":found,
      "limits":"Only bounded lexical windows. No interprocedural alias analysis, vtable inference, or player owner proof."}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE395_NITRO_REFERENCE_ORIGINS_SOURCE","status":"FAILED",
      "read_only":True,"owner_verified":False,"apk_built":False,"game_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre395_") as td:
            f=Path(td)/"pre99.tar.gz";download(drive_client(),f)
            archive_sha,_,size=sha_file(f)
            if archive_sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
            with tarfile.open(f,"r:gz") as tf:
                member=tf.getmember(SPEC["file"]);handle=tf.extractfile(member)
                if handle is None:raise ValueError("source unavailable")
                source=handle.read()
            if hashlib.sha256(source).hexdigest()!=SPEC["sha256"]:
                raise ValueError("source SHA mismatch")
            result.update(study(source.decode("utf-8","replace")))
            result.update({"status":"AUDIT_OK","archive_sha256":archive_sha,
                           "source_sha256":SPEC["sha256"]})
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE395_STATUS",result["status"])
    print("PRE395_136_REFERENCES",result.get("evidence",{}).get("field136",{}).get("count",0))
    print("PRE395_OWNER_VERIFIED",False)
    print("PRE395_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
