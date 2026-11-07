#!/usr/bin/env python3
"""PRE317: add PRE316 passive Nitro cycle summaries to disposable PRE247 logger.
It preserves all PRE247 stores, guest memory accesses and original log callbacks.
No runtime cheat, default controls unchanged; no signing, save, or guest edits.
"""
from pathlib import Path
import hashlib
from pre247_pal_meter_passive_probe_patch import CPP_REL,CPP_TEXT
HEADER=Path(__file__).with_name("pre316_nitro_cycle_monitor.hpp")
HEADER_NAME="pre316_nitro_cycle_monitor.hpp"
INCLUDE='#include "'+HEADER_NAME+'"\n'
ANCHOR="  if (site < 1 || site > 8) return;\n"
INSERT="""  if (site >= 1u && site <= 5u) {
    nfsmw_pre316::Snapshot snap{};
    if (g_pre316_nitro_cycle.observe(site, stored_f32_bits, snap)) {
      REXLOG_INFO("[NFSMW_PRE316_NITRO_CYCLE] site={} n={} last_f32_bits=0x{:08X} min_f32_bits=0x{:08X} max_f32_bits=0x{:08X} band_transitions={}",
                  snap.site, snap.samples, snap.last_bits,
                  snap.min_bits, snap.max_bits, snap.threshold_events);
    }
  }
"""
GLOBAL="static nfsmw_pre316::Monitor g_pre316_nitro_cycle{};\n"
def sha(b):return hashlib.sha256(b).hexdigest()
def inject(src:str)->str:
    if src.count(ANCHOR)!=1 or HEADER_NAME in src or "NFSMW_PRE316_NITRO_CYCLE" in src:
        raise ValueError("PRE317: logger mismatch or already patched")
    if src.count("#include <rex/logging/macros.h>")!=1 or src.count("NFSMW_PRE247_TRACE_METER(")!=1:
        raise ValueError("PRE317: old callback anchors not unique")
    out=src.replace("#include <rex/logging/macros.h>\n",
        "#include <rex/logging/macros.h>\n"+INCLUDE,1)
    out=out.replace("// Log only already-computed store arguments. Bound volume to 12 per site.\n",
        "// Log only already-computed store arguments. Bound volume to 12 per site.\n"+GLOBAL,1)
    out=out.replace(ANCHOR,ANCHOR+INSERT,1)
    if (out.count("NFSMW_PRE316_NITRO_CYCLE")!=1 or
        out.count("NFSMW_PRE247_CHEATS_DIAG")!=1 or
        out.count("NFSMW_PRE247_TRACE_METER(")!=1):
        raise ValueError("PRE317: logger invariant failed")
    # Reversible exactness requirement.
    if out.replace(ANCHOR+INSERT,ANCHOR,1).replace(
            "// Log only already-computed store arguments. Bound volume to 12 per site.\n"+GLOBAL,
            "// Log only already-computed store arguments. Bound volume to 12 per site.\n",1).replace(
            "#include <rex/logging/macros.h>\n"+INCLUDE,
            "#include <rex/logging/macros.h>\n",1)!=src:
        raise ValueError("PRE317: logger not reversible")
    return out
def apply(root:Path)->dict:
    root=Path(root)
    cpp=root/CPP_REL
    if not cpp.is_file():raise ValueError("PRE317: missing PRE247 logger")
    before=cpp.read_text(encoding="utf8")
    if before!=CPP_TEXT:raise ValueError("PRE317: pinned pre247 logger differs")
    modified=inject(before)
    h=cpp.parent/HEADER_NAME
    if h.exists():raise ValueError("PRE317: header already exists")
    header_raw=HEADER.read_bytes()
    if not header_raw.startswith(b"#pragma once\n"):raise ValueError("PRE317: header mismatch")
    # Never touch game or save. Only compiled logger module/header in isolated workspace.
    cpp.with_suffix(cpp.suffix+".pre317_original").write_text(before,encoding="utf8")
    h.write_bytes(header_raw)
    cpp.write_text(modified,encoding="utf8")
    if cpp.read_text(encoding="utf8")!=modified or h.read_bytes()!=header_raw:
        raise ValueError("PRE317: readback mismatch")
    return {"status":"STAGED_PASSIVE_ONLY","module":CPP_REL,
            "original_module_sha256":sha(before.encode()),
            "modified_module_sha256":sha(modified.encode()),
            "header_sha256":sha(header_raw),
            "guest_stores_rewritten":0,"extra_guest_loads":0,
            "cheat_activation":False,"pre247_log_remains":True,
            "persistent_game_tree_changed":False}
