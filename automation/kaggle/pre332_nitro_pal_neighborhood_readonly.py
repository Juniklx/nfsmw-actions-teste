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
            with tarfile.open(arc,"r:gz") as tf:
                member=next((m for m in tf if m.isfile() and m.name.lstrip("./")==spec["file"]),None)
                if member is None or member.size>8_000_000: raise ValueError("PAL CXX missing or oversized")
                raw=tf.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
                raise ValueError("PAL source SHA mismatch")
            info=inspect(raw.decode("utf-8",errors="replace"))
            if not info["nitro_present"]:raise ValueError("Nitro target function missing")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "source_sha256":spec["sha256"],**info,
                "meaning":"Only nearby symbols and structural counts. Address proximity does not establish class, vtable, player owner or caller."})
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE332_STATUS",result["status"])
    print("PRE332_METHODS_FOUND",result.get("methods_found",0))
    print("PRE332_OWNER_VERIFIED",result["owner_verified"])
    print("PRE332_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
