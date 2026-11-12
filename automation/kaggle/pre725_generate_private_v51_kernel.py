#!/usr/bin/env python3
"""PRE725 V51 authenticated read-only .size() receiver versus .data() source."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre724_generate_private_v51_kernel as pre724

KERNEL="juniklx/nfsmw-pre725-v51-dynamic-extension-origin"
TITLE="NFSMW PRE725 V51 Dynamic Extension Origin"
MARKER="NFSMW_PRE725_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE724_RETRY_LEXICAL_SCOPE_OR_PARENT_DRIFT')"
EXTRA=r"""
 # PRE725: determine whether optional insert is a literal Vulkan extension or dynamic name.
 # Only recognized public tokens / hashed private identifiers leave the Kaggle source.
 def h725(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def l725(lines,n):return mask_cpp(lines[n-1]) if 1<=n<=len(lines) else ''
 def extract725(lines,n):
  txt=l725(lines,n)
  m=re.search(r'\benabled_extensions\s*\.\s*emplace_back\s*\(',txt)
  if not m:return {'found':False}
  pos=m.end();depth=1;res=[]
  for c in txt[pos:]:
   if c=='(':depth+=1
   if c==')':
    depth-=1
    if depth==0:break
   res.append(c)
  return {'found':depth==0,'raw':''.join(res).strip()}
 def probe725():
  p724=report['pre725_optional_extension_retry_branch_audit']['source_findings']
  p708=report['pre708_conditions']['files']
  a=extract725(instance_lines,455);b=extract725(device_lines,291)
  if not a['found'] or not b['found']:return {'complete':False,'reason':'INSERTION_ARGUMENT_PARSE_FAILED'}
  i=a['raw'];d=b['raw']
  # A name loaded from a member of a runtime object is not a fixed literal extension.
  cstr=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)\s*\.\s*c_str\s*\(\s*\)\s*',i)
  lits=re.findall(r'"[^"\n]*"',i)
  vk_tokens=sorted(set(re.findall(r'\bVK_[A-Za-z0-9_]+\b',i)))
  exact_sha_match=h725(i)==p708['instance']['insert']['expr_sha256']
  cross_sha_match=h725(i)==p708['device']['insert']['expr_sha256']
  matched_base=bool(cstr) and h725(cstr.group(1))==report['pre711_operand_links']['files']['instance']['cstr_receiver']['receiver_object_sha256']
  matched_member=bool(cstr) and h725(cstr.group(2))==report['pre711_operand_links']['files']['instance']['cstr_receiver']['member_name_sha256']
  # Call-site extension domain is determined by which creation structure receives this array.
  ctx=report['pre706_provenance']['anchors']
  inst_create=('vkCreateInstance' in l725(instance_lines,523) and
      'ppEnabledExtensionNames' in l725(instance_lines,501))
  dev_create=('vkCreateDevice' in ''.join(l725(device_lines,n) for n in range(290,340)))
  # Existing cross-check of request-selection form in two C++ files.
  return {'complete':True,
   'instance_insert_line':455,'device_insert_line':291,
   'instance_argument_sha256':h725(i),
   'device_argument_sha256':h725(d),
   'instance_device_insert_arguments_equal_lexically':i==d,
   'matches_pre708_instance_argument_sha256':exact_sha_match,
   'matches_pre708_device_argument_sha256':cross_sha_match,
   'argument_is_arrow_member_cstr_call_lexically':bool(cstr),
   'argument_receiver_hash_matches_pre711':matched_base,
   'argument_member_hash_matches_pre711':matched_member,
   'argument_is_fixed_string_literal':bool(lits) and i.startswith('"'),
   'argument_has_any_string_literal':bool(lits),
   'argument_has_vulkan_macro_token':bool(vk_tokens),
   'literal_vulkan_tokens':vk_tokens,
   'argument_is_dynamic_member_cstr_syntax':bool(cstr) and not lits and not vk_tokens,
   'insertion_context_vk_create_instance':inst_create,
   'insertion_context_vk_create_device_separate':dev_create,
   'instance_insert_belongs_to_instance_extension_name_vector_lexical':p724['line455_is_enabled_extensions_emplace_back'] and inst_create,
   'requested_extension_filter_first_guard_448_450':bool(report['pre709_lookup_guards']['files']['instance']['conditions'][0]['lexical_scope']['brace_span_lines']==[448,450]),
   'optional_guard_second_if_454_458':p724['line454_455_scope']['target_in_lexical_braces'],
   'fallback_guard_525_538':p724['line537_second_vk_create_inside_retry_guard_lexically'],
   'individual_extension_name_identified':'NO_STATIC_NAME_DYNAMIC_SOURCE',
   'extension_runtime_value':'NOT_VERIFIED',
   'advertised_not_equivalent_to_enabled':True,
   'actual_extension_is_device_or_instance':'INSTANCE_ARGUMENT_AT_VKCREATEINSTANCE_CALLSITE_LEXICAL',
   'cpp_type_aliasing_ast_cfg':'NOT_VERIFIED',
   'real_vulkan_driver_calls':'NOT_VERIFIED',
   'real_extension_names_exported':False,'raw_source_exported':False,
   'private_identifiers_exported':False,'source_to_signed_elf_equivalence':'UNVERIFIED',
   'apk_built':False,'apk_modified':False,'signing_accessed':False,
   'fps_gain_proven':False}
 f725=probe725()
 report['pre725_optional_extension_name_origin_audit']={
  'stage':'PRE725_V51_OPTIONAL_EXTENSION_NAME_ORIGIN_READONLY',
  'source_findings':f725,'source_text_exported':False,
  'real_cpp_ast_used':False,'vulkan_runtime_tested':False,
  'apk_built':False,'apk_modified':False,'signing_material_accessed':False,
  'fps_gain_proven':False}
 report['analysis_type']='PRE725_AUTHENTICATED_V51_DYNAMIC_EXTENSION_NAME_ORIGIN_LEXICAL'
 report['status']=('PASS_PRE725_DYNAMIC_INSTANCE_EXTENSION_ORIGIN_AUDIT'
  if f725['complete'] and f725['argument_is_dynamic_member_cstr_syntax']
   and f725['instance_device_insert_arguments_equal_lexically']
   and f725['matches_pre708_instance_argument_sha256']
   and f725['argument_receiver_hash_matches_pre711']
   and f725['argument_member_hash_matches_pre711']
   and f725['insertion_context_vk_create_instance']
   and f725['optional_guard_second_if_454_458']
   and f725['fallback_guard_525_538']
  else 'BLOCK_PRE725_EXTENSION_NAME_ORIGIN_OR_PARENT_DRIFT')
