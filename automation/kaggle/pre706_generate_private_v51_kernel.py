#!/usr/bin/env python3
"""PRE706: inspect authenticated V51 VkDevice extension-list provenance in a private Kaggle notebook.

Read-only. Reuses PRE704 authenticated source ZIP & PRE705 audited notebook template.
Outputs bounded structural indicators, never raw source, ROM, APK or credentials.
"""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import pre704_generate_private_v51_kernel as pre704
import pre705_generate_private_v51_kernel as pre705

KERNEL="juniklx/nfsmw-pre706-v51-ext-origins-readonly"
TITLE="NFSMW PRE706 V51 Ext Origins Readonly"
MARKER="NFSMW_PRE706_KAGGLE_REMOTE.json"
DEVICE="nativo/sdk/src/ui/vulkan/vulkan_device.cpp"
INSTANCE="nativo/sdk/src/ui/vulkan/vulkan_instance.cpp"
DEVICE_SHA="24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38"
INSTANCE_SHA="700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04"
OLD=""" report['status']=('PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_FLOW_INDICATORS_ONLY'
                   if report['pre705_device_create_line_count']>0
                   and len(flow['device']['occurrences']['ppEnabledExtensionNames']['lines'])>0
                   else 'BLOCK_REQUIRED_DEVICE_EXTENSION_ANCHORS_MISSING')"""
