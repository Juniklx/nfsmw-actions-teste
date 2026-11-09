#!/usr/bin/env python3
"""PRE548: original PAL guest pvehicle counter field and hash xrefs, READ ONLY.

Authenticate source TAR PRE99. The original PAL VPAK pvehicle class's
seven upgrade availability field offsets are 40,44,48,52,60,68,72 bytes
from its binary layout; they are NOT a proven installed-package record.

Look for generated PPC guest functions referencing five or more of these
offsets via the same memory base register, and separately detect PPC
lis + ori/addi pairs constructing EXACT class/name hashes. Publish
bounded numeric function xrefs only, not game/source bytes or patches.
Do not infer Physics::Upgrades::SetPackage, checkout, persistent state
or actual engine power from PPC address proximity / structural matches.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,selftest

OUT=Path("/tmp/nfsmw-pre548/report.json")
ROOT="workspace/nativo/app/generated/default/"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
COM=re.compile(r"^\s*//\s*([a-z][a-z0-9_.-]{0,18})(?:\s+(.+?))?\s*$",re.I)
MEM=re.compile(r"(?<!\w)([-+]?(?:0x[0-9a-fA-F]+|\d+))\((r\d+)\)",re.I)
REG=re.compile(r"^r\d+$",re.I)
FIELDS={
 "engine_upgrades":40,"transmission_upgrades":44,"nos_upgrades":48,
 "brakes_upgrades":52,"tires_upgrades":60,"induction_upgrades":68,
 "chassis_upgrades":72
}
FIELD_SET=set(FIELDS.values())
HASH_NAMES=(
 "pvehicle","engine","bmwm3gtr","m3gtre46careerstart",
 "engine_upgrades","transmission_upgrades","nos_upgrades",
 "brakes_upgrades","tires_upgrades","induction_upgrades",
 "chassis_upgrades","punto"
)
MAX_HITS_PER_HASH=30
MAX_FIELD_SAMPLES=40
MAX_FUNC_LINES=18000
MAX_SOURCE_BYTES=200_000_000
MEM_OPS={"lwz","stw","lhz","sth","lbz","stb","ld","std","lwzx","stwx"}
def parse_int(token):
    token=token.strip().lower()
    if token.startswith(("+0x","-0x","0x")):
        sign=-1 if token.startswith("-") else 1
        body=token.lstrip("+-")
        return sign*int(body,16)
    return int(token,10)
def one_function(name,body,target_values):
    # This pass intentionally uses generated PPC instruction comments,
    # not C++ generated statements nor inferred function names.
    samebase=defaultdict(lambda:defaultdict(Counter))
    matches=[]
    constructions=[]
    recent_lis={}
    comment_num=0
    for ix,line in enumerate(body.splitlines()):
        m=COM.match(line)
        if not m:continue
        op=m.group(1).lower()
        args=[x.strip().lower() for x in (m.group(2) or "").split(",")]
        comment_num+=1
        if op in MEM_OPS and len(args)>=2:
            mm=MEM.search(",".join(args[1:]))
            if mm:
                offset=parse_int(mm.group(1))
                reg=mm.group(2).lower()
                if offset in FIELD_SET and op in ("lwz","stw"):
                    samebase[reg][offset][op]+=1
        if op=="lis" and len(args)>=2 and REG.fullmatch(args[0]):
            try:hi=parse_int(args[1])
            except ValueError:continue
            if -32768<=hi<=65535:
                recent_lis[args[0]]=(comment_num,hi&0xffff)
        elif op in ("ori","addi") and len(args)>=3 and args[0]==args[1] and REG.fullmatch(args[0]):
            x=recent_lis.get(args[0])
            if x and 0<comment_num-x[0]<=5:
                try:lo=parse_int(args[2])
                except ValueError:continue
                if -32768<=lo<=65535:
                    val=(((x[1]<<16)|(lo&0xffff)) if op=="ori"
                         else ((x[1]<<16)+(lo if lo<32768 else lo-65536)))&0xffffffff
                    which=target_values.get(val)
                    if which is not None:
                        constructions.append({"guest_function":name,
                          "hash_preimage":which,"class_or_field_hash_hex":f"{val:08x}",
                          "guest_register":args[0],
                          "construction":"lis_then_"+op,
                          "approx_guest_PPC_comment_instruction_ordinal":comment_num,
                          "register_reaching_definition_unverified":True})
    for base,offsets in samebase.items():
        if len(offsets)<5:continue
        nloads=sum(v["lwz"] for v in offsets.values())
        nstores=sum(v["stw"] for v in offsets.values())
        matches.append({
          "numeric_guest_function":name,
          "PPC_base_register":base,
          "different_pvehicle_field_offsets":len(offsets),
          "covered_pvehicle_upgrade_field_offsets":sorted(offsets),
          "known_field_names_matched_on_layout_only":[key for key,off in FIELDS.items() if off in offsets],
          "total_PPC_lwz_in_matches":nloads,
          "total_PPC_stw_in_matches":nstores,
          "contains_PPC_store_to_any_matched_offset":nstores>0,
          "offsets_are_binary_VPAK_layout_not_proven_guest_runtime_layout":True
        })
    return matches,constructions,comment_num

def audit():
    p473=json.loads(Path("docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json").read_text())
    p547=json.loads(Path("docs/PRE547_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p526=json.loads(Path("docs/PRE526_PC_SHOP_CHECKOUT_PHYSICS_SAFETY_READONLY.json").read_text())
    if (p473.get("status")!="AUDIT_OK" or
        p473.get("pvehicle_class_hash")!="4a97ec8f" or
        p473.get("field_offsets")!=FIELDS or
        p473.get("vpak_sha256")!="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad" or
        p547.get("status")!="AUDIT_OK" or
        p547.get("new_total_bytes")!=827240 or
        p547.get("new_sha256")!="b36481f30c4923a4d7bb81c3173ea2b44451456134b2e809d78a4113a19768e2" or
        p526.get("status")!="AUDIT_OK" or
        p526.get("guest_V48_GetMaxLevel_or_SetPackage_behavior_verified") is not False or
        p526.get("PhysicsUpgrades_cpp_public_reference_body_bytes")!=0):
        raise ValueError("PRE473/526/547 asset layout or signed project status changed")
    selftest()
    targets={hash32(n):n for n in HASH_NAMES}
    if len(targets)!=len(HASH_NAMES) or targets.get(0x4a97ec8f)!="pvehicle":
        raise ValueError("Attribute VaultLib lookup2 hashing class pin inconsistent")
    fingerprints=[]
    hist=Counter()
    constants={name:{"matches_total":0,"samples":[]} for name in HASH_NAMES}
    total_shards=0;total_funcs=0;source_total=0;comments=0;stores=0
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre548_") as td:
        src=Path(td)/"pre99.tar.gz"
        download(drive_client(),src)
        digest,_,size=sha_file(src)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated historical PAL PRE99 TAR SHA256/size mismatch")
        with tarfile.open(src,"r:gz") as tf:
            for member in tf:
                leaf=member.name.lstrip("./")
                if not member.isfile() or not leaf.startswith(ROOT):continue
                name=leaf[len(ROOT):]
                if not re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",name):continue
                total_shards+=1
                if not 100<=member.size<=9_000_000:raise ValueError("Invalid original codegen shard size")
                source_total+=member.size
                if source_total>MAX_SOURCE_BYTES:raise ValueError("Too many original source bytes")
                file=tf.extractfile(member)
                if file is None:raise ValueError("Unreadable original source shard")
                data=file.read()
                if len(data)!=member.size:raise ValueError("Truncated original source shard")
                txt=data.decode("utf-8",errors="strict")
                defs=list(DEF.finditer(txt))
                if not defs:raise ValueError("Original generated source without function definitions")
                for i,m in enumerate(defs):
                    fn=m.group(1)
                    end=defs[i+1].start() if i+1<len(defs) else len(txt)
                    part=txt[m.start():end]
                    if len(part)>1_500_000:raise ValueError("Unexpected original single guest body size")
                    a,b,c=one_function(fn,part,targets)
                    total_funcs+=1;comments+=c
                    for item in a:
                        hist[item["different_pvehicle_field_offsets"]]+=1
                        if item["contains_PPC_store_to_any_matched_offset"]:stores+=1
                        if len(fingerprints)<MAX_FIELD_SAMPLES:fingerprints.append(item)
                    for hit in b:
                        sub=constants[hit["hash_preimage"]]
                        sub["matches_total"]+=1
                        if len(sub["samples"])<MAX_HITS_PER_HASH:
                            hit["original_guest_codegen_shard"]=name
                            sub["samples"].append(hit)
    if total_shards!=129 or total_funcs!=56338:
        raise ValueError("Historical original PAL generated source corpus changed")
    return {
      "stage":"PRE548_ORIGINAL_PAL_GUEST_PVEHICLE_COUNTER_FIELD_HASH_STATE_WRITER_SCREEN_READONLY",
      "status":"AUDIT_OK",
      "PRE99_archive_sha256":EXPECTED_SHA256,
      "original_guest_shards_scanned":total_shards,
      "original_guest_functions_scanned":total_funcs,
      "original_guest_source_bytes_scanned":source_total,
      "source_PPC_instruction_comments_examined":comments,
      "verified_original_pal_vpak_pvehicle_class_hash":"4a97ec8f",
      "verified_pvehicle_binary_vpak_upgrade_field_offsets":FIELDS,
      "searched_lookup2_hashes":{n:f"{hash32(n):08x}" for n in HASH_NAMES},
      "guest_PPC_lis_then_ori_or_addi_hash_candidate_counts":constants,
      "guest_same_base_five_or_more_counter_offsets_match_count":sum(hist.values()),
      "guest_same_base_five_or_more_offsets_with_lwz_or_stw_store_count":stores,
      "candidate_same_base_counter_offset_match_histogram":dict(hist),
      "bounded_guest_numeric_offset_fingerprint_candidates":fingerprints,
      "PPC_lis_ori_short_window_does_not_exclude_other_hash_loading_methods":True,
      "PPC_same_base_offsets_not_proven_VLT_runtime_pvehicle_object":True,
      "counter_fields_are_UPGRADE_AVAILABILITY_not_installed_package":True,
      "guest_PhysicsUpgrades_SetPackage_address_identified":False,
      "game_guest_checkout_package_persistence_proven":False,
      "guest_motor_collection_load_accepted":False,
      "game_data_or_guest_code_modified_or_published":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,"BMW_tuning_enabled":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE548_ORIGINAL_PAL_GUEST_PVEHICLE_COUNTER_FIELD_HASH_STATE_WRITER_SCREEN_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
           "game_data_or_guest_code_modified_or_published":False,
           "APK_built":False,"save_modified":False,
           "signing_material_accessed":False,"BMW_tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE548_STATUS",r["status"])
    print("PRE548_FIELD_FINGERPRINTS",r.get("guest_same_base_five_or_more_counter_offsets_match_count"))
    print("PRE548_HIT_HASHES",[(k,v["matches_total"]) for k,v in r.get("guest_PPC_lis_then_ori_or_addi_hash_candidate_counts",{}).items()])
    print("PRE548_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
