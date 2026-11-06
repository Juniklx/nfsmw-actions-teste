#!/usr/bin/env python3
"""PRE245: in-memory money candidate guard integration dry run (PAL only).

Never writes generated game files. No apk / signer / saves; disabled by default
runtime bridge is only a specification until CMake and CVAR validation.
"""
from __future__ import annotations
import hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import TARGETS,body_for_function,COMMENT,STORE
from pre240_pal_money_old_value_readonly import OLD,EXPECTED_HASHES
OUT=Path("/tmp/nfsmw-pre245/NFSMW_PRE245_PAL_MONEY_GUARD_DRYRUN.json")
DECLARATION='extern "C" uint32_t NFSMW_CheatMoneyGuard(uint32_t previous, uint32_t proposed) noexcept;'
CALL='NFSMW_CheatMoneyGuard'
def validate_and_rewrite(src,target,spec):
    body=body_for_function(src,target)
    lines=body.splitlines(keepends=True)
    hits=[]
    for i,line in enumerate(lines):
        m=COMMENT.match(line)
        if m and i+1<len(lines) and STORE.match(lines[i+1]):
            hits.append((i,m.group(1).replace(" ",""),STORE.match(lines[i+1])))
    if len(hits)!=len(spec["stores"]):raise ValueError("Expected exact stores missing")
    rewrites=[]
    edits={}
    for ordinal,((idx,comment,store),(expected_mnemonic,exp_addr,exp_new),old_reg) in enumerate(zip(hits,spec["stores"],OLD[target]),1):
        addr=store.group(1).strip()
        value=store.group(2).strip()
        if (comment.lower(),addr,value)!=(expected_mnemonic.lower(),exp_addr,exp_new):
            raise ValueError("Unexpected original store or order")
        # The previous value register is read by the original guest code (PRE240).
        previous=f"ctx.{old_reg}.u32"
        # Some register names are mapped as local variables in C++.
        # Exact field accesses are verified by PRE240 and all such old regs are ctx here.
        injected=f"REX_STORE_U32({addr}, {CALL}({previous}, {value}));"
        prefix=re.match(r"^(\s*)",lines[idx+1]).group(1)
        edits[idx+1]=prefix+injected+"\n"
        rewrites.append({"ordinal":ordinal,
             "pc_candidate":spec["guest_pc_candidates_from_PRE237"][ordinal-1],
             "old_guest_register":old_reg,
             "original":lines[idx+1].strip(),
             "replacement":injected,
             "new_guest_loads":0,
             "rollback":lines[idx+1].strip()})
    transformed="".join(edits.get(i,line) for i,line in enumerate(lines))
    if transformed.count("REX_STORE_U32(")!=body.count("REX_STORE_U32("):
        raise ValueError("Unexpected store count after transform")
    if transformed.count(CALL+"(")!=len(rewrites):
        raise ValueError("Guard calls count mismatch")
    if "REX_LOAD_U32(" not in body or transformed.count("REX_LOAD_U32(")!=body.count("REX_LOAD_U32("):
        raise ValueError("Original loads modified")
    if len(rewrites)!=len(spec["stores"]):
        raise ValueError("Missing patch")
    if transformed==body:
        raise ValueError("Empty dry-run")
    return {"function":target,"sites":rewrites,
            "transformed_function_sha256":hashlib.sha256(transformed.encode("utf-8")).hexdigest(),
            "source_file_unmodified":True,
            "generated_cpp_only_in_memory":True,
            "all_original_loads_preserved":True,
            "original_stores_count_preserved":True}
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 r={"stage":"PRE245_PAL_MONEY_GUARD_IN_MEMORY_DRYRUN","status":"FAILED","phase":"START",
    "apk_built":False,"source_files_modified":False,"generated_files_written":False,
    "save_files_touched":False,"signer_accessed":False,
    "cheat_enabled":False,"game_executed":False}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre245_") as td:
   r["phase"]="VERIFY_PRE99"
   p=Path(td)/"pre99.tar.gz"
   download(drive_client(),p)
   sha,_,size=sha_file(p)
   if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 fingerprint changed")
   r["pre99_verified"]=True
   r["phase"]="READ_SHA_PINNED_PAL_GENERATED"
   required={x["filename"] for x in TARGETS.values()}
   sources={}
   with tarfile.open(p,"r:gz") as tf:
    for m in tf:
     name=m.name.lstrip("./")
     if not m.isfile() or name not in required:continue
     if m.size>3_000_000:raise ValueError("Unexpected source size")
     stream=tf.extractfile(m)
     if stream is None:raise ValueError("Missing tar member")
     data=stream.read()
     if hashlib.sha256(data).hexdigest()!=EXPECTED_HASHES[name]:
         raise ValueError("Unexpected source fingerprint")
     sources[name]=data.decode("utf-8","replace")
   if len(sources)!=len(required):raise ValueError("Missing PAL codegen shard")
   r["phase"]="VALIDATE_DRYRUN"
   r["proposed_bridge_declaration"]=DECLARATION
   r["bridge_behavior"]="default false CVAR; passthrough proposed when disabled, uint32 max(old, proposed) when enabled"
   r["functions"]=[]
   for name,spec in TARGETS.items():
    r["functions"].append(validate_and_rewrite(sources[spec["filename"]],name,spec))
   r["guarded_stores"]=sum(len(v["sites"]) for v in r["functions"])
   r["critical_limits"]=[
      "The guard function is not yet defined or linked into the real game.",
      "This proposal modifies only in-memory text; generated CPP/source files are not persisted.",
      "The CVAR and module include/CMake wiring require a separate actual build preflight.",
      "Blocking money debit stores may affect in-game purchase semantics; gameplay and saves untested.",
      "No patch is applied to Nitro, Speedbreaker or USA by this stage.",
   ]
   r["phase"]="COMPLETE"
   r["status"]="AUDIT_OK" if r["guarded_stores"]==8 else "INCOMPLETE"
 except Exception as e:
  r["exception_type"]=type(e).__name__
  r["failed_phase"]=r["phase"]
  print("PRE245_ERROR",type(e).__name__,r["phase"])
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PRE245_STATUS",r["status"],"GUARDED",r.get("guarded_stores",0))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
