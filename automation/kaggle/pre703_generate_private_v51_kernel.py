#!/usr/bin/env python3
"""PRE703: private isolated Kaggle kernel; no secrets, APK, ISO or network in notebook."""
import argparse
import base64
import hashlib
import json
import os
import re
import zlib
from pathlib import Path

PIN='68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48'
KERNEL='juniklx/nfsmw-pre703-v51-pacing-readonly'
MARKER='NFSMW_PRE703_KAGGLE_REMOTE.json'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def notebook_cell(source, auditor, run, attempt):
    b64src=base64.b64encode(zlib.compress(source,9)).decode('ascii')
    b64audit=base64.b64encode(zlib.compress(auditor,9)).decode('ascii')
    code="""import base64, hashlib, json, subprocess, sys, zlib
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path('/kaggle/working')
MARKER=ROOT/'NFSMW_PRE703_KAGGLE_REMOTE.json'
RUN_ID=@RUN@
ATTEMPT=@ATTEMPT@
SOURCE_SHA='68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48'
AUDITOR_SHA=@AUDITOR_SHA@
SOURCE_B64=@SOURCE_B64@
AUDITOR_B64=@AUDITOR_B64@
report={'stage':'PRE703_V51_KAGGLE_GOOGLE_TIMING_SOURCE_READONLY',
        'github_run_id':RUN_ID,'github_run_attempt':ATTEMPT,
        'status':'FAIL_CLOSED','source_to_signed_elf_equivalence':'UNVERIFIED',
        'signing_material_accessed':False,'apk_or_source_modified':False,
        'fps_gain_proven':False,'runtime_vulkan_timestamps_captured':False}
phase='BOOT'
try:
    phase='DECODE_PINNED_SOURCE'
    src=zlib.decompress(base64.b64decode(SOURCE_B64))
    script=zlib.decompress(base64.b64decode(AUDITOR_B64))
    assert hashlib.sha256(src).hexdigest()==SOURCE_SHA
    assert hashlib.sha256(script).hexdigest()==AUDITOR_SHA
    workspace=ROOT/'pre703_v51_source'
    presenter=workspace/'nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp'
    presenter.parent.mkdir(parents=True,exist_ok=True)
    with presenter.open('xb') as f: f.write(src)
    py=ROOT/'pre703_auditor.py'
    with py.open('xb') as f: f.write(script)
    del src, script
    phase='SELF_TEST'
    t=subprocess.run([sys.executable,str(py),'--self-test'],capture_output=True,text=True,timeout=35)
    assert t.returncode==0 and 'PRE703_KAGGLE_SELFTEST=7_PASS' in t.stdout
    phase='SOURCE_AUDIT'
    audit_dir=ROOT/'NFSMW_Kaggle_Logs'
    run=subprocess.run([sys.executable,str(py),'--source-root',str(workspace),
        '--output-dir',str(audit_dir)],capture_output=True,text=True,timeout=90)
    assert run.returncode==0
    outputs=list(audit_dir.glob('NFSMW_PRE703_KAGGLE_SOURCE_AUDIT_*.json'))
    assert len(outputs)==1
    parsed=json.loads(outputs[0].read_text(encoding='utf-8'))
    assert parsed['gate']=='PASS_V51_RECIPE_SOURCE_ONLY'
    assert parsed['presenter']['sha256']==SOURCE_SHA
    assert parsed['source_count']==1
    assert parsed['source_or_apk_modified'] is False
    report['status']='PASS_V51_RECIPE_SOURCE_ONLY'
    report['source_sha256']=SOURCE_SHA
    report['anchors']=parsed['presenter']['anchors']
    report['google_display_timing_lexical_hits']=parsed['presenter']['anchors']['VK_GOOGLE_display_timing']['count']
    report['runtime_extension_enabled']='NOT_VERIFIED'
    report['pre702_driver_google_timing']='ADVERTISED_USER_SUMMARY_ONLY'
except Exception as e:
    report['failure_phase']=phase
    report['failure_type']=type(e).__name__
finally:
    report['completed_utc']=datetime.now(timezone.utc).isoformat()
    MARKER.write_text(json.dumps(report,sort_keys=True,indent=2)+'\\n',encoding='utf-8')
    print('PRE703_KAGGLE_STATUS='+report['status'])
    print('PRE703_KAGGLE_RESULT='+MARKER.name)
"""
    for key,value in {
        '@RUN@':repr(str(run)),
        '@ATTEMPT@':repr(str(attempt)),
        '@AUDITOR_SHA@':repr(sha(auditor)),
        '@SOURCE_B64@':repr(b64src),
        '@AUDITOR_B64@':repr(b64audit),
    }.items():
        code=code.replace(key,value)
    compile(code,'<PRE703 private Kaggle code>','exec')
    return code

