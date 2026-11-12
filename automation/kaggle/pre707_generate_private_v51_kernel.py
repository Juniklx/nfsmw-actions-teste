#!/usr/bin/env python3
"""PRE707 V51 Vulkan extension selection-site audit on isolated authenticated Kaggle source.

Static lexical/structural evidence only. Does not patch source, enable Vulkan features,
start a game, touch signing, nor prove the signed Android binary's runtime state.
"""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706

KERNEL="juniklx/nfsmw-pre707-v51-ext-guards-readonly"
TITLE="NFSMW PRE707 V51 Ext Guards Readonly"
MARKER="NFSMW_PRE707_KAGGLE_REMOTE.json"
INJECTION_ANCHOR=" report['pre706_provenance']=result"
PASS_ANCHOR=" report['status']=('PASS_AUTHENTICATED_V51_EXTENSION_CONTAINER_PROVENANCE_INDICATORS_ONLY'"
EXTRA=r"""
 # PRE707: provenance at insertion sites. Context proximity is NOT proven C++ nesting.
 def classify_insert(line):
  m=re.search(r'\benabled_extensions\s*\.\s*(push_back|emplace_back|insert)\s*\(',line)
  if not m:
   return {'container_insert_found':False,'method':None,'argument_kind':'NOT_PARSED'}
  tail=line[m.end():]
  # Only one-line arguments are classified. Never export the original source line.
  rhs=tail.split(')',1)[0].strip()
  kind=('ENUMERATED_EXTENSION_NAME_FIELD' if re.search(r'(?:\.|->)\s*extensionName\b',rhs)
        else 'EXPLICIT_VULKAN_MACRO' if re.search(r'\bVK_[A-Za-z0-9_]+\b',rhs)
        else 'C_STRING_LITERAL' if rhs.startswith('"')
        else 'LOCAL_IDENTIFIER' if re.fullmatch(r'[A-Za-z_]\w*',rhs)
        else 'COMPLEX_OR_MULTILINE')
  return {'container_insert_found':True,'method':m.group(1),
          'argument_kind':kind,
          'mentions_extensionName':bool(re.search(r'\bextensionName\b',rhs)),
          'mentions_VK_constant':bool(re.search(r'\bVK_[A-Za-z0-9_]+\b',rhs)),
          'argument_hash_sha256':hashlib.sha256(rhs.encode('utf8')).hexdigest()}
 def classify_condition(line):
  line=re.sub(r'//.*$','',line)
  expr=re.search(r'\b(if|for|while|switch)\s*\(',line)
  if not expr:return None
  tests={
    'references_enabled_extensions':r'\benabled_extensions\b',
    'references_extension_name':r'\bextensionName\b',
    'references_extension_properties':r'\b(extensionProperties|extension_properties|extensions|properties)\b',
    'compares_values':r'(==|!=|<=|>=|<|>)',
    'calls_find_or_contains':r'(find\s*\(|contains\s*\(|strcmp\s*\(|strncmp\s*\()',
    'has_boolean_logic':r'(\&\&|\|\||!\s*[A-Za-z_(])',
    'has_vulkan_extension_literal':r'\bVK_[A-Za-z0-9_]+\b',
    'references_required_or_optional':r'\b(required|optional|supported|available)\b',
  }
  return {'control':expr.group(1),'indicators':sorted(k for k,pattern in tests.items()
                                                    if re.search(pattern,line,re.I))}
 sites={}
 for label,lines,lo,hi,ins in [
   ('device',device_lines,244,315,291),
   ('instance',instance_lines,430,510,455)]:
  if not (hi<=len(lines) and lo<=ins<=hi):
   raise ValueError('PRE707_EXPECTED_SOURCE_SLICE_MISSING')
  if result['anchors'][label]['count_container_name']!='enabled_extensions' or \
     result['anchors'][label]['pointer_container_name']!='enabled_extensions':
   raise ValueError('PRE707_LOCAL_CONTAINERS_NOT_CONFIRMED')
  local_mentions=[]
  for i in range(lo,hi+1):
   line=lines[i-1]
   tags=[]
   if 'vkEnumerateDeviceExtensionProperties' in line:tags.append('VULKAN_DEVICE_EXTENSION_ENUMERATION')
   if 'vkEnumerateInstanceExtensionProperties' in line:tags.append('VULKAN_INSTANCE_EXTENSION_ENUMERATION')
   if 'VkExtensionProperties' in line:tags.append('VULKAN_EXTENSION_PROPERTIES_TYPE')
   if re.search(r'\benabled_extensions\s*\.\s*(push_back|emplace_back|insert)\s*\(',line):
    tags.append('ENABLED_EXTENSIONS_INSERT')
   if re.search(r'\benabled_extensions\b',line) and '.size(' in line:tags.append('ENABLED_EXTENSIONS_COUNT')
   if re.search(r'\benabled_extensions\b',line) and '.data(' in line:tags.append('ENABLED_EXTENSIONS_POINTER')
   if re.search(r'\bVK_[A-Z0-9_]+_EXTENSION_NAME\b',line):tags.append('LITERAL_VULKAN_EXTENSION_CONSTANT')
   if 'VK_GOOGLE_display_timing' in line:tags.append('LITERAL_GOOGLE_DISPLAY_TIMING')
   if tags:
    local_mentions.append({'line':i,'tags':tags})
  conditions=[]
  # No braces/AST parsing; controls are merely lexically nearby, not proven guards.
  for i in range(max(lo,ins-36),ins+1):
   desc=classify_condition(lines[i-1])
   if desc:conditions.append({'line':i,**desc})
  insert=classify_insert(lines[ins-1])
  near_insert=[]
  for i in range(max(lo,ins-4),min(hi,ins+4)+1):
   line=lines[i-1]
   indicators=[]
   if 'extensionName' in line:indicators.append('EXTENSION_NAME_MEMBER')
   if re.search(r'\benabled_extensions\b',line):indicators.append('ENABLED_CONTAINER')
   if re.search(r'\bif\s*\(',line):indicators.append('IF_STATEMENT')
   if re.search(r'\bfor\s*\(',line):indicators.append('FOR_STATEMENT')
   if re.search(r'\bVK_[A-Za-z0-9_]+\b',line):indicators.append('VULKAN_MACRO')
   if re.search(r'(strcmp|find|contains)\s*\(',line):indicators.append('FILTER_FUNCTION')
   if indicators:near_insert.append({'line':i,'indicators':indicators})
  sites[label]={
   'slice_range':[lo,hi],'insert_line':ins,'insert':insert,
   'lexical_nearby_conditions':conditions,
   'near_insert_indicators':near_insert,
   'recognized_structural_sites':local_mentions,
   'vulkan_extension_constant_tokens':sorted(set(
     re.findall(r'\bVK_[A-Z0-9_]+_EXTENSION_NAME\b',
        '\n'.join(lines[lo-1:hi]))))[:50],
   'source_sha256':lookup['nativo/sdk/src/ui/vulkan/vulkan_'+label+'.cpp']['sha256'],
  }
 # Cross-check source markers against PRE704/PRE705/PRE706, fail closed on drift.
 if not sites['device']['insert']['container_insert_found'] or \
    not sites['instance']['insert']['container_insert_found']:
  raise ValueError('PRE707_REQUIRED_EXTENSION_INSERT_NOT_FOUND')
 if not any('VULKAN_DEVICE_EXTENSION_ENUMERATION' in x['tags']
            for x in sites['device']['recognized_structural_sites']):
  raise ValueError('PRE707_DEVICE_ENUMERATION_NOT_IN_WINDOW')
 report['pre707_selection']={
   'stage':'PRE707_V51_EXTENSION_SELECTION_SITE_CONTEXT',
   'sites':sites,'scope':'LEXICAL_PROXIMITY_ONLY_NO_CPP_AST',
   'source_hashes_verified':True,
   'driver_advertised_extensions':'PRE702_USER_REPORT_ONLY',
   'application_requested_names':'NOT_PROVEN',
   'vulkan_device_creation_success':'NOT_INFERRED',
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'complete_dataflow_proven':False,
   'filter_semantics_proven':False,
   'apk_binary_equivalence':'UNVERIFIED',
 }
"""
FINAL=r"""
 # Gate: read-only source-only site classification, not runtime enablement.
 report['analysis_type']='PRE707_LEXICAL_INSERTION_AND_NEARBY_CONTROL_INDICATORS'
 report['status']=(
    'PASS_AUTHENTICATED_V51_EXTENSION_SELECTION_SITES_LEXICAL_ONLY'
    if report['pre707_selection']['source_hashes_verified']
    and sites['device']['insert']['container_insert_found']
    and sites['instance']['insert']['container_insert_found']
    and report['pre706_provenance']['anchors']['device']['same_identifier']
    else 'BLOCK_REQUIRED_EXTENSION_SELECTION_SITE')
"""
def code(manifest,archive,run,attempt):
    c=pre706.code(manifest,archive,run,attempt)
    if c.count(INJECTION_ANCHOR)!=1:raise ValueError("PRE707_PARENT_SOURCE_ANCHOR_DRIFT")
    if c.count(PASS_ANCHOR)!=1:raise ValueError("PRE707_PARENT_STATUS_ANCHOR_DRIFT")
    c=c.replace(INJECTION_ANCHOR,EXTRA+"\n"+INJECTION_ANCHOR)
    # Insert before parent's status assignment, then after overwrite status at same scope.
    match="     else 'BLOCK_DEVICE_EXTENSION_FIELDS_NOT_AUTHENTICATED')"
    if c.count(match)!=1:raise ValueError("PRE707_PARENT_GATE_DRIFT")
    c=c.replace(match,match+"\n"+FINAL)
    for a,b in [
      ('NFSMW_PRE706_KAGGLE_REMOTE.json',MARKER),
      ('PRE706_V51_KAGGLE_DEVICE_EXTENSION_ORIGINS_READONLY',
       'PRE707_V51_KAGGLE_DEVICE_EXTENSION_SELECTION_SITES_READONLY'),
      ("print('PRE706_KAGGLE_GATE=","print('PRE707_KAGGLE_GATE="),
      ("print('PRE706_REPORT=","print('PRE707_REPORT="),
    ]:
     if a not in c:raise ValueError("PRE707_RENAME_ANCHOR_DRIFT "+a)
     c=c.replace(a,b)
    compile(c,'<PRE707 private Kaggle notebook>','exec')
    return c

