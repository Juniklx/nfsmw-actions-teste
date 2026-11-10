#!/usr/bin/env python3
"""PRE648: reversible GPU draw accounting only in PRE638 V50 temporary source.
Authenticates prior gates, compiles REAL ARM64 libmain.so, creates NO APK.
Never touches release keys, user saves, Drive sources or installed V50.
"""
from __future__ import annotations
import argparse,hashlib,http.client,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as p638
import pre447_bmw_lookup_route_probe_dryrun as p447
import pre622_bmw_attr_host_value_probe_ram_only as p622

OUT=Path("/tmp/nfsmw-pre648/PRE648_V50_SHADER_COUNTER_ARM64_NOAPK.json")
HEADER=Path("automation/kaggle/pre648_shader_pass_counter.h")
SOURCE=Path("nativo/app/src/nfsmw_nativo_dibujos.cpp")
DEST_HEADER=Path("nativo/app/src/nfsmw_pre648_shader_pass_counter.h")
BASE_SHA=p638.PIN_PRE635
PRE647=Path("docs/PRE647_V50_GPU_SOURCE_ANCHORS_RESULT.json")
EVIDENCE={}
PHASE="START"
COUNTER_METHOD=r"""  // PRE648: emit no messages per draw. One bounded summary every ten seconds.
  void InformeShaderPre648() {
    const auto ahora = std::chrono::steady_clock::now();
    if (siguiente_shader_pre648_ == std::chrono::steady_clock::time_point{}) {
      siguiente_shader_pre648_ = ahora + std::chrono::seconds(10);
      return;
    }
    if (ahora < siguiente_shader_pre648_) return;
    siguiente_shader_pre648_ = ahora + std::chrono::seconds(10);
    const auto resumen = shader_por_pase_pre648_.ExtraerYLimpiar();
    if (!resumen.total && !resumen.fuera_de_rango) return;
    std::string primeros;
    for (const auto& item : resumen.primeros) {
      if (!item.dibujos) break;
      primeros += fmt::format(" [p{} VS{} PS{} n{}]", item.categoria, item.vs_mas_uno,
                             item.ps_mas_uno, item.dibujos);
    }
    NFSMW_INFORME_ANILLO(
        "[nativo] PRE648 GPU_SHADER10s draws={} normal={} deferred_sky={} invalid={} top={}",
        resumen.total, resumen.normales, resumen.cielo_aplazado_emitido,
        resumen.fuera_de_rango, primeros);
  }

"""
PATCHES=[
 (
  '#include "nfsmw_nativo_dibujos.h"\n',
  '#include "nfsmw_nativo_dibujos.h"\n#include "nfsmw_pre648_shader_pass_counter.h"  // PRE648_DIAGNOSTIC_ONLY\n',
 ),
 (
  '    InformeCopias();  // every 10 s, who made the vertex copies and how long the ring waited\n',
  '    InformeCopias();  // every 10 s, who made the vertex copies and how long the ring waited\n'
  '    InformeShaderPre648();  // PRE648: same ring thread, ten-second bounded summaries\n',
 ),
 (
  '      c.ps_mas_uno = ps ? ps->numero + 1 : 0;\n',
  '      c.ps_mas_uno = ps ? ps->numero + 1 : 0;\n'
  '      c.vs_mas_uno = clave.vs;  // PRE648: retain VS for actual deferred Vulkan emission\n',
 ),
 (
  '    ++dibujados_;\n    ++dibujos_en_pase_;  // to know at which position of the pass the sky ends up emitted\n',
  '    ++dibujados_;\n'
  '    shader_por_pase_pre648_.Anotar(clave.vs, clave.ps, CategoriaDeDestino(pitch, claves), false);\n'
  '    ++dibujos_en_pase_;  // to know at which position of the pass the sky ends up emitted\n',
 ),
 (
  '    ++dibujos_en_pase_;\n    // Nothing tracked is valid any more: the dynamic state, the bindings and the index type are the sky\'s.\n',
  '    ++dibujos_en_pase_;\n'
  '    shader_por_pase_pre648_.Anotar(c.vs_mas_uno, c.ps_mas_uno, c.categoria, true);\n'
  '    // Nothing tracked is valid any more: the dynamic state, the bindings and the index type are the sky\'s.\n',
 ),
 (
  '  void InformeSubetapas() {\n',
  COUNTER_METHOD+'  void InformeSubetapas() {\n',
 ),
 (
  '  uint64_t fotograma_ = 0;\n',
  '  uint64_t fotograma_ = 0;\n'
  '  nfsmw::nativo::pre648::ContadorShaderPases shader_por_pase_pre648_{};\n'
  '  std::chrono::steady_clock::time_point siguiente_shader_pre648_{};\n',
 ),
 (
  '    uint32_t ps_mas_uno = 0;           // for the diagnostic per-draw query\n',
  '    uint32_t ps_mas_uno = 0;           // for the diagnostic per-draw query\n'
  '    uint32_t vs_mas_uno = 0;           // PRE648: deferred sky VS, count on emission only\n',
 ),
]
def sha(data):return hashlib.sha256(data).hexdigest()

