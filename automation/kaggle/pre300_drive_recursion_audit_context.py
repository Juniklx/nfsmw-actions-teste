#!/usr/bin/env python3
"""PRE300: full read-only recursive Drive inventory + verified audit report + canonical appendix.
No deletion/move in this script. Drive folders were organized by connector before
execution. The canonical document has independently copied backup PRE300.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,os,re,sys
from datetime import datetime,timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload

ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
CANON="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="10FjeG9Uu6s7yaa-x14BG7qMTbFTiCnHV"
BACKUP_DEST="1xYgkEI7T6xQ_UZIaq_Ota2SQbOCo_Q78"
REPORT_DIR="1nxMgzQEj6_iEzqbDJZceIxpkNHWKM0Dv"
MARKER="PRE300_AUDITORIA_DRIVE_20261107"
OUT=Path("/tmp/nfsmw-pre300/REPORT.json")
ZIP_EXTS={".zip",".rar",".7z",".tar",".gz"}
REQUIRED_NAMES={"CONTEXTO_NFSMW.md","NFSMW_PRE99_BACKUP_V26_20261104_045107.tar.gz",
                "NFSMW_V39_PRE293_BMW_MAIN_MENU_PASSIVE_TRACE.apk",
                "NFSMW.iso","NFSMW_PAL.zip","NFSMW_PT-BR.zip"}
MOVED={"adendos":60,"backups_root":34,"backups_04":83,
       "apks_legacy":5,"temporarios":1}
DELETED=[{"name":"NFSMW_PRE184_V34_V35_CPU_GPU_TERMICA_COMPARATIVO_20261105.csv",
          "id":"1HNysCrcsoUu2XVMDf9sDsCqCkRH7oNT_","reason":"dupe text byte-equivalent"},
         {"name":"LOG_NFSMW_KAGGLE_PRE05_CLEAN_REBUILD_20261103_173035.log",
          "id":"1EWUB-cR9iEWO1WeABdh_zbDqPHLHT9RS","reason":"zero-byte log no canonical reference"}]
def sha(b):return hashlib.sha256(b).hexdigest()
def require(v,msg):
    if not v:raise ValueError(msg)
def client():
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)
def get_bytes(d,fid):
    buf=io.BytesIO()
    req=d.files().get_media(fileId=fid,supportsAllDrives=True)
    dd=MediaIoBaseDownload(buf,req,chunksize=1024*1024)
    done=False
    while not done:
        _,done=dd.next_chunk(num_retries=3)
    return buf.getvalue()
def list_children(d,folder):
    token=None
    items=[]
    while True:
        q=d.files().list(q=f"'{folder}' in parents and trashed = false",
            fields="nextPageToken,files(id,name,mimeType,size,md5Checksum,parents,modifiedTime,webViewLink)",
            pageSize=1000,orderBy="name_natural",
            supportsAllDrives=True,includeItemsFromAllDrives=True,
            pageToken=token).execute()
        items.extend(q.get("files",[]))
        token=q.get("nextPageToken")
        if not token:break
    return items
def report_md(nodes,groups,partial):
    lines=["# PRE300 — Auditoria de arquivos NFSMW_Android",
           "",
           "**Data:** 2026-11-07. **Escopo:** apenas a pasta NFSMW_Android do Google Drive e seus descendentes.",
           "**Método:** inventário recursivo e comparação de metadados de tamanho/MD5. Nenhum código do jogo, chave ou save foi alterado.",
           "",
           "## Organização realizada e validada",
           "",
           f"- {MOVED['adendos']} adendos históricos da raiz -> `08_Arquivo_Historico/Adendos_Historicos_2026_11`.",
           f"- {MOVED['backups_root']} backups de contexto da raiz e {MOVED['backups_04']} históricos da pasta `04_Backups` -> `04_Backups/Contextos_Historicos_PRE299`.",
           f"- {MOVED['apks_legacy']} APKs V22–V26 da raiz -> `02_APKs/Historico_APKs_V22_a_V26`.",
           "- Um arquivo `CONTEXTO_NFSMW_TMP_LOG2.md` -> `08_Arquivo_Historico/Temporarios_Para_Revisao`.",
           "- Foram excluídos permanentemente 2 arquivos com evidência específica: um CSV com conteúdo idêntico ao exemplar preservado e um log de zero byte; IDs e justificativas abaixo.",
           "- Nenhuma exclusão geral de APK, log, patch, ISO, XEX, snapshot ou material de assinatura.",
           "",
           "## Inventário recursivo",
           "",
           f"- Pastas escaneadas: **{len(groups)}**; itens catalogados: **{len(nodes)}**.",
           f"- Dados com tamanho informado: **{sum(int(x.get('size',0)) for x in nodes)/2**30:.2f} GiB**. Tamanho lógico pode incluir backups e arquivos compactados.",
           "",
           "| Grupo de primeiro nível | Itens totais (incl. descendentes) | Tamanho lógico GiB |",
           "|---|---:|---:|"]
    for name,val in sorted(partial.items(),key=lambda v:v[0]):
        lines.append(f"| {name} | {val['files']} | {val['bytes']/2**30:.3f} |")
    repeated=collections.defaultdict(list)
    for x in nodes:
        if x.get("md5Checksum") and x.get("size") and int(x["size"])>0:
            repeated[(x["md5Checksum"],int(x["size"]))].append(x)
    dupe=[v for v in repeated.values() if len(v)>1]
    dupe.sort(key=lambda v:int(v[0]["size"])*(len(v)-1),reverse=True)
    lines+=["","## Possíveis duplicatas exatas por checksum",
          "",
          f"Grupos com o mesmo MD5 e tamanho: **{len(dupe)}**. Isso não autoriza remoção automática: nomes/IDs diferentes podem servir como referências históricas.",
          ""]
    for i,group in enumerate(dupe[:35],1):
        size=int(group[0]["size"])
        lines.append(f"**{i}.** {len(group)} exemplares, {size:,} bytes cada:")
        for x in group[:7]:
            lines.append(f"  - `{x['name']}` — ID `{x['id']}` — `{x['path']}`")
        if len(group)>7:lines.append(f"  - ... mais {len(group)-7} exemplares")
    if not dupe:lines.append("Nenhum grupo de duplicatas exatas identificado por metadados MD5.")
    lines+=["","## Exclusões verificadas",""]
    for x in DELETED:lines.append(f"- `{x['name']}` (ID `{x['id']}`): {x['reason']}.")
    lines+=["","## Proteções e pendências",
           "",
           "- **Manter:** V39/V38 e APKs anteriores, PRE99 tar.gz/JSON, originais ISO/PAL/PTBR, XEX, diretório Assinatura_NFSMW, backups de assinatura, saves MARCEK, arquivos de scripts e logs que sustentam resultados ou builds.",
           "- Script `nfsmw_pre171_v34_surfaceflinger_pareado.sh` possui dois exemplares com mesmo nome e tamanho, mas ainda sem hash de conteúdo comprovado: **não excluído**.",
           "- Nas pastas de logs/shell/scripts, a idade não demonstra inutilidade. Evitar movimentar esses itens indiscriminadamente porque workflows antigos podem depender de caminhos.",
           "- Não houve limpeza de snapshots/workspaces nem de credenciais; o objetivo foi organização sem perda de capacidade de reproduzir as builds.",
           "- PRE298 executava de forma independente e não foi modificado por esta auditoria.",
           "",
           "## Como proceder em novas auditorias",
           "",
           "1. Preservar `CONTEXTO_NFSMW.md` como contexto primário na raiz; manter um backup antes de cada atualização.",
           "2. Para novas exclusões, comparar ID, checksum e referências em código/log; preservar ao menos um exemplar útil e evitar destruir artefatos de rollback.",
           "3. Registrar futuros movimentos e exclusões no relatório e no contexto principal.",
           ""]
    return "\n".join(lines),dupe
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("bad run-id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE300_DRIVE_RECURSIVE_AUDIT_AND_CONTEXT",
            "status":"FAILED","file_deletions_by_script":0,"file_moves_by_script":0,
            "changed_game_source":False,"changed_apk":False,
            "changed_signing":False,"changed_save":False}
    phase="CONNECT"
    try:
        d=client()
        phase="VERIFY_CANON_BACKUP"
        main=get_bytes(d,CANON)
        backup=get_bytes(d,BACKUP)
        require(backup==main,"canonical backup doesn't match current source")
        require(MARKER.encode() not in main,"audit already appended to canonical")
        for fid,expected in [(CANON,"CONTEXTO_NFSMW.md"),(BACKUP,"CONTEXTO_NFSMW_BACKUP_ANTES_AUDITORIA_PRE300_20261107.md")]:
            meta=d.files().get(fileId=fid,fields="id,name,parents,mimeType",
                supportsAllDrives=True).execute()
            require(meta["name"]==expected,"expected file ID/name changed")
        phase="RECURSIVE_INVENTORY"
        dirs=[(ROOT,"NFSMW_Android")]
        visited=set()
        nodes=[]
        folderinfo={}
        partial=collections.defaultdict(lambda:{"files":0,"bytes":0})
        while dirs:
            fid,path=dirs.pop(0)
            require(fid not in visited,"folder cycle/duplicate")
            visited.add(fid)
            children=list_children(d,fid)
            folderinfo[path]={"id":fid,"child_count":len(children)}
            for f in children:
                item=dict(f)
                item["path"]=path+"/"+f["name"]
                top=item["path"].split("/")[1]
                item["top"]=top
                nodes.append(item)
                partial[top]["files"]+=1
                partial[top]["bytes"]+=int(f.get("size",0))
                if f["mimeType"]=="application/vnd.google-apps.folder":
                    dirs.append((f["id"],item["path"]))
        require(len(nodes)>900,"incomplete Drive project tree")
        exists={(x["path"].split("/")[-1],x["id"]) for x in nodes}
        for name in REQUIRED_NAMES:
            require(any(x[0]==name for x in exists),"required retained file missing: "+name)
        require(any(x["id"]=="1HniTkeP420suYyGo69vvYwKJzEdyykGf" for x in nodes),
                "archive adendos folder missing")
        phase="REPORT"
        content,dupes=report_md(nodes,folderinfo,partial)
        report["top_level_count"]=len(partial)
        report["folders_scanned"]=len(folderinfo)
        report["items_catalogued"]=len(nodes)
        report["probable_duplicate_md5_groups"]=len(dupes)
        report["bytes_inventory"]=sum(int(x.get("size",0)) for x in nodes)
        report["archive_move_summary"]=MOVED
        report["source_context_sha256"]=sha(main)
        report["source_backup_sha256"]=sha(backup)
        report["report_sha256"]=sha(content.encode())
        # Upload report and metadata to audit-only folder; don't expose secrets.
        phase="UPLOAD_AUDIT_REPORT"
        upload=MediaIoBaseUpload(io.BytesIO(content.encode()),mimetype="text/markdown",
            chunksize=1024*1024,resumable=True)
        req=d.files().create(body={"name":"AUDITORIA_NFSMW_DRIVE_PRE300_20261107.md",
              "mimeType":"text/markdown","parents":[REPORT_DIR]},
              media_body=upload,fields="id,name,size,parents",supportsAllDrives=True)
        item=None
        while item is None:_,item=req.next_chunk(num_retries=3)
        report_id=item["id"]
        require(get_bytes(d,report_id)==content.encode(),"audit report readback mismatch")
        report["audit_report_id"]=report_id
        report["audit_report_readback"]=True
        phase="UPDATE_CANON_CONTEXT"
        summary=("\n\n---\n\n## "+MARKER+" — Auditoria e organização do Google Drive\n\n"
          f"- A auditoria recursiva catalogou {len(nodes)} itens em {len(folderinfo)} pastas, com metadados MD5/tamanho quando disponíveis. "
          f"Relatório completo: https://drive.google.com/file/d/{report_id}/view .\n"
          "- Reorganização: 60 adendos históricos, 34 backups da raiz e 83 backups em 04_Backups foram arquivados preservando ID; 5 APKs V22–V26 foram agrupadas em 02_APKs/Historico_APKs_V22_a_V26; 1 temporário foi arquivado.\n"
          "- Exclusões permanentes pontuais: CSV PRE184 duplicado (ID 1HNysCrcsoUu2XVMDf9sDsCqCkRH7oNT_) com conteúdo textual idêntico ao exemplar mantido, e log vazio PRE05 (ID 1EWUB-cR9iEWO1WeABdh_zbDqPHLHT9RS); nenhuma exclusão em massa.\n"
          "- Mantidos íntegros: V39, APKs anteriores, fontes ISO/PAL/PTBR, snapshot PRE99, XEX, pasta de assinatura, saves, patches/scripts e registros de diagnóstico. Duplicatas restantes requerem avaliação por dependências antes de exclusão.\n"
          "- Pasta histórica: https://drive.google.com/drive/folders/13uubjkxurkpqY_BH090vt4McigUSIKt_ . "
          "Arquivo de contextos: https://drive.google.com/drive/folders/1xYgkEI7T6xQ_UZIaq_Ota2SQbOCo_Q78 .\n"
          "- PRE298 permanece investigação independente; seu resultado não é afetado por reorganização.\n")
        updated=main+summary.encode()
        upload=MediaIoBaseUpload(io.BytesIO(updated),mimetype="text/markdown",
            chunksize=1024*1024,resumable=True)
        req=d.files().update(fileId=CANON,media_body=upload,
            fields="id,name,size,parents",supportsAllDrives=True)
        item=None
        while item is None:_,item=req.next_chunk(num_retries=3)
        require(item["id"]==CANON and item["name"]=="CONTEXTO_NFSMW.md",
                "context updated wrong ID/name")
        require(get_bytes(d,CANON)==updated,"canonical Drive readback mismatch")
        require(get_bytes(d,BACKUP)==backup,"canonical backup unexpectedly changed")
        phase="COMPLETED"
        report["status"]="AUDIT_AND_CONTEXT_VERIFIED"
        report["canonical_updated"]=True
        report["canonical_sha256"]=sha(updated)
        report["canonical_size_bytes"]=len(updated)
        report["canonical_backup_unchanged"]=True
    except Exception as exc:
        report["phase"]=phase
        report["error_type"]=type(exc).__name__
        report["error_category"]="failure in read-only inventory or guarded report/context write"
    report["phase"]=phase
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PRE300_STATUS",report["status"])
    print("PRE300_PHASE",phase)
    print("PRE300_ITEMS",report.get("items_catalogued"))
    print("PRE300_FOLDERS",report.get("folders_scanned"))
    print("PRE300_DUP_GROUPS",report.get("probable_duplicate_md5_groups"))
    print("PRE300_REPORT_ID",report.get("audit_report_id"))
    print("PRE300_CANON_VERIFIED",report.get("canonical_updated"))
    print("PRE300_ERROR_TYPE",report.get("error_type"))
    return 0 if report["status"]=="AUDIT_AND_CONTEXT_VERIFIED" else 1
if __name__=="__main__":sys.exit(main())
