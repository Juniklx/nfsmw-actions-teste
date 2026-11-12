#!/usr/bin/env python3
"""PRE704: construct an isolated Kaggle source-only device-extension lexical audit."""
import argparse, base64, hashlib, io, json, re, zipfile
from pathlib import Path

KERNEL='juniklx/nfsmw-pre704-v51-device-ext-readonly'
TITLE='NFSMW PRE704 V51 Device Ext Readonly'
PRESENTER='68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48'
BACKEND='b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385'
PRE99='af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39'

CELL=r'''import base64, hashlib, io, json, re, zipfile
from pathlib import Path
from datetime import datetime, timezone
MARKER=Path('/kaggle/working/NFSMW_PRE704_KAGGLE_REMOTE.json')
RUN=__RUN__
ATTEMPT=__ATTEMPT__
MANIFEST=json.loads(__MANIFEST__)
ARCHIVE_B64=__ARCHIVE__
ARCHIVE_SHA=__ARCHIVE_SHA__
TOKENS={
 'vkCreateDevice':r'\bvkCreateDevice\b',
 'vkEnumerateDeviceExtensionProperties':r'\bvkEnumerateDeviceExtensionProperties\b',
 'ppEnabledExtensionNames':r'\bppEnabledExtensionNames\b',
 'enabledExtensionCount':r'\benabledExtensionCount\b',
 'VK_GOOGLE_display_timing':r'VK_GOOGLE_display_timing',
 'VK_GOOGLE_DISPLAY_TIMING_EXTENSION_NAME':r'VK_GOOGLE_DISPLAY_TIMING_EXTENSION_NAME',
 'vkGetPastPresentationTimingGOOGLE':r'\bvkGetPastPresentationTimingGOOGLE\b',
 'VK_KHR_swapchain':r'VK_KHR_swapchain',
 'VK_KHR_SWAPCHAIN_EXTENSION_NAME':r'VK_KHR_SWAPCHAIN_EXTENSION_NAME',
 'VK_KHR_present_id2':r'VK_KHR_present_id2',
 'VK_EXT_present_timing':r'VK_EXT_present_timing',
 'vkGetPhysicalDeviceFeatures2':r'\bvkGetPhysicalDeviceFeatures2\b',
 'vkGetDeviceProcAddr':r'\bvkGetDeviceProcAddr\b',
 'vkCreateSwapchainKHR':r'\bvkCreateSwapchainKHR\b',
 'vkQueuePresentKHR':r'\bvkQueuePresentKHR\b',
}
report={'stage':'PRE704_V51_KAGGLE_DEVICE_EXTENSION_SOURCE_READONLY',
 'github_run_id':RUN,'github_run_attempt':ATTEMPT,'status':'FAIL_CLOSED',
 'source_to_signed_elf_equivalence':'UNVERIFIED',
 'pre702_google_display_timing':'ADVERTISED_USER_SUMMARY_ONLY',
 'runtime_vk_device_enabled_extensions':'NOT_VERIFIED',
 'runtime_timestamps_captured':False,'source_or_apk_modified':False,
 'signing_material_accessed':False,'device_modified':False,
 'fps_gain_proven':False,'lexical_not_semantic':True}
phase='DECODE'
try:
 archive=base64.b64decode(ARCHIVE_B64,validate=True)
 if hashlib.sha256(archive).hexdigest()!=ARCHIVE_SHA: raise ValueError('zip digest')
 phase='MANIFEST'
 if MANIFEST.get('stage')!='PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE': raise ValueError('stage')
 if MANIFEST.get('pre99_sha256')!='af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39':raise ValueError('pre99 pin')
 if MANIFEST.get('presenter_sha256')!='68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48':raise ValueError('presenter pin')
 if MANIFEST.get('backend_sha256')!='b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385':raise ValueError('backend pin')
 entries=MANIFEST['entries']
 if not isinstance(entries,list) or not (2<=len(entries)<=150):raise ValueError('entries')
 lookup={x['path']:x for x in entries}
 if len(lookup)!=len(entries):raise ValueError('duplicate path')
 phase='SOURCE_AUDIT'
 findings=[]
 with zipfile.ZipFile(io.BytesIO(archive)) as zf:
  names=zf.namelist()
  if set(names)!=set(lookup) or len(names)!=len(lookup):raise ValueError('zip entries')
  if zf.testzip() is not None:raise ValueError('zip crc')
  for name in names:
   p=Path(name)
   if p.is_absolute() or '..' in p.parts or not name.startswith('nativo/'):raise ValueError('member path')
   raw=zf.read(name); item=lookup[name]
   if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('file digest')
   if len(raw)>2500000:raise ValueError('large member')
   lines=raw.decode('utf-8-sig').splitlines()
   hits={}
   for term,pattern in TOKENS.items():
    rx=re.compile(pattern)
    indexes=[i for i,line in enumerate(lines,1) if rx.search(line)]
    if indexes:hits[term]={'count':len(indexes),'lines':indexes[:30]}
   findings.append({'path':name,'sha256':item['sha256'],'hits':hits})
 report['files_scanned']=len(findings)
 report['source_hashes']=[{'path':x['path'],'sha256':x['sha256']} for x in findings]
 report['files_with_hits']=[x for x in findings if x['hits']]
 report['totals']={term:sum(x['hits'].get(term,{}).get('count',0) for x in findings) for term in TOKENS}
 report['presenter_sha256']=MANIFEST['presenter_sha256']
 report['backend_sha256']=MANIFEST['backend_sha256']
 report['pre99_sha256']=MANIFEST['pre99_sha256']
 report['status']=('PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_LEXICAL_ONLY'
                    if report['totals']['vkCreateDevice']>0 else
                    'BLOCK_DEVICE_CREATE_ANCHOR_MISSING')
except Exception as exc:
 report['failure_phase']=phase
 report['failure_type']=type(exc).__name__
finally:
 report['completed_utc']=datetime.now(timezone.utc).isoformat()
 MARKER.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('PRE704_KAGGLE_GATE='+report['status'])
 print('PRE704_REPORT='+MARKER.name)
'''