def patch_bytes(original):
 text=original.decode("utf-8")
 if "PRE648_DIAGNOSTIC_ONLY" in text:
  raise ValueError("PRE648 double application refused")
 reverse=[]
 for old,new in PATCHES:
  if text.count(old)!=1:
   raise ValueError("PRE648 anchor not unique/missing: "+old[:80])
  text=text.replace(old,new,1)
  reverse.append((new,old))
 changed=text.encode("utf-8")
 reverted=text
 for new,old in reversed(reverse):
  if reverted.count(new)!=1:
   raise ValueError("PRE648 reverse anchor not unique")
  reverted=reverted.replace(new,old,1)
 if reverted.encode("utf-8")!=original:
  raise ValueError("PRE648 source not exactly reversible")
 if len(changed)<=len(original):
  raise ValueError("PRE648 diagnostic expected extra instructions")
 if not ("PRE648 GPU_SHADER10s" in text and "c.vs_mas_uno" in text):
  raise ValueError("PRE648 source instrumentation markers missing")
 return changed

def require_gates():
 p638.require_pre637()
 g=json.loads(PRE647.read_text())
 if not (g.get("status")=="AUDIT_OK_SOURCE_RECIPE"
  and g.get("github_run_id")==42762305482
  and g.get("pre99_sha256")==p638.PIN_PRE99
  and g.get("v50_staged_c3_sha256")==BASE_SHA
  and g.get("limits",{}).get("exact_compiled_source_manifest_from_PRE638") is False):
  raise ValueError("PRE648 missing prior PRE647 gate or incorrect provenance caveat")
 files={v["path"]:v for v in g.get("files",[])}
 if files.get(str(SOURCE),{}).get("sha256")!=BASE_SHA:
  raise ValueError("PRE648 previous C3 source fingerprint mismatch")
 if not HEADER.is_file():
  raise ValueError("PRE648 counter header absent")
 return g

def skip_duplicate_menu(r):
 cmake=(r/"nativo/app/CMakeLists.txt").read_text()
 if cmake.count(v46.PRE292_REGISTER)!=1:
  raise ValueError("PRE648 expects already staged PRE292 menu exactly once")
 return {"menu_registered_once":True}

def stage_source(root):
 global PHASE
 PHASE="SOURCE_REPLAY_PRE638"
 previous=p434.ORIGINAL_STAGE
 try:
  p434.ORIGINAL_STAGE=skip_duplicate_menu
  staged=p638.stage_v50(root)
 finally:
  p434.ORIGINAL_STAGE=previous
 if not (staged.get("pre638_v49_source_recipe_verified") is True
  and staged.get("pre638_c3_fallback_bypass") is False
  and staged.get("pre638_v49_callbacks_nitro_preserved") is True
  and staged.get("pre638_save_modified") is False):
  raise ValueError("PRE648 inherited V50 source checks did not pass")
 path=root/SOURCE
 original=path.read_bytes()
 if sha(original)!=BASE_SHA:
  raise ValueError("PRE648 signed V50 replay C3 source SHA mismatch")
 if (root/DEST_HEADER).exists():
  raise ValueError("PRE648 header already exists in replay - refuse double apply")
 header=HEADER.read_bytes()
 if b"class ContadorShaderPases" not in header or b"kMemoriaContadores == 1048576" not in header:
  raise ValueError("PRE648 fixed-bounds counter header invariant missing")
 PHASE="REVERSIBLE_DIAGNOSTIC_PATCH"
 candidate=patch_bytes(original)
 path.write_bytes(candidate)
 (root/DEST_HEADER).write_bytes(header)
 if sha(path.read_bytes())!=sha(candidate) or sha((root/DEST_HEADER).read_bytes())!=sha(header):
  raise ValueError("PRE648 temporary-source writeback mismatch")
 EVIDENCE.update({
  "pre638_original_source_sha256":sha(original),
  "pre648_diagnostic_source_sha256":sha(candidate),
  "pre648_counter_header_sha256":sha(header),
  "pre648_source_exact_reverse_verified":True,
  "pre648_original_source_pinned":True,
  "pre648_only_temporary_tree_modified":True,
  "pre648_no_shader_spirv_edits":True,
  "pre648_skies_counted_only_when_emitted":True,
  "pre648_depth_only_ps_zero_retained":True,
  "pre648_counter_fixed_size_bytes":1048576,
  "pre648_gpu_timing_measured":False,
  "pre648_fps_gain_proven":False})
 PHASE="NATIVE_COMPILE_READY"
 return {**staged,"pre648_pre638_replay_verified":True}

