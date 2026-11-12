#!/usr/bin/env python3
"""PRE716: bounded source alias, predicate and push_back audit in private Kaggle.
Only authenticated read-only source. Does not instrument an APK or infer runtime enabled extensions.
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
import pre709_generate_private_v51_kernel as pre709
import pre710_generate_private_v51_kernel as pre710
import pre711_generate_private_v51_kernel as pre711
import pre712_generate_private_v51_kernel as pre712
import pre713_generate_private_v51_kernel as pre713
import pre714_generate_private_v51_kernel as pre714
import pre715_generate_private_v51_kernel as pre715

KERNEL="juniklx/nfsmw-pre716-v51-bool-pointers-lifetime-readonly"
TITLE="NFSMW PRE716 V51 Bool Pointers Lifetime Readonly"
MARKER="NFSMW_PRE716_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE715_SOURCE_DECLARATION_NOT_RESOLVED')"
EXTRA=r"""
 # PRE716: bounded source-only investigation of declared bool-pointer vector,
 # writes to pointed flags, extension name pointer lists and VkInstanceCreateInfo.
 # Conservative lexical probes: NOT a parser for complete C++/aliases/CFG.
 def h716(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def has716(s,n):return bool(re.search(r'\b'+re.escape(n)+r'\b',s)) if n else False
 def variable716(lines,number,expected_hash):
  masked=mask_cpp(lines[number-1])
  m=re.search(r'\bstd\s*::\s*vector\s*<\s*bool\s*\*\s*>\s*([A-Za-z_]\w*)\s*;',masked)
  if not m:return {'declaration_shape':'NOT_CONFIRMED','matched':False},None
  name=m.group(1)
  return {'declaration_shape':'STD_VECTOR_BOOL_PTR_SIMPLE',
    'declared_on_line':number,'declared_name_sha256':h716(name),'matched':True,
    'matches_previous_push_receiver_sha':h716(name)==expected_hash,
    'not_full_cpp_ast':True,'runtime_contents':'NOT_VERIFIED'},name
 def references716(lines,name,start,finish,control_line):
  # Non-exporting bounded lexical classification with true line positions.
  found=[]; members=[]
  for n in range(start, min(finish,len(lines))+1):
   s=mask_cpp(lines[n-1])
   if not has716(s,name):continue
   tags=[]
   if re.search(r'\b'+re.escape(name)+r'\s*\.\s*push_back\s*\(',s):tags.append('PUSH_BACK')
   if re.search(r'\b'+re.escape(name)+r'\s*\.\s*(?:size|data|empty|begin|end|cbegin|cend)\s*\(',s):
    tags.append('VECTOR_METHOD')
   if re.search(r'\b(?:for)\s*\([^;]*:\s*'+re.escape(name)+r'\b',s):
    tags.append('RANGE_FOR_ITERATION')
   if re.search(r'\*\s*[A-Za-z_]\w*\s*=\s*(?:true|false|0|1)\b',s):
    tags.append('BOOL_POINTER_ASSIGNMENT_SAME_LINE')
   if re.search(r'\b'+re.escape(name)+r'\s*\[',s):tags.append('INDEX_ACCESS')
   if re.search(r'\b'+re.escape(name)+r'\s*\.\s*clear\s*\(',s):tags.append('CLEAR')
   if n==start:tags.append('DECLARATION_LINE')
   if not tags:tags=['OTHER_REFERENCE']
   found.append({'line':n,'tags':sorted(set(tags)),
     'position_relative_to_vkCreateInstance':('before' if n<control_line else 'at' if n==control_line else 'after'),
     'source_line_sha256':h716(lines[n-1])})
  return {'lines_examined':[start,min(finish,len(lines))],
   'references_count':len(found),'references':found[:25],
   'truncated':len(found)>25,
   'actual_pointer_lifetime':'NOT_VERIFIED'}
 def assignment716(lines,start,finish):
  # Indicate possible dereference writes without assuming the target pointer.
  out=[]
  for n in range(start,min(finish,len(lines))+1):
   s=mask_cpp(lines[n-1])
   ptr=re.search(r'(?<![/*])\*\s*([A-Za-z_]\w*)\s*=\s*(true|false|0|1)\b',s)
   ref=re.search(r'([A-Za-z_]\w*)\s*->\s*second\s*=\s*(true|false|0|1)\b',s)
   if not (ptr or ref):continue
   out.append({'line':n,
     'kind':'DIRECT_DEREFERENCE_ASSIGNMENT' if ptr else 'ARROW_SECOND_ASSIGNMENT',
     'rhs_boolean_literal':(ptr or ref).group(2),
     'lhs_identifier_sha256':h716((ptr or ref).group(1)),
     'actual_binding_to_requested_extension':'NOT_VERIFIED'})
  return {'candidate_count':len(out),'candidates':out[:20],
    'truncated':len(out)>20,'all_aliases_resolved':False}
 def requested716(lines,upto):
  refs=[];typed=[]
  for n in range(1,min(len(lines),upto)+1):
   s=mask_cpp(lines[n-1])
   if not has716(s,'requested_extensions'):continue
   refs.append(n)
   prefix=s.split('requested_extensions',1)[0]
   methods=sorted(set(re.findall(r'\brequested_extensions\s*(?:\.|->)\s*(find|cend|end|emplace|insert|erase|size)\s*\(',s)))
   containers=re.findall(r'\bstd\s*::\s*(unordered_map|map|vector|array|set|unordered_set)\s*<',prefix)
   if containers:
    typed.append({'line':n,'type_token':containers[-1],
      'bool_pointer_token_before_name':bool(re.search(r'\bbool\s*\*',prefix)),
      'line_sha256':h716(lines[n-1])})
  return {'references_total':len(refs),'references_min_line':min(refs) if refs else None,
   'references_max_line':max(refs) if refs else None,
   'typed_declarations_found_lexically':typed[:12],
   'typed_candidates_total':len(typed),
   'possible_parameter_or_prior_declaration':'NOT_VERIFIED',
   'includes_and_typedef_resolution':'NOT_VERIFIED'}
 def instance_create716(lines):
  # Lines 500/501 were anchored by PRE705-706; report only public Vulkan tokens.
  create=[i for i,s in enumerate(lines,1) if re.search(r'\bvkCreateInstance\s*\(',mask_cpp(s))]
  struct=[i for i,s in enumerate(lines,1) if re.search(r'\bVkInstanceCreateInfo\b',mask_cpp(s))]
  count=[i for i,s in enumerate(lines,1) if re.search(r'\benabledExtensionCount\b',mask_cpp(s))]
  names=[i for i,s in enumerate(lines,1) if re.search(r'\bppEnabledExtensionNames\b',mask_cpp(s))]
  return {'create_lines':create[:10],'create_info_type_lines':struct[:10],
   'enabled_extension_count_lines':count[:10],
   'enabled_extension_name_pointer_lines':names[:10],
   'device_runtime_extensions_effectively_enabled':'NOT_VERIFIED',
   'data_pointer_lifetime':'NOT_VERIFIED'}
 expected=report['pre715_type_precedence_audit']['source_probe']['instance']['vector_declaration_line356']
 priorpush=report['pre712_alias_guard_audit']['files']['instance']['second_guard_body_push_back']['calls'][0]
 decl,name=variable716(instance_lines,356,priorpush['receiver_hash'])
 if not decl['matched'] or not decl['matches_previous_push_receiver_sha']:
  raise ValueError('PRE716_DECLARATION_NOT_SAME_AS_PUSHBACK')
 refs=references716(instance_lines,name,356,len(instance_lines),523)
 # Identify the actual alias of the map iterator found by PRE712 (without exporting it).
 first=parse_bounded_parentheses(instance_lines,448,'if')
 second=parse_bounded_parentheses(instance_lines,454,'if')
 third=parse_bounded_parentheses(instance_lines,456,'push_back')
 if not first['extracted'] or not second['extracted'] or not third['extracted']:
  raise ValueError('PRE716_CROSS_GATE_EXPRESSION_EXTRACTION')
 alias,rhs=pre712_equality(first['text'])
 push=mask_cpp(third['text']).strip()
 pushm=re.fullmatch(r'([A-Za-z_]\w*)\s*->\s*second',push)
 ptrmatch=bool(pushm and alias==pushm.group(1))
 key={'alias_hash':h716(alias) if alias else None,
      'push_arg_hash':h716(push),'push_arg_matches_find_iterator_second':ptrmatch,
      'push_arg_exact_arrow_second_shape':bool(pushm),
      'push_arg_contains_c_str':bool(re.search(r'\bc_str\s*\(',push)),
      'actual_value_of_second':'NOT_VERIFIED',
      'actual_cpp_pointer_type':'NOT_VERIFIED'}
 deltas={'in_scope':True,
   'instance_declared_vector':decl,
   'instance_push_arg_to_find_iterator_link':key,
   'instance_vector_references':refs,
   'instance_explicit_boolean_write_candidates':assignment716(instance_lines,356,len(instance_lines)),
   'instance_requested_extensions_all_prefix':requested716(instance_lines,445),
   'device_requested_extensions_all_prefix':requested716(device_lines,283),
   'instance_create_info':instance_create716(instance_lines)}
 report['pre716_boolptr_lifetime_map']={
   'stage':'PRE716_AUTHENTICATED_V51_BOOL_POINTER_VECTOR_AND_CREATE_INFO',
   'authenticated_source_sha_checks':True,
   'analysis_type':'LEXICAL_VECTOR_BOOL_PTR_AND_VKINSTANCE_CREATE_INFO_NOT_AST',
   'source_findings':deltas,
   'cpp_full_ast_or_cfg_proven':False,
   'actual_pointer_lifetime_proven':False,
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'source_to_signed_apk_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'source_text_exported':False,'secrets_accessed':False,
   'apk_built':False,'apk_modified':False,'fps_gain_proven':False}
 report['analysis_type']='PRE716_AUTHENTICATED_V51_BOOL_POINTER_VECTOR_LIFETIME_LEXICAL_ONLY'
 report['status']=('PASS_PRE716_AUTHENTICATED_V51_BOOLPTR_VECTOR_SOURCE_AUDIT'
  if decl['matches_previous_push_receiver_sha'] and ptrmatch
     and len(refs['references'])>=2
  else 'BLOCK_PRE716_VECTOR_OR_ALIAS_DRIFT')
"""
def code(manifest,archive,run,attempt):
    src=pre715.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE716_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE715_KAGGLE_REMOTE.json',MARKER),
        ('PRE715_V51_KAGGLE_TYPES_PRECEDENCE_READONLY',
         'PRE716_V51_KAGGLE_BOOL_POINTER_LIFETIME_READONLY'),
        ("print('PRE715_KAGGLE_GATE=","print('PRE716_KAGGLE_GATE="),
        ("print('PRE715_REPORT=","print('PRE716_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE716_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE716 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre716.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre716-purpose','metadata':{},
                  'source':['Authenticated V51 bounded C++ alias, condition callee and push_back lexical dataflow; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre716-readonly','metadata':{},
                   'source':src.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    return meta,notebook

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
        src=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'fake','123','1')
        assert MARKER in src and 'PRE716_AUTHENTICATED_V51_BOOL_POINTER_VECTOR_LIFETIME_LEXICAL_ONLY' in src
        assert 'PASS_PRE716_AUTHENTICATED_V51_BOOLPTR_VECTOR_SOURCE_AUDIT' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE716_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE716_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE716_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE716_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre716.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE716_PRIVATE_KERNEL='+KERNEL)
    print('PRE716_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
