"""Synthetic tests only. Never use proprietary files in public CI."""
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("pre732_auditar_catchup_atributos.py")
spec = importlib.util.spec_from_file_location("pre732", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Pre732ReadOnlyTests(unittest.TestCase):
    def test_offsets_endian_and_chunk_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "FE_ATTRIB.BIN"
            original = b"0" * 7 + struct.pack(">I", m.ATTRS["CatchUp"])
            original += b"1" * 7 + struct.pack("<I", m.ATTRS["CatchUpOverride"])
            source.write_bytes(original)
            hits = m.scan_file(source, block=8)
            by_key = {(x["attribute"], x["endianness"]): x for x in hits}
            self.assertEqual(by_key["CatchUp", "BE"]["sample_offsets_hex"], ["0x7"])
            self.assertEqual(by_key["CatchUpOverride", "LE"]["sample_offsets_hex"], ["0x12"])
            self.assertEqual(sum(x["count"] for x in hits), 2)
            self.assertEqual(source.read_bytes(), original)

    def test_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "gameplay.bin"
            source.write_bytes(b"!" + struct.pack(">I", m.ATTRS["CatchUp"]))
            self.assertEqual(m.scan_file(source, block=4)[0]["count"], 1)

    def test_exclude_signing_and_do_not_mutate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "default.xex").write_bytes(bytes(32))
            secret = root / "signer.jks"
            data = struct.pack(">I", m.ATTRS["CatchUp"])
            secret.write_bytes(data)
            result = m.audit([root], max_mib=10)
            self.assertEqual(result["files_scanned"], 1)
            self.assertEqual(result["files_with_matches"], 0)
            self.assertFalse(result["gameplay_changed"])
            self.assertEqual(secret.read_bytes(), data)

    def test_no_input_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            result = m.audit([Path(folder) / "missing.bin"])
            self.assertEqual(result["files_scanned"], 0)
            self.assertEqual(result["files_skipped"], 1)


if __name__ == "__main__":
    unittest.main()
