#!/usr/bin/env python3
"""PRE721: read-only V51 count RHS callee/args vs for531/member532 lexical probe."""
import argparse
import io
import json
import re
import zipfile
from pathlib import Path
import pre704_generate_private_v51_kernel as pre704
import pre706_generate_private_v51_kernel as pre706
import pre720_generate_private_v51_kernel as pre720

KERNEL="juniklx/nfsmw-pre721-v51-call-range-readonly"
TITLE="NFSMW PRE721 V51 Call Range Readonly"
MARKER="NFSMW_PRE721_KAGGLE_REMOTE.json"
PARENT_FINAL="  else 'BLOCK_PRE720_SOURCE_SYNTAX_ANCHORS_UNRESOLVED')"
EXTRA=r"""
 # PRE721: bounded callee/argument and range-item/member linkage probe.
 # Lexical-only; hashes only; never export private identifier spellings.
 def h721(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
 def l721(n): return mask_cpp(instance_lines[n-1]) if 1<=n<=len(instance_lines) else ''
 def bare721(s): return re.fullmatch(r'[A-Za-z_]\w*',s.strip())
 def chunks721(s):
  segments=[]; cur=[]; stack=[]; mp={')':'(',']':'[','}':'{','>':'<'}
  for c in s:
   if c in '([{':stack.append(c)
   elif c in ')]}':
    if stack and stack[-1]==mp[c]:stack.pop()
   if c==',' and not stack:
    segments.append(''.join(cur).strip());cur=[]
   else:cur.append(c)
  if cur or s.strip():segments.append(''.join(cur).strip())
  return segments
 if chunks721('a, fn(b,c), z')!=['a','fn(b,c)','z']:
  raise ValueError('PRE721_SPLIT_NESTED_SYNTHETIC_FAIL')
 def f721(n):
  p=parse_bounded_parentheses(instance_lines,n,'for')
  if not p.get('extracted'):return None
  return split720(mask_cpp(p['text']))
 def probe721():
  header=f721(531)
  if not header:return {'complete':False,'reason':'RANGE531_HEADER_MISSING'}
  lhs,range_name=header
  r=re.findall(r'[A-Za-z_]\w*',lhs)
  loop_variable=r[-1] if r else None
  row532=l721(532)
  m=re.search(r'\b([A-Za-z_]\w*)\s*(->|\.)\s*([A-Za-z_]\w*)\s*=\s*([^;]+)',row532)
  member={}
  if m:
   owner,operator,field,value=m.groups()
   member={'assignment_extracted':True,'receiver_sha256':h721(owner),
     'field_sha256':h721(field),'rhs_sha256':h721(value.strip()),
     'receiver_matches_loop_variable':bool(loop_variable and owner==loop_variable),
     'access_is_arrow':operator=='->','access_is_dot':operator=='.',
     'rhs_is_boolean_true':value.strip()=='true',
     'rhs_is_boolean_false':value.strip()=='false',
     'rhs_is_integer_zero':value.strip()=='0',
     'rhs_single_identifier':bool(bare721(value)),
     'raw_assignment_exported':False}
  else:
   member={'assignment_extracted':False,'raw_assignment_exported':False}
  row535=l721(535)
  assign=re.search(r'\benabledExtensionCount\b\s*=\s*([^;]+)',row535)
  if not assign:return {'complete':False,'reason':'COUNT535_ASSIGNMENT_MISSING'}
  expr=assign.group(1).strip()
  old=report['pre720_range_rhs_syntax_audit']['source_findings']
  if h721(expr)!=old['extension_count_535_rhs']['rhs_sha256']:
   raise ValueError('PRE721_COUNT535_HASH_MISMATCH')
  cm=re.match(r'^([A-Za-z_]\w*)\s*\(',expr)
  call={}
  if cm:
   callee=cm.group(1)
   left=expr.index('(',cm.start(0))
   depth=0;close=None
   for i in range(left,len(expr)):
    if expr[i]=='(':depth+=1
    elif expr[i]==')':
     depth-=1
     if depth==0:
      close=i;break
   if close is None: raise ValueError('PRE721_UNBALANCED_COUNT535_EXPRESSION')
   argstr=expr[left+1:close].strip()
   args=chunks721(argstr)
   call={'leading_identifier_call_shape':True,'callee_sha256':h721(callee),
     'callee_is_integer_type_spelling':bool(re.fullmatch(r'(?:u?int(?:8|16|32|64)_t|size_t|VkBool32|uint|int|unsigned)',callee)),
     'callee_is_vulkan_prefixed':callee.startswith('Vk'),
     'argument_count_lexical':len(args),
     'arguments_sha256':[h721(a) for a in args],
     'any_argument_mentions_range531_receiver':any(bool(re.search(r'(?<!\w)'+re.escape(range_name)+r'(?!\w)',a)) for a in args),
     'any_argument_mentions_loop531_variable':any(bool(loop_variable and re.search(r'(?<!\w)'+re.escape(loop_variable)+r'(?!\w)',a)) for a in args),
     'any_argument_has_method_call':any(bool(re.search(r'(?:\.|->)\s*[A-Za-z_]\w*\s*\(',a)) for a in args),
     'trailing_non_whitespace_after_closing_parenthesis':bool(expr[close+1:].strip()),
     'callee_cpp_entity_kind':'NOT_VERIFIED',
     'raw_expression_exported':False}
  else:call={'leading_identifier_call_shape':False,'raw_expression_exported':False}
  seen=[]
  for n in range(250,531):
   line=l721(n)
   if re.search(r'(?<!\w)'+re.escape(range_name)+r'(?!\w)',line):
    seen.append({'line':n,'line_sha256':h721(instance_lines[n-1]),
     'has_assignment_operator':bool(re.search(r'(?<![!<>=])=(?!=)',line)),
     'has_vector_token':bool(re.search(r'\bvector\b',line)),
     'has_map_token':bool(re.search(r'\b(?:map|unordered_map)\b',line)),
     'has_brace_initializer':'{' in line,
     'has_decltype_or_auto':bool(re.search(r'\b(?:decltype|auto)\b',line))})
  return {'complete':True,'loop531_variable_found':bool(loop_variable),
    'loop531_variable_sha256':h721(loop_variable) if loop_variable else None,
    'loop531_receiver_sha256':h721(range_name),
    'loop531_receiver_matches_pre720':h721(range_name)==old['loop531']['rhs_sha256'],
    'loop531_preceding_references_total':len(seen),
    'loop531_preceding_references_tail':seen[-12:],
    'line532_member_assignment':member,'line535_callable_shape':call,
    'lexical_identity_only':True,
    'pointer_alias_or_cpp_type_proven':False,
    'runtime_enabled_extension_count':'NOT_VERIFIED',
    'runtime_vkCreateInstance_retry':'NOT_VERIFIED',
    'raw_cpp_source_exported':False,
    'raw_identifier_exported':False}
 find721=probe721()
 report['pre721_call_range_linkage_audit']={
  'stage':'PRE721_AUTHENTICATED_V51_COUNT535_CALL_RANGE531_MEMBER532_READONLY',
  'analysis_type':'BOUNDED_CPP_LEXICAL_CALLEE_ARGUMENT_AND_MEMBER_RECEIVER_LINKAGE',
  'source_findings':find721,
  'source_sha_checks_inherited':True,
  'actual_cpp_type_or_semantics_proven':False,
  'real_extension_count_mismatch_proven':False,
  'stale_pointer_bug_proven':False,
  'source_to_signed_elf_equivalence':'UNVERIFIED',
  'apk_built':False,'apk_modified':False,
  'signing_material_accessed':False,'fps_gain_proven':False}
 report['analysis_type']='PRE721_AUTHENTICATED_V51_CALL_RANGE_LINKAGE_LEXICAL'
 report['status']=('PASS_PRE721_V51_BOUNDED_CALL_RANGE_LINKAGE_AUDIT'
    if find721['complete'] and find721['loop531_receiver_matches_pre720']
       and 'line532_member_assignment' in find721
       and 'line535_callable_shape' in find721
    else 'BLOCK_PRE721_LEXICAL_ANCHOR_MISMATCH')
"""

