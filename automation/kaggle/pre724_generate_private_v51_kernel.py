#!/usr/bin/env python3
"""PRE724 V51 authenticated read-only .size() receiver versus .data() source."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre723_generate_private_v51_kernel as pre723

KERNEL="juniklx/nfsmw-pre724-v51-optional-retry"
TITLE="NFSMW PRE724 V51 Optional Retry"
MARKER="NFSMW_PRE724_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE723_SIZE_RECEIVER_SHAPE_OR_PARENT_DRIFT')"
EXTRA=r"""
 # PRE724: conservative link of optional extension insertion and bounded Vulkan retry guard.
 # Never export unmasked source or private identifiers.
 def l724(n):return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def h724(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def scope724(guard_line,target,last):
  # Lexical braces, not a real C++ parser; strings/macros/implicit bodies may mislead.
  op=next((n for n in range(guard_line,min(last+1,guard_line+4)) if '{' in l724(n)),None)
  if op is None:return {'found':False,'target_in_lexical_braces':False,'open_line':None,'close_line':None}
  dep=0;inside=False;end=None
  for n in range(op,last+1):
   txt=l724(n);dep+=txt.count('{')-txt.count('}')
   if n==target:inside=dep>0
   if dep<=0:
    end=n;break
  return {'found':True,'target_in_lexical_braces':inside,'open_line':op,'close_line':end}
 def probe724():
  parent=report['pre724_size_receiver_identity_audit']['source_findings']
  old=report['pre717_instance_retry_audit']['source_findings']
  row454=l724(454);row455=l724(455)
  row523=l724(523);row525=l724(525);row535=l724(535);row537=l724(537)
  first=old['create_calls'][0];second=old['create_calls'][1]
  if not (first['line']==523 and second['line']==537 and
          first['argument_sha256']==second['argument_sha256']):
    return {'complete':False,'reason':'PARENT_VK_CREATE_CALL_SHAPE_DRIFT'}
  if not (parent['line355_size_receiver_matches_pointer501'] and
          parent['line355_size_receiver_matches_line500_vector'] and
          parent['line355_size_is_direct_assignment_rhs']):
    return {'complete':False,'reason':'PARENT_SIZE_POINTER_LINEAGE_DRIFT'}
  optional_guard=re.search(r'\bif\s*\(',row454) is not None
  optional_scope=scope724(454,455,459)
  retry_scope=scope724(525,537,541)
  retry_guard=re.search(r'\bif\s*\(',row525) is not None
  conditional_error_tokens=sorted(set(
    tok for n in range(525,528) for tok in
    re.findall(r'\bVK_ERROR_(?:EXTENSION_NOT_PRESENT|LAYER_NOT_PRESENT)\b',l724(n))))
  vector455=re.search(r'\benabled_extensions\s*\.\s*emplace_back\s*\(',row455) is not None
  extension_index=[x for x in parent['line356_537_mutation_candidates'] if x['line']==455 and 'emplace_back' in x['mutating_method_kinds']]
  count535=re.search(r'\benabledExtensionCount\s*=',row535) is not None
  if not optional_guard or not vector455 or not extension_index or not retry_guard or not count535:
    return {'complete':False,'reason':'OPTIONAL_OR_RETRY_SOURCE_ANCHOR_MISSING',
      'if454':optional_guard,'emplace455':vector455,'if525':retry_guard,'count535':count535}
  # Parent PRE717 extracted entire condition, potentially on multiple lines.
  pre717_errors=sorted(set(x for c in old['candidate_guards'] if c.get('line')==525
     for x in c.get('condition_vk_error_tokens',[])))
  line523_is_direct_call='vkCreateInstance' in row523
  line537_is_direct_call='vkCreateInstance' in row537
  count_field_writes_between_calls=[n for n in range(524,537)
   if re.search(r'\benabledExtensionCount\s*=',l724(n))]
  pointer_field_writes_between_calls=[n for n in range(524,537)
   if re.search(r'\bppEnabledExtensionNames\s*=',l724(n))]
  second_call_in_guard=retry_scope['target_in_lexical_braces']
  # Synthetic *Python-only* count/prefix model; no Vulkan and no source C++ execution.
  originals=['original_A','original_B']
  with_optional=originals+['optional_C']
  initial_count=len(originals)
  synthetic={
   'base_count':initial_count,'after_optional_count':len(with_optional),
   'initial_pointer_prefix_equals_originals':with_optional[:initial_count]==originals,
   'size_count_grows_by_one':len(with_optional)==initial_count+1,
   'same_python_list_placeholder_semantics_only':True}
  return {'complete':True,'line454_is_if':optional_guard,
   'line454_condition_has_negation':bool(re.search(r'!\s*\*',row454)),
   'line454_condition_has_arrow_second':bool(re.search(r'->\s*second\b',row454)),
   'line454_455_scope':optional_scope,
   'line455_is_enabled_extensions_emplace_back':vector455,
   'line455_before_first_vk_create':455<523,
   'line523_vk_create_shape':line523_is_direct_call,
   'line525_if_shape':retry_guard,
   'line525_guard_error_tokens':conditional_error_tokens,
   'line525_error_tokens_from_parent':pre717_errors,
   'line525_537_lexical_scope':retry_scope,
   'line537_second_vk_create_inside_retry_guard_lexically':second_call_in_guard,
   'line537_vk_create_shape':line537_is_direct_call,
   'vk_create_call_args_identical_sha256':first['argument_sha256']==second['argument_sha256'],
   'vk_create_call_arguments_sha256':first['argument_sha256'],
   'count_field_assignment_between_523_537':count_field_writes_between_calls,
   'pointer_field_assignment_between_523_537':pointer_field_writes_between_calls,
   'line535_count_reset_inside_guard_lexically':scope724(525,535,541)['target_in_lexical_braces'],
   'line535_count_reset_to_size_snapshot_355_lexical':parent['line535_arg_parent_sha256_matches'],
   'line455_vector_has_only_single_mutation_candidate':len(parent['line356_537_mutation_candidates'])==1,
   'synthetic_prefix_model':synthetic,
   'synthetic_model_is_actual_cpp_or_vulkan_test':False,
   'guard_really_taken_in_runtime':'NOT_VERIFIED',
   'extension_added_or_enabled_in_runtime':'NOT_VERIFIED',
   'vk_create_first_or_retry_result':'NOT_VERIFIED',
   'cpp_ast_cfg_semantics':'NOT_VERIFIED',
   'actual_pointer_lifetime_and_count':'NOT_VERIFIED',
   'source_to_signed_elf_equivalence':'UNVERIFIED',
   'source_text_exported':False,'private_identifiers_exported':False,
   'stale_pointer_bug_proven':False,'extension_count_mismatch_proven':False}
 f724=probe724()
 report['pre724_optional_extension_retry_branch_audit']={
  'stage':'PRE724_V51_OPTIONAL_EXTENSION_RETRY_GUARD_READONLY',
  'analysis_type':'HASHED_BOUNDED_CPP_LEXICAL_BRANCH_WITH_PYTHON_SYNTHETIC_PREFIX_MODEL',
  'authenticated_v51_source_inherited':True,'real_cpp_ast_or_cfg_used':False,
  'synthetic_model_not_actual_source':True,
  'source_findings':f724,'runtime_vulkan_tested':False,
  'apk_built':False,'apk_modified':False,'signing_material_accessed':False,
  'fps_gain_proven':False,'source_text_exported':False,
  'stale_pointer_bug_proven':False,'extension_count_mismatch_proven':False}
 report['analysis_type']='PRE724_AUTHENTICATED_V51_OPTIONAL_RETRY_GUARD_LEXICAL'
 report['status']=('PASS_PRE724_V51_OPTIONAL_RETRY_LEXICAL_AUDIT'
   if f724['complete'] and f724['line454_455_scope']['target_in_lexical_braces']
      and f724['line537_second_vk_create_inside_retry_guard_lexically']
      and f724['line535_count_reset_inside_guard_lexically']
      and f724['line523_vk_create_shape'] and f724['line537_vk_create_shape']
      and f724['vk_create_call_args_identical_sha256']
      and f724['count_field_assignment_between_523_537']==[535]
      and not f724['pointer_field_assignment_between_523_537']
      and f724['synthetic_prefix_model']['initial_pointer_prefix_equals_originals']
   else 'BLOCK_PRE724_RETRY_LEXICAL_SCOPE_OR_PARENT_DRIFT')
"""

def code(manifest,archive,run,attempt):
    src=pre723.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE724_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE723_KAGGLE_REMOTE.json',MARKER),
      ('PRE723_V51_KAGGLE_SIZE_RECEIVER_READONLY',
       'PRE724_V51_KAGGLE_OPTIONAL_RETRY_READONLY'),
      ("print('PRE723_KAGGLE_GATE=","print('PRE724_KAGGLE_GATE="),
      ("print('PRE723_REPORT=","print('PRE724_REPORT=")
    ):
       if old not in src:raise ValueError('PRE724_PARENT_TOKEN_DRIFT '+old)
       src=src.replace(old,new)
    compile(src,'<PRE724 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre724.ipynb',
         'language':'python','kernel_type':'notebook','is_private':True,
         'enable_gpu':False,'enable_internet':False,
         'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,'metadata':{
      'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre724-purpose','metadata':{},
        'source':['PRE724 authenticated V51 private lexical source; only hashes and metadata leave notebook.']},
       {'cell_type':'code','id':'pre724-readonly','metadata':{},
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
        assert MARKER in src and 'PASS_PRE724_V51_OPTIONAL_RETRY_LEXICAL_AUDIT' in src
        assert "'private_identifiers_exported':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET',
                          'KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
           assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE724_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
       p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE724_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE724_BAD_V51_DEVICE_INSTANCE_HASH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
       if z.testzip() is not None or set(z.namelist())!=set(hashes):
          raise ValueError('PRE724_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre724.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE724_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
