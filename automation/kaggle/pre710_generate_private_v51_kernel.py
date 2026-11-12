#!/usr/bin/env python3
"""PRE710: narrow V51 Vulkan source guard/lookup syntax audit in isolated private Kaggle.
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

KERNEL="juniklx/nfsmw-pre710-v51-guards-and-lookup-readonly"
TITLE="NFSMW PRE710 V51 Guards And Lookup Readonly"
MARKER="NFSMW_PRE710_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE709_STRUCTURE_NOT_AUTHENTICATED')"
EXTRA=r"""
 # PRE710 — bounded syntactic statements, free-function/member lookup & c_str origin.
 # It is NOT a C++ AST and cannot resolve runtime extension lists.
 def pre710_sha(s):
  return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def line_kind_list(fragment):
  clean=mask_cpp(fragment)
  return {
   'contains_continue':bool(re.search(r'\bcontinue\s*;',clean)),
   'contains_break':bool(re.search(r'\bbreak\s*;',clean)),
   'contains_return':bool(re.search(r'\breturn\b',clean)),
   'contains_throw':bool(re.search(r'\bthrow\b',clean)),
   'contains_goto':bool(re.search(r'\bgoto\b',clean)),
   'contains_emplace_back':bool(re.search(r'\bemplace_back\s*\(',clean)),
   'contains_push_back':bool(re.search(r'\bpush_back\s*\(',clean)),
   'contains_assignment':bool(re.search(r'(?<![!<>=])=(?!=)',clean)),
   'contains_if':bool(re.search(r'\bif\s*\(',clean)),
  }
 def body_tags(lines,start,end):
  if not 1<=start<=end<=len(lines):raise ValueError('PRE710_BODY_BOUNDS')
  source='\n'.join(lines[start-1:end])
  if 'R"(' in source or re.search(r'^\s*#',source,re.M):
   return {'status':'UNKNOWN_MACRO_OR_RAW_STRING','line_range':[start,end],
           'body_sha256':pre710_sha(source)}
  m=mask_cpp(source)
  signature=line_kind_list(source)
  return {'status':'BOUNDED_LEXICAL_BODY_STATEMENTS',
          'line_range':[start,end],
          'body_sha256':pre710_sha(source),
          'statement_flags':signature,
          'semicolon_count':m.count(';'),
          'source_exported':False,'executed_branch_proven':False}
 def condition_tokens(expression):
  e=expression.strip()
  return {
   'expression_sha256':pre710_sha(e),
   'references_requested_extensions':bool(re.search(r'\brequested_extensions\b',e)),
   'calls_free_std_find':bool(re.search(r'\bstd\s*::\s*(?:ranges\s*::\s*)?find\s*(?:<[^>]{0,70}>)?\s*\(',e)),
   'calls_member_find':bool(re.search(r'(?:\.|->)\s*find\s*\(',e)),
   'calls_member_end':bool(re.search(r'(?:\.|->)\s*end\s*\(',e)),
   'calls_member_contains':bool(re.search(r'(?:\.|->)\s*contains\s*\(',e)),
   'calls_member_count':bool(re.search(r'(?:\.|->)\s*count\s*\(',e)),
   'starts_with_negation':e.startswith('!'),
   'invocation_after_negation':bool(re.match(r'!\s*(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*\s*(?:<[^>]{1,100}>)?\s*\(',e)),
   'contains_double_colon':bool('::' in e),
   'contains_end_member_of_requested_extensions':bool(re.search(r'\brequested_extensions\s*(?:\.|->)\s*end\s*\(',e)),
   'contains_comparison_equal':'==' in e,
   'contains_comparison_not_equal':'!=' in e,
   'operator_angle_ambiguous':bool('<' in e or '>' in e),
   'string_literal_values_exported':False,
  }
 def cstr_receiver_signature(expression):
  e=expression.strip()
  # Recognizes simple identifiers/member chains only. Anything more complex stays unknown.
  pattern=r'(?<!\w)([A-Za-z_]\w*(?:\s*(?:\.|->)\s*[A-Za-z_]\w*){0,4})\s*(?:\.|->)\s*c_str\s*\('
  finds=list(re.finditer(pattern,e))
  allowable={'extension','ext','extension_name','name','property',
    'extensionName','extension_property','requested_extension','available_extension',
    'enabled_extension','requested_extensions'}
  out=[]
  for m in finds[:6]:
   receiver=re.sub(r'\s+','',m.group(1))
   atoms=re.findall(r'\b[A-Za-z_]\w*\b',receiver)
   out.append({'receiver_sha256':pre710_sha(receiver),
      'receiver_identifier_count':len(atoms),
      'receiver_is_simple_identifier':len(atoms)==1,
      'receiver_allowed_identifier':receiver if receiver in allowable else None,
      'receiver_contains_member_access':len(atoms)>1})
  return {'c_str_calls_detected':len(re.findall(r'(?:\.|->)\s*c_str\s*\(',e)),
   'simple_receiver_chains_resolved':len(out),
   'receiver_fingerprints':out,
   'receiver_complex_unresolved':bool(re.search(r'\bc_str\s*\(',e)) and not bool(out),
   'argument_expr_sha256':pre710_sha(e),
   'no_unknown_identifier_export':True}
 def bounded_for_signature(lines,index):
  source=lines[index-1]
  clean=mask_cpp(source)
  if 'for' not in clean:return {'line':index,'for_token_found':False}
  m=re.search(r'\bfor\s*\(([^)]*)\)',clean)
  if not m:return {'line':index,'for_token_found':True,'header_parse':'UNRESOLVED'}
  head=m.group(1)
  return {'line':index,'for_token_found':True,
          'has_range_for_colon':bool(re.search(r'(?<!:):(?!:)',head)),
          'mentions_const':bool(re.search(r'\bconst\b',head)),
          'mentions_auto':bool(re.search(r'\bauto\b',head)),
          'mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',head)),
          'mentions_available_extensions':bool(re.search(r'\bavailable_extensions\b',head)),
          'mentions_enabled_extensions':bool(re.search(r'\benabled_extensions\b',head)),
          'header_sha256':pre710_sha(head),
          'range_variable_proven':False}
 targets={
  'device':(device_lines,283,286,(287,288),290,(291,293),291),
  'instance':(instance_lines,445,448,(449,450),454,(455,458),455)
 }
 result={}
 for label,(lines,forline,first_if,first_range,second_if,second_range,add_line) in targets.items():
  prior=report['pre709_lookup_guards']['files'][label]
  scopes=prior['conditions']
  if (scopes[0]['lexical_scope'].get('status')!='BRACED_LEXICAL_SCOPE_ONLY' or
      scopes[1]['lexical_scope'].get('status')!='BRACED_LEXICAL_SCOPE_ONLY' or
      scopes[0]['lexical_scope']['brace_contains_target_line_start'] is not False or
      scopes[1]['lexical_scope']['brace_contains_target_line_start'] is not True):
   raise ValueError('PRE710_PRIOR_SCOPE_NOT_PROVEN')
  pfirst=parse_bounded_parentheses(lines,first_if,'if')
  psecond=parse_bounded_parentheses(lines,second_if,'if')
  pinsert=parse_bounded_parentheses(lines,add_line,'emplace_back')
  if not all(x['extracted'] for x in (pfirst,psecond,pinsert)):
   raise ValueError('PRE710_PARENT_EXPRESSION_PARSE_FAILED')
  if (pre710_sha(pfirst['text'].strip())!=prior['conditions'][0]['expression']['sha256'] or
      pre710_sha(psecond['text'].strip())!=prior['conditions'][1]['expression']['sha256'] or
      pre710_sha(pinsert['text'].strip())!=prior['insertion']['expression']['sha256']):
   raise ValueError('PRE710_EXPRESSION_HASH_DRIFT')
  result[label]={
   'first_if':{'line':first_if,'conditions':condition_tokens(pfirst['text']),
      'body':body_tags(lines,*first_range),
      'lexically_contains_insertion':False},
   'second_if':{'line':second_if,'conditions':condition_tokens(psecond['text']),
      'body':body_tags(lines,*second_range),
      'lexically_contains_insertion':True},
   'insertion':{'line':add_line,'argument':cstr_receiver_signature(pinsert['text'])},
   'nearby_loop':bounded_for_signature(lines,forline),
   'cpp_semantic_execution_proven':False,
   'requested_names_actual_values':'NOT_VERIFIED',
   'enabled_names_actual_values':'NOT_VERIFIED',
  }
 same={
  'first_body_flags_equal':result['device']['first_if']['body'].get('statement_flags')==result['instance']['first_if']['body'].get('statement_flags'),
  'first_condition_flags_equal':result['device']['first_if']['conditions']==result['instance']['first_if']['conditions'],
  'second_condition_flags_equal':result['device']['second_if']['conditions']==result['instance']['second_if']['conditions'],
  'cstr_receiver_summary_equal':result['device']['insertion']['argument']==result['instance']['insertion']['argument'],
 }
 report['pre710_statement_receiver_audit']={
  'stage':'PRE710_V51_GUARD_BODY_STATEMENT_AND_CSTR_RECEIVER',
  'authenticated_v51_sources':True,
  'files':result,
  'pair_consistency':same,
  'full_cpp_ast_or_cfg_proven':False,
  'runtime_extension_names':'NOT_VERIFIED',
  'source_to_signed_elf_equivalence':'UNVERIFIED',
  'apk_compiled':False,'apk_modified':False,
  'private_signing_material_accessed':False,
  'raw_cpp_source_exported':False,
  'fps_gain_proven':False,
 }
 report['analysis_type']='PRE710_BOUNDED_GUARD_STATEMENTS_AND_CSTR_RECEIVER_ONLY'
 report['status']=('PASS_AUTHENTICATED_V51_GUARD_STATEMENTS_LEXICAL_ONLY'
    if all(same.values()) and all(
      x['first_if']['body']['status']=='BOUNDED_LEXICAL_BODY_STATEMENTS'
      for x in result.values())
    else 'BLOCK_PRE710_GUARD_BODY_UNRESOLVED')
"""
def code(manifest,archive,run,attempt):
    src=pre709.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE710_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE708_KAGGLE_REMOTE.json',MARKER),
        ('PRE708_V51_KAGGLE_CONDITION_ARGUMENT_SYNTAX_READONLY',
         'PRE710_V51_KAGGLE_EXTENSION_LOOKUP_GUARDS_READONLY'),
        ("print('PRE708_KAGGLE_GATE=","print('PRE710_KAGGLE_GATE="),
        ("print('PRE708_REPORT=","print('PRE710_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE710_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE710 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre710.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre710-purpose','metadata':{},
                  'source':['Authenticated V51 Vulkan extension-list lexical scope review; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre710-readonly','metadata':{},
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
        assert MARKER in src and 'PRE710_BOUNDED_GUARD_STATEMENTS_AND_CSTR_RECEIVER_ONLY' in src
        assert 'PASS_AUTHENTICATED_V51_GUARD_STATEMENTS_LEXICAL_ONLY' in src
        assert "'runtime_extension_names':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE710_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE710_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE710_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE710_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre710.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE710_PRIVATE_KERNEL='+KERNEL)
    print('PRE710_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
