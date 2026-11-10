#!/usr/bin/env python3
"""PRE665: readonly, authenticated GPU draw-emission/timestamp insertion audit.
Replays actual PRE638 source plus exact PRE648 frequency instrumentation to
locate safe candidate boundaries. Never inserts Vulkan commands or builds APK.
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
import pre638_build_signed_v50_c3_two_request_diag as v50
import pre648_v50_shader_pass_counts_arm64_noapk as pre648
import pre652_build_signed_v51_gpu_shader_counts_diag as v51

OUT=Path("/tmp/nfsmw-pre665")
PIN_RENDER="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
PIN_BASE="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
PIN_DESTINOS="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
PIN_HEADER="9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe"
PRE662=Path("docs/PRE662_V51_VULKAN_TIMESTAMP_ALIAS_LIFECYCLE_VERIFIED.json")
PRE658=Path("docs/PRE658_V51_PASS_CATEGORY_GPU_COST_VERIFIED.json")
PRE652=Path("docs/PRE652_V51_SIGNED_GPU_SHADER_DIAGNOSTIC_VERIFIED.json")
PATTERNS={
 "renderer_vulkan_draw":r"\bvkCmdDraw(?:Indexed|Indirect|IndexedIndirect)?\b",
 "renderer_pre648_count":r"shader_por_pase_pre648_\.Anotar\s*\(",
 "renderer_target_classifier":r"\bCategoriaDeDestino\s*\(",
 "renderer_marker":r"\bMarcarGpu\s*\(",
 "renderer_deferred_sky":r"\bc\.vs_mas_uno\b|\bc\.ps_mas_uno\b",
 "renderer_pass":r"\bcategoria_pase_\b",
 "backend_mark":r"\b(?:void\s+)?MarcarGpu\s*\(",
 "backend_submit":r"\bvkQueueSubmit\s*\(",
 "backend_fence_poll":r"\bvkGetFenceStatus\s*\(",
 "backend_fence_wait":r"\bvkWaitForFences\s*\(",
 "backend_query_reset":r"\bvkCmdResetQueryPool\s*\(",
 "backend_writer_pointer":r"\bescribir_marca_\s*\(",
 "backend_reader_pointer":r"\bleer_consultas_\s*\(",
 "backend_renderpass_begin":r"\bvkCmdBeginRenderPass\s*\(",
 "backend_renderpass_end":r"\bvkCmdEndRenderPass\s*\(",
 "backend_commandbuffer_begin":r"\bvkBeginCommandBuffer\s*\(",
 "backend_commandbuffer_end":r"\bvkEndCommandBuffer\s*\(",
}
RENDER_KEYS=set(k for k in PATTERNS if k.startswith("renderer_"))
def sha(b):return hashlib.sha256(b).hexdigest()
def scan(source,pat,max_hits=36,context=9):
    lines=source.splitlines()
    hits=[]
    for n,line in enumerate(lines,1):
        if re.search(pat,line):
            lo=max(1,n-context);hi=min(len(lines),n+context)
            hits.append({"line":n,"source_line":line.strip()[:260],
                         "context":[f"{j:>5}: {lines[j-1][:250]}" for j in range(lo,hi+1)]})
    return {"total":len(hits),"lines":[x["line"] for x in hits],
            "examples":hits[:max_hits],"truncated":len(hits)>max_hits}
def audit():
    OUT.mkdir(exist_ok=True,parents=True)
    r={"stage":"PRE665_V51_GPU_DRAW_EMISSION_BOUNDARY_READONLY",
       "status":"FAILED_CLOSED","utc":datetime.now(timezone.utc).isoformat(),
       "read_only":True,"apk_built":False,"arm64_compiled":False,
       "vulkan_commands_injected":False,"shader_spirv_modified":False,
       "signed_apk_modified":False,"signing_material_accessed":False,
       "user_saves_accessed":False,"per_shader_gpu_time_measured":False,
       "fps_gain_proven":False}
    try:
        old=json.loads(PRE662.read_text())
        cat=json.loads(PRE658.read_text())
        release=json.loads(PRE652.read_text())
        if not (old.get("github_run_id")==42826615797
          and old.get("status")=="AUDIT_OK_SOURCE_ALIAS_LIFECYCLE_EXTRACTED"
          and old.get("source",{}).get("timestamp_cpp_sha256")==PIN_DESTINOS
          and cat.get("github_run_id")==42815591562
          and cat.get("status")=="AUDIT_OK_READONLY_SOURCE_AND_REAL_C2"
          and release.get("status")=="SIGNED_AND_DRIVE_VERIFIED"
          and release.get("apk",{}).get("version_code")==51
          and release.get("apk",{}).get("sha256")=="207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"):
            raise ValueError("PRE665 prior verified source/release evidence unexpectedly changed")
        v50.require_pre637()
        with tempfile.TemporaryDirectory(prefix="pre665_gpu_boundaries_") as td:
            temp=Path(td)
            tar=temp/"pre99.tar.gz"
            download(drive_client(),tar)
            d,_,size=sha_file(tar)
            if (d,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE665 PRE99 authentic archive size/hash mismatch")
            dest=temp/"restore";dest.mkdir()
            restore(tar,dest)
            tar.unlink(missing_ok=True)
            root=dest/"workspace"
            replay=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if replay["PRE398"].get("cheat_enabled") is not True:
                raise ValueError("PRE665 PRE398 global Nitro absent from replay")
            prev=p434.ORIGINAL_STAGE
            def menu_already_registered(path):
                cmake=(path/"nativo/app/CMakeLists.txt").read_text()
                if cmake.count(v46.PRE292_REGISTER)!=1:
                    raise ValueError("PRE665 menu stage must be registered once")
                return {"menu_registered_once":True}
            try:
                p434.ORIGINAL_STAGE=menu_already_registered
                staged=v50.stage_v50(root)
            finally:
                p434.ORIGINAL_STAGE=prev
            if not (staged.get("pre638_v49_source_recipe_verified") is True
              and staged.get("pre638_c3_fallback_bypass") is False
              and staged.get("pre638_v49_callbacks_nitro_preserved") is True
              and staged.get("pre638_save_modified") is False):
                raise ValueError("PRE665 production source stage failed")
            renderer=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
            backend=root/"nativo/app/src/nfsmw_nativo_destinos.cpp"
            source=renderer.read_bytes()
            if sha(source)!=PIN_BASE or sha(backend.read_bytes())!=PIN_DESTINOS:
                raise ValueError("PRE665 authenticated native source differs")
            instrumented=pre648.patch_bytes(source)
            if sha(instrumented)!=PIN_RENDER or sha(pre648.HEADER.read_bytes())!=PIN_HEADER:
                raise ValueError("PRE665 actual V51 instrumented source hash differs")
            render_text=instrumented.decode("utf-8")
            backend_text=backend.read_text(encoding="utf-8")
            scans={key:scan(render_text if key in RENDER_KEYS else backend_text,pat)
                   for key,pat in PATTERNS.items()}
            must_have=("renderer_vulkan_draw","renderer_pre648_count",
                       "renderer_target_classifier","renderer_marker",
                       "renderer_deferred_sky","backend_mark","backend_submit",
                       "backend_fence_wait","backend_query_reset",
                       "backend_writer_pointer","backend_reader_pointer")
            if any(scans[k]["total"]<1 for k in must_have):
                raise ValueError("PRE665 required callsite not located: "+",".join(k for k in must_have if scans[k]["total"]<1))
            if scans["renderer_pre648_count"]["total"]!=2:
                raise ValueError("PRE665 PRE648 normal/deferred counter calls not exactly two")
            # Pure lexical check only, no assumption of execution order beyond source.
            r["source"]={
              "pre99_sha256":d,"source_replay":"PRE99 -> PRE431 -> PRE638 -> PRE648 in memory",
              "base_renderer_sha256":sha(source),"v51_instrumented_renderer_sha256":sha(instrumented),
              "renderer_header_sha256":sha(pre648.HEADER.read_bytes()),
              "vulkan_backend_sha256":sha(backend.read_bytes()),
              "signed_elf_bitwise_source_equivalence_proven":False,
              "temp_tree_only":True}
            r["anchors"]=scans
            r["findings"]={
              "normal_and_deferred_frequency_accounting_present":True,
              "separate_timestamp_pool_exists":False,
              "pre664_sampler_native_integrated":False,
              "vulkan_draw_methods_identified":True,
              "source_writer_and_reader_call_paths_identified":True,
              "fence_lifecycle_requires_review_before_injection":True,
              "gpu_shader_duration_inferred_from_frequency":False,
              "timestamp_pair_isolation_when_draws_interleave_not_proven":True,
              "scope":"C++ lexical source sites; renderpass validity and actual command execution not yet proven"}
        r["status"]="AUDIT_OK_AUTHENTIC_V51_DRAW_AND_C2_SOURCE_ANCHORS"
        r["next"]="PRE666: inspect context/order of draw emission, deferred sky, in-pass Vulkan timestamp restrictions and per-slot fence states; no native injection until safety review"
    except Exception as e:
        r["error_type"]=type(e).__name__
        r["error_summary"]=str(e)[:240] if isinstance(e,ValueError) else "Source read-only gate failed"
    finally:
        (OUT/"PRE665_V51_DRAW_AND_C2_BOUNDARY_AUDIT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
        lines=["# PRE665 — limites Vulkan e pontos candidatos para timestamp", "",
          "**Status:** "+r["status"], "",
          "Somente leitura da fonte autenticada e patch PRE648 em memoria temporaria.",
          "Nenhum timestamp Vulkan extra emitido, APK gerada ou FPS medido.", "",
          "## Numero de sitios encontrados"]
        for name,data in r.get("anchors",{}).items():
            lines.append(f"- {name}: {data['total']} ocorrencias nas linhas {data['lines'][:30]}")
        lines += ["","## Proximo gate",
          "Revisao manual do fluxo command buffer, mudanca de shader/targets, deferred sky e fence antes de qualquer integracao.",
          "Nao inferir custo individual de shader pela contagem de draws."]
        (OUT/"RELATORIO_PRE665_GPU_DRAW_ANCHORS_READONLY.md").write_text("\n".join(lines)+"\n")
        print("PRE665_STATUS="+r["status"])
        print("PRE665_AUTHENTIC_SOURCE="+str(r.get("source",{}).get("v51_instrumented_renderer_sha256")==PIN_RENDER))
        for key in ("renderer_vulkan_draw","renderer_pre648_count","backend_writer_pointer","backend_reader_pointer"):
            print("PRE665_"+key.upper()+"_SITES="+str(r.get("anchors",{}).get(key,{}).get("total",0)))
        print("PRE665_APK_BUILT=false")
        print("PRE665_PER_SHADER_GPU_TIME_MEASURED=false")
        print("PRE665_FPS_GAIN_PROVEN=false")
        print("PRE665_ERROR_TYPE="+r.get("error_type","none"))
    return 0 if r["status"]=="AUDIT_OK_AUTHENTIC_V51_DRAW_AND_C2_SOURCE_ANCHORS" else 1
if __name__=="__main__":sys.exit(audit())
