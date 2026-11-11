#!/usr/bin/env python3
"""PRE684: guarded append to canonical private Drive context after verified backup."""
import datetime as dt
import hashlib
import io
import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

CONTEXT="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1ZhWEuV4javfU2EhDcmlK-9Zsp22rSJ2F"
ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="## PRE681-PRE684 - resultados verificados em 2026-11-10"
APPEND="""
---

## PRE681-PRE684 - resultados verificados em 2026-11-10

PRE681: GitHub Actions run 42902067651, job 130130329684, completed/success. APK V51 PRE652, snapshot de fontes historico e log PRE656 autenticados por SHA-256; CRC da APK, 121 chaves TOML, anchors Java/DEX e upload privado passaram. Evidencia no Drive: 1QJEGzudsBiGqe5Q0cDleA1KwFGNm9xqK. Padrões empacotados no TOML NAO equivalem as cvars ativas no S24 FE.

PRE682: GitHub Actions run 42910788328, job 130160579462, completed/success. classes.dex real da APK V51 contem argumentos graficos e referencias a metodos que leem SharedPreferences; co-ocorrencia, nao prova de dataflow nem de valores em runtime. Evidencia Drive: 1pkpOUw0jDBDDwzSZH9VZ2tM6b-uGR3zD. Captura do menu antes de jogar: Vulkan, 1920x1080, 60 FPS, sombras Xbox 360/Ultra/Longe, desfoque ligado, reflexos altos, anisotropico 16x. Opcoes exibidas nao sao leitura de cvars.

PRE683: GitHub Actions run 42913355889, job 130169400098, completed/success. Ambas as bibliotecas ARM64 contem nomes das cinco flags de desfoque e sombras; o log PRE656 nao registra valores explicitos. Evidencia Drive: 1Xbpc7krliit4xke9ZFcltfN3117hMK0V.

PRE684: GitHub Actions run 42935465892, job 130244338759, completed/success. Coerencia estatica da receita V49/V50/V51, certificado permanente e aprovacao PRE651; arquivo de cabeçalho PRE648 SHA-256 9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe. Nao foi executado replay/compilacao da arvore de fontes. APK V51 47.104.417 bytes SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b possui marcador PRE648 somente em libmain.so (PAL), nao em libmain_usa.so (USA). Log PRE656 original contem 14 linhas PRE648 GPU_SHADER10s; portanto instrumentacao PAL foi executada na sessao, sem demonstrar diretamente a biblioteca mapeada por /proc/maps. 14 janelas somaram 14.265.243 draws, 14.258.146 normais, 7.097 deferred_sky, zero IDs invalidos. Parciais de pares relatados: 8 na primeira janela, 12 nas demais. Na telemetria GPU C2 (7 amostras), medianas por Swap: cena 2,95 ms, copias 1,94 ms, cubo/desfoque juntos 1,33 ms, sombras 0,59 ms, reflexos 0,82 ms, hueco 7,56 ms. Frequencia de desenhos nao equivale a custo individual de shader. Evidencia privada PRE684 Drive: 1AXjA3oiLABjKi9_cP7Jx_esHH0evOzS2, ZIP de 2228 bytes, SHA256 033ce359372741cb6dc86dfa607f8a9625a3e19b6ad20d9a27e801c16b198ab8.

Baseline preservado: APK V51 PRE652, package io.github.nfsmwrecomp, versionCode 51, certificado SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Sem nova APK, patches, mudancas de shader ou ganho FPS demonstrado. Log PRE656 confirma 1920x1080 internos e cap 60 FPS; objetivo futuro ate 120 FPS com graficos completos. Seguir preservando controles, saves, fisica e protecoes termicas.

PRE685 proposto: confirmar cvars realmente recebidas pelo motor, sincronizacao de apresentacao e frametimes antes de decidir otimizacao; eventual instrumentacao exige autenticar arvore exata, alteracao reversivel, assinatura permanente e versionCode>51. Nao publicar APK, ISOs, logs privados ou material de assinatura em GitHub publico.

Status PRE684: ACTIONS_PASS; C2_GPU_AGGREGATED_ANALYZED; PAL_PRE648_EXECUTION_INDICATED; LIVE_GRAPHICS_CVARS_UNVERIFIED; NO_BUILD; FPS_GAIN_UNPROVEN.
"""

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def get_bytes(d,fid):
    b=io.BytesIO()
    downloader=MediaIoBaseDownload(b,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk()
    return b.getvalue()

def main():
    required=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    if any(not os.environ.get(k) for k in required):
        raise ValueError("PRE684_CONTEXT_MISSING_REQUIRED_SECRET")
    print("PRE684_CONTEXT_STAGE=AUTH")
    c=Credentials(token=None,refresh_token=os.environ[required[0]],
         client_id=os.environ[required[1]],client_secret=os.environ[required[2]],
         token_uri="https://oauth2.googleapis.com/token")
    c.refresh(Request())
    d=build("drive","v3",credentials=c,cache_discovery=False)
    print("PRE684_CONTEXT_STAGE=FETCH_META")
    meta=d.files().get(fileId=CONTEXT,fields="id,name,mimeType,size,parents").execute()
    if (meta.get("id")!=CONTEXT or meta.get("name")!="CONTEXTO_NFSMW.md"
        or ROOT not in meta.get("parents",[]) or meta.get("mimeType")!="text/markdown"):
        raise ValueError("PRE684_CONTEXT_WRONG_FILE_OR_PARENT")
    current=get_bytes(d,CONTEXT)
    if meta.get("size")!=str(len(current)):
        raise ValueError("PRE684_CONTEXT_SIZE_INCONSISTENT")
    original=current.decode("utf-8")
    if MARKER in original:
        print("PRE684_CONTEXT_SYNC=ALREADY_PRESENT")
        return
    expected="Status PRE680: TOML_APK_AUTHENTICATED, LOG_GALAXY_1080P_CONFIRMED, ACTUAL_BLUR_SHADOW_SETTINGS_UNKNOWN, NO_APK, CI_BLOCKED."
    if not original.rstrip().endswith(expected):
        raise ValueError("PRE684_CONTEXT_NOT_AT_VERIFIED_PRE680_TAIL")
    print("PRE684_CONTEXT_STAGE=VERIFY_BACKUP")
    if sha(get_bytes(d,BACKUP))!=sha(current):
        raise ValueError("PRE684_CONTEXT_CHANGED_SINCE_BACKUP")
    updated=(original.rstrip()+"\n\n"+APPEND.lstrip()).encode("utf-8")
    print("PRE684_CONTEXT_STAGE=UPDATE_IN_PLACE")
    d.files().update(fileId=CONTEXT,
        media_body=MediaIoBaseUpload(io.BytesIO(updated),mimetype="text/markdown",resumable=True),
        fields="id,size").execute()
    if sha(get_bytes(d,CONTEXT))!=sha(updated):
        raise ValueError("PRE684_CONTEXT_READBACK_MISMATCH")
    print("PRE684_CONTEXT_STAGE=WRITE_PRIVATE_RECEIPT")
    receipt=json.dumps({
       "stage":"PRE684_CANONICAL_CONTEXT_SYNC","status":"PASS",
       "run_id":os.environ.get("GITHUB_RUN_ID"),
       "original_id":CONTEXT,"backup_id":BACKUP,
       "old_sha256":sha(current),"new_sha256":sha(updated),
       "pre684_audit_run_id":"42935465892",
       "apk_or_signature_modified":False
    },sort_keys=True,indent=2).encode("utf-8")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    item=d.files().create(
        body={"name":"NFSMW_PRE684_CONTEXT_SYNC_"+stamp+".json","parents":[LOGS]},
        media_body=MediaIoBaseUpload(io.BytesIO(receipt),mimetype="application/json"),
        fields="id,size").execute()
    if sha(get_bytes(d,item["id"]))!=sha(receipt):
        raise ValueError("PRE684_RECEIPT_READBACK_MISMATCH")
    print("PRE684_CANONICAL_CONTEXT_UPDATE=PASS")
    print("PRE684_CONTEXT_BACKUP_READBACK=PASS")
    print("PRE684_CONTEXT_RECEIPT_PRIVATE=PASS")
    print("PRE684_SIGNING_AND_APK_UNCHANGED=TRUE")

if __name__=="__main__":
    main()
