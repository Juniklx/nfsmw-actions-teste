#!/usr/bin/env python3
"""PRE480: append-only, backup-first, exact-readback Google Drive context update.
This step modifies only the canonical project Markdown file, never app/game
saves, signed APK or game assets. Any mismatch leaves a verified backup.
"""
from __future__ import annotations
import argparse, hashlib, io, json
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from pre105_read_settings_source import drive_client

FILE_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
FILE_NAME="CONTEXTO_NFSMW.md"
MARKER="PRE480_BMW_TUNING_DEVELOPMENT_SYNC_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE480_BMW_TUNING_20261108.md"
APPEND="\n\n---\n\n## PRE480_BMW_TUNING_DEVELOPMENT_SYNC_20261108 — continuidade após V48\n\n**Meta solicitada pelo usuário:** implementar tunagem de desempenho real na BMW M3 GTR da carreira, com perfis físicos adequados, compras/garagem e persistência. **O recurso ainda NÃO está habilitado em nenhuma APK.** Manter APK V48 PRE452 como baseline, save \\`MARCEK\\`, Nitro infinito PRE398, controle PG-9076, shaders, física dos demais carros, assinatura release permanente e proteção térmica.\n\n**PRE455:** logs BMW vs Punto da instrumentação V48 PRE447 mostram \\`reason=2\\` nas 16 consultas; BMW (type41) motor0, transmissão0, suspensão0, nitro3, pneus0, freios0, indução0; Punto (type74) 4/4/3/3/3/4/3. Logs, por si sós, não imprimem \\`versionCode=48\\`. Nitro V48 em corrida não foi revalidado, embora marker binário exista.\n**PRE456:** [run 42502772448](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42502772448) confirma três possíveis subrotas internas do reason=2; não identificou individualmente a subrota usada pela BMW.\n**PRE457–PRE464:** levantamento e rastreio de dados originais. \\`NFSMW_PAL.zip\\` e \\`NFSMW.iso\\` no Google Drive do usuário; índice \\`ZDIR.BIN\\` PAL validado, 1390 entradas, catálogo localizou \\`GLOBAL\\\\ATTRIBUTES.BIN\\`. PRE463 decodificou VPAK, uma vault \\`db\\`.\n**PRE465–PRE467:** seções \\`StrE\\`/VLT, 2399 exports; PRE467 [run 42509329234](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509329234) comparou **byte por byte** o \\`GLOBAL\\\\ATTRIBUTES.BIN\\` PAL e USA. Ambos SHA256 \\`9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad\\`. Igualdade limitada a esse recurso.\n**PRE468–PRE472:** 2339 coleções com ponteiros, classes e campos opcionais, porém os arrays \\`UpgradeSpecs\\` nos campos BMW identificados são **ShiftSND/TurboSND de áudio**, não catálogo de peças. Não modificar esses campos para liberar tunagem.\n**PRE473** [run 42510870784](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42510870784): valores originais \\`pvehicle\\` da BMW \\`bmwm3gtr\\` e \\`m3gtre46careerstart\\` são *0/0/0/3/0/0/0* nas sete categorias, confirmando causalmente as contagens da V48; Punto *4/4/3/3/3/4/3*. Os zeros vêm da configuração do disco, não de regressão Android comprovada. Hash coleção \\`bmwm3gtr=0xCD88083F\\`; ainda precisa validar em runtime sua correspondência com o type 41 do carro do usuário.\n**PRE474–PRE476:** arrays e relações de \\`RefSpec\\`: BMW tem 1 referência explícita nas classes engine/transmission/chassis/tires/brakes; Punto tem base e uma adicional \\`0xA6F0F405\\`, presente em seis classes (engine, transmission, chassis, tires, brakes, induction), com herança própria. PRE476 [run 42511463983](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42511463983) \\`AUDIT_OK\\`, 0 alvos ausentes. Esses RefSpec **não equivalem** diretamente a pacotes compráveis nem autorizam copiar peças do Punto.\n**PRE477** [run 42512601096](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42512601096) \\`AUDIT_OK\\`, após corrigir \\`KeyError 'nos'\\` de duas execuções fracassadas. Seis classes físicas possuem layouts BIN íntegros e tamanhos iguais aos headers gerados. Exemplos lidos: BMW \\`MAX_RPM 9500\\`, \\`RED_LINE 8500\\`, \\`FINAL_GEAR 3.85\\`, \\`EBRAKE 850\\`; Punto base \\`7500\\`, \\`6500\\`, \\`3.70\\`, \\`350\\`; Punto derivado \\`7500\\`, \\`6500\\`, \\`2.50\\`, \\`700\\`. Valores brutos, não medição de efeito em corrida. Indução sem base \\`bmwm3gtr\\` localizada, embora existam \\`m3gtre46careerstart\\` e Punto derivado.\n**PRE478** [run 42512969258](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42512969258) \\`AUDIT_OK\\`: validação com relatórios PRE467/473/474/476/477 + **11 testes sintéticos**. Trava seis categorias sem catálogo/peças BMW específicos, preço frontend, física, prova de roundtrip de save e uso exclusivo de save descartável. Nitro protegido. Código \\`automation/kaggle/pre478_bmw_tuning_contract.py\\`; resultado \\`docs/PRE478_BMW_TUNING_FEATURE_OFF_CONTRACT.json\\`.\n**PRE479** [run 42513282234](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42513282234) \\`AUDIT_OK\\`: primeiro componente C++ de guarda da modificação, compilado com Clang e GCC C++17, **14 testes por compilador**; código \\`automation/kaggle/bmw_tuning/pre479_bmw_guard.hpp\\`. Módulo **não integrado ao runtime**, \\`kRuntimeIntegrationProven=false\\`, recusa toda ativação real; não cria APK, nem itens ou alterações de dados.\n\n**Fluxo original frontend verificado por leitura de código** \\`dbalatoni13/nfsmw\\`: \\`CarCustomizeManager::GetNumPackages()\\` chama \\`Physics::Upgrades::GetMaxLevel(ThePVehicle,type)\\`; \\`GetPartPrice()\\` usa \\`UnlockSystem::GetPerfPackageCost\\`; \\`InstallPerfPkg()\\` grava pelo \\`FECustomizationRecord::SetInstalledPhysics\\` e \\`WriteRecordIntoPhysics\\`, revertendo quando a escrita falha. Fonte PC serve de referência estrutural; verificar semântica exata no PAL Xbox antes de conectar hook.\n\n**Próximas ações obrigatórias:** (1) localizar e provar perfis físicos adicionais **específicos da BMW**, tipo/carro correto e seus efeitos; (2) validar o catálogo frontend, compra/receita e persistência com perfil descartável; (3) auditoria C++/ARM64 em ambiente isolado mantendo feature OFF; (4) só depois considerar APK experimental assinada, sem sobrescrever V48 nem save \\`MARCEK\\`. Nunca forçar \\`0->4\\`, nem expor \\`Option title\\`, \\`20/20\\` ou \\`999.999.999\\` como compras válidas.\n\n**Handoff detalhado:** GitHub \\`docs/PRE475_BMW_TUNING_ORIGINAL_LIMITS_AND_REFERENCES_20261108.md\\`, \\`docs/PRE476_BMW_PERFORMANCE_REFERENCES_VERIFIED_HANDOFF_20261108.md\\`, \\`docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json\\`, \\`docs/PRE478_BMW_TUNING_FEATURE_OFF_CONTRACT.json\\`, \\`docs/PRE479_BMW_TUNING_CPP_GUARD_OFF.json\\`.\n"
OUT=Path("/tmp/nfsmw-pre480/report.json")

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def get_bytes(drive,file_id:str)->bytes:
    output=io.BytesIO()
    req=drive.files().get_media(fileId=file_id,supportsAllDrives=True)
    fetch=MediaIoBaseDownload(output,req,chunksize=2*1024*1024)
    finished=False
    while not finished:
        _,finished=fetch.next_chunk(num_retries=3)
    return output.getvalue()

