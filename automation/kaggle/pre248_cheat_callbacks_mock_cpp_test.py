#!/usr/bin/env python3
"""PRE248 synthetic C++ syntax/link/bounded-callback tests; NEVER game build.

Compile PRE246/PRE247 callback module texts with a local mock REXLOG_INFO
header. Real Rex SDK and Android linking remain explicitly UNTESTED.
"""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path
from pre246_passive_money_probe_patch import CPP_TEXT as MONEY_CPP
from pre247_pal_meter_passive_probe_patch import CPP_TEXT as METER_CPP

OUT = Path("/tmp/nfsmw-pre248/NFSMW_PRE248_CXX_CALLBACK_ISOLATED_MOCK.json")
MOCK_HEADER = r"""#pragma once
#include <atomic>
extern std::atomic<unsigned> nfsmw_mock_logs;
template<typename... Args>
void nfsmw_mock_log(const char*, Args&&...) noexcept {
  nfsmw_mock_logs.fetch_add(1u, std::memory_order_relaxed);
}
#define REXLOG_INFO(...) nfsmw_mock_log(__VA_ARGS__)
"""
HARNESS = r"""#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>
#include <iostream>
std::atomic<unsigned> nfsmw_mock_logs{0u};
extern "C" void NFSMW_PRE246_TRACE_STORE(unsigned, unsigned, unsigned, unsigned) noexcept;
extern "C" void NFSMW_PRE247_TRACE_METER(unsigned, unsigned, unsigned) noexcept;
int main() {
  // Invalid sites should not generate logs.
  NFSMW_PRE246_TRACE_STORE(0,0,0,0);
  NFSMW_PRE246_TRACE_STORE(9,0,0,0);
  NFSMW_PRE247_TRACE_METER(0,0,0);
  NFSMW_PRE247_TRACE_METER(9,0,0);
  if (nfsmw_mock_logs.load()!=0u) return 10;
  // Each of sixteen independent sites can emit at most twelve records.
  for (unsigned site=1;site<=8;++site) {
    for (unsigned i=0;i<100;++i) {
      NFSMW_PRE246_TRACE_STORE(site,0x1000u+i,i,i+1);
      NFSMW_PRE247_TRACE_METER(site,0x2000u+i,0x3f800000u);
    }
  }
  if (nfsmw_mock_logs.load()!=192u) return 11;
  // Concurrent calls after saturation must not increase count.
  std::vector<std::thread> threads;
  for (unsigned i=0;i<8;++i) threads.emplace_back([] {
    for (unsigned k=0;k<300;++k) {
      NFSMW_PRE246_TRACE_STORE(8,0,0,0);
      NFSMW_PRE247_TRACE_METER(8,0,0);
    }
  });
  for (auto& th:threads) th.join();
  if (nfsmw_mock_logs.load()!=192u) return 12;
  std::cout << "PRE248_MOCK_LOGGING_16_SITES_192_RECORD_MAX_OK\n";
}
"""
def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r = {"stage":"PRE248_MOCK_CXX_SYNTAX_LINK_AND_LOG_CAP",
         "status":"FAILED", "phase":"START",
         "android_game_compiled":False, "apk_built":False,
         "signer_accessed":False, "game_sources_modified":False,
         "save_files_touched":False, "cheats_enabled":False,
         "real_rex_logging_sdk_compiled":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre248_") as t:
            root=Path(t)
            include=root/"rex/logging"
            include.mkdir(parents=True)
            (include/"macros.h").write_text(MOCK_HEADER,encoding="utf-8")
            (root/"money.cpp").write_text(MONEY_CPP,encoding="utf-8")
            (root/"meters.cpp").write_text(METER_CPP,encoding="utf-8")
            (root/"test.cpp").write_text(HARNESS,encoding="utf-8")
            r["phase"]="COMPILE_SYNTHETIC_CALLBACKS"
            cmd=["g++","-std=c++20","-O1","-Wall","-Wextra","-Werror","-pthread",
                 "-I",str(root),str(root/"money.cpp"),str(root/"meters.cpp"),
                 str(root/"test.cpp"),"-o",str(root/"a.out")]
            build=subprocess.run(cmd,capture_output=True,text=True,timeout=40)
            r["synthetic_compile_ok"]=build.returncode==0
            if build.returncode:
                r["safe_compiler_tail"]=(build.stderr or "")[-1400:]
                raise ValueError("PRE248: mock callback C++ compile failed")
            r["phase"]="EXECUTE_SYNTHETIC_TEST"
            test=subprocess.run([str(root/"a.out")],capture_output=True,text=True,timeout=30)
            r["synthetic_test_exit_code"]=test.returncode
            r["synthetic_test_output"]=(test.stdout or "")[:180]
            if test.returncode or "PRE248_MOCK_LOGGING_16_SITES_192_RECORD_MAX_OK" not in test.stdout:
                raise ValueError("PRE248: mock callback test failed")
            r["site_count"]=16
            r["max_logged_records_across_sites"]=192
            r["limits"]=[
                "The logging header is a local stub: this does not validate real REXLOG_INFO semantics.",
                "The test is host C++ only; no Android NDK, guest code, APK, signing or in-game cheats.",
                "The 16 site mappings remain static candidates and must be tested against actual gameplay."
            ]
            r["phase"]="COMPLETE"
            r["status"]="AUDIT_OK"
    except Exception as e:
        r["exception_type"]=type(e).__name__
        r["failed_phase"]=r["phase"]
        print("PRE248_ERROR",type(e).__name__,r["phase"])
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE248_STATUS",r["status"],"MOCK_CXX",r.get("synthetic_compile_ok",False))
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
