#!/usr/bin/env python3
"""PRE720: authenticated V51 Vulkan range-for and extension-count RHS lexical audit."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre719_generate_private_v51_kernel as pre719

KERNEL="juniklx/nfsmw-pre720-v51-range-rhs-readonly"
TITLE="NFSMW PRE720 V51 Range RHS Readonly"
MARKER="NFSMW_PRE720_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE719_SOURCE_MUTATION_GATES_INCOMPLETE')"
EXTRA=r"""
 # PRE720: cautious syntax classification of range-for 531 and count RHS 535.
 def h720(x):return hashlib.sha256(x.encode('utf-8')).hexdigest()
 def split720(header):
  stack=[]
  pairs={')':'(',']':'[','}':'{'}
  for i,ch in enumerate(header):
   if ch in '([{':stack.append(ch)
   elif ch in ')]}':
    if not stack or stack[-1]!=pairs[ch]:return None
    stack.pop()
   elif ch==':' and not stack:
    if (i and header[i-1]==':') or (i+1<len(header) and header[i+1]==':'):continue
    return header[:i].strip(),header[i+1:].strip()
  return None
 if split720('const std::pair<int,int>& [a,b] : requested_extensions')!=(
     'const std::pair<int,int>& [a,b]','requested_extensions'):
  raise ValueError('PRE720_CPP_NAMESPACE_SEPARATOR_SELF_TEST')
 if split720('auto& ext : x.y()')!=('auto& ext','x.y()'):
  raise ValueError('PRE720_CPP_MEMBER_SEPARATOR_SELF_TEST')
 def for720(n):
  p=parse_bounded_parentheses(instance_lines,n,'for')
  if not p.get('extracted'):return {'line':n,'header_extracted':False}
  head=mask_cpp(p['text'])
  pair=split720(head)
  if pair is None:return {'line':n,'header_extracted':True,
    'range_separator_found':False,'header_sha256':h720(head)}
  lhs,rhs=pair
  simple=re.fullmatch(r'[A-Za-z_]\w*',rhs)
  item=report['pre719_pointer_count_mutation_audit']['source_findings']
  name=rhs if simple else None
  return {'line':n,'header_extracted':True,'range_separator_found':True,
   'header_sha256':h720(head),'lhs_sha256':h720(lhs),'rhs_sha256':h720(rhs),
   'lhs_has_auto':bool(re.search(r'\bauto\b',lhs)),
   'lhs_has_structured_binding':bool(re.search(r'\[[^\]]+\]',lhs)),
   'lhs_has_namespace_qualification':'::' in lhs,
   'lhs_has_reference':'&' in lhs,
   'rhs_simple_identifier':bool(name),
   'rhs_identifier_sha256':h720(name) if name else None,
   'rhs_matches_initial_names_vector':bool(name and h720(name)==item['initial_pointer_source_sha256']),
   'rhs_mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',rhs)),
   'rhs_mentions_enabled_extensions':bool(re.search(r'\benabled_extensions\b',rhs)),
   'rhs_has_namespace_qualification':'::' in rhs,
   'rhs_has_member_access':bool(re.search(r'(?:\.|->)\s*\w+',rhs)),
   'rhs_function_call_shape':bool(re.search(r'\b\w+\s*\(',rhs)),
   'rhs_view_pipe':bool(re.search(r'(?<!\|)\|(?!\|)',rhs)),
   'rhs_has_ternary':'?' in rhs,
   'actual_cxx_value_or_alias':'NOT_VERIFIED',
   'raw_header_exported':False}
 def rhs720(n):
  row=mask_cpp(instance_lines[n-1])
  m=re.search(r'\benabledExtensionCount\b\s*=\s*([^;]+)',row)
  if not m:return {'line':n,'assignment_found':False}
  rhs=m.group(1).strip()
  old=report['pre719_pointer_count_mutation_audit']['source_findings']['line_535_count_rhs']
  if h720(rhs)!=old['rhs_sha256']:
   raise ValueError('PRE720_RHS_HASH_DIFFERS_FROM_AUTHENTICATED_PRE719')
  number=re.fullmatch(r'(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|\d+)[uUlL]*',rhs)
  nvalue=None
  if number:
   core=re.sub('[uUlL]+$','',rhs)
   try:nvalue=int(core,0) if core.lower().startswith(('0x','0b')) else int(core)
   except ValueError:nvalue=None
  simple=bool(re.fullmatch(r'[A-Za-z_]\w*',rhs))
  calls=bool(re.search(r'\b\w+(?:(?:::|\.|->)\w+)*\s*\(',rhs))
  member=bool(re.search(r'(?:\.|->)\s*\w+',rhs))
  cast=bool(re.search(r'\b(?:static_cast|reinterpret_cast|const_cast|dynamic_cast)\s*<',rhs))
  ternary=('?' in rhs and ':' in rhs)
  binary=bool(re.search(r'\+|<<|>>|&&|\|\||(?<!\|)\|(?!\|)|(?<!&)&(?!&)',rhs))
  if number:typ='integer_literal'
  elif rhs in ('true','false'):typ='boolean_literal'
  elif rhs in ('nullptr','NULL'):typ='null_literal'
  elif simple:typ='simple_identifier'
  elif ternary:typ='ternary_expression'
  elif cast:typ='cast_expression'
  elif calls:typ='function_or_method_call_shape'
  elif member:typ='member_access_expression'
  elif binary:typ='binary_expression'
  else:typ='complex_or_unclassified_expression'
  return {'line':n,'assignment_found':True,'rhs_sha256':h720(rhs),
   'syntactic_category':typ,'integer_literal':bool(number),
   'integer_literal_is_zero':bool(number and nvalue==0),
   'rhs_simple_identifier':simple,'rhs_function_call_shape':calls,
   'rhs_member_access_shape':member,'rhs_cast_shape':cast,
   'rhs_ternary_shape':ternary,'rhs_binary_shape':binary,
   'rhs_contains_size_call':bool(re.search(r'\.\s*size\s*\(',rhs)),
   'rhs_contains_std_namespace':'std::' in rhs,
   'rhs_contains_vk_token':bool(re.search(r'\bVK_\w+\b',rhs)),
   'actual_cpp_type':'NOT_VERIFIED','actual_runtime_value':'NOT_VERIFIED',
   'raw_rhs_exported':False}
 def line532(n):
  s=mask_cpp(instance_lines[n-1])
  return {'line':n,'line_sha256':h720(instance_lines[n-1]),
   'if_keyword':bool(re.search(r'\bif\s*\(',s)),
   'assignment_operator':bool(re.search(r'(?<![=!<>])=(?!=)',s)),
   'increment_operator':bool(re.search(r'\+\+|--',s)),
   'has_function_call':bool(re.search(r'\b\w+\s*\(',s)),
   'has_member_access':bool(re.search(r'(?:\.|->)\s*\w+',s)),
   'raw_line_exported':False}
 x531=for720(531)
 x528=for720(528)
 x535=rhs720(535)
 report['pre720_range_rhs_syntax_audit']={
  'stage':'PRE720_AUTHENTICATED_V51_RANGE531_COUNT535_SYNTAX_READONLY',
  'analysis_type':'BOUNDED_LEXICAL_CPP_NAMESPACE_AWARE_RANGE_FOR_AND_COUNT_EXPRESSION',
  'source_sha_checks_inherited':True,
  'source_findings':{
   'loop531':x531,'loop528_control':x528,
   'extension_count_535_rhs':x535,'loop531_body_line532':line532(532),
   'source_text_exported':False,'identifier_spelling_exported':False,
   'cpp_ast_or_cfg_proven':False,'pointer_lifetime_proven':False,
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'runtime_vkCreateInstance_result':'NOT_VERIFIED',
   'source_to_signed_apk_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'apk_built':False,'apk_modified':False,
   'signing_material_accessed':False,'fps_gain_proven':False},
  'stale_pointer_bug_proven':False,
  'extension_count_mismatch_proven':False,
  'source_or_apk_modified':False}
 report['analysis_type']='PRE720_AUTHENTICATED_V51_RANGE_RHS_LEXICAL_CLASSIFICATION'
 report['status']=('PASS_PRE720_V51_RANGE531_COUNT535_LEXICAL_CLASSIFIED'
  if x531['header_extracted'] and x531['range_separator_found']
     and x528['range_separator_found'] and x535['assignment_found']
  else 'BLOCK_PRE720_SOURCE_SYNTAX_ANCHORS_UNRESOLVED')
