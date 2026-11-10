#!/usr/bin/env python3
"""PRE674: fail-closed validation of the SpeedBreaker-informed backlog.
Pure Python stdlib, READ ONLY, no upstream imports, SDK, APK or credentials.
CI gate proves workflow structure/invariants, NOT GPU performance.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re,sys
from datetime import datetime,timezone
from pathlib import Path

SRC=Path("docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json")
FLOW=Path("docs/FLUXO_SPEEDBREAKER_NFSMW_ANDROID.md")
STUDY=Path("docs/PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md")
OUT=Path("/tmp/nfsmw-speedbreaker-flow/PRE674_SPEEDBREAKER_WORKFLOW_BACKLOG_GATE.json")
EXPECTED={
 "schema":"nfsmw-speedbreaker-backlog-v1",
 "upstream_commit":"fe04285d7629377c6e422a6ace8f535368f23c31",
 "baseline":"V51 PRE652",
 "signed_apk_sha256":"207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b",
 "certificate_sha256":"1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b",
 "renderer_sha256":"9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2",
}
REQUIRED_GATES=[
"G0_upstream_pin","G1_readonly_map","G2_host_safety_equivalence",
"G3_real_arm64_noapk","G4_device_caps_and_profile",
"G5_ab_visual_frametime_thermal_input",
"G6_authorized_permanent_signature_release","G7_drive_backup_context_readback"
]
PAUSED={"SB-05","SB-06"}
MANDATORY_PRESERVE={"graphics","shaders","shadows","physics","thermal_protection",
"touch","PG-9076","Nitro PRE398","BMW tuning","C3 guards","user saves","signing"}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def require(cond:bool,msg:str)->None:
 if not cond:raise ValueError(msg)
def check(x:dict)->dict:
 require(x.get("schema")==EXPECTED["schema"],"unexpected backlog schema")
 upstream=x.get("upstream",{})
 require(upstream.get("repository")=="SpeedBreakerProject/speedbreaker","unknown upstream")
 require(upstream.get("commit")==EXPECTED["upstream_commit"],"upstream commit unpinned")
 require(upstream.get("license_family")=="GPL-3.0-or-later","upstream GPL constraint missing")
 require(upstream.get("read_only_reference") is True and upstream.get("automatic_upstream_code_import") is False,
         "automatic import of external code forbidden")
 base=x.get("internal",{})
 require(base.get("baseline")==EXPECTED["baseline"] and base.get("version_code")==51,
         "baseline must be audited before changing workflow")
 require(base.get("package")=="io.github.nfsmwrecomp","Android package mismatch")
 require(base.get("signed_apk_sha256")==EXPECTED["signed_apk_sha256"],"baseline APK identity changed")
 require(base.get("certificate_sha256")==EXPECTED["certificate_sha256"],"permanent signer must be stable")
 require(base.get("native_renderer_source_sha256")==EXPECTED["renderer_sha256"],
         "renderer baseline fingerprint changed")
 require(base.get("internal_resolution")==[1920,1080] and base.get("target_fps_limit")==120,
         "graphics/performance constraints changed")
 require(MANDATORY_PRESERVE.issubset(set(base.get("preserve",[]))),
         "missing protected subsystems")
 policy=x.get("policy",{})
 require(policy.get("gates")==REQUIRED_GATES,"nonsequential or missing validation gates")
 for k in ("default_off","no_apk_in_planning","no_claim_of_proven_fps_gain"):
  require(policy.get(k) is True,"unsafe workflow policy: "+k)
 require(policy.get("automatic_release") is False,"automatic release is forbidden")
 cand=x.get("candidates",[])
 require(isinstance(cand,list) and len(cand)==7,"candidate count changed")
 require([z.get("id") for z in cand]==[f"SB-{i:02}" for i in range(1,8)],
         "candidate identifiers changed or duplicated")
 status=set()
 for z in cand:
  i=z["id"]
  require(z.get("priority") in (0,1,2,3,4),"bad priority "+i)
  require(z.get("evidence_type")=="external_readonly_concept_only",
          "upstream theory incorrectly promoted to runtime proof "+i)
  require(z.get("graphics_fidelity_required") is True,
          "graphics fidelity waived "+i)
  require(isinstance(z.get("source_paths"),list) and z["source_paths"] and
          all(p.startswith("runtime/") and ".." not in p and p.endswith((".h",".cpp")) for p in z["source_paths"]),
          "bad anchored upstream paths "+i)
  require(isinstance(z.get("required_evidence"),list) and z["required_evidence"],
          "candidate missing next evidence "+i)
  require(isinstance(z.get("hypothesis"),str) and len(z["hypothesis"])>20,
          "candidate lacks hypothesis "+i)
  require(z.get("status") not in ("released","fps_gain_proven","installed","implemented"),
          "unverified candidate promoted to release "+i)
  status.add(z.get("status"))
  if i in PAUSED:require(z.get("status")=="paused",i+" must remain paused")
 require(cand[0].get("status")=="active_audit",
         "SB-01 current priority must remain explicit until completion")
 require(cand[-1].get("status")=="no_android_port",
         "Smooth Motion Android capability not demonstrated")
 return {"candidates":len(cand),"paused":sorted(PAUSED),"status_types":sorted(status),
         "gates":len(REQUIRED_GATES),"external_reference_only":True,
         "device_runtime_validated":False,"fps_gain_proven":False,
         "no_upstream_code_import":True,"no_apk_built":True}
def selftest(x):
 count=0
 def invalid(mut):
  nonlocal count
  y=copy.deepcopy(x);mut(y)
  try:check(y)
  except ValueError:count+=1
  else:raise RuntimeError("unsafe sample incorrectly accepted")
 invalid(lambda t:t["upstream"].update(automatic_upstream_code_import=True))
 invalid(lambda t:t["internal"].update(version_code=52))
 invalid(lambda t:t["internal"].update(certificate_sha256="0"*64))
 invalid(lambda t:t["policy"].update(automatic_release=True))
 invalid(lambda t:t["policy"].update(default_off=False))
 invalid(lambda t:t["policy"]["gates"].remove("G4_device_caps_and_profile"))
 invalid(lambda t:t["candidates"][4].update(status="active_audit"))
 invalid(lambda t:t["candidates"][0].update(evidence_type="measured_on_android"))
 invalid(lambda t:t["candidates"][1].update(graphics_fidelity_required=False))
 invalid(lambda t:t["candidates"][6].update(status="implemented"))
 invalid(lambda t:t["candidates"][0].update(source_paths=["../../unsafe"]))
 return count
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--self-test",action="store_true")
 args=parser.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 report={"stage":"PRE674_SPEEDBREAKER_IDEAS_WORKFLOW_GUARDS",
         "github_run_id":os.getenv("GITHUB_RUN_ID","LOCAL"),
         "timestamp_utc":datetime.now(timezone.utc).isoformat(),
         "apk_built":False,"upstream_code_imported":False,"real_fps_gain_proven":False}
 try:
  doc=json.loads(SRC.read_text(encoding="utf-8"))
  evidence=check(doc)
  f=FLOW.read_bytes()
  study=STUDY.read_bytes()
  for tag in (b"SB-01",b"SB-02",b"SB-03",b"SB-04",b"SB-05",b"SB-06",b"SB-07",
              b"G0",b"G7",b"GPL",b"1920",b"PRE673"):
   require(tag in f,"workflow text missing "+tag.decode())
  require(b"shadow_lend.h" in study and b"PASS_PROFILE" in study,
          "upstream review unavailable")
  tests=selftest(doc) if args.self_test else 0
  report.update({"status":"PASS_BACKLOG_POLICY_AND_11_NEGATIVE_CASES" if args.self_test else "PASS_BACKLOG_POLICY",
                 "negative_cases_passed":tests,"evidence":evidence,
                 "source_sha256":{str(SRC):sha(SRC.read_bytes()),str(FLOW):sha(f),
                                  str(STUDY):sha(study)}})
 except Exception as e:
  report.update({"status":"FAILED_CLOSED","error_type":type(e).__name__,
                 "error_summary":str(e)[:300]})
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 for k in ("status","negative_cases_passed","error_type"):
  print("PRE674_"+k.upper()+"="+str(report.get(k,"none")))
 return 0 if report["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
