#!/usr/bin/env python3
"""PRE747 authentic USA-only Android NDK ARM64 object gate. No APK or signing."""
import argparse,hashlib,json,re,subprocess,sys,tempfile,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk,get_include_paths,arm64_elf
from pre288_bmw_feature_on_pal_native_preflight import clean_env
OUT=Path("/tmp/nfsmw-pre747/PRE747_USA_ARM64_OBJECT_NOAPK.json")
COMMIT="a964bab0524796efdd2a8818394f83909bafa404"
RAW="https://raw.githubusercontent.com/Juniklx/NFSMW-Recompiled-Mobile/"+COMMIT+"/nativo/experimental/usa_catchup/"
BLOBS={"nfsmw_catchup_carreira.cpp":"b0005eacd221387e448cc4fd7f239f5f201b303f",
       "nfsmw_catchup_carreira_policy.h":"e926726ff8bc96ec296dca8765ec726c19134933"}
CMAKE_SHA="74ba63ff327390856c4f8976dea6facdfc05cb86c4fa9e87ba4c5a7997f0fdc3"
TARGET_SHA="b1e56d940029022789d2159e99b6125912f0e0cdaf12124b9178e6ffc0825668"
PHASE="START"
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fetch(name):
  with urllib.request.urlopen(RAW+name,timeout=40) as r:data=r.read(15000)
  if not data or len(data)>12000 or blob(data)!=BLOBS[name]:
    raise ValueError("Public source Git blob hash mismatch")
  return data
def audit():
  global PHASE
  tool=find_ndk()
  with tempfile.TemporaryDirectory(prefix="nfsmw-pre747-") as td:
    t=Path(td);arch=t/"PRE99.tar.gz"
    PHASE="DOWNLOAD_PRE99"
    download(drive_client(),arch)
    dg,_md5,size=sha_file(arch)
    if dg!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive SHA mismatch")
    root=t/"restore";root.mkdir()
    restore(arch,root)
    arch.unlink(missing_ok=True)
    root=root/"workspace"
    PHASE="USA_SOURCE_PROVENANCE"
    cmake=root/"nativo/app_usa/CMakeLists.txt"
    previous=cmake.read_bytes()
    if sha(previous)!=CMAKE_SHA:raise ValueError("Original USA CMake SHA mismatch")
    pal_sha=sha((root/"nativo/app/CMakeLists.txt").read_bytes())
    guest=(root/"nativo/app_usa/generated/default/nfsmw_recomp.52.cpp").read_bytes()
    mark=b"DEFINE_REX_FUNC(sub_823328C0) {"
    if guest.count(mark)!=1:raise ValueError("USA controller function absent/duplicated")
    i=guest.index(mark)+len(mark)
    j=guest.find(b"\nDEFINE_REX_FUNC(",i)
    if j<0 or sha(guest[i:j])!=TARGET_SHA:
      raise ValueError("USA controller differs from authenticated PRE745")
    PHASE="STAGE_USA_ONLY"
    for name in BLOBS:
      dest=root/"nativo/app_usa/src"/name
      if dest.exists():raise ValueError("Refusing repeated patch")
      dest.write_bytes(fetch(name))
    source=root/"nativo/app_usa/src/nfsmw_catchup_carreira.cpp"
    header=root/"nativo/app_usa/src/nfsmw_catchup_carreira_policy.h"
    data=source.read_bytes()
    if (data.count(b"REX_HOOK_RAW(sub_823328C0)")!=1
        or b"REX_HOOK_RAW(sub_82332898)" in data
        or b"REXCVAR_DEFINE_BOOL(nfsmw_sem_catchup_carreira, false" not in data
        or b"kRaceStatusGlobal = 0x82A2CB18u" not in header.read_bytes()):
      raise ValueError("Incorrect edition/global/default in private hook")
    cmake_text=previous.decode()
    anchor="    src/nfsmw_recortes_carrera.cpp\n"
    addition="    src/nfsmw_catchup_carreira.cpp\n"
    if cmake_text.count(anchor)!=1 or addition in cmake_text:
      raise ValueError("USA CMake anchor missing or repeated")
    patched=cmake_text.replace(anchor,anchor+addition,1)
    if patched.replace(addition,"",1)!=cmake_text:raise ValueError("CMake patch not reversible")
    cmake.write_text(patched)
    if sha((root/"nativo/app/CMakeLists.txt").read_bytes())!=pal_sha:
      raise ValueError("PAL CMake modified")
    PHASE="COMPILING_ANDROID_AARCH64_OBJECT"
    obj=t/"usa_catchup_arm64.o"
    argv=[str(tool["compiler"]),"-std=c++23","-DANDROID=1","-O1","-fPIC",
          "-Wno-unused-parameter","-c",str(source),"-o",str(obj)]
    for d in get_include_paths(root):argv+=["-I",str(d)]
    p=subprocess.run(argv,capture_output=True,text=True,env=clean_env(),timeout=360)
    if p.returncode:raise ValueError("NDK compile failed: "+p.stderr[-1150:])
    if not arm64_elf(obj):raise ValueError("Not actual ELF64 AArch64")
    nm=tool["ndk"]/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    s=subprocess.run([str(nm),"-g",str(obj)],capture_output=True,text=True,env=clean_env(),timeout=60)
    if s.returncode or len(re.findall(r"(?m)\bT\s+sub_823328C0$",s.stdout))!=1:
      raise ValueError("USA exported hook symbol not found exactly once in ARM64 object")
    PHASE="VERIFIED"
    return {"status":"AUDIT_OK_USA_AARCH64_OBJECT","original_pre99_sha256":dg,
            "usa_controller_original_sha256":TARGET_SHA,"template_commit":COMMIT,
            "usa_cmake_reversible":True,"pal_cmake_unchanged":True,
            "cvar_default_off":True,"real_usa_arm64_object_compiled":True,
            "arm64_object_sha256":sha(obj.read_bytes()),"arm64_object_size":obj.stat().st_size,
            "full_game_linked":False,"apk_built":False,"signer_accessed":False,
            "saves_modified":False,"runtime_catchup_effect_verified":False}
def main():
  global PHASE
  parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
  o=parser.parse_args()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:
    if not o.run_id.isdecimal():raise ValueError("Run ID invalid")
    result=audit()
  except Exception as e:
    result={"status":"FAILED","phase":PHASE,"error_type":type(e).__name__,
            "error_summary":str(e)[-1150:] if isinstance(e,ValueError) else "NDK exception",
            "apk_built":False,"signer_accessed":False}
  result.update({"stage":"PRE747_USA_CATCHUP_REAL_ANDROID_NDK_OBJECT_NOAPK",
                 "run_id":o.run_id,"utc":datetime.now(timezone.utc).isoformat()})
  OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  print("PRE747_STATUS="+result["status"])
  print("PRE747_PHASE="+PHASE)
  print("PRE747_USA_ARM64_OBJECT="+str(result.get("real_usa_arm64_object_compiled",False)))
  print("PRE747_NO_APK_NO_SIGNER")
  if result["status"]=="FAILED":print("PRE747_ERROR_TYPE="+result["error_type"])
  return 0 if result["status"]=="AUDIT_OK_USA_AARCH64_OBJECT" else 1
if __name__=="__main__":sys.exit(main())
