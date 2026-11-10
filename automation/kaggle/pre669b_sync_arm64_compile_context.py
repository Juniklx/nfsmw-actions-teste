#!/usr/bin/env python3
"""PRE669B: append verified PRE669 native evidence to canonical Drive context, backup first."""
from __future__ import annotations
import hashlib,io,json,zipfile,os
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes
BASE_BYTES=1079282
BASE_SHA="e884f9b6e74b1b5e3703177e7bcc8b37037d9ab6fa81c01ef792f88ef6121811"
ZIP_ID="1mjtka23ddr35RAJXyENplaFJPcoQL2GU"
ZIP_BYTES=1666
ZIP_SHA="2aaf65a8775d94da7e6659dc1aa889415982e0e74342c657904793e1e1893175"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE669B_ARM64_NOAPK_20261110.md"
TITLE="# PRE669B — compilacao real ARM64 de modelo GPU desativado (2026-11-10)"
OUT=Path("/tmp/nfsmw-pre669b/record.json")
APPEND="""

---

# PRE669B — compilacao real ARM64 de modelo GPU desativado (2026-11-10)

- PRE669 CONCLUIDA: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42842752295 (job 129922006088), completed/success em 2026-11-10 15:39 UTC; PRE669_REAL_ARM64_COMPILE_ONLY_DEFAULT_OFF_NOAPK_GATE=PASS, status AUDIT_OK_ARM64_COMPILE_ONLY_NO_GPU_COMMANDS.
- Fonte real recompilada em arvore temporaria: PRE99 autenticado -> PRE431/PRE638 -> PRE648, renderer V51 SHA256 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2. PRE669 acrescentou apenas include do modelo host PRE666 e dois static_assert, sem invocar o modelo no draw, com default OFF. Fonte resultante SHA256 86aec2f1763968a79f156d0641971a9133bce55d135e3745c0cafc4d1402eb2c, header SHA256 4bcd567d88631a59845913d0ff02d5aa2e12feb0a485cd6781e43f4bd38d2895, reversao byte a byte validada.
- ELF PAL AArch64 libmain.so realmente compilado no runner: 117.842.192 bytes, SHA256 85e269af14f63f1eab7fc3f3637ab111557006dd2c23a60d3ce14e8146c72ab4. Preservados marcadores PRE648, guards C3 PRE635/PRE194 e Nitro PRE398. O ELF novo nao foi comparado bit a bit com o ELF publicado na APK V51.
- Primeira tentativa PRE669, run 42842352309, falhou ANTES da compilacao por preflight que considerou palavra vkCmdDraw em comentario do header como implementacao Vulkan. Corrigido filtro lexical no commit eaadc79ab2579a7db9a9b082e82d95b280930222; segunda tentativa passou.
- Evidencia real no Google Drive: NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE669_V51_ARM64_COMPILE_ONLY_42842752295.zip, https://drive.google.com/file/d/1mjtka23ddr35RAJXyENplaFJPcoQL2GU/view, tamanho 1666 bytes, SHA256 2aaf65a8775d94da7e6659dc1aa889415982e0e74342c657904793e1e1893175; ZIP CRC OK, arquivo lido novamente do Drive identico ao download GitHub, artefato 13778641556. ZIP inclui relatorio, NAO inclui o ELF grande.
- LIMITES: ZERO novas chamadas Vulkan timestamp, ZERO novo pool de consultas, ZERO comprovacao de fence real, ZERO medições reais de tempo GPU por shader VS62/PS58, ZERO teste FPS no Galaxy S24 FE, ZERO APK V52, ZERO acesso a material de assinatura. Compilacao de header em unidade de renderer NAO equivale a integracao runtime.
- Proxima PRE670: auditar e testar isoladamente a criacao/vida de pool Vulkan dedicado, timestamp stages/valid bits, fences por slot, reversibilidade e overhead, inicialmente ARM64 NO APK. Nao habilitar timestamps ou criar release antes de gates.
- Preservar V51 PRE652 (SHA256 APK 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b), package io.github.nfsmwrecomp, versionCode 51 validado na APK, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b, saves, Nitro PRE398, BMW, C3 guards, PG-9076/touch, 1920x1080, efeitos, SPIR-V, fisica e protecoes termicas. Alvo 120 FPS nao significa configuracao atual de 120; fluidez/SurfaceFlinger/PRE643 suspensos.

Status PRE669B: compilacao ARM64 real confirmada, mas nenhuma otimizacao, integracao de GPU timestamps ou ganho FPS comprovado.
"""
def sha(b):return hashlib.sha256(b).hexdigest()
def verify(d):
    payload=get_bytes(d,ZIP_ID)
    if len(payload)!=ZIP_BYTES or sha(payload)!=ZIP_SHA:raise ValueError("PRE669B ZIP sha/size mismatch")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None:raise ValueError("PRE669B ZIP CRC failed")
        x=json.loads(z.read("PRE669_V51_PASS_MODEL_COMPILE_ONLY_ARM64_NOAPK.json"))
    e=x.get("evidence",{})
    native=x.get("native_production_compile_report",{})
    if not(
      x.get("status")=="AUDIT_OK_ARM64_COMPILE_ONLY_NO_GPU_COMMANDS"
      and x.get("github_run_id")==42842752295
      and x.get("native_arm64_compiled") is True
      and e.get("real_arm64_libmain_sha256")=="85e269af14f63f1eab7fc3f3637ab111557006dd2c23a60d3ce14e8146c72ab4"
      and e.get("real_arm64_libmain_bytes")==117842192
      and x.get("arm64_elf_sha256")==e.get("real_arm64_libmain_sha256")
      and e.get("baseline_v51_source_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and e.get("source_reverse_byte_identical") is True
      and e.get("compile_time_default_off") is True
      and e.get("model_header_compiled_in_renderer_unit") is True
      and e.get("vulkan_commands_added") is False
      and e.get("native_runtime_sampler_calls_added") is False
      and x.get("runtime_sampling_enabled") is False
      and x.get("vulkan_query_pool_created") is False
      and x.get("vulkan_commands_injected") is False
      and x.get("actual_gpu_time_measured") is False
      and x.get("apk_built") is False and x.get("signing_material_accessed") is False
      and x.get("fps_gain_proven") is False
      and native.get("status")=="AUDIT_OK" and native.get("native_build_ok") is True
    ):raise ValueError("PRE669B native compile evidence inconsistent")
def run():
    d=drive_client()
    verify(d)
    before=get_bytes(d,FILE_ID); meta=get_meta(d)
    marker=TITLE.encode("utf-8"); addition=APPEND.encode("utf-8")
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md" and
       meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
       raise ValueError("PRE669B canonical metadata mismatch")
    if marker in before:
        if before.count(marker)!=1 or not before.endswith(addition) or len(before)-len(addition)!=BASE_BYTES or sha(before[:-len(addition)])!=BASE_SHA:
            raise ValueError("PRE669B cannot verify prior append")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "readback_identical":True,"canonical_sha256":sha(before)}
    if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
        raise ValueError("PRE669B canonical changed; refuse overwrite")
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},fields="id,name,size").execute()
    if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
        raise ValueError("PRE669B backup readback failed")
    if get_bytes(d,FILE_ID)!=before or get_meta(d).get("modifiedTime")!=meta.get("modifiedTime"):
        raise ValueError("PRE669B concurrent canonical update")
    after=before+addition
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
    readback=get_bytes(d,FILE_ID)
    if readback!=after or not readback.startswith(before) or readback.count(marker)!=1:
        raise ValueError("PRE669B postwrite readback failed; backup preserved")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
      "canonical_sha256":sha(readback),"canonical_bytes":len(readback),
      "readback_identical":True,"history_preserved":True}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=run()
    except Exception as e:r={"status":"FAILED_CLOSED","error_type":type(e).__name__,
       "error_summary":str(e)[:300] if isinstance(e,ValueError) else "Drive/API failure"}
    r.update({"stage":"PRE669B_ARM64_COMPILE_VERIFIED_CANONICAL_CONTEXT",
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
       print("PRE669B_"+key.upper()+"="+str(r.get(key,"none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
