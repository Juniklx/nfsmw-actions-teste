#!/usr/bin/env python3
"""PRE327 synthetic byte-order scan test; no Drive, game or credentials."""
from pre327_nitro_binary_xrefs_readonly import ADDRESS, PATTERNS, count_occurrences

assert ADDRESS == 2185382640
assert PATTERNS["big_endian"] == bytes.fromhex("82424af0")
assert PATTERNS["little_endian"] == bytes.fromhex("f04a4282")
sample = b"HEAD" + PATTERNS["big_endian"] + b"---" + PATTERNS["little_endian"] + b"END"
assert count_occurrences(sample, PATTERNS["big_endian"]) == (1, [4])
assert count_occurrences(sample, PATTERNS["little_endian"]) == (1, [11])
assert count_occurrences(b"irrelevant", PATTERNS["big_endian"]) == (0, [])
assert count_occurrences(PATTERNS["big_endian"] * 40, PATTERNS["big_endian"]) == (40, list(range(0, 128, 4)))
print("PRE327_MOCK_STATUS AUDIT_OK")
print("PRE327_MOCK_ASSERTIONS 7")
