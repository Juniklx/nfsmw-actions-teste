#!/usr/bin/env python3
"""PRE324: authenticated PRE99 PAL caller/xref of Nitro routine.
Read-only, no APK, patch, save, signing.
"""
from pathlib import Path
import tarfile,tempfile,re,json,sys,hashlib
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre324/NFSMW_PRE324_NITRO_CALLERS.json")
CXX=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
TARGETS=("sub_82424AF0","82424AF0")
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 d={"stage":"PRE324_NITRO_CALLERS_PINNED_PAL","status":"FAILED","apk_built":False,"game_modified":False,"signer_accessed":False}
 try:
  with tempfile.TemporaryDirectory(prefix="pre324_") as tmp:
   arc=Path(tmp)/"pre99.tar.gz";download(drive_client(),arc)
   h,_,n=sha_file(arc)
   if h!=EXPECTED_SHA256 or n!=EXPECTED_BYTES:raise ValueError("PRE99 SHA mismatch")
   x=[];nshards=0
   with tarfile.open(arc,"r:gz") as tf:
    for member in tf:
     name=member.name.lstrip("./")
     if not member.isfile() or not CXX.fullmatch(name):continue
     nshards+=1
     if member.size>8_000_000:raise ValueError("unexpected CXX member size")
     f=tf.extractfile(member)
     if f is None:raise ValueError("unreadable CXX")
     b=f.read()
     # Exact bytes matching distinguishes definitions/calls, no broad symbol guessing.
     if b"sub_82424AF0" not in b and b"82424AF0" not in b:continue
     lines=b.decode("utf8",errors="replace").splitlines()
     fn="unknown"
     for i,line in enumerate(lines):
      m=re.search(r"DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)",line)
      if m:fn=m.group(1)
      if "sub_82424AF0" not in line and "82424AF0" not in line:continue
      x.append({"file":name,"function":fn,"line":i+1,
        "match":line.strip()[:200],"context":[lines[j].strip()[:160]
           for j in range(max(0,i-5),min(len(lines),i+8))]})
   if nshards<100 or not x:raise ValueError("incomplete xrefs")
   d.update({"status":"AUDIT_OK","pre99_sha256":h,"pal_shards_scanned":nshards,
       "matches":x[:75],"total_matches":len(x),"truncated":len(x)>75,
       "limit":"Explicit textual calls only. Indirect vtable dispatch can have no named xref; object ownership remains unknown."})
 except Exception as e:d["error_type"]=type(e).__name__
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
 print("PRE324_STATUS",d["status"])
 print("PRE324_MATCHES",d.get("total_matches"))
 for m in d.get("matches",[])[:15]:print("PRE324_XREF",m["function"],m["file"],m["line"],m["match"][:110])
 print("PRE324_ERROR_TYPE",d.get("error_type"))
 return 0 if d["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
