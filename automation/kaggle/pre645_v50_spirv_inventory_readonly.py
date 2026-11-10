#!/usr/bin/env python3
"""PRE645 deterministic read-only V50 signed APK NFSSPV / SPIR-V inventory."""
import argparse
import collections
import csv
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path

APK_SHA="7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe"
APK_BYTES=47104881
PACKS=(
 "assets/nativo/nfsmw_shaders.nfsp",
 "assets/nativo/nfsmw_shaders_gles.nfsp",
 "assets/nativo/usa/nfsmw_shaders.nfsp",
 "assets/nativo/usa/nfsmw_shaders_gles.nfsp",
)
MAGIC=b"\x03\x02\x23\x07"
SELECTED={12:"ext_inst",61:"load",62:"store",87:"image_sample",88:"image_sample_explicit",
 95:"image_fetch",97:"image_read",98:"image_write",129:"fadd",133:"fmul",
 136:"fdiv",246:"loop_merge",247:"selection_merge",250:"branch_conditional"}
def sha(b): return hashlib.sha256(b).hexdigest()

def read_signed_apk(path):
    raw=path.read_bytes()
    provenance={"input_bytes":len(raw),"input_sha256":sha(raw)}
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip() is not None: raise ValueError("PRE638 artifact CRC mismatch")
            if sorted(n for n in z.namelist() if n.endswith(".apk")) != ["nfsmw-v50-c3-diagnostic-verified.apk"]:
                raise ValueError("Unexpected APK files in PRE638 artifact")
            if "pre638-v50-report.json" not in z.namelist():
                raise ValueError("PRE638 report missing")
            report=json.loads(z.read("pre638-v50-report.json"))
            if report.get("status")!="PRE638_V50_SIGNED_DIAGNOSTIC_VERIFIED":
                raise ValueError("PRE638 release unverified")
            apk=z.read("nfsmw-v50-c3-diagnostic-verified.apk")
    elif path.suffix.lower()==".apk":
        apk=raw
    else:
        raise ValueError("Input must be .zip or .apk")
    if len(apk)!=APK_BYTES or sha(apk)!=APK_SHA:
        raise ValueError("Signed V50 APK hash/size mismatch")
    return apk,provenance

def inspect_module(data,offset,number):
    if offset+20>len(data): raise ValueError("Truncated SPIR-V header")
    magic,version,generator,bound,schema=struct.unpack_from("<5I",data,offset)
    if magic!=0x07230203 or not 0x10000<=version<=0x10600 or bound<=1 or schema:
        raise ValueError("Invalid SPIR-V header")
    p=offset+20
    ops=collections.Counter()
    stages=[]
    while p+4<=len(data):
        head,=struct.unpack_from("<I",data,p)
        wc,opcode=head>>16,head&65535
        if wc==0 or opcode==0 or p+4*wc>len(data): break
        if opcode==15:
            if wc<4: raise ValueError("Malformed OpEntryPoint")
            stage,=struct.unpack_from("<I",data,p+4)
            stages.append(stage)
        ops[opcode]+=1
        p+=4*wc
        if sum(ops.values())>250000: raise ValueError("Excessive SPIR-V instructions")
    if len(stages)!=1 or stages[0] not in (0,4) or ops[56]<1:
        raise ValueError("SPIR-V module missing expected stage or function end")
    return {
       "module":number,"offset":offset,"bytes":p-offset,"sha256":sha(data[offset:p]),
       "stage":"vertex" if stages[0]==0 else "fragment",
       "instructions":sum(ops.values()),
       **{name:ops[op] for op,name in SELECTED.items()}
    },p