"""

def code(manifest,archive,run,attempt):
    src=pre719.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1: raise ValueError('PRE720_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
       ('NFSMW_PRE719_KAGGLE_REMOTE.json',MARKER),
       ('PRE719_V51_KAGGLE_POINTER_COUNT_MUTATION_READONLY',
        'PRE720_V51_KAGGLE_RANGE_RHS_SYNTAX_READONLY'),
       ("print('PRE719_KAGGLE_GATE=","print('PRE720_KAGGLE_GATE="),
       ("print('PRE719_REPORT=","print('PRE720_REPORT=")
    ):
        if old not in src: raise ValueError('PRE720_PARENT_MISSING_TOKEN '+old)
        src=src.replace(old,new)
    compile(src,'<PRE720 isolated Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre720.ipynb',
          'language':'python','kernel_type':'notebook','is_private':True,
          'enable_gpu':False,'enable_internet':False,'dataset_sources':[],
          'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,
      'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre720-purpose','metadata':{},
       'source':['V51 authenticated lexical audit of range-for 531 and count RHS 535. No source export.']},
      {'cell_type':'code','id':'pre720-readonly','metadata':{},
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
        src=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'fixture','123','1')
        assert MARKER in src
        assert 'PASS_PRE720_V51_RANGE531_COUNT535_LEXICAL_CLASSIFIED' in src
        assert "'source_text_exported':False" in src
        assert "'stale_pointer_bug_proven':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE720_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('invalid run IDs')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
      manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE720_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE720_BAD_DEVICE_INSTANCE_HASHES')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE720_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre720.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE720_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
