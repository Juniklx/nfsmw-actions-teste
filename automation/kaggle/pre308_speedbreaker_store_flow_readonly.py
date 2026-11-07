#!/usr/bin/env python3
"""PRE308: inspect authenticated PAL PRE99 Speedbreaker store sites 7 and 8.
Read-only: hashes, bounded original guest control flow, callback alignment.
No game mutation, APK, signer, save or credential disclosure.
"""
from __future__ import annotations
import hashlib,json,sys,tarfile,tempfile,re
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS,FLOAT,HOST

OUT=Path("/tmp/nfsmw-pre308/PRE308_SPEEDBREAKER_CANDIDATE_7_8_CONTEXT.json")
def must(ok,what):
    if not ok:raise ValueError(what)
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(root):
    tarpath=root/"pre99.tar.gz"
    download(drive_client(),tarpath)
    dg,_,sz=sha_file(tarpath)
    must(dg==EXPECTED_SHA256 and sz==EXPECTED_BYTES,"PRE99 SHA/size mismatch")
    spec=TARGETS["speedbreaker"]
    with tarfile.open(tarpath,"r:gz") as tar:
        entry=next((m for m in tar if m.isfile() and m.name.lstrip("./")==spec["file"]),None)
        must(entry is not None and entry.size<7_000_000,"missing or oversized PAL shard")
        inp=tar.extractfile(entry)
        must(inp is not None,"PAL source unreadable")
        raw=inp.read()
    must(sha(raw)==spec["sha256"],"PINNED PAL shard SHA mismatch")
    body=body_for_function(raw.decode("utf8"),spec["function"])
    lines=body.splitlines()
    sites=[]
    for ix, line in enumerate(lines):
        x=FLOAT.match(line)
        if not x or int(x.group(1))!=132:continue
        tail=lines[ix+1:ix+5]
        must(len([y for y in tail if HOST.match(y)])==1,"generated host store missing")
        sites.append(ix)
    must(len(sites)==3,"Expected exactly three structural field-132 stores")
    # pre247 site enumeration maps speedbreaker sites to 6,7,8
    results=[]
    for j,ix in enumerate(sites):
        section=[]
        for p in range(max(0,ix-50),min(len(lines),ix+25)):
            t=lines[p].strip()
            if any(tag in t for tag in ("// lfs","// stfs","// fadds","// fsubs",
                     "// fcmp","// b","// lwz","// stw","REX_LOAD_",
                     "REX_STORE_","temp.f32","ctx.f","loc_","ctx.lr")):
                section.append({"rel_line":p+1,"text":t[:200]})
        results.append({"site":j+6,"relative_store_line":ix+1,
                        "matched_opcode":lines[ix].strip()[:120],
                        "context":section[-75:]})
    result={"stage":"PRE308_PRE99_PAL_SPEEDBREAKER_SITES_6_8",
      "status":"AUDIT_OK","source_file":spec["file"],
      "source_sha256":sha(raw),"function":spec["function"],
      "field_offset":132,"store_sites":results,
      "runtime_log_20261107":{
        "site7_records":24,"site8_records":24,"site6_records":0,
        "site7_values_f32_range":[1.000666618347168,1.0013333559036255],
        "site8_value_f32":1.0,
        "same_guest_address_for_7_8_in_both_sessions":True,
        "note":"Site numbers are candidates, not verified meter identity or consumption logic"},
      "safety":{"apk_built":False,"source_modified":False,"cheats_enabled":False,
                "guest_memory_read_added":False,"save_touched":False,"signer_accessed":False},
      "next":"map original branch and consumption events; only then trial opt-in speedbreaker value substitution"}
    return result
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"status":"FAILED","stage":"PRE308_PRE99_PAL_SPEEDBREAKER_SITES_6_8"}
    try:
        with tempfile.TemporaryDirectory(prefix="pre308_") as p:r=audit(Path(p))
    except Exception as e:r["error_type"]=type(e).__name__
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE308_STATUS",r["status"])
    print("PRE308_SOURCE_SHA",r.get("source_sha256"))
    print("PRE308_STORES",[(x["site"],x["relative_store_line"]) for x in r.get("store_sites",[])])
    print("PRE308_ERROR_TYPE",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
