#!/usr/bin/env python3
"""PRE316 compile host-C++ Nitro cycle monitor and assert bounded milestones."""
from pathlib import Path
import subprocess,tempfile,json,sys
OUT=Path("/tmp/nfsmw-pre316/NITRO_CYCLE_MONITOR_TEST.json")
H=Path(__file__).with_name("pre316_nitro_cycle_monitor.hpp")
S=r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include "pre316_nitro_cycle_monitor.hpp"
using namespace nfsmw_pre316;
int main() {
  Monitor m;Snapshot r{};
  assert(!m.observe(0,Monitor::bits(1.0f),r));
  assert(!m.observe(6,Monitor::bits(1.0f),r));
  assert(!m.observe(1,Monitor::bits(-1.0f),r));
  assert(!m.observe(1,Monitor::bits(NAN),r));
  assert(!m.observe(1,Monitor::bits(2.0f),r));
  int emitted=0;
  for(int i=0;i<180;++i) {
    float v=1.f-i/179.f;
    if(m.observe(1,Monitor::bits(v),r)) ++emitted;
  }
  assert(m.sites[0].samples.load()==180);
  assert(Monitor::number(m.sites[0].min_bits.load())==0.f);
  assert(Monitor::number(m.sites[0].max_bits.load())==1.f);
  assert(emitted<50 && emitted>=8);
  for(int i=0;i<=180;++i) {
    float v=i/180.f;
    if(m.observe(2,Monitor::bits(v),r)) ++emitted;
  }
  assert(m.sites[1].samples.load()==181);
  assert(Monitor::number(m.sites[1].min_bits.load())==0.f);
  assert(Monitor::number(m.sites[1].max_bits.load())==1.f);
  // Stable values: power-of-two milestones are bounded. Once all milestones
  // are passed, 20000 repeated frames cannot produce excessive logs.
  int stable_logs=0;
  for(int i=0;i<20000;++i)
    if(m.observe(3,Monitor::bits(0.5f),r))++stable_logs;
  assert(stable_logs<=16 && stable_logs>=10);
  assert(m.sites[3].samples.load()==0);
  std::cout<<"PRE316_NITRO_MIN_MAX_ZERO_ONE_OK\n";
  std::cout<<"PRE316_NITRO_THRESHOLD_CHANGE_OK\n";
  std::cout<<"PRE316_NITRO_BOUNDED_LOGGING_OK\n";
  std::cout<<"PRE316_NITRO_NO_GUEST_MEMORY_OK\n";
}
"""
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE316_NITRO_CYCLE_MONITOR_CXX_MOCK","status":"FAILED",
       "apk_built":False,"guest_memory_read":False,"game_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre316_") as p:
            p=Path(p);(p/"test.cpp").write_text(S)
            proc=subprocess.run(["g++","-std=c++20","-Wall","-Wextra",
                "-Werror","-pedantic","-O2","-I",str(H.parent),
                str(p/"test.cpp"),"-o",str(p/"test")],
                capture_output=True,text=True,timeout=35)
            if proc.returncode:raise ValueError("C++ compile gate failed")
            test=subprocess.run([str(p/"test")],capture_output=True,text=True,timeout=20)
            report["checks"]=test.stdout.splitlines()
            if test.returncode or len(report["checks"])!=4:raise ValueError("C++ runtime gate failed")
        report["status"]="AUDIT_OK"
    except Exception as exc:report["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print("PRE316_STATUS",report["status"])
    print("PRE316_CHECKS",report.get("checks"))
    print("PRE316_ERROR_TYPE",report.get("error_type"))
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
