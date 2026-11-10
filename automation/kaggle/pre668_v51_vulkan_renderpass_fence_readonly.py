#!/usr/bin/env python3
"""PRE668: authenticated V51 Vulkan pass/slot/fence integration review, READONLY.
Replays the exact PRE665 V51 sources in a disposable directory. NO native
source patch, APK, new Vulkan query, real GPU timing or signing access.
"""
from __future__ import annotations
import hashlib,json,re,tempfile,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
import pre665_v51_gpu_draw_emission_boundaries_readonly as p665
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore

OUT=Path("/tmp/nfsmw-pre668")
PRE665_EVIDENCE=Path("docs/PRE665_V51_GPU_DRAW_BOUNDARIES_VERIFIED.json")
FILENAME="PRE668_V51_RENDERPASS_AND_QUERYPOOL_REVIEW.json"
NEEDLES={
 "renderer_open_pass":r"\bdfn_\.vkCmdBeginRenderPass\s*\(\s*cmd\s*,\s*&inicio",
 "renderer_close_pass":r"\bdfn_\.vkCmdEndRenderPass\s*\(\s*pase_comandos_\s*\)",
 "renderer_category_mark":r"contexto_->MarcarGpu\s*\(\s*categoria_pase_\s*\)",
 "renderer_normal_draw":r"\bdfn_\.vkCmdDraw(?:Indexed)?\s*\(\s*cmd\s*,",
 "renderer_deferred_draw":r"\bdfn_\.vkCmdDraw(?:Indexed)?\s*\(\s*cmd\s*,\s*c\.",
 "renderer_deferred_sky_emit":r"\bEmitirCielo\b|\bDibujarCielo\b|\bcielo_pendiente_\b",
 "renderer_live_cmd_buffer":r"\bcontexto_->ComandosTrabajo\s*\(|\bcontexto_->Comandos\b|\bpase_comandos_\b",
 "backend_vk_timestamp_pool_create":r"\bvkCreateQueryPool\s*\(",
 "backend_vk_timestamp_pool_destroy":r"\bvkDestroyQueryPool\s*\(",
 "backend_vk_timestamp_pool_reset":r"\bvkCmdResetQueryPool\s*\(",
 "backend_vk_timestamp_write":r"\bescribir_marca_\s*\(",
 "backend_vk_timestamp_read":r"\bleer_consultas_\s*\(",
 "backend_timestamp_valid_bits":r"\btimestampValidBits\b",
 "backend_timestamp_period":r"\btimestampPeriod\b",
 "backend_query_type_timestamp":r"\bVK_QUERY_TYPE_TIMESTAMP\b",
 "backend_vk_fence_poll":r"\bvkGetFenceStatus\s*\(",
 "backend_vk_fence_wait":r"\bvkWaitForFences\s*\(",
 "backend_vk_fence_reset":r"\bvkResetFences\s*\(",
 "backend_work_slot_completion":r"\bCompletarUna\s*\(|\bCompletar\s*\(",
 "backend_work_slot_submit":r"\bvkQueueSubmit\s*\(",
 "backend_new_work_cmd":r"\bvkBeginCommandBuffer\s*\(\s*comandos_trabajo_\s*,",
 "backend_end_work_cmd":r"\bvkEndCommandBuffer\s*\(\s*comandos_trabajo_\s*\)",
 "backend_query_result_wait":r"\bVK_QUERY_RESULT_WAIT_BIT\b",
 "backend_query_result_64":r"\bVK_QUERY_RESULT_64_BIT\b",
 "backend_slot_struct":r"\bstruct\s+RanuraTrabajo\b",
 "backend_slots_constant":r"\bkRanurasTrabajo\b|\bkMarcasPorRanura\b",
 "backend_getdeviceproc":r"\bvkGetDeviceProcAddr\b",
}
R_KEYS={k for k in NEEDLES if k.startswith("renderer_")}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def audit_scan(lines,regex,ctx=22,max_cases=12):
    matches=[i for i,line in enumerate(lines) if re.search(regex,line)]
    examples=[]
    for i in matches[:max_cases]:
        a=max(i-ctx,0);z=min(i+ctx+1,len(lines))
        examples.append({"line":i+1,"excerpt":[f"{k+1:5d}: {lines[k][:250]}" for k in range(a,z)]})
    return {"count":len(matches),"lines":[i+1 for i in matches],
            "examples":examples,"truncated":len(matches)>max_cases}
