#!/usr/bin/env python3
"""PRE718: authenticated V51 Vulkan instance extension/pointer fallback source-only auditor."""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre717_generate_private_v51_kernel as pre717

KERNEL="juniklx/nfsmw-pre718-v51-instance-pointer-fallback-readonly"
TITLE="NFSMW PRE718 V51 Instance Pointer Fallback Readonly"
MARKER="NFSMW_PRE718_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE717_INSTANCE_RETRY_EVIDENCE_INCOMPLETE')"
EXTRA=r"""
 # PRE718: bounded lexical value-flow of instance create/retry setup.
 # No full C++ parser, lifetime model, runtime, source exports, APK or key access.
 def h718(v): return hashlib.sha256(v.encode('utf-8')).hexdigest()
 def s718(n): return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def operations718(start,end):
  out=[]
  for n in range(start,min(end,len(instance_lines))+1):
   s=s718(n)
   field=sorted(set(re.findall(r'\b(?:enabledExtensionCount|ppEnabledExtensionNames)\b',s)))
   method=[]
   for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\.\s*(data|size|push_back|emplace_back|clear|reserve|resize|assign)\s*\(',s):
    method.append({'operation':m.group(2),'receiver_hash':h718(m.group(1))})
   hasfield=bool(field)
   if hasfield or method or re.search(r'\bvkCreateInstance\s*\(',s):
    out.append({'line':n,'line_sha256':h718(instance_lines[n-1]),
      'fields':field,'methods':method,
      'has_vkCreateInstance_call':bool(re.search(r'\bvkCreateInstance\s*\(',s)),
      'has_pointer_expression':bool(re.search(r'\.\s*data\s*\(',s)),
      'literal_extension_names_exported':False})
  return out
 def field718(n,field):
  s=s718(n)
  p=re.search(r'\b'+re.escape(field)+r'\b\s*=\s*(.+?)(?:;|$)',s)
  if not p: return {'line':n,'assignment_detected':False}
  rhs=p.group(1).strip()
  fun=re.search(r'\b([A-Za-z_]\w*)\s*\.\s*(size|data)\s*\(',rhs)
  return {'line':n,'assignment_detected':True,'rhs_sha256':h718(rhs),
    'rhs_vector_method':fun.group(2) if fun else None,
    'rhs_receiver_hash':h718(fun.group(1)) if fun else None,
    'is_lexical_only':True}
 def call_lhs718(n):
  s=s718(n)
  at=s.find('vkCreateInstance')
  if at<0: return {'line':n,'assignment_detected':False}
  prefix=s[:at]
  m=re.search(r'([A-Za-z_]\w*)\s*=\s*$',prefix)
  return {'line':n,'assignment_detected':bool(m),
   'lhs_identifier_sha256':h718(m.group(1)) if m else None,
   'operator_context_has_assignment':bool(re.search(r'=\s*$',prefix)),
   'full_cpp_variable_binding':'NOT_VERIFIED'}
 def condition718(n):
  parsed=parse_bounded_parentheses(instance_lines,n,'if')
  if not parsed.get('extracted'):
   return {'line':n,'condition_extracted':False}
  s=mask_cpp(parsed['text'])
  toks=sorted(set(re.findall(r'\bVK_ERROR_[A-Z0-9_]+\b',s)))
  identifiers=set(re.findall(r'\b[A-Za-z_]\w*\b',s))
  lhs=[call_lhs718(n) for n in (523,537)]
  names=[]
  for n2 in (523,537):
   pre=s718(n2).split('vkCreateInstance',1)[0]
   m=re.search(r'([A-Za-z_]\w*)\s*=\s*$',pre)
   names.append(m.group(1) if m else None)
  return {'line':n,'condition_extracted':True,'condition_sha256':h718(s),
   'error_constants':toks,
   'contains_both_extension_layer_errors':set(('VK_ERROR_EXTENSION_NOT_PRESENT','VK_ERROR_LAYER_NOT_PRESENT')).issubset(toks),
   'logical_or_present':bool(re.search(r'\|\|',s)),
   'call_assignment_identifiers_mentioned':[bool(name and name in identifiers) for name in names],
   'not_proven_cfg':True}
 def loop718(n):
  p=parse_bounded_parentheses(instance_lines,n,'for')
  if not p.get('extracted'):return {'line':n,'header_extracted':False}
  header=mask_cpp(p['text'])
  return {'line':n,'header_extracted':True,'range_for_token_present':':' in header,
   'header_sha256':h718(header),
   'mentions_requested_extensions':bool(re.search(r'\brequested_extensions\b',header)),
   'not_proven_cfg':True}
 def field_write_lines718(field,lo,hi):
  lines=[]
  for n in range(lo,hi+1):
   if re.search(r'\b'+re.escape(field)+r'\b\s*=',s718(n)):lines.append(n)
  return lines
 sourcehashes={x['path']:x['sha256'] for x in report['source_hashes']}
 if sourcehashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
  raise ValueError('PRE718_INSTANCE_SOURCE_AUTHENTICITY_DRIFT')
 old717=report['pre717_instance_retry_audit']
 if old717['source_findings']['create_calls'][0]['line']!=523 or old717['source_findings']['create_calls'][1]['line']!=537:
  raise ValueError('PRE718_PARENT_VKCREATEINSTANCE_ANCHOR_DRIFT')
 guards=condition718(525)
 fail=(not guards['condition_extracted'] or not guards['contains_both_extension_layer_errors'])
 if fail:raise ValueError('PRE718_FALLBACK_ERROR_GUARD_DRIFT')
 ptr501=field718(501,'ppEnabledExtensionNames')
 count500=field718(500,'enabledExtensionCount')
 count535=field718(535,'enabledExtensionCount')
 ops=operations718(487,540)
 rebuild=[x for x in ops if 523<x['line']<537 and x['methods']]
 ptrwrites=field_write_lines718('ppEnabledExtensionNames',523,537)
 countwrites=field_write_lines718('enabledExtensionCount',523,537)
 priorpush=[o['receiver_hash'] for item in rebuild for o in item['methods'] if o['operation'] in ('push_back','emplace_back')]
 pointer_to_rebuilt={'data_receiver_hash_matches_push_receiver':
   (ptr501['rhs_receiver_hash'] in priorpush) if ptr501.get('rhs_receiver_hash') and priorpush else 'NOT_VERIFIED',
   'count535_size_receiver_hash_matches_push_receiver':
   (count535['rhs_receiver_hash'] in priorpush) if count535.get('rhs_receiver_hash') and priorpush else 'NOT_VERIFIED',
   'pointer_assignment_repeated_between_calls':bool(ptrwrites),
   'pointer_update_lines':ptrwrites,
   'count_update_lines':countwrites,
   'cxx_vector_data_pointer_validity_after_changes':'NOT_VERIFIED',
   'real_memory_reallocation':'NOT_VERIFIED',
   'runtime_pointer_dereference':'NOT_VERIFIED'}
 report['pre718_instance_retry_dataflow_audit']={
  'stage':'PRE718_AUTHENTICATED_V51_INSTANCE_RETRY_VECTOR_POINTER_DATAFLOW',
  'source_sha_checks_inherited_and_crosschecked':True,
  'analysis_type':'CONSERVATIVE_CPP_LEXICAL_POINTER_AND_CREATE_INFO_NO_AST_CFG',
  'source_findings':{
   'source_window':[487,540],
   'line_501_pointer_setup':ptr501,
   'line_500_extension_count_setup':count500,
   'line_535_extension_count_reset':count535,
   'line_525_error_guard':guards,
   'line_528_bool_pointer_loop':loop718(528),
   'line_531_rebuild_loop':loop718(531),
   'instance_create_lhs':[call_lhs718(523),call_lhs718(537)],
   'line_540_status_guard':condition718(540),
   'lexical_operations':ops,
   'candidate_rebuild_operations_between_calls':rebuild,
   'pointer_and_extension_count_correspondence':pointer_to_rebuilt,
   'raw_source_exported':False,'private_identifier_spelling_exported':False,
   'full_cpp_ast_or_cfg_proven':False,'actual_pointer_lifetime_proven':False,
   'runtime_retry_observed':False,
   'runtime_instance_extensions':'NOT_VERIFIED',
   'source_to_signed_apk_elf_equivalence':'UNVERIFIED',
   'vk_google_display_timing_enabled':'NOT_VERIFIED',
   'apk_built':False,'apk_modified':False,'secrets_accessed':False,
   'fps_gain_proven':False},
  'stale_pointer_bug_proven':False,
  'runtime_recovery_proven':False,'source_or_apk_modified':False}
 report['analysis_type']='PRE718_AUTHENTICATED_V51_INSTANCE_RETRY_DATAFLOW_LEXICAL_ONLY'
 report['status']=('PASS_PRE718_V51_CONSERVATIVE_RETRY_POINTER_AUDIT'
  if ptr501['assignment_detected'] and count500['assignment_detected']
     and count535['assignment_detected'] and guards['condition_extracted']
     and len(ops)>=3
  else 'BLOCK_PRE718_POINTER_REBUILD_ANCHOR_INCOMPLETE')
"""

