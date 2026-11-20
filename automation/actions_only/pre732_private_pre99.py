#!/usr/bin/env python3
"""PRE732B: audit a pinned private archive; never patch gameplay or publish binary data."""
import argparse
import json
import tarfile
import tempfile
from pathlib import Path
from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre732_auditar_catchup_atributos import patterns

REPORT_FOLDER = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
BLOCK = 4 * 1024 * 1024

def wanted(name):
    low = name.lower()
    if not low.startswith("workspace/") or ".." in name.split("/"):
        return False
    ext = Path(low).suffix
    if ext == ".cpp" and ("/generated/" in low or "/generated-android/" in low):
        return True
    return ext in {".bin", ".bun", ".vpak", ".dat", ".nfsp"} and (
        "/game_root/" in low or "attrib" in low or "gameplay" in low
        or Path(low).name.startswith(("zdir", "zzdata", "global")))

def scan_stream(stream):
    pats = patterns()
    stat = {(name, end): {"count": 0, "sample_offsets_hex": []}
            for name, end, _ in pats}
    tail, size = b"", 0
    while True:
        chunk = stream.read(BLOCK)
        if not chunk:
            break
        buf, start = tail + chunk, size - len(tail)
        for name, end, needle in pats:
            result = stat[name, end]
            pos = buf.find(needle)
            while pos >= 0:
                if pos + 4 > len(tail):
                    result["count"] += 1
                    if len(result["sample_offsets_hex"]) < 16:
                        result["sample_offsets_hex"].append(hex(start + pos))
                pos = buf.find(needle, pos + 1)
        tail = buf[-3:]
        size += len(chunk)
    return [{"attribute": k[0], "endianness": k[1], **v}
            for k, v in stat.items() if v["count"]]

def inspect(tarpath):
    result = {"stage": "PRE732B_PRIVATE_PRE99_READONLY", "pc_hashes_not_x360_proof": True,
              "archive_sha256_verified": True, "gameplay_changed": False,
              "apk_built": False, "signing_material_read": False,
              "entries": 0, "eligible_scanned": 0, "eligible_bytes": 0,
              "matches": [], "eligible_skipped": 0}
    with tarfile.open(tarpath, "r:gz", errorlevel=2) as tar:
        for member in tar:
            result["entries"] += 1
            if result["entries"] > 100000:
                raise ValueError("Excessive archive member count")
            if not member.isfile() or not wanted(member.name):
                continue
            if member.size > 192 * 1024 * 1024 or member.size < 0:
                result["eligible_skipped"] += 1
                continue
            if result["eligible_bytes"] + member.size > 2_500_000_000:
                raise ValueError("Candidate byte budget exceeded")
            fh = tar.extractfile(member)
            if fh is None:
                raise ValueError("Unreadable candidate file")
            with fh:
                found = scan_stream(fh)
            result["eligible_scanned"] += 1
            result["eligible_bytes"] += member.size
            if found:
                result["matches"].append({"member": member.name, "size_bytes": member.size,
                                          "candidate_hashes": found})
    return result

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--report", type=Path, required=True)
    args = cli.parse_args()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre732b-") as td:
        drive = drive_client()
        meta = drive.files().get(fileId=BACKUP_ID, fields="id,size").execute()
        if meta.get("id") != BACKUP_ID or int(meta.get("size", 0)) != EXPECTED_BYTES:
            raise ValueError("PRE99 metadata mismatch")
        archive = Path(td) / "pre99.tar.gz"
        download(drive, archive)
        digest, _md5, size = sha_file(archive)
        if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
            raise ValueError("PRE99 digest mismatch")
        report = inspect(archive)
        report["backing_archive_sha256"] = digest
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        from googleapiclient.http import MediaFileUpload
        name = "NFSMW_PRE732B_CATCHUP_PRE99_READONLY_REPORT.json"
        uploaded = drive.files().create(
            body={"name": name, "parents": [REPORT_FOLDER], "mimeType": "application/json"},
            media_body=MediaFileUpload(str(args.report), mimetype="application/json"),
            fields="id,name,parents").execute()
        if uploaded.get("name") != name or REPORT_FOLDER not in uploaded.get("parents", []):
            raise ValueError("Private report upload was not verified")
        print("PRE732B_PRIVATE_DRIVE_REPORT_ID=" + uploaded["id"])
        print("PRE732B_ELIGIBLE_SCANNED=" + str(report["eligible_scanned"]))
        print("PRE732B_MATCHED_FILES=" + str(len(report["matches"])))
        print("PRE732B_NO_PATCH_NO_APK_NO_SIGNING")
if __name__ == "__main__":
    main()
