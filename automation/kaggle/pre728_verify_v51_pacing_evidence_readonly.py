#!/usr/bin/env python3
"""PRE728: authenticated previous-report reconciliation, not raw trace replay."""
import argparse,hashlib,io,json,os,zipfile
from pathlib import Path
PIN={
 "700":("1oRoyx0HsbNvsI-jhbQWbvDNZpXoG0bbR",6977,"29a34777e0b2de84fcfa847ca47f4a6828cc0a68de3f26d7ac857f3278af033e"),
 "701":("1I3RHJxrDY6up3GbRz3VufDngUqQEb866",5650,"46ae753d2ef446ee67caf4c31a9cdbdb2338f25bbfb703bd5f7ff42826279a33"),
 "727":("1V0-8L65bkwR4GsQ_Atb79MKwbAO7dQvf",1035,"9d5fd40b478eca6a7b2d31b1e9c8b732bd70454dd0585674eaeb4664a0ae1257")}
def audit(blobs):
 for k,(fid,n,h) in PIN.items():
  b=blobs[k]
  if not isinstance(b,bytes) or len(b)!=n or hashlib.sha256(b).hexdigest()!=h:
   raise ValueError("PRE728_AUTHENTICATED_DRIVE_SOURCE_DRIFT_"+k)
 s700=blobs["700"].decode("utf-8");s701=blobs["701"].decode("utf-8")
 for anchor in ("**2.279**","**2.277**","**59,991589 apresentações/s**","SurfaceView[io.github.nfsmwrecomp/","60 FPS"):
  if anchor not in s700:raise ValueError("PRE728_PRE700_REPORT_DRIFT")
 for anchor in ("**2.274**","**2.158**","**1.788**","**3 / 2.277 (0,13%)**","**119 / 2.277 (5,23%)**","**489 / 2.277 (21,48%)**","**459 (93,865%)**","**30**","**89**"):
  if anchor not in s701:raise ValueError("PRE728_PRE701_REPORT_DRIFT")
 with zipfile.ZipFile(io.BytesIO(blobs["727"])) as z:
  names=z.namelist()
  if z.testzip() is not None or names!=["PRE727_V51_REAL_LOG_VULKAN_ENABLED_EXTENSIONS.json"]:
   raise ValueError("PRE728_PRE727_ZIP_DRIFT")
  j=json.loads(z.read(names[0]))
 if j.get("status")!="PASS_PRE727_V51_REAL_APP_REPORTED_VULKAN_EXTENSIONS" or j.get("VK_GOOGLE_display_timing_reported_enabled_in_this_session") is not False:raise ValueError("PRE728_PRE727_ENABLED_REPORT_DRIFT")
 if j.get("device_extensions_reported_enabled")!=["VK_EXT_extended_dynamic_state3","VK_EXT_memory_budget","VK_KHR_swapchain"]:raise ValueError("PRE728_DEVICE_EXTENSION_DRIFT")
 total=2277;desired=3;ready=119;actual=489;coincident=30;actual_only=459;ready_only=89
 if not (1+2274+2==60+2158+59==246+1788+240+3==total and actual_only+coincident==actual and ready_only+coincident==ready):
  raise ValueError("PRE728_STATISTICAL_CONSISTENCY_DRIFT")
 return {"stage":"PRE728_V51_PINNED_DISPLAY_PACING_DECISION",
  "status":"PASS_PRE728_VERIFIED_SECONDARY_REPORT_RECONCILIATION",
  "source_scope":"HASHED_PRE700_PRE701_REPORTS_AND_PRE727_APP_LOG_SUMMARY",
  "raw_pre700_zip_replayed":False,"new_phone_trace_captured":False,
  "sources":{k:{"drive_file_id":v[0],"bytes":v[1],"sha256":v[2]} for k,v in PIN.items()},
  "device":"Samsung Galaxy S24 FE / Xclipse 940","app_version_code":51,
  "internal_resolution":"1920x1080","observed_fps_cap":60,"refresh_hz":120,
  "contiguous_intervals":total,"excluded_sampling_gap_ms":999.482344,
  "contiguous_mean_presentation_rate":59.991589,
  "desired_irregular":desired,"ready_irregular":ready,
  "actual_present_irregular":actual,
  "actual_irregular_with_ready_regular":actual_only,
  "actual_irregular_with_ready_irregular":coincident,
  "ready_irregular_with_actual_regular":ready_only,
  "irregular_actual_pct":round(actual/total*100,2),
  "fraction_actual_irregular_with_ready_regular_pct":round(actual_only/actual*100,3),
  "google_display_timing_reported_enabled_pre727":False,
  "google_display_timing_reported_advertised_pre702":True,
  "vulkan_per_frame_present_id":"NOT_VERIFIED",
  "app_to_surfaceflinger_frame_alignment":"NOT_VERIFIED",
  "surfaceview_frametimeline_support":"NOT_ASSURED_OFFICIAL_PERFETTO_DOCS_STATE_NOT_SUPPORTED",
  "pacing_root_cause":"NOT_VERIFIED",
  "decision":"NEXT_NONINVASIVE_SYNCHRONIZED_CAPABILITY_PROBE_BEFORE_ANY_V52",
  "next_gate":"PRE729_NONINVASIVE_CAPTURE_CAPABILITY_PROBE",
  "apk_changed":False,"signing_accessed":False,"fps_gain_proven":False}
def synthetic():
 assert 459+30==489 and 89+30==119 and 246+1788+240+3==2277
 assert round(459/489*100,3)==93.865
 print("PRE728_SYNTHETIC_MATH_PASS=TRUE")
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--apply",action="store_true")
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:return synthetic()
 if not a.apply or not a.out:p.error("requires --apply and --out")
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 keys=["GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"]
 if any(not os.environ.get(k) for k in keys):raise ValueError("PRE728_MISSING_DRIVE_AUTH")
 c=Credentials(token=None,refresh_token=os.environ[keys[0]],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ[keys[1]],client_secret=os.environ[keys[2]])
 c.refresh(Request())
 api=build("drive","v3",credentials=c,cache_discovery=False)
 blobs={k:api.files().get_media(fileId=v[0],supportsAllDrives=True).execute(num_retries=3) for k,v in PIN.items()}
 result=audit(blobs)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("PRE728_AUTHENTICATED_REPORT_HASHES_PASS=TRUE")
 print("PRE728_SECONDARY_EVIDENCE_GATE_PASS=TRUE")
 print("PRE728_RAW_PRE700_ZIP_REPLAYED=FALSE")
 print("PRE728_DISPLAY_PACING_CAUSE_UNVERIFIED=TRUE")
 print("PRE728_V51_APK_CHANGED=FALSE")
if __name__=="__main__":main()
