#!/usr/bin/env python3
"""PRE712: narrow V51 Vulkan source guard/lookup syntax audit in isolated private Kaggle.
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

KERNEL="juniklx/nfsmw-pre712-v51-alias-guards-readonly"
TITLE="NFSMW PRE712 V51 Alias Guards Readonly"
MARKER="NFSMW_PRE712_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE711_SOURCE_RELATIONSHIP_CHECKS')"
EXTRA=r"""
 # PRE712 — bounded C++ source probes: aliases, condition callee, push_back destination.
 # Lexical token-level evidence only. No source text exported, no AST/CFG/runtime proof.
 def pre712_sha(v):
  return hashlib.sha256(v.encode('utf-8')).hexdigest()
 def pre712_token(v,name):
  return bool(re.search(r'\b'+re.escape(name)+r'\b',v)) if name else False
 def pre712_simple(v):
  v=v.strip().strip('() ')
  return v if re.fullmatch(r'[A-Za-z_]\w*',v) else None
 def pre712_equality(expr):
  v=mask_cpp(expr)
  m=list(re.finditer(r'(?<![!<>=])==(?!=)',v))
  if len(m)!=1:return None,None
  n=m[0].start()
  return pre712_simple(v[:n]),v[n+2:].strip()
 def pre712_receiver(expr):
  m=re.search(r'(?<!\w)([A-Za-z_]\w*)\s*(\.|->)\s*([A-Za-z_]\w*)\s*(?:\.|->)\s*c_str\s*\(',mask_cpp(expr))
  return m.groups() if m else None
 def pre712_assignments(lines,loopline,ifline,alias,loopvar):
  # Inspect only the short lexical scope preceding the guard, not global source.
  s=mask_cpp('\n'.join(lines[loopline-1:ifline-1]))
  assignments=[]
  # Whole logical statement boundary limited to 600 chars, search no raw source output.
  for m in re.finditer(r'\b'+re.escape(alias)+r'\s*=(?!=)\s*',s) if alias else []:
   start=m.end()
   end=s.find(';',start)
   if end<0 or end-start>600:continue
   expr=s[start:end].strip()
   pre=s[max(0,m.start()-100):m.start()]
   assignments.append({
      'initializer_sha256':pre712_sha(expr),
      'declaration_auto_nearby':bool(re.search(r'\bauto\s*(?:\*|&|const|\s)*$',pre)),
      'initializer_mentions_range_variable':pre712_token(expr,loopvar),
      'initializer_mentions_requested_extensions':pre712_token(expr,'requested_extensions'),
      'initializer_mentions_available_extensions':pre712_token(expr,'available_extensions'),
      'initializer_mentions_enabled_extensions':pre712_token(expr,'enabled_extensions'),
      'calls_std_find_or_find_if':bool(re.search(r'\bstd\s*::\s*(?:ranges\s*::\s*)?find(?:_if)?\s*(?:<[^>]{1,80}>)?\s*\(',expr)),
      'calls_member_find':bool(re.search(r'(?:\.|->)\s*find\s*\(',expr)),
      'calls_member_end':bool(re.search(r'(?:\.|->)\s*end\s*\(',expr)),
      'lambda_capture_present':'[' in expr and ']' in expr,
      'initializer_values_not_exported':True})
  return {'window_lines':[loopline,ifline-1],
     'alias_assignment_candidates':len(assignments),
     'candidates':assignments[:3],
     'window_references_alias':pre712_token(s,alias),
     'window_references_range_var':pre712_token(s,loopvar),
     'assignments_outside_window':'NOT_VERIFIED',
     'cpp_alias_or_pointer_identity':'NOT_VERIFIED'}
 def pre712_guard(rhs,alias):
  v=mask_cpp(rhs) if rhs else ''
  return {'rhs_mentions_requested_extensions':pre712_token(v,'requested_extensions'),
    'rhs_has_member_end':bool(re.search(r'(?:\.|->)\s*end\s*\(',v)),
    'rhs_has_member_size':bool(re.search(r'(?:\.|->)\s*size\s*\(',v)),
    'rhs_mentions_alias':pre712_token(v,alias),
    'rhs_is_direct_identifier':bool(pre712_simple(v)),
    'rhs_sha256':pre712_sha(rhs) if rhs else None,
    'rhs_cpp_meaning':'NOT_VERIFIED'}
 def pre712_predicate(expr,alias,loopvar):
  s=mask_cpp(expr).strip()
  # Extract callee only if negation is followed by a free/scoped function identifier.
  m=re.match(r'^!\s*((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)\s*(?:<|\()',s)
  callee=m.group(1) if m else None
  if not m:
   m2=re.match(r'^!\s*([A-Za-z_]\w*(?:(?:\.|->)[A-Za-z_]\w*)+)\s*(?:<|\()',s)
   callee=m2.group(1) if m2 else None
  return {'starts_negation':s.startswith('!'),
    'negated_callee_lexically_parsed':callee is not None,
    'callee_hash':pre712_sha(callee) if callee else None,
    'callee_scoped':bool(callee and '::' in callee),
    'callee_member_access':bool(callee and ('.' in callee or '->' in callee)),
    'callee_starts_std':bool(callee and callee.startswith('std::')),
    'template_angle_seen':bool(re.search(r'<',s)),
    'mentions_alias':pre712_token(s,alias),
    'mentions_loop_variable':pre712_token(s,loopvar),
    'mentions_enabled_extensions':pre712_token(s,'enabled_extensions'),
    'mentions_requested_extensions':pre712_token(s,'requested_extensions'),
    'cpp_predicate_semantics':'NOT_VERIFIED','callee_name_not_exported':True}
 def pre712_push(lines,begin,end,alias,loopvar):
  s=mask_cpp('\n'.join(lines[begin-1:end]))
  # Captures simple receiver and bounded call argument fingerprint, not AST nesting.
  out=[]
  for m in re.finditer(r'(?<!\w)([A-Za-z_]\w*)\s*(?:\.|->)\s*push_back\s*\(',s):
   dest=m.group(1);start=m.end()
   # If nested parentheses, stop at first close; this is explicitly lexical only.
   close=s.find(')',start);arg=s[start:close] if close>=0 else ''
   prefix=mask_cpp('\n'.join(lines[max(0,begin-40):begin-1]))
   defs=[re.sub(r'\s+',' ',x.group(0)).strip() for x in re.finditer(
      r'(?m)(?:^|;|\{|\})\s*(?:[A-Za-z_]\w*(?:::\w+)?[<>,\s*&:]*)\b'+re.escape(dest)+r'\s*(?:[=;(])',prefix)]
   out.append({'receiver_hash':pre712_sha(dest),
     'receiver_same_as_alias':dest==alias,
     'receiver_same_as_loopvar':dest==loopvar,
     'receiver_is_enabled_extensions':dest=='enabled_extensions',
     'receiver_is_requested_extensions':dest=='requested_extensions',
     'receiver_definition_candidate_count_in_40_lines':len(defs),
     'receiver_def_candidate_hashes':[pre712_sha(x) for x in defs[:3]],
     'argument_lexical_sha256':pre712_sha(arg),
     'argument_mentions_alias':pre712_token(arg,alias),
     'argument_mentions_loopvar':pre712_token(arg,loopvar),
     'argument_mentions_enabled_extensions':pre712_token(arg,'enabled_extensions'),
     'argument_values':'NOT_VERIFIED','destination_cpp_type':'NOT_VERIFIED',
     'only_first_closing_parenthesis_used':True})
  return {'call_count':len(out),'calls':out,'destination_runtime_values':'NOT_VERIFIED'}
 targets={
   'device':(device_lines,283,286,290,291,(291,293)),
   'instance':(instance_lines,445,448,454,455,(455,458))
 }
 analyses={}
 for label,(lines,loop,first,second,insert,body) in targets.items():
  prior=report['pre711_operand_links']['files'][label]
  a=parse_bounded_parentheses(lines,first,'if')
  b=parse_bounded_parentheses(lines,second,'if')
  c=parse_bounded_parentheses(lines,insert,'emplace_back')
  if not all(x['extracted'] for x in (a,b,c)):
   raise ValueError('PRE712_PRE711_PARENT_EXTRACTION_FAILED')
  alias,rhs=pre712_equality(a['text'])
  rec=pre712_receiver(c['text'])
  loopinfo,loopvar=range711(lines[loop-1])
  if not alias or not rec:
   raise ValueError('PRE712_ALIAS_RECEIVER_STRUCTURE_UNRECOGNIZED')
  if pre712_sha(alias)!=prior['first_guard_equality']['left_hash']:
   raise ValueError('PRE712_LEFT_OPERAND_DRIFT')
  if alias!=rec[0] or pre712_sha(rec[2])!=prior['cstr_receiver']['member_name_sha256']:
   raise ValueError('PRE712_RECEIVER_IDENTITY_DRIFT')
  if pre712_sha(rhs)!=prior['first_guard_equality']['right_hash']:
   raise ValueError('PRE712_RIGHT_OPERAND_DRIFT')
  if pre712_sha(loopvar)!=prior['for_binding']['iterator_id_sha256']:
   raise ValueError('PRE712_LOOP_VARIABLE_DRIFT')
  analyses[label]={
    'alias_text_hash':pre712_sha(alias),
    'alias_same_as_loop_variable':alias==loopvar,
    'bounded_pre_guard_assignments':pre712_assignments(lines,loop,first,alias,loopvar),
    'comparison_rhs':pre712_guard(rhs,alias),
    'negated_condition_callee':pre712_predicate(b['text'],alias,loopvar),
    'second_guard_body_push_back':pre712_push(lines,*body,alias,loopvar),
    'cpp_symbol_binding':'NOT_VERIFIED'}
 consistency={
   'same_alias_hash':analyses['device']['alias_text_hash']==analyses['instance']['alias_text_hash'],
   'same_rhs_shape':analyses['device']['comparison_rhs']==analyses['instance']['comparison_rhs'],
   'same_negated_callee_tokens':analyses['device']['negated_condition_callee']==analyses['instance']['negated_condition_callee'],
   'extra_push_only_instance':analyses['instance']['second_guard_body_push_back']['call_count']==1 and analyses['device']['second_guard_body_push_back']['call_count']==0
 }
 report['pre712_alias_guard_audit']={
  'stage':'PRE712_V51_BOUNDED_ALIAS_PREDICATE_PUSHBACK',
  'authenticated_v51_source':True,'files':analyses,
  'pair_consistency':consistency,
  'cpp_ast_and_cfg_proven':False,
  'runtime_enabled_extensions':'NOT_VERIFIED',
  'vk_google_display_timing_enabled':'NOT_VERIFIED',
  'installed_apk_binary_identity':'UNVERIFIED',
  'raw_cpp_source_exported':False,'signing_material_accessed':False,
  'apk_built':False,'apk_modified':False,'fps_gain_proven':False}
 report['analysis_type']='PRE712_BOUNDED_ALIAS_PREDICATE_PUSHBACK_LEXICAL_ONLY'
 report['status']=('PASS_PRE712_V51_AUTHENTICATED_BOUNDED_DATAFLOW_READONLY'
   if all(consistency.values())
     and all(x['comparison_rhs']['rhs_mentions_requested_extensions'] for x in analyses.values())
   else 'BLOCK_PRE712_ALIAS_CONSISTENCY')
"""
def code(manifest,archive,run,attempt):
    src=pre711.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE712_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE711_KAGGLE_REMOTE.json',MARKER),
        ('PRE711_V51_KAGGLE_OPERAND_LINKS_READONLY',
         'PRE712_V51_KAGGLE_ALIAS_GUARDS_READONLY'),
        ("print('PRE711_KAGGLE_GATE=","print('PRE712_KAGGLE_GATE="),
        ("print('PRE711_REPORT=","print('PRE712_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE712_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE712 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre712.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre712-purpose','metadata':{},
                  'source':['Authenticated V51 bounded C++ alias, condition callee and push_back lexical dataflow; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre712-readonly','metadata':{},
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
        assert MARKER in src and 'PRE712_BOUNDED_ALIAS_PREDICATE_PUSHBACK_LEXICAL_ONLY' in src
        assert 'PASS_PRE712_V51_AUTHENTICATED_BOUNDED_DATAFLOW_READONLY' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE712_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE712_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE712_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE712_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre712.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE712_PRIVATE_KERNEL='+KERNEL)
    print('PRE712_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
