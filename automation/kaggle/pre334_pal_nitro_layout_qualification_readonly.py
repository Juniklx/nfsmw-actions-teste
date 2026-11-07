#!/usr/bin/env python3
"""PRE334: qualify six five-offset PAL Nitro-layout candidates, read-only.

Strong signatures are structural only; never equate them with player ownership.
"""
from pathlib import Path
import hashlib,json,re,sys,tarfile,tempfile
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function,DEF
from pre242_pal_float_dataflow_readonly import TARGETS

OUT=Path("/tmp/nfsmw-pre334/PRE334_NITRO_LAYOUT_QUALIFICATION.json")
SHARD=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
TARGETS_TO_QUALIFY={
 "sub_822040B0":"ctx.r11",
 "sub_82424AF0":"r31",
 "sub_825904F0":"r31",
 "sub_8270BF50":"r31",
 "sub_82719CB0":"r31",
 "sub_828A61D8":"r31",
}

def qualify(src:str,symbol:str,base:str)->dict:
    lines=body_for_function(src,symbol).splitlines()
    b=re.escape(base)
    addr=lambda offset: b+r"\.(?:u32|u64|s32|s64)\s*\+\s*"+str(offset)+r"\b"
    load252=re.compile(r"REX_LOAD_U32\(\s*"+addr(252))
    store252=re.compile(r"REX_STORE_U32\(\s*"+addr(252))
    load296=re.compile(r"REX_LOAD_U32\(\s*"+addr(296))
    direct_r3=re.compile(r"^\s*"+b+r"\.(?:u64|u32)\s*=\s*ctx\.r3\.(?:u64|u32)\s*;")
    def hits(rx):return [i+1 for i,l in enumerate(lines) if rx.search(l)]
    loads=hits(load252);stores=hits(store252);pointer=hits(load296);r3=hits(direct_r3)
    # A register assignment to r3 anywhere within a long function does not prove
    # persistent aliasing; report only matches within the function's first 90 lines.
    entry=[n for n in r3 if n<=90]
    return {"function":symbol,"register_base":base,"line_count":len(lines),
        "base_from_r3_near_entry":bool(entry),
        "base_from_r3_lines":entry[:6],
        "load_252_count":len(loads),"load_252_lines":loads[:12],
        "store_252_count":len(stores),"store_252_lines":stores[:12],
        "load_296_count":len(pointer),"load_296_lines":pointer[:12],
        "shape_matches_nitro":bool(entry and loads and stores and pointer),
        "owner_verified":False}

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE334_NITRO_LAYOUT_QUALIFICATION","status":"FAILED",
      "owner_verified":False,"apk_built":False,"guest_modified":False,"signer_accessed":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre334_") as td:
            arc=Path(td)/"pre99.tar.gz"
            download(drive_client(),arc)
            sha,_,size=sha_file(arc)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
            spec=TARGETS["nitro"]
            found={};shards=0
            with tarfile.open(arc,mode="r:gz") as tf:
                for member in tf:
                    name=member.name.lstrip("./")
                    if not member.isfile() or not SHARD.fullmatch(name):continue
                    shards+=1
                    if member.size>8_000_000:raise ValueError("unexpected PAL source size")
                    stream=tf.extractfile(member)
                    if stream is None:raise ValueError("missing PAL stream")
                    raw=stream.read()
                    if len(raw)!=member.size:raise ValueError("partial PAL shard")
                    if name==spec["file"] and hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
                        raise ValueError("Nitro source SHA mismatch")
                    if not any(sym.encode() in raw for sym in TARGETS_TO_QUALIFY):continue
                    src=raw.decode("utf8",errors="replace")
                    names={m.group(1) for m in DEF.finditer(src)}
                    for sym,base in TARGETS_TO_QUALIFY.items():
                        if sym not in names:continue
                        if sym in found:raise ValueError("duplicate function")
                        found[sym]={**qualify(src,sym,base),"shard":name}
            if shards<100 or len(found)!=len(TARGETS_TO_QUALIFY):
                raise ValueError("incomplete PAL qualified targets")
            if not found["sub_82424AF0"]["shape_matches_nitro"]:
                raise ValueError("reference Nitro fingerprint not matched")
            ordered=[found[x] for x in TARGETS_TO_QUALIFY]
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "pal_shards_scanned":shards,"functions_qualified":len(found),
                "nitro_shaped_candidates":sum(x["shape_matches_nitro"] for x in ordered),
                "functions":ordered,
                "limitation":"Syntax pattern is a candidate classifier, not proof of same object type, player owner or authority to modify guest memory."})
    except Exception as e:result["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE334_STATUS",result["status"])
    print("PRE334_FUNCTIONS",result.get("functions_qualified",0))
    print("PRE334_NITRO_SHAPED",result.get("nitro_shaped_candidates",0))
    print("PRE334_OWNER_VERIFIED",result["owner_verified"])
    print("PRE334_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