INSERT=r"""
 # PRE706: source-provenance clues around VkDeviceCreateInfo; no source lines exported.
 def file_lines(name,expected):
  if name not in lookup or lookup[name]['sha256']!=expected:raise ValueError('PRE706_PIN_MISMATCH')
  with zipfile.ZipFile(io.BytesIO(archive)) as z:
   raw=z.read(name)
  if len(raw)!=lookup[name]['bytes'] or hashlib.sha256(raw).hexdigest()!=expected:
   raise ValueError('PRE706_SOURCE_TAMPER')
  return raw.decode('utf-8-sig').splitlines()
 device_lines=file_lines('nativo/sdk/src/ui/vulkan/vulkan_device.cpp',
                         '24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38')
 instance_lines=file_lines('nativo/sdk/src/ui/vulkan/vulkan_instance.cpp',
                           '700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04')
 result={'stage':'PRE706_SOURCE_EXTENSION_CONTAINER_PROVENANCE',
         'source_hashes_verified':True,'anchors':{},'possible_extension_names':[],
         'runtime_extension_list':'NOT_VERIFIED','complete_cpp_dataflow_proven':False,
         'analysis_scope':'DEVICE_CXX_BOUNDED_STATIC_CONTEXT'}
 def tokens(lines,label,anchor):
  lower=max(1,anchor-2);upper=min(len(lines),anchor+2)
  fragment=' '.join(lines[lower-1:upper])
  # Only this syntactic pattern; pointers and function call chains remain unproven.
  field='enabledExtensionCount' if label=='count' else 'ppEnabledExtensionNames'
  shape='size' if label=='count' else 'data'
  pattern=r'\b'+field+r'\s*=\s*(?:static_cast<[^>]+>\s*\(\s*)?([A-Za-z_]\w*)\s*\.\s*'+shape+r'\s*\('
  m=re.search(pattern,fragment)
  return m.group(1) if m else None
 for kind,lines,points in (
  ('device',device_lines,[305,306,567,569,811]),
  ('instance',instance_lines,[500,501,535,639,641])):
  if max(points)>len(lines):raise ValueError('PRE706_SOURCE_LINE_COUNT_CHANGED')
  result['anchors'][kind]={'observed':[]}
  for pt in points:
   line=lines[pt-1]
   classification=('VK_CREATE_CALL' if 'vkCreateDevice' in line else
                   'EXTENSION_COUNT' if 'enabledExtensionCount' in line else
                   'EXTENSION_POINTER' if 'ppEnabledExtensionNames' in line else
                   'OTHER')
   result['anchors'][kind]['observed'].append(
        {'line':pt,'kind':classification,
         'line_sha256':hashlib.sha256(line.encode('utf8')).hexdigest()})
  cnt=tokens(lines,'count',305 if kind=='device' else 500)
  ptr=tokens(lines,'pointer',306 if kind=='device' else 501)
  result['anchors'][kind]['count_container_name']=cnt
  result['anchors'][kind]['pointer_container_name']=ptr
  result['anchors'][kind]['same_identifier']=bool(cnt and ptr and cnt==ptr)
  result['anchors'][kind]['nearby']=[]
  # Entire file searches can confuse unrelated scopes; report only a bounded
  # slice of lines preceding create-info and a small post-window.
  left,right=(205,355) if kind=='device' else (380,540)
  if right>len(lines):raise ValueError('PRE706_BOUNDED_SCOPE_MISSING')
  ident=cnt if cnt==ptr else None
  if ident:
   rx=re.compile(r'\b'+re.escape(ident)+r'\b')
   for i in range(left,right+1):
    ln=lines[i-1]
    if not rx.search(ln):continue
    cats=[]
    if re.search(r'\b'+re.escape(ident)+r'\s*\.(push_back|emplace_back|insert)\b',ln):
     cats.append('CONTAINER_ADD')
    if re.search(r'\b'+re.escape(ident)+r'\s*=',ln):
     cats.append('CONTAINER_ASSIGN')
    if re.search(r'(std::vector|std::set|std::array)\s*<',ln):
     cats.append('CONTAINER_TYPE_VISIBLE')
    if re.search(r'for\s*\(|while\s*\(',ln):cats.append('ITERATION')
    if re.search(r'\bif\s*\(',ln):cats.append('CONDITION')
    if re.search(r'\.(size|data)\s*\(',ln):cats.append('SIZE_DATA_USE')
    if not cats:cats=['MENTION_ONLY']
    result['anchors'][kind]['nearby'].append({'line':i,'kinds':cats,
      'line_sha256':hashlib.sha256(ln.encode('utf8')).hexdigest()})
  result['anchors'][kind]['bounded_scope']={'first':left,'last':right,
     'mentions':len(result['anchors'][kind]['nearby'])}
 # Expose only public standardized Vulkan extension names; never arbitrary literals.
 source_bundle='\n'.join(device_lines+instance_lines)
 known_names=set(re.findall(r'\bVK_[A-Z0-9_]+_EXTENSION_NAME\b',source_bundle))
 known_names.update(re.findall(r'VK_(?:KHR|EXT|GOOGLE)_[A-Za-z0-9_]+',source_bundle))
 result['possible_extension_names']=sorted(x for x in known_names if len(x)<130)[:100]
 result['possible_extension_names_truncated']=len(known_names)>100
 result['both_createinfo_fields_resolve_to_local_identifier']=(
   result['anchors']['device']['same_identifier'] and
   result['anchors']['instance']['same_identifier'])
 result['device_extension_container_identified']=result['anchors']['device']['same_identifier']
 # Audit passes only when source identity and both VkDeviceCreateInfo fields are verified.
 # It does NOT prove which extensions are enabled by the signed Android binary.
 report['pre706_provenance']=result
 report['analysis_type']='BOUNDED_V51_EXTENSION_CONTAINER_ORIGIN_INDICATORS_ONLY'
 report['runtime_vk_device_enabled_extensions']='NOT_VERIFIED'
 report['status']=('PASS_AUTHENTICATED_V51_EXTENSION_CONTAINER_PROVENANCE_INDICATORS_ONLY'
     if result['anchors']['device']['observed'][0]['kind']=='EXTENSION_COUNT'
     and result['anchors']['device']['observed'][1]['kind']=='EXTENSION_POINTER'
     and report['pre705_device_create_line_count']>0
     else 'BLOCK_DEVICE_EXTENSION_FIELDS_NOT_AUTHENTICATED')
"""
def sha(data):
    return hashlib.sha256(data).hexdigest()

