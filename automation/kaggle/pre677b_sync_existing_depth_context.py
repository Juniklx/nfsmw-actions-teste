#!/usr/bin/env python3
"""PRE677B: backup-first, idempotent canonical context append of verified
PRE677 SB-02 V51 existing lazy depth and shadow source audit. Never build APK or alter secrets.
"""
from __future__ import annotations
import hashlib,io,json,os
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/"docs/PRE677_SB02_V51_EXISTING_DEPTH_VERIFIED.json"
POLICY=ROOT/"docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json"
OUT=Path("/tmp/nfsmw-pre677b/result.json")
BEFORE_BYTES=1109220
BEFORE_SHA="a4c4594bcea31c6ef0f412afa5192d6379caa3039c08905c5e54ec796a5decc1"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE677B_SB02_DEPTH_GUARDS_20261110.md"
HEADING="# PRE677B — depth perezosa V51, sombra minimo e guardas SpeedBreaker SB-02 (2026-11-10)"
def sha(data):return hashlib.sha256(data).hexdigest()
def checked():
    x=json.loads(PIN.read_text())
    b=json.loads(POLICY.read_text())
    c=x.get("default_cvars_as_defined_in_backend_source",{})
    if not (
      x.get("schema")=="nfsmw-pre677-sb02-depth-trace-v1"
      and x.get("status")=="AUDIT_OK_AUTHENTIC_V51_EXISTING_DEFERRED_DEPTH_SOURCE_TRACE_ONLY"
      and x.get("github",{}).get("run_id")==42874003191
      and x.get("drive",{}).get("sha256")=="9fc48095000cb6f58f13695b4260c3b36e01612726e40c8836aa07cc7430280d"
      and x.get("drive",{}).get("size_bytes")==184147
      and x.get("drive",{}).get("crc_ok") is True
      and x.get("drive",{}).get("readback_identical") is True
      and x.get("source",{}).get("renderer_v51_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and x.get("source",{}).get("backend_v51_sha256")=="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
      and c.get("nfsmw_nativo_profundidad_perezosa",{}).get("default") is True
      and c.get("nfsmw_nativo_frontal_perezoso",{}).get("default") is True
      and c.get("nfsmw_nativo_sombra_minimo",{}).get("default") is True
      and c.get("nfsmw_nativo_restaurar_por_intercambio",{}).get("default") is False
      and x.get("synthetic_guards",{}).get("negative_test_cases")==24
      and x.get("synthetic_guards",{}).get("actual_v51_state_machine_tested") is False
      and x.get("safety",{}).get("no_apk") is True
      and b.get("internal",{}).get("version_code")==51
      and b.get("candidates",[{},{}])[1].get("id")=="SB-02"
    ):raise ValueError("PRE677B source evidence, gate or V51 identity mismatch")
    return {"pre677_verified_pin_sha256":sha(PIN.read_bytes()),
            "speedbreaker_backlog_sha256":sha(POLICY.read_bytes())}
TEXT=f"""

---

{HEADING}

- PRE677 SB-02 FONTE V51 **AUDIT_OK**: run GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42874003191, job 130032365729, artifact 13789888733, status completed/success. Script automation/kaggle/pre677_sb02_v51_existing_deferred_depth_readonly.py; replay PRE99 + PRE431 + PRE638 + PRE648 somente fonte TEMP autenticada. Renderer SHA256 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2 e backend b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385. Nao implica ELF de V51 assinado byte-identico.
- PONTO IMPORTANTE: o backend V51 JA TEM adiamento de copias de profundidade. CVar nfsmw_nativo_profundidad_perezosa (linha 318) foi declarada true POR PADRAO, com mecanismos CopiarProfundidad (referencias 1420,1727,3935,4007,4413), AntesDeEscribirProfundidad (304,317,1682,2925,3333,4140,4195) e estrutura pendientes_ (73 ocorrencias textuais no backend). O codigo fonte descreve flush antes de amostrar, evitar copia quando origem sera reescrita, e desativar mecanismo ao detectar DIFERENCIA; sao descricoes no fonte, nao equivalencia independente de pixels.
- OUTRAS CONFIGURACOES JA EXISTENTES: nfsmw_nativo_frontal_perezoso (linha 350) true por padrao; nfsmw_nativo_sombra_minimo (linha 390) true por padrao, usando relacao min de mapas mundo+carros e shader adequado segundo comentario; o ganho real no Galaxy nao foi aferido nesta etapa. nfsmw_nativo_restaurar_por_intercambio (linha 283) false por padrao, com aviso EXPLICITO no proprio fonte: se ligada, uma textura do mapa de sombras permanece emprestada e o carro deixa de receber sombras. NAO reativar sem prova de equivalencia rigorosa.
- RETIFICACAO PRE675: busca por chamadas vkCmd* diretas das duas unidades deixou de fora chamadas indiretas ao ponteiro copiar_imagen_ na origem de profundidade (linhas 1834 e 1888, subresources VK_IMAGE_ASPECT_DEPTH_BIT nas linhas 1828,1830,1875,1877). As 3 chamadas diretas catalogadas PRE675/PRE676 NAO eram um inventario exaustivo de copias de profundidade. Seguir binding de copiar_imagen_ e guarda em PRE678.
- QUESTAO DE FIDELIDADE: comentario da fonte V51 em linhas 291-295 atribui ausencia da leitura de HEIGHTMAP/radial blur a nfsmw_nativo_sin_desenfoque "true by default"; NAO foi verificada a declaracao/estado real deste toggle na PRE677 e isso pode conflitar com a exigencia do usuario de nao remover efeitos. PRE678 deve localizar declaracao/cvar ativa e comparar saida, sem alterar efeitos automaticamente.
- TESTE HOST: 24 negativos e 1 caso positivo sintetico sobre predicados de opt-in, ownership, formato, mip/layer/extent, guardas antes de escrita, dependencias de amostragem, barriers/fences, observadores guest/CPU, sombreamento do carro, alias e lifetime. PASS do modelo nao executa maquina de estados real, nao testa Vulkan, pixels, efeitos ou jogos.
- ARTEFATO preservado: Drive https://drive.google.com/file/d/1jtHLbUIFTFAbEQEs-c4aCTkU9YeBbuVE/view, ZIP 184147 bytes SHA256 9fc48095000cb6f58f13695b4260c3b36e01612726e40c8836aa07cc7430280d; CRC OK e readback Drive SHA identico. Trechos completos de codigo, contagens e testes incluidos; pin docs/PRE677_SB02_V51_EXISTING_DEPTH_VERIFIED.json.
- LIMITES: nenhum patch funcional novo, velocidade/latencia de GPU NAO medidas, nenhuma comparacao de pixel/perfilamento do S24 FE, sem shader, APK V52, chave, saves, codigo externo ou limites termicos alterados. A preservacao de sombras, FXAA e demais efeitos e requisito vinculante, nao pressuposto da cvar.
- PROXIMA PRE678 SB-02: investigar maquina de estados real de profundidad_perezosa, sombra_minimo, relacao com desenfoque/radial blur, binding de copiar_imagen_, consumidores guest e falhas historicas. So propor otimizacao nova apos G2 com casos negativos derivados das funcoes de producao, equivalencia visual/guest e G4 GPU real.
- RELEASE PRESERVADA: V51 PRE652, package io.github.nfsmwrecomp, versionCode 51, SHA256 APK 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Preservar Nitro PRE398, BMW, C3 PRE194/PRE635, touch/PG-9076, graficos completos 1920x1080, fisica, shaders, saves e protecoes termicas. PRE643/SF frame pacing pausados.

Status PRE677B: politicas de adiamento ja presentes, regressao documentada sob flag desativada e riscos identificados; nenhum FPS ganho, nova build ou integracao SpeedBreaker demonstrados.
""".encode("utf-8")
def run():
    evidence=checked()
    d=drive_client()
    before=get_bytes(d,FILE_ID)
    meta=get_meta(d)
    mark=HEADING.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md" and
      meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE677B canonical file identity mismatch")
    if mark in before:
        if before.count(mark)!=1 or not before.endswith(TEXT) or len(before)-len(TEXT)!=BEFORE_BYTES or sha(before[:-len(TEXT)])!=BEFORE_SHA:
            raise ValueError("PRE677B existing append differs from expected bytes")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,"readback_identical":True,
             "canonical_sha256":sha(before),"canonical_bytes":len(before),**evidence}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA:
        raise ValueError("PRE677B canonical content changed since PRE676B; fail closed")
    copy=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(copy.get("size",0))!=BEFORE_BYTES or get_bytes(d,copy["id"])!=before:
        raise ValueError("PRE677B backup readback mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE677B concurrent edit; no overwrite")
    new=before+TEXT
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
       media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False),
       fields="id,name,size").execute()
    final=get_bytes(d,FILE_ID)
    if final!=new or final.count(mark)!=1 or not final.startswith(before):
        raise ValueError("PRE677B Drive readback != intended append")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":copy["id"],
        "readback_identical":True,"canonical_sha256":sha(final),"canonical_bytes":len(final),
        "history_preserved":True,**evidence}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=run()
    except Exception as exc:
        result={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
            "error_summary":str(exc)[:300] if isinstance(exc,ValueError) else "Drive API/transport error"}
    result.update({"stage":"PRE677B_SB02_EXISTING_DEFERRED_DEPTH_CANONICAL_CONTEXT",
      "utc":datetime.now(timezone.utc).isoformat(),
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "apk_built":False,"signing_material_accessed":False,"shader_modified":False,
      "external_speedbreaker_code_imported":False,"fps_gain_proven":False})
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE677B_"+key.upper()+"="+str(result.get(key,"none")))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
