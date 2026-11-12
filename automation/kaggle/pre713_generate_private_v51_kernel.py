#!/usr/bin/env python3
"""PRE713: bounded source alias, predicate and push_back audit in private Kaggle.
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

KERNEL="juniklx/nfsmw-pre713-v51-find-sentinels-readonly"
TITLE="NFSMW PRE713 V51 Find Sentinels Readonly"
MARKER="NFSMW_PRE713_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE712_ALIAS_CONSISTENCY')"
EXTRA=r"""
 # PRE713 — bounded lexical classification only; no AST/CFG, raw source or runtime.
 def h713(t):return hashlib.sha256(t.encode('utf-8')).hexdigest()
 def has713(t,name):return bool(re.search(r'\b'+re.escape(name)+r'\b',t)) if name else False
 def find713(lines,loop,first,alias,var):
  frag=mask_cpp('\n'.join(lines[loop-1:first-1]))
  m=re.search(r'\b'+re.escape(alias)+r'\s*=(?!=)',frag)
  if not m:return {'found':False,'category':'ASSIGNMENT_UNRESOLVED'}
  rest=frag[m.end():].split(';',1)[0]
  hit=re.search(r'\b([A-Za-z_]\w*)\s*(\.|->)\s*find\s*\(',rest)
  if not hit:return {'found':False,'category':'MEMBER_FIND_UNRESOLVED'}
  who,op=hit.group(1),hit.group(2)
  args=rest[hit.end():]
  return {'found':True,'category':'BOUNDED_MEMBER_FIND',
   'receiver_is_requested_extensions':who=='requested_extensions',
   'receiver_is_enabled_extensions':who=='enabled_extensions',
   'receiver_sha256':h713(who),
   'find_arg_mentions_loopvar':has713(args,var),
   'find_arg_mentions_extensionName':has713(args,'extensionName'),
   'find_arg_uses_pointer':'->' in args,
   'find_arg_uses_member':'.' in args,
   'initializer_sha256':h713(rest.strip()),
   'argument_runtime_value':'NOT_VERIFIED'}
 def end713(rhs):
  s=mask_cpp(rhs).strip()
  m=re.search(r'\b([A-Za-z_]\w*)\s*(?:\.|->)\s*(end|cend|rend|crend|size|empty)\s*\(',s)
  return {'rhs_sha256':h713(rhs),
   'member_method':m.group(2) if m else None,
   'method_receiver_is_requested':m.group(1)=='requested_extensions' if m else 'NOT_VERIFIED',
   'rhs_mentions_requested_extensions':has713(s,'requested_extensions'),
   'has_std_end':bool(re.search(r'\bstd\s*::\s*(?:ranges\s*::\s*)?end\s*\(',s)),
   'has_cend_token':has713(s,'cend'),
   'has_end_token':has713(s,'end'),
   'has_comparison_or_template_angle':'<' in s or '>' in s,
   'cpp_sentinel_semantics':'NOT_VERIFIED'}
 def neg713(condition,alias):
  s=mask_cpp(condition).strip()
  rest=s[1:].lstrip() if s.startswith('!') else s
  cat=('NEGATED_PAREN' if rest.startswith('(')
       else 'NEGATED_MEMBER_OR_FIELD' if re.match(r'[A-Za-z_]\w*\s*(?:\.|->)',rest)
       else 'NEGATED_SCOPED_OR_FREE_CALL' if re.match(r'(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*\s*(?:<[^>]{0,100}>)?\s*\(',rest)
       else 'NEGATED_SIMPLE_IDENTIFIER' if re.fullmatch(r'[A-Za-z_]\w*',rest)
       else 'NEGATED_COMPLEX_OR_UNKNOWN')
  free=list(re.finditer(r'((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)\s*\(',rest))
  return {'category':cat,'starts_negation':s.startswith('!'),
   'first_callee_sha256':h713(free[0].group(1)) if free else None,
   'free_call_count':len(free),
   'mentions_alias':has713(rest,alias),'has_arrow':'->' in rest,
   'has_member_dot':'.' in rest,'has_scoped_name':'::' in rest,
   'has_template_or_comparison_angle':'<' in rest or '>' in rest,
   'expression_sha256':h713(s),'cpp_predicate_meaning':'NOT_VERIFIED'}
 def push713(lines,line,receiver_sha):
  s=mask_cpp('\n'.join(lines[:line]))
  hits=[m for m in re.finditer(r'\b([A-Za-z_]\w*)\s*(?:\.|->)\s*push_back\s*\(',s)
        if h713(m.group(1))==receiver_sha]
  if not hits:return {'matched_calls':0,'declaration':'NOT_VERIFIED'}
  name=hits[-1].group(1)
  before=s[:hits[-1].start()]
  occurrences=[]
  for i,ln in enumerate(before.splitlines(),1):
   if not has713(ln,name):continue
   typ=[]
   if re.search(r'\bstd::\s*(?:vector|deque|list|set|unordered_set)\s*<',ln):
    typ.append('STD_CONTAINER_TYPE_TOKEN')
   if re.search(r'\bauto\s*[&*]?\s*'+re.escape(name)+r'\b',ln):
    typ.append('AUTO_DECLARATION_TOKEN')
   if re.search(r'\b'+re.escape(name)+r'\s*(?:=|\{)',ln):
    typ.append('ASSIGNMENT_OR_INITIALIZER_TOKEN')
   if not typ:typ=['OTHER_MENTION']
   occurrences.append({'line':i,'tags':typ})
  return {'matched_calls':len(hits),'receiver_sha256':receiver_sha,
   'earlier_mentions':len(occurrences),'earlier_mentions_recent':occurrences[-10:],
   'cpp_container_type':'NOT_VERIFIED','source_text_exported':False}
 targets={'device':(device_lines,283,286,290,291),
          'instance':(instance_lines,445,448,454,455)}
 selected={}
 for label,(lines,loop,first,second,insert) in targets.items():
  old=report['pre712_alias_guard_audit']['files'][label]
  aa=parse_bounded_parentheses(lines,first,'if')
  bb=parse_bounded_parentheses(lines,second,'if')
  cc=parse_bounded_parentheses(lines,insert,'emplace_back')
  if not all(x['extracted'] for x in (aa,bb,cc)):raise ValueError('PRE713_SOURCE_EXTRACTION_DRIFT')
  alias,rhs=pre712_equality(aa['text'])
  receiver=pre712_receiver(cc['text'])
  _,var=range711(lines[loop-1])
  if alias!=receiver[0] or h713(alias)!=old['alias_text_hash']:
   raise ValueError('PRE713_ALIAS_BINDING_DRIFT')
  if h713(rhs)!=old['comparison_rhs']['rhs_sha256']:
   raise ValueError('PRE713_COMPARISON_RHS_DRIFT')
  finder=find713(lines,loop,first,alias,var)
  sentinel=end713(rhs)
  negated=neg713(bb['text'],alias)
  prior_push=old['second_guard_body_push_back']
  push=(push713(lines,insert+5,prior_push['calls'][0]['receiver_hash'])
        if prior_push['call_count']==1 else {'matched_calls':0})
  selected[label]={'find':finder,'rhs_sentinel':sentinel,
    'negated_guard':negated,'pushback_receiver_prior_mentions':push,
    'runtime_extension_names':'NOT_VERIFIED'}
 comparison={
  'equal_find_initializer_sha':selected['device']['find'].get('initializer_sha256')==selected['instance']['find'].get('initializer_sha256'),
  'equal_rhs_sha':selected['device']['rhs_sentinel']['rhs_sha256']==selected['instance']['rhs_sentinel']['rhs_sha256'],
  'equal_negation_sha':selected['device']['negated_guard']['expression_sha256']==selected['instance']['negated_guard']['expression_sha256'],
  'push_back_instance_only':report['pre712_alias_guard_audit']['pair_consistency']['extra_push_only_instance']}
 report['pre713_find_sentinel_audit']={
   'stage':'PRE713_V51_BOUNDED_FIND_SENTINEL_NEGATION_PUSHBACK',
   'source_hashes_authenticated':True,'files':selected,'pair_consistency':comparison,
   'cpp_ast_and_cfg_proven':False,'raw_source_exported':False,
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'source_to_signed_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'apk_built':False,'apk_modified':False,'secret_accessed':False,
   'fps_gain_proven':False}
 report['analysis_type']='PRE713_BOUNDED_FIND_SENTINEL_NEGATION_PUSHBACK_ONLY'
 report['status']=('PASS_PRE713_AUTHENTICATED_V51_LEXICAL_FIND_SENTINEL'
  if all(comparison.values()) and all(
   x['find']['found'] and x['rhs_sentinel']['rhs_mentions_requested_extensions']
    and x['negated_guard']['starts_negation'] for x in selected.values())
  else 'BLOCK_PRE713_FIND_OR_SENTINEL_STRUCTURE')
"""
def code(manifest,archive,run,attempt):
    src=pre712.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE713_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE712_KAGGLE_REMOTE.json',MARKER),
        ('PRE712_V51_KAGGLE_ALIAS_GUARDS_READONLY',
         'PRE713_V51_KAGGLE_FIND_SENTINELS_READONLY'),
        ("print('PRE712_KAGGLE_GATE=","print('PRE713_KAGGLE_GATE="),
        ("print('PRE712_REPORT=","print('PRE713_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE713_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE713 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre713.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre713-purpose','metadata':{},
                  'source':['Authenticated V51 bounded C++ alias, condition callee and push_back lexical dataflow; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre713-readonly','metadata':{},
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
        assert MARKER in src and 'PRE713_BOUNDED_FIND_SENTINEL_NEGATION_PUSHBACK_ONLY' in src
        assert 'PASS_PRE713_AUTHENTICATED_V51_LEXICAL_FIND_SENTINEL' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE713_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE713_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE713_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE713_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre713.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE713_PRIVATE_KERNEL='+KERNEL)
    print('PRE713_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
