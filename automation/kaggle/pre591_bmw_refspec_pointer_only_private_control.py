#!/usr/bin/env python3
"""PRE591: isolated BMW RefSpec active pointer diagnostic. BMW engine count remains zero.
VLT has new unused collection. No release APK, game/save source write, or actual
guest test. Rebuild PRE586 control from authenticated PRE502 source, change
*only* the PRE586 restored pvehicle RefSpec fixup into the original PRE502
two-ref array pointer. Safety gate checks all related bytes and archive hash.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre502_bmw_engine_combined_level1_scratch import audit as scratch_build,lookup_ptrn
from pre586_bmw_unlinked_vlt_collection_private import (
 variant as unlinked_variant,ATTR_LEN,ORIG_LEN,RESERVED,ROW,
 ENGINE_COUNTER,VPAK_BO,FOLDER as PRE586_FOLDER,ORIG_REF,PRE502_SHA)
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import member_zdir,zip_directory,ZDIR_SHA
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre572_prepare_ptbr_bmw_private_patch_fragments import stream_full_archive_digest,ensure_private_file
import pre572_prepare_ptbr_bmw_private_patch_fragments as helpers
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre591/report.json")
FOLDER="PRE591_BMW_REFSPEC_POINTER_ACTIVE_COUNT_ZERO_20261109"
EXPECTED_PRE586_SHA="a7e37cd5679f8a25d552049d9d0324b81fb74abe3b87c81a65348dbaa9fff7d7"
EXPECTED_PTBR_ARCHIVE_SHA="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
def sha(b):return hashlib.sha256(b).hexdigest()

def make_pointer_only(scratch,meta):
    unlinked,crc_unlinked,changes,orig_ptr_new_target,ptr_relative,source=unlinked_variant(scratch,meta)
    if (len(unlinked)!=ATTR_LEN or sha(unlinked)!=EXPECTED_PRE586_SHA
        or crc_unlinked!=0x820a01ba
        or len(changes)!=4):
        raise ValueError("PRE586 proven unlinked control bytes do not match")
    _,bin_len,vlt_len,bo,vltoff=struct.unpack_from("<IIIII",unlinked,16)
    if (bin_len<355000 or bo!=VPAK_BO or
        vltoff+vlt_len!=len(unlinked)):
        raise ValueError("PRE586 binary layout altered")
    offset=vltoff+ptr_relative
    if struct.unpack_from(">I",unlinked,offset)[0]!=ORIG_REF:
        raise ValueError("PRE586 pointer no longer points to stock reference")
    if orig_ptr_new_target!=source["new_two_ref_array_bin_relative_offset"]:
        raise ValueError("PRE502 two-ref array pointer provenance missing")
    candidate=bytearray(unlinked)
    struct.pack_into(">I",candidate,offset,orig_ptr_new_target)
    candidate=bytes(candidate)
    changed_from_unlinked=[i for i,(a,b) in enumerate(zip(unlinked,candidate)) if a!=b]
    if (not changed_from_unlinked or
        not all(offset<=i<offset+4 for i in changed_from_unlinked)
        or len(changed_from_unlinked)>4):
        raise ValueError("PRE591 differs from PRE586 outside pointer fixup")
    # PRE591 must be the original PRE502 scratch with *only the upgrade count*
    # reset to 0. No other resources may differ from authenticated source.
    if len(candidate)!=len(scratch):raise ValueError("VPAK length changed")
    diff_pre502=[i for i,(a,b) in enumerate(zip(scratch,candidate)) if a!=b]
    if diff_pre502!=[VPAK_BO+ENGINE_COUNTER+3]:
        raise ValueError("PRE591 differs from PRE502 outside one counter byte")
    if struct.unpack_from(">i",candidate,VPAK_BO+ENGINE_COUNTER)[0]!=0:
        raise ValueError("BMW upgrade counter not zero")
    if struct.unpack_from(">I",candidate,offset)[0]!=orig_ptr_new_target:
        raise ValueError("BMW active RefSpec pointer not pointing to two-ref array")
    if candidate[vltoff:offset]!=unlinked[vltoff:offset] or candidate[offset+4:]!=unlinked[offset+4:]:
        raise ValueError("Non-target VLT bytes differ from PRE586")
    p=ea_data_hash(candidate)
    if p in (0x296ad9ed,0x820a01ba,0x4d05584a):
        raise ValueError("PRE591 checksum collision with original/other tests")
    return candidate,p,offset,changed_from_unlinked,diff_pre502,orig_ptr_new_target

def audit():
    prev=json.loads(Path("docs/PRE586_PTBR_BMW_UNLINKED_VLT_PRIVATE_METADATA.json").read_text())
    ci=json.loads(Path("docs/PRE587_SHEVERY_UNLINKED_VLT_STATIC_PREFLIGHT_RESULT.json").read_text())
    handoff=Path("docs/PRE590_HANDOFF_PRE587_LIVE_UNLINKED_VLT_MARCEK_SUCCESS_20261109.md").read_text(encoding="utf-8")
    pre502=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    if (prev.get("status")!="AUDIT_OK" or ci.get("status")!="AUDIT_OK"
        or prev.get("candidate_VPAK_sha256")!=EXPECTED_PRE586_SHA
        or prev.get("original_BMW_pvehicle_ref_fixup_restored") is not True
        or prev.get("original_BMW_pvehicle_engine_upgrade_counter_retained") is not True
        or ci.get("actual_device_experiment_executed") is not False
        or pre502.get("status")!="AUDIT_OK"
        or pre502.get("scratch_vpak_bytes")!=ATTR_LEN
        or "509900a226ef281ab92a8567d818cb38e5afdb98a434bc77d0216fea384a2957" not in handoff
        or "não há nesta terceira sessão" not in handoff.lower()):
        raise ValueError("PRE586/PRE587 and latest on-device log evidence not anchored")
    s=session()
    entries,_=zip_directory(s)
    z=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
    d=[e for e in entries if e["name"].upper().endswith("NFS/ZZDATA4.BIN")]
    if len(z)!=1 or len(d)!=1:raise ValueError("PTBR ZIP ZDIR and ZZDATA4 ambiguous")
    zdir=member_zdir(s,z[0])
    if sha(zdir)!=ZDIR_SHA:raise ValueError("PTBR ZDIR original identity differs")
    r=struct.unpack_from("<IiIIiI",zdir,ROW*24)
    if r!=(0x9775379a,4,0,0,ORIG_LEN,0x296ad9ed):
        raise ValueError("Original translated ATTRIBUTES location changed")
    def consume(scratch):
        out,ea,ptr_off,changed_vs_prev,changed_vs_pre502,active_dest=make_pointer_only(scratch,pre502)
        index=bytearray(zdir)
        struct.pack_into("<iI",index,ROW*24+16,len(out),ea)
        if (index[:ROW*24]!=zdir[:ROW*24] or
            index[(ROW+1)*24:]!=zdir[(ROW+1)*24:]):
            raise ValueError("Unrelated ZDIR records modified")
        frag=out+bytes(RESERVED-len(out))
        summary=stream_full_archive_digest(s,d[0],frag)
        if summary["translated_original_ZZDATA4_full_sha256"]!=EXPECTED_PTBR_ARCHIVE_SHA:
            raise ValueError("Original ZIP archive hash mismatches proven translated source")
        helpers.PATCH_FOLDER=FOLDER
        drive=drive_client()
        folder,new=helpers.drive_folder(drive)
        index_file=ensure_private_file(drive,folder,"PRE591_ZDIR_BMW_REFSPEC_POINTER_ONLY.bin",bytes(index))
        region_file=ensure_private_file(drive,folder,"PRE591_ZZDATA4_FIRST341_REFSPEC_POINTER_ONLY.bin",frag)
        return {
         "folder_id":folder,"folder_newly_created":new,
         "ZDIR_fragment":index_file,
         "ZZDATA4_first_341_sectors_fragment":region_file,
         "candidate_VPAK_size":len(out),
         "scratch_new_export_count":2400,
         "candidate_VPAK_sha256":sha(out),
         "candidate_EA_crc32":f"{ea:08x}",
         "pointer_fixup_vpak_offset":ptr_off,
         "pointer_changed_bytes_vs_PRE586":changed_vs_prev,
         "counter_byte_changed_vs_PRE502":changed_vs_pre502,
         "active_BMW_pvehicle_refspec_points_to_two_ref_array":True,
         "BMW_pvehicle_motor_upgrade_count_zero":True,
         "new_VLT_engine_collection_preserved":True,
         "new_engine_not_buyable":True,
         "full_phone_archive_not_written":True,
         "guest_loader_executed":False,
         "MARCEK_save_load_with_candidate_proven":False,
         "BMW_tuning_enabled":False,
         "original_translated_game_files_modified":False,
         "save_modified":False,"APK_built":False,
         **summary
        }
    rebuilt=scratch_build(consume_scratch=consume)
    if (rebuilt.get("status")!="AUDIT_OK" or
        rebuilt.get("scratch_vpak_bytes")!=ATTR_LEN):
        raise ValueError("PRE502 combined source rebuilt incorrectly")
    private=rebuilt.get("_private_scratch_analysis")
    if not private or private.get("active_BMW_pvehicle_refspec_points_to_two_ref_array") is not True:
        raise ValueError("RefSpec pointer-only candidate not independently verified")
    return {"stage":"PRE591_BMW_REFSPEC_ONLY_WITH_ZERO_MOTOR_COUNT_PRIVATE_CONTROL",
            "status":"AUDIT_OK",**private}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE591_BMW_REFSPEC_ONLY_WITH_ZERO_MOTOR_COUNT_PRIVATE_CONTROL",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "guest_loader_executed":False,"BMW_tuning_enabled":False,"save_modified":False,
      "original_translated_game_files_modified":False,"APK_built":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE591_STATUS",r["status"],flush=True)
    print("PRE591_POINTER_ONLY",r.get("active_BMW_pvehicle_refspec_points_to_two_ref_array",False),flush=True)
    print("PRE591_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