def code(manifest,archive,run,attempt):
    body=pre705.kernel_code(manifest,archive,run,attempt)
    if body.count(OLD)!=1:raise ValueError("PRE706_PARENT_TEMPLATE_DRIFT")
    body=body.replace(OLD,INSERT)
    replacements={
        "NFSMW_PRE705_KAGGLE_REMOTE.json":MARKER,
        "PRE705_V51_KAGGLE_DEVICE_EXTENSION_FLOW_READONLY":
            "PRE706_V51_KAGGLE_DEVICE_EXTENSION_ORIGINS_READONLY",
        "print('PRE705_KAGGLE_GATE=":"print('PRE706_KAGGLE_GATE=",
        "print('PRE705_REPORT=":"print('PRE706_REPORT=",
    }
    for src,target in replacements.items():
        if src not in body:raise ValueError('PRE706_MISSING_TEMPLATE_MARKER '+src)
        body=body.replace(src,target)
    compile(body,'<PRE706 Kaggle readonly>', 'exec')
    return body

def build(manifest,archive,run,attempt):
    body=code(manifest,archive,run,attempt)
    meta={
      'id':KERNEL,'title':TITLE,'code_file':'pre706.ipynb',
      'language':'python','kernel_type':'notebook','is_private':True,
      'enable_gpu':False,'enable_internet':False,
      'dataset_sources':[],'competition_sources':[],
      'kernel_sources':[],'model_sources':[]
    }
    notebook={'nbformat':4,'nbformat_minor':5,
      'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre706-note','metadata':{},
                'source':['NFSMW PRE706 isolated source-only audited V51 extension list provenance.']},
               {'cell_type':'code','id':'pre706-audit','metadata':{},
                'source':body.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    return meta,notebook

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',type=Path)
    p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--run-id')
    p.add_argument('--attempt',default='1')
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    if args.self_test:
        body=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'not-a-real-source-bundle','123','1')
        assert 'pre706_provenance' in body
        assert "decode('utf-8-sig')" in body and "decode('utf8-sig')" not in body
        assert b'\xef\xbb\xbfA'.decode('utf-8-sig')=='A'
        assert 'PASS_AUTHENTICATED_V51_EXTENSION_CONTAINER_PROVENANCE_INDICATORS_ONLY' in body
        assert 'GOOGLE_REFRESH_TOKEN' not in body and 'KAGGLE_API_TOKEN' not in body
        assert MARKER in body
        assert re.sub(r'[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        assert '.size' not in body or 'enabledExtensionCount' in body
        assert 'runtime_vk_device_enabled_extensions' in body
        meta,note=build({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'x','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE706_GENERATOR_SYNTHETIC=9_PASS')
        return
    if not all((args.manifest,args.archive,args.output,args.run_id)):
        p.error('required --manifest --archive --output --run-id')
    if not re.fullmatch(r'[0-9]+',args.run_id) or not re.fullmatch(r'[0-9]+',args.attempt):
        p.error('run IDs must be numeric')
    manifest=json.loads(args.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),
        manifest.get('backend_sha256'))!=('PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',
        pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE706_UNAUTHENTICATED_MANIFEST')
    entries={e['path']:e['sha256'] for e in manifest['entries']}
    if entries.get(DEVICE)!=DEVICE_SHA or entries.get(INSTANCE)!=INSTANCE_SHA:
        raise ValueError('PRE706_DEVICE_INSTANCE_HASH_MISMATCH')
    raw=args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=manifest['count']:
            raise ValueError('PRE706_BAD_SOURCE_BUNDLE')
    meta,note=build(manifest,raw,args.run_id,args.attempt)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (args.output/'pre706.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    assert json.loads((args.output/'kernel-metadata.json').read_text())==meta
    print('PRE706_PRIVATE_KERNEL='+KERNEL)
    print('PRE706_V51_SOURCE_COUNT='+str(manifest['count']))
if __name__=="__main__":
    main()