def assemble(code):
    return {
        'nbformat':4,'nbformat_minor':5,
        'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
                    'language_info':{'name':'python'}},
        'cells':[
            {'cell_type':'markdown','metadata':{},'id':'pre703-note',
             'source':['NFSMW PRE703. Private isolated V51 source-only read-only timing audit.']},
            {'cell_type':'code','metadata':{},'id':'pre703-verify',
             'source':code.splitlines(keepends=True),'outputs':[],'execution_count':None}
        ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path)
    p.add_argument('--auditor',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--run-id')
    p.add_argument('--attempt',default='1')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:
        src=b'vkQueuePresentKHR and VK_GOOGLE_display_timing synthetic'
        prog=b'print("PRE703_KAGGLE_SELFTEST=7_PASS")'
        txt=notebook_cell(src,prog,'123','1')
        assert len(assemble(txt)['cells'])==2
        assert 'SOURCE_B64=' in txt and 'AUDITOR_B64=' in txt
        assert 'GOOGLE_REFRESH_TOKEN' not in txt and 'KAGGLE_API_TOKEN' not in txt
        assert sha(src)!=PIN
        assert assemble(txt)['cells'][0]['cell_type']=='markdown'
        assert 'NFSMW_PRE703_KAGGLE_REMOTE.json' in txt
        print('PRE703_GENERATOR_SELFTEST=6_PASS')
        return
    if not all((a.source,a.auditor,a.output,a.run_id)):
        p.error('required --source --auditor --output --run-id')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run/attempt required')
    source=a.source.read_bytes()
    auditor=a.auditor.read_bytes()
    if sha(source)!=PIN:
        raise RuntimeError('PRE703_SOURCE_NOT_V51_RECIPE')
    if b'PRE703_KAGGLE_SELFTEST=7_PASS' not in auditor:
        raise RuntimeError('PRE703_AUDITOR_UNEXPECTED')
    generated=notebook_cell(source,auditor,a.run_id,a.attempt)
    dest=a.output
    dest.mkdir(parents=True,exist_ok=True)
    metadata={
        'id':KERNEL,'title':'NFSMW PRE703 V51 Timing Readonly',
        'code_file':'pre703.ipynb','language':'python','kernel_type':'notebook',
        'is_private':True,'enable_gpu':False,'enable_internet':False,
        'dataset_sources':[],'competition_sources':[],
        'kernel_sources':[],'model_sources':[]
    }
    (dest/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (dest/'pre703.ipynb').write_text(json.dumps(assemble(generated),indent=2)+'\n')
    assert json.loads((dest/'kernel-metadata.json').read_text()) == metadata
    assert json.loads((dest/'pre703.ipynb').read_text())['nbformat'] == 4
    print('PRE703_KERNEL_PRIVATE=TRUE')
    print('PRE703_KERNEL_ID='+KERNEL)
    print('PRE703_PRESENTER_SHA256='+PIN)
    print('PRE703_NO_SECRETS_IN_KERNEL=TRUE')

if __name__=='__main__':
    main()
