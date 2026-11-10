#!/usr/bin/env python3
"""PRE674B: backup-first append of the adopted SpeedBreaker workflow into
canonical NFSMW Drive context. Never touch APK, signing keys or source trees.
"""
from __future__ import annotations
import hashlib,io,json,os
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

ROOT=Path(__file__).resolve().parents[2]
FLOW=ROOT/"docs/FLUXO_SPEEDBREAKER_NFSMW_ANDROID.md"
BACKLOG=ROOT/"docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json"
STUDY=ROOT/"docs/PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md"
OUT=Path("/tmp/nfsmw-pre674b/result.json")
BASE_BYTES=1097375
BASE_SHA="3300c76f7204a89abf767b29d5d73cec9e1f287c6a293b7aaa96e03b9f6fd746"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE674B_WORKFLOW_SPEEDBREAKER_20261110.md"
HEADING="# PRE674B — incorporacao das ideias SpeedBreaker no fluxo (2026-11-10)"
REPORT_TITLE="NFSMW_PRE674B_SPEEDBREAKER_WORKFLOW_CONTEXT_"
def sha(data):return hashlib.sha256(data).hexdigest()
def preflight():
    f=FLOW.read_bytes()
    b=BACKLOG.read_bytes()
    study=STUDY.read_bytes()
    policy=json.loads(b)
    if not (
      policy.get("schema")=="nfsmw-speedbreaker-backlog-v1"
      and policy.get("upstream",{}).get("commit")=="fe04285d7629377c6e422a6ace8f535368f23c31"
      and policy.get("upstream",{}).get("automatic_upstream_code_import") is False
      and policy.get("internal",{}).get("version_code")==51
      and policy.get("policy",{}).get("automatic_release") is False
      and len(policy.get("candidates",[]))==7
      and b"PRE673 ARM64 compile-only aprovados" in f
      and b"GPL" in f
      and b"PASS_PROFILE" in study
      and b"shadow_lend.h" in study
    ):raise ValueError("PRE674B backlog, source review or safety anchors do not match")
    return {"flow_sha256":sha(f),"backlog_sha256":sha(b),"study_sha256":sha(study)}
