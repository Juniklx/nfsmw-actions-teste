#!/usr/bin/env python3
"""PRE239: validate eight PAL money-store injection recipes in memory only.

No game edits, APK build, extra guest dereferences, trainer, save changes or signing.
The C++ snippets are candidates for later controlled instrumentation, NOT a cheat.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre239/NFSMW_PRE239_PAL_INJECTION_RECIPES.json")
TARGETS = {
    "sub_8256BFC8": {
        "filename": "workspace/nativo/app/generated/default/nfsmw_recomp.103.cpp",
        "stores": [
            ("r23,12(r10)", "ctx.r10.u32 + 12", "r23.u32"),
            ("r4,12(r10)", "ctx.r10.u32 + 12", "ctx.r4.u32"),
            ("r11,12(r10)", "ctx.r10.u32 + 12", "ctx.r11.u32"),
        ],
        "guest_pc_candidates_from_PRE237": [
            "0x8256C0B8", "0x8256C0C4", "0x8256C0D4",
        ],
    },
    "sub_82564D80": {
        "filename": "workspace/nativo/app/generated/default/nfsmw_recomp.7.cpp",
        "stores": [
            ("r9,12(r11)", "ctx.r11.u32 + 12", "ctx.r9.u32"),
            ("r24,12(r11)", "ctx.r11.u32 + 12", "r24.u32"),
            ("r7,12(r11)", "ctx.r11.u32 + 12", "ctx.r7.u32"),
            ("r24,12(r11)", "ctx.r11.u32 + 12", "r24.u32"),
            ("r5,12(r11)", "ctx.r11.u32 + 12", "ctx.r5.u32"),
        ],
        "guest_pc_candidates_from_PRE237": [
            "0x8256597C", "0x82565A40", "0x82565A54",
            "0x8256606C", "0x8256608C",
        ],
    },
}
LOG_HEADER = "workspace/nativo/sdk/include/rex/logging.h"
LOG_SOURCES = {
    "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp",
    "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp",
}
DEF = re.compile(r"\\bDEFINE_REX_FUNC\\((sub_[0-9A-Fa-f]{8})\\)")
COMMENT = re.compile(r"^\\s*//\\s*stw\\s+(r\\d+,\\s*12\\(r\\d+\\))\\s*$", re.I)
STORE = re.compile(r"^\\s*REX_STORE_U32\\(([^,;]+),\\s*([^;]+)\\);\\s*$")
LOG_REGEX = re.compile(r"\\b(?:rex::logging|rex::Log|REX_LOG|LOG_[A-Z_]+|spdlog::|#include <rex/logging.h>)")

def body_for_function(src, target):
    all_defs = list(DEF.finditer(src))
    for i, m in enumerate(all_defs):
        if m.group(1) == target:
            return src[m.start():all_defs[i+1].start() if i+1 < len(all_defs) else len(src)]
    raise ValueError("Target function missing")

def validate_one(src, spec, target):
    body = body_for_function(src, target)
    lines = body.splitlines(keepends=True)
    matches = []
    for i, line in enumerate(lines):
        comment = COMMENT.match(line)
        if not comment:
            continue
        if i + 1 >= len(lines):
            raise ValueError("Store without next line")
        st = STORE.match(lines[i+1])
        if not st:
            continue
        matches.append((i, comment.group(1).replace(" ", ""), st.group(1).strip(), st.group(2).strip()))
    expected = spec["stores"]
    if len(matches) != len(expected):
        raise ValueError(f"Mismatch store count for {target}: {len(matches)}")
    rows = []
    replacement = list(lines)
    for ix, ((line_index, mnemonic, addr, value), (exp_mnem, exp_addr, exp_value)) in enumerate(zip(matches, expected)):
        if (mnemonic.lower(), addr, value) != (exp_mnem.lower(), exp_addr, exp_value):
            raise ValueError(f"Store identity mismatch in {target} at index {ix}")
        # Original write is unchanged. A disabled-by-default post-store probe
        # uses already-calculated register expressions; no memory read.
        marker = f"NFSMW_PRE239_MONEY_PROBE_{target}_{ix+1}"
        probe = (
            f"#if defined(NFSMW_MONEY_STORE_TRACE_ENABLED)\\n"
            f"  NFSMW_MONEY_STORE_TRACE({ix+1}, "
            f"static_cast<uint32_t>({addr}), static_cast<uint32_t>({value}));\\n"
            f"#endif // {marker}\\n"
        )
        # Not integrating marker into generated source in this stage.
        replacement[line_index + 1] += probe
        rows.append({
            "ordinal_in_function": ix+1,
            "source_line_in_function": line_index+2,
            "pc_candidate": spec["guest_pc_candidates_from_PRE237"][ix],
            "comment": mnemonic,
            "original_store": lines[line_index+1].strip(),
            "proposed_post_store_probe": probe,
            "no_new_guest_memory_reads": True,
            "disabled_by_default": True,
        })
    dry = "".join(replacement)
    if dry.count("REX_STORE_U32(") != body.count("REX_STORE_U32("):
        raise ValueError("Original write count changed in memory")
    if dry.count("NFSMW_MONEY_STORE_TRACE(") != len(matches):
        raise ValueError("Probe count mismatch")
    if any(row["original_store"] not in dry for row in rows):
        raise ValueError("Original write missing from dry run")
    if "NFSMW_PRE239_MONEY_PROBE" in body:
        raise ValueError("Preexisting unexpected PRE239 markers")
    return {"function": target, "dry_run_only": True,
            "source_mutated": False, "candidate_sites": rows,
            "original_stores_preserved": True}

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {"stage": "PRE239_IN_MEMORY_PAL_PROBE_RECIPE",
              "status": "FAILED", "phase": "START", "pre99_verified": False,
              "source_mutated": False, "apk_built": False,
              "guest_memory_extra_reads": False, "saves_touched": False,
              "signing_material_touched": False, "cheats_enabled": False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre239_") as tmp:
            report["phase"] = "VERIFY_PRE99"
            path = Path(tmp)/"pre99.tar.gz"
            download(drive_client(), path)
            sha, _md5, size = sha_file(path)
            if sha != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("Authenticated PRE99 SHA or size mismatch")
            report["pre99_verified"] = True
            report["phase"] = "READ_SELECTED_FILES"
            paths = {v["filename"] for v in TARGETS.values()} | LOG_SOURCES | {LOG_HEADER}
            content = {}
            with tarfile.open(path, "r:gz") as tf:
                for m in tf:
                    if m.isfile() and m.name.lstrip("./") in paths:
                        if m.size > 3_000_000:
                            raise ValueError("Source member unexpectedly large")
                        f = tf.extractfile(m)
                        if f is None:
                            raise ValueError("Cannot read member")
                        data = f.read()
                        content[m.name.lstrip("./")] = {
                            "text": data.decode("utf-8", "replace"),
                            "sha256": hashlib.sha256(data).hexdigest(),
                        }
            for v in TARGETS.values():
                if v["filename"] not in content:
                    raise ValueError("Missing generated source")
            report["phase"] = "VALIDATE_IN_MEMORY_PATCH_RECIPE"
            validated = []
            for target, spec in TARGETS.items():
                src = content[spec["filename"]]
                item = validate_one(src["text"], spec, target)
                item["source_filename"] = spec["filename"]
                item["source_sha256"] = src["sha256"]
                validated.append(item)
            report["functions"] = validated
            report["observed_sites"] = sum(len(x["candidate_sites"]) for x in validated)
            report["phase"] = "AUDIT_EXISTING_LOGGING"
            report["logging_examples"] = []
            for filename in sorted(LOG_SOURCES | {LOG_HEADER}):
                if filename not in content:
                    continue
                src = content[filename]
                lines = src["text"].splitlines()
                matches = [{"line":i+1, "text":s.strip()[:260]}
                           for i,s in enumerate(lines)
                           if LOG_REGEX.search(s)]
                report["logging_examples"].append({
                    "filename":filename, "sha256":src["sha256"],
                    "total_matches":len(matches), "samples":matches[:30],
                })
            report["limitations"] = [
                "The codegen source is generated output: do not edit directly for release.",
                "Potential store-site PC mapping is based on PRE237 static xref, not runtime proof.",
                "Log implementation and placement in maintained source are not validated by this dry run.",
                "Probe macro intentionally undefined: enabling requires a separately verified integration.",
                "No guest memory load, account pointer access, cheat activation or APK produced.",
            ]
            report["status"] = "AUDIT_OK" if report["observed_sites"] == 8 else "INCOMPLETE"
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["failed_phase"] = report["phase"]
        print("PRE239_FAILURE", type(exc).__name__, report["phase"])
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\\n", encoding="utf-8")
    print("PRE239_STATUS", report["status"])
    print("PRE239_SITES", report.get("observed_sites", 0))
    return 0 if report["status"]=="AUDIT_OK" else 1

if __name__ == "__main__":
    sys.exit(main())
