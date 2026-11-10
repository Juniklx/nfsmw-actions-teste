#!/usr/bin/env python3
"""PRE662 — authenticated Vulkan timestamp alias, pool capacity and lifecycle.
Only inspects reconstructed PRE638 V50 source that underlies V51.
Does not build/install APK, touch keys, edit shaders or saves, or time the GPU.
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

OUT=Path("/tmp/nfsmw-pre662")
SOURCE_SHA="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
OLD=Path("docs/PRE660_V51_GPU_VULKAN_TIMESTAMP_FEASIBILITY_VERIFIED.json")
PATTERNS={
  "writer_alias":r"\bescribir_marca_\b",
  "reader_alias":r"\bleer_consultas_\b",
  "slot_capacity":r"\bkMarcasPorRanura\b",
  "timestamp_pool":r"\bconsultas_\b",
  "slot_use":r"\branura_\b",
  "timestamp_period":r"\bperiodo_marca_ns_\b",
  "valid_bits":r"\btimestampValidBits\b",
  "mark_function":r"\bvoid\s+MarcarGpu\s*\(",
  "write_vk_name":r"\bvkCmdWriteTimestamp(?:2(?:KHR)?)?\b",
  "read_vk_name":r"\bvkGetQueryPoolResults\b",
  "device_proc":r"\bvkGetDeviceProcAddr\b",
  "instance_proc":r"\bvkGetInstanceProcAddr\b",
  "queue_submit":r"\bvkQueueSubmit(?:2(?:KHR)?)?\b",
  "fence_wait":r"\bvkWaitForFences\b",
  "fence_status":r"\bvkGetFenceStatus\b",
  "query_reset":r"\bvkCmdResetQueryPool\b",
  "begin_commands":r"\bvkBeginCommandBuffer\b",
  "end_commands":r"\bvkEndCommandBuffer\b",
  "result_wait_flag":r"\bVK_QUERY_RESULT_WAIT_BIT\b",
  "result_status":r"\bVK_NOT_READY\b",
  "precise_stage":r"\bVK_PIPELINE_STAGE_(?:BOTTOM_OF_PIPE|TOP_OF_PIPE)_BIT\b",
  "timestamps_per_work":r"\bmarcas_gpu\b|\bnumero_marcas\b|\bmarcas_usadas\b",
}
def sha(b):return hashlib.sha256(b).hexdigest()
def match_occurrences(src,pat):
    return [m.start() for m in re.finditer(pat,src)]
def context(src,hit,before=10,after=16):
    lines=src.splitlines()
    number=src.count("\n",0,hit)+1
    lo=max(1,number-before);hi=min(len(lines),number+after)
    return {"start_line":lo,"end_line":hi,
      "text":"\n".join(f"{line:>5}: {lines[line-1][:240]}" for line in range(lo,hi+1))}
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE662_V51_VULKAN_TIMESTAMP_ALIAS_QUERY_POOL_LIFECYCLE",
      "status":"FAILED_CLOSED",
      "utc":datetime.now(timezone.utc).isoformat(),
      "no_apk_built":True,"no_keys_accessed":True,"no_shaders_modified":True,
      "no_sources_written_to_drive":True,"no_saves_accessed":True,
      "no_phone_runtime_changed":True,"per_shader_gpu_time_measured":False,
      "fps_gain_proven":False}
    try:
        old=json.loads(OLD.read_text())
        if not (old.get("status")=="AUDIT_OK_STATIC_VULKAN_TIMESTAMP_SUPPORT"
          and old.get("github_run_id")==42817191509
          and old.get("source",{}).get("pal_v50_source_sha256")==SOURCE_SHA
          and old.get("findings",{}).get("writer_and_reader_implementation_not_yet_resolved") is True):
            raise ValueError("PRE662 prior PRE660 evidence changed")
        p638.require_pre637()
        with tempfile.TemporaryDirectory(prefix="pre662_timestamp_src_") as td:
            temp=Path(td)
            tar=temp/"pre99.tar.gz"
            download(drive_client(),tar)
            digest,_,size=sha_file(tar)
            if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE662 authentic PRE99 source snapshot hash mismatch")
            dest=temp/"restore";dest.mkdir()
            restore(tar,dest)
            tar.unlink(missing_ok=True)
            root=dest/"workspace"
            pre=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if pre["PRE398"].get("cheat_enabled") is not True:
                raise ValueError("PRE662 preserved Nitro stage missing")
            prior=p434.ORIGINAL_STAGE
            def registered_menu(r):
                cmake=(r/"nativo/app/CMakeLists.txt").read_text()
                if cmake.count(v46.PRE292_REGISTER)!=1:
                    raise ValueError("PRE662 PRE292 menu registration differs")
                return {"menu_registered_once":True}
            try:
                p434.ORIGINAL_STAGE=registered_menu
                staged=p638.stage_v50(root)
            finally:
                p434.ORIGINAL_STAGE=prior
            if not (staged.get("pre638_v49_source_recipe_verified") is True
                and staged.get("pre638_c3_fallback_bypass") is False
                and staged.get("pre638_v49_callbacks_nitro_preserved") is True
                and staged.get("pre638_save_modified") is False):
                raise ValueError("PRE662 V50 production source stage not authenticated")
            dib=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
            if sha(dib.read_bytes())!=SOURCE_SHA:
                raise ValueError("PRE662 native renderer source SHA changed")
            srcpath=root/"nativo/app/src/nfsmw_nativo_destinos.cpp"
            hdrpath=root/"nativo/app/src/nfsmw_nativo_destinos.h"
            src=srcpath.read_text(encoding="utf-8")
            hdr=hdrpath.read_text(encoding="utf-8")
            report["source"]={"renderer_sha256":SOURCE_SHA,
              "timestamp_cpp_sha256":sha(srcpath.read_bytes()),
              "timestamp_header_sha256":sha(hdrpath.read_bytes()),
              "pre99_sha256":digest,
              "replay":"PRE99→PRE431→PRE638",
              "binary_equivalence_with_signed_V51_not_proven":True}
            hits={}
            for label,regex in PATTERNS.items():
                indices=match_occurrences(src,regex)
                # The key section is bounded but includes every occurrence position for audit
                hits[label]={
                   "total_matches":len(indices),
                   "line_numbers":[src.count("\n",0,p)+1 for p in indices][:100],
                   "source_snippets":[context(src,p,9,13) for p in indices[:10]]
                }
            for name in ("writer_alias","reader_alias","slot_capacity",
                         "timestamp_pool","mark_function","query_reset",
                         "queue_submit","fence_wait"):
                if not hits[name]["total_matches"]:
                    raise ValueError("PRE662 required source anchor missing: "+name)
            # Record also exact init/allocation and result/write lifecycle blocks with line numbers.
            lines=src.splitlines()
            regions={"initialization":[995,1125],
                     "mark_gpu":[3635,3730],
                     "query_reset_and_submit":[4750,5050],
                     "query_readback":[5300,5520]}
            excerpts={}
            for label,(a,b) in regions.items():
                if a>len(lines):raise ValueError("PRE662 source shorter than known PRE660 map")
                b=min(b,len(lines))
                excerpts[label]={"first_line":a,"last_line":b,
                  "lines":[f"{n:>5}: {lines[n-1][:245]}" for n in range(a,b+1)]}
            report["source_hits"]=hits
            report["source_excerpts"]=excerpts
            # Only report actual names; no inference from indirect commands yet
            report["direct_vk_cmd_write_timestamp_mentions"]=hits["write_vk_name"]["total_matches"]
            report["direct_vk_query_results_mentions"]=hits["read_vk_name"]["total_matches"]
            report["source_authenticated"]=True
        report["status"]="AUDIT_OK_SOURCE_ALIAS_LIFECYCLE_EXTRACTED"
        report["next_gate"]="Interpret writer/reader pointer calls, per-slot query limits, readback fence ordering and bounded GPU sampling before any diagnostic code"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        report["error_summary"]=str(exc)[:220] if isinstance(exc,ValueError) else "Read-only audit failed"
    finally:
        (OUT/"PRE662_V51_GPU_TIMESTAMP_ALIAS_LIFECYCLE_AUDIT.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        overview=["# PRE662 — Vulkan timestamps: aliases e ciclo de vida","",
          "**Status:** "+report["status"],
          "Somente leitura da fonte PAL autenticada; sem APK e sem medição por shader.","",
          "## Ocorrências dos mecanismos (código, não execução)"]
        overview.extend(f"- {k}: {v['total_matches']} ocorrências" for k,v in
                        report.get("source_hits",{}).items())
        overview+=["","## Limites",
          "Medições C2 por grupo não equivalem ao custo de VS62/PS58.",
          "Nenhum FPS, temperatura ou otimização comprovada."]
        (OUT/"RELATORIO_PRE662_V51_GPU_TIMESTAMP_LIFECYCLE.md").write_text(
          "\n".join(overview)+"\n",encoding="utf-8")
        for label,val in (("STATUS",report["status"]),
          ("SOURCE_AUTHENTICATED",report.get("source_authenticated",False)),
          ("WRITER_ALIAS_HITS",report.get("source_hits",{}).get("writer_alias",{}).get("total_matches",0)),
          ("READER_ALIAS_HITS",report.get("source_hits",{}).get("reader_alias",{}).get("total_matches",0)),
          ("QUERY_CAPACITY_HITS",report.get("source_hits",{}).get("slot_capacity",{}).get("total_matches",0)),
          ("FPS_GAIN_PROVEN",False),("APK_BUILT",False),
          ("ERROR_TYPE",report.get("error_type","none"))):
            print("PRE662_"+label+"="+str(val))
    return 0 if report["status"]=="AUDIT_OK_SOURCE_ALIAS_LIFECYCLE_EXTRACTED" else 1

if __name__=="__main__":
    sys.exit(run())
