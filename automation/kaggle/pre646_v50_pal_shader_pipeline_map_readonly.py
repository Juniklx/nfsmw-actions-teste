#!/usr/bin/env python3
"""PRE646: authenticated signed V50 NFSSPV index -> C6 logged VS/PS pairs, read-only."""
import argparse
import csv
import ctypes
import ctypes.util
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path

APK_SHA="7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe"
APK_SIZE=47104881
LOG_SHA="4fea4a354badd3babd46cebda56482b0c33eeb66aa6ec2fa85bc4cde86f05cce"
PACKS={
"PAL_VULKAN":("assets/nativo/nfsmw_shaders.nfsp","b84602ca9bf6efd84f54ad1509297baccd57c04ffcda494c77f5780a433f95a7",152),
"USA_VULKAN":("assets/nativo/usa/nfsmw_shaders.nfsp","8c49de7587c4405a37fe8904981a4902c5294f4e74472dbe3b5d9a643adfa267",150)
}
def hash256(b):return hashlib.sha256(b).hexdigest()

def xxh3(data):
    lib=ctypes.util.find_library("xxhash")
    if not lib:raise RuntimeError("libxxhash unavailable; refusing to bypass integrity checks")
    fn=ctypes.CDLL(lib).XXH3_64bits
    fn.restype=ctypes.c_uint64
    fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    buf=ctypes.create_string_buffer(data)
    return fn(buf,len(data))

