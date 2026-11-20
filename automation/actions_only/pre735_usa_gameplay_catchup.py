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
        print("PRE735_VPAK_META=" + json.dumps({"vault_count":vaults,"name_offset":nameoff,"name_length":namelen,"blob_size":len(blob)}), flush=True)
        if not (0 < vaults <= 512 and 16 + 20*vaults <= len(blob) and
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
            vl.append({"name": vaultname, "bin_off": binoff, "vlt_off": vltoff,
                       "bin_bytes":binlen,"vlt_bytes":vltlen,
                       "bin_head":binbytes[:8].hex(),"vlt_head":vltbytes[:8].hex(),
                       "race_bin_ascii_occurrences": binbytes.lower().count(b"race_bin")})
        rec["vault_count"] = vaults
        rec["vaults"] = vl
        site_map = []
        for hit in matches:
            for off_text in hit["sample_offsets_hex"]:
                pos = int(off_text, 16)
                owners = []
                for v in vl:
                    for section, offsetkey, sizekey in (
                        ("BIN", "bin_off", "bin_bytes"),
                        ("VLT", "vlt_off", "vlt_bytes")):
                        rel = pos - v[offsetkey]
                        if 0 <= rel < v[sizekey]:
                            owners.append({"vault": v["name"], "section": section,
                                           "relative_offset_hex": hex(rel)})
                # Nearby header words retained only in private Drive report.
                words = [hex(int.from_bytes(blob[pos + k:pos + k + 4], "big"))
                         for k in (0, 4, 8, 12) if pos + k + 4 <= len(blob)]
                site_map.append({"attribute": hit["attribute"],
                                 "file_offset_hex": off_text, "owners": owners,
                                 "nearby_words_be": words})
        rec["attribute_hits_by_vault"] = site_map
        # PRE736: inspect ExpN collection boundaries on selected race/template vaults.
        # Only metadata is reported, not game bytes or decrypted ISO.
        from pre465_usa_bmw_vpak_inner_schema_readonly import hash32
        focus = {"gpcore", "race_bin_01", "race_bin_04", "race_bin_15"}
        focused = []
        for v in vl:
            if v["name"] not in focus:
                continue
            base_vlt = v["vlt_off"]
            section = blob[base_vlt:base_vlt + v["vlt_bytes"]]
            entries = []
            pos = 0
            while pos + 8 <= len(section):
                tag = section[pos:pos + 4]
                length = int.from_bytes(section[pos + 4:pos + 8], "big")
                if tag not in (b"DepN", b"StrN", b"DatN", b"ExpN", b"PtrN") or length < 8 or pos + length > len(section):
                    break
                entries.append({"tag":tag.decode("ascii"),"offset":pos,"length":length})
                pos += length
            exp_sections = [x for x in entries if x["tag"] == "ExpN"]
            if len(exp_sections) != 1:
                raise ValueError("Expected exactly one ExpN chunk in " + v["name"])
            exp = exp_sections[0]
            exp_start = exp["offset"]
            cnt = int.from_bytes(section[exp_start + 8:exp_start + 12],"big")
            if not 1 <= cnt <= 50000 or exp_start + 12 + 20 * cnt > exp_start + exp["length"]:
                raise ValueError("Invalid ExpN count in " + v["name"])
            bin_section = blob[v["bin_off"]:v["bin_off"]+v["bin_bytes"]]
            if bin_section[:4] != b"StrE":
                raise ValueError("Expected StrE table")
            string_block_end = int.from_bytes(bin_section[4:8], "big")
            if not (8 <= string_block_end <= len(bin_section)):
                raise ValueError("Invalid StrE table boundary")
            known_names = {}
            for name_raw in bin_section[8:string_block_end].split(b"\x00"):
                if not 1 <= len(name_raw) <= 128:
                    continue
                if any(x < 32 or x > 126 for x in name_raw):
                    continue
                value = name_raw.decode("ascii")
                known_names.setdefault(hash32(value),[]).append(value)
            attrs = [x for x in site_map if any(y["vault"] == v["name"] for y in x["owners"])]
            addr = [(x, int(x["file_offset_hex"],16) - base_vlt) for x in attrs]
            mapped = []
            collection_examples = []
            for i in range(cnt):
                expid,kind,unused,sz,record = struct.unpack_from(">IIIII",section,exp_start + 12 + 20 * i)
                if record+12 > exp_start or sz > 65536 or sz < 12 or record+sz > exp_start:
                    continue
                collection_hash, class_hash, parent_hash = struct.unpack_from(">III",section,record)
                hits = [{"attribute":hit["attribute"],"file_offset_hex":hit["file_offset_hex"],
                         "offset_inside_record": rel-record}
                        for hit,rel in addr if record <= rel < record+sz]
                if len(collection_examples) < 6:
                    collection_examples.append({"export_id":hex(expid),"kind":hex(kind),
                                                "collection_hash":hex(collection_hash),
                                                "class_hash":hex(class_hash),
                                                "parent_hash":hex(parent_hash),
                                                "record_size":sz})
                if hits:
                    mapped.append({"export_id":hex(expid),"kind":hex(kind),
                                   "collection_hash":hex(collection_hash),
                                   "collection_name_candidates":known_names.get(collection_hash, []),
                                   "class_hash":hex(class_hash),
                                   "parent_hash":hex(parent_hash),
                                   "parent_name_candidates":known_names.get(parent_hash, []),
                                   "record_offset_hex":hex(record),
                                   "record_size":sz,"matching_fields":hits})
            focused.append({"vault":v["name"],"chunks":entries,"export_count":cnt,
                            "mapped_field_count":sum(len(x["matching_fields"]) for x in mapped),
                            "fields_in_vault":len(attrs),
                            "collection_samples":collection_examples,
                            "collections_with_catchup_fields":mapped})
        rec["pre736_focused_collection_metadata"] = focused

        rec["race_bin_vaults"] = [v["name"] for v in vl if "race" in v["name"].lower() or "bin" in v["name"].lower()]
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
