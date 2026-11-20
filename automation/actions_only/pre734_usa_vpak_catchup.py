#!/usr/bin/env python3
"""PRE734: authenticated Xbox 360 USA VPAK attribute hash audit via private ISO ranges.

All original bytes remain private; report is an interpretation-free occurrence map.
No resource editing, no APK, no signing, no gameplay changes.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre105_read_settings_source import drive_client
from pre733_iso_range_catchup import RemoteRange, find_volume, all_files, ISO_ID, EXPECTED_SIZE, REPORT_FOLDER, SECTOR
from pre732_private_pre99 import scan_stream

PINNED = (
    ("GLOBAL/ATTRIBUTES.BIN", "ZZDATA4.BIN", 287117312, 697856,
     "9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad", 3679311872),
    ("GLOBAL/FE_ATTRIB.BIN", "ZZDATA0.BIN", 162392064, 113856,
     "8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528", None),
)


def run(drive):
    meta = drive.files().get(fileId=ISO_ID, fields="id,size").execute()
    if meta.get("id") != ISO_ID or int(meta.get("size", 0)) != EXPECTED_SIZE:
        raise ValueError("USA ISO Drive identity/size mismatch")
    reader = RemoteRange(drive._http.credentials, ISO_ID, EXPECTED_SIZE)
    base, root_sector, root_size = find_volume(reader)
    files = {Path(name).name.upper(): (name, sector, size)
             for name, sector, size in all_files(reader, base, root_sector, root_size)}
    results = []
    for label, archive, inner_offset, size, expected_sha, expected_absolute in PINNED:
        if archive not in files:
            raise ValueError("Expected Xbox 360 archive not found: " + archive)
        name, sector, archive_size = files[archive]
        if inner_offset + size > archive_size:
            raise ValueError("VPAK exceeds original archive boundaries")
        absolute = base + sector * SECTOR + inner_offset
        if expected_absolute is not None and absolute != expected_absolute:
            raise ValueError("Original ATTRIBUTES.BIN absolute offset mismatch")
        reader.seek(absolute)
        blob = reader.read(size)
        actual = hashlib.sha256(blob).hexdigest()
        if actual != expected_sha or blob[:4] != b"VPAK":
            raise ValueError("Pinned VPAK SHA-256 or magic mismatch")
        matches = scan_stream(io.BytesIO(blob))
        vault_count = int.from_bytes(blob[4:8], "little")
        if vault_count < 1 or vault_count > 128:
            raise ValueError("Unexpected VPAK vault count")
        vaults = []
        for k in range(vault_count):
            start = 16 + 20*k
            name_local, bin_size, vlt_size, bin_off, vlt_off = __import__("struct").unpack_from("<IIIII", blob, start)
            if bin_off + bin_size > len(blob) or vlt_off + vlt_size > len(blob):
                raise ValueError("VPAK vault bounds invalid")
            vaults.append({"bin_offset": bin_off, "bin_size": bin_size,
                           "vlt_offset": vlt_off, "vlt_size": vlt_size})
        attr_rows = []
        for hit in matches:
            for off_txt in hit["sample_offsets_hex"]:
                off = int(off_txt, 16)
                section = "OTHER"
                for v in vaults:
                    if v["bin_offset"] <= off < v["bin_offset"] + v["bin_size"]:
                        section = "BIN"
                    if v["vlt_offset"] <= off < v["vlt_offset"] + v["vlt_size"]:
                        section = "VLT"
                attr_rows.append({"attribute": hit["attribute"], "offset_hex": off_txt,
                                  "section": section,
                                  "following_u32_big_endian": hex(int.from_bytes(blob[off+4:off+8], "big"))})
        text_names = {name: blob.count(name.encode("ascii")) for name in (
            "CatchUp", "CatchUpOverride", "CatchUpSkill",
            "CatchUpSpread", "CatchUpIntegral", "CatchUpDerivative")}
        results.append({
            "resource": label, "archive": archive, "size_bytes": size,
            "sha256_verified": True, "sha256": actual,
            "absolute_offset_hex": hex(absolute),
            "candidate_hashes": matches,
            "attribute_row_structure": attr_rows,
            "literal_ascii_tokens": text_names,
        })
    return {
        "stage": "PRE734_AUTHENTICATED_USA_CATCHUP_VPAK_READONLY",
        "source": "original USA ISO Drive/XDVDFS strict byte-range",
        "only_original_pinned_resource_shas_checked": True,
        "no_assumption_PC_XBOX_hash_parity": True,
        "xbox_catchup_disabled": False, "apk_built": False,
        "save_modified": False, "signing_accessed": False,
        "resources": results, "range_requests": reader.requests,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    drive = drive_client()
    result = run(drive)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("PRE734_VPAK_SHA256_VERIFIED=" + str(sum(r["sha256_verified"] for r in result["resources"])))
    print("PRE734_HASH_MATCHES=" + str(sum(len(r["candidate_hashes"]) for r in result["resources"])))
    name = "NFSMW_PRE734_USA_CATCHUP_VPAK_READONLY_REPORT.json"
    item = drive.files().create(
        body={"name": name, "parents": [REPORT_FOLDER], "mimeType": "application/json"},
        media_body=MediaFileUpload(str(args.report), mimetype="application/json"),
        fields="id,name,parents").execute()
    if item.get("name") != name or REPORT_FOLDER not in item.get("parents", []):
        raise ValueError("Drive report readback mismatch")
    print("PRE734_REPORT_DRIVE_ID=" + item["id"])
    print("PRE734_NO_PATCH_NO_APK_NO_SIGNING")
if __name__ == "__main__":
    main()
