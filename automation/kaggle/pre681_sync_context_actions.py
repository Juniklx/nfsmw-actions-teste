#!/usr/bin/env python3
"""PRE681 context sync: private Google Drive backup, append, in-place readback. No game/source/APK edits."""
import datetime as dt
import hashlib
import io
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
CONTEXT="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="# PRE681A — Actions público validado e contexto reconciliado"
ENTRY="""
---

# PRE681A — Actions público validado e contexto reconciliado (2026-11-10)

- **Execução verificada:** GitHub Actions do repositório público Juniklx/nfsmw-actions-teste, run 42902067651, job 130130329684, resultado completed/success. Gatilho do commit b71086808caa3c363128d53c15f755c57b1b6ab5. Log efetivamente consultado: PRE681_CODE_COMPILES=TRUE, PRE681_ACTIONS_V51_ARCHIVE_AUDIT=PASS, PRE681_DRIVE_PRIVATE_UPLOAD_READBACK=PASS, PRE681_DEVICE_GRAPHICS_SETTINGS=UNKNOWN, PRE681_APK_PATCH_OR_FPS_GAIN=NONE. https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42902067651
- **Evidência:** Google Drive privado 06_Logs_e_Medicoes/NFSMW_PRE681_ACTIONS_V51_READONLY_20261110_211026.zip, arquivo ID 1QJEGzudsBiGqe5Q0cDleA1KwFGNm9xqK, tamanho 1465 bytes, SHA256 6a05da090a40c93efc529d167d526155a2bbacd94bbd5cd379a677f16e80c470, ZIP CRC PASS e readback confirmado; contém PRE681_REPORT.json e PRE681_README.md.
- **Insumos autenticados por SHA-256:** APK V51 PRE652 47.104.417 bytes / 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b; fonte arquivada ZIP 21.026.481 bytes / 0ab7c949e62d377f444fb7b2489bc66d6387bd49b1798f184c4a953314064231; log PRE656 576.129 bytes / 649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7.
- **Auditoria real:** APK ZIP CRC íntegro, TOML com 121 chaves e bytes idênticos ao TOML da fonte arquivada; 4 âncoras textuais no Ajustes.java, 6 no MotorNativo.java e strings DEX presentes. Isso NÃO demonstra byte-identidade do Java arquivado com o código DEX real nem o fluxo de controle do aplicativo.
- **Sessão PRE656:** resolução interna 1920x1080 e cap 60 FPS (saída 1280x720/60 Hz). O objetivo do projeto até 120 FPS não estava ativo nesta sessão.
- **Qualidade:** padrões distribuídos no TOML: nfsmw_nativo_sin_desenfoque=true, nfsmw_nativo_pcf_barato=true, nfsmw_sombras_sin_vegetacion=true, nfsmw_nativo_sombras_escala=100, nfsmw_sombras_corte=150. Não confundir com os valores efetivamente ativos no S24 FE, pois nem SharedPreferences nem TOML privado do celular foram lidos. Fidelidade real ainda UNKNOWN.
- **Segurança:** Secrets OAuth Google foram utilizáveis na execução sem exibir seus valores. Nenhum material de assinatura foi acessado. O repositório antigo virou público e a consulta histórica mostrou que o run PRE194 42145746704 ainda tinha artefato ~45MB de APK acessível; revisar artefatos e workflows antigos antes de ampliar acesso a Secrets.
- **Estado preservado:** V51 PRE652, pacote io.github.nfsmwrecomp, versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Sem nova APK, patches, alterações em shaders, controles, física, saves ou proteções térmicas; nenhum ganho de FPS medido.
- **Próximo gate PRE682:** auditar cadeia de preferências/argumentos do launcher e exigir evidência autorizada dos ajustes ativos (desfoque, sombras rapida/suave/xbox360, distância e escala, resolução/FPS). O Actions não acessa automaticamente arquivos privados do celular: antes de qualquer patch, inspecionar tela de ajustes ou outro export autorizado.

Status PRE681: CI_PASS, PRIVATE_DRIVE_ZIP_READBACK_PASS, ACTIVE_DEVICE_GRAPHICS_UNKNOWN, NO_NEW_APK, NO_FPS_GAIN.
"""

def sha(b):
    return hashlib.sha256(b).hexdigest()

