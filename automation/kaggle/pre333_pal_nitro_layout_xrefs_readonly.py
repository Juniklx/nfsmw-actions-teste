#!/usr/bin/env python3
"""PRE333: PRE99 PAL cross-function shared-offset signature candidates. Read-only.

Matches structural field-offset combinations in generated C++; results are not
proof of object type, vtable membership, player identity, or shared ownership.
"""
from pathlib import Path
import hashlib,json,re,sys,tarfile,tempfile
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import DEF
from pre242_pal_float_dataflow_readonly import TARGETS

OUT=Path("/tmp/nfsmw-pre333/PRE333_NITRO_LAYOUT_XREFS.json")
SHARD=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
OFFSET=re.compile(r"\b((?:ctx\.)?r\d+)\.(?:u32|u64|s32|s64)\s*\+\s*(52|72|88|252|296)\b")
TARGET="sub_82424AF0"
FIELDS={52,72,88,252,296}
LIMIT=90

def candidates(text:str,shard:str)->list[dict]:
    out=[]
    found=list(DEF.finditer(text))
    for k,m in enumerate(found):
        body=text[m.start():found[k+1].start() if k+1<len(found) else len(text)]
        bybase={}
        for line_no,line in enumerate(body.splitlines(),1):
            if line.lstrip().startswith("//"):
                continue
            for x in OFFSET.finditer(line):
                reg,offset=x.group(1),int(x.group(2))
                bybase.setdefault(reg,{}).setdefault(offset,[]).append(line_no)
        for reg,offsets in bybase.items():
            selected=set(offsets)
            if len(selected)<3 and not (252 in selected and len(selected)>=2):
                continue
            out.append({"function":m.group(1),"shard":shard,"register_base":reg,
                "offsets":sorted(selected),
                "sample_relative_lines":{str(k):v[:6] for k,v in sorted(offsets.items())},
                "score":len(selected),"has_nitro_field":252 in selected})
    return out

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE333_PAL_NITRO_LAYOUT_XREFS","status":"FAILED",
        "owner_verified":False,"apk_built":False,"guest_modified":False,
        "signer_accessed":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre333_") as td:
            archive=Path(td)/"pre99.tar.gz"
            download(drive_client(),archive)
            sha,_,n=sha_file(archive)
            if sha!=EXPECTED_SHA256 or n!=EXPECTED_BYTES:raise ValueError("PRE99 integrity mismatch")
            spec=TARGETS["nitro"]
            candidates_found=[];shards=0
            with tarfile.open(archive,mode="r:gz") as tar:
                for member in tar:
                    name=member.name.lstrip("./")
                    if not member.isfile() or not SHARD.fullmatch(name):continue
                    shards+=1
                    if member.size>8_000_000:raise ValueError("unexpected shard size")
                    stream=tar.extractfile(member)
                    if stream is None:raise ValueError("unreadable PAL source")
                    raw=stream.read()
                    if len(raw)!=member.size:raise ValueError("incomplete PAL member")
                    if name==spec["file"] and hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
                        raise ValueError("Nitro PAL source SHA mismatch")
                    candidates_found+=candidates(raw.decode("utf-8",errors="replace"),name)
            if shards<100:raise ValueError("incomplete PAL shard scan")
            candidates_found.sort(key=lambda x:(-x["score"],-int(x["has_nitro_field"]),x["function"],x["register_base"]))
            target=[v for v in candidates_found if v["function"]==TARGET]
            if not target:raise ValueError("Nitro function layout not detected")
            report.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "pal_shards_scanned":shards,
                "candidate_count":len(candidates_found),
                "candidate_functions":len(set(x["function"] for x in candidates_found)),
                "candidates_bounded":candidates_found[:LIMIT],
                "candidates_truncated":len(candidates_found)>LIMIT,
                "nitro_target_entries":target[:6],
                "limitations":"Numerical offsets and register names do not establish object class or player owner. Results cannot authorize guest writes."})
    except Exception as e:report["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE333_STATUS",report["status"])
    print("PRE333_PAL_SHARDS",report.get("pal_shards_scanned",0))
    print("PRE333_CANDIDATES",report.get("candidate_count",0))
    print("PRE333_TARGET_ENTRIES",len(report.get("nitro_target_entries",[])))
    print("PRE333_OWNER_VERIFIED",report["owner_verified"])
    print("PRE333_ERROR_TYPE",report.get("error_type"))
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
