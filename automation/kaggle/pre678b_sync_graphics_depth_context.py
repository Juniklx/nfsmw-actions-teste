#!/usr/bin/env python3
"""PRE678B: backup-first, idempotent canonical context append of verified
PRE677 SB-02 V51 existing lazy depth and shadow source audit. Never build APK or alter secrets.
"""
from __future__ import annotations
import hashlib,io,json,os
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/"docs/PRE678_SB02_V51_DEPTH_GRAPHICS_QUALITY_VERIFIED.json"
POLICY=ROOT/"docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json"
OUT=Path("/tmp/nfsmw-pre678b/result.json")
BEFORE_BYTES=1113744
BEFORE_SHA="fbd977b5d05e90b5f9418194a759c826b3f1947d8bf27394230c11d78be6f8ee"
BACKUP_PARENT="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE678B_SB02_EFFECT_QUALITY_20261110.md"
HEADING="# PRE678B — fidelidade grafica, blur e copias depth SpeedBreaker SB-02 (2026-11-10)"
def sha(data):return hashlib.sha256(data).hexdigest()
def checked():
    x=json.loads(PIN.read_text())
    b=json.loads(POLICY.read_text())
    f=x.get("findings",{})
    blur=f.get("radial_blur_disabled_by_default_in_renderer_source",{})
    shadows=f.get("shadow_scale_source_default",{})
    if not (
      x.get("schema")=="nfsmw-pre678-sb02-quality-depth-source-v1"
      and x.get("status")=="AUDIT_OK_AUTHENTIC_V51_DEPTH_STATE_AND_GRAPHICS_QUALITY_SOURCE_ONLY"
      and x.get("github",{}).get("run_id")==42876324398
      and x.get("drive",{}).get("sha256")=="21b05b399053bcc15e5ae8424978a9fd60e5209534ea7a4fd867d6d5cc61e24f"
      and x.get("drive",{}).get("bytes")==252112
      and x.get("drive",{}).get("readback_identical") is True
      and x.get("drive",{}).get("crc_ok") is True
      and x.get("source",{}).get("renderer_v51_sha256")=="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
      and x.get("source",{}).get("backend_v51_sha256")=="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
      and blur.get("defined_default") is True
      and blur.get("line")==195
      and shadows.get("defined_default")==100
      and shadows.get("line")==89
      and f.get("blur_source_default_and_full_effects_requirement_conflict") is True
      and len(f.get("indirect_copy_image_calls",[]))==8
      and x.get("gate",{}).get("no_APK_build") is True
      and x.get("gate",{}).get("no_source_or_shader_modifications") is True
      and b.get("internal",{}).get("version_code")==51
      and b.get("candidates",[{},{}])[1].get("id")=="SB-02"
    ):raise ValueError("PRE678B source fidelity evidence mismatch")
    return {"pre678_verified_pin_sha256":sha(PIN.read_bytes()),
            "speedbreaker_backlog_sha256":sha(POLICY.read_bytes())}
