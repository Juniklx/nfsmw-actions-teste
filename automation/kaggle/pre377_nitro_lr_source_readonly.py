#!/usr/bin/env python3
"""PRE377: verify whether the Nitro guest C++ prologue exposes caller LR, read-only.

No APK, guest instrumentation, signer or save. Source pinned to PRE99 SHA.
A return-address field is not a car-owner identity.
"""
from pathlib import Path
import json,re,sys,tarfile,tempfile,hashlib
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS
OUT=Path("/tmp/nfsmw-pre377/PRE377_NITRO_LR_SOURCE_CANARY.json")
FUNCTION="sub_82424AF0"
PATTERNS={
"lr":re.compile(r"(?i)\b(?:ctx\.)?lr\b"),
"ctr":re.compile(r"(?i)\b(?:ctx\.)?ctr\b"),
"ctx_r3":re.compile(r"\bctx\.r3\b"),
"direct_indirect":re.compile(r"REX_CALL_(?:INDIRECT_)?FUNC\("),
}
def excerpt(lines,index,radius=4):
    return [{"line":j+1,"code":lines[j].strip()[:210]}
             for j in range(max(0,index-radius),min(len(lines),index+radius+1))]
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    out={"stage":"PRE377_NITRO_LR_PROLOGUE_READONLY","status":"FAILED",
         "owner_verified":False,"lr_is_owner":False,"apk_built":False,
         "game_modified":False}
    try:
        spec=TARGETS["nitro"]
        with tempfile.TemporaryDirectory(prefix="pre377_") as td:
            path=Path(td)/"pre99.tar.gz";download(drive_client(),path)
            digest,_,size=sha_file(path)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 SHA/size mismatch")
            with tarfile.open(path,"r:gz") as tf:
                member=tf.getmember(spec["file"])
                f=tf.extractfile(member)
                if f is None:raise ValueError("PAL shard unavailable")
                raw=f.read()
            if hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
                raise ValueError("Nitro PAL shard SHA mismatch")
            body=body_for_function(raw.decode("utf-8","replace"),FUNCTION)
            rows=body.splitlines()
            matches={}
            for key,pattern in PATTERNS.items():
                indices=[i for i,row in enumerate(rows) if pattern.search(row)]
                matches[key]={"total_hits":len(indices),
                   "first_24_relative_lines":[i+1 for i in indices[:24]],
                   "first_six_windows":[{"relative_line":i+1,"source":excerpt(rows,i)}
                                           for i in indices[:6]]}
            # Only a static lexical audit. Don't claim that LR is a stable callsite.
            out.update({"status":"AUDIT_OK","pre99_sha256":digest,
               "nitro_source_sha256":spec["sha256"],
               "nitro_body_lines":len(rows),"entry_first_70":[{"line":i+1,"code":row.strip()[:210]}
                                                            for i,row in enumerate(rows[:70])],
               "symbol_results":matches,
               "limitations":"Presence/absence of LR in generated body does not prove runtime return address semantics or player object ownership. No patches attempted."})
    except Exception as exc:out["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("PRE377_STATUS",out["status"])
    print("PRE377_LR_HITS",out.get("symbol_results",{}).get("lr",{}).get("total_hits"))
    print("PRE377_OWNER_VERIFIED",False)
    return 0 if out["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
