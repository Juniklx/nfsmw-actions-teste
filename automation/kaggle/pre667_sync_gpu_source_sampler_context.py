#!/usr/bin/env python3
"""PRE667: verified PRE665+PRE666 append-only canonical Drive checkpoint, backup first."""
from __future__ import annotations
import argparse,hashlib,io,json,time,zipfile
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

BEFORE_BYTES=1071598
BEFORE_SHA="27bebb9a1a1c3c67888e2b117934d40b01a80ea4fcbd6f9281718774c759ad7c"
ZIP665=("1Rlh7sfBzHFs2z0BA3_9LA3L_LrUVWbCs",21463,"f5086883884c5153926beaad6ddb7ffa649d56f99b844a78d5388d3e27980198")
ZIP666=("1I8YGJX_PQJG0RLjugyxp7bHer-Nh8ySg",1253,"05a03dba284e70eede9a4c7a355239b64e857a48df10e8359c598b203a41e063")
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE667_GPU_SOURCE_AND_SAMPLER_20261110.md"
MARKER=b"# PRE667 — PRE665 e PRE666 GPU: pontos reais Vulkan e modelo seguro de passagem"
OUT=Path("/tmp/nfsmw-pre667/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()
APPEND="""

---

# PRE667 — PRE665 e PRE666 GPU: pontos reais Vulkan e modelo seguro de passagem (2026-11-10)

## PRE665 — fonte V51 autenticada, somente leitura

- GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42837121790, job 129902187958, completed/success; PRE665_STATUS=AUDIT_OK_AUTHENTIC_V51_DRAW_AND_C2_SOURCE_ANCHORS; gate final PRE665_AUTHENTIC_DRAW_EMISSION_VULKAN_TIMESTAMP_SOURCE_GATE=PASS.
- Fonte PRE99 autenticada por SHA256 af8e82e198d00656814477fd64b8cc791fada21d937c1aa18e58b72005245bf, restaurada em diretorio temporario; replay PRE431, PRE638 e patch PRE648 exato em memoria, hash renderer V51 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2; backend Vulkan hash b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385. Equivalencia bit a bit dessa fonte reconstruida com ELF da V51 assinada NAO provada.
- Buscador encontrou 6 ocorrencias de vkCmdDraw/Indexed no arquivo de renderer, das quais 2 sao COMENTARIOS, e **4 sao chamadas reais**: desenhos normais em linhas 3693/3697, ceu adiado em 3782/3784. Contador PRE648 registra DESPOIS de emitir draw normal na linha 3711 e ceu adiado na 3790. Portanto essas linhas pos-draw NAO podem ser usadas diretamente como marca GPU de inicio pre-draw.
- Classificador C2 no renderer inicia nova categoria em 10107 e chama MarcarGpu na 10108. Backend C2 possui escritor por ponteiro em 3690 e 5165, leitor em 4956 e outras rotas de consultas, reinicio dos pools e fences presentes. PRE665 localizou PONTOS TEXTUAIS; nao implementou nem validou integracao, comando Vulkan extra, abertura de render pass ou isolamento de tempo por shader.
- ZIP original do run e re-download do Drive conferidos SHA256 byte a byte, CRC OK: https://drive.google.com/file/d/1Rlh7sfBzHFs2z0BA3_9LA3L_LrUVWbCs/view, nome 06_Logs_e_Medicoes/NFSMW_PRE665_V51_DRAW_BOUNDARY_SOURCE_AUDIT_42837121790.zip, 21463 bytes, SHA256 f5086883884c5153926beaad6ddb7ffa649d56f99b844a78d5388d3e27980198; artefato GitHub 13774062743; registro docs/PRE665_V51_GPU_DRAW_BOUNDARIES_VERIFIED.json.

## PRE666 — robustez do modelo host sem Vulkan

- Primeiro run 42838073582 completed/failure ANTES do compilador: condicao booleana invertida no workflow tentou negar no_vk_commands_injected. Nao foi defeito do codigo C++, renderer ou Android; sem APK. Corrigida uma unica assercao no workflow no commit dffeb9a4db4caf6bd383a2ad46f7c5e8ff01b93b.
- Retry definitivo https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42838202826, job 129905996369, completed/success. C++17 host compilado com -Wall -Wextra -Werror -pedantic e ASan/UBSan, testes de limites/estado e 1 milhao de eventos deterministas: PRE666_HOST_PASS_BOUNDARY_TEST=PASS, PRE666_EXPLICIT_PASS_END=PASS, PRE666_STATUS=HOST_PASS_ASAN_UBSAN_NO_VULKAN.
- Novo modelo em automation/kaggle/pre666_pass_bounded_sampler.h e pre666_pass_bounded_host_test.cpp: default OFF, ate 4 blocos/8 indices de consulta por slot, apenas par p2 VS62 PS58, chamada projetada imediatamente ANTES do draw, encerra bloco na troca de par, ANTES do fim de render pass e ANTES do fim de command buffer; recusa reuso quando a entrada externa informa fence incompleta, ignora ceu adiado. Nao confundir simulacao da fence com verifica-la de fato no driver.
- Evidencia no Drive https://drive.google.com/file/d/1I8YGJX_PQJG0RLjugyxp7bHer-Nh8ySg/view, 06_Logs_e_Medicoes/NFSMW_PRE666_HOST_PASS_END_42838202826.zip, 1253 bytes, SHA256 05a03dba284e70eede9a4c7a355239b64e857a48df10e8359c598b203a41e063, CRC OK e comparacao SHA no re-download; artefato GitHub 13774723008. O benchmark host NAO mede overhead no driver.

## Estado e proxima etapa

- V51 PRE652 permanece a ultima APK assinada, SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, pacote io.github.nfsmwrecomp, versionCode 51 no APK, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nenhuma V52 criada, nenhum novo teste de FPS feito, tempo de GPU de VS62/PS58 ainda desconhecido.
- Proxima PRE668: revisar na fonte autenticada os inicios/fins de render pass REAIS, comando/submissao, objetos de query pool e vida das fences. Preparar injeção estritamente reversivel em arvore temporaria, DEFAULT OFF, com pool dedicado somente se suportado e testado; gate ARM64 NO APK e inspeção do ELF antes de considerar APK diagnostica; quantificar overhead e vies de amostragem. Nao usar tabela de draws como prova de tempo GPU.
- Preservar 1920x1080, meta 120 FPS sem adulterar configuracao real do usuario, graficos, SPIR-V, efeitos, fisica, controles touch/iPega PG-9076, Nitro PRE398, BMW, C3 PRE194/PRE635, saves, assinatura e protecoes termicas. Prioridade GPU/shaders; SurfaceFlinger, frame pacing e C3 PRE643 continuam suspensos.

**Status PRE667:** auditoria fonte real PASS, modelo pass-boundary HOST PASS, evidencia arquivada; nenhum ganho de FPS ou medicao Vulkan individual comprovados.
"""

def verify_zip(drive, spec, json_name, expected_run, expected_status):
    fid,length,expected_sha=spec
    payload=get_bytes(drive,fid)
    if len(payload)!=length or sha(payload)!=expected_sha:
        raise ValueError("PRE667 archive bytes/hash do not match")
    with zipfile.ZipFile(io.BytesIO(payload)) as zipf:
        if zipf.testzip() is not None:raise ValueError("PRE667 archive CRC failure")
        report=json.loads(zipf.read(json_name))
    if report.get("status")!=expected_status or (expected_run is not None and report.get("github_run_id")!=expected_run):
        raise ValueError("PRE667 report status/run mismatch")
    if report.get("fps_gain_proven") is not False:raise ValueError("PRE667 false FPS claim")
    return report
def gate():
    d=drive_client()
    a=verify_zip(d,ZIP665,"PRE665_V51_DRAW_AND_C2_BOUNDARY_AUDIT.json",None,
        "AUDIT_OK_AUTHENTIC_V51_DRAW_AND_C2_SOURCE_ANCHORS")
    b=verify_zip(d,ZIP666,"PRE666_V51_HOST_PASS_END_SAFETY_REPORT.json",42838202826,
        "HOST_PASS_ASAN_UBSAN_NO_VULKAN")
    if not(a.get("source",{}).get("v51_instrumented_renderer_sha256")==
      "9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and a.get("anchors",{}).get("renderer_pre648_count",{}).get("lines")==[3711,3790]
      and a.get("apk_built") is False and a.get("arm64_compiled") is False
      and b.get("pass_end_flush_tested") is True
      and b.get("default_enabled") is False
      and b.get("apk_built") is False and b.get("real_arm64_compiled") is False):
        raise ValueError("PRE667 authenticated source/sampler evidence malformed")
    return d

def update():
    d=gate()
    additional=APPEND.encode("utf-8")
    if additional.count(MARKER)!=1:raise ValueError("PRE667 nonunique marker")
    meta=get_meta(d)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
      and meta.get("mimeType")=="text/markdown" and meta.get("parents")==[PARENT]):
        raise ValueError("PRE667 unexpected Drive canonical file identity")
    before=get_bytes(d,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE667 size mismatch")
    if MARKER in before:
        if not(before.count(MARKER)==1 and before.endswith(additional)
         and len(before)-len(additional)==BEFORE_BYTES
         and sha(before[:-len(additional)])==BEFORE_SHA):
            raise ValueError("PRE667 prior append differs; no overwrite")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
            "readback_identical":True,"canonical_sha256":sha(before),"canonical_bytes":len(before)}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA or before.count(b"# PRE664B ")!=1:
        raise ValueError("PRE667 previous canonical context changed since baseline; abort")
    after=before+additional
    backup=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},fields="id,name,size").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=BEFORE_BYTES or get_bytes(d,backup_id)!=before:
        raise ValueError("PRE667 context backup not identical")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE667 detected concurrent modification")
    for i in range(3):
        current=get_bytes(d,FILE_ID)
        if current==after:break
        if current!=before:raise ValueError("PRE667 concurrent write; abort")
        try:
            d.files().update(fileId=FILE_ID,supportsAllDrives=True,
              media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False),
              fields="id,name,size,modifiedTime").execute()
        except HttpError as e:
            if e.resp.status not in (500,502,503,504) or i==2:raise
            if get_bytes(d,FILE_ID)==after:break
            time.sleep(2*(i+1))
    readback=get_bytes(d,FILE_ID)
    if readback!=after or not readback.startswith(before) or readback.count(MARKER)!=1:
        raise ValueError("PRE667 postupdate readback mismatch; backup retained")
    return {"status":"AUDIT_OK","backup_created":True,
        "backup_id":backup_id,"original_sha256":sha(before),
        "canonical_sha256":sha(readback),"canonical_bytes":len(readback),
        "readback_identical":True,"previous_history_preserved":True}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=update()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,
         "error_summary":str(e)[:220] if isinstance(e,ValueError) else "Drive API or evidence transfer failure"}
    r.update({"stage":"PRE667_CANONICAL_GPU_SOURCE_AND_HOST_SAFETY",
      "github_run_id":int(args.run_id),"utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE667_"+key.upper()+"="+str(r.get(key,"none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
