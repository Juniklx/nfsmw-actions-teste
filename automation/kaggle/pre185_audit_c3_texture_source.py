#!/usr/bin/env python3
"""PRE185: SHA-pinned, read-only localization of the C3 texture in-flight error."""
from __future__ import annotations
import hashlib, json, re, tarfile, tempfile, zipfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre185-texture-c3-audit")
TEXT_EXT={".c",".cc",".cpp",".h",".hpp",".inl",".ipp",".kt",".java"}
STRONG=("incoherente","indice de textura en vuelo","índice de textura en vuelo",
        "texture index in flight","texture index in-flight","texture in flight",
        "textura en vuelo")
SECONDARY=("in_flight_texture","inflight_texture","texture_binding_thread",
           "texture_bind_thread","texture_link_thread","texture in-flight",
           "texturas en vuelo")
MAX_SOURCE=2_000_000
MAX_ARCHIVE_SOURCES=15
MAX_REPORT_RESULTS=125
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    matched=[];scanned=0;skipped_large=0;selected=0
    with tempfile.TemporaryDirectory(prefix="pre185_readonly_") as tmp:
        archive=Path(tmp)/"PRE99.tar.gz"
        download(drive_client(),archive)
        check,_,size=sha_file(archive)
        if check!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise RuntimeError("PRE185 refuses non-authenticated PRE99 archive")
        with tarfile.open(archive,"r:gz") as tar, zipfile.ZipFile(OUT/"PRE185_C3_TEXTURE_READONLY_AUDIT.zip","w",zipfile.ZIP_DEFLATED) as out:
            for member in tar:
                name=member.name
                if not member.isfile() or "/nativo/" not in "/"+name or Path(name).suffix.lower() not in TEXT_EXT:continue
                if member.size>MAX_SOURCE:
                    skipped_large+=1
                    continue
                if any(seg in name.lower() for seg in ("/build/","/outputs/","/gradle/","/.git/")):continue
                fd=tar.extractfile(member)
                if fd is None:continue
                data=fd.read()
                if len(data)!=member.size:raise RuntimeError("Source short read: "+name)
                scanned+=1
                text=data.decode("utf-8","replace")
                norm=text.casefold()
                is_strong=any(w in norm for w in STRONG)
                is_secondary=any(w in norm for w in SECONDARY)
                is_c3_texture=("c3" in norm and "textur" in norm and ("thread" in norm or "hilo" in norm or "indice" in norm or "índice" in norm))
                if not (is_strong or is_secondary or is_c3_texture):continue
                lines=text.splitlines()
                hits=[]
                for i,line in enumerate(lines):
                    lowered=line.casefold()
                    if (any(w in lowered for w in STRONG+SECONDARY) or
                        ("c3" in lowered and "textur" in lowered)):
                        start=max(0,i-7);end=min(len(lines),i+9)
                        hits.append({"line":i+1,"context":[str(j+1)+": "+lines[j][:300] for j in range(start,end)]})
                    if len(hits)>=12:break
                rec={"path":name,"bytes":len(data),"sha256":sha(data),
                     "strong":is_strong,"secondary":is_secondary,
                     "c3_texture":is_c3_texture,"hit_count_capped":len(hits),
                     "snippets":hits}
                if len(matched)<MAX_REPORT_RESULTS:matched.append(rec)
                if selected<MAX_ARCHIVE_SOURCES and (is_strong or is_secondary):
                    out.writestr("sources/"+str(selected+1)+"_"+Path(name).name,data)
                    selected+=1
            report={"stage":"PRE185","sha256_pre99_authenticated":check,
                    "pre99_bytes":size,"read_only":True,"modified_files":False,
                    "scanned_text_sources":scanned,"skipped_large_sources":skipped_large,
                    "matched_sources":matched,
                    "sources_included_in_archive":selected,
                    "limitation":"PRE99 snapshot is baseline; compare hashes and patches before assuming V35 exact source."}
            out.writestr("PRE185_REPORT.json",json.dumps(report,indent=2,ensure_ascii=False))
        print("PRE185_AUTHENTICATED",check,"SCANNED",scanned,
              "MATCHED",len(matched),"SOURCE_EXTRACTS",selected)
        for item in matched[:15]:
            print("PRE185_MATCH",item["path"],item["sha256"],
                  "strong",item["strong"],"secondary",item["secondary"],"C3",item["c3_texture"])
if __name__=="__main__":audit()