def load_pack(z,label):
    name,expected_sha,expected_count=PACKS[label]
    data=z.read(name)
    if hash256(data)!=expected_sha:raise ValueError("Pack SHA mismatch "+label)
    magic,version,count,body_xxh=struct.unpack_from("<8sIIQ",data,0)
    if magic!=b"NFSSPV\0\0" or version!=1 or count!=expected_count:
        raise ValueError("NFSSPV header invalid")
    if xxh3(data[24:])!=body_xxh:raise ValueError("NFSSPV body XXH3 mismatch")
    p=24;entries=[]
    for idx in range(count):
        n,words,original_xxh=struct.unpack_from("<IIQ",data,p);p+=16
        if not 24<=n<=65536 or not 5<=words<=1048576:raise ValueError("Entry length invalid")
        original=data[p:p+n];p+=n
        spv=data[p:p+words*4];p+=words*4
        if len(original)!=n or len(spv)!=words*4 or xxh3(original)!=original_xxh:
            raise ValueError("Original shader XXH3 mismatch")
        signature=int.from_bytes(original[:4],"big")
        if (signature&~1)!=0x102A0E00:raise ValueError("Original shader signature invalid")
        if struct.unpack_from("<I",spv,0)[0]!=0x07230203:raise ValueError("Bad SPIR-V magic")
        stage="VS" if signature&1 else "PS"
        cursor=20;entrypoint=None;instructions=0
        while cursor<len(spv):
            insn=struct.unpack_from("<I",spv,cursor)[0];size=insn>>16;op=insn&65535
            if not size or cursor+size*4>len(spv):raise ValueError("Malformed SPIR-V instruction")
            if op==15:
                if entrypoint is not None:raise ValueError("Multiple entrypoints")
                entrypoint=struct.unpack_from("<I",spv,cursor+4)[0]
            cursor+=size*4;instructions+=1
        if entrypoint!=(0 if stage=="VS" else 4):raise ValueError("Entrypoint stage mismatch")
        entries.append({"id":idx,"stage":stage,"sha256":hash256(spv),"original_xxh3":f"{original_xxh:016x}","instructions":instructions})
    if p!=len(data):raise ValueError("Trailing NFSSPV bytes")
    return entries

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apk",required=True,type=Path)
    ap.add_argument("--sanitized-log",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    arg=ap.parse_args()
    raw=arg.apk.read_bytes()
    if len(raw)!=APK_SIZE or hash256(raw)!=APK_SHA:raise ValueError("Signed V50 APK identity mismatch")
    log=json.loads(arg.sanitized_log.read_text())
    if log.get("original_log_sha256")!=LOG_SHA or log.get("original_log_bytes")!=972111:
        raise ValueError("Sanitized input provenance mismatch")
    if log.get("library_boot")!={"count":152,"vertex":63,"pixel":89}:raise ValueError("Runtime library count mismatch")
    rows=log["pipeline_id_vs_ps"]
    if len(rows)!=64 or [r[0] for r in rows]!=list(range(1,65)):
        raise ValueError("Expected numbered pipeline creation rows 1..64")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:raise ValueError("APK ZIP CRC mismatch")
        packs={key:load_pack(z,key) for key in PACKS}
    counters={}
    for name,p in packs.items():
        good=0
        for index,vs,ps in rows:
            ok=vs<len(p) and p[vs]["stage"]=="VS" and (ps==-1 or (ps<len(p) and p[ps]["stage"]=="PS"))
            if ok:good+=1
        counters[name]=good
    if counters!={"PAL_VULKAN":64,"USA_VULKAN":7}:
        raise ValueError("V50 PAL/USA stage matching regression: "+str(counters))
    p=packs["PAL_VULKAN"]
    output=[]
    for n,vs,ps in rows:
        vertex=p[vs];pixel=p[ps] if ps>=0 else None
        output.append({"pipeline_number":n,"vertex_id":vs,"fragment_id":ps,
            "vertex_spirv_sha256":vertex["sha256"],"fragment_spirv_sha256":pixel["sha256"] if pixel else "",
            "vertex_original_xxh3":vertex["original_xxh3"],
            "fragment_original_xxh3":pixel["original_xxh3"] if pixel else "",
            "vertex_static_instructions":vertex["instructions"],
            "fragment_static_instructions":pixel["instructions"] if pixel else 0})
    arg.output.mkdir(parents=True,exist_ok=True)
    with (arg.output/"PRE646_V50_FIRST64_SHADER_PIPELINE_MAP.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]))
        w.writeheader();w.writerows(output)
    result={"stage":"PRE646_V50_PAL_SPIRV_PIPELINE_STATIC_MAP","status":"AUDIT_OK",
       "original_signed_apk_sha256":APK_SHA,"source_log_sha256":LOG_SHA,
       "pipeline_creations_in_log":64,"pal_stage_valid":64,"usa_stage_valid":7,
       "distinct_vs":len({r[1] for r in rows}),"distinct_ps":len({r[2] for r in rows if r[2]!=-1}),
       "pack_header_body_original_xxh3_verified":True,
       "historical_source_mapping":"EntradaShader.numero = library index i; ClavePipeline vs/ps uses numero+1",
       "mapping_limitation":"Historical source archive is not authenticated as byte-identical V50 source; first 64 pipeline creations are not runtime per-shader draw counts or measured GPU timings.",
       "new_apk_created":False,"source_modified":False,"shaders_modified":False,"fps_gain_verified":False,
       "next_gate":"PRE647 authenticate exact V50 source and acquire per-pass shader runtime associations before any optimization"}
    (arg.output/"PRE646_V50_SPIRV_C6_GATE.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE646_STATUS=AUDIT_OK")
    print("PRE646_PAL_VULKAN="+str(counters["PAL_VULKAN"])+"/64")
    print("PRE646_USA_VULKAN="+str(counters["USA_VULKAN"])+"/64")
    print("PRE646_DISTINCT_VS="+str(result["distinct_vs"]))
    print("PRE646_DISTINCT_PS="+str(result["distinct_ps"]))
    print("PRE646_GPU_TIMING_BY_SHADER=NOT_MEASURED")
    print("PRE646_APK_BUILT=false")
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("PRE646_STATUS=FAILED "+type(e).__name__+": "+str(e),file=sys.stderr)
        raise
