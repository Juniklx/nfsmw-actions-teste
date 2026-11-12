#!/usr/bin/env python3
"""PRE726 V51 authenticated read-only .size() receiver versus .data() source."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre725_generate_private_v51_kernel as pre725

KERNEL="juniklx/nfsmw-pre726-v51-requested-driver-origin"
TITLE="NFSMW PRE726 V51 Requested Driver Origin"
MARKER="NFSMW_PRE726_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE725_EXTENSION_NAME_ORIGIN_OR_PARENT_DRIFT')"
EXTRA=r"""
 # PRE726: lexical chain, from driver extension properties to requested_extensions key.
 # No raw source, extension names or private identifiers leave authenticated Kaggle.
 def h726(x):return hashlib.sha256(x.encode('utf-8')).hexdigest()
 def L726(lines,n):return mask_cpp(lines[n-1]) if 1<=n<=len(lines) else ''
 def range726(lines,n):
  s=' '.join(L726(lines,k) for k in range(n,min(len(lines),n+2)+1))
  m=re.search(r'\bfor\s*\(',s)
  if not m:return {'found':False,'reason':'NO_FOR'}
  begin=m.end();depth=1;chars=[]
  for c in s[begin:]:
   if c=='(':depth+=1
   elif c==')':
    depth-=1
    if not depth:break
   chars.append(c)
  if depth:return {'found':False,'reason':'UNCLOSED_FOR'}
  v=''.join(chars)
  seps=[i for i,c in enumerate(v) if c==':' and (i==0 or v[i-1]!=':') and (i+1==len(v) or v[i+1]!=':')]
  if len(seps)!=1:return {'found':False,'reason':'NOT_SINGLE_RANGE_COLON'}
  left,right=v[:seps[0]].strip(),v[seps[0]+1:].strip()
  names=re.findall(r'[A-Za-z_]\w*',left)
  collection=re.fullmatch(r'[A-Za-z_]\w*',right)
  return {'found':True,'loop_var':names[-1] if names else None,'range':right,
   'range_is_identifier':bool(collection),'type_mentions_vk_extension_properties':'VkExtensionProperties' in left,
   'range_expr_sha256':h726(right),'loop_header_sha256':h726(v)}
 def requested_alias726(lines,first,stop):
  # Use complete bounded statements: aliases can be const auto&, or initializer multiline.
  source=mask_cpp('\n'.join(lines[first-1:stop]))
  found=[]
  for m in re.finditer(r'\b([A-Za-z_]\w*)\s*=(?!=)\s*',source):
   finish=source.find(';',m.end())
   if finish<0 or finish-m.end()>600:continue
   initializer=source[m.end():finish]
   if not re.search(r'\brequested_extensions\b',initializer):continue
   if not re.search(r'(?:\.|->)\s*find\s*\(',initializer):continue
   if not re.search(r'\bextensionName\b',initializer):continue
   line=first+source[:m.start()].count('\n')
   found.append({'line':line,'alias':m.group(1),
      'initializer_contains_find':True,'initializer_contains_extensionName':True,
      'alias_receiver_hash_is_pre711':h726(m.group(1))==report['pre711_operand_links']['files']['instance']['cstr_receiver']['receiver_object_sha256']})
  return found
 def origin726(lines,for_line,insert_line,kind):
  ranged=range726(lines,for_line)
  matches=requested_alias726(lines,for_line+1,insert_line-1)
  em=extract725(lines,insert_line)
  mm=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)\s*\.\s*c_str\s*\(\s*\)\s*',em.get('raw',''))
  alias_receiver=(matches[0]['alias']==mm.group(1)) if len(matches)==1 and mm else False
  var_name=ranged.get('loop_var')
  firstguard=448 if kind=='instance' else 286
  only_member=(h726(mm.group(2))==h726('first')) if mm else False
  # Detect actual Vulkan enumeration calls, not merely extension-type tokens.
  enum_name='vkEnumerateInstanceExtensionProperties' if kind=='instance' else 'vkEnumerateDeviceExtensionProperties'
  other='vkEnumerateDeviceExtensionProperties' if kind=='instance' else 'vkEnumerateInstanceExtensionProperties'
  enum_sites=[n for n in range(1,min(for_line,len(lines))+1) if re.search(r'\b'+enum_name+r'\s*\(',L726(lines,n))]
  nearby_enums=[n for n in enum_sites if for_line-80<=n<for_line]
  # Verify Vulkan extensionName property is accessed in the filter's lookup, not infer its value.
  finder_line=matches[0]['line'] if len(matches)==1 else None
  extension_name_in_find=bool(matches and matches[0]['initializer_contains_extensionName'])
  return {'kind':kind,'for_line':for_line,'insert_line':insert_line,
   'loop_header_found':ranged.get('found',False),
   'loop_type_mentions_VkExtensionProperties':ranged.get('type_mentions_vk_extension_properties',False),
   'range_is_identifier':ranged.get('range_is_identifier',False),
   'range_expr_sha256':ranged.get('range_expr_sha256'),
   'range_var_differs_from_find_alias':len(matches)==1 and bool(var_name) and var_name!=matches[0]['alias'],
   'requested_find_assignments_in_branch':len(matches),
   'requested_find_alias_line':finder_line,
   'requested_find_alias_matches_emplace_cstr_receiver':alias_receiver,
   'cstr_uses_requested_map_first_member':alias_receiver and only_member,
   'lookup_mentions_extensionName':extension_name_in_find,
   'Vulkan_driver_extension_enumeration_call_before_loop':bool(enum_sites),
   'Vulkan_driver_extension_enumeration_call_lines_before_loop':enum_sites[-8:],
   'enumeration_nearby_loop_lines':nearby_enums[-8:],
   'opposite_domain_enum_call_before_loop':bool(any(re.search(r'\b'+other+r'\s*\(',L726(lines,n)) for n in range(1,for_line))),
   'enumeration_dataflow_to_range_proven':False,
   'runtime_advertised_extensions':'NOT_VERIFIED',
   'runtime_requested_extensions':'NOT_VERIFIED',
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'cpp_ast_or_cfg':'NOT_VERIFIED',
   'raw_cpp_exported':False,'private_identifiers_exported':False}
 inst726=origin726(instance_lines,445,455,'instance')
 dev726=origin726(device_lines,283,291,'device')
 f726={'instance':inst726,'device':dev726,
  'requested_find_to_emplace_link_in_both_contexts':inst726['requested_find_alias_matches_emplace_cstr_receiver'] and dev726['requested_find_alias_matches_emplace_cstr_receiver'],
  'explicit_driver_enumeration_is_not_runtime_enabled':True,
  'source_to_signed_elf_equivalence':'UNVERIFIED',
  'releases_compiled':False,'apk_modified':False,'signing_material_accessed':False,
  'fps_gain_proven':False,'source_text_exported':False,
  'real_vulkan_extension_names_exported':False,'private_identifiers_exported':False}
 report['pre726_requested_driver_origin_audit']={
  'stage':'PRE726_V51_REQUESTED_DRIVER_EXTENSION_ORIGIN_READONLY',
  'source_findings':f726,'runtime_vulkan_tested':False,
  'cpp_ast_or_cfg_used':False,'source_text_exported':False,
  'apk_built':False,'apk_modified':False,'signing_material_accessed':False,'fps_gain_proven':False}
 report['analysis_type']='PRE726_AUTHENTICATED_V51_REQUESTED_DRIVER_EXTENSION_ORIGIN_LEXICAL'
 report['status']=('PASS_PRE726_V51_REQUESTED_MAP_ALIAS_ORIGIN_AUDIT'
  if inst726['loop_header_found'] and dev726['loop_header_found']
   and inst726['requested_find_assignments_in_branch']==1
   and dev726['requested_find_assignments_in_branch']==1
   and inst726['requested_find_alias_matches_emplace_cstr_receiver']
   and dev726['requested_find_alias_matches_emplace_cstr_receiver']
   and inst726['lookup_mentions_extensionName']
   and dev726['lookup_mentions_extensionName']
  else 'BLOCK_PRE726_REQUESTED_MAP_ALIAS_ORIGIN_UNRESOLVED')
