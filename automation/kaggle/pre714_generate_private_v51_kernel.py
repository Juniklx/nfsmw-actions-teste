#!/usr/bin/env python3
"""PRE714: bounded source alias, predicate and push_back audit in private Kaggle.
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

KERNEL="juniklx/nfsmw-pre714-v51-negation-container-readonly"
TITLE="NFSMW PRE714 V51 Negation Container Readonly"
MARKER="NFSMW_PRE714_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE713_FIND_OR_SENTINEL_STRUCTURE')"
EXTRA=r"""
 # PRE714 — balanced expression fingerprint, no export of proprietary identifiers.
 # The tokens below are structural, NOT a C++ AST, evaluation or ABI proof.
 def p714hash(v):return hashlib.sha256(v.encode('utf-8')).hexdigest()
 def p714skeleton(expression):
  clean=mask_cpp(expression).strip()
  raw=re.findall(r'::|->|&&|\|\||==|!=|<=|>=|[A-Za-z_]\w*|[0-9]+|[^\s]',clean)
  known={'true':'BOOL','false':'BOOL','nullptr':'NULL','const':'CONST',
         'auto':'AUTO','std':'STD','get':'GET','second':'SECOND',
         'first':'FIRST','has_value':'HAS_VALUE','value':'VALUE'}
  abstract=[]
  for t in raw[:64]:
   if re.fullmatch(r'[A-Za-z_]\w*',t):abstract.append(known.get(t,'IDENT'))
   elif re.fullmatch(r'[0-9]+',t):abstract.append('NUMBER')
   else:abstract.append(t)
  clean_no_whitespace=''.join(clean.split())
  return {'skeleton':abstract,
   'token_count':len(raw),
   'truncated':len(raw)>64,
   'starts_negation':clean.startswith('!'),
   'parenthesis_balance':clean.count('(')-clean.count(')'),
   'angle_balance':clean.count('<')-clean.count('>'),
   'has_member_arrow':'->' in clean,
   'has_member_dot':'.' in clean,
   'has_scope_colons':'::' in clean,
   'get_template_syntax':bool(re.search(r'(?:\bget|->\s*get|\.get)\s*<',clean)),
   'angle_tokens_may_be_templates':('<' in clean or '>' in clean),
   'expr_sha256':p714hash(expression.strip()),
   'runtime_predicate_value':'NOT_VERIFIED','cpp_ast_proven':False}
 def p714_container_line(lines,lineno,target_hash):
  source=lines[lineno-1]
  clean=mask_cpp(source)
  types=sorted(set(re.findall(r'\bstd\s*::\s*(vector|deque|list|set|unordered_set|map|unordered_map|array)\s*<',clean)))
  names=set(re.findall(r'\b[A-Za-z_]\w*\b',clean))
  candidates=[name for name in names if p714hash(name)==target_hash]
  return {'line':lineno,'line_sha256':p714hash(source),
    'std_container_tokens':types,
    'receiver_identifier_present_in_same_line':bool(candidates),
    'receiver_has_assignment_in_line':bool(candidates and re.search(
      r'\b'+re.escape(candidates[0])+r'\s*=',clean)),
    'receiver_has_semicolon_after_identifier':bool(candidates and
      re.search(r'\b'+re.escape(candidates[0])+r'\s*;',clean)),
    'cpp_declaration_type_proven':False,
    'variable_name_exported':False,'container_runtime_contents':'NOT_VERIFIED'}
 def p714_push(lines,begin,end,target_hash):
  hits=[]
  for lineno in range(begin,end+1):
   clean=mask_cpp(lines[lineno-1])
   m=re.search(r'\b([A-Za-z_]\w*)\s*(?:\.|->)\s*push_back\s*\(',clean)
   if not m:continue
   extracted=parse_bounded_parentheses(lines,lineno,'push_back')
   rhs=extracted['text'].strip() if extracted['extracted'] else None
   hits.append({'line':lineno,'target_sha256':p714hash(m.group(1)),
     'same_target_hash_as_prior':p714hash(m.group(1))==target_hash,
     'argument_extracted':bool(rhs is not None),
     'argument_sha256':p714hash(rhs) if rhs is not None else None,
     'argument_skeleton':p714skeleton(rhs)['skeleton'] if rhs is not None else [],
     'argument_values':'NOT_VERIFIED'})
  return hits
 tests={'device':(device_lines,290,291),
        'instance':(instance_lines,454,455)}
 groups={}
 for label,(lines,guard,insert) in tests.items():
  expr=parse_bounded_parentheses(lines,guard,'if')
  if not expr['extracted']:raise ValueError('PRE714_SECOND_GUARD_PARSE_UNRESOLVED')
  previous=report['pre713_find_sentinel_audit']['files'][label]['negated_guard']
  structure=p714skeleton(expr['text'])
  if structure['expr_sha256']!=previous['expression_sha256']:
   raise ValueError('PRE714_PREDICATE_HASH_DRIFT')
  result={'negated_guard_line':guard,
          'negated_expression_structure':structure,
          'vk_device_extension_list':'NOT_VERIFIED'}
  if label=='instance':
   prior=report['pre712_alias_guard_audit']['files']['instance']['second_guard_body_push_back']
   target=prior['calls'][0]['receiver_hash']
   result['pushback_container_reference_line356']=p714_container_line(lines,356,target)
   result['pushback_calls_near_insert']=p714_push(lines,455,459,target)
   result['prior_pushback_receiver_hash_matches_report']=(
     bool(result['pushback_calls_near_insert']) and all(
        q['same_target_hash_as_prior'] for q in result['pushback_calls_near_insert']))
  groups[label]=result
 equality={
   'same_guard_source_hash':groups['device']['negated_expression_structure']['expr_sha256']==groups['instance']['negated_expression_structure']['expr_sha256'],
   'same_guard_abstract_skeleton':groups['device']['negated_expression_structure']['skeleton']==groups['instance']['negated_expression_structure']['skeleton'],
   'instance_push_receiver_hash_matches':groups['instance']['prior_pushback_receiver_hash_matches_report']}
 report['pre714_negation_container']={
   'stage':'PRE714_V51_NEGATED_PREDICATE_AND_INSTANCE_CONTAINER',
   'files':groups,'consistency':equality,'source_hashes_authenticated':True,
   'analysis_scope':'CONSERVATIVE_LEXICAL_SKELETON_NO_CPP_AST',
   'raw_source_exported':False,'secret_material_accessed':False,
   'cpp_ast_or_cfg_proven':False,
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'signed_apk_binary_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'apk_built':False,'apk_modified':False,'fps_gain_proven':False}
 report['analysis_type']='PRE714_NEGATION_AND_PUSH_CONTAINER_SOURCE_STRUCTURE_ONLY'
 report['status']=('PASS_PRE714_AUTHENTICATED_V51_NEGATION_CONTAINER_LEXICAL'
   if all(equality.values()) and
      groups['instance']['pushback_container_reference_line356']['receiver_identifier_present_in_same_line']
   else 'BLOCK_PRE714_NEGATION_OR_CONTAINER_UNRESOLVED')
"""
def code(manifest,archive,run,attempt):
    src=pre713.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE714_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE713_KAGGLE_REMOTE.json',MARKER),
        ('PRE713_V51_KAGGLE_FIND_SENTINELS_READONLY',
         'PRE714_V51_KAGGLE_NEGATION_CONTAINER_READONLY'),
        ("print('PRE713_KAGGLE_GATE=","print('PRE714_KAGGLE_GATE="),
        ("print('PRE713_REPORT=","print('PRE714_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE714_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE714 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre714.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre714-purpose','metadata':{},
                  'source':['Authenticated V51 bounded C++ alias, condition callee and push_back lexical dataflow; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre714-readonly','metadata':{},
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
        assert MARKER in src and 'PRE714_NEGATION_AND_PUSH_CONTAINER_SOURCE_STRUCTURE_ONLY' in src
        assert 'PASS_PRE714_AUTHENTICATED_V51_NEGATION_CONTAINER_LEXICAL' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE714_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE714_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE714_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE714_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre714.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE714_PRIVATE_KERNEL='+KERNEL)
    print('PRE714_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
