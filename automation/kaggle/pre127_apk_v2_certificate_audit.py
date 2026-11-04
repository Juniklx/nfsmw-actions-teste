#!/usr/bin/env python3
"""Read SHA-256 of the DER certificate in an Android APK v2 signature block.

Independent of apksigner CLI text. This is not a replacement for apksigner
cryptographic verification. Requires exactly one v2 signer/certificate.
"""
from __future__ import annotations
import argparse
import hashlib
import struct
from pathlib import Path

APK_SIG_BLOCK_MAGIC = b"APK Sig Block 42"
APK_V2_PAIR_ID = 0x7109871A
MAX_SIGNATURE_BLOCK = 32 * 1024 * 1024


def length_prefixed(data: bytes, offset: int) -> tuple[bytes, int]:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Malformed APK v2 length prefix")
    length = struct.unpack_from("<I", data, offset)[0]
    end = offset + 4 + length
    if end > len(data):
        raise ValueError("APK v2 length extends beyond signed payload")
    return data[offset + 4:end], end


def one_length_prefixed(data: bytes) -> bytes:
    payload, end = length_prefixed(data, 0)
    if end != len(data):
        raise ValueError("More than one APK v2 signer or certificate")
    return payload


def apk_v2_cert_sha256(apk: Path) -> str:
    size = apk.stat().st_size
    if size < 256 or size > 2**32:
        raise ValueError("Invalid or unsupported APK size")
    with apk.open("rb") as fp:
        tail_size = min(65557, size)
        fp.seek(size - tail_size)
        tail = fp.read(tail_size)
        eocd = tail.rfind(b"PK\x05\x06")
        if eocd < 0 or eocd + 22 > len(tail):
            raise ValueError("No APK ZIP EOCD record")
        comment_len = struct.unpack_from("<H", tail, eocd + 20)[0]
        if eocd + 22 + comment_len != len(tail):
            raise ValueError("Invalid ZIP EOCD comment length")
        central_dir = struct.unpack_from("<I", tail, eocd + 16)[0]
        if central_dir < 32 or central_dir > size - 22:
            raise ValueError("Invalid APK central directory offset")
        fp.seek(central_dir - 24)
        footer = fp.read(24)
        block_size = struct.unpack_from("<Q", footer, 0)[0]
        if footer[8:] != APK_SIG_BLOCK_MAGIC:
            raise ValueError("Missing Android APK Signing Block")
        if block_size < 24 or block_size > MAX_SIGNATURE_BLOCK:
            raise ValueError("Invalid Android APK signature block length")
        start = central_dir - (block_size + 8)
        if start < 0:
            raise ValueError("Invalid Android APK signature block offset")
        fp.seek(start)
        block = fp.read(block_size + 8)
        if len(block) != block_size + 8:
            raise ValueError("Short APK Signing Block")
        if struct.unpack_from("<Q", block, 0)[0] != block_size:
            raise ValueError("APK Signing Block head/footer mismatch")
    pairs = block[8:-24]
    value = None
    pos = 0
    while pos < len(pairs):
        if pos + 12 > len(pairs):
            raise ValueError("Truncated APK Signing Block pair")
        length = struct.unpack_from("<Q", pairs, pos)[0]
        pos += 8
        if length < 4 or pos + length > len(pairs):
            raise ValueError("Invalid APK Signing Block pair length")
        pair_id = struct.unpack_from("<I", pairs, pos)[0]
        pair_data = pairs[pos + 4:pos + length]
        pos += length
        if pair_id == APK_V2_PAIR_ID:
            if value is not None:
                raise ValueError("Duplicate APK v2 block")
            value = pair_data
    if value is None:
        raise ValueError("APK missing v2 signatures")
    signer = one_length_prefixed(one_length_prefixed(value))
    signed_data, next_offset = length_prefixed(signer, 0)
    _signatures, next_offset = length_prefixed(signer, next_offset)
    _public_key, next_offset = length_prefixed(signer, next_offset)
    if next_offset != len(signer):
        raise ValueError("Malformed APK v2 signer fields")
    _digests, next_offset = length_prefixed(signed_data, 0)
    certificates, next_offset = length_prefixed(signed_data, next_offset)
    cert = one_length_prefixed(certificates)
    if not cert.startswith(b"\x30") or len(cert) < 128:
        raise ValueError("APK v2 certificate is not DER")
    return hashlib.sha256(cert).hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("apk", type=Path)
    a = p.parse_args()
    print(apk_v2_cert_sha256(a.apk))
