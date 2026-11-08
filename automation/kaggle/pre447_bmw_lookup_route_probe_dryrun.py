#!/usr/bin/env python3
"""PRE447: in-memory, default-OFF preview of PPC zero-return route telemetry.
NO APK, guest execution, saves, credentials or persistent source writes.
"""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre447/report.json")
ROOT="workspace/nativo/app/generated/default/"
FILES={
 "lookup":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818")
}
FLAG="NFSMW_PRE447_LOOKUP_ROUTE_ENABLE"
NAME="NFSMW_PRE447_ROUTE"
DECL='\nextern "C" void NFSMW_PRE447_ROUTE(unsigned, unsigned, unsigned, int) noexcept;\n'
LOCAL=("#if defined("+FLAG+") && "+FLAG+"\n"
 "\tconst unsigned pre447_return_to = static_cast<unsigned>(ctx.lr);\n"
 "\tconst unsigned pre447_original_type = ctx.r4.u32;\n"
 "#endif\n")
OPS=("REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(",
     "REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64(",
     "__imp__sub_","REX_CALL_INDIRECT_FUNC(")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def trace(n):
 return ("#if defined("+FLAG+") && "+FLAG+"\n"
  "\tif (pre447_return_to == 0x8256F83Cu && pre447_original_type <= 6u) {\n"
  "\t\tNFSMW_PRE447_ROUTE(pre447_return_to,pre447_original_type,"+str(n)+"u,ctx.r3.s32);\n"
  "\t}\n#endif\n")
def preview(raw,other):
 if sha(raw)!=FILES["lookup"][1] or sha(other)!=FILES["builder"][1]:
  raise ValueError("PRE99 source fingerprint mismatch")
 b=body_for_function(other.decode(),FILES["builder"][2]).splitlines()
 calls=[i for i,l in enumerate(b) if "__imp__sub_823E5988(ctx, base);" in l]
 if len(calls)!=2 or not any("ctx.lr = 0x8256F83C;" in line for line in b[calls[0]-2:calls[0]]):
  raise ValueError("No unique first-call return-address proof")
 original=raw.decode()
 if FLAG in original or NAME in original:raise ValueError("Already instrumented")
 body=body_for_function(original,FILES["lookup"][2])
 lines=body.splitlines(keepends=True)
 exits=[i+1 for i,l in enumerate(lines) if l.strip()=="return;"]
 if exits!=[60,126,153]:raise ValueError("PPC return locations changed")
 if sum(l.strip()=="uint32_t ea{};" for l in lines)!=1:
  raise ValueError("Local variable placement unexpected")
 expanded=[]
 for i,l in enumerate(lines,1):
  if l.strip()=="uint32_t ea{};":expanded.append(LOCAL)
  if i in exits:expanded.append(trace(exits.index(i)+1))
  expanded.append(l)
 changed="".join(expanded)
 if changed.count("NFSMW_PRE447_ROUTE(")!=3:raise ValueError("Route hooks incomplete")
 staged=original.replace(body,changed,1)
 m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9a-fA-F]{8}\)",staged)
 if not m:raise ValueError("Missing declaration anchor")
 staged=staged[:m.start()]+DECL+staged[m.start():]
 for op in OPS:
  if staged.count(op)!=original.count(op):raise ValueError("Guest memory opcode/call count delta: "+op)
 if staged.replace(DECL,"",1).replace(changed,body,1)!=original:
  raise ValueError("Preview not reversible byte for byte")
 return {"original_sha256":sha(raw),"preview_sha256":sha(staged.encode()),
  "routes":{"1":"no_category_descriptor","2":"resolved_value_may_be_zero_or_positive",
            "3":"fallback_zero_multiple_causes"},
  "original_return_lines":exits,"only_first_helper_call":True,
  "original_caller_lr":"0x8256F83C","flag":FLAG,
  "enabled_by_default":False,"additional_guest_calls":0,
  "additional_guest_loads":0,"additional_guest_stores":0,
  "reversible":True,"callbacks_compiled_or_executed":False}
def audit():
 with tempfile.TemporaryDirectory(prefix="pre447_") as d:
  tarpath=Path(d)/"pre99.tar.gz";download(drive_client(),tarpath)
  digest,_,size=sha_file(tarpath)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 backup mismatch")
  sources={}
  names={ROOT+x[0]:k for k,x in FILES.items()}
  with tarfile.open(tarpath,"r:gz") as tar:
   for m in tar:
    name=m.name.lstrip("./")
    if name not in names:continue
    if not m.isfile() or m.size>7000000:raise ValueError("Invalid generated source")
    f=tar.extractfile(m)
    if f is None:raise ValueError("Unavailable guest source")
    sources[names[name]]=f.read()
  if set(sources)!=set(FILES):raise ValueError("Required guest shards missing")
  result=preview(sources["lookup"],sources["builder"])
  return {"status":"AUDIT_OK","stage":"PRE447_BMW_LOOKUP_ROUTE_DRYRUN_OFF",
   "pre99_sha256":digest,"preview":result,
   "bmw_zero_route_identified_in_runtime":False,
   "apk_built":False,"save_modified":False,"sources_modified_on_disk":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:200]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE447_STATUS",r["status"],"ERROR",r.get("error","none"))
 print("PRE447_PREVIEW",r.get("preview"))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
