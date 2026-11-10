#!/usr/bin/env python3
"""PRE675 / SB-02: READ-ONLY shadow/depth/resolve and guest-copy lexical dependency
map from authenticated V51 source. No change to source, shaders, APK, keys,
GPU commands or device; reports candidates, NOT safe deferred shadow resolve.
"""
from __future__ import annotations
import hashlib,json,re,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as v50
import pre648_v50_shader_pass_counts_arm64_noapk as p648
import pre665_v51_gpu_draw_emission_boundaries_readonly as p665

OUT=Path("/tmp/nfsmw-pre675")
REPORT=OUT/"PRE675_V51_SHADOW_DEPTH_RESOLVE_SOURCE_DEPENDENCY_AUDIT.json"
DOC=OUT/"PRE675_SB02_SHADOW_DEPTH_READONLY_REPORT.md"
POLICY=Path("docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json")
PRE668=Path("docs/PRE668_V51_VULKAN_RENDERPASS_AND_QUERY_SCOPE_VERIFIED.json")
PRE674=Path("docs/FLUXO_SPEEDBREAKER_NFSMW_ANDROID.md")
PIN_RENDER=p665.PIN_RENDER
PIN_BASE=p665.PIN_BASE
PIN_BACKEND=p665.PIN_DESTINOS
PIN_HEADER=p665.PIN_HEADER
RENDER=Path("nativo/app/src/nfsmw_nativo_dibujos.cpp")
BACKEND=Path("nativo/app/src/nfsmw_nativo_destinos.cpp")
ANCHORS={
 "shadow_terms":r"\b(?:shadow(?:s|map)?|sombra(?:s)?|sombras|sunshadow)\b",
 "depth_terms":r"\b(?:depth(?:Stencil)?|profundidad|zbuffer|z_buffer|D24S8|D32_SFLOAT|D16_UNORM)\b",
 "shadow_depth_formats":r"\b(?:VK_FORMAT_[A-Z0-9_]*(?:D16|D24|D32|S8)[A-Z0-9_]*|VK_IMAGE_ASPECT_DEPTH_BIT|VK_IMAGE_ASPECT_STENCIL_BIT)\b",
 "renderpass_begin_end":r"\bvkCmd(?:BeginRenderPass|EndRenderPass|BeginRendering|EndRendering)\s*\(",
 "renderpass_attachments":r"\b(?:VkAttachmentDescription|VkAttachmentReference|VkFramebufferCreateInfo|VkRenderPassCreateInfo|VkSubpassDescription|VkImageViewCreateInfo)\b",
 "image_copy_resolve_blit":r"\bvkCmd(?:CopyImage|CopyImageToBuffer|CopyBufferToImage|ResolveImage|BlitImage|CopyBuffer)\s*\(",
 "image_layout_barrier":r"\b(?:vkCmdPipelineBarrier2?|VkImageMemoryBarrier2?|VK_IMAGE_LAYOUT_[A-Z0-9_]+)\b",
 "image_create_destroy":r"\b(?:vkCreateImage|vkDestroyImage|vkCreateImageView|vkDestroyImageView|vkAllocateMemory|vkFreeMemory)\s*\(",
 "gpu_reads_writes":r"\b(?:VK_ACCESS_[A-Z0-9_]+|VK_PIPELINE_STAGE_[A-Z0-9_]+)\b",
 "guest_read_write_candidates":r"\b(?:guest|huesped|invitado|memoria|AplazarCopia|PrepararTextura|SubirTextura|RecogerEnlaces|CopiarTextura|EscribirMemoria|LeerMemoria)\b",
 "texture_sampling_candidates":r"\b(?:vkUpdateDescriptorSets|vkCmdBindDescriptorSets|VkDescriptorImageInfo|VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL|VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER)\b",
 "shader_draw_candidates":r"\bvkCmdDraw(?:Indexed|Indirect|IndexedIndirect)?\s*\(",
}
def sha(b):return hashlib.sha256(b).hexdigest()
def check_pins():
    x=json.loads(POLICY.read_text())
    y=json.loads(PRE668.read_text())
    f=PRE674.read_text()
    if not (
      x.get("schema")=="nfsmw-speedbreaker-backlog-v1"
      and x.get("internal",{}).get("version_code")==51
      and x.get("upstream",{}).get("commit")=="fe04285d7629377c6e422a6ace8f535368f23c31"
      and x.get("policy",{}).get("automatic_release") is False
      and x.get("candidates",[{}])[1].get("id")=="SB-02"
      and x["candidates"][1].get("status")=="queued_readonly"
      and y.get("status")=="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY"
      and y.get("authenticated_source",{}).get("renderer_v51_sha256")==PIN_RENDER
      and y.get("authenticated_source",{}).get("backend_sha256")==PIN_BACKEND
      and "SB-02" in f and "GPL" in f
    ):raise ValueError("PRE675 approved flow or V51 source pin mismatch")
    return {"speedbreaker_flow_sha256":sha(PRE674.read_bytes()),
        "speedbreaker_backlog_sha256":sha(POLICY.read_bytes()),
        "pre668_source_pin_sha256":sha(PRE668.read_bytes())}
