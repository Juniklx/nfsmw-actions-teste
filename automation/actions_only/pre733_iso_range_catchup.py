#!/usr/bin/env python3
"""PRE733: read-only Drive HTTP Range XDVDFS audit of the USA Xbox 360 ISO.

No ISO or extracted game bytes leave the user's private Drive or ephemeral job.
No patch, signing, or APK. PC hash candidates are not proof of X360 semantics.
"""
import argparse
import json
import struct
from pathlib import Path
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.http import MediaFileUpload
from pre105_read_settings_source import drive_client
from pre732_private_pre99 import scan_stream

ISO_ID = "1eDWuZTPrtfzk-2qD1l1YgN6GYg-_9mfr"
EXPECTED_SIZE = 7834892288
REPORT_FOLDER = "1yw1Z83O0d83CoQccjYREfhxAF17eHD-"
MAGIC = b"MICROSOFT*XBOX*MEDIA"
SECTOR = 2048
CACHE = 1024 * 1024
BASES = (0, 0x0FD90000, 0x02080000, 0x18300000)


class RemoteRange:
    def __init__(self, credentials, file_id, size):
        self.session = AuthorizedSession(credentials)
        self.url = "https://www.googleapis.com/drive/v3/files/" + file_id + "?alt=media"
        self.size = size
        self.pos = 0
        self.cache_id = -1
        self.cache_data = b""
        self.requests = 0

    def seek(self, offset, whence=0):
        base = 0 if whence == 0 else self.pos if whence == 1 else self.size if whence == 2 else None
        if base is None:
            raise ValueError("Bad seek mode")
        new = base + offset
        if new < 0 or new > self.size:
            raise ValueError("Out-of-bounds ISO seek")
        self.pos = new
        return new

    def tell(self):
        return self.pos

    def _block(self, index):
        if index == self.cache_id:
            return self.cache_data
        start = index * CACHE
        end = min(start + CACHE, self.size) - 1
        self.requests += 1
        if self.requests > 3072:
            raise ValueError("Excessive remote ISO HTTP requests")
        with self.session.get(self.url, headers={"Range": f"bytes={start}-{end}"},
                              stream=True, timeout=120) as response:
            if response.status_code != 206:
                raise ValueError(f"Drive Range not supported (status {response.status_code}); refusing full ISO")
            cr = response.headers.get("Content-Range", "")
            if not cr.startswith(f"bytes {start}-{end}/"):
                raise ValueError("Unexpected Drive Content-Range")
            amount = end + 1 - start
            data = response.raw.read(amount + 1)
            if len(data) != amount:
                raise ValueError("Truncated/excess Drive range response")
        self.cache_id = index
        self.cache_data = data
        return data

    def read(self, size):
        if size is None or size < 0 or size > 64 * 1024 * 1024:
            raise ValueError("Unbounded or oversized ISO read")
        size = min(size, self.size - self.pos)
        out = bytearray()
        while len(out) < size:
            index, inside = divmod(self.pos, CACHE)
            data = self._block(index)
            take = min(size - len(out), len(data) - inside)
            if take <= 0:
                raise ValueError("Invalid ISO block")
            out.extend(data[inside:inside+take])
            self.pos += take
        return bytes(out)


class BoundedReader:
    def __init__(self, source, size):
        self.source, self.remaining = source, size

    def read(self, n):
        size = min(max(0, n), self.remaining)
        data = self.source.read(size)
        self.remaining -= len(data)
        return data


def find_volume(iso):
    for base in BASES:
        iso.seek(base + 32 * SECTOR)
        descriptor = iso.read(SECTOR)
        if descriptor[:20] == MAGIC and descriptor[0x7ec:0x800] == MAGIC:
            root_sector, root_size = struct.unpack_from("<II", descriptor, 0x14)
            if 0 < root_size <= 2 * 1024 * 1024:
                return base, root_sector, root_size
    raise ValueError("Known XDVDFS descriptors not found; no brute-force ISO scan")


