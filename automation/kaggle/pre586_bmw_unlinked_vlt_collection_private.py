#!/usr/bin/env python3
"""PRE586: structural-only VLT diagnostic in scratch, no BMW pvehicle activation.
Based on PRE502 authentic experimental VPAK with new synthetic collection,
but restores BOTH existing BMW pvehicle engine counter and original RefSpec
fixup pointer. If this loads the career, remaining failure likely active
pvehicle linkage/counter rather than just VLT/ExpN/PtrN parser presence.
No APK, save, original PTBR ZIP or original phone game bytes are modified.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre502_bmw_engine_combined_level1_scratch import (
  audit as scratch_build, lookup_ptrn, PTR_START, EXP_LEN, EXP_START,
  OLD_BIN_LEN, OLD_VLT_LEN)
from pre494_bmw_engine_scratch_refspec_relocation import get_field,find_ptr_record
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import member_zdir,zip_directory,ZDIR_SHA
import pre572_prepare_ptbr_bmw_private_patch_fragments as helpers
from pre572_prepare_ptbr_bmw_private_patch_fragments import stream_full_archive_digest,ensure_private_file
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre586/report.json")
FOLDER="PRE586_BMW_NEW_COLLECTION_UNLINKED_VLT_DIAG_20261109"
ATTR_LEN=698004
ORIG_LEN=697856
RESERVED=698368
ROW=805
ORIG_REF=256660
ENGINE_COUNTER=256488
VPAK_BO=128
SOURCE_INDEX_SHA=ZDIR_SHA
PRE502_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
def sha(b):return hashlib.sha256(b).hexdigest()

def variant(scratch,pre502):
    if (len(scratch)!=ATTR_LEN or sha(scratch)!=PRE502_SHA
        or pre502.get("status")!="AUDIT_OK"
        or pre502.get("scratch_export_count")!=2400
        or pre502.get("scratch_BMW_pvehicle_engine_upgrade_limit_one") is not True
        or pre502.get("source_vpak_bytes")!=ORIG_LEN
        or pre502.get("new_engine_ExpN_RefSpec_PtrN_reparsed") is not True):
        raise ValueError("PRE502 combined scratch and report not trusted")
    reader,p=locate()
    original=reader.read(p["absolute_offset"],p["size"])
    if len(original)!=ORIG_LEN or sha(original)!=EXPECTED_VPAK_SHA:
        raise ValueError("Original PAL/translated VPAK not authenticated")
    _,ob,ov,obo,ovo=struct.unpack_from("<IIIII",original,16)
    _,nb,nv,nbo,nvo=struct.unpack_from("<IIIII",scratch,16)
    if ((ob,ov,obo,ovo)!=(OLD_BIN_LEN,OLD_VLT_LEN,VPAK_BO,355136)
        or (nbo,nv)!=(VPAK_BO,OLD_VLT_LEN+68)
        or nvo+nv!=len(scratch)):
        raise ValueError("VLT and BIN layout unexpected")
    old_vlt=original[ovo:ovo+ov]
    old_field=get_field(old_vlt)
    old_record=find_ptr_record(old_vlt,old_field)
    old_ptr=old_vlt[PTR_START:]
    if struct.unpack_from(">I",old_ptr,old_record+8)[0]!=ORIG_REF:
        raise ValueError("Original stock BMW engine fixup not 256660")
    candidate=bytearray(scratch)
    count_at=VPAK_BO+ENGINE_COUNTER
    if struct.unpack_from(">i",candidate,count_at)[0]!=1:
        raise ValueError("PRE502 combined engine upgrade counter no longer 1")
    struct.pack_into(">i",candidate,count_at,0)
    ptr_new_at=PTR_START+36+20
    new_vlt=scratch[nvo:nvo+nv]
    if new_vlt[ptr_new_at:ptr_new_at+4]!=b"PtrN":
        raise ValueError("New PtrN after ExpN expansion missing")
    ptr_fixup_relative=ptr_new_at+old_record+8
    ptr_fixup_absolute=nvo+ptr_fixup_relative
    old_destination=struct.unpack_from(">I",candidate,ptr_fixup_absolute)[0]
    if old_destination!=pre502["new_two_ref_array_bin_relative_offset"]:
        raise ValueError("PRE502 relocated pvehicle RefSpec pointer changed")
    struct.pack_into(">I",candidate,ptr_fixup_absolute,ORIG_REF)
    out=bytes(candidate)
    changes=[i for i,(x,y) in enumerate(zip(scratch,out)) if x!=y]
    if not changes or not all(
         count_at<=i<count_at+4 or ptr_fixup_absolute<=i<ptr_fixup_absolute+4
         for i in changes):
        raise ValueError("Candidate differs from PRE502 outside pvehicle counter/fixup")
    cand_vlt=out[nvo:nvo+nv]
    pointers=lookup_ptrn(cand_vlt,ptr_new_at, len(cand_vlt)-ptr_new_at)
    if pointers.get(old_field)!=[(3,1,ORIG_REF)]:
        raise ValueError("Unlinked BMW pvehicle fixup was not restored")
    new_col=pre502["new_engine_collection_vlt_relative_offset"]
    layout=pre502["new_engine_layout_bin_relative_offset"]
    if pointers.get(new_col+28)!=[(3,1,layout)]:
        raise ValueError("New but unlinked physical engine collection missing")
    if (out[VPAK_BO+ENGINE_COUNTER:VPAK_BO+ENGINE_COUNTER+4]
        !=original[VPAK_BO+ENGINE_COUNTER:VPAK_BO+ENGINE_COUNTER+4]
        or out[nvo+ptr_new_at:nvo+ptr_new_at+4]!=b"PtrN"):
        raise ValueError("BMW upgrade count or PtrN invalid")
    if out[VPAK_BO+ORIG_REF:VPAK_BO+ORIG_REF+20]!=original[VPAK_BO+ORIG_REF:VPAK_BO+ORIG_REF+20]:
        raise ValueError("Existing stock BMW pvehicle engine reference bytes changed")
    # Distinguish this experiment from original and combined.
    crc=ea_data_hash(out)
    if crc in (0x296ad9ed,0x4d05584a):
        raise ValueError("Candidate EA checksum unexpectedly equals old/combined")
    return out,crc,changes,old_destination,ptr_fixup_relative,pre502

def audit():
    p580=json.loads(Path("docs/PRE580_PTBR_BMW_MOTOR_ONLY_PRIVATE_CONTROL_METADATA.json").read_text())
    p581=json.loads(Path("docs/PRE581_SHEVERY_TORQUE_ONLY_STATIC_PREFLIGHT_RESULT.json").read_text())
    p585=json.loads(Path("docs/PRE585_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (any(x.get("status")!="AUDIT_OK" for x in (p580,p581,p585))
        or p580.get("candidate_VPAK_bytes")!=ORIG_LEN
        or p580.get("changed_resource_byte_count")!=24
        or p580.get("original_VLT_bytes_unchanged") is not True
        or p585.get("new_handoff_readback_verified") is not True
        or p581.get("actual_device_experiment_executed") is not False):
        raise ValueError("PRE580, PRE581, PRE585 preconditions unverified")
    s=session()
    entries,central=zip_directory(s)
    inds=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
    datas=[e for e in entries if e["name"].upper().endswith("NFS/ZZDATA4.BIN")]
    if len(inds)!=1 or len(datas)!=1:raise ValueError("PTBR archive/index ambiguous")
    zdir=member_zdir(s,inds[0])
    if sha(zdir)!=SOURCE_INDEX_SHA:raise ValueError("Original translated index SHA changed")
    name,arch,sector,total,size,oldcrc=struct.unpack_from("<IiIIiI",zdir,ROW*24)
    if (name,arch,sector,total,size,oldcrc)!=(0x9775379a,4,0,0,ORIG_LEN,0x296ad9ed):
        raise ValueError("PTBR ZDIR original BMW resource record not as expected")
    def consume(scratch:bytes):
        # Rebuild the same verified PRE502 scratch and remove only its two
        # *active* BMW pvehicle changes, retaining the unreferenced new VLT collection.
        # Local scope; all bytes stay private.
        built=variant(scratch,meta)
        proposed,crc,changes,oldtarget,fixup_off,source=built
        newindex=bytearray(zdir)
        struct.pack_into("<iI",newindex,ROW*24+16,len(proposed),crc)
        if (newindex[:ROW*24]!=zdir[:ROW*24] or
            newindex[(ROW+1)*24:]!=zdir[(ROW+1)*24:]):
            raise ValueError("Unexpected ZDIR record mutation")
        candidate_region=proposed+bytes(RESERVED-len(proposed))
        summary=stream_full_archive_digest(s,datas[0],candidate_region)
        helpers.PATCH_FOLDER=FOLDER
        d=drive_client()
        folder,new=helpers.drive_folder(d)
        indfile=ensure_private_file(d,folder,"PRE586_ZDIR_VLT_NEW_COLLECTION_UNLINKED.bin",bytes(newindex))
        datafile=ensure_private_file(d,folder,"PRE586_ZZDATA4_FIRST341_UNLINKED_VLT.bin",candidate_region)
        return {
          "folder_id":folder,"folder_newly_created":new,
          "ZDIR_fragment":indfile,
          "ZZDATA4_first_341_sectors_fragment":datafile,
          "candidate_VPAK_size":len(proposed),
          "candidate_VPAK_sha256":sha(proposed),
          "candidate_EA_crc32":f"{crc:08x}",
          "PRE502_combined_synthetic_source_sha256":PRE502_SHA,
          "PRE502_changed_bytes_reverted":len(changes),
          "PRE502_changed_offsets_reverted":changes,
          "original_BMW_pvehicle_engine_upgrade_counter_retained":True,
          "original_BMW_pvehicle_ref_fixup_restored":True,
          "new_unlinked_VLT_engine_collection_preserved":True,
          "scratch_new_export_count":2400,
          "unlinked_collection_name_missing_StrE":source.get("new_collection_name_missing_original_StrE"),
          "guest_loader_support_proven":False,
          "BMW_tuning_enabled":False,
          "save_load_with_candidate_proven":False,
          "phone_game_assets_modified":False,
          "APK_built":False,
          "save_modified":False,
          **summary
        }
    # Build once, but callback needs the full report meta. PRE502 consumes
    # before its report is finalized, so reconstruct only keys from canonical
    # authenticated PRE502 report already in repo.
    meta=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    if meta.get("status")!="AUDIT_OK" or meta.get("scratch_vpak_bytes")!=ATTR_LEN:
        raise ValueError("PRE502 report unavailable for independent repair")
    rebuilt=scratch_build(consume_scratch=consume)
    if rebuilt.get("status")!="AUDIT_OK" or rebuilt.get("scratch_vpak_bytes")!=ATTR_LEN:
        raise ValueError("PRE502 rebuilt source invalid")
    extra=rebuilt.get("_private_scratch_analysis")
    if not extra or not extra.get("original_BMW_pvehicle_ref_fixup_restored"):
        raise ValueError("Unlinked structural experiment failed verification")
    return {"stage":"PRE586_BMW_UNLINKED_VLT_COLLECTION_PRIVATE_GATE",
       "status":"AUDIT_OK",**extra,
       "subject_save_isolation_required":False,
       "full_game_data_patch_applied_to_phone":False,
       "original_translated_zip_modified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE586_BMW_UNLINKED_VLT_COLLECTION_PRIVATE_GATE",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
      "full_game_data_patch_applied_to_phone":False,"original_translated_zip_modified":False,
      "phone_game_assets_modified":False,"save_modified":False,"APK_built":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE586_STATUS",r["status"],flush=True)
    print("PRE586_NEW_UNLINKED_COLLECTION",r.get("new_unlinked_VLT_engine_collection_preserved",False),flush=True)
    print("PRE586_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
