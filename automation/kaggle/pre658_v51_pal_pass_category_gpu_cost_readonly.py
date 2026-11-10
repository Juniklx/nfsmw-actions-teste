#!/usr/bin/env python3
"""PRE658: authenticate V50 production GPU source, map numeric PRE648 pass
categories to render-target heuristics, and compare with V51 C2 per-pass
GPU aggregate timestamps. No shader edits, no APK, no signing, no saves.
"""
from __future__ import annotations
import hashlib,json,re,sys,tempfile,statistics
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
from pre480_append_canonical_context_safe import get_bytes
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as p638

OUT=Path("/tmp/nfsmw-pre658")
LOG_ID="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
LOG_SHA="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
SOURCE_SHA="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
V51_SIGNED_APK_SHA="207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
COUNTER_SHA="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
NAMES=["kGpuSombras","kGpuEscena","kGpuReflejo","kGpu320","kGpuMenores","kGpuEscenaSinProfundidad"]
C2_PATTERN=re.compile(
    r"\[(?P<time>2026-11-10 \d\d:\d\d:\d\d\.\d{3})\].*?"
    r"C2: GPU por Swap: sombras (?P<sombras>[\d.]+) ms, "
    r"escena (?P<escena>[\d.]+), reflejo (?P<reflejo>[\d.]+), "
    r"320 \(cubo y desenfoque\) (?P<cubo320>[\d.]+), "
    r"menores (?P<menores>[\d.]+), copias (?P<copias>[\d.]+), "
    r"borrados (?P<borrados>[\d.]+), resto (?P<resto>[\d.]+), "
    r"escena sin profundidad (?P<escena_sin_profundidad>[\d.]+), "
    r"hueco entre trabajos (?P<hueco>[\d.]+)",re.M)
def sha(b):return hashlib.sha256(b).hexdigest()

def extract_function(source):
    m=re.search(r"\binline\s+uint32_t\s+CategoriaDeDestino\s*\(\s*uint32_t\s+pitch\s*,\s*const\s+uint64_t\*\s*claves\s*\)\s*\{",source)
    if not m:raise ValueError("PRE658 CategoriaDeDestino function missing from authenticated source")
    start=source.index("{",m.start());depth=0
    for pos in range(start,len(source)):
        if source[pos]=="{":depth+=1
        elif source[pos]=="}":
            depth-=1
            if depth==0:return source[m.start():pos+1],source.count("\n",0,m.start())+1
    raise ValueError("PRE658 unmatched source category function braces")

def numeric_categories(root):
    candidates=[]
    for file in sorted((root/"nativo/app").rglob("*")):
        if not file.is_file() or file.suffix not in (".h",".hpp",".cpp",".cc") or file.stat().st_size>1500000:
            continue
        s=file.read_text(encoding="utf-8",errors="replace")
        if "kGpuSombras" not in s:continue
        for m in re.finditer(r"\benum(?:\s+class)?(?:\s+\w+)?(?:\s*:\s*\w+)?\s*\{([^{}]*)\}",s,re.S):
            body=m.group(1)
            if not all(n in body for n in NAMES):continue
            current=-1;vals={}
            for raw in body.split(","):
                token=re.sub(r"//[^\n]*|/\*.*?\*/","",raw,flags=re.S).strip()
                line=re.match(r"^([A-Za-z_]\w*)\s*(?:=\s*(0x[0-9a-fA-F]+|\d+))?\s*$",token)
                if not line:continue
                if line.group(2):current=int(line.group(2),0)
                else:current+=1
                vals[line.group(1)]=current
            if all(n in vals for n in NAMES):
                candidates.append({"path":str(file.relative_to(root)), "line":s.count("\n",0,m.start())+1,
                    "values":{n:vals[n] for n in NAMES},"enum_source_sha256":sha(m.group(0).encode())})
        # Some versions use constants instead of enum. Match all kGpu constants declared explicitly.
        decls=dict((name,int(value,0)) for name,value in
            re.findall(r"\b(kGpu\w+)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*[,;]",s))
        if all(n in decls for n in NAMES):
            candidates.append({"path":str(file.relative_to(root)), "line":0,
                "values":{n:decls[n] for n in NAMES},
                "enum_source_sha256":sha(s.encode())})
    if not candidates:raise ValueError("PRE658 numeric GPU category enum not found; don't infer p1-p4 from names")
    values=candidates[0]["values"]
    if any(c["values"]!=values for c in candidates):
        raise ValueError("PRE658 multiple contradictory declarations of GPU category enum")
    if len(set(values.values()))!=len(NAMES) or min(values.values())<0 or max(values.values())>=16:
        raise ValueError("PRE658 GPU category values overlap or exceed PRE648 counter capacity")
    return values,candidates

