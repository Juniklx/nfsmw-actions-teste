#!/usr/bin/env python3
"""PRE668B: verify PRE668 ZIP and append canonical Drive context with backup."""
from __future__ import annotations
import hashlib,io,json,zipfile,sys
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

BASE_BYTES=1076525
BASE_SHA="bb44ac06e477164c16b3a860e506ea09e78ef6a830c664d5da9c3dc37bf7e817"
SOURCE_ID="1AjpdmISLNYQ-pbsL26LhqTto1041pNq7"
SOURCE_LENGTH=44006
SOURCE_SHA="feb982402b62bd7dc77b54fcd26ea18783775cf90c70bbfeeb551828c275a201"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE668B_VULKAN_SOURCE_20261110.md"
HEADING="# PRE668B — auditoria Vulkan PRE668 e limites de integracao (2026-11-10)"
OUTPUT=Path("/tmp/nfsmw-pre668b/report.json")
APPEND="""

---

# PRE668B — auditoria Vulkan PRE668 e limites de integracao (2026-11-10)

- PRE668 fonte autenticada, somente leitura: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42840437196, job 129913900676, artifact 13774704353, sucesso e PRE668_AUTHENTIC_NATIVE_VULKAN_SOURCE_SCOPE_GATE=PASS.
- Reproduziu fonte PRE99 autenticada, replay PRE431/PRE638 e patch exato PRE648 em diretorio temporario. Renderer V51 SHA256 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2; backend Vulkan SHA256 b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385. Equivalencia binaria bit a bit dessa fonte com libmain.so V51 assinada NAO provada.
- Sites exatos: inicio renderpass principal no renderer linha 10153, fim linha 4680; draws reais 3693, 3697, 3782, 3784 (ultimos dois sao o ceu adiado); contadores PRE648 POS-draw 3711 e 3790. O backend C2 possui consulta de timestampValidBits (1037) e timestampPeriod (1038/1046), criacao de query pools, reset de consultas C2 em 4835, escrita de timestamp em 3690/5165, poll de fence em 4927, wait em 4939, submit em 5181. A renderizacao de saida usa outro renderpass nao identico ao da cena.
- A fonte consultar timestampValidBits NAO comprova suporte e medicao real de um NOVO pool separado no Galaxy S24 FE. Ainda nao existe pool extra, validacao runtime para novo pool, garantia de fences para as novas consultas, avaliacao do multiview e etapas de pipeline, teste de overhead, nem tempo GPU exclusivo do par p2 VS62 PS58.
- Artefato verificado no Drive NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE668_V51_RENDERPASS_FENCE_QUERY_REVIEW_42840437196.zip: https://drive.google.com/file/d/1AjpdmISLNYQ-pbsL26LhqTto1041pNq7/view, 44006 bytes, SHA256 feb982402b62bd7dc77b54fcd26ea18783775cf90c70bbfeeb551828c275a201. CRC ZIP aprovado e retorno Drive comparado ao original GitHub; resumo pinado em docs/PRE668_V51_VULKAN_RENDERPASS_AND_QUERY_SCOPE_VERIFIED.json.
- Proxima PRE669: implementar fonte ponte reversivel em arvore TEMPORARIA, desligada por padrao, testar reais compilacao ARM64 e ELF SEM APK e SEM assinatura antes de qualquer experimento de timestamp real em aparelho. Nao mexer no pool C2 nem gerar V52 ate validar resource lifecycle e sobrecarga.
- V51 PRE652 preservada: versionCode 51 no APK validado, pacote io.github.nfsmwrecomp, certificado SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nao alterar 1920x1080, graficos, SPIR-V, efeitos, fisica, controles touch/iPega PG-9076, Nitro PRE398, BMW, C3, saves ou protecoes termicas. Fluidez/SurfaceFlinger e PRE643 ainda suspensos.

Status PRE668B: auditoria source PASS e evidencias arquivadas; nenhuma compilacao ARM64 nova, APK nova, ganho FPS ou tempo GPU individual comprovados.
"""
def sha(x):return hashlib.sha256(x).hexdigest()
def validate_zip(d):
    zbytes=get_bytes(d,SOURCE_ID)
    if len(zbytes)!=SOURCE_LENGTH or sha(zbytes)!=SOURCE_SHA:
        raise ValueError("PRE668B evidence ZIP bytes/SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        if z.testzip() is not None:raise ValueError("PRE668B ZIP CRC failure")
        a=json.loads(z.read("PRE668_V51_RENDERPASS_AND_QUERYPOOL_REVIEW.json"))
    h=a.get("callsite_evidence",{})
    if not(
        a.get("status")=="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY"
        and a.get("authenticated_source",{}).get("renderer_v51_with_pre648_sha256")==
            "9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
        and a.get("authenticated_source",{}).get("backend_v51_sha256")==
            "b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
        and h.get("renderer_open_pass",{}).get("lines")==[10153]
        and h.get("renderer_close_pass",{}).get("lines")==[4680]
        and h.get("backend_vk_timestamp_write",{}).get("lines")==[3690,5165]
        and a.get("vulkan_commands_injected") is False
        and a.get("arm64_compiled") is False
        and a.get("apk_built") is False and a.get("fps_gain_proven") is False):
        raise ValueError("PRE668B source evidence does not pass recorded constraints")
def run():
    d=drive_client()
    validate_zip(d)
    before=get_bytes(d,FILE_ID); meta=get_meta(d)
    m=HEADING.encode("utf-8")
    addition=APPEND.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
         and meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE668B canonical metadata changed")
    if m in before:
        if before.count(m)!=1 or not before.endswith(addition) or sha(before[:-len(addition)])!=BASE_SHA:
            raise ValueError("PRE668B prior edit exists but differs")
        return {"status":"ALREADY_APPLIED_VERIFIED","readback_identical":True,
                "backup_created":False,"canonical_sha256":sha(before)}
    if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
        raise ValueError("PRE668B canonical baseline hash/size changed; refuse overwrite")
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
         body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
        raise ValueError("PRE668B backup failed readback")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE668B concurrent modification")
    after=before+addition
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
    verified=get_bytes(d,FILE_ID)
    if verified!=after or verified.count(m)!=1 or not verified.startswith(before):
        raise ValueError("PRE668B canonical readback mismatch; backup saved")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
       "canonical_sha256":sha(verified),"canonical_bytes":len(verified),
       "readback_identical":True,"previous_history_preserved":True}
def main():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=run()
    except Exception as exc:r={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
      "error_summary":str(exc)[:320] if isinstance(exc,ValueError) else "API/transfer error"}
    r.update({"stage":"PRE668B_V51_QUERY_SCOPE_CANONICAL_CONTEXT",
              "github_run_id":int(__import__("os").environ["GITHUB_RUN_ID"]),
              "utc":datetime.now(timezone.utc).isoformat(),
              "apk_built":False,"signing_material_accessed":False})
    OUTPUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for k in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE668B_"+k.upper()+"="+str(r.get(k,"none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":sys.exit(main())