def main():
    OUT.mkdir(exist_ok=True,parents=True)
    result={
      "stage":"PRE668_V51_VULKAN_REAL_RENDERPASS_SLOT_AND_QUERY_POOL_REVIEW",
      "status":"FAILED_CLOSED",
      "utc":datetime.now(timezone.utc).isoformat(),
      "source_only":True,"actual_shader_duration_measured":False,
      "driver_timestamp_valid_bits_probed":False,
      "vulkan_query_pool_created":False,
      "vulkan_commands_injected":False,
      "actual_fence_guarantees_tested":False,
      "arm64_compiled":False,"apk_built":False,
      "certificates_or_secrets_accessed":False,"user_save_accessed":False,
      "fps_gain_proven":False}
    try:
      old=json.loads(PRE665_EVIDENCE.read_text(encoding="utf-8"))
      if not (
        old.get("github_run_id")==42837121790
        and old.get("status")=="AUDIT_OK_AUTHENTIC_V51_DRAW_AND_C2_SOURCE_ANCHORS"
        and old.get("authenticated_source",{}).get("v51_instrumented_renderer_sha256")==p665.PIN_RENDER
        and old.get("authenticated_source",{}).get("backend_sha256")==p665.PIN_DESTINOS
        and old.get("no_apk_built") is True
        and old.get("no_vk_commands_injected") is True
      ):raise ValueError("PRE668 refuses unverified PRE665 provenance")
      p665.v50.require_pre637()
      with tempfile.TemporaryDirectory(prefix="nfsmw_pre668_v51_") as td:
        td=Path(td);archive=td/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,length=sha_file(archive)
        if (digest,length)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE668 authentic PRE99 archive hash/length mismatch")
        dest=td/"unpack";dest.mkdir()
        restore(archive,dest)
        archive.unlink(missing_ok=True)
        root=dest/"workspace"
        replay=p665.v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
        if replay["PRE398"].get("cheat_enabled") is not True:
            raise ValueError("PRE668 PRE398 source replay unexpectedly absent")
        original_menu=p665.p434.ORIGINAL_STAGE
        def skip_replayed_menu(path):
            cmake=(path/"nativo/app/CMakeLists.txt").read_text()
            if cmake.count(p665.v46.PRE292_REGISTER)!=1:
                raise ValueError("PRE668 PRE292 already-staged menu source count !=1")
            return {"menu_registered_once":True}
        try:
            p665.p434.ORIGINAL_STAGE=skip_replayed_menu
            staged=p665.v50.stage_v50(root)
        finally:
            p665.p434.ORIGINAL_STAGE=original_menu
        if not (
          staged.get("pre638_v49_source_recipe_verified") is True
          and staged.get("pre638_c3_fallback_bypass") is False
          and staged.get("pre638_v49_callbacks_nitro_preserved") is True
          and staged.get("pre638_save_modified") is False
        ):raise ValueError("PRE668 signed V50 recipe not safely reproduced")
        render_file=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
        backend_file=root/"nativo/app/src/nfsmw_nativo_destinos.cpp"
        base=render_file.read_bytes();back=backend_file.read_bytes()
        if sha(base)!=p665.PIN_BASE or sha(back)!=p665.PIN_DESTINOS:
            raise ValueError("PRE668 V50 renderer/backend source fingerprint changed")
        render=p665.pre648.patch_bytes(base)
        if sha(render)!=p665.PIN_RENDER:
            raise ValueError("PRE668 PRE648 V51 exact renderer patch fingerprint changed")
        if sha(p665.pre648.HEADER.read_bytes())!=p665.PIN_HEADER:
            raise ValueError("PRE668 PRE648 source counter header drift")
        lines_r=render.decode("utf-8").splitlines()
        lines_b=back.decode("utf-8").splitlines()
        out={k:audit_scan(lines_r if k in R_KEYS else lines_b,rx)
             for k,rx in NEEDLES.items()}
        important={
          "renderer_open_pass":1,
          "renderer_close_pass":1,
          "renderer_category_mark":1,
          "backend_vk_timestamp_pool_create":1,
          "backend_vk_timestamp_pool_destroy":1,
          "backend_vk_timestamp_pool_reset":1,
          "backend_vk_timestamp_write":2,
          "backend_vk_timestamp_read":1,
          "backend_vk_fence_poll":1,
          "backend_vk_fence_wait":1,
          "backend_work_slot_submit":1,
          "backend_work_slot_completion":2,
          "backend_new_work_cmd":1,
          "backend_end_work_cmd":1,
        }
        missing={k:{"expected_at_least":n,"actual":out[k]["count"]}
                 for k,n in important.items() if out[k]["count"]<n}
        if missing:raise ValueError("PRE668 missing critical trusted callsite(s): "+str(missing)[:600])
        if out["renderer_normal_draw"]["count"]!=4:
            raise ValueError("PRE668 exact renderer normal+sky Vulkan draw sites differ")
        if out["renderer_category_mark"]["lines"]!=[10108]:
            raise ValueError("PRE668 category marker moved")
        if out["renderer_open_pass"]["lines"]!=[10153] or out["renderer_close_pass"]["lines"]!=[4680]:
            raise ValueError("PRE668 renderpass scope changed since PRE665 review")
        if out["backend_vk_fence_poll"]["lines"]!=[4927]:
            raise ValueError("PRE668 fence status source drift")
        if out["backend_vk_timestamp_write"]["lines"]!=[3690,5165]:
            raise ValueError("PRE668 recorded C2 timestamp writer source drift")
        report_source={
          "pre99_backup_sha256":digest,
          "renderer_v50_before_pre648_sha256":sha(base),
          "renderer_v51_with_pre648_sha256":sha(render),
          "backend_v51_sha256":sha(back),
          "pre648_header_sha256":sha(p665.pre648.HEADER.read_bytes()),
          "temporary_tree_only":True,
          "signed_v51_elf_byte_equivalence_proven":False
        }
        result["authenticated_source"]=report_source
        result["callsite_evidence"]=out
        result["technical_decisions"]={
          "renderpass_open_and_close_are_in_renderer":True,
          "backend_output_renderpass_is_separate_from_scene":True,
          "C2_slot_recycling_and_query_read_have_prior_fence_operations_in_source":True,
          "fence_status_return_error_handling_proven":False,
          "extra_pool_creation_has_not_been_prototyped":True,
          "extra_query_reset_before_begin_renderpass_required":True,
          "timestamp_valid_bits_on_s24_fe_verified":False,
          "timestampPeriod_fetched_from_real_device_for_new_pool":False,
          "pre_draw_emit_must_record_begin_before_draw":True,
          "pre_renderpass_end_must_flush_pair":True,
          "all_disabled_paths_exact_gpu_command_equivalence_verified":False,
          "multiview_timestamp_query_consumption_checked":False,
          "pipeline_stage_top_vs_bottom_selection_validated":False,
          "source_only_anchor_review_not_runtime_test":True,
          "next_gate":"PRE669 implement strictly default-OFF reversible temporary-tree bridge and compile ARM64 NO APK, then evaluate supported Vulkan pool/timestamps/fences separately"
        }
        result["status"]="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY"
    except Exception as exc:
      result["error_type"]=type(exc).__name__
      result["error_summary"]=str(exc)[:800] if isinstance(exc,ValueError) else "Unexpected run/replay or Drive error"
    finally:
      evidence=OUT/FILENAME
      evidence.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
      md=["# PRE668 — auditoria de pontos Vulkan V51", "",
          "**Status:** "+result["status"], "",
          "Escopo: fonte autenticada reconstruida TEMPORARIAMENTE, nenhuma alteracao da APK.",
          "A auditoria nao mede timestamp no S24 FE nem overhead de Vulkan.", "",
          "## Pontos textuais encontrados"]
      for k,v in result.get("callsite_evidence",{}).items():
        md.append(f"- {k}: {v['count']} ocorrencias (linhas {v['lines'][:22]})")
      md += ["","## Limites a resolver antes de rodar timestamp GPU real",
             "- Novo pool VK_QUERY_TYPE_TIMESTAMP separado do C2, indices por slot e suporte do device",
             "- Fonte de verdade para slot e fence em cada reset/read; conferir retorno de cada chamada",
             "- Etapas de pipeline, multiview e validity bits; chamadas legais dentro do render pass",
             "- Flush de burst antes de vkCmdEndRenderPass e ao alternar para ceu adiado",
             "- Risco de overhead e vies de selecao dos primeiros 4 blocos de cada slot",
             "- Somente depois: nova compilacao ARM64 NO APK, sem interferir em assinatura e saves"]
      (OUT/"PRE668_V51_VULKAN_SOURCE_SCOPE_REVIEW.md").write_text("\n".join(md)+"\n",encoding="utf-8")
      print("PRE668_STATUS="+result["status"])
      if result.get("callsite_evidence"):
        print("PRE668_RENDERPASS_BEGIN_LINE="+str(result["callsite_evidence"]["renderer_open_pass"]["lines"]))
        print("PRE668_RENDERPASS_END_LINE="+str(result["callsite_evidence"]["renderer_close_pass"]["lines"]))
        print("PRE668_TIMESTAMP_WRITE_C2_LINE="+str(result["callsite_evidence"]["backend_vk_timestamp_write"]["lines"]))
      print("PRE668_VULKAN_COMMANDS_INJECTED=false")
      print("PRE668_ARM64_COMPILED=false")
      print("PRE668_APK_BUILT=false")
      print("PRE668_GPU_SHADER_TIME_MEASURED=false")
      print("PRE668_FPS_GAIN_PROVEN=false")
      print("PRE668_ERROR_TYPE="+result.get("error_type","none"))
    return 0 if result["status"]=="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY" else 1
if __name__=="__main__":sys.exit(main())