def audit():
    doc={
      "stage":"PRE658_V51_PAL_RENDER_PASS_CATEGORY_AND_C2_GPU_TIME",
      "status":"FAILED_CLOSED",
      "timestamp_utc":datetime.now(timezone.utc).isoformat(),
      "read_only":True, "no_apk_built":True,"signing_accessed":False,
      "no_shader_spirv_edits":True,"no_device_changes":True,
      "fps_gain_proven":False,"per_shader_gpu_time_measured":False,
      "cannot_estimate_shader_cost_from_draws":True,
      "v51_signed_apk_sha256":V51_SIGNED_APK_SHA}
    try:
        pre656=json.loads(Path("docs/PRE656_V51_REAL_SHADER_LOG_VERIFIED.json").read_text())
        if (pre656.get("status")!="AUDIT_OK_REAL_DEVICE_LOG_READONLY" or
            pre656.get("github_run")!=42813194428 or
            pre656.get("original_uploaded_log",{}).get("sha256")!=LOG_SHA or
            pre656.get("counts",{}).get("total_draws")!=14265243 or
            pre656.get("counts",{}).get("invalid")!=0):
            raise ValueError("PRE658 prior PRE656 original log certification absent")
        remote=get_bytes(drive_client(),LOG_ID)
        if len(remote)!=576129 or sha(remote)!=LOG_SHA:
            raise ValueError("PRE658 Drive original on-device log SHA/size mismatch")
        doc["log_verified"]=True
        doc["log_drive_id"]=LOG_ID
        doc["log_sha256"]=LOG_SHA
        log=remote.decode("utf-8")
        reports=[]
        for m in C2_PATTERN.finditer(log):
            values={k:float(m.group(k)) for k in (
                "sombras","escena","reflejo","cubo320","menores","copias","borrados","resto",
                "escena_sin_profundidad","hueco")}
            reports.append({"timestamp":m.group("time"),**values})
        if len(reports)!=7:raise ValueError("PRE658 C2 per-pass GPU interval count differs")
        doc["c2_measurements"]=reports
        doc["c2_summary_unweighted_arithmetic_means_ms_per_swap"]={
            key:round(statistics.mean(report[key] for report in reports),5)
            for key in ("sombras","escena","reflejo","cubo320","menores","copias",
                        "borrados","resto","escena_sin_profundidad","hueco")}
        doc["c2_sampling_caveats"]=[
          "Seven C2 interval averages (about twenty seconds each), not sample-by-sample GPU traces.",
          "Arithmetic mean of reported per-Swap intervals is unweighted and mixes menu/cinematic/driving.",
          "GPU categories are render-target heuristics; may group multiple shaders and passes.",
          "C2 GPU per-pass times cannot be uniquely attributed to VS62/PS58.",
          "GPU time, frame pacing and asynchronous GPU gaps have different meanings; no FPS improvement claimed."
        ]
        p638.require_pre637()
        with tempfile.TemporaryDirectory(prefix="pre658_v50_category_") as td:
            folder=Path(td)
            archive=folder/"pre99.tar.gz"
            download(drive_client(),archive)
            digest,_,size=sha_file(archive)
            if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE658 PRE99 verified source backup mismatch")
            doc["pre99_sha256"]=digest
            doc["pre99_bytes"]=size
            dest=folder/"restore";dest.mkdir()
            restore(archive,dest)
            archive.unlink(missing_ok=True)
            root=dest/"workspace"
            stages=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if stages["PRE398"].get("cheat_enabled") is not True:
                raise ValueError("PRE658 Nitro source stage missing")
            previous=p434.ORIGINAL_STAGE
            def registered_menu(r):
                cmake=(r/"nativo/app/CMakeLists.txt").read_text()
                if cmake.count(v46.PRE292_REGISTER)!=1:
                    raise ValueError("PRE658 expected PRE292 menu registered once")
                return {"menu_registered_once":True}
            try:
                p434.ORIGINAL_STAGE=registered_menu
                gate=p638.stage_v50(root)
            finally:
                p434.ORIGINAL_STAGE=previous
            if not (gate.get("pre638_v49_source_recipe_verified") is True
                and gate.get("pre638_c3_fallback_bypass") is False
                and gate.get("pre638_v49_callbacks_nitro_preserved") is True
                and gate.get("pre638_save_modified") is False):
                raise ValueError("PRE658 V50 exact stage replay gate failed")
            source_bytes=(root/"nativo/app/src/nfsmw_nativo_dibujos.cpp").read_bytes()
            if sha(source_bytes)!=SOURCE_SHA or sha(source_bytes)!=p638.PIN_PRE635:
                raise ValueError("PRE658 V50 reconstructed source is not the pinned native source")
            source=source_bytes.decode("utf-8")
            function,line=extract_function(source)
            doc["source"]={"relative_path":"nativo/app/src/nfsmw_nativo_dibujos.cpp",
                "sha256":sha(source_bytes),"function_line":line,
                "function_sha256":sha(function.encode()),"function_exact":function,
                "includes_c3_guard":("NFSMW_PRE635_C3_TWOREQUEST_TRACE" in source),
                "mark_gpu_called":bool(re.search(r"contexto_->MarcarGpu\s*\(\s*categoria_pase_\s*\)",source)),
                "pre648_counter_same_function_called":("CategoriaDeDestino(pitch, claves)" in
                    Path("automation/kaggle/pre648_v50_shader_pass_counts_arm64_noapk.py").read_text())}
            for term in (
                "const bool color = claves[0] || claves[1] || claves[2] || claves[3];",
                "if (!color && claves[4] && pitch >= 1600)",
                "if (pitch >= 1280)",
                "return claves[4] ? kGpuEscena : kGpuEscenaSinProfundidad;",
                "if (pitch >= 640)",
                "if (pitch >= 320)",
                "return kGpuMenores;"
            ):
                if term not in function:
                    raise ValueError("PRE658 render-target category logic unexpectedly changed: "+term[:60])
            if not (doc["source"]["mark_gpu_called"] and
                    doc["source"]["pre648_counter_same_function_called"]):
                raise ValueError("PRE658 C2 markers and PRE648 counts not sourced by same category function")
            enums,provenance=numeric_categories(root)
            doc["enum_definitions"]=provenance
            doc["numeric_categories"]=enums
            reverse={str(v):k for k,v in enums.items()}
            doc["passes_by_category"]={
              "sombras":enums["kGpuSombras"],"escena":enums["kGpuEscena"],
              "reflejo":enums["kGpuReflejo"],"cubo320":enums["kGpu320"],
              "menores":enums["kGpuMenores"],
              "escena_sin_profundidad":enums["kGpuEscenaSinProfundidad"]}
            doc["target_classifier"]=[
              {"condition":"no color attachment, depth attachment present, pitch>=1600",
               "category":"kGpuSombras","category_id":enums["kGpuSombras"]},
              {"condition":"pitch>=1280 and depth attachment",
               "category":"kGpuEscena","category_id":enums["kGpuEscena"]},
              {"condition":"pitch>=1280 and no depth attachment",
               "category":"kGpuEscenaSinProfundidad","category_id":enums["kGpuEscenaSinProfundidad"]},
              {"condition":"640<=pitch<1280 (unless prior conditions match)",
               "category":"kGpuReflejo","category_id":enums["kGpuReflejo"]},
              {"condition":"320<=pitch<640",
               "category":"kGpu320","category_id":enums["kGpu320"]},
              {"condition":"pitch<320","category":"kGpuMenores","category_id":enums["kGpuMenores"]}
            ]
            doc["v50_source_recipe_replayed"]=True
        focus=[{"category_id":p["category"],"category_name":reverse.get(str(p["category"]),"unmapped"),
               "vs_id":p["vs"],"ps_id":p["ps"],
               "draws_lower_bound":p["draws"]}
            for p in pre656["top_observed_lower_bounds"]]
        if len(focus)<6 or focus[0]["category_id"] not in enums.values():
            raise ValueError("PRE658 runtime shader pairs not covered by authenticated render pass categories")
        doc["top_shader_pairs_by_render_target"]=focus
        doc["priority"]="Investigate VS62 PS58 in scene/render-target group, but do not assume GPU hotspot from draw frequency"
        doc["next_gate"]="PRE659 choose safe per-group GPU timestamp diagnostics, no patch/SDK until GPU timing scope proven"
        doc["status"]="AUDIT_OK_READONLY_SOURCE_AND_REAL_C2"
    except Exception as e:
        doc["error_type"]=type(e).__name__
        doc["error_summary"]=str(e)[:280] if isinstance(e,ValueError) else "audit failed without exposing sensitive data"
    finally:
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/"PRE658_V51_GPU_PASS_CATEGORY_C2_AUDIT.json").write_text(
            json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        lines=["# PRE658 — categorias e custo GPU por grupo (somente leitura)","",
         "**Estado:** "+doc["status"],"",
         "A regra de categoria é heurística por render target; não mede execução GPU de um shader específico.",
         "O C2 agrega duração de grupos e o PRE648 agrega número de draws; não correlacionar os dois como tempo de VS/PS.",
         ""]
        for c in doc.get("target_classifier",[]):
            lines.append(f"- p{c['category_id']} {c['category']}: {c['condition']}")
        lines+=["","## Tempos de GPU C2 (médias aritméticas não ponderadas de sete intervalos)"]
        for k,v in doc.get("c2_summary_unweighted_arithmetic_means_ms_per_swap",{}).items():
            lines.append(f"- {k}: {v:.3f} ms/Swap")
        lines+=["","## Próximo passo","Mapear o escopo das timestamps Vulkan por grupo e medir custo direcionado antes de modificar SPIR-V.",
          "Não alterar qualidade, gráficos, sombras, física, assinatura, FPS ou térmica.", "",
          "**Limites:** sem APK nova, sem timing individual, sem ganho FPS comprovado."]
        (OUT/"RELATORIO_PRE658_V51_PASS_GPU_TIME_READONLY.md").write_text(
            "\n".join(lines)+"\n",encoding="utf-8")
        for name,val in (
           ("STATUS",doc["status"]),
           ("SOURCE_REPLAY",doc.get("v50_source_recipe_replayed",False)),
           ("ENUM_RESOLVED",bool(doc.get("numeric_categories"))),
           ("C2_SAMPLES",len(doc.get("c2_measurements",[]))),
           ("APK_CREATED",False),("FPS_GAIN_PROVEN",False),
           ("ERROR_TYPE",doc.get("error_type","none"))):
            print("PRE658_"+name+"="+str(val))
    return 0 if doc["status"]=="AUDIT_OK_READONLY_SOURCE_AND_REAL_C2" else 1
if __name__=="__main__":sys.exit(audit())
