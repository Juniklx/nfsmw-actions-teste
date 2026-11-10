#!/usr/bin/env python3
"""PRE670B: hash/CRC verify host-only GPU query guard, backup and append canonical MD."""
from __future__ import annotations
import hashlib,io,json,os,zipfile
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

BASE_BYTES=1082318
BASE_SHA="25cae4f5cac8960b3c2393efd4d8cbf277da225283e26f16da5b69a1ed92a350"
ZIP_ID="18MOa647PrVIpj6QH1UhFUoI4sLn7Bf5J"
ZIP_BYTES=2272
ZIP_SHA="93de0d4fe092a640436e7ee87613aa6e71faed4f8bde44e5e0bf66e55439ea7b"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE670B_GPU_QUERY_GUARD_20261110.md"
TITLE="# PRE670B — seguranca do pool de timestamps separado (modelo HOST)"
OUT=Path("/tmp/nfsmw-pre670b/result.json")
APPEND="""

---

# PRE670B — seguranca do pool de timestamps separado (modelo HOST) (2026-11-10)

- PRE670 APROVADA pelo GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42848964021 (job 129944031585; artifact 13777629426). Marcadores: PRE670_HOST_RESOURCE_LIFECYCLE_TEST=PASS; PRE670_STATUS=HOST_PASS_CHECKED_FENCE_RESOURCE_GUARDS_ONLY; teste C++17 estrito com sanitizadores ASan/UBSan. Ancoragem PRE665/PRE668 em fonte autentica e PRE669 ARM64 de referencia, SEM recompilar ARM64 nesta etapa.
- Criado MODELO C++17, sem headers de Vulkan, em automation/kaggle/pre670_separate_timestamp_pool_lifecycle_model.h; teste automation/kaggle/pre670_timestamp_lifecycle_host_test.cpp. O codigo proposto e isolado do pool C2 ja usado pelo motor: flag default OFF, ate 4 blocos/8 indices por slot, verificacao simulada de disponibilidade e periodo/valid bits, indices limitados por slot. Sem novo comando Vulkan ou pool real criado.
- O modelo recusa reuso de slot enquanto ha submissao pendente, quando fence retorna NOT_READY ou ERRO, antes de confirmar sucesso de leitura, ou quando informacao externa de conclusao da fence nao e VK_SUCCESS. Erros de submit ou fence desligam o diagnostico. Faz ensaio matematico de wrap de timestamps com valid bits, mas nenhum tempo da GPU Samsung foi medido. ASan/UBSan PASS nao prova seguranca de drivers/Vulkan.
- RISCO REAL confirmado em trechos autenticados PRE668 do backend C2: em CompletarUna, vkWaitForFences na linha 4939 nao testa explicitamente VkResult antes de vkResetFences (4950) e leitura (4956). O diagnostico NOVO nao deve depender implicitamente desse retorno nem alterar/desligar o C2. Necessario integrar tratamento proprio de VK_SUCCESS/VK_NOT_READY/falhas antes de consultar/reutilizar pool. PRE668 encontrou criacao existente do pool C2 (1043), reset (4835), escrita (3690/5165), final de renderpass cena (4680), inicio (10153).
- Vulkan: timestampValidBits e timestampPeriod da fila devem ser conferidos no dispositivo real; os stages e eventual multiview precisam de tratamento. Intervalo entre timestamps nao representa necessariamente custo EXCLUSIVO de VS62 PS58, particularmente em GPU com multiplas etapas/overlap; vies das primeiras quatro amostras nao resolvido.
- Evidencia conferida no Drive: NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE670_V51_GPU_TIMESTAMP_LIFECYCLE_HOST_42848964021.zip, https://drive.google.com/file/d/18MOa647PrVIpj6QH1UhFUoI4sLn7Bf5J/view, 2272 bytes SHA256 93de0d4fe092a640436e7ee87613aa6e71faed4f8bde44e5e0bf66e55439ea7b; CRC ZIP e download/re-download Drive SHA identicos; JSON e log internos, script-fonte persistido no GitHub; resumo docs/PRE670_V51_DEDICATED_TIMESTAMP_HOST_RESOURCE_SAFETY_VERIFIED.json.
- PROXIMA PRE671: antes de criar release, revisar e integrar em arvore TEMPORARIA um adaptador Vulkan INATIVO por padrao, com pool realmente separado e todos caminhos de erro/consulta/fence; compilar ARM64 sem APK e verificar reversao, invariantes e sobrecarga de comandos DESATIVADOS. Somente apos gates pode-se planejar teste com pool ativo e timestamps no Galaxy S24 FE; NAO assumir que novos timestamps medem shader exclusivo.
- Nenhuma APK V52, mudanca de chaves, saves, shaders SPIR-V, fisica, controle, resolucao ou mecanismo termico. Ultima APK assinada permanece V51 PRE652 (SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, versionCode 51 no APK, pacote io.github.nfsmwrecomp; certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b). Prioridade GPU/shaders, com frame pacing/SurfaceFlinger e C3 PRE643 pausados.

Status PRE670B: protecoes de sincronizacao validadas so em MODEL HOST; nenhuma chamada Vulkan nova, nenhuma medicao GPU individual, nenhum teste FPS ou ganho comprovado.
"""
def sha(x):return hashlib.sha256(x).hexdigest()
def validate_zip(d):
    blob=get_bytes(d,ZIP_ID)
    if len(blob)!=ZIP_BYTES or sha(blob)!=ZIP_SHA:
        raise ValueError("PRE670B archive SHA/size changed")
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if archive.testzip() is not None:raise ValueError("PRE670B archive CRC failure")
        report=json.loads(archive.read("PRE670_V51_HOST_RESOURCE_SAFETY_REPORT.json"))
        log=archive.read("host_test.log").decode("utf-8")
    if not (
      report.get("status")=="HOST_PASS_CHECKED_FENCE_RESOURCE_GUARDS_ONLY"
      and report.get("github_run_id")==42848964021
      and report.get("source_gates",{}).get("PRE669_real_ARM64_noAPK_run")==42842752295
      and report.get("default_enabled") is False
      and report.get("max_pairs_per_slot")==4
      and report.get("separate_mock_query_indices_per_slot")==8
      and report.get("C2_existing_timestamp_pool_modified") is False
      and report.get("native_vulkan_pool_created") is False
      and report.get("native_vulkan_calls_injected") is False
      and report.get("runtime_fence_checked") is False
      and report.get("real_gpu_time_measured") is False
      and report.get("real_arm64_compiled_in_this_run") is False
      and report.get("apk_built") is False
      and report.get("fps_gain_proven") is False
      and "PRE670_HOST_RESOURCE_LIFECYCLE_TEST=PASS" in log
      and "PRE670_FENCE_FAILURE_FAIL_CLOSED=true" in log
    ):raise ValueError("PRE670B host-only report gate mismatch")
