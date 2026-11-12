#!/usr/bin/env python3
"""PRE705 isolated Kaggle device extension selection evidence, based on PRE704 authenticated bundle.

The generated private notebook analyzes a bounded authenticated V51 source bundle;
no APK build, signing, source patch, game assets, secrets or external network.
"""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import pre704_generate_private_v51_kernel as pre704

KERNEL = "juniklx/nfsmw-pre705-v51-ext-flow-readonly"
TITLE = "NFSMW PRE705 V51 Ext Flow Readonly"
MARKER = "NFSMW_PRE705_KAGGLE_REMOTE.json"
OLD = """ report['status']=('PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_LEXICAL_ONLY'
                    if report['totals']['vkCreateDevice']>0 else
                    'BLOCK_DEVICE_CREATE_ANCHOR_MISSING')"""
INSERT = r"""
 # PRE705: bounded source-flow indicators; no source text emitted in report.
 flow={}
 targets={
  'device':'nativo/sdk/src/ui/vulkan/vulkan_device.cpp',
  'instance':'nativo/sdk/src/ui/vulkan/vulkan_instance.cpp',
  'presenter':'nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp',
  'device_header':'nativo/sdk/include/rex/ui/vulkan/device.h',
 }
 with zipfile.ZipFile(io.BytesIO(archive)) as sourcezip:
  for label,path in targets.items():
   if path not in lookup: raise ValueError('required target missing: '+label)
   raw=sourcezip.read(path)
   if len(raw)!=lookup[path]['bytes'] or hashlib.sha256(raw).hexdigest()!=lookup[path]['sha256']:
    raise ValueError('flow target hash')
   lines=raw.decode('utf-8-sig').splitlines()
   tracked={
    'vkCreateDevice':r'\bvkCreateDevice\b',
    'vkEnumerateDeviceExtensionProperties':r'\bvkEnumerateDeviceExtensionProperties\b',
    'ppEnabledExtensionNames':r'\bppEnabledExtensionNames\b',
    'enabledExtensionCount':r'\benabledExtensionCount\b',
    'vkCreateInstance':r'\bvkCreateInstance\b',
    'VK_KHR_swapchain':r'VK_KHR_swapchain',
    'VK_KHR_SWAPCHAIN_EXTENSION_NAME':r'VK_KHR_SWAPCHAIN_EXTENSION_NAME',
    'VK_GOOGLE_display_timing':r'VK_GOOGLE_display_timing',
    'vkGetPastPresentationTimingGOOGLE':r'\bvkGetPastPresentationTimingGOOGLE\b',
    'VkDeviceCreateInfo':r'\bVkDeviceCreateInfo\b',
    'VkInstanceCreateInfo':r'\bVkInstanceCreateInfo\b',
    'VK_ERROR_EXTENSION_NOT_PRESENT':r'VK_ERROR_EXTENSION_NOT_PRESENT',
    'vkGetDeviceProcAddr':r'\bvkGetDeviceProcAddr\b',
    'features2':r'(Features2|features2|pNext)',
    'extensions_add':r'(push_back|emplace_back|insert\s*\(|append\s*\(|AddExtension|EnableExtension)',
    'if_condition':r'\bif\s*\(',
    'loop':r'\b(for|while)\s*\(',
   }
   hits={key:[i for i,ln in enumerate(lines,1) if re.search(pattern,ln)]
         for key,pattern in tracked.items()}
   decision_words=r'(extension|Extension|device|Device|feature|Feature|result|Result|VK_SUCCESS|VK_ERROR)'
   contexts={}
   for term in ('vkCreateDevice','vkEnumerateDeviceExtensionProperties',
                'ppEnabledExtensionNames','enabledExtensionCount','vkCreateInstance',
                'VK_KHR_SWAPCHAIN_EXTENSION_NAME'):
    contexts[term]=[]
    for anchor in hits[term][:15]:
     left=max(1,anchor-12);right=min(len(lines),anchor+12)
     flags={}
     for kind,pattern in {'if_condition':r'\bif\s*\(',
                          'loop':r'\b(for|while)\s*\(',
                          'vector_add':r'(push_back|emplace_back|insert\s*\()',
                          'error_check':r'(VK_SUCCESS|VK_ERROR|CheckResult|VK_CHECK|vk::Result)',
                          'features_chain':r'(pNext|Features2|features2)',
                          'extension_name':r'(EXTENSION_NAME|extension_name|extensionNames)',
                          'device_create_info':r'(VkDeviceCreateInfo|DeviceCreateInfo)',
                          'instance_create_info':r'(VkInstanceCreateInfo|InstanceCreateInfo)'
                         }.items():
      flags[kind]=[i for i in range(left,right+1)
                   if re.search(pattern,lines[i-1])][:15]
     contexts[term].append({'anchor_line':anchor,'window_first':left,
                             'window_last':right,'nearby_indicators':flags})
   assignments=[]
   for idx,ln in enumerate(lines,1):
    if 'ppEnabledExtensionNames' not in ln and 'enabledExtensionCount' not in ln:continue
    if len(assignments)>=40:break
    expr=ln.split('=',1)[-1].strip() if '=' in ln else ''
    kind=('NULL_LITERAL' if 'nullptr' in expr or re.search(r'\bNULL\b',expr)
          else 'ARRAY_DATA' if '.data(' in expr or '.data()' in expr
          else 'SIZE_CALL' if '.size(' in expr or '.size()' in expr
          else 'STATIC_LITERAL' if re.search(r'^\d+\b',expr)
          else 'OTHER_OR_MULTILINE')
    assignments.append({'line':idx,'field':('ppEnabledExtensionNames' if 'ppEnabledExtensionNames' in ln else 'enabledExtensionCount'),
                        'rhs_shape':kind,'has_assignment_on_same_line':'=' in ln,
                        'rhs_sha256':hashlib.sha256(expr.encode('utf8')).hexdigest() if expr else None})
   constants=sorted(set(re.findall(r'\bVK_[A-Z0-9_]+_EXTENSION_NAME\b',raw.decode('utf-8-sig'))))
   flow[label]={
     'path':path,'sha256':lookup[path]['sha256'],'lines_total':len(lines),
     'occurrences':{k: {'count':len(v),'lines':v[:60]} for k,v in hits.items()},
     'anchor_windows':contexts,'assignment_shapes':assignments,
     'vulkan_extension_constant_tokens':constants[:90],
     'constant_tokens_truncated':len(constants)>90
   }
 report['pre705_flow']=flow
 report['pre705_device_create_line_count']=len(flow['device']['occurrences']['vkCreateDevice']['lines'])
 report['pre705_instance_create_line_count']=len(flow['instance']['occurrences']['vkCreateInstance']['lines'])
 report['pre705_google_timing_explicit_hits_in_30_files']=report['totals']['VK_GOOGLE_display_timing']
 report['analysis_type']='BOUNDED_LEXICAL_CONTROL_FLOW_INDICATORS_NOT_RUNTIME'
 report['runtime_vk_device_enabled_extensions']='NOT_VERIFIED'
 report['status']=('PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_FLOW_INDICATORS_ONLY'
                   if report['pre705_device_create_line_count']>0
                   and len(flow['device']['occurrences']['ppEnabledExtensionNames']['lines'])>0
                   else 'BLOCK_REQUIRED_DEVICE_EXTENSION_ANCHORS_MISSING')
"""
def sha(data):
    return hashlib.sha256(data).hexdigest()