def build(manifest,archive,run,attempt):
    c=code(manifest,archive,run,attempt)
    meta={
     'id':KERNEL,'title':TITLE,'code_file':'pre707.ipynb','language':'python',
     'kernel_type':'notebook','is_private':True,'enable_gpu':False,
     'enable_internet':False,'dataset_sources':[],'competition_sources':[],
     'kernel_sources':[],'model_sources':[]
    }
    note={'nbformat':4,'nbformat_minor':5,
      'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre707-note','metadata':{},
               'source':['NFSMW PRE707 V51 private isolated source-only extension guards lexical audit.']},
               {'cell_type':'code','id':'pre707-source','metadata':{},
               'source':c.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    return meta,note

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
      body=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'synthetic','123','1')
      assert MARKER in body
      assert "LEXICAL_PROXIMITY_ONLY_NO_CPP_AST" in body
      assert "filter_semantics_proven':False" in body
      assert "PASS_AUTHENTICATED_V51_EXTENSION_SELECTION_SITES_LEXICAL_ONLY" in body
      assert "runtime_enabled_extensions':'NOT_VERIFIED'" in body
      assert all(x not in body for x in ('GOOGLE_REFRESH_TOKEN','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'))
      assert re.sub(r'[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.split('/')[1]
      m,n=build({},b'irrelevant','123','1')
      assert len(n['cells'])==2 and m['is_private'] and not m['enable_gpu'] and not m['enable_internet']
      print('PRE707_SYNTHETIC_SELFTEST=8_PASS')
      return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('required inputs missing')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
      p.error('numeric run id required')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),
        manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',
        pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE707_UNAUTHENTICATED_V51_MANIFEST')
    paths={x['path']:x['sha256'] for x in manifest['entries']}
    if paths.get(pre706.DEVICE)!=pre706.DEVICE_SHA or paths.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE707_SOURCE_HASHES_NOT_V51')
    data=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(paths):
        raise ValueError('PRE707_SOURCE_ZIP_BAD')
    meta,note=build(manifest,data,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre707.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE707_PRIVATE_KERNEL='+KERNEL)
    print('PRE707_SOURCES='+str(len(paths)))

if __name__=='__main__':main()
