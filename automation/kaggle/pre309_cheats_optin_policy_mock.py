#!/usr/bin/env python3
"""PRE309 isolated host-C++ cheat gate mock. No game build, APK, saves or signer."""
from pathlib import Path
import subprocess,tempfile,json,hashlib,sys
OUT=Path("/tmp/nfsmw-pre309/PRE309_OPTIN_CHEAT_POLICY_MOCK.json")
HEADER=Path(__file__).with_name("pre309_cheats_optin_policy.hpp")
SOURCE=r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include "pre309_cheats_optin_policy.hpp"
using namespace nfsmw_pre309;
int main() {
  Switches s;
  Gate g{};
  assert(!s.enabled(Feature::Nitro));
  assert(!s.enabled(Feature::Speedbreaker));
  assert(!s.enabled(Feature::Money));
  // Both meters unchanged until ALL explicit gates and switch are true.
  for (auto f : {Feature::Nitro, Feature::Speedbreaker}) {
    assert(meter_value(s,f,g,0.25f,1.0f)==0.25f);
  }
  s.nitro.store(true);
  s.speedbreaker.store(true);
  s.money.store(true);
  assert(meter_value(s,Feature::Speedbreaker,g,0.25f,1.0f)==0.25f);
  g.verified_target=true;g.verified_owner=true;g.safe_session=true;
  assert(meter_value(s,Feature::Nitro,g,0.25f,1.0f)==0.25f);
  g.explicit_user_opt_in=true;
  assert(meter_value(s,Feature::Nitro,g,0.25f,1.0f)==1.0f);
  assert(meter_value(s,Feature::Speedbreaker,g,0.25f,1.0f)==1.0f);
  // Do not reinterpret meter values that violate validated 0..max domain.
  assert(meter_value(s,Feature::Nitro,g,-1.0f,1.0f)==-1.0f);
  assert(meter_value(s,Feature::Nitro,g,1.2f,1.0f)==1.2f);
  assert(meter_value(s,Feature::Nitro,g,0.5f,0.0f)==0.5f);
  float invalid=std::numeric_limits<float>::quiet_NaN();
  assert(std::isnan(meter_value(s,Feature::Nitro,g,invalid,1.0f)));
  assert(meter_value(s,Feature::Nitro,g,0.5f,invalid)==0.5f);
  // The money handler is intentionally a no-op; no validated balance writer.
  assert(money_value(s,g,12345u)==12345u);
  assert(money_value(s,g,0xffffffffu)==0xffffffffu);
  s.reset();
  assert(!s.enabled(Feature::Nitro));
  assert(!s.enabled(Feature::Speedbreaker));
  assert(!s.enabled(Feature::Money));
  assert(meter_value(s,Feature::Nitro,g,0.25f,1.0f)==0.25f);
  std::cout<<"PRE309_DISABLED_DEFAULT_OK\n";
  std::cout<<"PRE309_ALL_FOUR_PERMISSION_GATES_OK\n";
  std::cout<<"PRE309_FLOAT_DOMAIN_FAILCLOSED_OK\n";
  std::cout<<"PRE309_MONEY_PASS_THROUGH_OK\n";
}
"""
def run():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE309_OPTIN_CHEAT_POLICY_MOCK","status":"FAILED",
            "actual_cheat_enabled":False,"game_compiled":False,"apk_built":False,
            "save_modified":False,"signer_accessed":False}
    try:
        raw=HEADER.read_bytes()
        result["policy_sha256"]=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre309_") as d:
            s=Path(d)/"test.cpp";s.write_text(SOURCE)
            dest=Path(d)/"test"
            c=subprocess.run(["g++","-std=c++20","-Wall","-Wextra","-Werror","-pedantic",
                              "-O1","-I",str(HEADER.parent),str(s),"-o",str(dest)],
                            text=True,capture_output=True,timeout=45)
            if c.returncode:raise ValueError("compile failed")
            r=subprocess.run([str(dest)],text=True,capture_output=True,timeout=20)
            expected=["PRE309_DISABLED_DEFAULT_OK","PRE309_ALL_FOUR_PERMISSION_GATES_OK",
                      "PRE309_FLOAT_DOMAIN_FAILCLOSED_OK","PRE309_MONEY_PASS_THROUGH_OK"]
            if r.returncode or any(x not in r.stdout for x in expected):
                raise ValueError("synthetic assertions failed")
            result["status"]="AUDIT_OK"
            result["validated_assertions"]=expected
            result["actual_cheat_enabled"]=False
    except Exception as e:result["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print("PRE309_STATUS",result["status"])
    print("PRE309_ASSERTIONS",len(result.get("validated_assertions",[])))
    print("PRE309_REAL_CHEATS_ENABLED",result["actual_cheat_enabled"])
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(run())
