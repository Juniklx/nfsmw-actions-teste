#!/usr/bin/env python3
"""PRE722 V51 private Kaggle authenticated count cast argument origin (read-only)."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre721_generate_private_v51_kernel as pre721

KERNEL="juniklx/nfsmw-pre722-v51-cast-arg-readonly"
TITLE="NFSMW PRE722 V51 Cast Arg Readonly"
MARKER="NFSMW_PRE722_KAGGLE_REMOTE.json"
PARENT_FINAL="    else 'BLOCK_PRE721_LEXICAL_ANCHOR_MISMATCH')"
EXTRA=r"""
 # PRE722: origin of the unique integer cast argument in enabledExtensionCount on line 535.
 # ONLY sanitized hashes / boolean lexical indicators leave the authenticated private Kaggle run.
 def h722(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def l722(n):return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def ident722(s):return bool(re.fullmatch(r'[A-Za-z_]\w*',s.strip()))
 def word722(name,s):return bool(re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',s)) if name else False
 def eq722(s):return bool(re.search(r'(?<![!<>=])=(?!=)',s))
 def classify722():
  findings=report['pre721_call_range_linkage_audit']['source_findings']
  expected_arg_sha=findings['line535_callable_shape']['arguments_sha256']
  if len(expected_arg_sha)!=1: return {'complete':False,'reason':'PRE721_NOT_ONE_ARG'}
  row=l722(535)
  match=re.search(r'\benabledExtensionCount\b\s*=\s*([^;]+)',row)
  if not match:return {'complete':False,'reason':'COUNT535_MISSING'}
  value=match.group(1).strip()
  call=re.fullmatch(r'([A-Za-z_]\w*)\s*\((.*)\)',value)
  if not call:return {'complete':False,'reason':'CAST_CALL_SHAPE_NOT_EXACT'}
  caster,arg=call.groups();arg=arg.strip()
  if h722(arg)!=expected_arg_sha[0]:
   raise ValueError('PRE722_PARENT_ARGUMENT_HASH_DRIFT')
  pre719=report['pre719_pointer_count_mutation_audit']['source_findings']
  srcptr=pre719['initial_pointer_source_sha256']
  simple=ident722(arg)
  operand=arg if simple else None
  preceding=[]
  if operand:
   for i in range(250,535):
    textline=l722(i)
    if word722(operand,textline):
     preceding.append({
       'line':i,'line_sha256':h722(instance_lines[i-1]),
       'contains_assignment_equal':eq722(textline),
       'contains_increment_or_decrement':bool(re.search(r'\+\+|--',textline)),
       'contains_compound_assignment':bool(re.search(r'(?:\+=|-=|\*=|/=|%=)',textline)),
       'contains_auto_or_decltype':bool(re.search(r'\b(?:auto|decltype)\b',textline)),
       'contains_size_method':bool(re.search(r'\.\s*size\s*\(',textline)),
       'contains_clear_erase_or_resize':bool(re.search(r'\.\s*(?:clear|erase|resize)\s*\(',textline)),
       'contains_push_back_or_emplace_back':bool(re.search(r'\.\s*(?:push_back|emplace_back)\s*\(',textline)),
       'contains_std_container_token':bool(re.search(r'\b(?:vector|map|unordered_map|array)\b',textline)),
       'contains_enabledExtensionCount':bool(re.search(r'\benabledExtensionCount\b',textline)),
       'contains_ppEnabledExtensionNames':bool(re.search(r'\bppEnabledExtensionNames\b',textline)),
       'contains_loop531_receiver':False})
  ptrline=l722(501)
  ptrmatch=re.search(r'\bppEnabledExtensionNames\b\s*=\s*([^;]+)',ptrline)
  ptrrhs=ptrmatch.group(1).strip() if ptrmatch else ''
  pointer_owner_match=re.fullmatch(r'([A-Za-z_]\w*)\s*\.\s*data\s*\(\s*\)',ptrrhs)
  owner=pointer_owner_match.group(1) if pointer_owner_match else None
  other=[
   {'line':i,'count_assignment':bool(re.search(r'\benabledExtensionCount\b\s*=',l722(i))),
    'pointer_assignment':bool(re.search(r'\bppEnabledExtensionNames\b\s*=',l722(i)))}
   for i in range(499,538)
  ]
  size_matches=[]
  if operand:
   for i in range(485,538):
    t=l722(i)
    if re.search(r'\b'+re.escape(operand)+r'\b\s*=',t) or re.search(r'\b'+re.escape(operand)+r'\b\s*(?:\+\+|--)',t):
     size_matches.append({'line':i,'has_size_call':bool(re.search(r'\.\s*size\s*\(',t)),
                          'has_minus_one':bool(re.search(r'-\s*1\b',t)),
                          'has_boolean_comparison':bool(re.search(r'\b(?:true|false)\b',t)),
                          'has_conditional_operator':'?' in t})
  return {
   'complete':True,
   'integer_type_cast_spelling_in_parent':findings['line535_callable_shape']['callee_is_integer_type_spelling'],
   'single_argument_sha256':h722(arg),
   'argument_is_simple_identifier':simple,
   'argument_identifier_sha256':h722(operand) if operand else None,
   'argument_matches_initial_names_vector':bool(operand and h722(operand)==srcptr),
   'argument_matches_loop531_receiver':bool(operand and h722(operand)==findings['loop531_receiver_sha256']),
   'argument_matches_loop531_variable':bool(operand and h722(operand)==findings['loop531_variable_sha256']),
   'argument_mentions_enabled_extensions':bool(re.search(r'\benabled_extensions\b',arg)),
   'argument_mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',arg)),
   'argument_mentions_size_method':bool(re.search(r'\.\s*size\s*\(',arg)),
   'argument_has_addition_or_subtraction':bool(re.search(r'(?<![+])\+(?![+])|(?<![-])-([^-]|$)',arg)),
   'argument_has_comparison':bool(re.search(r'(?:==|!=|<=|>=|(?<![<])<(?![<=])|(?<![>-])>(?![=>]))',arg)),
   'argument_has_ternary':'?' in arg,
   'argument_preceding_occurrences_total':len(preceding),
   'argument_preceding_occurrences_tail':preceding[-20:],
   'argument_assignments_near_retry':size_matches[-16:],
   'line501_pointer_source_found':bool(owner),
   'line501_pointer_source_sha256':h722(owner) if owner else None,
   'line501_pointer_source_matches_pre719':bool(owner and h722(owner)==srcptr),
   'cast_argument_matches_line501_pointer_source':bool(owner and operand and owner==operand),
   'count_reassignments_499_537':[x['line'] for x in other if x['count_assignment']],
   'pointer_reassignments_499_537':[x['line'] for x in other if x['pointer_assignment']],
   'actual_collection_size_or_runtime_value':'NOT_VERIFIED',
   'cpp_ast_semantics':'NOT_VERIFIED',
   'source_signed_elf_equivalence':'UNVERIFIED',
   'stale_pointer_bug_proven':False,
   'count_mismatch_proven':False,
   'source_text_exported':False,
   'private_identifiers_exported':False}
 f722=classify722()
 report['pre722_count_argument_origin_audit']={
  'stage':'PRE722_V51_COUNT535_CAST_ARGUMENT_ORIGIN_READONLY',
  'analysis_type':'HASHED_BOUNDED_CPP_CAST_ARGUMENT_DATA_ORIGIN_LEXICAL',
  'source_findings':f722,
  'source_sha_checks_inherited':True,
  'source_text_exported':False,
  'signed_binary_proven_equal':False,
  'runtime_vulkan_extension_count':'NOT_VERIFIED',
  'stale_pointer_bug_proven':False,
  'extension_count_mismatch_proven':False,
  'apk_modified':False,'apk_built':False,'signing_material_accessed':False,
  'fps_gain_proven':False}
 report['analysis_type']='PRE722_AUTHENTICATED_V51_CAST_ARGUMENT_ORIGIN_LEXICAL'
 report['status']=('PASS_PRE722_V51_CAST_ARGUMENT_ORIGIN_CLASSIFIED'
   if f722['complete'] and f722['single_argument_sha256']==
       report['pre721_call_range_linkage_audit']['source_findings']['line535_callable_shape']['arguments_sha256'][0]
      and f722['line501_pointer_source_matches_pre719']
   else 'BLOCK_PRE722_CAST_OR_POINTER_ANCHORS_UNRESOLVED')
