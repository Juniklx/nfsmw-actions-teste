#!/usr/bin/env python3
"""PRE238: read-only PAL store-site / logging audit for a future money probe.

Does NOT patch generated C++, build Android, read arbitrary guest memory, alter
saves, run trainers, or touch Android signing material.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download

OUT = Path("/tmp/nfsmw-pre238/NFSMW_PRE238_STORE_LOGGING_PROBE_AUDIT.json")
TARGETS = {"sub_8256BFC8", "sub_82564D80"}
GENERATED = re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
DEF = re.compile(r"\bDEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
STW = re.compile(r"^\s*//\s*stw\s+r\d+,\s*12\(r\d+\)", re.I)
WRITE = re.compile(r"\bREX_STORE_(?:U8|U16|U32|U64|F32|F64)\s*\(")
LOG_HINT = re.compile(r"\b(?:spdlog|rex::Log|Log::|LOG\w*|NFSMW_PRE\d+|logger|\binfo\s*\()\b", re.I)
LOG_FILES = {
    "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp",
    "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp",
}
MAX_GENERATED_BYTES = 3_000_000
MAX_SOURCE_BYTES = 2_000_000

def scan_function(source: str, file_name: str, target: str):
    matches = list(DEF.finditer(source))
    hit = next(((i, m) for i, m in enumerate(matches) if m.group(1) == target), None)
    if hit is None:
        return None
    i, start = hit
    end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
    body = source[start.start():end]
    lines = body.splitlines()
    rows = []
    for j, line in enumerate(lines):
        if not STW.search(line):
            continue
        neighborhood = lines[max(0, j - 5):min(len(lines), j + 7)]
        writes = [v.strip()[:280] for v in lines[j + 1:min(len(lines), j + 5)] if WRITE.search(v)]
        rows.append({
            "function_relative_line": j + 1,
            "guest_store_comment": line.strip()[:200],
            "nearby_host_write_macro": writes[:2],
            "nearby_excerpt": [v.strip()[:230] for v in neighborhood[:12]],
            "store_not_proven_money_alone": True,
        })
    return {
        "function": target,
        "generated_file": file_name,
        "file_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "definition_found": True,
        "commented_stw_plus12_count": len(rows),
        "store_sites": rows[:16],
        "store_sites_truncated": len(rows) > 16,
    }

def synthetic_syntax_probe(root: Path):
    # This compiles an original, isolated example, not a game patch.
    cpp = root / "pre238_synthetic_probe.cpp"
    cpp.write_text(r"""
#include <cstdint>
#include <vector>
struct Trace { std::uint32_t pc, guest_address, written_value; };
struct MockStore {
  std::vector<Trace> seen;
  void original_store(std::uint32_t, std::uint32_t) noexcept {}
  void after_store(std::uint32_t pc, std::uint32_t addr, std::uint32_t val) {
    seen.push_back({pc, addr, val});
  }
};
void perform_original_write_then_observe(MockStore& s, std::uint32_t pc,
                                         std::uint32_t addr, std::uint32_t value) {
  s.original_store(addr, value);
  s.after_store(pc, addr, value);
}
int main() { MockStore s; perform_original_write_then_observe(s, 1, 2, 3); }
""", encoding="utf-8")
    p = subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fsyntax-only", str(cpp)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, text=True,
    )
    return {
        "isolated_cpp_syntax_ok": p.returncode == 0,
        "compiler_return_code": p.returncode,
        "note": "Synthetic g++ test only; no SDK, generated game, or APK compilation.",
    }

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "stage": "PRE238_PAL_STORE_LOGGING_READONLY",
        "status": "NOT_VALIDATED",
        "snapshot_sha256_expected": EXPECTED_SHA256,
        "source_modified": False,
        "apk_built": False,
        "saves_modified": False,
        "signing_material_accessed": False,
        "runtime_guest_reads_added": False,
        "real_cheats_implemented": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre238_") as td:
            root = Path(td)
            report["phase"] = "GET_AUTHENTICATED_PRE99"
            archive = root / "snapshot.tar.gz"
            download(drive_client(), archive)
            actual_sha, _md5, actual_size = sha_file(archive)
            if actual_sha != EXPECTED_SHA256 or actual_size != EXPECTED_BYTES:
                raise ValueError("Pinned PRE99 archive digest or length mismatch")
            report["pre99_verified"] = True
            report["phase"] = "SCAN_READONLY"
            found = {}
            log_sources = []
            files = 0
            with tarfile.open(archive, "r:gz") as tf:
                for m in tf:
                    if not m.isfile():
                        continue
                    name = m.name.lstrip("./")
                    is_gen = bool(GENERATED.fullmatch(name))
                    is_log = name in LOG_FILES
                    if not (is_gen or is_log):
                        continue
                    if m.size > (MAX_GENERATED_BYTES if is_gen else MAX_SOURCE_BYTES):
                        raise ValueError("Unexpected source member size")
                    f = tf.extractfile(m)
                    if f is None:
                        raise ValueError("Cannot read selected tar member")
                    raw = f.read()
                    src = raw.decode("utf-8", errors="replace")
                    if is_gen:
                        files += 1
                        for candidate in TARGETS - found.keys():
                            if "DEFINE_REX_FUNC(" + candidate + ")" not in src:
                                continue
                            entry = scan_function(src, name, candidate)
                            if entry is not None:
                                entry["file_sha256"] = hashlib.sha256(raw).hexdigest()
                                found[candidate] = entry
                    if is_log:
                        hits = [
                            {"line": i + 1, "text": s.strip()[:240]}
                            for i, s in enumerate(src.splitlines())
                            if LOG_HINT.search(s)
                        ]
                        log_sources.append({
                            "path": name,
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "log_related_lines": len(hits),
                            "samples": hits[:18],
                        })
            report["pal_shards_scanned"] = files
            report["target_functions"] = [found[k] for k in sorted(found)]
            report["missing_targets"] = sorted(TARGETS - found.keys())
            report["logging_sources"] = log_sources
            report["phase"] = "SYNTHETIC_CPP_SYNTAX"
            report["syntax_probe"] = synthetic_syntax_probe(root)
            report["integration_constraints"] = [
                "No direct arbitrary guest memory reads, including through REX_LOAD_U32.",
                "Observe only already-computed guest address and written value at a verified store.",
                "Do not suppress debits or credits without full transaction semantics.",
                "Keep per-edition probes isolated and disabled by default.",
                "No game patch or live build produced in PRE238.",
            ]
            # A successful audit establishes only code-site candidates.
            report["status"] = (
                "AUDIT_OK" if files >= 100 and len(found) == 2
                and report["syntax_probe"]["isolated_cpp_syntax_ok"]
                else "INCOMPLETE"
            )
            report["phase"] = "COMPLETE"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["phase_on_failure"] = report.get("phase")
        print("PRE238_ERROR", type(exc).__name__, report.get("phase"))
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PRE238_STATUS", report["status"])
    print("PRE238_SHARDS", report.get("pal_shards_scanned", 0))
    print("PRE238_FUNCTIONS", [x["function"] for x in report.get("target_functions", [])])
    return 0 if report["status"] == "AUDIT_OK" else 1

if __name__ == "__main__":
    sys.exit(main())
