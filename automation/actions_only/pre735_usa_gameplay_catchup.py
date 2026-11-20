#!/usr/bin/env python3
"""PRE735: authenticate GLOBAL/GAMEPLAY.BIN resource in original X360 USA ISO.

Candidate source based on GManager::Init("GLOBAL\\GAMEPLAY.BIN") from
dbalatoni13/nfsmw original reconstructed source. Read-only, private report.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from pre105_read_settings_source import drive_client
from pre733_iso_range_catchup import (RemoteRange, ISO_ID, EXPECTED_SIZE,
                                     find_volume, all_files, REPORT_FOLDER, SECTOR)
from pre732_private_pre99 import scan_stream

TARGET = "GLOBAL\\GAMEPLAY.BIN"
TARGET_HASH = 0x51EAFEC3
EXPECTED_ZDIR_BYTES = 33360
EXPECTED_ZDIR_SHA = "96c275a628f24e101f4fad9cb0531594c31effd870f64de3056c0e958e362ae6"
LIMIT = 48 * 1024 * 1024


def name_hash(name):
    h = 0xffffffff
    for c in name.upper():
        h = (33*h + ord(c)) & 0xffffffff
    return h


def audit(drive):
    if name_hash(TARGET) != TARGET_HASH:
        raise ValueError("Filename hash regression")
    meta = drive.files().get(fileId=ISO_ID, fields="id,size").execute()
    if meta.get("id") != ISO_ID or int(meta.get("size", 0)) != EXPECTED_SIZE:
        raise ValueError("Pinned USA ISO metadata mismatch")
    reader = RemoteRange(drive._http.credentials, ISO_ID, EXPECTED_SIZE)
    base, root_sect, root_size = find_volume(reader)
    entries = all_files(reader, base, root_sect, root_size)
    nfs = {name.upper(): (sector, size) for name,sector,size in entries
           if name.upper().startswith("NFS/")}
    zdir_loc = nfs.get("NFS/ZDIR.BIN")
    if not zdir_loc or zdir_loc[1] != EXPECTED_ZDIR_BYTES:
        raise ValueError("Original ZDIR entry not found")
    reader.seek(base + zdir_loc[0] * SECTOR)
    zdir = reader.read(zdir_loc[1])
    if hashlib.sha256(zdir).hexdigest() != EXPECTED_ZDIR_SHA:
        raise ValueError("Original USA ZDIR SHA mismatch")
    rows = []
    for i, row in enumerate(struct.iter_unpack("<IiIIiI", zdir)):
        name_hash_u32, archive, sector, total, size, checksum = row
        if name_hash_u32 == TARGET_HASH:
            rows.append({"index": i, "archive": archive, "sector": sector,
                         "total": total, "size": size, "checksum": checksum})
    if len(rows) not in (1, 2):
        raise ValueError("Unexpected gameplay resource count: %d" % len(rows))
    blobs = []
    locations = []
    for entry_i in rows:
        idx_i = entry_i["archive"]
        if not 0 <= idx_i <= 9:
            raise ValueError("Unexpected gameplay container number")
        archive_i = nfs.get(f"NFS/ZZDATA{idx_i}.BIN")
        if archive_i is None:
            raise ValueError("Expected ZZDATA not found")
        relative_i = entry_i["sector"] * SECTOR
        if not 16 <= entry_i["size"] <= LIMIT or relative_i + entry_i["size"] > archive_i[1]:
            raise ValueError("Gameplay resource invalid/oversized bounds")
        reader.seek(base + archive_i[0] * SECTOR + relative_i)
        raw_i = reader.read(entry_i["size"])
        if len(raw_i) != entry_i["size"]:
            raise ValueError("Gameplay resource truncated")
        blobs.append(raw_i)
        locations.append({**entry_i, "sha256": hashlib.sha256(raw_i).hexdigest()})
    print("PRE735_RESOURCE_CANDIDATES=" + json.dumps(locations, sort_keys=True), flush=True)
    if any(x != blobs[0] for x in blobs[1:]):
        raise ValueError("Gameplay entries differ bytewise; cannot select authoritative copy")
    entry = rows[0]
    idx = entry["archive"]
    blob = blobs[0]
    matches = scan_stream(io.BytesIO(blob))
    rec = {
        "stage": "PRE735_AUTHENTICATED_USA_GAMEPLAY_RESOURCE_READONLY",
        "status": "AUDIT_OK",
        "source": "USA ISO in user's private Drive",
        "source_full_iso_sha_verified": False,
        "xvdvfs_and_zdir_verified": True,
        "target_resource_name": TARGET,
        "target_name_hash": hex(TARGET_HASH),
        "zdir_index": entry["index"],
        "duplicate_locations_verified_bytewise_equal": len(blobs) > 1,
        "resource_locations": locations,
        "archive_index": idx, "resource_size": len(blob),
        "resource_sha256": hashlib.sha256(blob).hexdigest(),
        "resource_head_magic_hex": blob[:8].hex(),
        "resource_is_vpak": blob[:4] == b"VPAK",
        "candidate_hashes_found": matches,
        "runtime_catchup_values_confirmed": False,
        "gameplay_modified": False,
        "apk_built": False,
        "signing_material_accessed": False,
        "remote_range_requests": reader.requests,
    }
    if blob[:4] == b"VPAK":
        vaults, nameoff, namelen = struct.unpack_from("<III", blob,4)
        if not (0 < vaults <= 64 and 16 + 20*vaults <= len(blob) and
                nameoff + namelen <= len(blob)):
            raise ValueError("Invalid gameplay VPAK metadata")
        vl = []
        for j in range(vaults):
            nameidx, binlen, vltlen, binoff, vltoff = struct.unpack_from("<IIIII",blob,16+j*20)
            if binoff+binlen>len(blob) or vltoff+vltlen>len(blob):
                raise ValueError("VPAK subsection out of range")
            bound = nameoff + nameidx
            stop = blob.find(b"\x00",bound,min(len(blob),nameoff+namelen))
            if bound < nameoff or stop < 0 or stop - bound > 80:
                raise ValueError("VPAK vault name invalid")
            vaultname = blob[bound:stop].decode("ascii","replace")
            binbytes, vltbytes = blob[binoff:binoff+binlen],blob[vltoff:vltoff+vltlen]
            vl.append({"name": vaultname,"bin_bytes":binlen,"vlt_bytes":vltlen,
                       "bin_head":binbytes[:8].hex(),"vlt_head":vltbytes[:8].hex(),
                       "race_bin_ascii_occurrences": binbytes.lower().count(b"race_bin")})
        rec["vaults"] = vl
    return rec


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    drive=drive_client()
    report=audit(drive)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE735_GAMEPLAY_RESOURCE_SHA256="+report["resource_sha256"])
    print("PRE735_GAMEPLAY_RESOURCE_SIZE="+str(report["resource_size"]))
    print("PRE735_HASH_RECORD_COUNT="+str(len(report["candidate_hashes_found"])))
    filename="NFSMW_PRE735_GAMEPLAY_ISO_USA_READONLY_REPORT.json"
    upl=drive.files().create(
        body={"name":filename,"parents":[REPORT_FOLDER],"mimeType":"application/json"},
        media_body=MediaFileUpload(str(args.report),mimetype="application/json"),
        fields="id,name,parents").execute()
    if upl.get("name")!=filename or REPORT_FOLDER not in upl.get("parents",[]):
        raise ValueError("Private Drive report upload did not verify")
    print("PRE735_REPORT_DRIVE_ID="+upl["id"])
    print("PRE735_NO_MODIFICATIONS_NO_APK_NO_SIGNING")

if __name__=="__main__":
    main()