def scan(txt,pattern):
    # No assumptions on AST or execution order; lexical source index only.
    rows=txt.splitlines()
    matches=[]
    rx=re.compile(pattern,re.IGNORECASE)
    for n,line in enumerate(rows,1):
        if rx.search(line):
            matches.append(n)
    examples=[]
    for n in matches[:10]:
        lo=max(1,n-3);hi=min(len(rows),n+3)
        examples.append({"line":n,"context":[f"{j}: {rows[j-1][:210]}" for j in range(lo,hi+1)]})
    return {"count":len(matches),"first_lines":matches[:50],
            "examples":examples,"truncated_count":max(0,len(matches)-len(examples))}
def source_scan(renderer,backend):
    result={}
    for path,text in ((str(RENDER),renderer),(str(BACKEND),backend)):
        result[path]={name:scan(text,rx) for name,rx in ANCHORS.items()}
    return result
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r={
       "stage":"PRE675_SPEEDBREAKER_SB02_AUTHENTIC_V51_SHADOW_RESOLVE_SOURCE_DEPENDENCY_READONLY",
       "status":"FAILED_CLOSED",
       "utc":datetime.now(timezone.utc).isoformat(),
       "read_only":True,"apk_built":False,"arm64_compiled":False,
       "signed_v51_modified":False,"temp_source_modified":False,
       "shader_spirv_modified":False,"license_review_required_for_literal_port":True,
       "external_code_imported":False,"signing_material_accessed":False,
       "user_saves_accessed":False,"actual_shadow_resolve_deferred":False,
       "shadow_lend_equivalence_proven":False,"guest_memory_consumer_semantics_proven":False,
       "barrier_lifetime_safety_proven":False,"gpu_timestamp_measured":False,
       "fps_gain_proven":False
    }
    try:
        evidence=check_pins()
        v50.require_pre637()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre675_sb02_") as directory:
            temp=Path(directory)
            arc=temp/"pre99.tar.gz"
            download(drive_client(),arc)
            hashgot,size=sha_file(arc)
            if (hashgot,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE675 source archive wrong hash or size")
            dest=temp/"restore";dest.mkdir()
            restore(arc,dest)
            arc.unlink(missing_ok=True)
            root=dest/"workspace"
            replay=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if replay["PRE398"].get("cheat_enabled") is not True:
                raise ValueError("PRE675 authenticated Nitro recipe not retained")
            prev=p434.ORIGINAL_STAGE
            def menu_already_registered(base):
                cmake=(base/"nativo/app/CMakeLists.txt").read_text()
                if cmake.count(v46.PRE292_REGISTER)!=1:
                    raise ValueError("PRE675 V51 menu recipe not registered once")
                return {"menu_registered_once":True}
            try:
                p434.ORIGINAL_STAGE=menu_already_registered
                staged=v50.stage_v50(root)
            finally:
                p434.ORIGINAL_STAGE=prev
            if not (
                staged.get("pre638_v49_source_recipe_verified") is True
                and staged.get("pre638_c3_fallback_bypass") is False
                and staged.get("pre638_v49_callbacks_nitro_preserved") is True
                and staged.get("pre638_save_modified") is False
            ):raise ValueError("PRE675 previous C3/Nitro staging proof invalid")
            original=(root/RENDER).read_bytes()
            backend=(root/BACKEND).read_bytes()
            if sha(original)!=PIN_BASE or sha(backend)!=PIN_BACKEND:
                raise ValueError("PRE675 V51 authenticated renderer/backend base mismatch")
            render=p648.patch_bytes(original)
            if sha(render)!=PIN_RENDER or sha(p648.HEADER.read_bytes())!=PIN_HEADER:
                raise ValueError("PRE675 PRE648 V51 shader counter source hash differs")
            scans=source_scan(render.decode("utf-8"),backend.decode("utf-8"))
            render_file=scans[str(RENDER)]
            backend_file=scans[str(BACKEND)]
            if render_file["shader_draw_candidates"]["count"]<2 or render_file["renderpass_begin_end"]["count"]<2:
                raise ValueError("PRE675 Vulkan renderer draw/renderpass sites missing")
            if backend_file["image_copy_resolve_blit"]["count"]+render_file["image_copy_resolve_blit"]["count"]==0:
                # Source still valid: report unsupported hypothesis, not false PASS.
                interpretation="No vkCmdCopyImage/vkCmdBlitImage/vkCmdResolveImage token found in the two inspected files; the copy graph could reside elsewhere"
            else:interpretation="GPU copy/resolve/blit references located; no evidence yet that they are depth/shadow resolves"
            if (root/RENDER).read_bytes()!=original or (root/BACKEND).read_bytes()!=backend:
                raise ValueError("PRE675 source changed during readonly scan")
            r["source"]={**evidence,"authenticated_pre99_sha256":hashgot,
              "renderer_before_pre648_sha256":sha(original),
              "renderer_v51_counter_sha256":sha(render),
              "backend_v51_sha256":sha(backend),
              "pre648_header_sha256":sha(p648.HEADER.read_bytes()),
              "replay":"PRE99 + PRE431 + PRE638 + PRE648 in memory",
              "temporary_tree_only":True,
              "signed_release_elf_identical_to_replay_proven":False}
            r["anchors"]=scans
            r["findings"]={
             "copy_sites_observed":interpretation,
             "shadow_or_depth_token_sites_in_renderer":render_file["shadow_terms"]["count"]+render_file["depth_terms"]["count"],
             "shadow_or_depth_token_sites_in_backend":backend_file["shadow_terms"]["count"]+backend_file["depth_terms"]["count"],
             "copy_and_blit_renderer_sites":render_file["image_copy_resolve_blit"]["count"],
             "copy_and_blit_backend_sites":backend_file["image_copy_resolve_blit"]["count"],
             "image_layout_barrier_renderer_sites":render_file["image_layout_barrier"]["count"],
             "image_layout_barrier_backend_sites":backend_file["image_layout_barrier"]["count"],
             "guest_memory_reads_proven":False,
             "image_to_guest_coherency_proven":False,
             "safe_shadow_lending_proven":False,
             "prioritize_next":"Trace actual VkImage extents/formats and guest address consumers of shadow copy/resolve before deciding if deferred resolves can be implemented"
            }
        r["status"]="AUDIT_OK_AUTHENTIC_V51_SHADOW_SOURCE_CANDIDATE_MAP_ONLY"
    except Exception as exc:
        r["error_type"]=type(exc).__name__
        r["error_summary"]=str(exc)[:300] if isinstance(exc,ValueError) else "Source restore or dependency/API exception"
    finally:
        REPORT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
        lines=[
          "# PRE675 / SB-02 — inventário somente leitura de shadow/depth e transferências Vulkan",
          "",
          "**Resultado:** "+r["status"],
          "",
          "Fonte autenticada PRE99→PRE431→PRE638→PRE648 em diretório temporário, com hashes V51. "
          "As correspondências são **lexicais**, não fluxo de execução nem prova de custo GPU.",
          "",
          "## Âncoras de código",
        ]
        for file,patterns in r.get("anchors",{}).items():
            lines.append(f"### {file}")
            for key,v in patterns.items():lines.append(f"- {key}: {v['count']} ocorrências; primeiras linhas {v['first_lines'][:12]}")
        lines += [
           "",
           "## Evidências que ainda faltam",
           "1. Identificar se as cópias encontradas realmente escrevem o mapa de sombras D24S8 e se o guest lê esses bytes na mesma frame.",
           "2. Estabelecer formato, mip, layer, layout, destino físico guest e invalidação/cache antes de adiar qualquer cópia.",
           "3. Avaliar pixel fidelity e consistência de memória guest com resolvers em fixture; rejeitar todos os casos incertos.",
           "4. Medir tempo real por passe com fences/availability no Galaxy S24 FE; contagens lexicais não representam execução.",
           "",
           "Nenhum código SpeedBreaker foi copiado ou integrado. Nenhum APK, shader, timestamp ou build ARM64.",
        ]
        DOC.write_text("\n".join(lines)+"\n")
        for key in ("status","error_type"):
            print("PRE675_"+key.upper()+"="+str(r.get(key,"none")))
        if r.get("findings"):
            for k in ("shadow_or_depth_token_sites_in_renderer","copy_and_blit_renderer_sites",
                      "copy_and_blit_backend_sites","image_layout_barrier_renderer_sites"):
                print("PRE675_"+k.upper()+"="+str(r["findings"].get(k,0)))
        print("PRE675_SHADOW_LEND_IMPLEMENTED=false")
        print("PRE675_APK_BUILT=false")
        print("PRE675_FPS_GAIN_PROVEN=false")
    return 0 if r["status"]=="AUDIT_OK_AUTHENTIC_V51_SHADOW_SOURCE_CANDIDATE_MAP_ONLY" else 1
if __name__=="__main__":sys.exit(main())
