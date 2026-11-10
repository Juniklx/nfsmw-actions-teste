#!/usr/bin/env python3
"""PRE673SB: backup-first append of independent read-only SpeedBreaker study.
Never access signing files, mutate game source, build APK, or copy external code.
"""
from __future__ import annotations
import hashlib,io,json,os
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes
ROOT=Path(__file__).resolve().parents[2]
BASE_BYTES=1093252
BASE_SHA="a2d1f48625349734e6989be7211ab3df29227e4e703b963b816c96622f42d06b"
SOURCE=ROOT/"docs/PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md"
SRC_COMMIT="fe04285d7629377c6e422a6ace8f535368f23c31"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE673SB_SPEEDBREAKER_STUDY_20261110.md"
TITLE="# PRE673SB — estudo comparativo do SpeedBreaker (2026-11-10)"
OUT=Path("/tmp/nfsmw-pre673sb/result.json")
def sha(b):return hashlib.sha256(b).hexdigest()
APPENDIX=f"""

---

{TITLE}

- FONTE DO USUARIO: speedbreaker github.txt aponta https://github.com/SpeedBreakerProject/speedbreaker; foi consultado seu README, CHANGELOG e codigo-fonte publico, branch main commit {SRC_COMMIT} datado 2026-11-07. Projeto externo e distinto do cheat interno chamado Speedbreaker. E tambem recompilacao estatica do Xbox 360 Most Wanted 2005 usando Vulkan/SDL3, mas com runtime proprio. O README atual diz Android COMING SOON; nenhum APK Android pronto dali foi transferido ou executado em nosso S24 FE.
- RELATORIO DETALHADO versionado: docs/PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md, produzido pela leitura de arquivos reais runtime/gpu/renderer.cpp, runtime/gpu/shadow_lend.h, runtime/gpu/shader_translator.cpp, runtime/gpu/command_processor.cpp, runtime/video/presenter.cpp, runtime/video/present_schedule.h, runtime/game/frame_time.cpp e CHANGELOG.md. Esse material externo e somente referencia tecnica; NENHUM codigo de terceiro foi incorporado na nossa V51.
- ALTA RELEVANCIA GPU: em SpeedBreaker, NFSMW_PASS_PROFILE reserva pool Vulkan proprio para timestamps por PASSE, conta desenhos, resolves, uploads, submits, sincronizacao em memoria e intervals entre passes. Esse modelo ajuda nossa PRE673/PRE674 a separar custo da cena do custo de copia/sombra/submit e nao afirmar que muitos draws VS62/PS58 sao shader caro. A rotina externa NAO verifica todos VkResult nem a politica de fence do nosso motor; importacao direta PROIBIDA antes da revisao. A PRE672 local exige caps, multiview/per-tile e disponibilidade.
- CANDIDATA FUTURA DE OTIMIZACAO: shadow_lend.h adia resolves de mapas de sombra de profundidade e permite amostrar imagem preservada quando formato, extent, layout, destino guest e invalidacoes satisfazem criterios estritos, potencialmente reduzindo trafego GPU sem remover efeito. NEED: auditar renderpass, caches, dependencias guest e D24 de nossa V51, calcular economia e comprovar pixels equivalentes por testes A/B. A tecnica de fusao de passes solares e outra candidata, sem omitir qualquer efeito visivel.
- OUTRAS IDEIAS A INVESTIGAR: gerar shader sem caminhos custosos de precision/registradores quando matematica Xbox 360 e pixels permanecem equivalentes (nao presumir ganhos do MoltenVK/AMD no Exynos Xclipse); politica de CPU idle do command processor com esperas finas; apresentar quadros com cadencia de vblank regular e controlar quantizacao dos passos do jogo. SpeedBreaker descreve Smooth Motion de imagens intermediarias, mas mundo fisico continua 60 passos/s e recurso nao foi validado nem disponibilizado para Android. Nao mudar a fisica ou forcar 120 passos/s.
- PRIORIZACAO: 1) concluir PRE673 ARM64 apenas compile-only/default OFF, depois fazer perfilamento por passes e gaps GPU com query/fence propria validada no Android; 2) auditoria read-only de shadow resolves, possivelmente maior economia de largura de banda que otimizar shader cujo custo exclusivo nao foi medido; 3) revisar shaders so com comparacao de SPIR-V e imagem; 4) frame pacing/SurfaceFlinger depois, ainda pausados. Diminuir 1080p, sombras, efeitos, qualidade ou desativar mecanismos termicos NAO e permitido.
- LIMITES/LICENCA: SpeedBreaker tem COPYING GPL-3.0 e arquivos sob GPL-3.0-or-later; quaisquer adaptacoes literais exigem revisao de licenca e avisos. Os codigos de fonte, shaders, saves e APKs do nosso projeto sao distintos. Os relatos externos de desempenho em iPad, Mac, SteamOS ou Linux NAO comprovam FPS no Galaxy S24 FE.
- REFERENCIA DE RELEASE: V51 PRE652 permanece ultima APK assinada versionCode 51, package io.github.nfsmwrecomp, certificado SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b; SEM nova V52, SEM shader/cheat/save/controle/termica alterados nesta auditoria. Nitro PRE398, C3 PRE194/PRE635, BMW e iPega PG-9076/touch preservados.

Status PRE673SB: ESTUDO FONTE EXTERNA READ_ONLY FEITO; beneficios potenciais identificados, nenhum port, otimização ou ganho FPS demonstrado. PRE673 ARM64 deve ser conferida por run conclusivo independente.
""".encode("utf-8")
def run():
  x=SOURCE.read_bytes()
  for t in (b"SpeedBreaker",b"shadow_lend.h",b"PASS_PROFILE",b"frame_time.cpp",
            b"present_schedule.h",b"PRE673",SRC_COMMIT.encode()):
    if t not in x:raise ValueError("PRE673SB source report incomplete")
  d=drive_client()
  before=get_bytes(d,FILE_ID)
  meta=get_meta(d)
  mark=TITLE.encode("utf-8")
  if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
         and meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
    raise ValueError("PRE673SB wrong canonical file/parent")
  if mark in before:
    if before.count(mark)!=1 or not before.endswith(APPENDIX) or (
      len(before)-len(APPENDIX)!=BASE_BYTES or sha(before[:-len(APPENDIX)])!=BASE_SHA
    ):raise ValueError("PRE673SB previously applied but differs")
    return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
            "readback_identical":True,"canonical_sha256":sha(before),
            "canonical_bytes":len(before),"source_report_sha256":sha(x)}
  if len(before)!=BASE_BYTES or sha(before)!=BASE_SHA:
    raise ValueError("PRE673SB canonical SHA changed; no mutation")
  backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
  if int(backup.get("size",0))!=BASE_BYTES or get_bytes(d,backup["id"])!=before:
    raise ValueError("PRE673SB backup readback mismatch")
  if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
    raise ValueError("PRE673SB concurrent context update")
  after=before+APPENDIX
  d.files().update(fileId=FILE_ID,supportsAllDrives=True,
    media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
    fields="id,name,size").execute()
  check=get_bytes(d,FILE_ID)
  if check!=after or not check.startswith(before) or check.count(mark)!=1:
    raise ValueError("PRE673SB canonical postwrite mismatch")
  return {"status":"AUDIT_OK","backup_created":True,"backup_id":backup["id"],
          "readback_identical":True,"canonical_sha256":sha(check),
          "canonical_bytes":len(check),"source_report_sha256":sha(x),
          "history_preserved":True}
def main():
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:r=run()
  except Exception as e:
    r={"status":"FAILED_CLOSED","error_type":type(e).__name__,
       "error_summary":str(e)[:300] if isinstance(e,ValueError) else "Drive API/transfer error"}
  r.update({"stage":"PRE673SB_EXTERNAL_SPEEDBREAKER_READONLY_CANONICAL_CONTEXT",
            "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
            "utc":datetime.now(timezone.utc).isoformat(),
            "apk_built":False,"signing_material_accessed":False,
            "user_saves_modified":False,"third_party_code_incorporated":False})
  OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
  for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
    print("PRE673SB_"+key.upper()+"="+str(r.get(key,"none")))
  return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
