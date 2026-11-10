#!/usr/bin/env python3
"""PRE671B backup-first canonical context update only after native ARM64 + host PFN gates.
Fail-closed on stale canonical SHA, mismatched Drive evidence, or non-idempotence.
"""
from __future__ import annotations
import hashlib,io,json,os,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes
ROOT=Path(__file__).resolve().parents[2]
BASE_BYTES=1086089
BASE_SHA="47478c1b3ef460490850ab9867246fa06735e462d61961f07a090ce458bd6184"
NATIVE_DOC=ROOT/"docs/PRE671_V51_NATIVE_VULKAN_ARM64_COMPILE_GATE_VERIFIED.json"
HOST_DOC=ROOT/"docs/PRE671H_V51_VULKAN_PFN_TYPED_HOST_MOCK_VERIFIED.json"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE671B_NATIVE_VULKAN_NOAPK_20261110.md"
TITLE="# PRE671B — adaptador Vulkan ARM64 compilado e testes HOST (2026-11-10)"
OUT=Path("/tmp/nfsmw-pre671b/report.json")
def sha(x):return hashlib.sha256(x).hexdigest()
def checkhex(x):return isinstance(x,str) and re.fullmatch(r"[0-9a-f]{64}",x) is not None
def checked_zip(d,doc):
    if not (
      isinstance(doc.get("drive_zip_id"),str) and
      isinstance(doc.get("zip_bytes"),int) and
      checkhex(doc.get("zip_sha256")) and
      doc.get("zip_crc_pass") is True and
      doc.get("drive_readback_sha_match") is True
    ):raise ValueError("PRE671B pinned ZIP doc incomplete")
    raw=get_bytes(d,doc["drive_zip_id"])
    if len(raw)!=doc["zip_bytes"] or sha(raw)!=doc["zip_sha256"]:
        raise ValueError("PRE671B source artifact differs from Drive pin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:raise ValueError("PRE671B ZIP CRC invalid")
        return {p:z.read(p) for p in z.namelist()}
def validate(d):
    native_doc=json.loads(NATIVE_DOC.read_text())
    host_doc=json.loads(HOST_DOC.read_text())
    if not(
        native_doc.get("github_run_id")==42853007076
        and native_doc.get("status")=="AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL"
        and host_doc.get("github_run_id")==42854074303
        and host_doc.get("status")=="PASS_HOST_VULKAN_DISPATCH_MOCKS_ONLY"
    ):raise ValueError("PRE671B wrong final GitHub run or status pin")
    host_zip=checked_zip(d,host_doc)
    host=json.loads(host_zip["PRE671H_V51_VULKAN_PFN_HOST_MOCK_REPORT.json"])
    if not(
      host.get("status")=="PASS_HOST_VULKAN_DISPATCH_MOCKS_ONLY"
      and host.get("run_id")==42854074303
      and host.get("asan_ubsan_pass") is True
      and host.get("real_gpu_driver_tested") is False
      and host.get("real_VkQueryPool_created") is False
      and host.get("apk_created") is False
      and host.get("multiview_guard_verified") is False
      and host.get("per_tile_execution_guard_verified") is False
    ):raise ValueError("PRE671B host ABI mock evidence mismatched")
    native_zip=checked_zip(d,native_doc)
    result=json.loads(native_zip["PRE671_V51_VULKAN_POOL_ADAPTER_ARM64_NOAPK.json"])
    e=result.get("evidence",{})
    base=result.get("native_production_compile_report",{})
    if not(
      result.get("status")=="AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL"
      and result.get("github_run_id")==42853007076
      and result.get("native_arm64_compiled") is True
      and result.get("query_pool_created") is False
      and result.get("timestamp_queries_recorded") is False
      and result.get("adapter_called_at_runtime") is False
      and result.get("runtime_device_timestamp_capabilities_checked") is False
      and result.get("gpu_time_measured") is False
      and result.get("apk_built") is False
      and result.get("signing_material_accessed") is False
      and result.get("shader_spirv_modified") is False
      and result.get("fps_gain_proven") is False
      and base.get("status")=="AUDIT_OK"
      and base.get("native_build_ok") is True
      and base.get("native_cmake_ok") is True
      and e.get("baseline_renderer_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and e.get("vulkan_adapter_header_sha256")==
        host["source_sha256"]["automation/kaggle/pre671_vk_separate_timestamp_pool_compile_only.h"]
      and e.get("source_reverse_byte_identical") is True
      and e.get("vulkan_declarations_parsed_in_renderer_arm64_TU") is True
      and e.get("adapter_runtime_constructed") is False
      and e.get("runtime_vk_query_pool_created") is False
      and e.get("C2_query_pool_modified") is False
      and e.get("default_enabled") is False
      and e.get("all_existing_native_guard_markers_preserved") is True
      and checkhex(e.get("linked_real_arm64_libmain_sha256"))
      and e.get("linked_real_arm64_libmain_sha256")==result.get("arm64_elf_sha256")
      and isinstance(e.get("linked_real_arm64_libmain_bytes"),int)
      and e["linked_real_arm64_libmain_bytes"] > 50_000_000
    ):raise ValueError("PRE671B native AArch64 / no runtime query gate mismatch")
    return native_doc,host_doc,result
def addition(native_doc,host_doc,result):
    evidence=result["evidence"]
    return (f"""

---

{TITLE}

- PRE671 ARM64 REAL: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42853007076, status conclusivo AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL. Fonte V51 temporaria autenticada (renderer SHA256 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2), stage PRE648, include PRE671 reversivel byte a byte. Header Vulkan native SHA256 {evidence['vulkan_adapter_header_sha256']}; fonte de compilacao SHA256 {evidence['patched_compile_only_renderer_sha256']}. Nenhuma arvore persistente alterada.
- ARM64 libmain.so real: {evidence['linked_real_arm64_libmain_bytes']} bytes, SHA256 {evidence['linked_real_arm64_libmain_sha256']}, ELF AArch64 auditado com os marcadores antigos PRE648, guards C3 PRE635/PRE194 e Nitro PRE398. NAO foi demonstrada equivalencia binaria com a libmain.so assinada na V51. O header foi analisado pelo compilador dentro da unidade de renderizacao, mas NAO chamado nem criado pool real no jogo; nao afirmar que medicao runtime funcionou.
- Adaptador tem PFN tipados VkCreateQueryPool, VkDestroyQueryPool, VkCmdResetQueryPool, VkCmdWriteTimestamp, VkGetQueryPoolResults e VkDeviceWaitIdle, usa pool de timestamp separado, max 4 pares/8 indices por slot, default OFF e requer sinal explicito VK_SUCCESS de fence antes da leitura. O C2 antigo nao foi modificado. No codigo ainda NAO ha chamadas ativas integradas, nem teste no dispositivo.
- PRE671H: teste independente HOST C++17 com ASan/UBSan e callbacks Vulkan MOCKADOS, GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42854074303, PASS_HOST_VULKAN_DISPATCH_MOCKS_ONLY. Testou ABI PFN, rejeicao de fence nao pronta, disponibilidade do resultado, offsets de queries, erros de submissao/leitura e destruicao com espera simulada. Nao criou VkDevice real e nao mediu GPU.
- Evidencias Google Drive: PRE671 ARM64 {native_doc['drive_zip_url']}, {native_doc['zip_bytes']} bytes, SHA256 {native_doc['zip_sha256']}, CRC e readback iguais; PRE671H mocks {host_doc['drive_zip_url']}, {host_doc['zip_bytes']} bytes, SHA256 {host_doc['zip_sha256']}, CRC/readback iguais. Resumos pinados em docs/PRE671_V51_NATIVE_VULKAN_ARM64_COMPILE_GATE_VERIFIED.json e docs/PRE671H_V51_VULKAN_PFN_TYPED_HOST_MOCK_VERIFIED.json.
- LIMITACOES IMPORTANTES: multiview e modo per-tile NAO validados; vkCmdResetQueryPool requer fora de renderpass. Falta verificar timestampValidBits e timestampPeriod reais no Galaxy S24 FE, disponibilidade/suporte das etapas Vulkan, sincronizacao real das fences, impactos da instrumentacao e representatividade estatistica das quatro amostras. Duracoes entre TOP_OF_PIPE e BOTTOM_OF_PIPE nao sao necessariamente custo exclusivo do shader VS62/PS58. NENHUM FPS melhor comprovado.
- PROXIMO PRE672: realizar teste de integracao bloqueada para multiview/per-tile, verificador de capacidade real, leitura com fence VK_SUCCESS e paths de falha; manter default OFF, repetir ARM64 NOAPK com fonte autenticada, depois avaliar experimento no dispositivo sem reduzir qualidade.
- V51 PRE652 segue ultima APK validada: SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, versionCode 51, package io.github.nfsmwrecomp, assinatura permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Sem V52, sem assinatura nova, sem modificacao em saves, shaders SPIR-V, 1920x1080, controles touch/PG-9076, Nitro, BMW, fisica, efeitos ou protecoes termicas; SurfaceFlinger/frame pacing e PRE643 C3 continuam pausados.

Status PRE671B: compilacao ARM64 real do adaptador inativo e testes host Vulkan mock PASS; compatibilidade runtime com Xclipse 940 e ganhos de FPS nao demonstrados.
""").encode("utf-8")
def run():
    d=drive_client()
    native_doc,host_doc,r=validate(d)
    add=addition(native_doc,host_doc,r)
    before=get_bytes(d,FILE_ID); meta=get_meta(d); marker=TITLE.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
       and meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE671B unexpected canonical identity")
    if marker in before:
        if (before.count(marker)!=1 or not before.endswith(add)
            or len(before)-len(add)!=BASE_BYTES or sha(before[:-len(add)])!=BASE_SHA):
            raise ValueError("PRE671B existing update not identical")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "readback_identical":True,"canonical_sha256":sha(before),"canonical_bytes":len(before)}
    if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
        raise ValueError("PRE671B canonical changed, refuse write")
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
        raise ValueError("PRE671B backup mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE671B concurrent canonical update")
    after=before+add
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
    data=get_bytes(d,FILE_ID)
    if data!=after or data.count(marker)!=1 or not data.startswith(before):
        raise ValueError("PRE671B canonical readback mismatch")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
      "canonical_sha256":sha(data),"canonical_bytes":len(data),
      "readback_identical":True,"history_preserved":True}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=run()
    except Exception as e:
        result={"status":"FAILED_CLOSED","error_type":type(e).__name__,
          "error_summary":str(e)[:300] if isinstance(e,ValueError) else "Drive/API/transfer error"}
    result.update({"stage":"PRE671B_CANONICAL_VULKAN_NATIVE_COMPILE_AND_MOCK",
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,
      "user_saves_modified":False})
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE671B_"+key.upper()+"="+str(result.get(key,"none")))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
