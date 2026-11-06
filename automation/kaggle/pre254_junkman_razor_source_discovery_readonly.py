#!/usr/bin/env python3
"""PRE254: authenticated PRE99 static keyword / money-site source audit.
Read-only. No APK build, no key access, no save modification.
Keyword matches are leads, not proof of any inventory representation.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tarfile, tempfile, sys
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUTPUT=Path("/tmp/nfsmw-pre254/PRE254_JUNKMAN_RAZOR_SOURCE_DISCOVERY.json")
TEXT_SUFFIX={".cpp",".c",".h",".hpp",".cc",".java",".kt",".json",".xml",
             ".txt",".ini",".toml",".yml",".yaml",".cmake",".csv",".md"}
BIN_SUFFIX={".xex",".xbe",".xip",".xdbf",".bin",".dat"}
RELEVANT_PREFIX=("workspace/nativo/app/","workspace/nativo/app_usa/",
                 "workspace/android/app/","workspace/nativo/out/")
EXCLUDE_SUBSTR=("credential","secret","password","keystore","/signing/",
                "asssinatura","assinatura",".p12",".pfx",".jks",
                "/thirdparty/","/third_party/","/build/","/outputs/",
                "/.gradle/","/node_modules/")
PATTERNS={
    "junkman": r"junk[ _-]*man|junkman",
    "junk_parts": r"junk[ _-]*part|junk[ _-]*upgrade",
    "unique_performance": r"unique[ _-]*(?:performance|upgrade|part|engine|transmission|suspension|brakes|tires|turbo|nitrous)",
    "inventory": r"(?:inventory|inventario|stock|parts[ _-]*count|upgrade[ _-]*count)",
    "razor": r"\\brazor\\b",
    "bmw_m3": r"bmw[ _-]*m3|m3[ _-]*gtr",
    "prologue": r"prologue|prologo|intro[ _-]*race|starter[ _-]*car",
    "career_reward": r"career[ _-]*reward|race[ _-]*reward|pink[ _-]*slip",
}
# Escape-safe byte regex, with optional NULs between ASCII characters for UTF-16LE/BE.
def patterns_for(value: str):
    base=value.replace("\\\\b",r"\\b")
    result=[re.compile(base.encode("ascii"),re.I)]
    return result
SEARCH={k:patterns_for(v) for k,v in PATTERNS.items()}
SOURCE_TARGET="workspace/nativo/app/generated/default/nfsmw_recomp.7.cpp"
SOURCE_SHA="0f423d5906ebadf38209a4e9c7e43449573b6f37f02f3df6528f5bef1251daa6"
def audit():
    with tempfile.TemporaryDirectory(prefix="pre254_") as td:
        archive=Path(td)/"PRE99.tar.gz"
        download(drive_client(),archive)
        dig,_,n=sha_file(archive)
        if dig != EXPECTED_SHA256 or n != EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 fingerprint mismatch")
        output={"stage":"PRE254_JUNKMAN_RAZOR_READONLY_DISCOVERY",
                "status":"AUDIT_OK","verified_pre99_sha256":dig,
                "read_only":True,"apk_built":False,"patch_applied":False,
                "key_accessed":False,"saves_accessed":False,
                "no_semantics_inferred":True,
                "category_counts":{k:0 for k in SEARCH},
                "hits":{k:[] for k in SEARCH},
                "files_scanned":0,"bytes_scanned":0,
                "filename_candidates":[],"skipped_large_files":0}
        target=None
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for m in tar:
                if not m.isfile():continue
                name=m.name.lstrip("./")
                lower=name.lower()
                if any(x in lower for x in EXCLUDE_SUBSTR):continue
                if not name.startswith(RELEVANT_PREFIX):continue
                if re.search(r"junk|razor|bmw|upgrade|reward|inventory|unique",Path(name).name,re.I):
                    if len(output["filename_candidates"])<75:output["filename_candidates"].append(name)
                ext=Path(name).suffix.lower()
                if ext not in TEXT_SUFFIX and ext not in BIN_SUFFIX:continue
                if m.size > (50_000_000 if ext in BIN_SUFFIX else 5_000_000):
                    output["skipped_large_files"]+=1
                    continue
                f=tar.extractfile(m)
                if f is None:continue
                raw=f.read()
                if len(raw)!=m.size:raise ValueError("Truncated member")
                output["files_scanned"]+=1
                output["bytes_scanned"]+=len(raw)
                if name==SOURCE_TARGET:
                    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
                        raise ValueError("PRE240 PAL money source SHA mismatch")
                    target=raw
                member_hash=None
                for category,rxs in SEARCH.items():
                    local=[]
                    for rx in rxs:
                        local.extend(list(rx.finditer(raw))[:60])
                    if not local:continue
                    output["category_counts"][category]+=len(local)
                    if len(output["hits"][category])>=30:continue
                    if member_hash is None:member_hash=hashlib.sha256(raw).hexdigest()
                    # Bounded excerpts for diagnosis; never publish archive contents.
                    excerpts=[]
                    for h in local[:3]:
                        a=max(0,h.start()-30);b=min(len(raw),h.end()+45)
                        sample=raw[a:b].decode("utf-8","replace")
                        sample="".join(c if c.isprintable() else " " for c in sample)
                        excerpts.append({"offset":h.start(),"context":sample[:90]})
                    output["hits"][category].append({"file":name,"sha256":member_hash,
                                                     "matches_in_file_bounded":len(local),
                                                     "samples":excerpts})
        if target is None:raise ValueError("Pinned PAL generated source not present")
        text=target.decode("utf-8","replace")
        definitions=list(re.finditer(r"(?m)^DEFINE_REX_FUNC\\(sub_[0-9A-Fa-f]{8}\\)",text))
        body=None
        for i,m in enumerate(definitions):
            if m.group(1)=="sub_82564D80":
                body=text[m.start():definitions[i+1].start() if i+1<len(definitions) else len(text)]
                break
        if body is None:raise ValueError("PAL account write function missing")
        lines=body.splitlines()
        idx=[i for i,line in enumerate(lines) if re.search(r"//\\s*stw\\s+r\\d+,\\s*12\\(r11\\)",line)]
        if len(idx)!=5:raise ValueError("Expected exactly five PAL account stores")
        fifth=idx[4]
        ctx=[{"ordinal":i-fifth,"text":line.strip()[:180]}
             for i,line in enumerate(lines[max(0,fifth-60):fifth+16],max(0,fifth-60))]
        output["confirmed_money_site8_static_context"]={
            "function":"sub_82564D80","store_ordinal":5,
            "target_guest_pc_candidate":"0x8256608C",
            "preceding_and_following_lines":ctx,
            "note":"Account store observed 30000->3000 in Android PRE253; this is static context, not whole purchase semantics"}
        output["limitations"]=[
            "Exact keyword absence does not rule out unnamed guest inventory fields",
            "Source snapshot PRE99 was authenticated but is not a dynamically symbolized game",
            "Inventory storage, per-part semantics, Razor race and reward behavior remain unproven",
            "No original game save was read or changed",
            "Binary game archives outside PRE99 are not exhaustively indexed"]
        return output

def main():
    arg=argparse.ArgumentParser();arg.add_argument("--run-id",required=True)
    a=arg.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Bad run id")
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    out={"status":"FAILED","phase":"START","read_only":True,"apk_built":False}
    try:out=audit()
    except Exception as e:out["error_type"]=type(e).__name__
    out["github_run_id"]=a.run_id
    out["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE254_STATUS",out["status"])
    print("PRE254_CATEGORY_COUNTS",out.get("category_counts",{}))
    print("PRE254_FILES_SCANNED",out.get("files_scanned",0))
    if out["status"]!="AUDIT_OK":print("PRE254_ERROR",out.get("error_type"))
    return 0 if out["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
