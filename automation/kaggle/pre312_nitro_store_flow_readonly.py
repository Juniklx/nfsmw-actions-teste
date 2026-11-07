#!/usr/bin/env python3
"""PRE312: inspect authenticated PAL PRE99 Nitro store sites 7 and 8.
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

OUT=Path("/tmp/nfsmw-pre312/PRE312_NITRO_SITES_1_5_CONTEXT.json")
def must(ok,what):
    if not ok:raise ValueError(what)
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(root):
    tarpath=root/"pre99.tar.gz"
    download(drive_client(),tarpath)
    dg,_,sz=sha_file(tarpath)
    must(dg==EXPECTED_SHA256 and sz==EXPECTED_BYTES,"PRE99 SHA/size mismatch")
    spec=TARGETS["nitro"]
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
        if not x or int(x.group(1))!=252:continue
        tail=lines[ix+1:ix+5]
        must(len([y for y in tail if HOST.match(y)])==1,"generated host store missing")
        sites.append(ix)
    must(len(sites)==5,"Expected exactly five structural field-252 stores")
    # PRE247 maps Nitro candidate sites to 1,2,3,4,5
    results=[]
    for j,ix in enumerate(sites):
        section=[]
        for p in range(max(0,ix-50),min(len(lines),ix+25)):
            t=lines[p].strip()
            if any(tag in t for tag in ("// lfs","// stfs","// fadds","// fsubs",
                     "// fcmp","// b","// lwz","// stw","REX_LOAD_",
                     "REX_STORE_","temp.f32","ctx.f","loc_","ctx.lr")):
                section.append({"rel_line":p+1,"text":t[:200]})
        results.append({"site":j+1,"relative_store_line":ix+1,
                        "matched_opcode":lines[ix].strip()[:120],
                        "context":section[-75:]})
    result={"stage":"PRE312_PRE99_PAL_NITRO_SITES_1_5",
      "status":"AUDIT_OK","source_file":spec["file"],
      "source_sha256":sha(raw),"function":spec["function"],
      "field_offset":252,"store_sites":results,
      "runtime_log_20261107":{
        "site1_records":12,"site2_records":12,"site3_records":12,"site4_records":12,"site5_records":0,
        "site1_2_values_f32_range":[0.9200000762939453,0.9933333396911621],
        "site3_4_values_f32_range":[0.3470035791397095,0.3507603406906128],
        "same_guest_address_for_1_2_3_4_in_latest_session":True,
        "note":"Site numbers are structural candidates; runtime button state not directly logged"},
      "safety":{"apk_built":False,"source_modified":False,"cheats_enabled":False,
                "guest_memory_read_added":False,"save_touched":False,"signer_accessed":False},
      "next":"Map which Nitro store is authoritative in depletion/regen before enabling gated substitution"}
    return result
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"status":"FAILED","stage":"PRE312_PRE99_PAL_NITRO_SITES_1_5"}
    try:
        with tempfile.TemporaryDirectory(prefix="pre312_") as p:r=audit(Path(p))
    except Exception as e:r["error_type"]=type(e).__name__
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE312_STATUS",r["status"])
    print("PRE312_SOURCE_SHA",r.get("source_sha256"))
    print("PRE312_STORES",[(x["site"],x["relative_store_line"]) for x in r.get("store_sites",[])])
    print("PRE312_ERROR_TYPE",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
