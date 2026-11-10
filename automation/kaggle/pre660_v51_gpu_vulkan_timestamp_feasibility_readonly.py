#!/usr/bin/env python3
"""PRE660: read-only source audit of GPU timestamp/query instrumentation.
Reconstructs authenticated PRE638 V50 source (common Vulkan backend used by V51)
and locates timing calls, their scope, and potential selective shader timing hooks.
No APK, no changes to rendering, no key access or phone runtime changes.
"""
from __future__ import annotations
import hashlib,json,re,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as p638

OUT=Path("/tmp/nfsmw-pre660")
PIN_V50_SOURCE="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
PRE658_REPORT=Path("docs/PRE658_V51_PASS_CATEGORY_GPU_COST_VERIFIED.json")
BACKEND_TERMS={
 "gpu_marker":r"\bMarcarGpu\s*\(",
 "timestamp_command":r"\bvkCmdWriteTimestamp(?:2(?:KHR)?)?\s*\(",
 "query_pool_create":r"\bvkCreateQueryPool\s*\(",
 "query_pool_results":r"\bvkGetQueryPoolResults\s*\(",
 "query_pool_reset":r"\bvk(?:Cmd)?ResetQueryPool(?:EXT)?\s*\(",
 "timestamp_query_type":r"\bVK_QUERY_TYPE_TIMESTAMP\b",
 "timestamp_valid_bits":r"\btimestampValidBits\b",
 "timestamp_period":r"\btimestampPeriod\b",
 "pipeline_stats_query_type":r"\bVK_QUERY_TYPE_PIPELINE_STATISTICS\b",
 "render_pass_start":r"\bvkCmdBeginRenderPass\s*\(",
 "render_pass_end":r"\bvkCmdEndRenderPass\s*\(",
 "vulkan_draw_indexed":r"\bvkCmdDrawIndexed\s*\(",
 "vulkan_draw_simple":r"\bvkCmdDraw\s*\(",
 "precise_marks":r"\bmarcas_precisas\b",
 "gpu_category_report":r"C2: GPU por Swap:",
}
def sha(data):return hashlib.sha256(data).hexdigest()
def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    report={
      "stage":"PRE660_V51_GPU_SHADER_TIMESTAMP_QUERY_FEASIBILITY",
      "status":"FAILED_CLOSED",
      "timestamp_utc":datetime.now(timezone.utc).isoformat(),
      "apk_created":False,"signing_material_accessed":False,
      "shader_spirv_modified":False,"vulkan_commands_changed":False,
      "game_saves_accessed":False,"phone_runtime_tested":False,
      "timing_per_shader_obtained":False,"fps_gain_verified":False
    }
    try:
      previous=json.loads(PRE658_REPORT.read_text())
      if not (previous.get("status")=="AUDIT_OK_READONLY_SOURCE_AND_REAL_C2"
         and previous.get("github_run_id")==42815591562
         and previous.get("base_source",{}).get("stage_source_sha256")==PIN_V50_SOURCE
         and previous.get("runtime_device_log",{}).get("c2_intervals")==7
         and previous.get("boundary",{}).get("subshader_gpu_duration_unknown") is True):
        raise ValueError("PRE660 pinned PRE658 run and source provenance missing")
      p638.require_pre637()
      with tempfile.TemporaryDirectory(prefix="pre660_gpu_timestamp_") as td:
        folder=Path(td);archive=folder/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,nbytes=sha_file(archive)
        if (digest,nbytes)!=(EXPECTED_SHA256,EXPECTED_BYTES):
          raise ValueError("PRE660 authenticated PRE99 tar size/SHA changed")
        report["pre99_sha256"]=digest
        restore_dest=folder/"restored";restore_dest.mkdir()
        restore(archive,restore_dest)
        archive.unlink(missing_ok=True)
        root=restore_dest/"workspace"
        replay=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
        if replay["PRE398"].get("cheat_enabled") is not True:
          raise ValueError("PRE660 signed source replay lost PRE398 Nitro")
        prev=p434.ORIGINAL_STAGE
        def menu_already_patched(r):
          c=(r/"nativo/app/CMakeLists.txt").read_text()
          if c.count(v46.PRE292_REGISTER)!=1:
            raise ValueError("PRE660 PRE292 duplicated menu staging")
          return {"menu_registered_once":True}
        try:
          p434.ORIGINAL_STAGE=menu_already_patched
          staged=p638.stage_v50(root)
        finally:
          p434.ORIGINAL_STAGE=prev
        if not (staged.get("pre638_v49_source_recipe_verified") is True
          and staged.get("pre638_c3_fallback_bypass") is False
          and staged.get("pre638_v49_callbacks_nitro_preserved") is True
          and staged.get("pre638_save_modified") is False):
          raise ValueError("PRE660 replayed V50 stage invalid")
        native=root/"nativo/app"
        dib=native/"src/nfsmw_nativo_dibujos.cpp"
        if sha(dib.read_bytes())!=PIN_V50_SOURCE:
          raise ValueError("PRE660 reconstructed V50 renderer differs from pinned source")
        hits={k:[] for k in BACKEND_TERMS}
        files_scanned=0
        filenames=set()
        for path in sorted(native.rglob("*")):
          if not path.is_file() or path.suffix not in (".cpp",".c",".cc",".hpp",".h") or path.stat().st_size>3000000:
            continue
          # Scan only authenticated source path; no raw source embedded in the result
          s=path.read_text(encoding="utf-8",errors="replace")
          files_scanned+=1
          short=str(path.relative_to(root))
          for label,pattern in BACKEND_TERMS.items():
            indexes=[(s.count("\n",0,m.start())+1,m.start()) for m in re.finditer(pattern,s)]
            if not indexes:continue
            filenames.add(short)
            for line,pos in indexes[:12]:
              hits[label].append({
                "file":short,"line":line,
                "source_line":s.splitlines()[line-1][:230].strip()
              })
        if not hits["gpu_marker"] or not hits["gpu_category_report"]:
          raise ValueError("PRE660 original C2 marker path not in authenticated GPU source")
        if not hits["timestamp_command"] and not hits["timestamp_query_type"]:
          raise ValueError("PRE660 no GPU timestamp Vulkan implementation in source; cannot assert support")
        report["source_audit"]={
          "v50_renderer_sha256":PIN_V50_SOURCE,
          "source_replay_status":"PRE638_PRODUCTION_REPLAY_VERIFIED",
          "files_scanned":files_scanned,
          "matching_files":sorted(filenames),
          "hit_counts_by_term":{k:len(v) for k,v in hits.items()},
          "sampled_source_lines":hits,
          "timing_identification":{
             "vulkan_timestamp_commands_present":bool(hits["timestamp_command"]),
             "timestamp_query_type_present":bool(hits["timestamp_query_type"]),
             "query_pool_created":bool(hits["query_pool_create"]),
             "query_results_read":bool(hits["query_pool_results"]),
             "query_pool_reset_found":bool(hits["query_pool_reset"]),
             "gpu_category_marker_found":bool(hits["gpu_marker"]),
             "device_timestamp_limits_extracted":bool(hits["timestamp_valid_bits"] or hits["timestamp_period"]),
          }
        }
        report["read_only_authenticated_source_verified"]=True
      report["risks_and_limits"]=[
        "Only source paths / selected line excerpts were scanned; no Vulkan timestamps were issued in this PRE660 gate.",
        "C2 already aggregates measured GPU time by category; no isolated VS/PS GPU execution timing is present in the V51 log.",
        "Do not add timestamp query before/after every draw: millions of draws per session and extra command/query overhead.",
        "A targeted timing method must account for asynchronous GPU work, command buffer boundaries and pass grouping.",
        "Any future query measurement needs query-capacity, synchronization and overhead gates before a signed diagnostic APK.",
        "No shader SPIR-V edit until a specific performance bottleneck is demonstrated."
      ]
      report["next"]="PRE661 inspect selected Vulkan query/timestamp source portions and design bounded opt-in group sampling, no signed V52 without separate gates"
      report["status"]="AUDIT_OK_STATIC_VULKAN_TIMESTAMP_SUPPORT"
    except Exception as e:
      report["error_type"]=type(e).__name__
      report["error_summary"]=str(e)[:240] if isinstance(e,ValueError) else "auditor could not complete"
    finally:
      (OUT/"PRE660_GPU_VULKAN_TIMESTAMP_SOURCE_AUDIT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n")
      lines=["# PRE660 — Vulkan GPU timestamp source feasibility, read-only","",
        "Estado: "+report["status"],"",
        "A PRE658 atestou categorias GPU na fonte PAL; esta PRE660 localiza APIs de timestamp, query pool, reset e leitura de resultados.",
        "Nenhuma medição de tempo por shader foi executada ou alegada.", "",
        "## Sinais encontrados na árvore autenticada"]
      for k,n in report.get("source_audit",{}).get("hit_counts_by_term",{}).items():
        lines.append(f"- {k}: {n} ocorrências nos arquivos auditados (amostra limitada a 12 por arquivo)")
      lines.extend(["","## Limites","Sem APK, sem leitura de senha/chave, sem SPIR-V modificado, sem alteração Vulkan ou FPS ganho."])
      (OUT/"RELATORIO_PRE660_V51_GPU_TIMESTAMP_READONLY.md").write_text("\n".join(lines)+"\n")
      for k,v in (
        ("STATUS",report["status"]),
        ("SOURCE_REPLAY",report.get("read_only_authenticated_source_verified",False)),
        ("TIMESTAMP_COMMAND_FOUND",bool(report.get("source_audit",{}).get("timing_identification",{}).get("vulkan_timestamp_commands_present"))),
        ("QUERY_POOL_FOUND",bool(report.get("source_audit",{}).get("timing_identification",{}).get("query_pool_created"))),
        ("APK_BUILT",False),("PER_SHADER_GPU_TIME_MEASURED",False),
        ("ERROR_TYPE",report.get("error_type","none"))):
        print("PRE660_"+k+"="+str(v))
    return 0 if report["status"]=="AUDIT_OK_STATIC_VULKAN_TIMESTAMP_SUPPORT" else 1
if __name__=="__main__":sys.exit(audit())
