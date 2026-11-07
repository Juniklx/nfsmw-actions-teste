#!/usr/bin/env python3
"""PRE325: read-only PRE99 PAL Nitro dispatch evidence scan. No APK, patch, signer or save."""
from pathlib import Path
import tarfile,tempfile,re,json,sys
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre325/NFSMW_PRE325_NITRO_DISPATCH.json")
TARGET="sub_82424AF0"
PATTERNS=(
    ("symbol",re.compile(r"\bsub_82424AF0\b",re.I)),
    ("hex_address",re.compile(r"(?<![0-9a-f])(?:0x)?82424af0(?![0-9a-f])",re.I)),
    ("decimal_address",re.compile(r"(?<!\d)2185382640(?!\d)")),
)
CXX=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE325_NITRO_DISPATCH_READONLY","status":"FAILED",
      "apk_built":False,"game_modified":False,"signer_accessed":False,
      "owner_verified":False,"indirect_dispatch_verified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre325_") as tmp:
            archive=Path(tmp)/"pre99.tar.gz"
            download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 archive integrity mismatch")
            hits=[];shards=0;other=0;sample=[]
            with tarfile.open(archive,"r:gz") as tf:
                for member in tf:
                    name=member.name.lstrip("./")
                    if not member.isfile():continue
                    if CXX.fullmatch(name):shards+=1
                    elif name.startswith("workspace/nativo/") and name.endswith((".cpp",".hpp",".h",".c")):other+=1
                    else:continue
                    if member.size>8_000_000:continue
                    f=tf.extractfile(member)
                    if f is None:continue
                    lines=f.read().decode("utf-8",errors="replace").splitlines()
                    current="unknown"
                    for i,line in enumerate(lines):
                        m=re.search(r"DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)",line)
                        if m:current=m.group(1)
                        tags=[tag for tag,pat in PATTERNS if pat.search(line)]
                        if not tags:continue
                        if len(hits)<150:
                            hits.append({"file":name,"line":i+1,"function":current,
                                "tags":tags,"text":line.strip()[:200],
                                "nearby":[x.strip()[:140] for x in lines[max(0,i-3):min(len(lines),i+4)]]})
            if shards<100:raise ValueError("insufficient PAL shards")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,"pal_shards_scanned":shards,
                "other_source_files_scanned":other,"bounded_matches":hits,
                "matches_truncated":len(hits)==150,
                "interpretation":"Textual evidence only. No match does not exclude indirect dispatch. Neither player ownership nor capacity semantics are proven.",
                "next_gate":"Runtime trace of ctx.r3 object identity, bounded per-session, with player-versus-AI corroboration before any optional patch."})
    except Exception as e:
        result["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE325_STATUS",result["status"])
    print("PRE325_PAL_SHARDS",result.get("pal_shards_scanned"))
    print("PRE325_MATCHES",len(result.get("bounded_matches",[])))
    print("PRE325_OWNER_VERIFIED",result["owner_verified"])
    print("PRE325_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