def get_meta(drive):
    return drive.files().get(fileId=FILE_ID,supportsAllDrives=True,
        fields="id,name,mimeType,size,modifiedTime,md5Checksum,parents").execute()

def update(drive):
    metadata=get_meta(drive)
    if (metadata.get("name")!=FILE_NAME or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 600000<int(metadata.get("size",0))<1000000):
        raise ValueError("Unexpected canonical Drive file identity / size / folder")
    before=get_bytes(drive,FILE_ID)
    if int(metadata["size"])!=len(before):
        raise ValueError("Drive metadata size differs from downloaded bytes")
    text=before.decode("utf-8")
    if "PRE454_V48_PRE452_SIGNED_VERIFIED_20261108" not in text:
        raise ValueError("PRE454 expected terminal history missing")
    if MARKER in text:
        return {"status":"ALREADY_APPLIED","original_sha256":sha(before),
                "new_sha256":sha(before),"backup_created":False,"append_bytes":0,
                "canonical_file_id":FILE_ID}
    if not text.rstrip().endswith("Aplicar apenas adendo com verificação integral de leitura e backup."):
        raise ValueError("Unexpected canonical end-of-file content; refusing append")
    addition=APPEND.encode("utf-8")
    after=before+addition
    if not after.startswith(before) or after.count(MARKER.encode())!=1:
        raise ValueError("Append-only byte composition rejected")

    # Pre-update exact backup in same Drive folder, verified through raw readback.
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[PARENT]},
        fields="id,name,size,md5Checksum,parents").execute()
    bid=backup["id"]
    if (int(backup.get("size",0))!=len(before) or
        sha(get_bytes(drive,bid))!=sha(before)):
        raise ValueError("Backup comparison failed; canonical file not changed")
    result={"backup_created":True,"backup_drive_file_id":bid,
            "backup_file_name":BACKUP_NAME,"original_sha256":sha(before),
            "original_bytes":len(before)}
    # Refuse an overwrite if another writer touched the content during backup.
    current_meta=get_meta(drive)
    if (current_meta.get("modifiedTime")!=metadata.get("modifiedTime") or
        sha(get_bytes(drive,FILE_ID))!=sha(before)):
        raise ValueError("Canonical source changed during backup, no update allowed")
    body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False)
    updated=drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
        media_body=body,fields="id,name,mimeType,size,md5Checksum,modifiedTime").execute()
    if updated.get("id")!=FILE_ID:
        raise ValueError("Drive returned unexpected canonical ID")
    final=get_bytes(drive,FILE_ID)
    if final!=after or final[:len(before)]!=before or final.count(MARKER.encode())!=1:
        raise ValueError("Canonical readback mismatch; preserve backup and manually reconcile")
    result.update({"status":"AUDIT_OK","new_sha256":sha(after),
        "append_bytes":len(addition),"new_total_bytes":len(final),
        "file_bytewise_verified":True,"canonical_file_id":FILE_ID})
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE480_CANONICAL_CONTEXT_APPEND_BACKUP_VERIFIED",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:
        report.update(update(drive_client()))
    except Exception as e:
        report.update({"error_type":type(e).__name__,"error":str(e)[:320]})
    report["run_id"]=a.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE480_STATUS",report["status"],flush=True)
    print("PRE480_BACKUP_ID",report.get("backup_drive_file_id","none"),flush=True)
    print("PRE480_READBACK",report.get("file_bytewise_verified",False),flush=True)
    print("PRE480_ERROR",report.get("error","none"),flush=True)
    return 0 if report["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":raise SystemExit(main())
