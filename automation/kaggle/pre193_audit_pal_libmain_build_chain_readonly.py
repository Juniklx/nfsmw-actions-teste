#!/usr/bin/env python3
"""PRE193: read-only verification of PAL/PT-BR libmain build-chain and V35 binary.
No restore, compilation, source patching, release-signing or credential reporting.
"""
from __future__ import annotations
import hashlib, json, re, tarfile, tempfile, zipfile
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre193-pal-libmain-readonly")
APK_ID="1New_ieqealhy_FrXsKH1cgtV57otu4od"
APK_SIZE=47102145
APK_SHA="e3b5699e017cb6c8b21baebfa00ea4bb33c731c1f63fff39ee01ef7192a09a13"
PAL_SOURCE="workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp"
PAL_SOURCE_SHA="046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2"
USA_SOURCE="workspace/nativo/app_usa/src/nfsmw_nativo_dibujos.cpp"
USA_SOURCE_SHA="92e0a15836217a535c6f81e2461381616f46c331c83201cabd14a71c2d8c2342"
MAIN_SHA="ce33b914b113531d888010368d8570205e4acf54542e659e36963790a4dc5a7c"
USA_MAIN_SHA="4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83"
BUILDER_SHA="ff490bd4d1025f06cc3470af030b7f881a618c34e3046acada4b06123edd54f2"
TARGETS=[
 "workspace/android/app/build.gradle.kts",
 "workspace/android/app/src/main/cpp/CMakeLists.txt",
 "workspace/nativo/app/CMakeLists.txt",
 "workspace/nativo/app/generated/default/sources.cmake",
 "workspace/nativo/app_usa/CMakeLists.txt",
 PAL_SOURCE, USA_SOURCE,
]
PATTERNS=(
 "nfsmw.edicion", "appnativa", "outnativo", "externalnativebuild",
 "cmakelists.txt", "add_subdirectory", "add_library", "target_link_libraries",
 "include(", "sources.cmake", "nfsmw_nativo_dibujos",
 "libmain", "cxx_shared", "cmake_source_dir", "nativo/app",
 "file(glob", "aux_source_directory", "aplazarcopia",
 "indice de textura en vuelo incoherente",
)
SKIP=("password","secret","token","keystore","private_key","credential")
def sha(v:bytes)->str:return hashlib.sha256(v).hexdigest()

def extract_snippets(name:str,blob:bytes)->dict:
    lines=blob.decode("utf-8","replace").splitlines()
    hit=[i for i,v in enumerate(lines) if any(k in v.casefold() for k in PATTERNS)
         and not any(k in v.casefold() for k in SKIP)]
    keep=set()
    for i in hit[:38]:
        keep.update(range(max(0,i-2),min(len(lines),i+3)))
    lines_out=[]
    for i in sorted(keep)[:120]:
        v=lines[i].strip()[:260]
        if any(k in v.casefold() for k in SKIP):v="[REDACTED]"
        lines_out.append({"line":i+1,"text":v})
    return {"path":name,"bytes":len(blob),"sha256":sha(blob),
            "lines_total":len(lines),"hits_total":len(hit),
            "snippets_capped":lines_out,
            "source_ref_dibujos":any("nfsmw_nativo_dibujos" in v.casefold() for v in lines),
            "cmake_source_glob":any("file(glob" in v.casefold() or
                                    "aux_source_directory" in v.casefold() for v in lines),
            "contains_c3_error":b"indice de textura en vuelo incoherente" in blob}

def get_apk(drive,file_id:str,path:Path)->None:
    with path.open("wb") as fh:
        dl=MediaIoBaseDownload(fh,drive.files().get_media(fileId=file_id,supportsAllDrives=True),
                               chunksize=8*1024*1024)
        done=False
        while not done:_,done=dl.next_chunk(num_retries=4)

