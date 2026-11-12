#!/usr/bin/env python3
"""PRE719: authenticated V51 Vulkan pointer/count mutation lexical audit only."""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre718_generate_private_v51_kernel as pre718

KERNEL="juniklx/nfsmw-pre719-v51-pointer-count-readonly"
TITLE="NFSMW PRE719 V51 Pointer Count Readonly"
MARKER="NFSMW_PRE719_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE718_POINTER_REBUILD_ANCHOR_INCOMPLETE')"
EXTRA=r"""
 # PRE719: bounded V51 source-only audit of the second Vulkan instance attempt.
 # Do not conclude pointer invalidation, actual extension use, or runtime success.
 def h719(x): return hashlib.sha256(x.encode('utf-8')).hexdigest()
 def s719(n): return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def report_line719(n):
  s=s719(n)
  calls=[{'op':m.group(2),'receiver_sha256':h719(m.group(1))}
         for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\.\s*(data|size|push_back|emplace_back|erase|clear|resize|reserve|assign|insert|swap|pop_back)\s*\(',s)]
  indices=[{'receiver_sha256':h719(m.group(1)),'assignment':True}
         for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\[[^]\n]*\]\s*(?<![=!])=(?!=)',s)]
  deref=bool(re.search(r'(?<![/*])\*\s*[A-Za-z_]\w*\s*=(?!=)',s))
  return {'line':n,'sha256':h719(instance_lines[n-1]),
    'methods':calls,'indexed_assignment_receivers':indices,
    'direct_pointer_assignment_shape':deref,
    'count_field_mentioned':bool(re.search(r'\benabledExtensionCount\b',s)),
    'names_pointer_mentioned':bool(re.search(r'\bppEnabledExtensionNames\b',s)),
    'increment_operator_present':bool(re.search(r'\+\+|--|\+=|-=|(?<!\*)\*=',s)),
    'brace_delta_lexical':s.count('{')-s.count('}'),
    'has_break':bool(re.search(r'\bbreak\b',s)),
    'has_continue':bool(re.search(r'\bcontinue\b',s)),
    'has_return':bool(re.search(r'\breturn\b',s)),
    'possible_function_call_names_exported':False}
 def loop_header719(n,vector_hash):
  p=parse_bounded_parentheses(instance_lines,n,'for')
  if not p.get('extracted'):return {'line':n,'header_extracted':False}
  header=mask_cpp(p['text'])
  hascolon=':' in header and ';' not in header
  left,right=header.split(':',1) if hascolon else (header,'')
  names=re.findall(r'\b[A-Za-z_]\w*\b',left)
  loopvar=names[-1] if names else None
  receiver=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*',right)
  return {'line':n,'header_extracted':True,'range_for_shape':hascolon,
    'header_sha256':h719(header),
    'loop_variable_hash':h719(loopvar) if loopvar else None,
    'range_receiver_hash':h719(receiver.group(1)) if receiver else None,
    'range_receiver_matches_initial_pointer_source':bool(receiver and vector_hash and h719(receiver.group(1))==vector_hash),
    'no_ast_or_cfg':True}
 def count_provenance719():
  s=s719(535)
  match=re.search(r'\benabledExtensionCount\b\s*=\s*([^;]+)',s)
  if not match:return {'assignment_found':False}
  rhs=match.group(1).strip()
  single=re.fullmatch(r'[A-Za-z_]\w*',rhs)
  symbol=single.group(0) if single else None
  references=[]
  if symbol:
   pattern=re.compile(r'\b'+re.escape(symbol)+r'\b')
   for n in range(487,536):
    row=s719(n)
    if not pattern.search(row):continue
    matchwrite=bool(re.search(r'\b'+re.escape(symbol)+r'\b\s*(?:=|\+=|-=|\+\+|--)',row)
                  or re.search(r'(?:\+\+|--)\s*'+re.escape(symbol)+r'\b',row))
    refs=bool(re.search(r'\b'+re.escape(symbol)+r'\b\s*\(',row))
    references.append({'line':n,'sha256':h719(instance_lines[n-1]),
      'has_syntactic_assignment_or_increment':matchwrite,
      'has_function_call_shape':refs})
  return {'assignment_found':True,'rhs_sha256':h719(rhs),
    'rhs_single_identifier':bool(symbol),
    'rhs_single_identifier_sha256':h719(symbol) if symbol else None,
    'rhs_has_size_call':bool(re.search(r'\.\s*size\s*\(',rhs)),
    'rhs_has_subtraction':bool(re.search(r'(?<!-)-(?![->])',rhs)),
    'rhs_has_cast':bool(re.search(r'\b(?:static_cast|reinterpret_cast)\s*<',rhs)),
    'references_to_rhs_single_identifier_487_535':references[:50],
    'reference_total':len(references),
    'actual_binding_or_value':'NOT_VERIFIED',
    'actual_cpp_type':'NOT_VERIFIED'}
 previous=report['pre718_instance_retry_dataflow_audit']
 gate=previous['source_findings']
 if previous['stage']!='PRE718_AUTHENTICATED_V51_INSTANCE_RETRY_VECTOR_POINTER_DATAFLOW':
  raise ValueError('PRE719_PARENT_STAGE_DRIFT')
 if [x['line'] for x in report['pre717_instance_retry_audit']['source_findings']['create_calls']]!=[523,537]:
  raise ValueError('PRE719_CREATE_CALL_ANCHOR_DRIFT')
 if not (gate['line_500_extension_count_setup']['assignment_detected'] and gate['line_501_pointer_setup']['assignment_detected']
    and gate['line_535_extension_count_reset']['assignment_detected']):
  raise ValueError('PRE719_FIELD_ANCHOR_DRIFT')
 initial_vector_hash=gate['line_501_pointer_setup'].get('rhs_receiver_hash')
 rows=[report_line719(n) for n in range(523,541)]
 arrays=[{'line':row['line'],'receiver_sha256':a['receiver_sha256']}
   for row in rows for a in row['indexed_assignment_receivers']]
 mutations=[{'line':row['line'],'method':m['op'],'receiver_sha256':m['receiver_sha256']}
   for row in rows for m in row['methods']
   if m['op'] in ('push_back','emplace_back','erase','clear','resize','reserve','assign','insert','swap','pop_back')]
 ptr_update_lines=[n for n in range(523,538)
   if re.search(r'\bppEnabledExtensionNames\b\s*=',s719(n))]
 count_update_lines=[n for n in range(523,538)
   if re.search(r'\benabledExtensionCount\b\s*=',s719(n))]
 cnt=count_provenance719()
 loop528=loop_header719(528,initial_vector_hash)
 loop531=loop_header719(531,initial_vector_hash)
 report['pre719_pointer_count_mutation_audit']={
  'stage':'PRE719_AUTHENTICATED_V51_INSTANCE_POINTER_COUNT_MUTATION_READONLY',
  'source_sha_checks_inherited':True,
  'analysis_type':'BOUNDED_CPP_LEXICAL_523_540_NO_AST_CFG_OR_POINTER_LIFETIME',
  'source_findings':{
   'line_535_count_rhs':cnt,
   'loop_528_shape':loop528,'loop_531_shape':loop531,
   'line_classifications_523_540':rows,
   'explicit_mutating_vector_method_candidates':mutations,
   'indexed_assignment_candidates':arrays,
   'indexed_assignment_to_initial_vector_count':sum(1 for a in arrays if a['receiver_sha256']==initial_vector_hash),
   'mutating_method_on_initial_vector_count':sum(1 for a in mutations if a['receiver_sha256']==initial_vector_hash),
   'initial_pointer_source_sha256':initial_vector_hash,
   'pointer_field_assignment_lines_523_537':ptr_update_lines,
   'count_field_assignment_lines_523_537':count_update_lines,
   'possible_aliases_or_indirect_mutations':'NOT_VERIFIED',
   'effective_extension_count_at_second_call':'NOT_VERIFIED',
   'pointer_validity_at_second_call':'NOT_VERIFIED',
   'real_reallocation':'NOT_VERIFIED',
   'actual_cpp_ast_cfg_or_type_analysis':False,
   'runtime_vk_instance_create_result':'NOT_VERIFIED',
   'runtime_enabled_extensions':'NOT_VERIFIED',
   'source_to_signed_apk_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'source_text_exported':False,'identifier_spelling_exported':False,
   'apk_built':False,'apk_modified':False,'signing_material_accessed':False,
   'fps_gain_proven':False},
  'stale_pointer_or_count_mismatch_proven':False,
  'source_or_apk_modified':False,
  'runtime_behavior_proven':False}
 report['analysis_type']='PRE719_AUTHENTICATED_V51_INSTANCE_POINTER_COUNT_MUTATION_LEXICAL_ONLY'
 report['status']=('PASS_PRE719_V51_BOUNDED_POINTER_COUNT_MUTATION_AUDIT'
   if cnt['assignment_found'] and loop528['header_extracted']
      and loop531['header_extracted'] and len(rows)==18 and 535 in count_update_lines
   else 'BLOCK_PRE719_SOURCE_MUTATION_GATES_INCOMPLETE')
"""

