#!/usr/bin/env python3
"""PRE566: isolated filesystem-backed readback of the translated BMW scratch.
Only in a temporary CI directory; not a playable game folder or a guest test.
Never change/export user game data, original ZIP, APK, credentials or saves.
"""
from __future__ import annotations
import argparse, hashlib, json, os, struct, tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import zip_directory, member_zdir, ZDIR_SHA
from pre502_bmw_engine_combined_level1_scratch import audit as build_scratch
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash

OUT = Path("/tmp/nfsmw-pre566/report.json")
ROW, TARGET_HASH, ARCHIVE, SECTOR = 805, 0x9775379a, 4, 0
SOURCE_SIZE, NEW_SIZE, REGION, ARCHIVE_BYTES = 697856, 698004, 698368, 401068032
SOURCE_CRC, NEW_CRC = 0x296ad9ed, 0x4d05584a
NEW_SHA = "d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
TRANSLATED_INDEX_SHA = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf"
EXPECTED_NEW_ROW_SHA = "728e02041249ed029026fcdd7a92f254b60f1669f81ebad45e57f53574481735"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_exact(fd: int, n: int, off: int) -> bytes:
    if n < 0 or off < 0: raise ValueError("negative read")
    out = bytearray()
    while len(out) < n:
        buf = os.pread(fd, n-len(out), off+len(out))
        if not buf: raise ValueError("unexpected end of scratch file")
        out.extend(buf)
    return bytes(out)