def dir_entries(tab):
    work = [0]
    visited = set()
    while work:
        off = work.pop()
        if off in visited or off + 14 > len(tab):
            continue
        visited.add(off)
        left, right, sector, size, attrs, name_len = struct.unpack_from("<HHIIBB", tab, off)
        for ptr in (left, right):
            if ptr not in (0, 0xFFFF):
                work.append(ptr * 4)
        if not name_len or off + 14 + name_len > len(tab):
            continue
        name = tab[off + 14:off + 14 + name_len].decode("latin1")
        yield {"name": name, "sector": sector, "size": size, "is_dir": bool(attrs & 0x10)}


def all_files(iso, base, root_sector, root_size):
    visited_dirs = set()
    results = []

    def visit(sector, size, prefix, depth):
        if depth > 20 or len(results) > 10000:
            raise ValueError("Directory traversal bound exceeded")
        if (sector, size) in visited_dirs:
            return
        visited_dirs.add((sector, size))
        if size < 14 or size > 2 * 1024 * 1024:
            raise ValueError("Unexpected XDVDFS directory size")
        iso.seek(base + sector * SECTOR)
        table = iso.read(size)
        for item in dir_entries(table):
            name = prefix + "/" + item["name"] if prefix else item["name"]
            if item["is_dir"]:
                visit(item["sector"], item["size"], name, depth+1)
            else:
                results.append((name, item["sector"], item["size"]))
    visit(root_sector, root_size, "", 0)
    return results


def audit(iso):
    base, sector, size = find_volume(iso)
    files = all_files(iso, base, sector, size)
    candidates = [(name, s, n) for name,s,n in files
                  if name.lower().endswith((".bin", ".vpak")) and 0 < n <= 32 * 1024 * 1024]
    def priority(item):
        name = item[0].lower()
        return (0 if "attrib" in name else 1 if "gameplay" in name else 2 if "race" in name
                else 3 if "zdir" in name else 4, item[2])
    candidates.sort(key=priority)
    result = {
        "stage": "PRE733_USA_ISO_XDVDFS_READONLY",
        "iso_drive_file_size_verified": True,
        "iso_full_sha256_verified": False,
        "xbox_catchup_disabled": False,
        "gameplay_changed": False, "apk_built": False, "signing_material_read": False,
        "xvdvfs_partition_base_hex": hex(base),
        "total_game_files": len(files),
        "candidate_bin_files": len(candidates),
        "files_scanned": 0, "bytes_scanned": 0, "matches": [],
        "candidate_filenames": [x[0] for x in candidates[:200]],
    }
    for name, sector, size in candidates:
        if result["bytes_scanned"] + size > 160 * 1024 * 1024:
            break
        iso.seek(base + sector * SECTOR)
        hits = scan_stream(BoundedReader(iso, size))
        result["files_scanned"] += 1
        result["bytes_scanned"] += size
        if hits:
            result["matches"].append({"name": name, "size": size, "hashes": hits})
    result["range_calls"] = iso.requests
    return result


def main():
    opts = argparse.ArgumentParser()
    opts.add_argument("--report", required=True, type=Path)
    args = opts.parse_args()
    drive = drive_client()
    meta = drive.files().get(fileId=ISO_ID, fields="id,size,name,mimeType").execute()
    if meta.get("id") != ISO_ID or int(meta.get("size", 0)) != EXPECTED_SIZE:
        raise ValueError("USA ISO identity/size metadata mismatch")
    iso = RemoteRange(drive._http.credentials, ISO_ID, EXPECTED_SIZE)
    result = audit(iso)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    name = "NFSMW_PRE733_ISO_USA_CATCHUP_READONLY_REPORT.json"
    media = MediaFileUpload(str(args.report), mimetype="application/json")
    uploaded = drive.files().create(body={"name": name, "mimeType": "application/json",
                                          "parents": [REPORT_FOLDER]},
                                   media_body=media, fields="id,name,parents").execute()
    if uploaded.get("name") != name or REPORT_FOLDER not in uploaded.get("parents", []):
        raise ValueError("Private Drive upload verification failed")
    print("PRE733_REPORT_DRIVE_ID=" + uploaded["id"])
    print("PRE733_SCANNED_FILES=" + str(result["files_scanned"]))
    print("PRE733_MATCHED_FILES=" + str(len(result["matches"])))
    print("PRE733_REMOTE_CALLS=" + str(result["range_calls"]))
    print("PRE733_NO_PATCH_NO_APK_NO_SIGNING")

if __name__ == "__main__":
    main()