def sha(b):return hashlib.sha256(b).hexdigest()

def code(manifest,archive,run,attempt):
    s=CELL
    replacements={'__RUN__':repr(str(run)),'__ATTEMPT__':repr(str(attempt)),
        '__MANIFEST__':repr(json.dumps(manifest,separators=(',',':'),sort_keys=True)),
        '__ARCHIVE__':repr(base64.b64encode(archive).decode('ascii')),
        '__ARCHIVE_SHA__':repr(sha(archive))}
    for k,v in replacements.items():s=s.replace(k,v)
    compile(s,'<PRE704 Kaggle isolated cell>','exec')
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',type=Path)
    p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--run-id')
    p.add_argument('--attempt',default='1')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:
        test=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'zip-test','123','1')
        assert 'NFSMW_PRE704_KAGGLE_REMOTE.json' in test
        assert 'GOOGLE_REFRESH_TOKEN' not in test and 'KAGGLE_API_TOKEN' not in test
        assert 'vkCreateDevice' in test and 'sha256' in test
        assert re.sub(r'[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.split('/')[1]
        print('PRE704_GENERATOR_SYNTHETIC=5_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('missing arguments')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('run ID/attempt must be numeric')
    manifest=json.loads(a.manifest.read_text())
    if manifest['stage']!='PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE':raise ValueError('stage')
    if (manifest['pre99_sha256'],manifest['presenter_sha256'],manifest['backend_sha256'])!=(PRE99,PRESENTER,BACKEND):raise ValueError('source pins')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        if zf.testzip() is not None:raise ValueError('zip crc')
        if len(zf.namelist())!=manifest['count']:raise ValueError('count')
    body=code(manifest,archive,a.run_id,a.attempt)
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    notebook={'nbformat':4,'nbformat_minor':5,
        'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
        'cells':[{'cell_type':'markdown','id':'pre704-note','metadata':{},'source':['NFSMW PRE704 private isolated Vulkan device extension source audit.']},
                 {'cell_type':'code','id':'pre704-audit','metadata':{},'source':body.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre704.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    (out/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (out/'pre704.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    assert json.loads((out/'kernel-metadata.json').read_text())==meta
    print('PRE704_PRIVATE_KERNEL='+KERNEL)
    print('PRE704_STAGE_FILES='+str(manifest['count']))
if __name__=='__main__':main()