def audit():
    p564 = json.loads(Path("docs/PRE564_PTBR_BMW_SYNTHETIC_RAM_RESOURCE_LOOKUP_READONLY.json").read_text())
    p563 = json.loads(Path("docs/PRE563_PTBR_ZZDATA4_ATTRIBUTES_FIRST_REGION_READONLY.json").read_text())
    if (p564.get("status") != "AUDIT_OK"
        or p564.get("translated_source_index_row") != ROW
        or p564.get("translated_source_resource_sector") != SECTOR
        or p564.get("translated_virtual_synthetic_resource_SHA256") != NEW_SHA
        or p564.get("translated_virtual_EA_crc_hex") != f"{NEW_CRC:08x}"
        or p564.get("translated_virtual_ZDIR_record_SHA256") != EXPECTED_NEW_ROW_SHA
        or p564.get("real_guest_loader_executed") is not False
        or p563.get("status") != "AUDIT_OK"
        or p563.get("first_region_trailing_all_zero") is not True
        or p563.get("first_next_positive_ZZDATA4_sector_from_ZDIR") != 341
        or p563.get("translated_ZZDATA4_full_uncompressed_bytes") != ARCHIVE_BYTES):
        raise ValueError("Authenticated PRE563/PRE564 prerequisite mismatch")
    s = session()
    entries, _ = zip_directory(s)
    matches = [e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
    if len(matches) != 1: raise ValueError("Translated ZIP index ambiguous")
    zdir = member_zdir(s, matches[0])
    if len(zdir) != 33312 or sha(zdir) != TRANSLATED_INDEX_SHA or ZDIR_SHA != TRANSLATED_INDEX_SHA:
        raise ValueError("Translated original ZDIR fingerprint mismatch")
    old_row = struct.unpack_from("<IiIIiI", zdir, ROW*24)
    if old_row != (TARGET_HASH, ARCHIVE, SECTOR, 0, SOURCE_SIZE, SOURCE_CRC):
        raise ValueError("Translated source attributes row changed")
    if [i for i, x in enumerate(struct.iter_unpack("<IiIIiI", zdir))
        if x[0] == TARGET_HASH] != [ROW]:
        raise ValueError("Translated name hash is not unique")
    def verify_scratch(scratch):
        if len(scratch) != NEW_SIZE or sha(scratch) != NEW_SHA or ea_data_hash(scratch) != NEW_CRC:
            raise ValueError("PRE502 synthetic candidate mismatches pinned VPAK")
        updated = bytearray(zdir)
        struct.pack_into("<iI", updated, ROW*24+16, NEW_SIZE, NEW_CRC)
        if (sha(updated[ROW*24:(ROW+1)*24]) != EXPECTED_NEW_ROW_SHA
            or bytes(updated[:ROW*24]) != zdir[:ROW*24]
            or bytes(updated[(ROW+1)*24:]) != zdir[(ROW+1)*24:]):
            raise ValueError("Unexpected ZDIR mutation outside target record")
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre566_ephemeral_") as tmp:
            # NEVER place these files under a game path or expose them as a runnable game.
            nfs = Path(tmp) / "NFS"
            nfs.mkdir()
            zdir_path = nfs / "ZDIR.BIN"
            data_path = nfs / "ZZDATA4.BIN"
            with zdir_path.open("xb") as f:
                f.write(updated)
                f.flush()
            # Sparse scratch-only image: all other resources are intentionally absent.
            # It must never be copied to the phone or substituted for real ZZDATA4.
            with data_path.open("xb") as f:
                f.truncate(ARCHIVE_BYTES)
                f.seek(0)
                f.write(scratch)
                f.flush()
            if (zdir_path.stat().st_size != len(zdir)
                or data_path.stat().st_size != ARCHIVE_BYTES):
                raise ValueError("Scratch file sizes invalid")
            iz = os.open(zdir_path, os.O_RDONLY)
            idata = os.open(data_path, os.O_RDONLY)
            try:
                entry = struct.unpack("<IiIIiI", read_exact(iz, 24, ROW*24))
                if entry != (TARGET_HASH, ARCHIVE, SECTOR, 0, NEW_SIZE, NEW_CRC):
                    raise ValueError("File-backed ZDIR lookup mismatch")
                original_as_read = read_exact(iz, len(zdir), 0)
                if original_as_read[:ROW*24] != zdir[:ROW*24] or original_as_read[(ROW+1)*24:] != zdir[(ROW+1)*24:]:
                    raise ValueError("File-backed non-target ZDIR byte mismatch")
                data = read_exact(idata, entry[4], entry[2]*2048)
                pad = read_exact(idata, REGION-NEW_SIZE, NEW_SIZE)
                if (sha(data) != NEW_SHA or ea_data_hash(data) != entry[5]
                    or pad != bytes(REGION-NEW_SIZE)):
                    raise ValueError("File-backed physical resource readback mismatch")
                # A negative control: old index + new data must not validate.
                old_sized = read_exact(idata, SOURCE_SIZE, SECTOR*2048)
                old_index_rejects_candidate = ea_data_hash(old_sized) != SOURCE_CRC
                if not old_index_rejects_candidate:
                    raise ValueError("Old ZDIR checksum unexpectedly accepts new resource")
            finally:
                os.close(iz)
                os.close(idata)
        return {
            "file_backed_scratch_index_readback": True,
            "file_backed_scratch_resource_readback": True,
            "old_index_rejects_new_scratch_resource": True,
            "temporary_sparse_ZZDATA4_logical_bytes": ARCHIVE_BYTES,
            "temporary_sparse_ZZDATA4_non_target_resources_not_copied": True,
            "temporary_files_deleted_on_exit": True,
            "translated_attributes_index_row": ROW,
            "translated_attributes_sector": SECTOR,
            "synthetic_resource_sha256": NEW_SHA,
            "synthetic_resource_ea_checksum": f"{NEW_CRC:08x}",
            "remaining_zero_padding_bytes": REGION-NEW_SIZE,
        }
    rebuilt = build_scratch(consume_scratch=verify_scratch)
    proof = rebuilt.pop("_private_scratch_analysis", None)
    if (rebuilt.get("status") != "AUDIT_OK" or proof is None
        or rebuilt.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE502 synthetic rebuild proof invalid")
    return {
        "stage":"PRE566_PTBR_BMW_TEMPORARY_FILE_BACKED_READBACK_NOT_GUEST",
        "status":"AUDIT_OK",
        **proof,
        "real_guest_loader_executed":False,
        "V48_hostpath_execution_observed":False,
        "on_device_asset_overlay_ready":False,
        "safe_save_isolation_proven":False,
        "genuine_upgrade_purchase_validated":False,
        "BMW_tuning_enabled":False,
        "APK_built":False,
        "original_translated_game_file_written":False,
        "original_game_asset_uploaded_or_exported":False,
        "save_modified":False,
        "signing_material_accessed":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: report = audit()
    except Exception as e:
        report = {"stage":"PRE566_PTBR_BMW_TEMPORARY_FILE_BACKED_READBACK_NOT_GUEST",
                  "status":"FAILED","error_type":type(e).__name__,
                  "error":str(e)[:240],
                  "real_guest_loader_executed":False,
                  "safe_save_isolation_proven":False,
                  "BMW_tuning_enabled":False,
                  "APK_built":False,
                  "original_translated_game_file_written":False,
                  "original_game_asset_uploaded_or_exported":False,
                  "save_modified":False,"signing_material_accessed":False}
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE566_STATUS",report["status"],flush=True)
    print("PRE566_FILE_READBACK",report.get("file_backed_scratch_resource_readback",False),flush=True)
    print("PRE566_GUEST_LOADER",report["real_guest_loader_executed"],flush=True)
    print("PRE566_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
