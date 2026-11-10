#!/usr/bin/env python3
"""PRE672B: validate archived host-only fail-closed Vulkan guards before
backup-first append to canonical Drive MD; no APK/keys/saves/code modification.
"""
from __future__ import annotations
import hashlib,io,json,os,zipfile
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes
ROOT=Path(__file__).resolve().parents[2]
BASE_BYTES=1089967
BASE_SHA="3443d2e16c7adedd1eb1e4706d04840159d0e0facae3612a1d78c73810b3f4e6"
ZIP_ID="1ed40JZKb8Y0G9b3tvd95iSPpFSt82hjt"
ZIP_BYTES=1457
ZIP_SHA="7ac972ace1dad98740b909921becc4805a6c0c0a24550cbad4846130e02b7b97"
PIN=ROOT/"docs/PRE672_V51_VULKAN_MULTIVIEW_TILE_FENCE_HOST_GUARD_VERIFIED.json"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE672B_HOST_SAFETY_20261110.md"
TITLE="# PRE672B — bloqueios Vulkan multiview/per-tile e fence (HOST) (2026-11-10)"
OUT=Path("/tmp/nfsmw-pre672b/result.json")
def sha(b):return hashlib.sha256(b).hexdigest()
def addition():
    return ("""

---

# PRE672B — bloqueios Vulkan multiview/per-tile e fence (HOST) (2026-11-10)

- PRE672 HOST APPROVED: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42860554425; status PASS_HOST_VULKAN_CAPABILITY_AND_LIFECYCLE_DENY_BY_DEFAULT, C++17 ASan/UBSan PASS. Mocks sem uso de Vulkan real, sem compilacao ARM64 nesta etapa e sem APK.
- Modelo em automation/kaggle/pre672_gpu_timestamp_capability_failclosed_host.h e teste automation/kaggle/pre672_gpu_timestamp_capability_failclosed_host_test.cpp. Define default OFF e ate quatro pares de timestamps por slot, oito indices por slot. Rejeita status desconhecido ou multiview com viewMask != 0; rejeita status desconhecido ou ativo per-tile; ausencia de PFN, fila grafica, suporte timestampComputeAndGraphics, bits validos (1..64), periodo positivo finito, etapas verificadas, ou quantidade de slots fora de 1..16. Essas informacoes sao ENTRADAS SIMULADAS, nao sondas feitas no Galaxy.
- O modelo exige reset fora de render pass, timestamps apenas dentro do passe correto, bloqueia ceu adiado, pares abertos ao fim de passe/comando, uso de query slot submetido e leitura antes de VkFenceOutcome::Success + todas as disponibilidades. Resultados simulados de fence, query ou submit ERROR desativam o diagnostico. Nenhuma consulta Vulkan real foi gravada. Sem prova de sincronizacao real no driver.
- Primeira tentativa PRE672 https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42860425158 falhou devido a assercao incorreta no PROPRIO TESTE: slot de gravacao com zero pares abertos pode encerrar corretamente. A assercao foi corrigida e o segundo run passou. Nao alterar codigo do renderizador devido a essa falha de teste.
- Evidencia no Drive: NFSMW_PRE672_V51_VULKAN_FAILCLOSED_HOST_42860554425.zip https://drive.google.com/file/d/1ed40JZKb8Y0G9b3tvd95iSPpFSt82hjt/view, 1457 bytes, SHA256 7ac972ace1dad98740b909921becc4805a6c0c0a24550cbad4846130e02b7b97, CRC ZIP e readback validados. Resumo pinado em docs/PRE672_V51_VULKAN_MULTIVIEW_TILE_FENCE_HOST_GUARD_VERIFIED.json.
- LIMITES: model host puro NAO esta integrado ao adapter PRE671 no ELF ARM64 ainda, NAO testou que multiview/per-tile estejam inativos no Galaxy, nao verificou suporte de timestamps nem overhead do driver; nao criou pool nem mediu VS62/PS58 ou FPS. TOP_OF_PIPE a BOTTOM_OF_PIPE nao representa necessariamente custo exclusivo do shader. Sem optimizacao comprovada.
- PROXIMO PRE673: conectar apenas o header de guards na unidade de renderizacao PRE671 de arvore TEMPORARIA, compilar ARM64 NOAPK com default OFF e reversao, checar marcadores anteriores. Nao inserir chamadas de timestamps em renderpass ate passar revisao de uso real e checagem runtime de capacidades.
- Ultima APK assinada continua V51 PRE652 (versionCode 51, io.github.nfsmwrecomp, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b, APK SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b). Preservados Nitro PRE398, C3 PRE194/PRE635, BMW, touch/PG-9076, saves, 1920x1080, shaders SPIR-V, graficos, fisica, efeitos e protecoes termicas; SurfaceFlinger/frame pacing e PRE643 continuam pausados.

Status PRE672B: gate apenas HOST aprovado; nenhuma alteracao da V51, ganho FPS ou medicao GPU real.
""").encode("utf-8")
def verify(d):
    doc=json.loads(PIN.read_text())
    if not(doc.get("github_run_id")==42860554425
       and doc.get("status")=="PASS_HOST_VULKAN_CAPABILITY_AND_LIFECYCLE_DENY_BY_DEFAULT"
       and doc.get("drive_zip_id")==ZIP_ID
       and doc.get("zip_sha256")==ZIP_SHA
       and doc.get("zip_bytes")==ZIP_BYTES
       and doc.get("zip_crc_pass") is True
       and doc.get("drive_readback_sha_match") is True
       and doc.get("limits",{}).get("apk_built") is False
       and doc.get("limits",{}).get("host_only") is True):
        raise ValueError("PRE672B pinned GitHub/Drive gate mismatch")
    raw=get_bytes(d,ZIP_ID)
    if len(raw)!=ZIP_BYTES or sha(raw)!=ZIP_SHA:
        raise ValueError("PRE672B Drive ZIP byte/hash mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:raise ValueError("PRE672B ZIP CRC failure")
        r=json.loads(z.read("PRE672_V51_HOST_GUARD_REPORT.json"))
        log=z.read("host.log")
    labels=r.get("mocked_failclosed_gates",{})
    required=(
      "PRE672_MULTIVIEW_DEFAULT_DENY",
      "PRE672_PER_TILE_UNKNOWN_OR_ENABLED_DENY",
      "PRE672_TIMESTAMP_VALID_BITS_AND_PERIOD_GUARDS",
      "PRE672_RESET_REQUIRES_OUTSIDE_RENDERPASS",
      "PRE672_DEFERRED_SKY_BLOCKED",
      "PRE672_UNBALANCED_TIMESTAMP_PAIR_BLOCKED",
      "PRE672_BOUNDED_QUERY_INDICES",
      "PRE672_FENCE_AND_SUBMIT_ERRORS_FAIL_CLOSED",
      "PRE672_QUERY_AVAILABILITY_REQUIRED",
    )
    if not(
      r.get("status")=="PASS_HOST_VULKAN_CAPABILITY_AND_LIFECYCLE_DENY_BY_DEFAULT"
      and r.get("github_run_id")==42860554425
      and r.get("host_asan_ubsan_pass") is True
      and all(labels.get(k)=="PASS" and (k+"=PASS").encode() in log for k in required)
      and r.get("real_vk_query_pool_created") is False
      and r.get("runtime_query_integration") is False
      and r.get("native_arm64_compiled") is False
      and r.get("apk_built") is False
      and r.get("fps_gain_proven") is False
      and r.get("source_sha256")==doc.get("code_sha256")
    ):raise ValueError("PRE672B host report and mock claims differ")
def run():
    d=drive_client()
    verify(d)
    before=get_bytes(d,FILE_ID)
    meta=get_meta(d)
    appendix=addition()
    marker=TITLE.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
       and meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE672B wrong canonical identity")
    if marker in before:
        if before.count(marker)!=1 or not before.endswith(appendix) or (
          len(before)-len(appendix)!=BASE_BYTES or sha(before[:-len(appendix)])!=BASE_SHA
        ):raise ValueError("PRE672B unexpected previous application")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,"readback_identical":True,
                "canonical_sha256":sha(before),"canonical_bytes":len(before)}
    if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
        raise ValueError("PRE672B stale base: refuse update")
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
        raise ValueError("PRE672B backup readback not identical")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE672B concurrent canonical change")
    after=before+appendix
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
    readback=get_bytes(d,FILE_ID)
    if readback!=after or not readback.startswith(before) or readback.count(marker)!=1:
        raise ValueError("PRE672B postwrite mismatch; original backup available")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
            "canonical_sha256":sha(readback),"canonical_bytes":len(readback),
            "readback_identical":True,"history_preserved":True}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=run()
    except Exception as e:r={"status":"FAILED_CLOSED","error_type":type(e).__name__,
        "error_summary":str(e)[:300] if isinstance(e,ValueError) else "Drive transfer/API failure"}
    r.update({"stage":"PRE672B_VULKAN_HOST_SAFETY_CANONICAL_DRIVE_CONTEXT",
              "run_id":int(os.environ["GITHUB_RUN_ID"]),
              "utc":datetime.now(timezone.utc).isoformat(),
              "apk_built":False,"signing_material_accessed":False,
              "user_saves_modified":False})
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    for k in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE672B_"+k.upper()+"="+str(r.get(k,"none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