def inspect_pack(name,data):
    if data[:8]!=b"NFSSPV\0\0" or len(data)<32: raise ValueError("Unexpected NFSSPV magic")
    version,declared=struct.unpack_from("<2I",data,8)
    offsets=[]
    p=0
    while (p:=data.find(MAGIC,p))>=0:
        if p%4: raise ValueError("Unaligned SPIR-V")
        offsets.append(p);p+=4
    if len(offsets)!=declared or not 0<declared<10000:
        raise ValueError("NFSSPV module count inconsistent with observed magic")
    rows=[]
    for i,start in enumerate(offsets):
        row,end=inspect_module(data,start,i)
        if i+1<len(offsets) and end>=offsets[i+1]:
            raise ValueError("Overlapping SPIR-V modules")
        rows.append({"pack":name,**row})
    c=collections.Counter(row["stage"] for row in rows)
    return ({
       "name":name,"bytes":len(data),"sha256":sha(data),"archive_version":version,
       "declared_modules":declared,"detected_modules":len(rows),
       "vertex":c["vertex"],"fragment":c["fragment"],
       "unique_module_hashes":len({r["sha256"] for r in rows}),
       "total_static_instructions":sum(r["instructions"] for r in rows),
       "top_by_static_instructions":[
          {"module":r["module"],"stage":r["stage"],"instructions":r["instructions"],"sha256":r["sha256"]}
          for r in sorted(rows,key=lambda r:(-r["instructions"],r["module"]))[:8]
       ]
    },rows)

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    a=parser.parse_args()
    apk,provenance=read_signed_apk(a.input)
    out={"stage":"PRE645_V50_GPU_SPIRV_READONLY","status":"AUDIT_OK",
      "reference":"PRE638 signed V50","apk_sha256":APK_SHA,"apk_size":APK_BYTES,
      "origin_run":42748358853,"origin_artifact_id":13733586196,
      "source_modified":False,"shader_modified":False,"apk_built":False,
      "fps_gain_verified":False,"per_shader_runtime_cost_verified":False,
      "note":"Static module instruction count does not measure shader cost, frequency, or runtime GPU hotspots.",
      "input":provenance,"packs":[]}
    rows=[]
    with zipfile.ZipFile(io.BytesIO(apk)) as z:
        if z.testzip() is not None:raise ValueError("APK CRC failure")
        found=sorted(n for n in z.namelist() if n.endswith(".nfsp"))
        if found!=sorted(PACKS):raise ValueError("APK NFSSPV layout changed")
        for n in PACKS:
            pack,entries=inspect_pack(n,z.read(n))
            out["packs"].append(pack);rows.extend(entries)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"PRE645_V50_SPIRV_READONLY.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (a.output_dir/"PRE645_V50_SPIRV_MODULES.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    text=["# PRE645 - Inventário SPIR-V real da APK V50","",
      "**Resultado: AUDIT_OK.** Leitura somente; nenhum código, shader ou APK modificado.",
      "",
      f"APK SHA-256: \`{APK_SHA}\`", "",
      "| Pacote | Bytes | Módulos | Vertex | Fragment | Binários únicos | Instruções estáticas |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for x in out["packs"]:
        text.append(f"| \`{x['name']}\` | {x['bytes']} | {x['detected_modules']} | {x['vertex']} | {x['fragment']} | {x['unique_module_hashes']} | {x['total_static_instructions']} |")
    text += ["","## Próximo gate e limitações", "",
      "A contagem estática de instruções e os módulos repetidos **não** permitem identificar shaders caros em tempo real nem afirmar redundância de execução na GPU.",
      "O custo GPU da PRE641 era agregado por passe; ainda falta associar módulo SPIR-V e VkPipeline aos passes cena, pós-processamento, reflexos e sombras.",
      "Próxima etapa: auditoria read-only do código gerador e associação pipeline/pass antes de propor uma alteração SPIR-V isolada; validar equivalência visual e custo em cenário controlado.",
      "PRE643 C3 e fluidez permanecem suspensas; guardas C3 preservados; V50 é baseline, sem otimização comprovada."]
    (a.output_dir/"RELATORIO_PRE645_V50_SPIRV_READONLY.md").write_text("\n".join(text)+"\n",encoding="utf-8")
    print("PRE645_STATUS=AUDIT_OK")
    print("PRE645_APK_SHA256="+APK_SHA)
    for x in out["packs"]:
        print("PRE645_PACK="+x["name"]+" modules="+str(x["detected_modules"])+
            " unique="+str(x["unique_module_hashes"])+
            " vertex="+str(x["vertex"])+" fragment="+str(x["fragment"]))
    print("PRE645_APK_BUILT=false")
    print("PRE645_FPS_GAIN_VERIFIED=false")
if __name__=="__main__":
    try:run()
    except Exception as e:
        print("PRE645_STATUS=FAILED",file=sys.stderr)
        print("PRE645_ERROR="+type(e).__name__+": "+str(e),file=sys.stderr)
        raise