APPEND=f"""

---

{HEADING}

- PEDIDO DO USUARIO: incorporar tecnicas e ideias verificadas do repositorio publico SpeedBreakerProject/speedbreaker ao fluxo do NFSMW-Recompiled-Mobile Android, mas como **propostas com gates**; nao importar um motor de outro projeto automaticamente.
- ARQUIVOS NOVOS GITHUB: docs/FLUXO_SPEEDBREAKER_NFSMW_ANDROID.md (metodo de G0 a G7), docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json (7 candidatos SB-01..SB-07), automation/kaggle/pre674_speedbreaker_workflow_policy_gate.py (valida esquema e regras, testa 11 cenarios negativos), .github/workflows/nfsmw-pre674-speedbreaker-ideas-policy.yml (gate somente Python, sem toolchain/segredos/APK); auditoria de origem anterior em docs/PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md.
- EVIDENCIA PRE674 DE FLUXO: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42866684780 completed/success em 2026-11-10, depois de atualizacao do roteiro para refletir PRE673. Execucao inicial PRE674 https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42866402690 tambem completou success, com PRE674_STATUS=PASS_BACKLOG_POLICY_AND_11_NEGATIVE_CASES, PRE674_NEGATIVE_CASES_PASSED=11. Essas verificacoes validam POLITICA de CI e backlog; nao validam semantica de Vulkan/GPU ou desempenho do jogo.
- PRE673 COMPLETO: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42863564617, job 129995803230, artifact 13786633724, status success e PRE673_STATUS=PASS_REAL_ARM64_ADAPTER_AND_CAPABILITY_GUARD_COMPILE_ONLY_NOAPK. Compilacao ARM64 real em replay V51 da unidade de renderer com adaptador de pool Vulkan PRE671 + protecoes de capacidades/fences PRE672, inativos DEFAULT OFF. Nenhum pool VkQueryPool novo criado, nenhuma escrita de timestamp nova, nenhuma medicao GPU/VS62/PS58, nenhuma APK, nenhum incremento de versionCode, nenhum ganho FPS comprovado. Primeira tentativa PRE673 42862951880 falhou ANTES da compilacao por assert lexical impróprio para header HOST; retry corrigiu e confirmou.
- ORDEM DE INVESTIGACAO ADOTADA: SB-01 P0 timestamps por passe de cena + gaps entre passes Vulkan para separar custo de draws VS62/PS58, resolves/uploads/submits; SB-02 P1 leitura apenas da estrutura de shadow resolves e futura estrategia de resolve adiado com equivalencia de pixels, textura e memoria guest; SB-03 P2 combinacao de passes de sol/halo somente se equivalentes; SB-04 P2 compilacao/registradores/precisao de shaders com teste real no Xclipse 940; SB-05 P3 command processor idle e SB-06 P3 frame pacing/vblank continuam PAUSADOS; SB-07 Smooth Motion nao portada para Android (nao acelera passos de fisica).
- GATES PROXIMOS: G0 commit externo pinado e licenca; G1 mapeamento fonte autenticada read-only; G2 HOST sanitizers e casos negativos; G3 compilacao NDK AArch64 sem APK; G4 capacidade Vulkan REAL e instrumentos default OFF no S24 FE; G5 A/B/A mesma cena do carro parado, 1080p, imagens/pixels equivalentes, input, temperatura/clocks e p50/p95/p99 de frametimes; G6 release somente autorizada com mesmo certificado e versionCode crescente; G7 backup e readback do contexto do Drive. Nenhum cherry-pick externo automatico.
- LIMITES DE ENGENHARIA: dados de GPU por pass ou tempo entre TOP/BOTTOM nao implicam tempo exclusivo do shader; numero de draws isolado nao implica custo GPU. PRE672 bloqueia multiview/per-tile/status desconhecidos, exige fence real, availability e VkResult; ainda nao foram testados no GPU Samsung. Code SpeedBreaker GPL-3.0-or-later, exige revisao legal se copia literal. Relatos de Mac/iPad/SteamOS nao sao benchmark Android.
- RELEASE PRESERVADA: V51 PRE652 versionCode 51, package io.github.nfsmwrecomp, APK SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Sem V52. Preservados Nitro PRE398, BMW, C3 PRE194/PRE635, saves, controles touch/iPega PG-9076, shaders, sombras, 1920x1080, fisica, efeitos e thermal. SurfaceFlinger/frame pacing e PRE643 seguem pausados.

Status PRE674B: adocao de ideias no FLUXO e gates do repositorio COMPROVADA, GPU real e ganho FPS NAO comprovados. Proximo passo tecnico isolado: auditoria de dependencias de shadow/depth resolves da fonte V51 e probe read-only de suporte a timestamp GPU Android, sem patch de shader ou APK nova.
""".encode("utf-8")
def operation():
  evidence=preflight()
  d=drive_client()
  before=get_bytes(d,FILE_ID)
  meta=get_meta(d)
  mark=HEADING.encode("utf-8")
  if meta.get("id")!=FILE_ID or meta.get("name")!="CONTEXTO_NFSMW.md" or meta.get("parents")!=[PARENT] or int(meta.get("size",0))!=len(before):
    raise ValueError("wrong Drive canonical file identity")
  if mark in before:
    if before.count(mark)!=1 or not before.endswith(APPEND) or len(before)-len(APPEND)!=BASE_BYTES or sha(before[:-len(APPEND)])!=BASE_SHA:
      raise ValueError("existing PRE674B append differs from the pin")
    return dict(status="ALREADY_APPLIED_VERIFIED",backup_created=False,canonical_sha256=sha(before),canonical_bytes=len(before),readback_identical=True,**evidence)
  if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:raise ValueError("context SHA changed since PRE673SB; failed closed")
  backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},fields="id,name,size").execute()
  if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:raise ValueError("PRE674B backup readback mismatch")
  if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:raise ValueError("PRE674B concurrent edit")
  final=before+APPEND
  d.files().update(fileId=FILE_ID,supportsAllDrives=True,
      media_body=MediaIoBaseUpload(io.BytesIO(final),mimetype="text/markdown",resumable=False),
      fields="id,name,size").execute()
  got=get_bytes(d,FILE_ID)
  if got!=final or not got.startswith(before) or got.count(mark)!=1:raise ValueError("PRE674B canonical readback is not identical")
  return dict(status="AUDIT_OK",backup_created=True,backup_id=backup["id"],canonical_sha256=sha(got),canonical_bytes=len(got),readback_identical=True,history_preserved=True,**evidence)
def main():
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:result=operation()
  except Exception as exc:
    result={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
            "error_summary":str(exc)[:350] if isinstance(exc,ValueError) else "Drive API or network error"}
  result.update(stage="PRE674B_ADOPT_SPEEDBREAKER_WORKFLOW_CANONICAL_CONTEXT",
      github_run_id=int(os.environ["GITHUB_RUN_ID"]),utc=datetime.now(timezone.utc).isoformat(),
      apk_built=False,signing_material_accessed=False,external_code_imported=False,
      gpu_timestamp_measured=False,fps_gain_proven=False)
  OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
  for k in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
    print("PRE674B_"+k.upper()+"="+str(result.get(k,"none")))
  return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
