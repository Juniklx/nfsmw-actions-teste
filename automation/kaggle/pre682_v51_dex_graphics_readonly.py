#!/usr/bin/env python3
"""PRE682: verify signed V51 APK Dalvik bytecode anchors, no game modifications.
Presence/call co-location is NOT full data-flow nor proof of live device settings.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
import os
import struct
import tempfile
import zipfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

APK_ID = "1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws"
APK_SHA256 = "207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
APK_BYTES = 47104417
PRIVATE_LOG_FOLDER = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MOTOR = "Lio/github/nfsmwrecomp/MotorNativo;"
PREFS = "Lio/github/nfsmwrecomp/Ajustes;"
MOTOR_ARGS = (
    "--nfsmw_resolucion_interna=", "--nfsmw_limite_fps=",
    "--nfsmw_nativo_sin_desenfoque=", "--nfsmw_nativo_pcf_barato=",
    "--nfsmw_sombras_sin_vegetacion=", "--nfsmw_nativo_sombras_escala=",
    "--nfsmw_sombras_corte=", "--nfsmw_cubemap_caras_max=",
    "--nfsmw_reflejo_carretera=", "--nfsmw_resplandor_cielo=",
)
PREFS_METHODS = {
    "desenfoque": ("desenfoque", "getBoolean"),
    "calidadSombras": ("calidad_sombras", "getString"),
    "sombrasEscala": ("sombras_escala", "getInt"),
    "sombrasCorte": ("sombras_corte", "getInt"),
    "limiteFps": ("limite_fps", "getInt"),
    "resolucionInterna": ("resolucion_interna", "getString"),
}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def u2(data, off):
    return struct.unpack_from("<H", data, off)[0]

def u4(data, off):
    return struct.unpack_from("<I", data, off)[0]

def uleb(data, off):
    value=0
    for shift in range(0, 35, 7):
        byte=data[off]
        off+=1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, off
    raise ValueError("PRE682_INVALID_ULEB128")

class Dex:
    def __init__(self, data: bytes):
        if data[:4]!=b"dex\n" or data[7]!=0 or len(data)<112:
            raise ValueError("PRE682_BAD_DEX_HEADER")
        if u4(data, 32)!=len(data):
            raise ValueError("PRE682_DEX_SIZE_MISMATCH")
        self.data=data
        ssize,so=u4(data,0x38),u4(data,0x3c)
        tsize,to=u4(data,0x40),u4(data,0x44)
        msize,mo=u4(data,0x58),u4(data,0x5c)
        csize,co=u4(data,0x60),u4(data,0x64)
        self.strings=[]
        for i in range(ssize):
            begin=u4(data,so+4*i)
            _,p=uleb(data,begin)
            end=data.index(b"\x00",p)
            self.strings.append(data[p:end].decode("utf-8","replace"))
        self.types=[self.strings[u4(data,to+4*i)] for i in range(tsize)]
        self.methods=[(self.types[u2(data,mo+8*i)],self.strings[u4(data,mo+8*i+4)]) for i in range(msize)]
        self.classes={}
        for i in range(csize):
            pos=co+32*i
            cls=self.types[u4(data,pos)]
            if cls not in (MOTOR,PREFS):
                continue
            p=u4(data,pos+24)
            sizes=[]
            for _ in range(4):
                n,p=uleb(data,p)
                sizes.append(n)
            for _ in range(sizes[0]+sizes[1]):
                _,p=uleb(data,p)
                _,p=uleb(data,p)
            compiled={}
            for method_count in sizes[2:]:
                index=0
                for _ in range(method_count):
                    delta,p=uleb(data,p)
                    index+=delta
                    _,p=uleb(data,p)
                    code_off,p=uleb(data,p)
                    if not code_off:
                        continue
                    mcls,mname=self.methods[index]
                    if mcls!=cls:
                        raise ValueError("PRE682_DEX_METHOD_CLASS_INCONSISTENCY")
                    compiled.setdefault(mname,[]).append(self._read_code(code_off))
            self.classes[cls]=compiled

    def _read_code(self,off):
        data=self.data
        units=u4(data,off+12)
        start=off+16
        if units>200000 or start+units*2>len(data):
            raise ValueError("PRE682_DEX_CODE_OUT_OF_BOUNDS")
        words=struct.unpack_from("<"+"H"*units,data,start)
        literals=set()
        invokes=set()
        # Conservative scan over 16-bit code units. Validate co-occurrence, not
        # control flow, register binding, conditional semantics or execution.
        for i,word in enumerate(words):
            op=word & 0xff
            if op==0x1a and i+1<units:
                ix=words[i+1]
                if ix<len(self.strings):
                    literals.add(self.strings[ix])
            elif op==0x1b and i+2<units:
                ix=words[i+1] | (words[i+2]<<16)
                if ix<len(self.strings):
                    literals.add(self.strings[ix])
            elif (0x6e<=op<=0x72 or 0x74<=op<=0x78) and i+1<units:
                ix=words[i+1]
                if ix<len(self.methods):
                    invokes.add(self.methods[ix])
        return {"literals": literals, "invokes": invokes}

    def code(self,cls,name):
        candidates=self.classes.get(cls,{}).get(name,[])
        if not candidates:
            raise ValueError("PRE682_REQUIRED_DEX_METHOD_NOT_FOUND: "+name)
        return {
            "literals":set().union(*(x["literals"] for x in candidates)),
            "invokes":set().union(*(x["invokes"] for x in candidates)),
            "overloads":len(candidates),
        }

def inspect(dexdata: bytes):
    dex=Dex(dexdata)
    args=dex.code(MOTOR,"argumentos")
    missing=[token for token in MOTOR_ARGS if token not in args["literals"]]
    if missing:
        raise ValueError("PRE682_REQUIRED_ARG_CONSTANT_MISSING: "+",".join(missing))
    invocations={name for cls,name in args["invokes"] if cls==PREFS}
    missing_calls=[name for name in PREFS_METHODS if name not in invocations]
    if missing_calls:
        raise ValueError("PRE682_REQUIRED_PREFERENCE_CALL_MISSING: "+",".join(missing_calls))
    shadows=["rapida","xbox360"]
    if not all(x in args["literals"] for x in shadows):
        raise ValueError("PRE682_SHADOW_MODE_CONSTANT_MISSING")
    prefs=[]
    for name,(literal,reader) in PREFS_METHODS.items():
        # A method may be overloaded (getter and setter). Require a code body
        # with the preference key and appropriate SharedPreferences read.
        options=dex.classes[PREFS].get(name,[])
        if not any(literal in x["literals"] and ("Landroid/content/SharedPreferences;",reader) in x["invokes"] for x in options):
            raise ValueError("PRE682_TYPED_PREFERENCE_GETTER_NOT_VERIFIED: "+name)
        prefs.append({"method":name,"key":literal,"read_api":reader,"present":True})
    return {
        "dex_sha256":sha(dexdata),
        "motor_argument_method_found":True,
        "argument_literals_verified":list(MOTOR_ARGS),
        "motor_invokes_preference_getters":sorted(PREFS_METHODS),
        "shadow_mode_literals":["rapida","xbox360"],
        "typed_preference_getters":prefs,
        "method_reference_scope":"within same Dex code_item; no data-flow validation",
    }

def client():
    required=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    missing=[k for k in required if not os.environ.get(k)]
    if missing:
        raise ValueError("PRE682_MISSING_SECRETS: "+",".join(missing))
    c=Credentials(token=None,refresh_token=os.environ[required[0]],
                 client_id=os.environ[required[1]],client_secret=os.environ[required[2]],
                 token_uri="https://oauth2.googleapis.com/token")
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)

def get_bytes(drive, fileid):
    buf=io.BytesIO()
    request=drive.files().get_media(fileId=fileid)
    downloader=MediaIoBaseDownload(buf,request,chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk()
    return buf.getvalue()

def main():
    drive=client()
    apk=get_bytes(drive,APK_ID)
    if len(apk)!=APK_BYTES or sha(apk)!=APK_SHA256:
        raise ValueError("PRE682_APK_PIN_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(apk)) as f:
        if f.testzip() is not None:
            raise ValueError("PRE682_APK_CRC_FAILURE")
        names=[x for x in f.namelist() if x.endswith(".dex")]
        if not names:
            raise ValueError("PRE682_NO_DEX_IN_APK")
        modules=[inspect(f.read(name)) for name in names if b"Lio/github/nfsmwrecomp/MotorNativo;" in f.read(name)]
        if len(modules)!=1:
            raise ValueError("PRE682_MOTOR_DEX_COUNT_NE_ONE")
    report={
        "gate":"PRE682_V51_SIGNED_APK_DEX_ANCHORS_READONLY",
        "status":"PASS_STATIC_DEX_METHOD_AND_LITERALS",
        "timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "github_run_id":os.environ.get("GITHUB_RUN_ID"),
        "apk":{"drive_file_id":APK_ID,"size":len(apk),"sha256":APK_SHA256,"zip_crc":"PASS"},
        "dex_audit":modules[0],
        "screenshot_source":"user-provided graphical launcher screenshot; not present in ZIP",
        "observed_ui_options_not_runtime_confirmed":{
            "api":"Vulkan","resolution":"1920x1080","cap_fps":60,
            "shadows":"Xbox 360","shadow_resolution":"Ultra","shadow_distance":"Long",
            "motion_blur":"On","anisotropic":"16x","car_reflections":"High"
        },
        "limitations":{
            "preferences_read_from_S24_FE":False,
            "runtime_argv_captured":False,
            "effective_cvar_values_confirmed":False,
            "exact_boolean_negation_dataflow_proven":False,
            "rendered_fidelity_confirmed":False,
            "source_or_apk_modified":False,
            "fps_gain_demonstrated":False,
        },
    }
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre682_") as td:
        path=Path(td)/("NFSMW_PRE682_V51_DEX_GRAPHICS_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")+".zip")
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("PRE682_DEX_REPORT.json",json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
            z.writestr("PRE682_STATUS.md","PRE682: static DEX anchors present, runtime graphics values unverified. No APK build.\\n")
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None: raise ValueError("PRE682_RESULT_ZIP_CRC_FAILURE")
        media=MediaFileUpload(str(path),mimetype="application/zip",resumable=True)
        result=drive.files().create(body={"name":path.name,"parents":[PRIVATE_LOG_FOLDER]},
                                    media_body=media,fields="id,size").execute()
        if result.get("size") != str(path.stat().st_size):
            raise ValueError("PRE682_DRIVE_UPLOAD_SIZE_MISMATCH")
        if sha(get_bytes(drive,result["id"]))!=sha(path.read_bytes()):
            raise ValueError("PRE682_DRIVE_READBACK_HASH_MISMATCH")
    print("PRE682_SIGNED_V51_DEX_STATIC_AUDIT=PASS")
    print("PRE682_PRIVATE_DRIVE_READBACK=PASS")
    print("PRE682_DEVICE_PREFERENCES_AND_RUNTIME_CVARS=UNVERIFIED")
    print("PRE682_APK_PATCH_BUILD_FPS_GAIN=NONE")

if __name__=="__main__":
    main()
