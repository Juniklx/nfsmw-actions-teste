#!/usr/bin/env python3
"""PRE691: offline, read-only inspection of pinned RADV Xclipse Android release.

Never executes, extracts, or loads the third-party .so. Not a compatibility or
FPS test. Expected SHA256 belongs to JimVulkan's v1.8.0 release published on
2026-10-19. Rejects unexpected package structure and architecture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

EXPECTED_SHA256 = "0545b1b24817cc0ed4a9e4fc440a7080cbaf69a9ce5d1e4bb22b0e697129c223"
EXPECTED_LIBRARY = "vulkan.radeon.so"
MAX_ARCHIVE_BYTES = 25_000_000
MAX_UNCOMPRESSED_BYTES = 100_000_000


def inspect(path: Path) -> dict:
    if not path.is_file():
        raise ValueError("PRE691_ARCHIVE_MISSING")
    raw = path.read_bytes()
    if not (1_000_000 < len(raw) < MAX_ARCHIVE_BYTES):
        raise ValueError("PRE691_ARCHIVE_SIZE_UNEXPECTED")
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("PRE691_RELEASE_SHA256_MISMATCH")
    with zipfile.ZipFile(path, "r") as z:
        entries = z.infolist()
        files = [i for i in entries if not i.is_dir()]
        if not files or len(files) > 30:
            raise ValueError("PRE691_ZIP_MEMBER_COUNT_UNEXPECTED")
        for i in files:
            if i.filename != Path(i.filename).name or i.filename.startswith("."):
                raise ValueError("PRE691_UNEXPECTED_NESTED_ZIP_PATH")
            if i.file_size > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("PRE691_ZIP_UNCOMPRESSED_MEMBER_EXCESSIVE")
            if i.flag_bits & 1:
                raise ValueError("PRE691_ENCRYPTED_ZIP_UNEXPECTED")
        names = [i.filename for i in files]
        if len(names) != len(set(names)):
            raise ValueError("PRE691_DUPLICATE_ZIP_FILENAME")
        if not {"meta.json", "NOTICE.txt", EXPECTED_LIBRARY}.issubset(names):
            raise ValueError("PRE691_REQUIRED_ZIP_MEMBERS_MISSING")
        meta_info = z.getinfo("meta.json")
        if meta_info.file_size > 64 * 1024:
            raise ValueError("PRE691_META_TOO_LARGE")
        meta = json.loads(z.read("meta.json").decode("utf-8"))
        lib_name = meta.get("libraryName")
        if lib_name != EXPECTED_LIBRARY:
            raise ValueError("PRE691_DRIVER_LIBRARY_NAME_MISMATCH")
        label = meta.get("name")
        if not isinstance(label, str) or not label:
            raise ValueError("PRE691_DRIVER_DISPLAY_NAME_MISSING")
        lib_info = z.getinfo(EXPECTED_LIBRARY)
        if not 100000 < lib_info.file_size < MAX_UNCOMPRESSED_BYTES:
            raise ValueError("PRE691_LIBRARY_SIZE_UNEXPECTED")
        with z.open(lib_info) as stream:
            elf = stream.read(64)
        if len(elf) < 64 or elf[:4] != b"\x7fELF":
            raise ValueError("PRE691_LIBRARY_IS_NOT_ELF")
        if elf[4] != 2 or elf[5] != 1:
            raise ValueError("PRE691_ELF_NOT_64BIT_LITTLE_ENDIAN")
        machine = int.from_bytes(elf[18:20], "little")
        if machine != 183:
            raise ValueError("PRE691_ELF_NOT_AARCH64")
        # CRC check decompresses the archive in memory internally, does not
        # extract files or execute the library.
        if z.testzip() is not None:
            raise ValueError("PRE691_BAD_ZIP_CRC")
        return {
            "gate": "PRE691_RADV_XCLIPSE_RELEASE_ZIP_STATIC_AUDIT",
            "status": "PACKAGE_FORMAT_ONLY__DEVICE_LOAD_UNTESTED",
            "release": "v1.8.0",
            "sha256": sha,
            "size_bytes": len(raw),
            "package_name": label,
            "libraryName": lib_name,
            "driver_binary_arch": "ELF64_AARCH64",
            "files": names,
            "all_members_crc_ok": True,
            "limits": {
                "no_library_was_executed": True,
                "no_android_device_was_changed": True,
                "apk_v51_loader_unverified": True,
                "s24fe_runtime_compatibility_unverified": True,
                "frame_pacing_improvement_unproven": True,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.release_zip)
    result = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    print("PRE691_RADV_PACKAGE_SHA_AND_ELF_AARCH64=PASS", file=sys.stderr)
    print("PRE691_DEVICE_AND_APK_INTEGRATION=NOT_TESTED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