"""

def code(manifest,archive,run,attempt):
    src=pre721.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE722_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE721_KAGGLE_REMOTE.json',MARKER),
      ('PRE721_V51_KAGGLE_CALL_RANGE_LINKAGE_READONLY',
       'PRE722_V51_KAGGLE_CAST_ARGUMENT_ORIGIN_READONLY'),
      ("print('PRE721_KAGGLE_GATE=","print('PRE722_KAGGLE_GATE="),
      ("print('PRE721_REPORT=","print('PRE722_REPORT=")
    ):
       if old not in src:raise ValueError('PRE722_PARENT_TOKEN_DRIFT '+old)
       src=src.replace(old,new)
    compile(src,'<PRE722 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre722.ipynb',
         'language':'python','kernel_type':'notebook','is_private':True,
         'enable_gpu':False,'enable_internet':False,
         'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,'metadata':{
        'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
        'cells':[{'cell_type':'markdown','id':'pre722-purpose','metadata':{},
          'source':['PRE722 read-only hashed C++ lexical count cast argument origin audit.']},
         {'cell_type':'code','id':'pre722-readonly','metadata':{},
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
        assert MARKER in src and 'PASS_PRE722_V51_CAST_ARGUMENT_ORIGIN_CLASSIFIED' in src
        assert "'private_identifiers_exported':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET',
                          'KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE722_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE722_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE722_BAD_V51_DEVICE_INSTANCE_HASH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE722_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre722.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE722_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