TEXT=f"""

---

{HEADING}

- PRE678 SB-02 AUDITORIA SOMENTE LEITURA APROVADA: GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42876324398, job 130040482718, artifact 13791183670, status completed/success. Replay fonte V51 PRE99+PRE431+PRE638+PRE648 em area temporaria. Hash renderer 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2 e backend b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385; nao comprova equivalencia binaria ELF assinado.
- ALERTA FIDELIDADE: fonte renderer nativo/app/src/nfsmw_nativo_dibujos.cpp linha 195 define nfsmw_nativo_sin_desenfoque = true POR PADRAO. Comentarios 187-198 confirmam REMOCAO do desfoque radial nas bordas quando se acelera e usa NOS, originalmente presente no Xbox 360. Segundo comentario, false conserva o efeito. Essa remocao por default conflita com a meta do usuario de preservar TODOS os efeitos; NAO declarar que o jogo V51 no Galaxy usa efetivamente esse valor sem consultar TOML/runtime. NAO ligar/desligar cvar ou editar shader sem autorizacao e testes.
- SOMBRAS: backend nativo/app/src/nfsmw_nativo_destinos.cpp linha 89 declara nfsmw_nativo_sombras_escala default 100 por cento, sem reduzir escala por padrao. Valor efetivo no jogo continua DESCONHECIDO. Outras flags observadas PRE677: profundidad_perezosa, frontal_perezoso e sombra_minimo true por default; restaurar_por_intercambio false (bug documentado de carro sem sombra). Nao alterar condicoes dessas optimizacoes sem G2 pixels/guest.
- MAQUINA DE ESTADOS E DESFOQUE: renderer 2637-2640 detecta a composicao sem desfoque e chama LecturasDeProfundidadMuertas(true) ao preparar samplers, reverte em 2737-2738. No backend AplazarCopiaProfundidad em 3360-3378 adia so se houver leitura morta recente e nao houver leitura efetiva recente; AntesDeEscribirProfundidad em 3333-3357 grava a copia pendente ou a descarta com guarda de leitura tardia. Assim parte do ganho potencial de eliminar copia de depth depende justamente do desfoque DESLIGADO. O codigo tem fallback, mas esta analise nao prova equivalencia de shaders/pixels ou sincronizacao GPU.
- COPIA VULKAN INDIRETA: backend linhas 915-922 vincula copiar_imagen_ ao vkCmdCopyImage por vkGetDeviceProcAddr e falha Inicializar se faltar. Oito invocacoes indiretas encontradas: linhas 1613,1834,1888,2287,3324,3450,4296,4337. O inventario PRE675 de vkCmd* diretas nao era exaustivo.
- RESULTADO CONSERVADOR: a V51 PRE652 permanece sem mudancas; sem novo patch, APK, shader, alteracao de qualidade, controle, saves, credenciais ou thermal, e sem ganho real de FPS medido. Testes HOST PRE677 eram logicos e nao reproduzem o Vulkan no S24 FE. A auditoria PRE678 NAO mediu CVar efetivo da V51 instalada.
- EVIDENCIAS: Drive ZIP PRE678 https://drive.google.com/file/d/1hMBm2zfsKgPZLm23wb5P-IkjbIS5Lhkw/view (252112 bytes, SHA256 21b05b399053bcc15e5ae8424978a9fd60e5209534ea7a4fd867d6d5cc61e24f, CRC e readback SHA verificados), fonte e report completos no ZIP; pin no repo docs/PRE678_SB02_V51_DEPTH_GRAPHICS_QUALITY_VERIFIED.json.
- PROXIMO PRE679 SB-02: verificar TOML e aplicacao do toggle de desfoque no shader final, e o real valor de sombras_escala; nunca assumir default = runtime. Projetar teste de equiv G2 de depth/blur/sombra sem remocao de efeitos; nao portar literalmente codigo SpeedBreaker sob GPL sem revisao de licenca e adequacao.
- IDENTIDADE PRESERVADA: APK V51 PRE652, versionCode 51, pacote io.github.nfsmwrecomp, SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b; preservar Nitro, BMW, C3, PG9076/touch, 1920x1080, limite maximo 120 FPS, todos os efeitos, fisica, saves e limites termicos.

Status PRE678B: desfoque radial desligado por DEFAULT em fontes V51; efetividade na APK instalada NAO CONFIRMADA, sem mudancas e sem ganho de FPS.
""".encode("utf-8")
def run():
    evidence=checked()
    d=drive_client()
    before=get_bytes(d,FILE_ID)
    meta=get_meta(d)
    mark=HEADING.encode("utf-8")
    if not(meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md" and
      meta.get("parents")==[PARENT] and int(meta.get("size",0))==len(before)):
        raise ValueError("PRE678B canonical file identity mismatch")
    if mark in before:
        if before.count(mark)!=1 or not before.endswith(TEXT) or len(before)-len(TEXT)!=BEFORE_BYTES or sha(before[:-len(TEXT)])!=BEFORE_SHA:
            raise ValueError("PRE678B existing append differs from expected bytes")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,"readback_identical":True,
             "canonical_sha256":sha(before),"canonical_bytes":len(before),**evidence}
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA:
        raise ValueError("PRE678B canonical content changed since PRE677B; fail closed")
    copy=d.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[BACKUP_PARENT]},fields="id,name,size").execute()
    if int(copy.get("size",0))!=BEFORE_BYTES or get_bytes(d,copy["id"])!=before:
        raise ValueError("PRE678B backup readback mismatch")
    if get_meta(d).get("modifiedTime")!=meta.get("modifiedTime") or get_bytes(d,FILE_ID)!=before:
        raise ValueError("PRE678B concurrent edit; no overwrite")
    new=before+TEXT
    d.files().update(fileId=FILE_ID,supportsAllDrives=True,
       media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False),
       fields="id,name,size").execute()
    final=get_bytes(d,FILE_ID)
    if final!=new or final.count(mark)!=1 or not final.startswith(before):
        raise ValueError("PRE678B Drive readback != intended append")
    return {"status":"AUDIT_OK","backup_created":True,"backup_id":copy["id"],
        "readback_identical":True,"canonical_sha256":sha(final),"canonical_bytes":len(final),
        "history_preserved":True,**evidence}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=run()
    except Exception as exc:
        result={"status":"FAILED_CLOSED","error_type":type(exc).__name__,
            "error_summary":str(exc)[:300] if isinstance(exc,ValueError) else "Drive API/transport error"}
    result.update({"stage":"PRE678B_SB02_GRAPHICS_DEPTH_CANONICAL_CONTEXT",
      "utc":datetime.now(timezone.utc).isoformat(),
      "github_run_id":int(os.environ["GITHUB_RUN_ID"]),
      "apk_built":False,"signing_material_accessed":False,"shader_modified":False,
      "external_speedbreaker_code_imported":False,"fps_gain_proven":False})
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    for key in ("status","backup_created","backup_id","canonical_sha256","readback_identical","error_type"):
        print("PRE678B_"+key.upper()+"="+str(result.get(key,"none")))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