"""

def code(manifest,archive,run,attempt):
    src=pre724.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE725_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE724_KAGGLE_REMOTE.json',MARKER),
      ('PRE724_V51_KAGGLE_OPTIONAL_RETRY_READONLY',
       'PRE725_V51_KAGGLE_DYNAMIC_EXTENSION_ORIGIN_READONLY'),
      ("print('PRE724_KAGGLE_GATE=","print('PRE725_KAGGLE_GATE="),
      ("print('PRE724_REPORT=","print('PRE725_REPORT=")
    ):
       if old not in src:raise ValueError('PRE725_PARENT_TOKEN_DRIFT '+old)
       src=src.replace(old,new)
    compile(src,'<PRE725 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre725.ipynb',
         'language':'python','kernel_type':'notebook','is_private':True,
         'enable_gpu':False,'enable_internet':False,
         'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,'metadata':{
      'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre725-purpose','metadata':{},
        'source':['PRE725 authenticated V51 private lexical source; only hashes and metadata leave notebook.']},
       {'cell_type':'code','id':'pre725-readonly','metadata':{},
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
        assert MARKER in src and 'PASS_PRE725_DYNAMIC_INSTANCE_EXTENSION_ORIGIN_AUDIT' in src
        assert "'private_identifiers_exported':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET',
                          'KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
           assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'fixture','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE725_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
       p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
        manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE725_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE725_BAD_V51_DEVICE_INSTANCE_HASH')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
       if z.testzip() is not None or set(z.namelist())!=set(hashes):
          raise ValueError('PRE725_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre725.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE725_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
