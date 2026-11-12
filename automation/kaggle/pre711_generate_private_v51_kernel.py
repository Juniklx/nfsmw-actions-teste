#!/usr/bin/env python3
"""PRE711: narrow V51 Vulkan source guard/lookup syntax audit in isolated private Kaggle.
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

KERNEL="juniklx/nfsmw-pre711-v51-operand-links-readonly"
TITLE="NFSMW PRE711 V51 Operand Links Readonly"
MARKER="NFSMW_PRE711_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE710_GUARD_BODY_UNRESOLVED')"
EXTRA=r"""
 # PRE711: bounded syntactic links; no AST, source export or runtime claims.
 def h711(v):return hashlib.sha256(v.encode('utf-8')).hexdigest()
 def range711(line):
  m=re.search(r'\bfor\s*\(([^)\n]*)\)',mask_cpp(line))
  if not m:return {'status':'NOT_VERIFIED','range_for':False},None
  chunks=re.split(r'(?<!:):(?!:)',m.group(1),maxsplit=1)
  if len(chunks)!=2:return {'status':'NOT_VERIFIED','range_for':False},None
  decl,rng=[x.strip() for x in chunks]
  vm=re.search(r'([A-Za-z_]\w*)\s*$',decl)
  var=vm.group(1) if vm else None
  if var in ('const','auto','volatile'):var=None
  return {'status':'RANGE_FOR_LEXICAL' if var else 'VARIABLE_NOT_RESOLVED',
          'range_for':True,'contains_const':bool(re.search(r'\bconst\b',decl)),
          'iterator_id_sha256':h711(var) if var else None,
          'container_expr_sha256':h711(rng),
          'container_expr_mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',rng)),
          'source_not_exported':True,'cpp_type':'NOT_VERIFIED'},var
 def receiver711(expr,var):
  e=mask_cpp(expr)
  m=re.search(r'(?<!\w)([A-Za-z_]\w*)\s*(\.|->)\s*([A-Za-z_]\w*)\s*(?:\.|->)\s*c_str\s*\(',e)
  if not m:return {'status':'NOT_VERIFIED','linked_to_for_variable':'NOT_VERIFIED'}
  first,op,second=m.groups()
  return {'status':'TWO_IDENTIFIER_MEMBER_CSTR',
    'receiver_object_sha256':h711(first),'member_name_sha256':h711(second),
    'linked_to_for_variable':first==var if var else 'NOT_VERIFIED',
    'member_name_allowlisted':second if second in ('extensionName','name','extension_name') else 'REDACTED',
    'access':('arrow' if op=='->' else 'dot'),'cpp_member_type':'NOT_VERIFIED',
    'runtime_name':'NOT_VERIFIED'}
 def equality711(expr,var):
  e=mask_cpp(expr)
  matches=list(re.finditer(r'(?<![!<>=])==(?!=)',e))
  if len(matches)!=1:return {'status':'NOT_VERIFIED','op_count':len(matches)}
  n=matches[0].start();l=e[:n].strip();r=e[n+2:].strip()
  def has(s,t):return bool(re.search(r'\b'+re.escape(t)+r'\b',s))
  return {'status':'ONE_LEXICAL_EQUALITY','op_count':1,
    'left_requested_extensions':has(l,'requested_extensions'),
    'right_requested_extensions':has(r,'requested_extensions'),
    'left_for_iterator':has(l,var) if var else 'NOT_VERIFIED',
    'right_for_iterator':has(r,var) if var else 'NOT_VERIFIED',
    'left_nullptr':l.strip(' ()')=='nullptr',
    'right_nullptr':r.strip(' ()')=='nullptr',
    'left_hash':h711(l),'right_hash':h711(r),
    'operand_text_exported':False,'cpp_semantics':'NOT_VERIFIED'}
 def negation711(expr,var):
  e=mask_cpp(expr).strip()
  return {'status':'NEGATION_LEXICAL',
    'starts_bang':e.startswith('!'),'bang_followed_by_open_paren':bool(re.match(r'!\s*\(',e)),
    'mentions_for_iterator':bool(re.search(r'\b'+re.escape(var)+r'\b',e)) if var else 'NOT_VERIFIED',
    'mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',e)),
    'has_template_or_relational_angle':('<' in e or '>' in e),
    'has_scoped_symbol':'::' in e,'has_member_access':('.' in e or '->' in e),
    'predicate_values':'NOT_VERIFIED'}
 def push711(lines,start,end,var):
  src=mask_cpp('\n'.join(lines[start-1:end]))
  m=list(re.finditer(r'([A-Za-z_]\w*)\s*(?:\.|->)\s*push_back\s*\(',src))
  return {'call_count':len(m),
    'receiver_ids_sha256':[h711(x.group(1)) for x in m],
    'receiver_is_enabled_extensions':[x.group(1)=='enabled_extensions' for x in m],
    'receiver_is_requested_extensions':[x.group(1)=='requested_extensions' for x in m],
    'receiver_is_for_iterator':[(x.group(1)==var if var else 'NOT_VERIFIED') for x in m],
    'pushback_argument_values':'NOT_VERIFIED','source_not_exported':True}
 targets={'device':(device_lines,283,286,290,291,(291,293)),
          'instance':(instance_lines,445,448,454,455,(455,458))}
 pairs={}
 for label,(lines,loop,first,second,insert,body) in targets.items():
  prior=report['pre710_statement_receiver_audit']['files'][label]
  aa=parse_bounded_parentheses(lines,first,'if')
  bb=parse_bounded_parentheses(lines,second,'if')
  cc=parse_bounded_parentheses(lines,insert,'emplace_back')
  if not all(x['extracted'] for x in (aa,bb,cc)):raise ValueError('PRE711_PARSE_MISMATCH')
  if (h711(aa['text'].strip())!=prior['first_if']['conditions']['expression_sha256']
   or h711(bb['text'].strip())!=prior['second_if']['conditions']['expression_sha256']
   or h711(cc['text'].strip())!=prior['insertion']['argument']['argument_expr_sha256']):
   raise ValueError('PRE711_PRE710_EXPRESSION_SHA_DRIFT')
  for_info,var=range711(lines[loop-1])
  pairs[label]={'for_binding':for_info,
    'first_guard_equality':equality711(aa['text'],var),
    'first_guard_continue':prior['first_if']['body']['statement_flags']['contains_continue'],
    'second_guard':negation711(bb['text'],var),
    'cstr_receiver':receiver711(cc['text'],var),
    'push_back':push711(lines,*body,var),
    'runtime_branch_values':'NOT_VERIFIED'}
 comparison={
   'same_first_equality_hashes':
     pairs['device']['first_guard_equality'].get('left_hash')==pairs['instance']['first_guard_equality'].get('left_hash')
     and pairs['device']['first_guard_equality'].get('right_hash')==pairs['instance']['first_guard_equality'].get('right_hash'),
   'same_negation_structure':pairs['device']['second_guard']==pairs['instance']['second_guard'],
   'same_cstr_receiver':pairs['device']['cstr_receiver']==pairs['instance']['cstr_receiver']
 }
 report['pre711_operand_links']={'stage':'PRE711_V51_BOUNDED_OPERAND_LINKS',
  'authenticated_source_sha_checks':True,'files':pairs,'comparisons':comparison,
  'source_exported':False,'cpp_ast_or_cfg_proven':False,
  'runtime_enabled_extensions':'NOT_VERIFIED','installed_apk_binary_identity':'UNVERIFIED',
  'vk_google_display_timing_enabled':'NOT_VERIFIED','apk_built':False,'apk_modified':False,
  'signing_material_accessed':False,'fps_gain_proven':False}
 report['analysis_type']='PRE711_BOUNDED_SOURCE_OPERAND_LINKS_ONLY'
 report['status']=('PASS_PRE711_AUTHENTICATED_BOUNDED_RELATIONSHIPS_READONLY'
  if all(comparison.values()) and all(x['first_guard_continue'] for x in pairs.values())
  and pairs['device']['push_back']['call_count']==0
  and pairs['instance']['push_back']['call_count']>0
  else 'BLOCK_PRE711_SOURCE_RELATIONSHIP_CHECKS')
"""def code(manifest,archive,run,attempt):
    src=pre710.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE711_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE710_KAGGLE_REMOTE.json',MARKER),
        ('PRE710_V51_KAGGLE_EXTENSION_LOOKUP_GUARDS_READONLY',
         'PRE711_V51_KAGGLE_OPERAND_LINKS_READONLY'),
        ("print('PRE710_KAGGLE_GATE=","print('PRE711_KAGGLE_GATE="),
        ("print('PRE710_REPORT=","print('PRE711_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE711_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE711 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre711.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre711-purpose','metadata':{},
                  'source':['Authenticated V51 Vulkan operand and loop binding structural links; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre711-readonly','metadata':{},
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
        assert MARKER in src and 'PRE711_BOUNDED_SOURCE_OPERAND_LINKS_ONLY' in src
        assert 'PASS_PRE711_AUTHENTICATED_BOUNDED_RELATIONSHIPS_READONLY' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE711_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE711_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE711_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE711_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre711.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE711_PRIVATE_KERNEL='+KERNEL)
    print('PRE711_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
