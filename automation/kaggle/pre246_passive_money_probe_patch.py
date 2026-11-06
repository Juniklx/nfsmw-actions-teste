#!/usr/bin/env python3
"""PRE246: ephemeral PAL-only, passive money-store diagnostic injection.

Intended for a V37 controlled diagnostic build, NOT a money cheat.
Only the already-computed register values at PRE237/PRE240-confirmed stores
are passed to a bounded logger, after the ORIGINAL REX_STORE_U32.
Requires authenticated PRE99 root, refuses unknown code/source SHA.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

from pre239_pal_money_probe_recipe_readonly import TARGETS, body_for_function, COMMENT, STORE
from pre240_pal_money_old_value_readonly import OLD, EXPECTED_HASHES

CMAKE_REL = "nativo/app/CMakeLists.txt"
CMAKE_SHA256 = "4ba69347dbf5106d42c8df470e6e5e690c7785b0d31cd336a1b536d904877e26"
FILE_CPP = "nativo/app/src/nfsmw_cheats_trace_pre246.cpp"
CPP_TEXT = r'''#include <atomic>
#include <cstdint>
#include <rex/logging.h>

// Passive bounded trace only. No guest pointer dereference.
static std::atomic<std::uint32_t> g_money_trace_counts_pre246[8]{};

extern "C" void NFSMW_PRE246_TRACE_STORE(std::uint32_t site,
                                         std::uint32_t guest_address,
                                         std::uint32_t previous,
                                         std::uint32_t proposed) noexcept {
  if (site < 1 || site > 8) return;
  auto& n = g_money_trace_counts_pre246[site - 1];
  std::uint32_t seen = n.load(std::memory_order_relaxed);
  while (seen < 12u && !n.compare_exchange_weak(
           seen, seen + 1u, std::memory_order_relaxed, std::memory_order_relaxed)) {}
  if (seen >= 12u) return;
  REXLOG_INFO("[NFSMW_PRE246_CHEATS_DIAG] money site={} addr=0x{:08X} previous={} written={}",
              site, guest_address, previous, proposed);
}
'''
DECL = '\nextern "C" void NFSMW_PRE246_TRACE_STORE(unsigned int, unsigned int, unsigned int, unsigned int) noexcept;\n'
FUNC = "NFSMW_PRE246_TRACE_STORE"

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def splice_function(src: str, target: str, spec: dict, start_site: int) -> tuple[str, dict]:
    body = body_for_function(src, target)
    lines = body.splitlines(keepends=True)
    hits = []
    for i, line in enumerate(lines):
        m = COMMENT.match(line)
        if m and i + 1 < len(lines) and STORE.match(lines[i + 1]):
            hits.append((i, m.group(1).replace(" ", ""), STORE.match(lines[i + 1])))
    expected = spec["stores"]
    if len(hits) != len(expected) or len(expected) != len(OLD[target]):
        raise ValueError("PRE246: unexpected number of guest stores")
    out_lines = list(lines)
    report_sites = []
    for ordinal, ((idx, comment, host), (expect_comment, addr, new), old) in enumerate(
        zip(hits, expected, OLD[target]), 1
    ):
        if (comment.lower(), host.group(1).strip(), host.group(2).strip()) != (
            expect_comment.lower(), addr, new
        ):
            raise ValueError("PRE246: store opcode/value changed from pinned PRE240")
        guest_pc = spec["guest_pc_candidates_from_PRE237"][ordinal - 1]
        site = start_site + ordinal - 1
        original = lines[idx + 1]
        prefix = re.match(r"^(\s*)", original).group(1)
        trace = (prefix + FUNC + "(" + str(site) + ", "
                 + addr + ", ctx." + old + ".u32, " + new + ");\n")
        out_lines[idx + 1] = original + trace
        report_sites.append({"site": site, "guest_pc_crosswalk": guest_pc,
            "original_host_store": original.strip(),
            "previous_register": old,
            "probe_inserted_after_original": True})
    new_body = "".join(out_lines)
    if new_body.count("REX_STORE_U32(") != body.count("REX_STORE_U32("):
        raise ValueError("PRE246: store count changed")
    if new_body.count("REX_LOAD_U32(") != body.count("REX_LOAD_U32("):
        raise ValueError("PRE246: load count changed")
    if new_body.count(FUNC + "(") != len(expected):
        raise ValueError("PRE246: injected callback count mismatch")
    if src.count(body) != 1:
        raise ValueError("PRE246: could not uniquely locate function text")
    return src.replace(body, new_body, 1), {
        "target": target, "sites": report_sites, "original_host_loads_unchanged": True,
        "original_host_stores_unchanged": True
    }

def apply(root: Path) -> dict:
    root = Path(root)
    app = root / "nativo/app"
    cmake = root / CMAKE_REL
    if not cmake.is_file():
        raise ValueError("PRE246: app CMake not found")
    original_cmake = cmake.read_bytes()
    if sha_bytes(original_cmake) != CMAKE_SHA256:
        raise ValueError("PRE246: CMake SHA pinned PRE99 mismatch")
    if (root / FILE_CPP).exists():
        raise ValueError("PRE246: trace module already exists, refusing double patch")
    cmake_text = original_cmake.decode("utf-8")
    needle = "add_library(nfsmw SHARED ${NFSMW_SOURCES})"
    if cmake_text.count(needle) != 1:
        raise ValueError("PRE246: native library CMake anchor missing")
    cmake_new = cmake_text.replace(needle,needle + "\n    target_sources(nfsmw PRIVATE src/nfsmw_cheats_trace_pre246.cpp)",1)
    generated = []
    for name, spec in TARGETS.items():
        path = root / spec["filename"].removeprefix("workspace/")
        if not path.is_file():
            raise ValueError("PRE246: source missing " + name)
        raw = path.read_bytes()
        if sha_bytes(raw) != EXPECTED_HASHES[spec["filename"]]:
            raise ValueError("PRE246: generated source hash mismatch " + name)
        generated.append((name, spec, path, raw))
    new_files = []
    total_sites = 0
    for name, spec, path, raw in generated:
        src = raw.decode("utf-8")
        # The generated shards use their own preamble; do not require an nfsmw_pch.h include.
        # Insert one extern at the first *top-level* function macro, after the preamble.
        if FUNC in src:
            raise ValueError("PRE246: callback appears in original source")
        source_new, details = splice_function(src,name,spec, 1 if name=="sub_8256BFC8" else 4)
        first_def = re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)", source_new)
        if first_def is None:
            raise ValueError("PRE246: top-level function definition anchor missing " + name)
        source_new = source_new[:first_def.start()] + DECL + source_new[first_def.start():]
        if source_new.count(DECL) != 1:
            raise ValueError("PRE246: declaration count mismatch")
        total_sites += len(details["sites"])
        new_files.append((path,raw,source_new.encode("utf-8"),details))
    if total_sites != 8:
        raise ValueError("PRE246: incomplete or duplicate money trace points")
    # All checks passed. Only now write into the disposable restored runner tree.
    for path,raw,patched,details in new_files:
        path.with_suffix(path.suffix+".pre246_original").write_bytes(raw)
        path.write_bytes(patched)
        if sha_bytes(path.read_bytes()) != sha_bytes(patched):
            raise ValueError("PRE246: generated source write/readback mismatch")
    cpp = root / FILE_CPP
    cpp.write_text(CPP_TEXT,encoding="utf-8")
    if not (app / "src").is_dir():raise ValueError("PRE246: src folder missing")
    cmake.with_suffix(".txt.pre246_original").write_bytes(original_cmake)
    cmake.write_text(cmake_new,encoding="utf-8")
    if cpp.read_text(encoding="utf-8") != CPP_TEXT:
        raise ValueError("PRE246: trace source readback mismatch")
    if sha_bytes(cmake.read_bytes()) == CMAKE_SHA256:
        raise ValueError("PRE246: CMake remained unchanged")
    return {
      "pre246_passive_probe_applied_to_ephemeral_restored_tree":True,
      "module":FILE_CPP,
      "module_sha256":sha_bytes(cpp.read_bytes()),
      "cmake_original_sha256":CMAKE_SHA256,
      "cmake_patched_sha256":sha_bytes(cmake.read_bytes()),
      "money_traces":total_sites,
      "source_files":[{
          "path":str(path.relative_to(root)),
          "original_sha256":sha_bytes(raw),
          "patched_sha256":sha_bytes(patched),
          **details
        } for path,raw,patched,details in new_files],
      "original_game_store_mutated":False,
      "extra_guest_memory_loads":0,
      "gameplay_cheats_enabled":False,
      "source_persistent_drive_modified":False,
      "logging_marker":"NFSMW_PRE246_CHEATS_DIAG"
    }