"""

def code(manifest,archive,run,attempt):
    src=pre725.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE726_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE725_KAGGLE_REMOTE.json',MARKER),
      ('PRE725_V51_KAGGLE_DYNAMIC_EXTENSION_ORIGIN_READONLY',
       'PRE726_V51_KAGGLE_REQUESTED_DRIVER_ORIGIN_READONLY'),
      ("print('PRE725_KAGGLE_GATE=","print('PRE726_KAGGLE_GATE="),
      ("print('PRE725_REPORT=","print('PRE726_REPORT=")
    ):
       if old not in src:raise ValueError('PRE726_PARENT_TOKEN_DRIFT '+old)
       src=src.replace(old,new)
    compile(src,'<PRE726 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre726.ipynb',
         'language':'python','kernel_type':'notebook','is_private':True,
         'enable_gpu':False,'enable_internet':False,
         'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,'metadata':{
      'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre726-purpose','metadata':{},
        'source':['PRE726 authenticated V51 private lexical source; only hashes and metadata leave notebook.']},
       {'cell_type':'code','id':'pre726-readonly','metadata':{},
        'source':src.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
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
        src=code({},b'fixture','123','1')
        assert MARKER in src and 'PASS_PRE726_V51_REQUESTED_MAP_ALIAS_ORIGIN_AUDIT' in src
        assert "'private_identifiers_exported':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET',
                          'KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
           assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE726_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
       p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE726_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE726_BAD_V51_DEVICE_INSTANCE_HASH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
       if z.testzip() is not None or set(z.namelist())!=set(hashes):
          raise ValueError('PRE726_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre726.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE726_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