def code(manifest,archive,run,attempt):
    src=pre717.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:
        raise ValueError('PRE718_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
        ('NFSMW_PRE717_KAGGLE_REMOTE.json',MARKER),
        ('PRE717_V51_KAGGLE_INSTANCE_RETRY_BRANCH_READONLY',
         'PRE718_V51_KAGGLE_INSTANCE_POINTER_FALLBACK_READONLY'),
        ("print('PRE717_KAGGLE_GATE=","print('PRE718_KAGGLE_GATE="),
        ("print('PRE717_REPORT=","print('PRE718_REPORT="),
    ):
        if old not in src: raise ValueError('PRE718_PARENT_MISSING_TOKEN '+old)
        src=src.replace(old,new)
    compile(src,'<PRE718 isolated Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    metadata={'id':KERNEL,'title':TITLE,'code_file':'pre718.ipynb',
              'language':'python','kernel_type':'notebook','is_private':True,
              'enable_gpu':False,'enable_internet':False,'dataset_sources':[],
              'competition_sources':[],'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
        'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
        'cells':[{'cell_type':'markdown','id':'pre718-purpose','metadata':{},
           'source':['Authenticated source-only Vulkan instance pointer and fallback investigation. No runtime or APK changes.']},
         {'cell_type':'code','id':'pre718-readonly','metadata':{},
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
        assert MARKER in script and "PASS_PRE718_V51_CONSERVATIVE_RETRY_POINTER_AUDIT" in script
        assert "'stale_pointer_bug_proven':False" in script
        assert "'raw_source_exported':False" in script
        for name in ('GOOGLE_REFRESH_TOKEN','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert name not in script
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,notebook=build({},b'fake','123','1')
        assert meta['is_private'] and not meta['enable_internet'] and not meta['enable_gpu']
        assert len(notebook['cells'])==2
        print('PRE718_SYNTHETIC=PASS')
        return
    if not all((args.manifest,args.archive,args.output,args.run_id)):
        parser.error('missing required input')
    if not re.fullmatch(r'[0-9]+',args.run_id) or not re.fullmatch(r'[0-9]+',args.attempt):
        parser.error('numeric run ids only')
    manifest=json.loads(args.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE718_UNAUTHENTICATED_V51_MANIFEST')
    hashes={entry['path']:entry['sha256'] for entry in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE718_DEVICE_INSTANCE_HASH_DRIFT')
    payload=args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE718_BAD_AUTHENTICATED_SOURCE_ARCHIVE')
    meta,notebook=build(manifest,payload,args.run_id,args.attempt)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (args.output/'pre718.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE718_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__': main()