def code(manifest,archive,run,attempt):
    src=pre718.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1: raise ValueError('PRE719_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
       ('NFSMW_PRE718_KAGGLE_REMOTE.json',MARKER),
       ('PRE718_V51_KAGGLE_INSTANCE_POINTER_FALLBACK_READONLY',
        'PRE719_V51_KAGGLE_POINTER_COUNT_MUTATION_READONLY'),
       ("print('PRE718_KAGGLE_GATE=","print('PRE719_KAGGLE_GATE="),
       ("print('PRE718_REPORT=","print('PRE719_REPORT=")
    ):
        if old not in src: raise ValueError('PRE719_PARENT_MISSING_TOKEN '+old)
        src=src.replace(old,new)
    compile(src,'<PRE719 isolated Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre719.ipynb',
          'language':'python','kernel_type':'notebook','is_private':True,
          'enable_gpu':False,'enable_internet':False,'dataset_sources':[],
          'competition_sources':[],'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
     'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
     'cells':[{'cell_type':'markdown','id':'pre719-purpose','metadata':{},
      'source':['Read-only V51 C++ lexical pointer/count candidate audit; no runtime or APK mutation.']},
     {'cell_type':'code','id':'pre719-readonly','metadata':{},
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
        src=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'f','123','1')
        assert MARKER in src and "'stale_pointer_or_count_mismatch_proven':False" in src
        assert "'source_text_exported':False" in src
        assert 'PASS_PRE719_V51_BOUNDED_POINTER_COUNT_MUTATION_AUDIT' in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,notebook=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(notebook['cells'])==2
        print('PRE719_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing inputs')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('invalid run ids')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
      manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE719_BAD_V51_SOURCE_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE719_SOURCE_SHA_MISMATCH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE719_ARCHIVE_CORRUPT')
    meta,notebook=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre719.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE719_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__': main()