def verify_elf(build, original_find):
 global PHASE
 PHASE="VERIFY_REAL_ARM64_ELF"
 binaries=original_find(build)
 if len(binaries)!=1 or not native.arm64_elf(binaries[0]):
  raise ValueError("PRE648 expected one real PAL ARM64 libmain ELF")
 lib=binaries[0].read_bytes()
 for marker in (b"PRE648 GPU_SHADER10s",b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
   b"NFSMW_PRE194_C3",b"NFSMW_PRE398_GLOBAL_NITRO_FULL"):
  if marker not in lib:
   raise ValueError("PRE648 linked ELF lacks diagnostic or legacy guard marker")
 EVIDENCE.update({"real_arm64_libmain_sha256":sha(lib),"real_arm64_libmain_bytes":len(lib),
  "pre648_marker_linked_in_real_arm64_elf":True,
  "pre635_c3_guard_preserved_in_arm64_elf":True,
  "pre398_nitro_preserved_in_arm64_elf":True})
 PHASE="ARM64_LINK_AND_COUNTER_GATE_PASS"
 return binaries

def audit(run_id):
 global PHASE
 require_gates()
 old=(native.replay_v37,native.stage_logger,native.find_outputs,
      native.FEATURE,native.CALLBACK,native.PAL_FILENAME,native.download)
 original_find=native.find_outputs
 original_download=native.download
 def download_with_retries(client,destination):
  for attempt in range(3):
   try:
    destination.unlink(missing_ok=True)
    return original_download(client,destination)
   except (http.client.IncompleteRead,ConnectionError,TimeoutError,OSError) as exc:
    destination.unlink(missing_ok=True)
    EVIDENCE["pre99_transfer_transient_retries"]=attempt+1
    print("PRE648_PRE99_TRANSFER_RETRY="+str(attempt+1)+" CAUSE="+type(exc).__name__)
    if attempt==2:raise
 try:
  native.download=download_with_retries
  native.replay_v37=v46.replay_v46_sources
  native.stage_logger=stage_source
  native.find_outputs=lambda build:verify_elf(build,original_find)
  native.FEATURE=p447.FLAG
  native.CALLBACK=p622.SYMBOL
  native.PAL_FILENAME=p447.FILES["lookup"][0]
  PHASE="PRE99_NATIVE_REBUILD"
  compiled=native.audit(Path(__file__).resolve().parents[2])
 finally:
  (native.replay_v37,native.stage_logger,native.find_outputs,
   native.FEATURE,native.CALLBACK,native.PAL_FILENAME,native.download)=old
 okay=(compiled.get("status")=="AUDIT_OK"
  and compiled.get("cmake_configure",{}).get("ok") is True
  and compiled.get("production_native_build",{}).get("ok") is True
  and compiled.get("linked_library",{}).get("arm64_elf") is True
  and EVIDENCE.get("pre648_marker_linked_in_real_arm64_elf") is True
  and EVIDENCE.get("pre648_source_exact_reverse_verified") is True)
 return {"stage":"PRE648_V50_SHADER_PASS_DRAW_COUNTER_ARM64_NOAPK",
  "status":"AUDIT_OK" if okay else "NOT_APPROVED","run_id":run_id,
  "phase":PHASE,"pre99_sha256":compiled.get("backup_sha256"),
  "native_build_ok":compiled.get("production_native_build",{}).get("ok"),
  "native_cmake_ok":compiled.get("cmake_configure",{}).get("ok"),
  "linked_library_sha256":compiled.get("linked_library",{}).get("sha256"),
  "evidence":EVIDENCE,
  "signed_v50_elf_source_equivalence_verified":False,
  "apk_created":False,"signed":False,"signing_accessed":False,
  "user_saves_modified":False,"shaders_modified":False,
  "runtime_counter_logs_obtained":False,"gpu_time_per_shader_measured":False,
  "fps_gain_proven":False,
  "next_gate":"PRE649 verify counter overhead and source-based native fallback safety; only then consider signed V51 diagnostics"}

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--run-id",required=True)
 args=parser.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:
  if not args.run_id.isdecimal():raise ValueError("Workflow run ID must be numeric")
  result=audit(args.run_id)
 except Exception as e:
  result={"stage":"PRE648_V50_SHADER_PASS_DRAW_COUNTER_ARM64_NOAPK",
   "status":"FAILED","phase":PHASE,"error_type":type(e).__name__,
   "error_summary":str(e)[:260] if isinstance(e,ValueError) else "native gate exception",
   "apk_created":False,"signed":False,"signing_accessed":False}
 result["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 for label,value in (
  ("STATUS",result["status"]),("PHASE",result.get("phase","unknown")),
  ("NATIVE_BUILD_OK",result.get("native_build_ok",False)),
  ("ARM64_COUNTER_LINKED",result.get("evidence",{}).get("pre648_marker_linked_in_real_arm64_elf",False)),
  ("SOURCE_REVERSE",result.get("evidence",{}).get("pre648_source_exact_reverse_verified",False)),
  ("APK_CREATED",False),("SIGNING_ACCESSED",False),
  ("ERROR_TYPE",result.get("error_type","none"))):
  print("PRE648_"+label+"="+str(value))
 return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
 sys.exit(main())
