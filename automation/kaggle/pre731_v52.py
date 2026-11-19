"""Build the integrated V52 using the established PRE652 release chain."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zipfile

import pre652_build_signed_v51_gpu_shader_counts_diag as baseline

PATCH = Path(__file__).with_name("pre731_touch.patch").resolve()
SOURCE = Path("android/app/src/main/java/io/github/nfsmwrecomp/TouchControllerView.java")
stage_baseline = baseline.stage_v51
verify_baseline = baseline.verify_v51

def sha(data):
    return hashlib.sha256(data).hexdigest()

def stage(root):
    state = stage_baseline(root)
    source = root / SOURCE
    before = source.read_bytes()
    subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=root, check=True)
    subprocess.run(["git", "apply", str(PATCH)], cwd=root, check=True)
    after = source.read_bytes()
    if after.count(b"redraw |= control.move(") != 1 or after.count(b"if (redraw) invalidate();") != 1:
        raise ValueError("V52 touch move not staged")
    print("V52_TOUCH_SOURCE_SHA256=" + sha(before) + "->" + sha(after), flush=True)
    return state

def verify(apk,sdk,v30,progress):
    result=verify_baseline(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk) as z:
        d=z.read("classes.dex")
    def word(off):
        return struct.unpack_from("<I",d,off)[0]
    def string(idx):
        start=word(word(60)+4*idx)
        while d[start]&128: start+=1
        start+=1
        return d[start:d.index(0,start)]
    def typ(idx):
        return string(word(word(68)+4*idx))
    found=set()
    for i in range(word(88)):
        owner,proto,name=struct.unpack_from("<HHI",d,word(92)+8*i)
        if string(name)!=b"move": continue
        cls=typ(owner)
        if cls not in {b"Lio/github/nfsmwrecomp/TouchControllerView$"+x+b";" for x in (b"Control",b"Dpad",b"Stick")}: continue
        base=word(76)+12*proto
        args=word(base+8)
        if args and word(args)==2 and all(typ(i)==b"F" for i in struct.unpack_from("<HH",d,args+4)):
            if typ(word(base+4))!=b"Z": raise ValueError("Unexpected V52 DEX move return")
            found.add(cls)
    if len(found)!=3: raise ValueError("Missing V52 DEX boolean move signatures")
    progress["v52_touch_dex_verified"]=True
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--report",required=True)
    opts,_=parser.parse_known_args()
    baseline.VERSION=52
    baseline.APK_NAME="NFSMW_V52_PRE731_TOUCH_REDRAW_CANDIDATA.apk"
    baseline.stage_v51=stage
    baseline.verify_v51=verify
    rc=baseline.main()
    if rc: raise SystemExit(rc)
    report=json.loads(Path(opts.report).read_text())
    assert report["pre652_target_version_code"]==52 and report["v52_touch_dex_verified"]
    print("V52_TOUCH_SIGNED_VERIFIED")
