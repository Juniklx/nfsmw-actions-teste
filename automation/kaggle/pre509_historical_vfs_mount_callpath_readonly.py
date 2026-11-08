#!/usr/bin/env python3
"""PRE509: bounded authenticated PRE99 native VFS mount and file-open callpath.

Reanalyze code, not comments; show only small redacted source neighborhoods
in private CI logs. Publish metadata line numbers/hashes, not original source
files. PRE99 is historical and does not prove the V48 Android mount path.
No game assets are ever extracted or changed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre509/report.json")
ROOT="workspace/"
TARGETS=[
 "workspace/nativo/sdk/src/filesystem/virtual_file_system.cpp",
 "workspace/nativo/sdk/src/filesystem/devices/host_path_file.cpp",
 "workspace/nativo/sdk/src/filesystem/devices/host_path_entry.cpp",
 "workspace/nativo/sdk/src/filesystem/devices/host_path_device.cpp",
 "workspace/nativo/sdk/src/kernel/xboxkrnl/xboxkrnl_io.cpp",
 "workspace/nativo/sdk/src/rexglue/commands/init_command.cpp",
 "workspace/nativo/sdk/src/system/runtime.cpp",
 "workspace/nativo/sdk/src/ui/rex_app.cpp",
 "workspace/nativo/app/src/nfsmw_app.h",
]
MANDATORY=set(TARGETS)-{
 "workspace/nativo/sdk/src/filesystem/devices/host_path_entry.cpp",
 "workspace/nativo/sdk/src/filesystem/devices/host_path_device.cpp",
}
PATS={
 "mount_or_host_device":r"\bMount\s*\(|\bMountPath\s*\(|\bHostPathDevice\b|\bRegisterDevice\b|\bMountDirectory\b",
 "guest_game_route":r"game://|Game:\\|game_data_path|game_data_dir|game_path|game_dir|game_root|disc_path",
 "virtual_path_resolution":r"\bResolvePath\s*\(|\bOpenFile\s*\(|entry->Open\s*\(|\bFileAction\b",
 "host_physical_read":r"HostPathFile::(?:Read|Open)|HostPathEntry::(?:Open|ResolvePath)|\bReadSync\s*\(|\bpread\s*\(",
 "archive_name":r"\bZZDATA[0-9]*\b|\bZDIR\b|ATTRIBUTES\.BIN",
}
RX={k:re.compile(v,re.I) for k,v in PATS.items()}
REDACT=re.compile(r"(?i)password|passphrase|client_secret|refresh_token|private_key|oauth|credential|authorization|api[_-]?key")
# Preserve line layout while stripping C/C++ comments to avoid "ZZDATA" hits
# from narrative performance logs being mistaken for active code.
LEX=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/',re.S)
def drop_comments(text):
    def sub(m):
        t=m.group(0)
        return "".join("\n" if c=="\n" else " " for c in t) if t.startswith("//") or t.startswith("/*") else t
    return LEX.sub(sub,text)
def safe(line):
    if REDACT.search(line):return "[REDACTED POSSIBLY SENSITIVE LINE]"
    line=line.strip().replace("\t"," ")
    return line[:170]+("..." if len(line)>170 else "")
def audit():
    baseline=json.loads(Path("docs/PRE505_PRE99_NATIVE_ASSET_LOADER_PATHS_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE508_HISTORICAL_NATIVE_LOADER_SOURCE_ANCHORS_READONLY.json").read_text())
    if baseline.get("status")!="AUDIT_OK" or prior.get("status")!="AUDIT_OK" or prior.get("source_semantics_manually_reviewed") is not False:
        raise ValueError("PRE505/PRE508 authenticated historical boundary not verified")
    pinned={row["relative_path"]:row["source_sha256"]
            for row in baseline.get("first_party_source_candidates",[])}
    missing_pins=MANDATORY-set(pinned)
    if missing_pins:raise ValueError("Missing PRE505 source identity: "+str(sorted(missing_pins)))
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre509_") as td:
        archive=Path(td)/"pre99.tar.gz"
        download(drive_client(),archive)
        sha,_,size=sha_file(archive)
        if (sha,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 archive hash/size mismatch")
        source={}
        with tarfile.open(archive,mode="r:gz",errorlevel=2) as tar:
            for member in tar:
                name=member.name.lstrip("./")
                if name not in TARGETS:continue
                if not member.isfile() or not 0<member.size<=200_000:
                    raise ValueError("Suspicious target member "+name)
                fd=tar.extractfile(member)
                if fd is None:raise ValueError("Unreadable source "+name)
                raw=fd.read()
                if len(raw)!=member.size:raise ValueError("Truncated source "+name)
                observed=hashlib.sha256(raw).hexdigest()
                if name in pinned and observed!=pinned[name]:
                    raise ValueError("PRE505 pinned mismatch "+name)
                source[name]=(raw.decode("utf-8","replace"),observed)
        if MANDATORY-set(source):raise ValueError("Required source missing")
        reports=[]
        for path in TARGETS:
            if path not in source:continue
            original,digest=source[path]
            lines=original.splitlines()
            code_lines=drop_comments(original).splitlines()
            if len(lines)!=len(code_lines):raise ValueError("C++ comment strip line alignment lost")
            hits=[]
            counts=Counter()
            for i,clean in enumerate(code_lines,1):
                kinds=[name for name,rx in RX.items() if rx.search(clean)]
                if not kinds:continue
                counts.update(kinds)
                score=(13 if "mount_or_host_device" in kinds else 0)+(
                    10 if "virtual_path_resolution" in kinds else 0)+(
                    8 if "host_physical_read" in kinds else 0)+(
                    5 if "guest_game_route" in kinds else 0)+(
                    2 if "archive_name" in kinds else 0)
                hits.append((score,i,kinds))
            top=sorted(hits,key=lambda x:(-x[0],x[1]))[:10]
            print("PRE509_SOURCE",path,"sha256",digest,"active_code_hits",len(hits),flush=True)
            evidence=[]
            for _,line_num,kinds in sorted(top,key=lambda x:x[1]):
                low=max(1,line_num-4);high=min(len(lines),line_num+4)
                print("PRE509_SOURCE_CONTEXT",path,"anchor",line_num,"kinds",",".join(kinds),flush=True)
                for n in range(low,high+1):
                    print(f"PRE509_SRC:{path}:{n:05d} {safe(lines[n-1])}",flush=True)
                print("PRE509_END_CONTEXT",path,line_num,flush=True)
                evidence.append({"line":line_num,"kind":kinds,
                                 "original_line_sha256":hashlib.sha256(lines[line_num-1].encode()).hexdigest()})
            reports.append({
               "original_pre99_relative_source":path,
               "sha256":digest,"matched_pre505_pin":path in pinned,
               "source_lines":len(lines),
               "noncomment_matching_code_lines":len(hits),
               "pattern_hit_counts":dict(counts),
               "selected_code_anchors":evidence,
               "source_exported":False
            })
    return {"stage":"PRE509_HISTORICAL_VFS_GAME_MOUNT_SOURCE_CALLPATH_READONLY",
      "status":"AUDIT_OK","PRE99_archive_sha256":sha,
      "source_provenance":"authenticated PRE99 historical snapshot, not current V48",
      "comments_masked_before_pattern_scan":True,
      "candidate_files_read":len(reports),
      "source_reviews":reports,
      "bounded_redacted_snippets_only_in_private_job_log":True,
      "actual_V48_file_mount_verified":False,
      "game_ZDIR_resource_reader_identified":False,
      "VPAK_loader_acceptance_verified":False,
      "runtime_BMW_tuning_verified":False,
      "original_code_or_game_data_written":False,
      "APK_built":False,"save_modified":False,"signing_accessed":False,
      "tuning_enabled":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:d=audit()
    except Exception as ex:
        d={"stage":"PRE509_HISTORICAL_VFS_GAME_MOUNT_SOURCE_CALLPATH_READONLY",
           "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:240],
           "original_code_or_game_data_written":False,"APK_built":False,
           "save_modified":False,"signing_accessed":False,"tuning_enabled":False}
    d["run_id"]=a.run_id;d["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
    print("PRE509_STATUS",d["status"],flush=True)
    print("PRE509_SOURCE_COUNT",d.get("candidate_files_read"),flush=True)
    print("PRE509_ERROR",d.get("error_type","none"),d.get("error",""),flush=True)
    return 0 if d["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
