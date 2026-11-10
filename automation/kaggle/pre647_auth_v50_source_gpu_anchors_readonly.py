#!/usr/bin/env python3
"""PRE647 reconstructs V50 source recipe in disposable tree and audits Vulkan GPU hooks; no APK."""
import hashlib,json,re,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as p638

OUT=Path("/tmp/nfsmw-pre647")
ANCHORS={
"nativo/app/src/nfsmw_nativo_dibujos.cpp":{
 "draw_entry":r"\bbool\s+Dibujar\s*\(\s*const\s+PeticionDibujo",
 "pipeline_key":r"\bstruct\s+ClavePipeline\s*\{",
 "vs_number":r"clave\.vs\s*=\s*p\.vs->numero\s*\+\s*1",
 "ps_number":r"clave\.ps\s*=\s*ps\s*\?\s*ps->numero\s*\+\s*1",
 "pipeline_lookup":r"\bVkPipeline\s+PipelineDe\s*\(",
 "pipeline_create":r"\bVkResult\s+CrearPipelineVulkan\s*\(",
 "vk_create":r"\bvkCreateGraphicsPipelines\s*\(",
 "draw_indexed":r"\bvkCmdDrawIndexed\s*\(",
 "draw_direct":r"\bvkCmdDraw\s*\(",
 "pass_category":r"categoria_pase_\s*=\s*CategoriaDeDestino\s*\(",
 "gpu_pass_marker":r"contexto_->MarcarGpu\s*\(\s*categoria_pase_\s*\)",
 "alpha_variant":r"\bModuloSoloAlfa\s*\(",
 "early_z_variant":r"\bModuloZTemprana\s*\(",
 "sky_deferred":r"\bvoid\s+EmitirCieloAplazado\s*\(",
 "c3_guard_trace":r"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
},
"nativo/app/src/nfsmw_nativo_shaders.cpp":{
 "entry":r"\bEntradaShader\b",
 "index_lookup":r"\bShadersNativos::PorNumero\s*\(",
 "identify":r"\bShadersNativos::Identificar\s*\("
},
"nativo/app/src/nfsmw_shader_library.cpp":{
 "container_magic":r"kFirma\s*\{",
 "integrity_hash":r"XXH3_64bits\s*\("
}}
def sha(x):return hashlib.sha256(x).hexdigest()
def audit():
 OUT.mkdir(parents=True,exist_ok=True)
 doc={"stage":"PRE647_V50_SOURCE_GPU_ANCHORS_READONLY","status":"FAIL_CLOSED",
 "utc":datetime.now(timezone.utc).isoformat(),
 "signed_v50_apk_sha256":"7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe",
 "pre99_verified":False,"pre638_v50_source_recipe_replayed":False,
 "exact_signed_v50_elf_source_provenance":False,"binary_equivalence_verified":False,
 "runtime_shader_draw_frequency_measured":False,"runtime_shader_gpu_time_measured":False,
 "drive_source_modified":False,"shaders_modified":False,"apk_built":False,
 "signing_material_accessed":False,"user_saves_accessed":False}
 try:
  p638.require_pre637()
  with tempfile.TemporaryDirectory(prefix="pre647_v50_") as td:
   folder=Path(td);archive=folder/"pre99.tar.gz"
   download(drive_client(),archive)
   digest,_,size=sha_file(archive)
   doc["pre99_sha256"]=digest;doc["pre99_bytes"]=size
   if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
    raise ValueError("PRE99 source SHA or size mismatch")
   doc["pre99_verified"]=True
   dest=folder/"restored";dest.mkdir()
   restore(archive,dest);archive.unlink(missing_ok=True)
   root=dest/"workspace"
   stages=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
   if stages["PRE398"].get("cheat_enabled") is not True:
    raise ValueError("PRE398 Nitro missing after source replay")
   previous=p434.ORIGINAL_STAGE
   def already_staged_menu(r):
    cmake=(r/"nativo/app/CMakeLists.txt").read_text()
    if cmake.count(v46.PRE292_REGISTER)!=1:
     raise ValueError("PRE292 menu registration count mismatch")
    return {"menu_registered_once":True}
   try:
    p434.ORIGINAL_STAGE=already_staged_menu
    staged=p638.stage_v50(root)
   finally:
    p434.ORIGINAL_STAGE=previous
   if not (staged.get("pre638_v49_source_recipe_verified") is True
    and staged.get("pre638_c3_two_request_patch_sha256")==p638.PIN_PRE635
    and staged.get("pre638_c3_fallback_bypass") is False
    and staged.get("pre638_v49_callbacks_nitro_preserved") is True
    and staged.get("pre638_save_modified") is False):
    raise ValueError("Signed V50 exact stage recipe gate failed")
   path=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
   if sha(path.read_bytes())!=p638.PIN_PRE635:
    raise ValueError("V50 C3 staged SHA differs from published V50 build gate")
   doc["pre638_v50_source_recipe_replayed"]=True
   doc["v50_c3_source_sha256"]=p638.PIN_PRE635
   details={};missing=[]
   for rel,anchors in ANCHORS.items():
    data=(root/rel).read_bytes()
    txt=data.decode("utf-8")
    found={}
    for key,pattern in anchors.items():
     lines=[txt.count("\n",0,m.start())+1 for m in re.finditer(pattern,txt,re.MULTILINE)]
     found[key]={"count":len(lines),"lines":lines[:12]}
     if not lines:missing.append(rel+":"+key)
    details[rel]={"bytes":len(data),"sha256":sha(data),"anchors":found}
   doc["gpu_files"]=details
   if missing:raise ValueError("GPU hook anchors missing: "+",".join(missing)[:250])
   doc["status"]="AUDIT_OK_SOURCE_RECIPE"
   doc["next_gate"]="PRE648 draft aggregate VS/PS/pass draw counters in disposable source; host mock and ARM64 no-APK gate before device build"
 except Exception as e:
  doc["error_type"]=type(e).__name__
  doc["error_summary"]=str(e)[:280] if isinstance(e,ValueError) else "error without sensitive details"
 finally:
  (OUT/"PRE647_V50_GPU_SOURCE_REPLAY.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
  summary=["# PRE647 - V50 source recipe + GPU pipeline source audit","",
  "Gate: "+doc["status"],"",
  "The source is reconstructed from pinned PRE99 through the actual V46 and PRE638 V50 staging function.",
  "This validates the replayed source recipe; it does NOT prove bit-for-bit equivalence with the previously signed APK V50 ELF.",
  "The report includes file SHA256, byte sizes, and source anchor line numbers, without including full source archives or user logs.",
  "",
  "## PRE648 proposed measurement (not implemented in PRE647)","",
  "Aggregate draw counts per shader ID and target category in Dibujar after successful submission; distinguish the deferred sky from normal draws and avoid double counting. Consider both VS and PS including depth-only pass without PS.",
  "Do not log per draw; use bounded memory and periodic summarized output only.",
  "C2 GPU time is per pass; draw counts alone cannot measure the GPU time of an individual SPIR-V module.",
  "First validate behavior against identical draw streams and compile a real ARM64 native library without creating an APK. Then evaluate instrumentation cost before attempting optimization.",
  "Keep 1920x1080 visuals, physics, PG9076/touch, Nitro, BMW, safeguards PRE194/PRE635, app saves, Android permanent certificate and thermal limits untouched.",
  "",
  "No patch, no APK, no signing, no device test and no proven FPS gain in this stage."]
  (OUT/"RELATORIO_PRE647_V50_GPU_SOURCE_READONLY.md").write_text("\n".join(summary)+"\n")
  for key in ("status","pre99_verified","pre638_v50_source_recipe_replayed"):
   print("PRE647_"+key.upper()+"="+str(doc[key]))
  print("PRE647_GPU_FILES="+str(len(doc.get("gpu_files",{}))))
  print("PRE647_BINARY_EQUIVALENCE=false")
  print("PRE647_APK_BUILT=false")
  print("PRE647_SIGNING_MATERIAL_ACCESSED=false")
  print("PRE647_ERROR_TYPE="+str(doc.get("error_type","none")))
 return 0 if doc["status"]=="AUDIT_OK_SOURCE_RECIPE" else 1
if __name__=="__main__":
 sys.exit(audit())
