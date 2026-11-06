#!/usr/bin/env python3
"""PRE247: disposable PAL passive nitro / Speedbreaker store probes.

Works only on an authenticated, temporary PRE99 tree AFTER PRE246 money tracing.
No guest reads, store rewriting, APK generation, signing, saves or Drive writes.
These are structural candidates; never call their identity runtime-proven.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS, FLOAT, HOST

CPP_REL = "nativo/app/src/nfsmw_cheats_trace_pre247.cpp"
CMAKE_REL = "nativo/app/CMakeLists.txt"
MONEY_TARGET = "target_sources(nfsmw PRIVATE src/nfsmw_cheats_trace_pre246.cpp)"
METER_TARGET = "target_sources(nfsmw PRIVATE src/nfsmw_cheats_trace_pre247.cpp)"
SYMBOL = "NFSMW_PRE247_TRACE_METER"
DECL = '\nextern "C" void NFSMW_PRE247_TRACE_METER(unsigned int, unsigned int, unsigned int) noexcept;\n'
CPP_TEXT = r"""#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>

// Log only already-computed store arguments. Bound volume to 12 per site.
static std::atomic<std::uint32_t> g_meter_trace_counts_pre247[8]{};

extern "C" void NFSMW_PRE247_TRACE_METER(std::uint32_t site,
                                          std::uint32_t guest_address,
                                          std::uint32_t stored_f32_bits) noexcept {
  if (site < 1 || site > 8) return;
  auto& n = g_meter_trace_counts_pre247[site - 1];
  std::uint32_t seen = n.load(std::memory_order_relaxed);
  while (seen < 12u && !n.compare_exchange_weak(
           seen, seen + 1u, std::memory_order_relaxed, std::memory_order_relaxed)) {}
  if (seen >= 12u) return;
  REXLOG_INFO("[NFSMW_PRE247_CHEATS_DIAG] meter_candidate={} addr=0x{:08X} written_f32_bits=0x{:08X}",
              site, guest_address, stored_f32_bits);
}
"""

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def insert(src: str, label: str, spec: dict, site_start: int) -> tuple[str, dict]:
    body = body_for_function(src, spec["function"])
    lines = body.splitlines(keepends=True)
    sites = []
    changes = {}
    for i, line in enumerate(lines):
        m = FLOAT.match(line)
        if not m or int(m.group(1)) != spec["offset"]:
            continue
        nxt = [(j, lines[j]) for j in range(i+1, min(i+5, len(lines)))]
        hosts = [(j, s) for j, s in nxt if HOST.match(s) and
                 int(HOST.match(s).group(1)) == spec["offset"]]
        converts = [j for j, s in nxt if "temp.f32 = float(" in s]
        if len(hosts) != 1 or len(converts) != 1 or converts[0] >= hosts[0][0]:
            raise ValueError("PRE247: unrecognized float store conversion")
        j, host = hosts[0]
        if j in changes:
            raise ValueError("PRE247: overlapping stores")
        site = site_start + len(sites)
        address = "r31.u32 + " + str(spec["offset"])
        indent = re.match(r"^(\s*)", host).group(1)
        call = (indent + SYMBOL + "(" + str(site) + ", " + address +
                ", temp.u32);\n")
        changes[j] = host + call
        sites.append({"site": site, "field_offset": spec["offset"],
                      "store_preserved": host.strip(),
                      "call_after_original_store": True,
                      "proposed_bits_from_original_temp": True})
    if len(sites) != spec["expected_stores"]:
        raise ValueError("PRE247: incorrect number of float writes")
    changed_body = "".join(changes.get(j, row) for j, row in enumerate(lines))
    if changed_body.count("REX_STORE_U32(") != body.count("REX_STORE_U32("):
        raise ValueError("PRE247: original stores changed")
    if changed_body.count("REX_LOAD_U32(") != body.count("REX_LOAD_U32("):
        raise ValueError("PRE247: new memory loads detected")
    if changed_body.count(SYMBOL+"(") != len(sites):
        raise ValueError("PRE247: callback count differs")
    if src.count(body) != 1 or SYMBOL in src:
        raise ValueError("PRE247: function text not unique or already patched")
    updated = src.replace(body, changed_body, 1)
    first = re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)", updated)
    if first is None:
        raise ValueError("PRE247: top-level function declaration missing")
    updated = updated[:first.start()] + DECL + updated[first.start():]
    if updated.count(DECL) != 1:
        raise ValueError("PRE247: duplicate declaration")
    return updated, {"resource_candidate": label, "function": spec["function"],
                     "source_store_count": len(sites), "sites": sites,
                     "extra_guest_loads": 0}

def apply(root: Path) -> dict:
    root = Path(root)
    cmake = root / CMAKE_REL
    cpp = root / CPP_REL
    if not cmake.is_file() or cpp.exists():
        raise ValueError("PRE247: CMake missing or float logger already exists")
    cm = cmake.read_bytes()
    text = cm.decode("utf-8")
    if text.count(MONEY_TARGET) != 1 or METER_TARGET in text:
        raise ValueError("PRE247: PRE246 money module anchor absent or duplicated")
    mods = []
    for label, spec in TARGETS.items():
        path = root / spec["file"].removeprefix("workspace/")
        if not path.is_file():
            raise ValueError("PRE247: missing pinned PAL generated source")
        raw = path.read_bytes()
        if sha(raw) != spec["sha256"]:
            raise ValueError("PRE247: source SHA mismatch")
        updated, details = insert(raw.decode("utf-8"), label, spec,
                                  1 if label == "nitro" else 6)
        mods.append((path, raw, updated.encode("utf-8"), details))
    if sum(len(m[3]["sites"]) for m in mods) != 8:
        raise ValueError("PRE247: incomplete PAL meter site count")
    # Strictly disposable workspace, after every validation.
    for path, raw, updated, details in mods:
        path.with_suffix(path.suffix + ".pre247_original").write_bytes(raw)
        path.write_bytes(updated)
        if sha(path.read_bytes()) != sha(updated):
            raise ValueError("PRE247: patched source readback failed")
    cpp.write_text(CPP_TEXT, encoding="utf-8")
    cmake.write_text(text.replace(MONEY_TARGET, MONEY_TARGET + "\n    " + METER_TARGET, 1),
                     encoding="utf-8")
    if cpp.read_text(encoding="utf-8") != CPP_TEXT:
        raise ValueError("PRE247: logger readback failed")
    if cmake.read_text(encoding="utf-8").count(METER_TARGET) != 1:
        raise ValueError("PRE247: CMake registration failed")
    return {
        "passive_float_probes": 8,
        "combined_money_and_meter_probe_sites": 16,
        "module": CPP_REL,
        "module_sha256": sha(cpp.read_bytes()),
        "resources": [
            {"file": str(path.relative_to(root)), "original_sha256": sha(raw),
             "patched_sha256": sha(updated), **details}
            for path, raw, updated, details in mods
        ],
        "stores_replaced": 0, "extra_guest_memory_loads": 0,
        "cheats_enabled": False, "runtime_identity_proven": False,
        "game_build": False, "apk_built": False,
        "gameplay_not_tested": True
    }
