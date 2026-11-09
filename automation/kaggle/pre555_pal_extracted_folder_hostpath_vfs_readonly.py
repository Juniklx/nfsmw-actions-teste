#!/usr/bin/env python3
"""PRE555: authenticated historical extracted-folder VFS callpath and PAL resource boundary.

Read-only: PRE99 user-owned source is SHA pinned, inspected in a private runner and
discarded; only structural evidence and fixed metadata are committed. No source
snippets, original game assets, APKs or saves are published. This is NOT a V48
on-device trace, nor a guest ZDIR/VPAK loader verification.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre555/report.json")
TARGETS = {
 "runtime": ("workspace/nativo/sdk/src/system/runtime.cpp",
             "2a0a0f221f4851500afe79a0d7515f3a8815210d93799d7c75605feaa?"),
 "host_device": ("workspace/nativo/sdk/src/filesystem/devices/host_path_device.cpp",
                 "dccda2f48817a594aaa1e22dd4d6210e6f8c8eb438345ad9e423420587450be4"),
 "host_entry": ("workspace/nativo/sdk/src/filesystem/devices/host_path_entry.cpp",
                "d9cc8916666ab499ccb67fc07c9283917da8bf708c987c05cf9a393ae28bbdb3"),
 "host_file": ("workspace/nativo/sdk/src/filesystem/devices/host_path_file.cpp",
               "7dace8159023592ee8008a0b0528a3798aea6a1856bc8e003492b9c4cce65346"),
 "virtual_fs": ("workspace/nativo/sdk/src/filesystem/virtual_file_system.cpp",
                "a3e89c5d85f899d9756750fc35544902bc9d"),
 "guest_io": ("workspace/nativo/sdk/src/kernel/xboxkrnl/xboxkrnl_io.cpp",
              "40869526201fbed631b7bb506c83680edc02b2f4a6701f31a19b1a068c622015"),
}
# The first two placeholders are filled from the exact already authenticated PRE509 report
# to avoid mistyping 64-character source pins; no arbitrary report values may be accepted.
PATS = {
 "runtime": {
  "android_uri_detection": r"\bIsAndroidContentUri\s*\(",
  "regular_image_file_test": r"es_uri_android\s*\|\|\s*std::filesystem::is_regular_file\s*\(",
  "image_device_branch": r"std::make_unique<rex::filesystem::DiscImageDevice>\s*\(",
  "folder_device_branch": r"std::make_unique<rex::filesystem::HostPathDevice>\s*\(",
  "exclusive_image_else_folder": r"DiscImageDevice>\s*\([^;]+;\s*}\s*else\s*\{\s*device\s*=\s*std::make_unique<rex::filesystem::HostPathDevice>",
  "device_initialize": r"if\s*\(\s*!device->Initialize\s*\(",
  "register_mount": r"file_system_->RegisterDevice\s*\(",
 },
 "host_device": {
  "initialize": r"HostPathDevice::Initialize\s*\(",
  "resolve_guest_relative_path": r"HostPathDevice::ResolvePath\s*\(",
  "physical_child_enumeration": r"rex::filesystem::ListFiles\s*\(",
 },
 "host_entry": {
  "open": r"HostPathEntry::Open\s*\(",
  "open_existing_host_file": r"rex::filesystem::FileHandle::OpenExisting\s*\(",
  "return_host_file": r"new\s+HostPathFile\s*\(",
 },
 "host_file": {
  "read_bytes": r"HostPathFile::ReadSync\s*\(",
 },
 "virtual_fs": {
  "resolve_mount_device": r"device->ResolvePath\s*\(",
  "open_guest_file": r"VirtualFileSystem::OpenFile\s*\(",
 },
 "guest_io": {
  "guest_kernel_to_vfs_open": r"REX_KERNEL_FS\s*\(\s*\)\s*->\s*OpenFile\s*\(",
 }
}
LEX = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/', re.S)

def strip_comments(raw: str) -> str:
 def repl(match):
  v=match.group(0)
  return "".join("\n" if c=="\n" else " " for c in v) if v.startswith("//") or v.startswith("/*") else v
 return LEX.sub(repl, raw)

def load_metadata(name):
 j=json.loads(Path(name).read_text())
 if j.get("status")!="AUDIT_OK": raise ValueError("Prior audit incomplete: "+name)
 return j

def audit():
 prev=load_metadata("docs/PRE509_HISTORICAL_VFS_MOUNT_CALLPATH_READONLY.json")
 v48=load_metadata("docs/PRE511_ORIGINAL_V48_APK_RUNTIME_MARKERS_READONLY.json")
 dex=load_metadata("docs/PRE515_V48_DEX_GAME_ROOT_METHOD_REFS_READONLY.json")
 pal=load_metadata("docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json")
 prep=load_metadata("docs/PRE554_V48_RUNTIME_EVIDENCE_PREPARATION_READONLY.json")
 note=Path("docs/PRE554_SHEVERY_ANDROID_DEVICE_EVIDENCE_READONLY_20261108.md").read_text()
 if ("Sim estou executando via pasta extraída" not in note or
     "user_confirmed_source_type=EXTRACTED_FOLDER" not in note):
  raise ValueError("Current user-supplied extracted-folder evidence absent")
 if (prev.get("actual_V48_file_mount_verified") is not False or
     prev.get("source_provenance")!="authenticated PRE99 historical snapshot, not current V48" or
     v48.get("original_apk_sha256")!="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35" or
     v48.get("V48_apk_exact_hash_verified") is not True or
     dex.get("selected_game_edition_runtime_proven") is not False or
     pal.get("original_pal_ZDIR_in_ram_resource_lookup_verified") is not True or
     pal.get("original_pal_ZZDATA_sector_padding_all_zero_verified") is not True or
     prep.get("device_session_vfs_mount_branch_proven") is not False):
  raise ValueError("Prior source, edition or resource provenance changed")
 prior={x["original_pre99_relative_source"]:x["sha256"] for x in prev["source_reviews"]}
 # Enforce exactly the authenticated PRE509 source hash pins.
 pins={k:(p,prior.get(p)) for k,(p,_) in TARGETS.items()}
 if any(not sha or len(sha)!=64 for p,sha in pins.values()):
  raise ValueError("PRE509 pins absent")
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre555_") as folder:
  z=Path(folder)/"pre99.tar.gz"
  download(drive_client(),z)
  digest,_,total=sha_file(z)
  if (digest,total)!=(EXPECTED_SHA256,EXPECTED_BYTES) or digest!=prev["PRE99_archive_sha256"]:
   raise ValueError("Authenticated PRE99 archive changed")
  bypath={v[0]:k for k,v in pins.items()}
  checked={}
  with tarfile.open(z,"r:gz",errorlevel=2) as archive:
   for member in archive:
    name=member.name.lstrip("./")
    if name not in bypath: continue
    label=bypath[name]
    if label in checked or not member.isfile() or not (100 <= member.size <= 250000):
     raise ValueError("Missing, duplicate or oversized authenticated source")
    f=archive.extractfile(member)
    if f is None: raise ValueError("Source read failed")
    raw=f.read()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=pins[label][1] or len(raw)!=member.size:
     raise ValueError("PRE509 source bytes differ for "+label)
    src=strip_comments(raw.decode("utf-8","replace"))
    matches={}
    for tag,pat in PATS[label].items():
     m=re.search(pat,src,re.S)
     if not m: raise ValueError("Code-path anchor missing: "+label+"/"+tag)
     # Only source anchor line numbers and hashes, not source contents.
     anchor=1+src.count("\n",0,m.start())
     line=src.splitlines()[anchor-1]
     matches[tag]={"line":anchor,"line_sha256":hashlib.sha256(line.encode()).hexdigest()}
    checked[label]={"historical_source_path":name,"source_sha256":sha,
                    "required_code_anchors":matches}
  if set(checked)!=set(TARGETS): raise ValueError("Required historical source missing")
 runtime=checked["runtime"]["required_code_anchors"]
 if not (runtime["regular_image_file_test"]["line"] <
         runtime["exclusive_image_else_folder"]["line"] <
         runtime["device_initialize"]["line"] <=
         runtime["register_mount"]["line"]):
  raise ValueError("Unexpected image/folder branching and mount order")
 # Validated original PAL resource index -> member mapping. Not real phone file bytes.
 if (pal.get("source_PAL_index_row")!=806 or
     pal.get("source_PAL_original_ZDIR_sha256")!="7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee" or
     pal.get("original_resource_sector_offset_bytes")!=355932160 or
     pal.get("original_pal_ZZDATA_sector_padding_zero_bytes")!=512):
  raise ValueError("PAL historical ZDIR-to-ZZDATA mapping changed")
 return {
   "stage":"PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_HISTORICAL_SOURCE_AUDIT",
   "status":"AUDIT_OK",
   "user_reported_current_game_source":"EXTRACTED_FOLDER_NOT_ISO",
   "phone_versionCode_48_previous_user_shevery_confirmed":True,
   "v48_apk_binary_hostpathdevice_marker_confirmed_from_PRE511":True,
   "v48_compiled_android_edition_selection_chain_confirmed_from_PRE515":True,
   "PRE99_authenticated_source_archive_sha256":digest,
   "PRE99_history_not_V48_execution":True,
   "PRE99_regular_file_or_URI_uses_discimage_else_folder_uses_hostpath_code_verified":True,
   "PRE99_guest_kernel_vfs_host_entry_file_read_code_anchors_verified":True,
   "PRE99_source_code_anchor_index":checked,
   "original_PAL_ZDIR_index_row_for_GLOBAL_ATTRIBUTES_BIN":806,
   "original_PAL_ZZDATA4_resource_offset_bytes":355932160,
   "original_PAL_ZZDATA4_reserved_sector_bytes":698368,
   "original_PAL_ZZDATA4_zero_padding_bytes":512,
   "PRE551_original_PAL_archive_sector_RAM_readback_verified":True,
   "translation_extracted_folder_bytes_match_original_PAL_ZIP_proven":False,
   "v48_current_runtime_hostpath_mount_traced":False,
   "pal_guest_libmain_loaded_directly_observed":False,
   "actual_guest_ZDIR_VPAK_loader_execution_proven":False,
   "new_BMW_ExpN_collection_accepted_by_guest":False,
   "FE_price_checkout_physics_save_persistence_proven":False,
   "game_source_exported":False,"game_assets_modified":False,
   "APK_built":False,"save_modified":False,
   "signing_material_accessed":False,"BMW_tuning_enabled":False,
   "next_gate":"TRACE_ZDIR_ZZDATA_GUEST_RESOURCE_READER_AND_COMPARE_EXTRACTED_FOLDER_BYTES_NONDESTRUCTIVELY"
 }
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--run-id",required=True)
 args=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try: report=audit()
 except Exception as ex:
  report={"stage":"PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_HISTORICAL_SOURCE_AUDIT",
          "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:220],
          "game_source_exported":False,"game_assets_modified":False,"APK_built":False,
          "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
 report["run_id"]=args.run_id
 report["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print("PRE555_STATUS",report["status"],flush=True)
 print("PRE555_FOLDERVFS_PRE99",report.get("PRE99_regular_file_or_URI_uses_discimage_else_folder_uses_hostpath_code_verified"),flush=True)
 print("PRE555_SOURCE_FILES",len(report.get("PRE99_source_code_anchor_index",{})),flush=True)
 print("PRE555_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
 return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
 raise SystemExit(main())
