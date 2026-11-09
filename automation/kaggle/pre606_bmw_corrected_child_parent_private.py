#!/usr/bin/env python3
"""PRE606: reconstruct PRE605 BMW child engine corrected-parent VPAK from
authenticated original PRE502 and build private PTBR patch fragments with
strict full archive streaming hash. Never apply to user's phone or publish
original game data.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre502_bmw_engine_combined_level1_scratch import audit as rebuild,NEW_HASH,ENGINE_CLASS,EXP_START,hash32
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import member_zdir,zip_directory,ZDIR_SHA
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre572_prepare_ptbr_bmw_private_patch_fragments import stream_full_archive_digest,ensure_private_file
import pre572_prepare_ptbr_bmw_private_patch_fragments as helpers
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre606/report.json")
FOLDER="PRE606_BMW_ENGINE_CHILD_PARENT_CORRECTED_20261109"
ORIGINAL_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
CORRECTED_SHA="11c122bf9b32011fd3955498517e51f2f1f11551bc2bbd9f448201bc4ef862f3"
EXPECTED_CRC="31aef5d7"
PTBR_ORIG_ARCHIVE="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
ROW=805
ORIG_LEN=697856
VPAK_LEN=698004
REGION=698368

def sha(v):return hashlib.sha256(v).hexdigest()
def audit():
    p604=json.loads(Path("docs/PRE604_BMW_PARENT_ORIGINAL_PUNTO_STRE_READONLY.json").read_text())
    p605=json.loads(Path("docs/PRE605_BMW_ENGINE_PARENT_ONLY_RAM_RESULT.json").read_text())
    p603=json.loads(Path("docs/PRE603_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (any(x.get("status")!="AUDIT_OK" for x in (p603,p604,p605))
        or p605.get("candidate_parent_adjusted_VPAK_sha256")!=CORRECTED_SHA
        or p605.get("candidate_parent_adjusted_EA_checksum_hex")!=EXPECTED_CRC
        or p605.get("BMW_engine_counter_still_one") is not True
        or p605.get("all_other_PRE502_VPAK_bytes_unchanged") is not True
        or p604.get("original_Punto_second_engine_absent_StrE") is not True
        or p604.get("candidate_parent_is_default") is not True):
        raise ValueError("PRE604-PRE605 controlled source validation missing")
    s=session()
    entries,_=zip_directory(s)
    indexes=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
    archives=[e for e in entries if e["name"].upper().endswith("NFS/ZZDATA4.BIN")]
    if len(indexes)!=1 or len(archives)!=1:raise ValueError("Original translated ZIP ambiguity")
    index=member_zdir(s,indexes[0])
    if sha(index)!=ZDIR_SHA:raise ValueError("Original ZDIR checksum differs")
    old_record=struct.unpack_from("<IiIIiI",index,ROW*24)
    if old_record!=(0x9775379a,4,0,0,ORIG_LEN,0x296ad9ed):
        raise ValueError("Original translated attributes resource record incorrect")
    def use_scratch(scratch):
        if len(scratch)!=VPAK_LEN or sha(scratch)!=ORIGINAL_SHA:
            raise ValueError("Authenticated PRE502 source VPAK changed")
        _,bl,vl,bo,vo=struct.unpack_from("<IIIII",scratch,16)
        if bl!=355088 or vl!=342788 or vo+vl!=len(scratch):
            raise ValueError("PRE502 VPAK geometry changed")
        pos=vo+EXP_START+8
        if struct.unpack_from(">III",scratch,vo+EXP_START)!=(NEW_HASH,ENGINE_CLASS,hash32("default")):
            raise ValueError("Expected new child default parent not found")
        new=bytearray(scratch)
        struct.pack_into(">I",new,pos,hash32("bmwm3gtr"))
        new=bytes(new)
        if sha(new)!=CORRECTED_SHA or f"{ea_data_hash(new):08x}"!=EXPECTED_CRC:
            raise ValueError("PRE605 corrected-parent SHA/EA checksum changed")
        if struct.unpack_from(">i",new,128+256488)[0]!=1:
            raise ValueError("Engine upgrade counter not preserved at 1")
        diffs=[i for i,(x,y) in enumerate(zip(scratch,new)) if x!=y]
        if diffs!=[520072,520073,520074,520075]:
            raise ValueError("Corrected experiment must change exactly 4 parent bytes")
        z=bytearray(index)
        struct.pack_into("<iI",z,ROW*24+16,len(new),int(EXPECTED_CRC,16))
        if z[:ROW*24]!=index[:ROW*24] or z[(ROW+1)*24:]!=index[(ROW+1)*24:]:
            raise ValueError("Non-target ZDIR record altered")
        region=new+bytes(REGION-len(new))
        result=stream_full_archive_digest(s,archives[0],region)
        if result["translated_original_ZZDATA4_full_sha256"]!=PTBR_ORIG_ARCHIVE:
            raise ValueError("Complete original translated archive fingerprint differs")
        helpers.PATCH_FOLDER=FOLDER
        drive=drive_client()
        folder,created=helpers.drive_folder(drive)
        zp=ensure_private_file(drive,folder,"PRE606_ZDIR_BMW_CHILD_PARENT_CORRECTED.bin",bytes(z))
        dp=ensure_private_file(drive,folder,"PRE606_ZZDATA4_FIRST341_BMW_PARENT_CORRECTED.bin",region)
        return {
          "folder_id":folder,"folder_newly_created":created,
          "ZDIR_fragment":zp,"ZZDATA4_first_341_sectors_fragment":dp,
          "candidate_VPAK_sha256":sha(new),"candidate_VPAK_bytes":len(new),
          "candidate_EA_crc32":EXPECTED_CRC,
          "candidate_parent_hash":"cd88083f",
          "candidate_engine_counter":1,
          "candidate_BMW_two_ref_list_preserved":True,
          "pre502_comparison_parent_only_4_bytes":diffs,
          "experiment_not_functional_tuning_proof":True,
          "phone_guest_tested":False,
          "user_game_files_modified":False,
          "user_save_modified":False,
          "APK_modified":False,
          **result
        }
    b=rebuild(consume_scratch=use_scratch)
    if b.get("status")!="AUDIT_OK":raise ValueError("PRE502 reconstruction failed")
    meta=b.get("_private_scratch_analysis")
    if not meta or meta.get("candidate_parent_hash")!="cd88083f":
        raise ValueError("Staged private fragments missing")
    return {"stage":"PRE606_BMW_DERIVED_ENGINE_PARENT_CORRECTED_PRIVATE_PTBR_FRAGMENTS","status":"AUDIT_OK",**meta}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={
      "stage":"PRE606_BMW_DERIVED_ENGINE_PARENT_CORRECTED_PRIVATE_PTBR_FRAGMENTS",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "user_game_files_modified":False,"user_save_modified":False,"APK_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE606_STATUS",r["status"]);print("PRE606_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