def code(manifest,archive,run,attempt):
    src=pre720.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE721_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    for old,new in (
      ('NFSMW_PRE720_KAGGLE_REMOTE.json',MARKER),
      ('PRE720_V51_KAGGLE_RANGE_RHS_SYNTAX_READONLY',
       'PRE721_V51_KAGGLE_CALL_RANGE_LINKAGE_READONLY'),
      ("print('PRE720_KAGGLE_GATE=","print('PRE721_KAGGLE_GATE="),
      ("print('PRE720_REPORT=","print('PRE721_REPORT=")
    ):
        if old not in src:raise ValueError('PRE721_PARENT_TOKEN_MISSING '+old)
        src=src.replace(old,new)
    compile(src,'<PRE721 isolated notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre721.ipynb',
          'language':'python','kernel_type':'notebook','is_private':True,
          'enable_gpu':False,'enable_internet':False,
          'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,
      'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
      'cells':[{'cell_type':'markdown','id':'pre721-purpose','metadata':{},
       'source':['PRE721 V51 authenticated lexical-only callee, argument and range-identifier audit.']},
      {'cell_type':'code','id':'pre721-readonly','metadata':{},
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
        assert MARKER in src
        assert 'PASS_PRE721_V51_BOUNDED_CALL_RANGE_LINKAGE_AUDIT' in src
        assert "'raw_cpp_source_exported':False" in src
        assert "'stale_pointer_bug_proven':False" in src
        for forbidden in ('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_SECRET','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'):
            assert forbidden not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE721_SYNTHETIC=PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required inputs')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('invalid run/attempt')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),
      manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
        raise ValueError('PRE721_BAD_AUTHENTICATED_MANIFEST')
    hashes={e['path']:e['sha256'] for e in manifest['entries']}
    if hashes.get(pre706.DEVICE)!=pre706.DEVICE_SHA or hashes.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
        raise ValueError('PRE721_BAD_DEVICE_INSTANCE_HASHES')
    payload=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or set(z.namelist())!=set(hashes):
            raise ValueError('PRE721_BAD_SOURCE_ARCHIVE')
    meta,note=build(manifest,payload,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre721.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE721_PRIVATE_KERNEL='+KERNEL)

if __name__=='__main__':main()
