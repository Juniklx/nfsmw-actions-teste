#!/usr/bin/env python3
"""PRE675B: backup-first, idempotent canonical context append of verified
PRE675 SB-02 AUTHENTIC V51 source-only audit. Never build APK or alter secrets.
"""
from __future__ import annotations
import hashlib,io,json,os
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/"docs/PRE675_SB02_V51_SHADOW_READONLY_VERIFIED.json"
POLICY=ROOT/"docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json"
OUT=Path("/tmp/nfsmw-pre675b/result.json")
BEFORE_BYTES=1101778
BEFORE_SHA="7ac311c4af42aaecca73a2d379a7a0bfd5ea98e94d6af067aec844054fe4c790"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE675B_SB02_SHADOW_SOURCE_20261110.md"
HEADING="# PRE675B — mapa autentico de sombras/depth V51 / SpeedBreaker SB-02 (2026-11-10)"
def sha(data):return hashlib.sha256(data).hexdigest()
def checked():
    x=json.loads(PIN.read_text())
    b=json.loads(POLICY.read_text())
    if not(
      x.get("github_run_id")==42869180941
      and x.get("status")=="AUDIT_OK_AUTHENTIC_V51_SHADOW_SOURCE_CANDIDATE_MAP_ONLY"
      and x.get("drive_zip_sha256")=="d3dd6df8794f6a7b1cb16546a07a6e7463bb1e4b281508529667bfdaeae31069"
      and x.get("drive_zip_bytes")==28240
      and x.get("zip_crc_ok") is True and x.get("drive_readback_identical") is True
      and x.get("source",{}).get("renderer_v51_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and x.get("source",{}).get("backend_v51_sha256")=="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
      and x.get("lexical_sites",{}).get("renderer",{}).get("shadow_and_depth")==211
      and x.get("lexical_sites",{}).get("backend",{}).get("shadow_and_depth")==187
      and x.get("limits",{}).get("apk_built") is False
      and x.get("limits",{}).get("shadow_lend_implemented") is False
      and b.get("internal",{}).get("version_code")==51
      and b.get("candidates",[{},{}])[1].get("id")=="SB-02"
    ):raise ValueError("PRE675B verified PIN, candidate or release baseline mismatch")
    return {"pre675_verified_pin_sha256":sha(PIN.read_bytes()),
            "speedbreaker_backlog_sha256":sha(POLICY.read_bytes())}
TEXT=f"""

---

{HEADING}

- GATE **PRE675 SB-02 APROVADO**: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42869180941, job 130015521430, status completed/success, PRE675_STATUS=AUDIT_OK_AUTHENTIC_V51_SHADOW_SOURCE_CANDIDATE_MAP_ONLY. Programa automation/kaggle/pre675_sb02_v51_shadow_depth_resolve_readonly.py. Duas primeiras execucoes 42868619512 / 42868904937 falharam FECHADAS por assert de nomes de campos PRE668 e contrato sha_file; nenhuma alterou fonte, APK ou backup. A terceira corrigida passou.
- FONTE AUTENTICADA: replay isolado PRE99 + PRE431 + PRE638 + PRE648. PRE99 SHA256 af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39; V51 renderer antes do PRE648 1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92, apos PRE648 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2; backend b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385. Replay nao comprova byte-identidade do ELF assinado da V51.
- INVENTARIO SOMENTE LEXICAL / NAO EXECUTADO: nativo/app/src/nfsmw_nativo_dibujos.cpp contem 72 correspondencias de termos shadow, 139 de depth, 1 chamada de copia/resolve/blit Vulkan (linha ~9770), 15 referencias a layout/barrier, 2 referencias a formatos depth/stencil. nativo/app/src/nfsmw_nativo_destinos.cpp contem 61 shadow, 126 depth, 2 chamadas de copia/resolve/blit (linhas ~5543 e ~5667), 41 referencias a layout/barrier, 17 a formatos depth/stencil. Somando termos: 211 renderer e 187 backend. Sao ocorrencias regex no texto, NAO quantidade de mapas de sombra, operacoes por frame nem gargalo confirmado.
- EVIDENCIA PRESERVADA: zip PRE675 no Google Drive https://drive.google.com/file/d/14D-uUcpZ6vdPPSMOtCYQOv2eGvuVxx_3/view, 28240 bytes, SHA256 d3dd6df8794f6a7b1cb16546a07a6e7463bb1e4b281508529667bfdaeae31069, CRC e SHA do readback identicos. Resumo autenticado versionado no GitHub docs/PRE675_SB02_V51_SHADOW_READONLY_VERIFIED.json. Artifact GitHub 13788497145.
- HIPOTESE SB-02 SpeedBreaker: futuro resolve de shadow/depth adiado poderia economizar trafego de memoria sem reduzir sombras, SOMENTE se formato, mip/layer/extent, layout, vida da imagem, consumidores guest/CPU, invalidacoes, barriers e equivalencia visual/memoria forem comprovados. O inventario NAO demonstrou que as tres chamadas localizadas sao resolvers de sombras, nem que o jogo tolera atraso. NENHUM codigo externo foi copiado, pools Vulkan nao foram ativados, nao ha medicoes reais de GPU/sombras ou ganho FPS comprovado.
- PROXIMO PRE676 SB-02: rastrear consumidor da memoria guest e VkImage/VkFormat/extent, barreiras, lifecycle de cada copia nas linhas indicadas, comparando semantica com SpeedBreaker apenas como referencia; manter READ ONLY, se inseguro rejeitar. Em paralelo PRE673 headers GPU continuam default OFF e per-pass timestamps reais no S24 FE aguardam probe de capacidades; PRE643/fluidez permanecem pausados.
- INVARIANTES: ultima APK V51 PRE652, versionCode 51, io.github.nfsmwrecomp, SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Preservar Nitro, BMW, C3, touch/iPega PG-9076, saves, 1920x1080, graficos completos, efeitos, sombras, shaders, fisica, protecoes termicas. Nao gerar V52 sem novos gates e autorizacao.

Status PRE675B: G1 mapa de candidatos SB-02 comprovado, G2 equivalencia e G4 GPU fisica nao realizados; nenhuma melhoria aplicada ou medida.
""".encode("utf-8")
def run():
    evidence=checked()
    d=drive_client()
    before=get_bytes(d,FILE_ID)
    meta=get_meta(d)
    mark=HEADING.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md" and
      meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE675B canonical file identity mismatch")
    if mark in before:
        if before.count(mark)!=1 or not before.endswith(TEXT) or len(before)-len(TEXT)!=BEFORE_BYTES or sha(before[:-len(TEXT)])!=BEFORE_SHA:
            raise ValueError("PRE675B existing append differs from expected bytes")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,"readback_identical":True,
             "canonical_sha256":sha(before),"canonical_bytes":len(before),**evidence}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA:
        raise ValueError("PRE675B canonical content changed since PRE674B; fail closed")
    copy=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(copy.get("size",0))!=BEFORE_BYTES or get_bytes(d,copy["id"])!=before:
        raise ValueError("PRE675B backup readback mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE675B concurrent edit; no overwrite")
    new=before+TEXT
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
       media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False),
       fields="id,name,size").execute()
    final=get_bytes(d,FILE_ID)
    if final!=new or final.count(mark)!=1 or not final.startswith(before):
        raise ValueError("PRE675B Drive readback != intended append")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":copy["id"],
        "readback_identical":True,"canonical_sha256":sha(final),"canonical_bytes":len(final),
        "history_preserved":True,**evidence}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=run()
    except Exception as exc:
        result={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
            "error_summary":str(exc)[:300] if isinstance(exc,ValueError) else "Drive API/transport error"}
    result.update({"stage":"PRE675B_SB02_SHADOW_READONLY_CANONICAL_CONTEXT",
      "utc":datetime.now(timezone.utc).isoformat(),
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "apk_built":False,"signing_material_accessed":False,"shader_modified":False,
      "external_speedbreaker_code_imported":False,"fps_gain_proven":False})
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE675B_"+key.upper()+"="+str(result.get(key,"none")))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
