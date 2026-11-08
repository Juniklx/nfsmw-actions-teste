#!/usr/bin/env python3
"""PRE375: authenticated PAL read-only Nitro call/dataflow provenance study.
No APK, no save, no modification, no signing access; owner unknown by default.
"""
from pathlib import Path
import hashlib,json,re,sys,tarfile,tempfile
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS

OUT=Path("/tmp/nfsmw-pre375/PRE375_NITRO_CONTEXT_PROVENANCE.json")
PAT=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
TARGET="sub_82424AF0"
SYMBOL=re.compile(r"(?<![A-Za-z_0-9])sub_82424AF0(?![A-Za-z_0-9])",re.I)
HEX=re.compile(r"(?<![0-9a-f])(?:0x)?82424af0(?![0-9a-f])",re.I)
FIELD=re.compile(r"\br31\.(?:u32|u64|s32|s64)\s*\+\s*(252|296)\b")
REG=re.compile(r"\b(?:ctx\.r3|r31)\.(?:u32|u64|s32|s64)\b")
LOADSTORE=re.compile(r"REX_(?:LOAD|STORE)_U32\(")
OTHER_R3=re.compile(r"\bctx\.r3\b")
def cap(s,n=210):return s.strip()[:n]
def digest(x):return hashlib.sha256(x).hexdigest()
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE375_NITRO_CONTEXT_PROVENANCE_READONLY","status":"FAILED",
       "owner_verified":False,"player_pointer_verified":False,"cheat_enabled":False,
       "apk_built":False,"guest_modified":False,"signer_accessed":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre375_") as td:
            arc=Path(td)/"pre99.tar.gz";download(drive_client(),arc)
            sha,_,size=sha_file(arc)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 integrity mismatch")
            spec=TARGETS["nitro"]
            shards=0;target_source=None;references=[];total_refs=0
            with tarfile.open(arc,"r:gz") as tf:
                for member in tf:
                    name=member.name.lstrip("./")
                    if not member.isfile() or not PAT.fullmatch(name):continue
                    shards+=1
                    if member.size>8_000_000:raise ValueError("oversized PAL shard")
                    reader=tf.extractfile(member)
                    if reader is None:raise ValueError("missing member")
                    raw=reader.read()
                    if len(raw)!=member.size:raise ValueError("incomplete PAL shard")
                    if name==spec["file"]:
                        if digest(raw)!=spec["sha256"]:raise ValueError("Nitro source SHA mismatch")
                        target_source=raw.decode("utf-8","replace")
                    if b"82424AF0" not in raw and b"82424af0" not in raw:continue
                    for n,line in enumerate(raw.decode("utf-8","replace").splitlines(),1):
                        if SYMBOL.search(line) or HEX.search(line):
                            total_refs+=1
                            if len(references)<200:references.append({"shard":name,"line":n,"code":cap(line)})
            if shards!=129 or target_source is None:raise ValueError("PAL inventory/target missing")
            body=body_for_function(target_source,TARGET)
            rows=body.splitlines()
            blocks=[]
            for i,line in enumerate(rows):
                if FIELD.search(line):
                    lo=max(0,i-7);hi=min(len(rows),i+10)
                    blocks.append({"relative_line":i+1,"fields":FIELD.findall(line),
                      "code":cap(line),"context":[{"line":j+1,"code":cap(rows[j])} for j in range(lo,hi)]})
            r3lines=[{"line":i+1,"code":cap(row)} for i,row in enumerate(rows[:100]) if REG.search(row)]
            calls=[{"line":i+1,"code":cap(row)} for i,row in enumerate(rows) if
                   ("PPC_CALL" in row or "REX_CALL" in row or "call" in row.lower()) and len(row)<400]
            if len(blocks)<4:raise ValueError("Expected Nitro field events missing")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
              "pal_shards_scanned":shards,"nitro_shard":spec["file"],"nitro_shard_sha256":spec["sha256"],
              "target_function":TARGET,"target_body_lines":len(rows),
              "bounded_target_entry_register_lines":r3lines[:24],
              "bounded_field_windows":blocks[:25],
              "bounded_indirect_call_lines":calls[:50],
              "symbolic_reference_count":total_refs,
              "bounded_symbolic_references":references,
              "limits":{"reference_cap":200,"field_window_cap":25,"calls_cap":50},
              "interpretation":"Only static textual calls, field and register flows; does not prove which car is player or rule out virtual dispatch. Function definition itself appears as a reference.",
              "next_gate":"Derive a structural player-vehicle pointer independently from XInput and guest state, otherwise owner stays unknown; no Nitro guest-store rewrites."})
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE375_STATUS",result["status"])
    print("PRE375_SHARDS",result.get("pal_shards_scanned",0))
    print("PRE375_SYMBOL_REFERENCES",result.get("symbolic_reference_count",0))
    print("PRE375_OWNER_VERIFIED",False)
    print("PRE375_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