def kernel_code(manifest, archive, run, attempt):
    src=pre704.code(manifest, archive, run, attempt)
    if src.count(OLD)!=1:
        raise ValueError("PRE705_UPSTREAM_TEMPLATE_CHANGED")
    src=src.replace(OLD,INSERT)
    replacements={
      "NFSMW_PRE704_KAGGLE_REMOTE.json":MARKER,
      "PRE704_V51_KAGGLE_DEVICE_EXTENSION_SOURCE_READONLY":
          "PRE705_V51_KAGGLE_DEVICE_EXTENSION_FLOW_READONLY",
      "print('PRE704_KAGGLE_GATE='":"print('PRE705_KAGGLE_GATE='",
      "print('PRE704_REPORT='":"print('PRE705_REPORT='",
    }
    for key,value in replacements.items():
        if key not in src:raise ValueError('PRE705_UPSTREAM_FIELD_MISSING: '+key)
        src=src.replace(key,value)
    compile(src,"<PRE705 Kaggle source-only>", "exec")
    return src

def assemble(manifest,archive,run,attempt):
    src=kernel_code(manifest,archive,run,attempt)
    notebook={'nbformat':4,'nbformat_minor':5,
              'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
              'cells':[{'cell_type':'markdown','id':'pre705-note','metadata':{},
                        'source':['NFSMW PRE705 isolated read-only Vulkan VkDevice extension list source flow.']},
                       {'cell_type':'code','id':'pre705-audit','metadata':{},
                        'source':src.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre705.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    return notebook,meta

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--attempt',default='1')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        code=kernel_code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'fake-zip','123','1')
        assert 'pre705_flow' in code and 'BOUNDED_LEXICAL_CONTROL_FLOW' in code
        assert MARKER in code
        assert 'GOOGLE_REFRESH_TOKEN' not in code and 'KAGGLE_API_TOKEN' not in code
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.split('/')[1]
        assert 'PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_FLOW_INDICATORS_ONLY' in code
        assert 'vkCreateDevice' in code and 'ppEnabledExtensionNames' in code
        assert 'runtime_vk_device_enabled_extensions' in code
        print('PRE705_GENERATOR_SYNTHETIC=8_PASS')
        return
    if not all((args.manifest,args.archive,args.output,args.run_id)):
        parser.error('missing inputs')
    if not re.fullmatch(r'[0-9]+',args.run_id) or not re.fullmatch(r'[0-9]+',args.attempt):
        parser.error('numeric IDs required')
    manifest=json.loads(args.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE705_MANIFEST_NOT_AUTHENTICATED')
    archive=args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        if zf.testzip() is not None or len(zf.namelist())!=manifest['count']:
            raise ValueError('PRE705_ZIP_BAD')
    notebook,meta=assemble(manifest,archive,args.run_id,args.attempt)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'pre705.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    (args.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    assert json.loads((args.output/'kernel-metadata.json').read_text())==meta
    print('PRE705_PRIVATE_KERNEL='+KERNEL)
    print('PRE705_STAGE_FILES='+str(manifest['count']))

if __name__=='__main__':
    main()
