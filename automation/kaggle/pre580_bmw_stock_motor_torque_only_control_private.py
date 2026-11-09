#!/usr/bin/env python3
"""PRE580: private diagnostic fragment, BMW stock engine torque-only VPAK.
No new VLT collections/export records, no RefSpec changes, no pvehicle limits.
Compare original PTBR with nine original engine float values +5% synthetic;
not an unlock of tuning, not a release, not a game-file/device write.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import zip_directory,member_zdir,ZDIR_SHA
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre572_prepare_ptbr_bmw_private_patch_fragments import (
    stream_full_archive_digest,ensure_private_file)
import pre572_prepare_ptbr_bmw_private_patch_fragments as helpers
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre580/report.json")
OLD_RESOURCE_BYTES=697856
RESERVED=698368
ZDIR_ROW=805
BMW_MOTOR_BASE=139176
BMW_MOTOR_BYTES=96
BO=128
EXPECTED_BMW_ORIGINAL_SHA="e09efe8e63d0971da0949e898dbf8ba1b03c2954d2da04db48e9e56cb6437471"
EXPECTED_PTBR_ZZDATA4_SHA="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
PATCH_FOLDER="PRE580_BMW_TORQUE_ONLY_DIAGNOSTIC_20261109"
def sha(b):return hashlib.sha256(b).hexdigest()

def build_motor_only_variant():
    ref=json.loads(Path("docs/PRE497_BMW_TORQUE_ENGINE_SYNTHETIC_ENDPOINT.json").read_text())
    p477=json.loads(Path("docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json").read_text())
    p579=Path("docs/PRE579_DEVICE_AB_MARCEK_RESTORED_LOG_20261109.md").read_text(encoding="utf-8")
    if (ref.get("status")!="AUDIT_OK" or p477.get("status")!="AUDIT_OK"
        or ref.get("authenticated_source_pal_vpak_sha256")!=EXPECTED_VPAK_SHA
        or p477.get("source_sha256")!=EXPECTED_VPAK_SHA
        or p477["class_models"]["engine"]["collections"]["bmwm3gtr"]["bin_base_offset"]!=BMW_MOTOR_BASE
        or "83522f3f328bc9385c8fb9ebf20b6f0b668f4a7519db08a4d38d4881ffa37cde" not in p579):
        raise ValueError("Verified original motor layout or user A/B evidence missing")
    vectors=[v for v in ref["synthetic_test_vectors"] if v["synthetic_gain_basis_points"]==500]
    if len(vectors)!=1:raise ValueError("Reference PRE497 +5pct test vector absent")
    reader, pos=locate()
    original=reader.read(pos["absolute_offset"],pos["size"])
    if len(original)!=OLD_RESOURCE_BYTES or sha(original)!=EXPECTED_VPAK_SHA:
        raise ValueError("PAL source VPAK authentication failed")
    _stub,bin_len,vlt_len,bin_off,vlt_off=struct.unpack_from("<IIIII",original,16)
    if (bin_len,vlt_len,bin_off,vlt_off)!=(354959,342720,128,355136):
        raise ValueError("Original VPAK bin/VLT section map changed")
    motor_off=BO+BMW_MOTOR_BASE
    motor_original=original[motor_off:motor_off+BMW_MOTOR_BYTES]
    if sha(motor_original)!=EXPECTED_BMW_ORIGINAL_SHA:
        raise ValueError("Stock BMW physical engine SHA differs")
    modified=bytearray(original)
    changed_positions=[]
    for i in range(9):
        off=motor_off+8+4*i
        value=struct.unpack_from(">f",original,off)[0]
        if not math.isfinite(value) or value<=0:
            raise ValueError("Original BMW engine torque sample invalid")
        struct.pack_into(">f",modified,off,value*1.05)
    new_motor=bytes(modified[motor_off:motor_off+BMW_MOTOR_BYTES])
    if sha(new_motor)!=vectors[0]["output_engine_layout_sha256"]:
        raise ValueError("Synthetic stock BMW +5pct reference SHA mismatch")
    for i,(left,right) in enumerate(zip(original,modified)):
        if left!=right:changed_positions.append(i)
    if not changed_positions or not all(motor_off+8<=i<motor_off+44 for i in changed_positions):
        raise ValueError("Difference outside nine stock BMW torque samples")
    if len(modified)!=len(original) or modified[vlt_off:]!=original[vlt_off:]:
        raise ValueError("VLT/repacked export changed in torque-only diagnostic")
    if modified[BO:BO+bin_len][:BMW_MOTOR_BASE]!=original[BO:BO+bin_len][:BMW_MOTOR_BASE]:
        raise ValueError("BMW stock pvehicle or preceding BIN fields changed")
    ea_new=ea_data_hash(bytes(modified))
    if ea_new==0x296ad9ed:
        raise ValueError("Experimental resource hash identical to original unexpectedly")
    return bytes(modified),changed_positions,ea_new,sha(new_motor)

def audit():
    p572=json.loads(Path("docs/PRE572_PTBR_BMW_PRIVATE_PATCH_BUNDLE_METADATA.json").read_text())
    p578=json.loads(Path("docs/PRE578_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (p572.get("status")!="AUDIT_OK" or p578.get("status")!="AUDIT_OK"
        or p572.get("translated_original_ZZDATA4_full_sha256")!=EXPECTED_PTBR_ZZDATA4_SHA):
        raise ValueError("Prior patch source and canonical report missing")
    synthetic,changed,crc,engine_sha=build_motor_only_variant()
    sess=session()
    entries,central_sha=zip_directory(sess)
    idx=[x for x in entries if x["name"].upper().endswith("NFS/ZDIR.BIN")]
    data=[x for x in entries if x["name"].upper().endswith("NFS/ZZDATA4.BIN")]
    if len(idx)!=1 or len(data)!=1:raise ValueError("PTBR original ZIP members ambiguous")
    original_index=member_zdir(sess,idx[0])
    if sha(original_index)!=ZDIR_SHA:raise ValueError("PTBR ZDIR differs from original source")
    h,arch,sector,total,size,old_crc=struct.unpack_from("<IiIIiI",original_index,ZDIR_ROW*24)
    if (h,arch,sector,total,size,old_crc)!=(0x9775379a,4,0,0,OLD_RESOURCE_BYTES,0x296ad9ed):
        raise ValueError("Translated target original index not PRE561")
    candidate_index=bytearray(original_index)
    struct.pack_into("<I",candidate_index,ZDIR_ROW*24+20,crc)
    if (candidate_index[:ZDIR_ROW*24]!=original_index[:ZDIR_ROW*24] or
        candidate_index[(ZDIR_ROW+1)*24:]!=original_index[(ZDIR_ROW+1)*24:]):
        raise ValueError("Non-BMW ZDIR rows changed")
    changed_index_offsets=[i for i,(x,y) in enumerate(zip(original_index,candidate_index)) if x!=y]
    if not changed_index_offsets or not all(ZDIR_ROW*24+20<=i<ZDIR_ROW*24+24 for i in changed_index_offsets):
        raise ValueError("ZDIR changes extend outside one checksum")
    fragment=synthetic+bytes(RESERVED-OLD_RESOURCE_BYTES)
    full=stream_full_archive_digest(sess,data[0],fragment)
    if full["translated_original_ZZDATA4_full_sha256"]!=EXPECTED_PTBR_ZZDATA4_SHA:
        raise ValueError("Original PTBR full archive changed")
    helpers.PATCH_FOLDER=PATCH_FOLDER
    d=drive_client()
    folder,created=helpers.drive_folder(d)
    zz=ensure_private_file(d,folder,"PRE580_ZZDATA4_FIRST341_TORQUE_ONLY.bin",fragment)
    z=ensure_private_file(d,folder,"PRE580_ZDIR_TORQUE_ONLY.bin",bytes(candidate_index))
    return {
      "stage":"PRE580_PTBR_BMW_STOCK_MOTOR_TORQUE_ONLY_CONTROL_FRAGMENT",
      "status":"AUDIT_OK",
      "folder_id":folder,"folder_newly_created":created,
      "fragment_original_ZDIR_crc32":f"{old_crc:08x}",
      "fragment_torque_only_ZDIR_EA_crc32":f"{crc:08x}",
      "ZDIR_original_SHA256":ZDIR_SHA,
      "ZDIR_fragment":z,
      "ZZDATA4_first_341_sectors_fragment":zz,
      "changed_resource_byte_count":len(changed),
      "changed_resource_byte_range":[min(changed),max(changed)],
      "new_engine_layout_sha256":engine_sha,
      "source_VPAK_bytes":OLD_RESOURCE_BYTES,
      "candidate_VPAK_bytes":len(synthetic),
      "original_VLT_bytes_unchanged":True,
      "original_BIN_non_motor_bytes_unchanged":True,
      "original_pvehicle_upgrade_counter_unchanged":True,
      "new_engine_collection_added":False,
      "new_ExpN_RefSpec_PtrN_added":False,
      "torque_multiplier_synthetic":1.05,
      "full_modified_ZZDATA4_was_written_to_Drive":False,
      "user_phone_files_modified":False,
      "guest_loader_executed":False,
      "MARCEK_save_load_with_candidate_proven":False,
      "BMW_buyable_upgrade_enabled":False,
      "APK_built":False,"save_modified":False,
      **full
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={
      "stage":"PRE580_PTBR_BMW_STOCK_MOTOR_TORQUE_ONLY_CONTROL_FRAGMENT",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "user_phone_files_modified":False,"APK_built":False,
      "save_modified":False,"guest_loader_executed":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE580_STATUS",r["status"],flush=True)
    print("PRE580_PHONE_UNCHANGED",r.get("user_phone_files_modified",False) is False,flush=True)
    print("PRE580_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
