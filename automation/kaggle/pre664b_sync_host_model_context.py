#!/usr/bin/env python3
"""PRE664B: fail-closed append of verified host-only gate to canonical Drive MD."""
import argparse,hashlib,io,json,zipfile,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

BEFORE_BYTES=1068911
BEFORE_SHA="c6f7e933cc87c72057c5387d444ed712ea813d3493b841a6991f7d297925f600"
ZIP_ID="1HJTbTOQ4FWei1gk3RUjZuwXJD5sHBhbo"
ZIP_SHA="3036894e00d32f51152afe85ddb62614a3697bbda81ba9b22d6beecbe549b9d1"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE664B_HOST_MODEL_20261110.md"
MARKER="# PRE664B — Host model de amostragem GPU limitada".encode("utf-8")
OUT=Path("/tmp/nfsmw-pre664b/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

APPEND="""

---

# PRE664B — Host model de amostragem GPU limitada (2026-11-10)

- **Base:** PRE662/PRE663 verificaram fonte do C2 Vulkan com 128 timestamps por slot, ponteiros de escrita/leitura e leitura apos fence. PRE656 V51 registrou >=2.186.797 desenhos do par p2 VS62 PS58 (tops parciais); PRE658 estabeleceu que p2 corresponde a cena. Quantidade de draws NAO prova tempo GPU individual.
- **PRE664 HOST-ONLY aprovada:** GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42831540098, job 129882575040, completed/success, PRE664_HOST_MODEL_TEST=PASS, PRE664_STATUS=HOST_MODEL_PASS_NO_VULKAN_INJECTION. Model C++17 estrito e ASan/UBSan em automation/kaggle/pre664_bounded_burst_sampler.h e pre664_bounded_burst_host_test.cpp. O job comparou relatorios PRE662/PRE658 existentes e NAO repetiu a autenticacao PRE99.
- **Contrato testado no host:** default OFF, amostra blocos contiguos de p2 VS62 PS58, maximo 4 blocos / 8 indices de consulta por slot, pool separado APENAS PLANEJADO, sem alterar o pool C2. Fecha bloco na troca de shader e no fim do command buffer, recusa reuso se chamador informar fence incompleta, exclui ceu adiado. O prototipo NAO consulta fence real, NAO cria query pool Vulkan, NAO executa cmd timestamp, NAO foi ligado ao motor.
- **Evidencia autenticada no Drive:** https://drive.google.com/file/d/1HJTbTOQ4FWei1gk3RUjZuwXJD5sHBhbo/view, NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE664_HOST_MODEL_AND_LOG_42831540098.zip, tamanho 1329 bytes, SHA256 3036894e00d32f51152afe85ddb62614a3697bbda81ba9b22d6beecbe549b9d1, ZIP CRC integro, mesmo bytes do artefato GitHub 13772296035 na leitura de retorno do Drive.
- **Limites:** benchmark host CPU desativado nao mede overhead real Vulkan, frametime, stutter ou FPS no Galaxy S24 FE. Vies de selecao das primeiras quatro amostras ainda nao quantificado. Sem fonte ARM64 compilada nova, sem APK V52, shader modificado, patch de C2, save, credencial, assinatura ou mudanca termica. V51 segue baseline autentica e instalada apenas na medida sustentada pelos logs PRE656; versionCode instalado nao foi independentemente lido.
- **PRE665 proxima:** auditar pontos reais de insercao Vulkan e sequencia de slots/fences, validar pool separado, overhead e bias, e realizar ARM64 noAPK com default OFF antes de qualquer APK de medicao no aparelho. Preservar 1920x1080, graficos, shaders, fisica, PG-9076/touch, Nitro PRE398, BMW, guards C3, assinatura permanente e protecoes termicas. Prioridade shaders/GPU; fluidez/SurfaceFlinger e C3 PRE643 continuam suspensos ate decisao posterior.

**Status PRE664B:** modelo host e log verificados; custo GPU do par VS62/PS58 ainda nao medido; ganho FPS NAO comprovado.
"""

def validate_zip(drive):
    z=get_bytes(drive,ZIP_ID)
    if len(z)!=1329 or sha(z)!=ZIP_SHA:raise ValueError("PRE664B evidence ZIP hash/size differs")
    with zipfile.ZipFile(io.BytesIO(z)) as f:
        if f.testzip() is not None or set(f.namelist())!={"PRE664_HOST_MODEL_REPORT.json","host_test.log"}:
            raise ValueError("PRE664B bad artifact ZIP contents or CRC")
        d=json.loads(f.read("PRE664_HOST_MODEL_REPORT.json"))
        log=f.read("host_test.log").decode("utf-8")
    if not (d.get("github_run_id")==42831540098
      and d.get("status")=="HOST_MODEL_PASS_NO_VULKAN_INJECTION"
      and d.get("github_commit")=="225298ba9dbfe433578b7bca1448fe9bb398a995"
      and d.get("model",{}).get("default_enabled") is False
      and d.get("model",{}).get("max_contiguous_bursts_per_slot")==4
      and d.get("model",{}).get("dedicated_query_capacity_per_slot")==8
      and d.get("verification",{}).get("asan_ubsan_host") is True
      and d.get("verification",{}).get("strict_host_cpp17") is True
      and all(d.get(k) is False for k in ("apk_built","native_arm64_built","vulkan_commands_injected","fps_gain_proven","signing_material_accessed","game_saves_modified"))
      and "PRE664_HOST_MODEL_TEST=PASS" in log
      and "PRE664_C2_POOL_MODIFIED=false" in log):
        raise ValueError("PRE664B host report invalid")

def update():
    drive=drive_client();validate_zip(drive)
    appendix=APPEND.encode("utf-8")
    if appendix.count(MARKER)!=1:raise ValueError("PRE664B duplicated appendix heading")
    meta=get_meta(drive)
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
           and meta.get("mimeType")=="text/markdown" and meta.get("parents")==[PARENT]):
        raise ValueError("PRE664B canonical identity mismatch")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):raise ValueError("PRE664B metadata inconsistent")
    if MARKER in before:
        if not(before.count(MARKER)==1 and before.endswith(appendix)
          and len(before)-len(appendix)==BEFORE_BYTES and sha(before[:-len(appendix)])==BEFORE_SHA):
            raise ValueError("PRE664B conflicting prior appendix")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
                "canonical_sha256":sha(before),"canonical_bytes":len(before),"readback_identical":True}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA or before.count(b"# PRE663 ")!=1:
        raise ValueError("PRE664B Drive context changed; abort without writing")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},fields="id,name,size").execute()
    bid=backup["id"]
    if int(backup.get("size",-1))!=BEFORE_BYTES or get_bytes(drive,bid)!=before:
        raise ValueError("PRE664B backup not byte identical")
    if get_meta(drive).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(drive,FILE_ID)!=before:
        raise ValueError("PRE664B concurrent context edit")
    for i in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE664B changed during update")
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
              media_body=MediaIoBaseUpload(io.BytesIO(target),mimetype="text/markdown",resumable=False),
              fields="id,name,size").execute()
        except HttpError as exc:
            if exc.resp.status not in (500,502,503,504) or i==2:raise
            if get_bytes(drive,FILE_ID)==target:break
            time.sleep(2*(i+1))
    after=get_bytes(drive,FILE_ID)
    if not(after==target and after.startswith(before) and after.count(MARKER)==1):
        raise ValueError("PRE664B Drive readback mismatch; backup retained")
    return {"status":"AUDIT_OK","backup_created":True,"backup_file_id":bid,
        "canonical_sha256":sha(after),"canonical_bytes":len(after),
        "readback_identical":True,"history_prefix_unchanged":True}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    args=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=update()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,
        "error_summary":str(e)[:180] if isinstance(e,ValueError) else "Drive API failure"}
    r.update({"stage":"PRE664B_HOST_MODEL_CONTEXT","run_id":args.run_id,
     "utc":datetime.now(timezone.utc).isoformat(),
     "apk_built":False,"signing_accessed":False,"saves_modified":False})
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    for k in ("status","backup_created","backup_file_id","canonical_sha256","readback_identical","error_type"):
        print("PRE664B_"+k.upper()+"="+str(r.get(k,"none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
