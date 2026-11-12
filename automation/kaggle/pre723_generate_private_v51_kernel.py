#!/usr/bin/env python3
"""PRE723 V51 authenticated read-only .size() receiver versus .data() source."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre722_generate_private_v51_kernel as pre722

KERNEL="juniklx/nfsmw-pre723-v51-size-receiver"
TITLE="NFSMW PRE723 V51 Size Receiver"
MARKER="NFSMW_PRE723_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE722_CAST_OR_POINTER_ANCHORS_UNRESOLVED')"
EXTRA=r"""
 # PRE723: lexical origin of .size() at line 355, and comparison with vector .data() at 501.
 # Audited source remains private; only hashes, shape booleans and line numbers are exported.
 def h723(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def l723(n):return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def refs723(idt,txt):return bool(re.search(r'(?<!\w)'+re.escape(idt)+r'(?!\w)',txt)) if idt else False
 def probe723():
  previous=report['pre722_count_argument_origin_audit']['source_findings']
  row535=l723(535)
  mt=re.search(r'\benabledExtensionCount\b\s*=\s*([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)',row535)
  if not mt:return {'complete':False,'reason':'CAST535_PATTERN_DRIFT'}
  _,count_arg=mt.groups()
  if h723(count_arg)!=previous['single_argument_sha256']:
   raise ValueError('PRE723_COUNT_ARG_SHA_DRIFT')
  row355=l723(355)
  assignments=re.findall(r'(?<!\w)'+re.escape(count_arg)+r'\s*=\s*([^;]+)',row355)
  sizes=re.findall(r'([A-Za-z_]\w*)\s*(\.|->)\s*size\s*\(\s*\)',row355)
  owners=[n for n,op in sizes]
  if len(assignments)!=1 or len(owners)!=1:
   return {'complete':False,'reason':'LINE355_SOURCE_SHAPE_UNRESOLVED',
    'assignment_candidates_count':len(assignments),'size_receivers_count':len(owners)}
  lhs_rhs=assignments[0].strip()
  owner=owners[0]
  line355_size_is_assignment_rhs=bool(re.fullmatch(
   re.escape(owner)+r'\s*(?:\.|->)\s*size\s*\(\s*\)',lhs_rhs))
  vector501=re.search(r'\bppEnabledExtensionNames\b\s*=\s*([A-Za-z_]\w*)\s*\.\s*data\s*\(\s*\)',l723(501))
  vector500=re.search(r'\benabledExtensionCount\b\s*=\s*(?:[^;]*?)([A-Za-z_]\w*)\s*\.\s*size\s*\(',l723(500))
  if not vector501:return {'complete':False,'reason':'POINTER501_VECTOR_UNRESOLVED'}
  ptr=vector501.group(1)
  prev719=report['pre719_pointer_count_mutation_audit']['source_findings']
  if h723(ptr)!=previous['line501_pointer_source_sha256']:
   raise ValueError('PRE723_POINTER_SOURCE_HASH_DRIFT')
  ref_lines=[]
  mutation_candidates=[]
  for i in range(355,538):
   line=l723(i)
   if not refs723(owner,line):continue
   mutops=re.findall(r'(?<!\w)'+re.escape(owner)+r'\s*(?:\.|->)\s*(push_back|emplace_back|erase|clear|resize|reserve|assign|insert|swap|pop_back)\s*\(',line)
   lhswrites=bool(re.search(r'(?<!\w)'+re.escape(owner)+r'\s*(?:=|\+=|-=|\+\+|--)(?!=)',line))
   subscript=bool(re.search(r'(?<!\w)'+re.escape(owner)+r'\s*\[[^\]]+\]\s*(?:=|\+=|-=)(?!=)',line))
   if i!=355 and (mutops or lhswrites or subscript):
    mutation_candidates.append({'line':i,'mutating_method_lexical':bool(mutops),
      'mutating_method_kinds':sorted(set(mutops)),
      'direct_assignment_or_increment':lhswrites,
      'subscript_assignment':subscript,
      'line_sha256':h723(instance_lines[i-1])})
   ref_lines.append({'line':i,
      'contains_size_call':bool(re.search(r'(?<!\w)'+re.escape(owner)+r'\s*(?:\.|->)\s*size\s*\(',line)),
      'contains_data_call':bool(re.search(r'(?<!\w)'+re.escape(owner)+r'\s*(?:\.|->)\s*data\s*\(',line)),
      'line_sha256':h723(instance_lines[i-1])})
  count_arg_mentions=[]
  for i in range(355,538):
   if refs723(count_arg,l723(i)):
    count_arg_mentions.append(i)
  return {
   'complete':True,'line355_argument_assignment_candidates':len(assignments),
   'line355_size_receiver_candidates':len(owners),
   'line355_size_is_direct_assignment_rhs':line355_size_is_assignment_rhs,
   'line355_size_receiver_sha256':h723(owner),
   'line355_size_receiver_matches_pointer501':owner==ptr,
   'line355_size_receiver_matches_line500_vector':bool(vector500 and owner==vector500.group(1)),
   'line355_size_receiver_matches_count_arg':owner==count_arg,
   'line355_size_access_operator_is_dot':sizes[0][1]=='.',
   'line355_size_access_operator_is_arrow':sizes[0][1]=='->',
   'line355_assignment_rhs_sha256':h723(lhs_rhs),
   'line355_size_receiver_matches_enabled_extensions':owner=='enabled_extensions',
   'line355_size_receiver_matches_requested_extensions':owner=='requested_extensions',
   'line500_size_receiver_extracted':bool(vector500),
   'line500_size_receiver_matches_pointer501':bool(vector500 and vector500.group(1)==ptr),
   'line501_pointer_source_sha256':h723(ptr),
   'line355_537_owner_refs_count':len(ref_lines),
   'line355_537_owner_refs_tail':ref_lines[-25:],
   'line356_537_mutation_candidates':mutation_candidates[:30],
   'line356_537_mutation_candidates_truncated':len(mutation_candidates)>30,
   'line355_537_count_arg_reference_lines':count_arg_mentions[:25],
   'line355_537_count_arg_reference_lines_truncated':len(count_arg_mentions)>25,
   'line535_arg_parent_sha256_matches':True,
   'count355_equals_pointer501_size_runtime':'NOT_VERIFIED',
   'count355_equals_line500_size_runtime':'NOT_VERIFIED',
   'real_vulkan_extension_count_or_pointer_validity':'NOT_VERIFIED',
   'cpp_ast_or_cfg_semantics':'NOT_VERIFIED',
   'source_signed_elf_equivalence':'UNVERIFIED',
   'stale_pointer_bug_proven':False,'extension_count_mismatch_proven':False,
   'source_text_exported':False,'private_identifiers_exported':False}
 f723=probe723()
 report['pre723_size_receiver_identity_audit']={
  'stage':'PRE723_V51_LINE355_SIZE_RECEIVER_VS_POINTER501_READONLY',
  'analysis_type':'AUTHENTICATED_HASHED_BOUNDED_CPP_SIZE_RECEIVER_LEXICAL',
  'source_findings':f723,
  'authenticated_v51_source_inherited':True,
  'real_cpp_ast_used':False,'runtime_vulkan_audited':False,
  'source_signed_elf_equivalence':'UNVERIFIED',
  'stale_pointer_bug_proven':False,'extension_count_mismatch_proven':False,
  'apk_built':False,'apk_modified':False,'signing_material_accessed':False,
  'fps_gain_proven':False,'source_text_exported':False}
 report['analysis_type']='PRE723_AUTHENTICATED_V51_SIZE_RECEIVER_LEXICAL'
 report['status']=('PASS_PRE723_V51_SIZE_RECEIVER_AUDIT'
    if f723['complete'] and f723['line535_arg_parent_sha256_matches']
       and f723['line355_size_is_direct_assignment_rhs']
       and f723['line501_pointer_source_sha256']==
         report['pre722_count_argument_origin_audit']['source_findings']['line501_pointer_source_sha256']
    else 'BLOCK_PRE723_SIZE_RECEIVER_SHAPE_OR_PARENT_DRIFT')
"""

def code(manifest,archive,run,attempt):
    src=pre722.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE723_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE722_KAGGLE_REMOTE.json',MARKER),
      ('PRE722_V51_KAGGLE_CAST_ARGUMENT_ORIGIN_READONLY',
       'PRE723_V51_KAGGLE_SIZE_RECEIVER_READONLY'),
      ("print('PRE722_KAGGLE_GATE=","print('PRE723_KAGGLE_GATE="),
      ("print('PRE722_REPORT=","print('PRE723_REPORT=")
    ):
       if old not in src:raise ValueError('PRE723_PARENT_TOKEN_DRIFT '+old)
       src=src.replace(old,new)
    compile(src,'<PRE723 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre723.ipynb',
         'language':'python','kernel_type':'notebook','is_private':True,
         'enable_gpu':False,'enable_internet':False,
         'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,'metadata':{
      'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre723-purpose','metadata':{},
        'source':['PRE723 authenticated V51 private lexical source; only hashes and metadata leave notebook.']},
       {'cell_type':'code','id':'pre723-readonly','metadata':{},
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
        assert MARKER in src and 'PASS_PRE723_V51_SIZE_RECEIVER_AUDIT' in src
        assert "'private_identifiers_exported':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET',
                          'KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
           assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE723_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
       p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE723_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE723_BAD_V51_DEVICE_INSTANCE_HASH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
       if z.testzip() is not None or set(z.namelist())!=set(hashes):
          raise ValueError('PRE723_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre723.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE723_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
