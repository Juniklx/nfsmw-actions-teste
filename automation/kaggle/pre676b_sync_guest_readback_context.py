#!/usr/bin/env python3
"""PRE676B: backup-first, idempotent canonical context append of verified
PRE675 SB-02 AUTHENTIC V51 source-only audit. Never build APK or alter secrets.
"""
from __future__ import annotations
import hashlib,io,json,os
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/"docs/PRE676_SB02_V51_GUEST_READBACK_TRACE_VERIFIED.json"
POLICY=ROOT/"docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json"
OUT=Path("/tmp/nfsmw-pre676b/result.json")
BEFORE_BYTES=1105324
BEFORE_SHA="634818910fab3b236e8dba12aa07f3ec5e21d1e6a59f1ec731080b4cd038413b"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE676B_SB02_READBACK_20261110.md"
HEADING="# PRE676B — rastreio autenticado Vulkan readback / guest V51 SB-02 (2026-11-10)"
def sha(data):return hashlib.sha256(data).hexdigest()
def checked():
    x=json.loads(PIN.read_text())
    b=json.loads(POLICY.read_text())
    if not (
       x.get("status")=="AUDIT_OK_AUTHENTIC_V51_COPY_READBACK_SOURCE_TRACE_ONLY"
       and x.get("github",{}).get("run_id")==42871368565
       and x.get("drive",{}).get("sha256")=="5eb8bceae7f048e05bf9a26461aa4ddd0567374819b1be7915d8505f59cbb49d"
       and x.get("drive",{}).get("bytes")==71801
       and x.get("drive",{}).get("zip_crc_ok") is True
       and x.get("drive",{}).get("readback_sha_match") is True
       and x.get("source",{}).get("renderer_v51_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
       and x.get("source",{}).get("backend_v51_sha256")=="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
       and x.get("backend_queue",{}).get("guest_write_call_line")==5717
       and x.get("limits",{}).get("no_apk") is True
       and x.get("limits",{}).get("no_safe_to_defer_conclusion") is True
       and b.get("internal",{}).get("version_code")==51
       and b.get("candidates",[{},{}])[1].get("id")=="SB-02"
    ):raise ValueError("PRE676B verified pin or SB-02 plan differs")
    return {"pre676_verified_pin_sha256":sha(PIN.read_bytes()),
            "speedbreaker_backlog_sha256":sha(POLICY.read_bytes())}
TEXT=f"""

---

{HEADING}

- GATE PRE676 SB-02 APROVADO: GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42871368565, job 130023187562, artifact 13789656935, status completed/success. Script automation/kaggle/pre676_sb02_v51_copy_readback_guest_source.py recompilou NENHUM arquivo e reconstruiu fonte V51 PRE99->PRE431->PRE638->PRE648 em direitorio TEMP com SHA renderer 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2 e backend b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385. O ELF assinado V51 nao foi comparado byte a byte.
- RESULTADO FONTE V51 / COPIAS: renderer nativo/app/src/nfsmw_nativo_dibujos.cpp linha 9770 GrabarCopiaTextura grava vkCmdCopyBufferToImage do buffer subida_ para imagem de textura por mip/layer (aspect COLOR), NAO resolve shadow guest. Backend nativo/app/src/nfsmw_nativo_destinos.cpp linha 5543 usa vkCmdCopyImageToBuffer em rotina Volcar, com codigo de arquivo PNG e possivel depth; este e um caminho de diagnostico, nao prova de overhead normal. Backend linha 5667 usa vkCmdCopyImageToBuffer da textura resuelta, subrecurso aspect COLOR, e enfileira o destino reg.rb_copy_dest_base, pitch e info em lecturas_pendientes_ (linhas 5669-5671).
- CONSUMO MEMORIA GUEST EXISTENTE: backend em 5193-5195 move lecturas_pendientes_ para ranura de submissao; rotina EscribirLecturas em 5682-5723, usada apos conclusao GPU, invalida memoria mapeada nao coerente em 5715 e chama EscribirTexelsEnGuest(memoria_->TranslatePhysical(0), ..., p.base, ...) em 5717-5718. Fence de ranura em 4939; esta leitura de fonte NAO demonstra ausencia de race em driver, nem sua frequencia de execucao. A escrita guest tem semantica observavel; nao adiar arbitrariamente.
- ACHADO DE ALTO VALOR: o proprio backend V51 faz referencia a CopiarProfundidad(reg,...), linha 1420, e mostra texto de copie de profundidade APLAZADA (adiada) com mapa pendientes_ em 1421-1426. Assim, o motor PARECE JA TER um mecanismo proprio de deferred depth copy; a PRE676 NAO demonstrou sua politica integral, condicoes de validade, custo ou equivalencia. Nao portar cegamente shadow_lend.h do SpeedBreaker; primeiro auditar implementacao ja existente.
- PROVA ARQUIVADA: Drive https://drive.google.com/file/d/12ckHtjYME6_g2PuAHH-S5ftFYBhJh4s5/view, ZIP 71801 bytes, SHA256 5eb8bceae7f048e05bf9a26461aa4ddd0567374819b1be7915d8505f59cbb49d, CRC e readback SHA verificados. Dados completos (trechos e linhas) no JSON do ZIP; evidencia de resumo pinada em docs/PRE676_SB02_V51_GUEST_READBACK_TRACE_VERIFIED.json.
- LIMITES: inventario lexical e revisao de fonte, NAO teste Vulkan no Galaxy S24 FE, NAO proveu que todos os resolves do jogo sejam essas 3 chamadas, NAO mediu chamadas por quadro, tempo GPU ou FPS; sem novos shaders, API, codigo externo, recursos, saves, APK ou assinaturas.
- PROXIMO PRE677 SB-02: auditar em detalhe CopiarProfundidad e pendientes_ e mecanismo RecogerEnlaces, confirmar format D24S8, extent, owner, invalidacoes e dependencias de leitura guest/CPU em fontes autenticadas; executar host tests com casos negativos ANTES de qualquer patch de otimizacao. SB-01 timestamps/per-pass Vulkan permanecem desligados e nao testados no GPU real.
- RELEASE INALTERADA: V51 PRE652, versionCode 51, pacote io.github.nfsmwrecomp, APK SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, certificado de release permanente 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Preservados Nitro PRE398, BMW, C3 PRE194/PRE635, toque/PG-9076, arquivos de jogo/saves, shaders, sombras, efeitos, fisica, 1920x1080, alvo maximo 120 FPS e limites termicos. SurfaceFlinger/fluidez e PRE643 continuam pausados.

Status PRE676B: Fonte e consumidor de copia guest encontrados; beneficio de adiamento shadow NAO comprovado, nenhuma nova APK ou FPS ganho.
""".encode("utf-8")
def run():
    evidence=checked()
    d=drive_client()
    before=get_bytes(d,FILE_ID)
    meta=get_meta(d)
    mark=HEADING.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md" and
      meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE676B canonical file identity mismatch")
    if mark in before:
        if before.count(mark)!=1 or not before.endswith(TEXT) or len(before)-len(TEXT)!=BEFORE_BYTES or sha(before[:-len(TEXT)])!=BEFORE_SHA:
            raise ValueError("PRE676B existing append differs from expected bytes")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,"readback_identical":True,
             "canonical_sha256":sha(before),"canonical_bytes":len(before),**evidence}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA:
        raise ValueError("PRE676B canonical content changed since PRE675B; fail closed")
    copy=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(copy.get("size",0))!=BEFORE_BYTES or get_bytes(d,copy["id"])!=before:
        raise ValueError("PRE676B backup readback mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE676B concurrent edit; no overwrite")
    new=before+TEXT
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
       media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False),
       fields="id,name,size").execute()
    final=get_bytes(d,FILE_ID)
    if final!=new or final.count(mark)!=1 or not final.startswith(before):
        raise ValueError("PRE676B Drive readback != intended append")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":copy["id"],
        "readback_identical":True,"canonical_sha256":sha(final),"canonical_bytes":len(final),
        "history_preserved":True,**evidence}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=run()
    except Exception as exc:
        result={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
            "error_summary":str(exc)[:300] if isinstance(exc,ValueError) else "Drive API/transport error"}
    result.update({"stage":"PRE676B_SB02_GUEST_READBACK_SOURCE_CANONICAL_CONTEXT",
      "utc":datetime.now(timezone.utc).isoformat(),
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "apk_built":False,"signing_material_accessed":False,"shader_modified":False,
      "external_speedbreaker_code_imported":False,"fps_gain_proven":False})
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE676B_"+key.upper()+"="+str(result.get(key,"none")))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
