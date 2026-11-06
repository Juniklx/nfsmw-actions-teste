#!/usr/bin/env python3
"""PRE194: SHA-pinned PAL-only C3 diagnostic, retaining original safety fallback.

Only modifies a single guard in AplazarCopia. No tuning, no release signing,
no file writes. The caller must commit patched bytes to a separate build tree.
"""
from __future__ import annotations
import hashlib

BASE_SHA = "046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2"
PATCHED_SHA = "a01f25e531af783d37f70a3c3caa0f3e7a979d2bdbdd923abf7b2c6062d29d1e"
MARKER = b"NFSMW_PRE194_C3"
OLD = b'''    const size_t indice = size_t(textura.en_vuelo) - 1;
    if (indice >= en_vuelo_.size() || en_vuelo_[indice].textura != &textura || en_vuelo_[indice].copia) {
      ApagarEnlaces(fmt::format("DIFERENCIA: indice de textura en vuelo incoherente ({} de {})", indice,
                                en_vuelo_.size()));
      return false;
    }
'''
NEW = b'''    const size_t indice = size_t(textura.en_vuelo) - 1;
    const bool indice_fuera = indice >= en_vuelo_.size();
    const bool referencia_distinta = !indice_fuera && en_vuelo_[indice].textura != &textura;
    const bool copia_duplicada = !indice_fuera && en_vuelo_[indice].copia;
    if (indice_fuera || referencia_distinta || copia_duplicada) {
      ApagarEnlaces(fmt::format("DIFERENCIA: indice de textura en vuelo incoherente ({} de {}) "
                                "[NFSMW_PRE194_C3 indice_fuera={} referencia_distinta={} copia_duplicada={}]",
                                indice, en_vuelo_.size(), indice_fuera, referencia_distinta,
                                copia_duplicada));
      return false;
    }
'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch_verified(source: bytes) -> bytes:
    if sha(source) != BASE_SHA:
        raise ValueError("PRE194 PAL source SHA differs from authenticated PRE99; refuses double or unexpected patch")
    if MARKER in source or source.count(OLD) != 1:
        raise ValueError("PRE194 PAL guard missing or already patched")
    output = source.replace(OLD, NEW, 1)
    if output.count(MARKER) != 1 or output.count(OLD) != 0:
        raise ValueError("PRE194 unexpected replacement result")
    if PATCHED_SHA != "TO_BE_VERIFIED" and sha(output) != PATCHED_SHA:
        raise ValueError("PRE194 output SHA mismatch")
    return output

if __name__ == "__main__":
    raise SystemExit("PRE194 module is imported by a verified isolated builder; no direct source writes")