def get_raw(d, fid):
    output=io.BytesIO()
    stream=MediaIoBaseDownload(output,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=stream.next_chunk()
    return output.getvalue()

def main():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    missing=[k for k in names if not os.environ.get(k)]
    if missing:
        raise RuntimeError("PRE681_CONTEXT_MISSING_SECRETS="+",".join(missing))
    cred=Credentials(token=None,refresh_token=os.environ[names[0]],
                     client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
                     token_uri="https://oauth2.googleapis.com/token")
    cred.refresh(Request())
    d=build("drive","v3",credentials=cred,cache_discovery=False)
    meta=d.files().get(fileId=CONTEXT,fields="id,name,mimeType,parents,size,md5Checksum").execute()
    if meta.get("name")!="CONTEXTO_NFSMW.md" or meta.get("mimeType") not in ("text/markdown","text/plain") or ROOT not in meta.get("parents",[]):
        raise ValueError("PRE681_CONTEXT_TARGET_MISMATCH")
    old=get_raw(d,CONTEXT)
    if meta.get("size")!=str(len(old)) or meta.get("md5Checksum")!=hashlib.md5(old).hexdigest():
        raise ValueError("PRE681_CONTEXT_METADATA_MISMATCH")
    content=old.decode("utf-8")
    if MARKER in content:
        if "42902067651" not in content: raise ValueError("PRE681_CONTEXT_MARKER_CONFLICT")
        print("PRE681_CANONICAL_CONTEXT=ALREADY_CURRENT")
        return
    if "# PRE680 — observacao independente" not in content[-16000:]:
        raise ValueError("PRE681_PRE680_ANCHOR_NOT_AT_TAIL")
    q=f"'{ROOT}' in parents and name = '04_Backups' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    folders=d.files().list(q=q,fields="files(id,name),nextPageToken",page_size=100).execute()
    if len(folders.get("files",[]))!=1 or folders.get("nextPageToken"):
        raise ValueError("PRE681_BACKUP_FOLDER_MISSING_OR_AMBIGUOUS")
    backup_parent=folders["files"][0]["id"]
    timestamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup=d.files().copy(fileId=CONTEXT,body={"name":"CONTEXTO_NFSMW_BACKUP_PRE681_"+timestamp+".md","parents":[backup_parent]},
                          fields="id,parents").execute()
    if backup_parent not in backup.get("parents",[]) or sha(get_raw(d,backup["id"]))!=sha(old):
        raise ValueError("PRE681_BACKUP_READBACK_MISMATCH")
    if sha(get_raw(d,CONTEXT))!=sha(old):
        raise ValueError("PRE681_CONTEXT_CHANGED_DURING_BACKUP")
    new=(content.rstrip()+"\n\n"+ENTRY.lstrip()).encode("utf-8")
    uploaded=d.files().update(fileId=CONTEXT,media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown"),
                              fields="id,size,md5Checksum").execute()
    if uploaded.get("id")!=CONTEXT or uploaded.get("size")!=str(len(new)) or sha(get_raw(d,CONTEXT))!=sha(new):
        raise ValueError("PRE681_CONTEXT_INPLACE_READBACK_MISMATCH")
    evidence=json.dumps({"status":"PASS","gate":"PRE681_CONTEXT_SYNC","run_id":os.environ.get("GITHUB_RUN_ID"),
        "context_file_id":CONTEXT,"backup_file_id":backup["id"],"before_sha256":sha(old),"after_sha256":sha(new),
        "pre681_actions_run":42902067651,"private_pre681_zip_id":"1QJEGzudsBiGqe5Q0cDleA1KwFGNm9xqK",
        "device_preferences_obtained":False,"new_apk":False},indent=2,sort_keys=True).encode("utf-8")
    saved=d.files().create(body={"name":"NFSMW_PRE681_CONTEXT_SYNC_"+timestamp+".json","parents":[LOGS]},
                           media_body=MediaIoBaseUpload(io.BytesIO(evidence),mimetype="application/json"),
                           fields="id,size").execute()
    if sha(get_raw(d,saved["id"]))!=sha(evidence):
        raise ValueError("PRE681_CONTEXT_SYNC_AUDIT_READBACK_MISMATCH")
    print("PRE681_CANONICAL_CONTEXT_UPDATE=PASS")
    print("PRE681_PRIVATE_BACKUP_READBACK=PASS")
    print("PRE681_SYNC_EVIDENCE_PRIVATE=PASS")
    print("PRE681_APK_OR_SIGNING_MATERIAL_MODIFIED=FALSE")

if __name__=="__main__":
    main()
