#!/usr/bin/env python3
"""PRE332: inspect PAL Nitro function neighborhood in authenticated PRE99, read only."""
from pathlib import Path
import hashlib,json,tarfile,tempfile,re,sys
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS

OUT=Path("/tmp/nfsmw-pre332/PRE332_NITRO_NEIGHBORHOOD.json")
NEIGHBORS=(
 "sub_82424820","sub_82424940","sub_824249E0",
 "sub_82424AF0","sub_82424E58","sub_82425078","sub_82425100",
)
COMMENT_RE=re.compile(r"^\s*//\s*([A-Za-z0-9_.]+)")
OFFSET_RE=re.compile(r"\b(?:252|0xFC)\b",re.I)
DISPATCH_RE=re.compile(r"REX_CALL_INDIRECT_FUNC|\b(?:mtctr|bctrl)\b",re.I)
CALL_RE=re.compile(r"\bREX_CALL(?:_INDIRECT)?_FUNC\b")
R3_RE=re.compile(r"\b(?:ctx\.r3|r3\.[usf]\d+)\b")
LOAD_RE=re.compile(r"REX_LOAD_")
STORE_RE=re.compile(r"REX_STORE_")
def inspect(text:str)->dict:
    result=[]
    for function in NEIGHBORS:
        try:
            lines=body_for_function(text,function).splitlines()
        except ValueError:
            result.append({"symbol":function,"present":False})
            continue
        comments=[m.group(1) for line in lines if (m:=COMMENT_RE.match(line))]
        r3=[i+1 for i,line in enumerate(lines) if R3_RE.search(line)]
        offsets=[i+1 for i,line in enumerate(lines) if OFFSET_RE.search(line)]
        indirect=[i+1 for i,line in enumerate(lines) if DISPATCH_RE.search(line)]
        result.append({"symbol":function,"present":True,"lines":len(lines),
            "r3_mentions":len(r3),"r3_lines_first":r3[:10],
            "offset_252_mentions":len(offsets),"offset_252_lines_first":offsets[:16],
            "indirect_dispatch_mentions":len(indirect),"indirect_lines_first":indirect[:12],
            "load_count":sum(bool(LOAD_RE.search(l)) for l in lines),
            "store_count":sum(bool(STORE_RE.search(l)) for l in lines),
            "ppc_comment_mnemonics_first":comments[:20]})
    return {"methods":result,"methods_found":sum(x["present"] for x in result),
      "nitro_present":next(x["present"] for x in result if x["symbol"]=="sub_82424AF0")}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE332_PAL_NITRO_NEIGHBORHOOD","status":"FAILED",
      "owner_verified":False,"apk_built":False,"guest_modified":False,"signer_accessed":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre332_") as td:
            arc=Path(td)/"pre99.tar.gz"
            download(drive_client(),arc)
            sha,_,size=sha_file(arc)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 mismatch")
            spec=TARGETS["nitro"]
            matched={}
            scanned=0
            shard_name=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
            with tarfile.open(arc,"r:gz") as tf:
                for member in tf:
                    name=member.name.lstrip("./")
                    if not member.isfile() or not shard_name.fullmatch(name):
                        continue
                    scanned+=1
                    if member.size>8_000_000:
                        raise ValueError("unexpected PAL shard size")
                    fp=tf.extractfile(member)
                    if fp is None: raise ValueError("unreadable PAL shard")
                    raw=fp.read()
                    if len(raw)!=member.size:raise ValueError("incomplete PAL shard")
                    if name==spec["file"] and hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
                        raise ValueError("original Nitro PAL source SHA mismatch")
                    if not any(n.encode() in raw for n in NEIGHBORS):
                        continue
                    decoded=raw.decode("utf-8",errors="replace")
                    detail=inspect(decoded)
                    for method in detail["methods"]:
                        if not method["present"]:continue
                        symbol=method["symbol"]
                        if symbol in matched:raise ValueError("duplicate PAL function definition")
                        matched[symbol]={**method,"shard":name}
            if scanned<100:raise ValueError("incomplete PAL shard search")
            if "sub_82424AF0" not in matched:raise ValueError("Nitro function missing")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "original_nitro_source_sha256":spec["sha256"],
                "pal_shards_scanned":scanned,"methods_found":len(matched),
                "nitro_present":True,"methods":[matched[n] if n in matched else
                   {"symbol":n,"present":False} for n in NEIGHBORS],
                "meaning":"Across all PAL shards, code-address neighbors are not automatically same class or vtable. Owner unproven."})
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE332_STATUS",result["status"])
    print("PRE332_PAL_SHARDS",result.get("pal_shards_scanned",0))
    print("PRE332_METHODS_FOUND",result.get("methods_found",0))
    print("PRE332_OWNER_VERIFIED",result["owner_verified"])
    print("PRE332_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