def main()->None:
    OUT.mkdir(parents=True,exist_ok=True)
    builder=Path("automation/kaggle/pre180_build_signed_v35_sdl_wait_fix.py").read_bytes()
    if sha(builder)!=BUILDER_SHA:
        raise RuntimeError("PRE193: V35 builder changed: refuse inference")
    text=builder.decode("utf-8")
    checks={
       "gradle_runs_pal_es":'"-Pnfsmw.edicion=pal_es"' in text,
       "stages_usa_from_v30":'v30["lib/arm64-v8a/libmain_usa.so"]' in text,
       "verifies_pal_generated_cmake":'root/"nativo/app/generated/default/sources.cmake"' in text,
       "pre180_does_not_explicitly_write_pal_dibujos":'nativo/app/src/nfsmw_nativo_dibujos.cpp' not in text,
    }
    if not all(checks.values()):raise RuntimeError("PRE193: builder preflight mismatched")
    report={"stage":"PRE193_PAL_PTBR_MAIN_BUILD_CHAIN_READONLY","read_only":True,
      "build_occurred":False,"patch_applied":False,"release_key_accessed":False,
      "pre99_authenticated":False,"builder_sha256":BUILDER_SHA,
      "builder_checks":checks,"runtime_mapped_library_proven":False,
      "selected_ptbr_ui_evidence":"PRE192 user screenshot, not direct proc maps",
      "sources":{}}
    with tempfile.TemporaryDirectory(prefix="pre193_") as temp:
        temp=Path(temp)
        d=drive_client()
        tar_path=temp/"pre99.tar.gz"
        download(d,tar_path)
        digest,_,n=sha_file(tar_path)
        if digest!=EXPECTED_SHA256 or n!=EXPECTED_BYTES:
            raise ValueError("PRE193: PRE99 SHA/byte-count mismatch")
        report["pre99_authenticated"]=True
        report["pre99_sha256"]=digest
        found={}
        with tarfile.open(tar_path,"r:gz") as tar:
            for member in tar:
                name=member.name.lstrip("./")
                if not member.isfile() or name not in TARGETS:continue
                if member.size>3_000_000:raise RuntimeError("PRE193: source unexpectedly large")
                fp=tar.extractfile(member)
                if fp is None:raise RuntimeError("PRE193: source not readable")
                b=fp.read()
                if len(b)!=member.size:raise ValueError("PRE193: truncated source")
                found[name]=extract_snippets(name,b)
        if set(found)!=set(TARGETS):
            raise ValueError("PRE193: missing source files: "+",".join(sorted(set(TARGETS)-set(found))))
        if found[PAL_SOURCE]["sha256"]!=PAL_SOURCE_SHA or found[USA_SOURCE]["sha256"]!=USA_SOURCE_SHA:
            raise ValueError("PRE193: PAL/USA C3 source not exact authenticated PRE99 bytes")
        report["sources"]=found
        report["source_gates_passed"]=True
        tar_path.unlink()
        apk=temp/"v35.apk"
        get_apk(d,APK_ID,apk)
        if apk.stat().st_size!=APK_SIZE or sha(apk.read_bytes())!=APK_SHA:
            raise ValueError("PRE193: unexpected V35 APK")
        with zipfile.ZipFile(apk) as z:
            if z.testzip() is not None:raise ValueError("PRE193: APK CRC mismatch")
            libs={}
            for name,expected in [("libmain.so",MAIN_SHA),("libmain_usa.so",USA_MAIN_SHA)]:
                b=z.read("lib/arm64-v8a/"+name)
                if sha(b)!=expected or not b.startswith(b"\x7fELF"):
                    raise ValueError("PRE193: APK library hash/ELF mismatch")
                libs[name]={"bytes":len(b),"sha256":sha(b),
                            "elf_arm64":len(b)>=20 and b[18:20]==b"\xb7\x00",
                            "contains_original_c3_error":b"indice de textura en vuelo incoherente" in b}
            if not libs["libmain.so"]["elf_arm64"] or not libs["libmain.so"]["contains_original_c3_error"]:
                raise ValueError("PRE193: PAL libmain ARM64/C3 string not found")
        report["v35_apk_sha256"]=APK_SHA
        report["libraries"]=libs
        report["apk_gates_passed"]=True
    output=OUT/"NFSMW_PRE193_PAL_BUILD_CHAIN_AUDIT.json"
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE193_READONLY_SUCCESS")
    print("PRE193_PRE99_SHA256_MATCH",report["pre99_authenticated"])
    print("PRE193_PAL_SOURCE_SHA256_MATCH",report["source_gates_passed"])
    print("PRE193_V35_APK_LIBMAIN_SHA256_MATCH",report["apk_gates_passed"])
    print("PRE193_RUNTIME_MAPPING_OBSERVED",report["runtime_mapped_library_proven"])
    print("PRE193_REPORT",output)
if __name__=="__main__":main()
