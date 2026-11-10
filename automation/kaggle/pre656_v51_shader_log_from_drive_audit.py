#!/usr/bin/env python3
"""PRE656: exact V51 PRE648 log SHA and PRE645 PAL shader inventory, read-only.
No APK build, signing, user saved games, native code changes or thermal operations.
The top-12 log output is censored: per pair totals are LOWER BOUNDS.
"""
import argparse,csv,hashlib,io,json,re,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre480_append_canonical_context_safe import drive_client,get_bytes

LOG_FILE_ID="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
LOG_SIZE=576129
LOG_SHA="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
PRE645_CSV_SHA="84e90b39eebb520a1f19cafe8162233198586357190690afa7900668561e6d42"
APK_V51_DRIVE_ID="1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws"
PAL_PACK="assets/nativo/nfsmw_shaders.nfsp"
LOG_LINE=re.compile(r"PRE648 GPU_SHADER10s draws=(\d+) normal=(\d+) deferred_sky=(\d+) invalid=(\d+) top=(.*)$")
TOP_ENTRY=re.compile(r"\[p(\d+) VS(\d+) PS(\d+) n(\d+)\]")
TIMESTAMP=re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]")
OUT=Path("/tmp/nfsmw-pre656")
def sha(b):return hashlib.sha256(b).hexdigest()
def run(csv_path:Path):
    invdata=csv_path.read_bytes()
    if sha(invdata)!=PRE645_CSV_SHA:raise ValueError("PRE645 signed V50 module inventory SHA mismatch")
    inventory=list(csv.DictReader(io.StringIO(invdata.decode("utf-8"))))
    pal={int(x["module"]):x for x in inventory if x["pack"]==PAL_PACK}
    if len(pal)!=152 or sum(1 for x in pal.values() if x["stage"]=="vertex")!=63:
        raise ValueError("PRE645 authentic PAL SPIR-V module count changed")
    raw=get_bytes(drive_client(),LOG_FILE_ID)
    if len(raw)!=LOG_SIZE or sha(raw)!=LOG_SHA:
        raise ValueError("Uploaded V51 original log readback does not match user-supplied SHA and size")
    text=raw.decode("utf-8",errors="strict")
    loglines=text.splitlines()
    if not (loglines and TIMESTAMP.match(loglines[0])
        and "2026-11-10 08:54:09.239" in loglines[0]
        and "2026-11-10 08:56:33.135" in loglines[-1]
        and "Samsung Xclipse 940" in text
        and "resolucion interna 1920x1080 y limite de FPS 60" in text
        and "biblioteca con 152 shaders (63 vertex, 89 pixel)" in text):
        raise ValueError("PRE656 unexpected runtime context, V51 session or PAL library")
    windows=[]
    aggregate=Counter()
    for line_no,line in enumerate(loglines,1):
        m=LOG_LINE.search(line)
        if not m:continue
        t=TIMESTAMP.match(line)
        if not t:raise ValueError("PRE656 shader report without timestamp")
        totals=list(map(int,m.group(1,2,3,4)))
        pairs=[tuple(map(int,v)) for v in TOP_ENTRY.findall(m.group(5))]
        if not 0<len(pairs)<=12 or len(set(x[:3] for x in pairs))!=len(pairs):
            raise ValueError("PRE656 invalid top12 category or duplicate key")
        if totals[0]!=totals[1]+totals[2] or totals[3]!=0:
            raise ValueError("PRE656 draw count conservation/invalid index failure")
        if sum(p[3] for p in pairs)>totals[0]:raise ValueError("PRE656 top draws > window")
        if pairs!=sorted(pairs,key=lambda p:-p[3]):
            raise ValueError("PRE656 top12 ordering inconsistent")
        for code,vs,ps,n in pairs:
            v=pal.get(vs-1)
            f=pal.get(ps-1) if ps else None
            if not v or v["stage"]!="vertex" or (ps and (not f or f["stage"]!="fragment")):
                raise ValueError("PRE656 logged PAL stage did not match PRE645 module index")
            if n<=0:raise ValueError("PRE656 top entry count invalid")
            aggregate[(code,vs,ps)]+=n
        windows.append({"line":line_no,"timestamp":t.group(1),"draws":totals[0],
          "normal":totals[1],"deferred_sky":totals[2],"invalid":totals[3],
          "reported_top12":len(pairs),"top12_draws":sum(x[3] for x in pairs)})
    grand=sum(w["draws"] for w in windows)
    if (len(windows)!=14 or grand!=14265243 or sum(w["deferred_sky"] for w in windows)!=7097
      or sum(w["invalid"] for w in windows)!=0 or
      aggregate[(2,62,58)]!=2186797 or aggregate[(1,43,37)]!=1934821):
        raise ValueError("PRE656 pinned original V51 runtime counts diverged")
    c3=[(n,line) for n,line in enumerate(loglines,1) if "[error]" in line and "NFSMW_PRE194_C3" in line]
    if len(c3)!=1 or not all(s in c3[0][1] for s in ("indice_fuera=false",
         "referencia_distinta=false","copia_duplicada=true")):
        raise ValueError("PRE656 observed C3 event unexpectedly changed")
    ordered=[]
    for (category,vs,ps),draws in sorted(aggregate.items(),key=lambda item:(-item[1],item[0])):
        v=pal[vs-1];f=pal.get(ps-1) if ps else None
        ordered.append({"pass_category":category,"vs_logged":vs,"ps_logged_or_zero":ps,
          "draws_in_reported_top12_lower_bound":draws,
          "minimum_percent_all_draws":round(100*draws/grand,5),
          "vs_pal_index_zero_based":vs-1,"vs_sha256":v["sha256"],
          "vs_static_spirv_instructions":int(v["instructions"]),
          "ps_pal_index_zero_based":ps-1 if ps else None,
          "ps_sha256":f["sha256"] if f else "",
          "ps_static_spirv_instructions":int(f["instructions"]) if f else None,
          "ps_static_image_sample_opcodes":int(f["image_sample"]) if f else 0})
    top_sum=sum(w["top12_draws"] for w in windows)
    result={"stage":"PRE656_V51_GPU_SHADER_PASS_REAL_LOG",
      "status":"AUDIT_OK_REAL_DEVICE_LOG_READONLY",
      "utc":datetime.now(timezone.utc).isoformat(),
      "source":{"file_id":LOG_FILE_ID,"bytes":len(raw),"sha256":sha(raw),
         "lines":len(loglines),"first":TIMESTAMP.match(loglines[0]).group(1),
         "last":TIMESTAMP.match(loglines[-1]).group(1),
         "read_back_remote_matches_user_attachment":True},
      "gpu_device":"Samsung Xclipse 940",
      "native_v51_diagnostic_marker_present":True,
      "v51_signed_apk_drive_id":APK_V51_DRIVE_ID,
      "package_manager_versioncode_read_on_device":False,
      "library":{"PAL_SPIRV_modules":152,"vertex":63,"fragment":89,
        "pre645_csv_sha256":PRE645_CSV_SHA,
        "all_reported_spirv_stages_matched":True},
      "counts":{"windows":len(windows),"total_draws":grand,
        "normal":sum(w["normal"] for w in windows),
        "deferred_sky":sum(w["deferred_sky"] for w in windows),
        "invalid":sum(w["invalid"] for w in windows),
        "top12_list_coverage_draws":top_sum,
        "top12_list_coverage_percent":round(100*top_sum/grand,5),
        "distinct_logged_pairs":len(ordered),"all_pair_counts_are_lower_bounds":True},
      "top_pairs":ordered,
      "windows_detail":windows,
      "c3":{"source_line":c3[0][0],"time":"08:54:48.918",
           "copia_duplicada":True,"guard_fallback_activated":True,
           "separate_investigation_paused":True},
      "configuration":{"internal_resolution":"1920x1080","fps_cap_in_log":60,
        "phone_s24fe_inferred_from_device_and_user":True},
      "limits":{"shader_gpu_time_individually_measured":False,
        "fps_gain_proven":False,"code_or_shaders_modified":False,
        "apk_built":False,"controller_tested":False,
        "graphics_quality_downgraded":False},
      "next_gate":"PRE657 readonly map pass category enums/render targets and verify GPU time hotspot of p2 VS62 PS58 before any SPIR-V edit"
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"PRE656_V51_REAL_GPU_SHADER_LOG_AUDIT.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (OUT/"PRE656_V51_TOP_SHADER_PAIRS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(ordered[0]));w.writeheader();w.writerows(ordered)
    with (OUT/"PRE656_V51_WINDOWS.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(windows[0]));w.writeheader();w.writerows(windows)
    print("PRE656_STATUS=AUDIT_OK_REAL_DEVICE_LOG_READONLY")
    print("PRE656_LOG_SHA256="+LOG_SHA)
    print("PRE656_V51_GPU_SHADER_WINDOWS="+str(len(windows)))
    print("PRE656_DRAW_COUNT="+str(grand))
    print("PRE656_INVALID_COUNT="+str(result["counts"]["invalid"]))
    print("PRE656_PAL_SPIRV_INDEX_CHECK=PASS")
    print("PRE656_P2_VS62_PS58_MIN_DRAWS="+str(aggregate[(2,62,58)]))
    print("PRE656_FPS_GAIN_PROVEN=false")
    print("PRE656_APK_BUILT=false")
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--pre645-csv",required=True,type=Path)
    args=p.parse_args()
    try:sys.exit(run(args.pre645_csv))
    except Exception as e:
        print("PRE656_STATUS=FAILED")
        print("PRE656_ERROR_TYPE="+type(e).__name__)
        print("PRE656_ERROR_SUMMARY="+str(e)[:200] if isinstance(e,ValueError) else "read-only audit failure")
        raise
