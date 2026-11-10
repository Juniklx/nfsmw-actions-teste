#!/usr/bin/env python3
"""PRE679 / SB-02: READ-ONLY shadow/depth/resolve and guest-copy lexical dependency
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

OUT=Path("/tmp/nfsmw-pre679")
REPORT=OUT/"PRE679_V51_CVAR_BLUR_SPECIALIZATION_SOURCE_AUDIT.json"
DOC=OUT/"PRE679_SB02_CVAR_BLUR_SPECIALIZATION_READONLY_REPORT.md"
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
    ):raise ValueError("PRE679 approved flow or V51 source pin mismatch")
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
       "stage":"PRE679_SPEEDBREAKER_SB02_AUTHENTIC_V51_SHADOW_RESOLVE_SOURCE_DEPENDENCY_READONLY",
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
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre679_sb02_") as directory:
            temp=Path(directory)
            arc=temp/"pre99.tar.gz"
            download(drive_client(),arc)
            hashgot,_,size=sha_file(arc)
            if (hashgot,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE679 source archive wrong hash or size")
            dest=temp/"restore";dest.mkdir()
            restore(arc,dest)
            arc.unlink(missing_ok=True)
            root=dest/"workspace"
            replay=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if replay["PRE398"].get("cheat_enabled") is not True:
                raise ValueError("PRE679 authenticated Nitro recipe not retained")
            prev=p434.ORIGINAL_STAGE
            def menu_already_registered(base):
                cmake=(base/"nativo/app/CMakeLists.txt").read_text()
                if cmake.count(v46.PRE292_REGISTER)!=1:
                    raise ValueError("PRE679 V51 menu recipe not registered once")
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
            ):raise ValueError("PRE679 previous C3/Nitro staging proof invalid")
            original=(root/RENDER).read_bytes()
            backend=(root/BACKEND).read_bytes()
            if sha(original)!=PIN_BASE or sha(backend)!=PIN_BACKEND:
                raise ValueError("PRE679 V51 authenticated renderer/backend base mismatch")
            render=p648.patch_bytes(original)
            if sha(render)!=PIN_RENDER or sha(p648.HEADER.read_bytes())!=PIN_HEADER:
                raise ValueError("PRE679 PRE648 V51 shader counter source hash differs")
            scans=source_scan(render.decode("utf-8"),backend.decode("utf-8"))
            render_file=scans[str(RENDER)]
            backend_file=scans[str(BACKEND)]
            if render_file["shader_draw_candidates"]["count"]<2 or render_file["renderpass_begin_end"]["count"]<2:
                raise ValueError("PRE679 Vulkan renderer draw/renderpass sites missing")
            if backend_file["image_copy_resolve_blit"]["count"]+render_file["image_copy_resolve_blit"]["count"]==0:
                # Source still valid: report unsupported hypothesis, not false PASS.
                interpretation="No vkCmdCopyImage/vkCmdBlitImage/vkCmdResolveImage token found in the two inspected files; the copy graph could reside elsewhere"
            else:interpretation="GPU copy/resolve/blit references located; no evidence yet that they are depth/shadow resolves"
            # PRE679 targeted *lexical* dependency trace, source-only.
            pre678_pin=json.loads(Path("docs/PRE678_SB02_V51_DEPTH_GRAPHICS_QUALITY_VERIFIED.json").read_text())
            if not (
              pre678_pin.get("status")=="AUDIT_OK_AUTHENTIC_V51_DEPTH_STATE_AND_GRAPHICS_QUALITY_SOURCE_ONLY"
              and pre678_pin.get("github",{}).get("run_id")==42876324398
              and pre678_pin.get("drive",{}).get("readback_identical") is True
              and pre678_pin.get("findings",{}).get("radial_blur_disabled_by_default_in_renderer_source",{}).get("defined_default") is True
              and pre678_pin.get("source",{}).get("renderer_v51_sha256")==PIN_RENDER
            ):raise ValueError("PRE679 previous blur source pin unavailable or invalid")
            pre677_pin=json.loads(Path("docs/PRE677_SB02_V51_EXISTING_DEPTH_VERIFIED.json").read_text())
            if not (
                pre677_pin.get("status")=="AUDIT_OK_AUTHENTIC_V51_EXISTING_DEFERRED_DEPTH_SOURCE_TRACE_ONLY"
                and pre677_pin.get("github",{}).get("run_id")==42874003191
                and pre677_pin.get("drive",{}).get("crc_ok") is True
                and pre677_pin.get("drive",{}).get("readback_identical") is True
                and pre677_pin.get("source",{}).get("renderer_v51_sha256")==PIN_RENDER
                and pre677_pin.get("source",{}).get("backend_v51_sha256")==PIN_BACKEND
                and pre677_pin.get("synthetic_guards",{}).get("negative_test_cases")==24
                and pre677_pin.get("safety",{}).get("no_source_edits") is True
            ):raise ValueError("PRE679 PRE677 evidence is not authenticated")
            pre676_pin=json.loads(Path("docs/PRE676_SB02_V51_GUEST_READBACK_TRACE_VERIFIED.json").read_text())
            if not (
                pre676_pin.get("status")=="AUDIT_OK_AUTHENTIC_V51_COPY_READBACK_SOURCE_TRACE_ONLY"
                and pre676_pin.get("github",{}).get("run_id")==42871368565
                and pre676_pin.get("drive",{}).get("zip_crc_ok") is True
                and pre676_pin.get("drive",{}).get("readback_sha_match") is True
                and pre676_pin.get("source",{}).get("renderer_v51_sha256")==PIN_RENDER
                and pre676_pin.get("source",{}).get("backend_v51_sha256")==PIN_BACKEND
                and pre676_pin.get("limits",{}).get("no_safe_to_defer_conclusion") is True
            ):raise ValueError("PRE679 prior PRE676 evidence gate differs")
            pre675_pin=json.loads(Path("docs/PRE675_SB02_V51_SHADOW_READONLY_VERIFIED.json").read_text())
            if not (
                pre675_pin.get("github_run_id")==42869180941
                and pre675_pin.get("status")=="AUDIT_OK_AUTHENTIC_V51_SHADOW_SOURCE_CANDIDATE_MAP_ONLY"
                and pre675_pin.get("source",{}).get("renderer_v51_sha256")==PIN_RENDER
                and pre675_pin.get("source",{}).get("backend_v51_sha256")==PIN_BACKEND
                and pre675_pin.get("drive_readback_identical") is True
                and pre675_pin.get("lexical_sites",{}).get("renderer",{}).get("copy_call_lines")==[9770]
                and pre675_pin.get("lexical_sites",{}).get("backend",{}).get("copy_call_lines")==[5543,5667]
            ):raise ValueError("PRE679 prior PRE675 trusted source/copy-site gate mismatch")
            rlines=render.decode("utf-8").splitlines()
            blines=backend.decode("utf-8").splitlines()
            sites=[
                ("renderer_buffer_upload",rlines,9770,"vkCmdCopyBufferToImage"),
                ("backend_png_dump",blines,5543,"vkCmdCopyImageToBuffer"),
                ("backend_guest_readback",blines,5667,"vkCmdCopyImageToBuffer")
            ]
            def window(lines,center,before=55,after=90):
                a=max(1,center-before);b=min(len(lines),center+after)
                return {"first_line":a,"last_line":b,
                        "source_excerpt":[f"{n:5d}: {lines[n-1][:260]}" for n in range(a,b+1)]}
            r["copy_sites"]={}
            for name,lines,lineno,api in sites:
                if api not in lines[lineno-1] or lines[lineno-1].lstrip().startswith("//"):
                    raise ValueError(f"PRE679 exact Vulkan transfer site changed {name}:{lineno}")
                r["copy_sites"][name]={"line":lineno,"api":api,"window":window(lines,lineno)}
            # Demand distinguishing source details so classification does not drift.
            if not (
                "subida_" in rlines[9769] and "textura.imagen.imagen" in rlines[9769]
                and 'fmt::format("{:03}.png"' in blines[5543]
                and "volcado_indice_" in blines[5544]
                and "resuelta.imagen.imagen" in blines[5666]
                and "lecturas_pendientes_.push_back" in blines[5668]
                and "rb_copy_dest_base" in blines[5668]
                and "rb_copy_dest_pitch" in blines[5669]
            ):raise ValueError("PRE679 upload, png dump or guest readback proof not anchored")
            patterns={
                "readback_queue":"lecturas_pendientes_",
                "guest_base":"rb_copy_dest_base",
                "guest_pitch":"rb_copy_dest_pitch",
                "submit_transfer":"AntesDeTransferir",
                "fence_wait":"vkWaitForFences",
                "fence_status":"vkGetFenceStatus",
                "readback_map":"vkMapMemory",
                "transfer_to_guest_candidate":"memcpy",
                "depth_image_aspect":"VK_IMAGE_ASPECT_DEPTH_BIT",
                "depth_stencil_format":"VK_FORMAT_D24_UNORM_S8_UINT",
                "layout_general":"VK_IMAGE_LAYOUT_GENERAL",
                "vk_resolve_image":"vkCmdResolveImage",
                "image_to_buffer":"vkCmdCopyImageToBuffer",
                "buffer_to_image":"vkCmdCopyBufferToImage",
                "copy_result_image":"resuelta",
                "transfer_cleanup":"lectura.bufer"
            }
            r["consumer_candidates"]={}
            for title,lines in (("renderer",rlines),("backend",blines)):
                r["consumer_candidates"][title]={}
                for tag,needle in patterns.items():
                    places=[i for i,line in enumerate(lines,1) if needle in line]
                    r["consumer_candidates"][title][tag]={
                        "count":len(places),"first_lines":places[:80],
                        "source_windows":[window(lines,i,8,14) for i in places[:8]]}
            if r["consumer_candidates"]["backend"]["readback_queue"]["count"]<2:
                raise ValueError("PRE679 guest readback queue producer/consumer sites missing")
            r["source_site_classification"]={
                "renderer_9770":"host buffer -> GPU image upload, not image -> guest shadow resolve",
                "backend_5543":"GPU image -> buffer, near .png / volcado diagnostic capture; may include depth",
                "backend_5667":"GPU resolved image -> buffer; readback queue carries guest base and pitch metadata",
                "copy_operations_are_proven_shadow_resolves":False,
                "consumer_execution_order_proven":False,
                "readback_sync_equivalence_proven":False,
                "safe_to_defer_any_transfer":False,
                "implicit_depth_resolves_elsewhere_ruled_out":False,
                "per_frame_runtime_frequency_measured":False,
                "next":"Trace actual readback drain / guest-memory write, transfer fences, renderpass implicit resolves, depth/stencil format conversion; do not defer without G2 equivalence and negative cases"}
            # PRE679: inspect existing depth-copy deferral (read-only). This is
            # NOT a patch and not proof of correct GPU/runtime behavior.
            observed={
              "depth_copy":"CopiarProfundidad",
              "depth_before_write":"AntesDeEscribirProfundidad",
              "depth_pending_map":"pendientes_",
              "depth_lazy_flag":"nfsmw_nativo_profundidad_perezosa",
              "shadow_swap_flag":"nfsmw_nativo_prestar",
              "car_shadow_comment":"el coche deja de recibir sombras",
              "depth_source":"profundidad",
              "resolved_texture":"TexturaResuelta",
              "image_aspect_depth":"VK_IMAGE_ASPECT_DEPTH_BIT",
              "depth_format":"VK_FORMAT_D24_UNORM_S8_UINT",
              "image_stencil":"VK_IMAGE_ASPECT_STENCIL_BIT",
              "barrier":"vkCmdPipelineBarrier",
              "collect_links":"RecogerEnlaces",
              "destroy_resource":"Destruir",
              "guest_memory_write":"EscribirTexelsEnGuest",
              "copy_deferred_log":"APLAZADA",
              "draw_sampling":"vkCmdBindDescriptorSets"
            }
            r["existing_deferred_depth"]={}
            for title,lines in (("renderer",rlines),("backend",blines)):
                r["existing_deferred_depth"][title]={}
                for tag,term in observed.items():
                    pts=[n for n,line in enumerate(lines,1) if term in line]
                    r["existing_deferred_depth"][title][tag]={
                      "count":len(pts),"first_lines":pts[:120],
                      "windows":[window(lines,n,15,22) for n in pts[:10]]}
            must=r["existing_deferred_depth"]["backend"]
            if not (must["depth_copy"]["count"]>0 and
                    must["depth_pending_map"]["count"]>0 and
                    must["depth_lazy_flag"]["count"]>0 and
                    must["car_shadow_comment"]["count"]>0):
                raise ValueError("PRE679 existing depth mechanism or documented shadow regression absent")
            r["depth_contexts"]={
              "config_shadow_swap_and_lazy_depth":window(blines,299,60,100),
              "deferred_depth_registration":window(blines,1420,65,110),
              "pending_depth_copy_flush":window(blines,1560,95,130),
              "depth_image_formats_barriers":window(blines,1850,85,110),
              "fence_completion":window(blines,4939,75,110),
              "readback_guest_memory":window(blines,5717,60,65)
            }
            # Isolated conservative HOST predicate exercises (synthetic only).
            keys=("explicit_optin","owner_known","format_exact","mip_layer_extent_exact",
                  "source_before_write_guard","destination_before_write_guard",
                  "sampler_dependency_known","barrier_and_fence_known",
                  "no_guest_cpu_observer","no_car_shadow_sampling",
                  "no_alias","source_lifetime_pinned")
            def allow_synthetic(case):
                return all(case.get(k) is True for k in keys)
            yes={k:True for k in keys}
            tests=[{"case":"all_guards_true_synthetic_only","expected":True,
                    "actual":allow_synthetic(yes)}]
            for key in keys:
                off=dict(yes);off[key]=False
                tests.append({"case":"deny_"+key,"expected":False,"actual":allow_synthetic(off)})
                absent=dict(yes);absent.pop(key)
                tests.append({"case":"deny_unknown_"+key,"expected":False,
                              "actual":allow_synthetic(absent)})
            if any(case["expected"] is not case["actual"] for case in tests):
                raise ValueError("PRE679 fail-closed synthetic host policy negative test failed")
            r["synthetic_host_guards"]={"status":"LOGICAL_MODEL_PASS_NOT_VULKAN",
                "tests":tests,"negative_tests":len(tests)-1,
                "true_V51_code_exercised":False,"pixel_equivalence_tested":False}
            r["depth_interpretation"]={
              "existing_lazy_depth_pipeline_in_V51_source":True,
              "previous_shadow_image_swap_regression_in_source_comment":True,
              "shadow_swap_safe_to_reenable":False,
              "safe_new_depth_deferral_proven":False,
              "depth_queue_frequency_per_frame":None,
              "GPU_and_guest_memory_equivalence_proven":False,
              "car_shadow_pixels_equal_proven":False,
              "host_guard_model_is_independent_of_V51_execution":True,
              "next":"PRE679: inspect precise state transitions and existing guards, derive real host test cases for copies/pixel/guest equivalence before considering any optimization"
            }
            # PRE679 precise declaration review. Inspect *code* rather than
            # trusting the surrounding performance comments or toggles.
            import collections
            flags=[
              "nfsmw_nativo_sin_desenfoque",
              "nfsmw_nativo_sombras_escala",
              "nfsmw_nativo_profundidad_perezosa",
              "nfsmw_nativo_frontal_perezoso",
              "nfsmw_nativo_sombra_minimo",
              "nfsmw_nativo_restaurar_por_intercambio",
              "nfsmw_nativo_profundidad_escalable",
              "nfsmw_nativo_sombras_pcf",
              "nfsmw_nativo_pase_sombras_sin_load"
            ]
            def declaration(name):
                rx=re.compile(r"\bREXCVAR_DEFINE_(BOOL|INT32|FLOAT)\s*\(\s*"+re.escape(name)+r"\s*,\s*(true|false|-?\d+(?:\.\d+)?)\b")
                seen=[]
                for title,lines in (("renderer",rlines),("backend",blines)):
                    joined="\n".join(lines)
                    for m in rx.finditer(joined):
                        line=joined.count("\n",0,m.start())+1
                        seen.append({"unit":title,"line":line,"type":m.group(1),
                                     "source_declared_default":m.group(2),
                                     "source_window":window(lines,line,5,9)})
                return seen
            r["graphics_cvar_declarations"]={name:declaration(name) for name in flags}
            # Every declaration that is present is preserved verbatim; no
            # claim about user TOML overriding the default is allowed.
            known=r["graphics_cvar_declarations"]
            for name,expected in (
                 ("nfsmw_nativo_profundidad_perezosa","true"),
                 ("nfsmw_nativo_frontal_perezoso","true"),
                 ("nfsmw_nativo_sombra_minimo","true"),
                 ("nfsmw_nativo_restaurar_por_intercambio","false")):
                if not any(x["source_declared_default"]==expected for x in known[name]):
                    raise ValueError("PRE679 backend default changed: "+name)
            def around_code(name,limit=15,before=14,after=44):
                found={}
                for title,lines in (("renderer",rlines),("backend",blines)):
                    found[title]=[
                        {"line":i,"window":window(lines,i,before,after)}
                        for i,line in enumerate(lines,1) if name in line
                    ][:limit]
                return found
            trace_symbols=[
              "AplazarCopiaProfundidad",
              "EjecutarCopiaProfundidad",
              "AntesDeEscribirProfundidad",
              "LecturasDeProfundidadMuertas",
              "perezosa_apagada_",
              "profundidades_descartadas_",
              "profundidad_descartada_",
              "profundidades_pendientes_",
              "pendientes_",
              "CopiarProfundidad",
              "SombraMinimoCopiaDesde",
              "SombraMinimoDiferencia",
              "SombraMinimoTrasIntercambio",
              "SombraMinimoAntesDeBorrar",
              "SombraMinimoEncendido",
              "copiar_imagen_",
              "vkCmdCopyImage",
              "vkGetDeviceProcAddr",
              "vkCmdBlitImage",
              "nfsmw_nativo_sombras_escala",
              "nfsmw_nativo_sin_desenfoque",
              "sin_desenfoque",
              "LecturasDeProfundidadMuertas(",
              "shader_p_000139",
              "HEIGHTMAP",
              "radial",
              "desenfoque"
            ]
            r["depth_state_symbol_evidence"]={name:around_code(name,18,10,18) for name in trace_symbols}
            def noncomment_occurrences(term,lines):
                return [{"line":i,"code":line.strip()[:260]}
                        for i,line in enumerate(lines,1)
                        if term in line and not line.lstrip().startswith(("//","*","/*"))]
            r["depth_state_calls"]={
              "backend":{
                x:noncomment_occurrences(x,blines)[:60]
                for x in ("AplazarCopiaProfundidad(","AntesDeEscribirProfundidad(",
                          "LecturasDeProfundidadMuertas(","SombraMinimoCopiaDesde(",
                          "copiar_imagen_(","SombraMinimoDiferencia(",
                          "REXCVAR_GET(nfsmw_nativo_profundidad_perezosa)")
              },
              "renderer":{
                x:noncomment_occurrences(x,rlines)[:60]
                for x in ("LecturasDeProfundidadMuertas(","sin_desenfoque","REXCVAR_GET(nfsmw_nativo_sin_desenfoque)")
              }
            }
            # Copy-image indirection is a separate call family from vkCmd*.
            r["copy_binding"]={
              "backend_assignment_candidates":[
                {"line":i,"code":line.strip()[:280]}
                for i,line in enumerate(blines,1)
                if re.search(r"copiar_imagen_\s*=",line)
              ],
              "vkCmdCopyImage_token_sites":{
                 title:[i for i,line in enumerate(lines,1) if "vkCmdCopyImage" in line]
                 for title,lines in (("renderer",rlines),("backend",blines))
              },
              "indirect_call_lines":[
                 i for i,line in enumerate(blines,1)
                 if re.search(r"copiar_imagen_\s*\(",line)
              ]
            }
            r["graphics_quality_assessment"]={
              "rendering_full_quality_proven":False,
              "user_toml_runtime_values_examined":False,
              "release_binary_cvar_defaults_proven":False,
              "blur_disabled_by_current_apk_proven":False,
              "blur_default_as_declared_in_two_inspected_units":[
                  {"unit":x["unit"],"line":x["line"],"value":x["source_declared_default"]}
                  for x in known["nfsmw_nativo_sin_desenfoque"]
              ],
              "shadow_resolution_scale_default_from_source":[
                  {"unit":x["unit"],"line":x["line"],"value":x["source_declared_default"]}
                  for x in known["nfsmw_nativo_sombras_escala"]
              ],
              "needs_full_effects_review_before_any_optimization":True,
              "safe_to_activate_image_swap":False,
              "safe_to_skip_any_additional_depth_copy":False,
              "real_gpu_work_per_frame_measured":False,
              "next":"PRE680: evaluate runtime TOML from device separately, develop isolated CVar/pending depth guard fixture, no automatic blur removal."
            }
            if (not r["copy_binding"]["indirect_call_lines"]
                or not r["depth_state_calls"]["backend"]["AplazarCopiaProfundidad("]
                or not r["depth_state_calls"]["backend"]["AntesDeEscribirProfundidad("]):
                raise ValueError("PRE679 depth state machine exact function call anchors changed")
            r["state_machine_inference"]={
              "queue_registration":"AplazarCopiaProfundidad may register deferred copy after depth resolve",
              "flush_on_sampling":"Pending copy may be recorded when depth texture sampled",
              "flush_or_drop_before_source_write":"AntesDeEscribirProfundidad chooses depending on outstanding readers/age",
              "late_read_guard":"perezosa_apagada_ may be toggled on DIFERENCIA",
              "readback_guest_color_path_independent":"PRE676 separate texture readback workflow",
              "inference_not_control_flow_proof":True,
              "pixel_equivalence_proven":False,
              "V51_runtime_testing":False
            }
            # PRE679: authoritative *source* flow only, no runtime cvar or
            # user's TOML available in this isolated replay.
            def cite_line(lines,line,token):
                if token not in lines[line-1]:
                    raise ValueError(f"PRE679 expected source anchor changed: {line} {token}")
                return {"line":line,"text":lines[line-1].strip(),
                        "window":window(lines,line,7,11)}
            d=known["nfsmw_nativo_sin_desenfoque"]
            if len(d)!=1 or d[0]["source_declared_default"]!="true" or d[0]["line"]!=195:
                raise ValueError("PRE679 radial blur CVar default changed")
            r["blur_dataflow"]={
              "default":cite_line(rlines,195,"REXCVAR_DEFINE_BOOL(nfsmw_nativo_sin_desenfoque, true"),
              "frame_latched":cite_line(rlines,4819,"REXCVAR_GET(nfsmw_nativo_sin_desenfoque)"),
              "final_composition_guard":cite_line(rlines,2637,"composicion_sin_desenfoque"),
              "composition_shader_fingerprint":cite_line(rlines,2638,"kHuellaComposicion"),
              "tell_depth_dead_read":cite_line(rlines,2640,"LecturasDeProfundidadMuertas(true)"),
              "end_depth_dead_read":cite_line(rlines,2738,"LecturasDeProfundidadMuertas(false)"),
              "specialization_condition":cite_line(rlines,3018,"composicion_sin_desenfoque"),
              "specialization_bit":cite_line(rlines,3019,"kSpecSinDesenfoque"),
              "quality_shadow_default":cite_line(blines,89,"REXCVAR_DEFINE_INT32(nfsmw_nativo_sombras_escala, 100"),
              "runtime_actual_cvar_value":None,
              "runtime_cvar_from_user_config_verified":False,
              "runtime_final_fragment_shader_variant_verified":False,
              "compiler_elided_depth_sampling_verified":False,
              "source_control_flow_consistent":True
            }
            # Discover other compiled source files which define/build specialization
            # bit or generic CVar config. Each hit includes file/line, never secrets
            # and never value of any user's settings.
            scan_roots=[root/"nativo/app",root/"nativo/sdk/include",root/"nativo/sdk/src"]
            targets=("kSpecSinDesenfoque","VkSpecializationInfo","pSpecializationInfo",
                     "specializationMapEntry","REXCVAR_GET","LoadConfig","config.toml")
            filehits={}
            config_candidates=[]
            inspected=0
            for sr in scan_roots:
                if not sr.exists():continue
                for fp in sr.rglob("*"):
                    if not fp.is_file() or fp.suffix not in (".cpp",".cc",".c",".h",".hpp",".toml",".ini",".json",".kt",".py"):
                        continue
                    rel=fp.relative_to(root).as_posix()
                    if any(q in rel.lower() for q in ("secret","credential","keystore","password","token")):
                        continue
                    if fp.stat().st_size>950000:continue
                    inspected+=1
                    if inspected>13000:raise ValueError("PRE679 source scan file count bound exceeded")
                    try: txt=fp.read_text(errors="replace")
                    except OSError:continue
                    lines=txt.splitlines()
                    matches={term:[n for n,line in enumerate(lines,1) if term in line][:18]
                             for term in targets}
                    matches={k:v for k,v in matches.items() if v}
                    if matches and (rel in (str(RENDER),str(BACKEND)) or
                                    any(k!="REXCVAR_GET" for k in matches)):
                        filehits[rel]={"terms":matches,
                           "selected_source_lines":{
                               term:[{"line":n,"code":lines[n-1][:240]} for n in nums[:10]]
                               for term,nums in matches.items()}}
                    if fp.suffix in (".toml",".ini") or any(y in fp.name.lower() for y in ("cvar","config","settings")):
                        if fp.suffix in (".cpp",".h",".hpp",".toml",".ini",".json"):
                            config_candidates.append({"file":rel,"sha256":sha(fp.read_bytes()),
                                                      "size":fp.stat().st_size})
            r["configuration_and_shader_source_index"]={
              "source_files_inspected":inspected,
              "specific_source_hits":filehits,
              "candidate_config_source_files":config_candidates[:100],
              "files_truncated":len(config_candidates)>100,
              "android_user_toml_read":False,
              "android_user_settings_read":False,
              "device_executed":False
            }
            if not any("kSpecSinDesenfoque" in v["terms"] for v in filehits.values()):
                raise ValueError("PRE679 kSpecSinDesenfoque not found in authenticated source")
            # Logic-only negative checks based on actual source guards;
            # DO NOT imply this executes real C++ or Vulkan.
            cases=[]
            for matching in (False,True):
                for disable_blur in (False,True):
                    for actual_depth_observer in (False,True):
                        guard=matching and disable_blur
                        must_copy=actual_depth_observer or not guard
                        cases.append({"composition_shader_match":matching,
                           "blur_disabled":disable_blur,
                           "real_depth_observer":actual_depth_observer,
                           "source_dead_depth_read_hint":guard,
                           "must_not_suppress_copy":must_copy,
                           "fail_closed_when_observer":must_copy if actual_depth_observer else True})
            if any(x["real_depth_observer"] and not x["must_not_suppress_copy"] for x in cases):
                raise ValueError("PRE679 model allows skipping a copy required by a reader")
            r["blur_depth_host_logic_only"]={
              "positive_cases":len(cases),"all_cases_safe_as_model":True,
              "cases":cases,"tested_actual_cpp":False,"tested_actual_vulkan":False,
              "pixel_equivalence":False}
            r["reliability_conclusion"]={
              "no_cvar_runtime_observation":True,
              "source_default_blur_removal_confirmed":True,
              "fullscreen_effect_restore_would_change_depth_copy_demands":True,
              "actual_device_shader_binary_or_pixels_verified":False,
              "speedbreaker_shadow_lending_approved":False,
              "new_depth_deferral_approved":False,
              "new_apk_or_shader_created":False,
              "next":"PRE680: isolate configuration value in real device/asset or explicit user TOML (read-only), then fidelity test and conditional depth-copy guard before any patch"}
            if (root/RENDER).read_bytes()!=original or (root/BACKEND).read_bytes()!=backend:
                raise ValueError("PRE679 source changed during readonly scan")
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
             "prioritize_next":"Trace queued readback drain and guest-memory writes, transfer fences and depth/stencil semantics before any attempt to defer copies"
            }
        r["status"]="AUDIT_OK_AUTHENTIC_V51_CVAR_BLUR_SPECIALIZATION_SOURCE_ONLY"
    except Exception as exc:
        r["error_type"]=type(exc).__name__
        r["error_summary"]=str(exc)[:300] if isinstance(exc,ValueError) else "Source restore or dependency/API exception"
    finally:
        REPORT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
        lines=[
          "# PRE679 / SB-02 — rastreio dos três caminhos de transferência Vulkan e candidatos de consumidores guest",
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
        lines += ["", "## Tres chamadas de transferencia mapeadas por origem e destino",
          "- Renderer 9770: vkCmdCopyBufferToImage, subida_ -> textura.imagen; nao e leitura guest de sombra.",
          "- Backend 5543: vkCmdCopyImageToBuffer com .png e volcado_indice_; caminho aparente de dump/diagnostico; pode conter depth.",
          "- Backend 5667: vkCmdCopyImageToBuffer com resuelta.imagen, depois lecturas_pendientes_ com rb_copy_dest_base e pitch; candidato a leitura da memoria do jogo.",
          "- Os consumidores, fences e equivalencia temporal permanecem DESCONHECIDOS; nao e seguro adiar qualquer transferencia.",
          "", "## Evidências que ainda faltam",
           "1. Identificar se as cópias encontradas realmente escrevem o mapa de sombras D24S8 e se o guest lê esses bytes na mesma frame.",
           "2. Estabelecer formato, mip, layer, layout, destino físico guest e invalidação/cache antes de adiar qualquer cópia.",
           "3. Avaliar pixel fidelity e consistência de memória guest com resolvers em fixture; rejeitar todos os casos incertos.",
           "4. Medir tempo real por passe com fences/availability no Galaxy S24 FE; contagens lexicais não representam execução.",
           "",
           "Nenhum código SpeedBreaker foi copiado ou integrado. Nenhum APK, shader, timestamp ou build ARM64.",
        ]
        lines += ["","## PRE679 — codigo de adiamento de profundidade ja existente",
             "- Fonte V51 autentica consultada: CopiarProfundidad, pendientes_, AntesDeEscribirProfundidad e caminhos de leitura guest.",
             "- Comentarios de fonte registram que uma troca de imagens de sombra foi DESATIVADA porque o carro ficava sem sombras.",
             "- Preservar a desativacao, e nao importar literalmente a solucao SpeedBreaker sem evidencias G2 e testes de imagens.",
             "- O teste HOST desta etapa e um modelo sintetico de predicados de recusa; nao e equivalente a executar o codigo da V51.",
             "- Nao foi testada GPU real, equivalencia de pixels, memoria guest, travamentos ou ganhos de FPS."]
        if "synthetic_host_guards" in r:
            lines.append("PRE679_HOST_NEGATIVE_TESTS="+str(r["synthetic_host_guards"]["negative_tests"]))
        lines+=["","## PRE679 — achados de declaracoes e maquina de estados",
                 "- Os defaults no codigo sao registrados sem confundir com configuracoes TOML no aparelho.",
                 "- A cadeia AplazarCopiaProfundidad / AntesDeEscribirProfundidad e guardas contra leituras tardias foi inventariada; nao foi executada.",
                 "- A indirecao copiar_imagen_ e rastreada, incluindo atribuicoes, usos e familias de copia.",
                 "- As flags sin_desenfoque e sombras_escala exigem auditoria de fidelidade antes de qualquer otimizacao.",
                 "- Nenhuma equivalencia visual, ganho de FPS ou equivalencia binaria da APK foi demonstrada."]
        if "graphics_cvar_declarations" in r:
            for flag in ("nfsmw_nativo_sin_desenfoque","nfsmw_nativo_sombras_escala","nfsmw_nativo_profundidad_perezosa",
                         "nfsmw_nativo_frontal_perezoso","nfsmw_nativo_sombra_minimo","nfsmw_nativo_restaurar_por_intercambio"):
                lines.append("- "+flag+": "+str([(x["unit"],x["line"],x["source_declared_default"])
                                     for x in r["graphics_cvar_declarations"][flag]]))
        lines+=["","## PRE679 — CVar, TOML e shader specialization",
          "- Confirmado somente por codigo de fonte autenticada: flag default, amostragem por frame e bit de especializacao final.",
          "- O mesmo estado controla o aviso de leitura morta ao subsistema C2 e o bit kSpecSinDesenfoque.",
          "- O scan complementar indexa arquivos fonte de CVar e specialization sem usar configuracoes privadas.",
          "- TOML do Android, shader binario ativo e equiv. de pixels NAO foram observados; nao afirmar blur efetivo na V51 instalada.",
          "- Se blur original estiver ligado, a profundidade da composicao deve continuar disponivel; desabilitar copias cegamente perderia efeitos."]
        if "blur_dataflow" in r:
            for k,v in r["blur_dataflow"].items():
                if isinstance(v,dict) and "line" in v:lines.append(f"- {k}: linha {v['line']} => {v['text'][:140]}")
        if "configuration_and_shader_source_index" in r:
            ix=r["configuration_and_shader_source_index"]
            lines.append(f"- Fonte inspecionada: {ix['source_files_inspected']} arquivos; {len(ix['specific_source_hits'])} arquivos com indices.")
        DOC.write_text("\n".join(lines)+"\n")
        for key in ("status","error_type"):
            print("PRE679_"+key.upper()+"="+str(r.get(key,"none")))
        if r.get("findings"):
            for k in ("shadow_or_depth_token_sites_in_renderer","copy_and_blit_renderer_sites",
                      "copy_and_blit_backend_sites","image_layout_barrier_renderer_sites"):
                print("PRE679_"+k.upper()+"="+str(r["findings"].get(k,0)))
        print("PRE679_SHADOW_LEND_IMPLEMENTED=false")
        print("PRE679_APK_BUILT=false")
        print("PRE679_BLUR_SOURCE_FLOW="+str(bool(r.get("blur_dataflow"))))
        print("PRE679_SOURCE_FILES_INSPECTED="+str(r.get("configuration_and_shader_source_index",{}).get("source_files_inspected",0)))
        print("PRE679_ACTUAL_TOML_VERIFIED=false")
        print("PRE679_ACTUAL_GPU_PIXELS_VERIFIED=false")
        print("PRE679_DECL_BLUR="+str(r.get("graphics_quality_assessment",{}).get("blur_default_as_declared_in_two_inspected_units",[])))
        print("PRE679_DECL_SHADOW_SCALE="+str(r.get("graphics_quality_assessment",{}).get("shadow_resolution_scale_default_from_source",[])))
        print("PRE679_IMAGE_COPY_INDIRECT_SITES="+str(r.get("copy_binding",{}).get("indirect_call_lines",[])))
        print("PRE679_FULL_VISUAL_EQUIVALENCE_PROVEN=false")
        print("PRE679_EXISTING_DEFERRED_DEPTH_FOUND="+str(r.get("depth_interpretation",{}).get("existing_lazy_depth_pipeline_in_V51_source",False)))
        print("PRE679_HOST_NEGATIVE_TESTS="+str(r.get("synthetic_host_guards",{}).get("negative_tests",0)))
        print("PRE679_DEPTH_PIXEL_GUEST_EQUIVALENCE_PROVEN=false")
        print("PRE679_FPS_GAIN_PROVEN=false")
    return 0 if r["status"]=="AUDIT_OK_AUTHENTIC_V51_CVAR_BLUR_SPECIALIZATION_SOURCE_ONLY" else 1
if __name__=="__main__":sys.exit(main())