def run():
    d=drive_client()
    validate_zip(d)
    before=get_bytes(d,FILE_ID); meta=get_meta(d)
    marker=TITLE.encode("utf-8")
    addition=APPEND.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
           and meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE670B unexpected canonical Drive file metadata")
    if marker in before:
        if (before.count(marker)!=1 or not before.endswith(addition)
                or len(before)-len(addition)!=BASE_BYTES
                or sha(before[:-len(addition)])!=BASE_SHA):
            raise ValueError("PRE670B non-identical previous update; refuse overwrite")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
                "readback_identical":True,"canonical_sha256":sha(before),"canonical_bytes":len(before)}
    if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
        raise ValueError("PRE670B unexpected prior context SHA or bytes; refuse overwrite")
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},fields="id,name,size").execute()
    if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
        raise ValueError("PRE670B backup readback mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE670B concurrent canonical modification")
    after=before+addition
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
    readback=get_bytes(d,FILE_ID)
    if readback!=after or not readback.startswith(before) or readback.count(marker)!=1:
        raise ValueError("PRE670B post-write mismatch; backup available")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
      "canonical_sha256":sha(readback),"canonical_bytes":len(readback),
      "readback_identical":True,"history_preserved":True}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:res=run()
    except Exception as exc:
        res={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
          "error_summary":str(exc)[:300] if isinstance(exc,ValueError) else "Drive transfer/API failure"}
    res.update({"stage":"PRE670B_VERIFIED_GPU_RESOURCE_LIFECYCLE_HOST_CANONICAL_CONTEXT",
       "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
       "utc":datetime.now(timezone.utc).isoformat(),"apk_built":False,
       "signing_material_accessed":False,"saves_modified":False})
    OUT.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE670B_"+key.upper()+"="+str(res.get(key,"none")))
    return 0 if res["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
