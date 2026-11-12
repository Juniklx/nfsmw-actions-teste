#!/usr/bin/env python3
"""PRE717: authenticated V51 bounded vkCreateInstance retry/guard/flag audit.
Private Kaggle notebook; never export raw source, secrets, binaries, or runtime claims.
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
import pre716_generate_private_v51_kernel as pre716

KERNEL="juniklx/nfsmw-pre717-v51-instance-retry-branch-readonly"
TITLE="NFSMW PRE717 V51 Instance Retry Branch Readonly"
MARKER="NFSMW_PRE717_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE716_VECTOR_OR_ALIAS_DRIFT')"
EXTRA=r"""
 # PRE717: bounded source-only control-site audit around two vkCreateInstance calls.
 # Report lexical order, argument correspondence, guard/error tokens and flag write linkage.
 # This is NOT an AST, CFG, executed retry test, or Vulkan runtime proof.
 def hash717(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def clean717(number):
  return mask_cpp(instance_lines[number-1]) if 1<=number<=len(instance_lines) else ''
 def call717(n):
  item=parse_bounded_parentheses(instance_lines,n,'vkCreateInstance')
  return {'line':n,'extracted':bool(item.get('extracted')),
    'argument_sha256':hash717(item['text'].strip()) if item.get('extracted') else None,
    'argument_count_lexical':(item['text'].count(',')+1) if item.get('extracted') else None,
    'not_cpp_argument_parser':True}
 def guard717(n):
  row=clean717(n)
  types=[k for k in ('if','else','for','while') if re.search(r'\b'+k+r'\b',row)]
  if not types:return None
  result={'line':n,'keyword_kinds':types,'line_sha256':hash717(instance_lines[n-1]),
    'contains_vkCreateInstance':bool(re.search(r'\bvkCreateInstance\s*\(',row)),
    'contains_vk_success':bool(re.search(r'\bVK_SUCCESS\b',row)),
    'vk_error_tokens':sorted(set(re.findall(r'\bVK_ERROR_[A-Z0-9_]+\b',row))),
    'mentions_bool_literal':bool(re.search(r'\b(?:true|false)\b',row)),
    'not_formal_control_flow':True}
  if 'if' in types:
   p=parse_bounded_parentheses(instance_lines,n,'if')
   result['condition_extracted']=bool(p.get('extracted'))
   if p.get('extracted'):
    s=mask_cpp(p['text'])
    result['condition_sha256']=hash717(s)
    result['condition_vk_error_tokens']=sorted(set(re.findall(r'\bVK_ERROR_[A-Z0-9_]+\b',s)))
    result['condition_contains_vkCreateInstance']=bool(re.search(r'\bvkCreateInstance\s*\(',s))
    result['condition_contains_vk_success']=bool(re.search(r'\bVK_SUCCESS\b',s))
    result['has_comparison_or_negation']=bool(re.search(r'(?:==|!=|<=|>=|(?<![=!])!(?!=))',s))
  return result
 def for_link717(n):
  p=parse_bounded_parentheses(instance_lines,n,'for')
  if not p.get('extracted'):
   return {'for_header_extracted':False,'loop_variable_match_to_deref529':'NOT_VERIFIED',
       'vector_receiver_match':'NOT_VERIFIED'}
  header=mask_cpp(p['text']).strip()
  if ':' not in header:
   return {'for_header_extracted':True,'range_for_shape':False,
    'loop_variable_match_to_deref529':'NOT_VERIFIED','vector_receiver_match':'NOT_VERIFIED'}
  lhs,rhs=header.split(':',1)
  names=re.findall(r'\b[A-Za-z_]\w*\b',lhs)
  var=names[-1] if names else None
  deref=re.search(r'(?<![/*])\*\s*([A-Za-z_]\w*)\s*=\s*(?:false|0)\b',clean717(529))
  decl=report['pre716_boolptr_lifetime_map']['source_findings']['instance_declared_vector']
  vector_name=None
  v=re.search(r'\bstd\s*::\s*vector\s*<\s*bool\s*\*\s*>\s*([A-Za-z_]\w*)\s*;',clean717(356))
  if v: vector_name=v.group(1)
  return {'for_header_extracted':True,'range_for_shape':True,
   'for_line':n,'loop_variable_sha256':hash717(var) if var else None,
   'loop_variable_match_to_deref529':bool(var and deref and var==deref.group(1)),
   'vector_receiver_match':bool(vector_name and rhs.strip()==vector_name),
   'vector_receiver_sha_matches_pre716':bool(vector_name and hash717(vector_name)==decl['declared_name_sha256']),
   'direct_pointer_write_line529':bool(deref),
   'pointer_target_or_lifetime_proven':False,
   'not_cpp_ast':True}
 calls=[i for i,s in enumerate(instance_lines,1)
        if re.search(r'\bvkCreateInstance\s*\(',mask_cpp(s))]
 previous=report['pre716_boolptr_lifetime_map']['source_findings']['instance_create_info']['create_lines']
 if calls!=previous or calls!=[523,537]:
  raise ValueError('PRE717_VKINSTANCE_CALL_ANCHOR_DRIFT')
 create=[call717(x) for x in calls]
 guards=[x for x in (guard717(i) for i in range(516,541)) if x is not None]
 boolwrites=report['pre716_boolptr_lifetime_map']['source_findings']['instance_explicit_boolean_write_candidates']['candidates']
 linked=for_link717(528)
 extension_counts=[i for i in range(516,541)
   if re.search(r'\benabledExtensionCount\b',clean717(i))]
 extension_ptrs=[i for i in range(516,541)
   if re.search(r'\bppEnabledExtensionNames\b',clean717(i))]
 facts={'create_calls':create,'first_second_call_arguments_lexically_equal':
    (create[0]['argument_sha256']==create[1]['argument_sha256'])
    if all(z['extracted'] for z in create) else 'NOT_VERIFIED',
   'candidate_guards':guards,
   'guard_scan_window_lines':[516,540],
   'loop_line528_to_write529':linked,
   'boolean_write_candidates':boolwrites,
   'writes_after_first_before_second':[z['line'] for z in boolwrites if 523<z['line']<537],
   'extension_count_mentions_between_calls':extension_counts,
   'extension_name_pointer_mentions_between_calls':extension_ptrs,
   'second_call_after_pointer_write':bool(523<529<537 and linked['direct_pointer_write_line529']),
   'conditions_proven_cpp_cfg':False,
   'vk_create_instance_retry_executed_at_runtime':'NOT_VERIFIED',
   'boolean_pointer_storage_lifetime':'NOT_VERIFIED',
   'logical_branch_taken_runtime':'NOT_VERIFIED',
   'runtime_instance_extensions':'NOT_VERIFIED',
   'source_to_installed_signed_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'source_text_exported':False,
   'signing_material_accessed':False,'apk_built':False,
   'apk_modified':False,'fps_gain_proven':False}
 report['pre717_instance_retry_audit']={
   'stage':'PRE717_AUTHENTICATED_V51_VKCREATEINSTANCE_RETRY_BRANCH_SOURCE_AUDIT',
   'source_sha_checks_inherited_from_PRE704':True,
   'analysis_type':'LEXICAL_CONTROL_AND_BOOL_PTR_LINK_ONLY_NOT_CPP_AST_OR_CFG',
   'source_findings':facts,
   'actual_recovery_semantics_proven':False,
   'runtime_retry_observed':False,
   'no_source_or_apk_changes':True}
 report['analysis_type']='PRE717_AUTHENTICATED_V51_INSTANCE_RETRY_CONSERVATIVE_LEXICAL_ONLY'
 report['status']=('PASS_PRE717_V51_SOURCE_RETRY_CANDIDATE_AUDITED'
  if all(z['extracted'] for z in create)
     and linked['for_header_extracted']
     and linked['direct_pointer_write_line529']
     and facts['second_call_after_pointer_write']
  else 'BLOCK_PRE717_INSTANCE_RETRY_EVIDENCE_INCOMPLETE')
"""

def code(manifest,archive,run,attempt):
    src=pre716.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:
        raise ValueError('PRE717_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
        ('NFSMW_PRE716_KAGGLE_REMOTE.json',MARKER),
        ('PRE716_V51_KAGGLE_BOOL_POINTER_LIFETIME_READONLY',
         'PRE717_V51_KAGGLE_INSTANCE_RETRY_BRANCH_READONLY'),
        ("print('PRE716_KAGGLE_GATE=","print('PRE717_KAGGLE_GATE="),
        ("print('PRE716_REPORT=","print('PRE717_REPORT="),
    ):
        if old not in src: raise ValueError('PRE717_PARENT_MISSING_TOKEN '+old)
        src=src.replace(old,new)
    compile(src,'<PRE717 isolated Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    metadata={'id':KERNEL,'title':TITLE,'code_file':'pre717.ipynb',
              'language':'python','kernel_type':'notebook','is_private':True,
              'enable_gpu':False,'enable_internet':False,'dataset_sources':[],
              'competition_sources':[],'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
        'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
        'cells':[{'cell_type':'markdown','id':'pre717-purpose','metadata':{},
           'source':['Authenticated source-only review of possible Vulkan instance retry; no runtime or APK changes.']},
         {'cell_type':'code','id':'pre717-readonly','metadata':{},
          'source':src.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    return metadata,notebook

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--attempt',default='1')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        script=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'fake','123','1')
        assert MARKER in script
        assert 'PASS_PRE717_V51_SOURCE_RETRY_CANDIDATE_AUDITED' in script
        assert "'actual_recovery_semantics_proven':False" in script
        assert "'source_text_exported':False" in script
        for name in ('GOOGLE_REFRESH_TOKEN','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert name not in script
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,notebook=build({},b'fake','123','1')
        assert meta['is_private'] and not meta['enable_internet'] and not meta['enable_gpu']
        assert len(notebook['cells'])==2
        print('PRE717_SYNTHETIC=PASS')
        return
    if not all((args.manifest,args.archive,args.output,args.run_id)):
        parser.error('missing required input')
    if not re.fullmatch(r'[0-9]+',args.run_id) or not re.fullmatch(r'[0-9]+',args.attempt):
        parser.error('numeric run ids only')
    manifest=json.loads(args.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE717_UNAUTHENTICATED_V51_MANIFEST')
    hashes={entry['path']:entry['sha256'] for entry in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE717_DEVICE_INSTANCE_HASH_DRIFT')
    payload=args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE717_BAD_AUTHENTICATED_SOURCE_ARCHIVE')
    meta,notebook=build(manifest,payload,args.run_id,args.attempt)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (args.output/'pre717.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE717_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__': main()
