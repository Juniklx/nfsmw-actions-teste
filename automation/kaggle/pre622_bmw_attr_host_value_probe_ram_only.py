#!/usr/bin/env python3
"""PRE622: RAM-only reversible preview of passive original PAL attribute-value
telemetry at existing REX_LOAD_U32 return site, selected by original caller LR.
No new guest calls, loads/stores, no APK/game/save writes and no callback linked.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre622/report.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.28.cpp"
EXPECTED_SHARD_SHA="11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad"
FNAME="sub_823E5988"
FLAG="NFSMW_PRE622_ATTR_VALUE_ENABLE"
SYMBOL="NFSMW_PRE622_ATTR_VALUE"
DECL='\nextern "C" void '+SYMBOL+'(unsigned,unsigned,unsigned,int) noexcept;\n'
LOCAL=("#if defined("+FLAG+") && "+FLAG+"\n"
"\tconst unsigned pre622_return_to = static_cast<unsigned>(ctx.lr);\n"
"\tconst unsigned pre622_original_type = ctx.r4.u32;\n"
"#endif\n")
TRACE=("#if defined("+FLAG+") && "+FLAG+"\n"
"\tif (pre622_return_to == 0x8256F83Cu && pre622_original_type <= 6u) {\n"
"\t\t"+SYMBOL+"(pre622_return_to,pre622_original_type,ctx.r11.u32,ctx.r3.s32);\n"
"\t}\n"
"#endif\n")
OPS=("REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
     "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64(",
     "__imp__sub_","REX_CALL_INDIRECT_FUNC(")
def sha(b):return hashlib.sha256(b).hexdigest()
def preview(raw):
    if sha(raw)!=EXPECTED_SHARD_SHA:raise ValueError("Expected original PAL code shard changed")
    original=raw.decode("utf-8")
    if FLAG in original or SYMBOL in original:raise ValueError("Source already instrumented")
    body=body_for_function(original,FNAME)
    lines=body.splitlines(keepends=True)
    if len(lines)!=155:raise ValueError("Original lookup size unexpected")
    anchor="ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);"
    idx=[i for i,l in enumerate(lines) if anchor in l]
    local=[i for i,l in enumerate(lines) if l.strip()=="uint32_t ea{};"]
    returns=[i+1 for i,l in enumerate(lines) if l.strip()=="return;"]
    if idx!=[103] or len(local)!=1 or returns!=[60,126,153]:
      raise ValueError("Critical resolved return load or original exit path shifted")
    output=[]
    for i,line in enumerate(lines):
      if i==local[0]:output.append(LOCAL)
      output.append(line)
      if i==idx[0]:output.append(TRACE)
    patched="".join(output)
    if patched.count(SYMBOL+"(")!=1:
      raise ValueError("Expected one callback host instrumentation")
    staged=original.replace(body,patched,1)
    m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9a-fA-F]{8}\)",staged)
    if not m:raise ValueError("Declaration anchor missing")
    staged=staged[:m.start()]+DECL+staged[m.start():]
    for op in OPS:
      if staged.count(op)!=original.count(op):
        raise ValueError("Guest memory/indirect call opcode count differs: "+op)
    reverted=staged.replace(DECL,"",1).replace(patched,body,1)
    if reverted!=original:raise ValueError("RAM preview not perfectly reversible")
    return {
      "original_shard_sha256":sha(raw),
      "RAM_preview_sha256":sha(staged.encode("utf-8")),
      "function":FNAME,
      "guest_return_reasons_PRE447":[1,2,3],
      "source_guest_attribute_read_relative_line":104,
      "guest_attribute_value_read_original_opcode":"REX_LOAD_U32(ctx.r11.u32 + 0)",
      "recorded_host_fields":["original_caller_lr","original_type_0_to_6","value_address_ctx_r11","already_resolved_value_ctx_r3"],
      "host_original_caller_lr":"0x8256F83C",
      "host_callback_enabled_by_default":False,
      "host_callback_compiled":False,
      "new_guest_memory_reads":0,"new_guest_memory_writes":0,
      "new_guest_calls":0,
      "original_PPC_guest_instruction_order_preserved":True,
      "source_reverted_bit_for_bit":True,
      "guest_callback_only_original_normal_lookup":True,
      "direct_attribution_of_zero_to_new_BMW_collection_proven":False,
      "guest_value_runtime_traced":False
    }
def audit():
  prior=json.loads(Path("docs/PRE621_BMW_GUEST_ATTR_LOOKUP_REGISTERS_READONLY.json").read_text())
  p620=Path("docs/PRE620_HANDOFF_USER_VERIFIED_PRE607_ACTIVE_HASH_BMW_CATEGORY_ZERO_20261109.md").read_text(encoding="utf-8")
  if (prior.get("status")!="AUDIT_OK" or
      prior.get("private_original_pre99_sha256")!=EXPECTED_SHA256 or
      prior.get("pinned_functions",{}).get("lookup",{}).get("attribute_value_return_relative_lines")!=[104] or
      prior.get("attribute_descriptor_semantic_identity_proven") is not False or
      "PRE607_CONFIRMED_BY_USER_SHA256" not in p620):
    raise ValueError("PRE621 code and PRE620 actual phone hash proof missing")
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre622_") as tmp:
    archive=Path(tmp)/"pre99.tar.gz"
    download(drive_client(),archive)
    dig,_,size=sha_file(archive)
    if (dig,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("Original PRE99 archive provenance changed")
    with tarfile.open(archive,"r:gz") as tar:
      members=[x for x in tar if x.name.lstrip("./")==SOURCE]
      if len(members)!=1 or not members[0].isfile() or members[0].size>7_000_000:
        raise ValueError("Expected private original generated source member not unique")
      raw=tar.extractfile(members[0]).read()
      meta=preview(raw)
  return {"stage":"PRE622_ORIGINAL_BMW_ATTR_VALUE_HOST_PROBE_RAM_PREVIEW","status":"AUDIT_OK",
      "source_original_PRE99_sha256":EXPECTED_SHA256,**meta,
      "preview_stored_in_memory_only":True,
      "no_new_APK_build":True,"phone_game_data_modified":False,
      "save_modified":False,"signing_accessed":False,"callback_not_linked":True,
      "pending_runtime_validation":True}
def main():
  p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:r=audit()
  except Exception as e:r={"stage":"PRE622_ORIGINAL_BMW_ATTR_VALUE_HOST_PROBE_RAM_PREVIEW",
       "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
       "no_new_APK_build":True,"phone_game_data_modified":False,
       "save_modified":False,"signing_accessed":False,"callback_not_linked":True}
  r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
  OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
  print("PRE622_STATUS",r["status"])
  print("PRE622_ERROR",r.get("error_type","none"),r.get("error",""))
  return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
