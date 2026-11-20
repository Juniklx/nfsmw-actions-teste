#!/usr/bin/env python3
"""PRE742 private PPC offset-cluster scan on SHA-pinned original PRE99 guest code.

Read-only. Search decimal PPC displacements for GRaceStatus possible field
layout inferred from structurally verified r3+6704 (race parameters).
Do not claim other shifted PC fields are proven on Xbox.
"""
import argparse
import json
import re
import tarfile
import tempfile
from collections import Counter
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID,EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
M=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
FUNC=re.compile(rb"(?m)^DEFINE_REX_FUNC\((sub_82[0-9A-F]{6})\)\s*\{")
OFFSETS={
  "race_context_inferred":6700,
  "race_params_verified":6704,
  "catchup_integral_predicted":17768,
  "catchup_derivative_predicted":17772,
  "catchup_adaptive_bonus_predicted":17776,
  "catchup_avg_percent_predicted":17780,
  "catchup_skill_count_predicted":17784,
  "catchup_skill_table_predicted":17788,
  "catchup_spread_count_predicted":17832,
  "catchup_spread_table_predicted":17836,
}
CATCH_NAMES=[x for x in OFFSETS if x.startswith("catchup")]
PAT={name:re.compile(rb"\b"+str(value).encode()+rb"\(r\d+\)") for name,value in OFFSETS.items()}
HASH_HIGH=re.compile(rb"(?i)//\s*(?:lis|addis)\s+\w+,\s*4315\b")
HASH_LOW=re.compile(rb"(?i)//\s*(?:ori|addi)\s+\w+,\s*\w+,\s*1254\b")
MAX_SCAN=400*1024*1024


def audit(archive):
    report={
        "stage":"PRE742_DECIMAL_PPC_CATCHUP_FIELD_CANDIDATES_READONLY",
        "pre99_sha256_verified":True,
        "struct_layout_x360_extra_offsets_verified":False,
        "known_offset":6704,
        "predicted_offset_subtraction_from_PC":124,
        "files_examined":0,
        "functions_examined":0,
        "bytes_examined":0,
        "field_occurrences":Counter(),
        "hits_by_field":{k:[] for k in OFFSETS},
        "catchup_cluster_candidates":[],
        "hash_imm_candidates":[],
        "files_modified":False,"apk_built":False,"signing_accessed":False,
    }
    with tarfile.open(archive,"r:gz",errorlevel=2) as tf:
        for m in tf:
            if not m.isfile() or not M.match(m.name):continue
            if not 0<m.size<=24*1024*1024:raise ValueError("Unexpected size of guest source")
            report["bytes_examined"]+=m.size
            if report["bytes_examined"]>MAX_SCAN:raise ValueError("Scan over limit")
            fh=tf.extractfile(m)
            if fh is None:raise ValueError("Guest source unreadable")
            with fh:data=fh.read()
            report["files_examined"]+=1
            func=list(FUNC.finditer(data))
            for i,f in enumerate(func):
                name=f.group(1).decode()
                body=data[f.end():func[i+1].start() if i+1<len(func) else len(data)]
                report["functions_examined"]+=1
                hits={}
                for field,p in PAT.items():
                    occurrences=list(p.finditer(body))
                    if not occurrences:continue
                    report["field_occurrences"][field]+=len(occurrences)
                    hits[field]=[o.start() for o in occurrences]
                    if len(report["hits_by_field"][field])<20:
                        report["hits_by_field"][field].append({"fn":name,"member":m.name,
                            "count":len(occurrences)})
                catch=[field for field in CATCH_NAMES if field in hits]
                if catch and len(report["catchup_cluster_candidates"])<150:
                    excerpts=[]
                    for field in catch[:4]:
                        pos=hits[field][0]
                        excerpts.append({"field":field,
                          "source":body[max(0,pos-250):min(len(body),pos+550)].decode("utf-8","replace")})
                    report["catchup_cluster_candidates"].append({
                        "function":name,"member":m.name,
                        "catchup_field_types_matched":catch,"other_offsets_matched":[x for x in hits if x not in catch],
                        "num_matching_fields":len(catch),
                        "excerpts":excerpts
                    })
                highs=list(HASH_HIGH.finditer(body))
                lows=list(HASH_LOW.finditer(body))
                if highs and lows and len(report["hash_imm_candidates"])<40:
                    close=[(a,b) for a in highs for b in lows if abs(a.start()-b.start())<500]
                    if close:
                        start=min(close[0][0].start(),close[0][1].start())
                        report["hash_imm_candidates"].append({
                            "function":name,"member":m.name,
                            "snippet":body[max(0,start-500):min(len(body),start+1000)].decode("utf-8","replace")})
    report["field_occurrences"]=dict(report["field_occurrences"])
    report["catchup_cluster_candidates"].sort(key=lambda x:x["num_matching_fields"],reverse=True)
    return report


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--report",required=True,type=Path)
    o=a.parse_args()
    drive=drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre742-") as temp:
        archive=Path(temp)/"pre99.tar.gz"
        meta=drive.files().get(fileId=BACKUP_ID,fields="id,size").execute()
        if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
            raise ValueError("PRE99 archive metadata unexpected")
        download(drive,archive)
        sha,_md5,size=sha_file(archive)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive changed")
        report=audit(archive)
    o.report.parent.mkdir(parents=True,exist_ok=True)
    o.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE742_FUNCTIONS="+str(report["functions_examined"]))
    print("PRE742_FIELDS="+json.dumps(report["field_occurrences"],sort_keys=True))
    print("PRE742_CLUSTERS="+str(len(report["catchup_cluster_candidates"])))
    print("PRE742_HASH_IMMEDIATE_CANDIDATES="+str(len(report["hash_imm_candidates"])))
    name="NFSMW_PRE742_PRIVATE_PPC_DECIMAL_OFFSETS.json"
    uploaded=drive.files().create(
        body={"name":name,"parents":[FOLDER],"mimeType":"application/json"},
        media_body=MediaFileUpload(str(o.report),mimetype="application/json"),
        fields="id,name,parents").execute()
    if uploaded.get("name")!=name or FOLDER not in uploaded.get("parents",[]):
        raise ValueError("Report upload verification failed")
    print("PRE742_REPORT_DRIVE_ID="+uploaded["id"])
    print("PRE742_NO_PATCH_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
