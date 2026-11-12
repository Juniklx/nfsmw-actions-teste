#!/usr/bin/env python3
"""PRE709: narrow V51 Vulkan source guard/lookup syntax audit in isolated private Kaggle.
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
import pre708_generate_private_v51_kernel as pre708

KERNEL="juniklx/nfsmw-pre709-v51-guards-and-lookup-readonly"
TITLE="NFSMW PRE709 V51 Guards And Lookup Readonly"
MARKER="NFSMW_PRE709_KAGGLE_REMOTE.json"
PARENT_FINAL="    else 'BLOCK_CONDITIONS_OR_ARGUMENTS_UNRESOLVED')"
EXTRA=r"""
 # PRE709 checks exact bounded expressions from PRE708 and conservative lexical
 # control-block clues. Everything emitted is from a fixed allowlist or hashes.
 def lexical_role(expr):
  expr=expr.strip()
  calls=sorted(set(re.findall(r'(?:\.|->)\s*(find|contains|count|end|begin|c_str|empty|has_value|value|size|data)\s*\(',expr)))
  tuple_access=sorted(set(int(s) for s in re.findall(r'\b(?:std::)?get\s*<\s*([0-9])\s*>',expr)))
  funs=sorted(set(re.findall(r'\b(get|strcmp|strncmp|find|contains|count)\s*(?:<[^>]{1,40}>)?\s*\(',expr)))
  allowed_tokens=sorted(set(re.findall(r'\b(requested_extensions|enabled_extensions|extensionName|extension|property|extensions|available_extensions|supported_extensions|std|optional)\b',expr)))
  classifiers={
   'requested_extensions_membership_lookup':bool(re.search(r'\brequested_extensions\s*(?:\.|->)\s*(find|count|contains)\s*\(',expr)),
   'requested_extensions_reference':bool(re.search(r'\brequested_extensions\b',expr)),
   'lookup_compares_to_zero':bool(re.search(r'(?:==|!=)\s*0\b|\b0\s*(?:==|!=)',expr)),
   'lookup_compares_to_end':bool(re.search(r'(?:\.|->)\s*end\s*\(',expr)),
   'compares_to_false':bool(re.search(r'(?:==|!=)\s*false\b',expr)),
   'contains_nullptr':bool(re.search(r'\bnullptr\b',expr)),
   'prefix_negated':expr.startswith('!'),
   'has_c_str_call':bool(re.search(r'(?:\.|->)\s*c_str\s*\(',expr)),
   'contains_std_get_template':bool(re.search(r'\b(?:std::)?get\s*<',expr)),
   'has_unbalanced_angle_text':expr.count('<')!=expr.count('>'),
   'has_comparison_double_equals':'==' in expr,
  }
  return {'sha256':hashlib.sha256(expr.encode('utf-8')).hexdigest(),
          'bytes':len(expr.encode('utf-8')),
          'member_method_tokens':calls,'function_tokens':funs,
          'tuple_get_numeric_indices':tuple_access,
          'allowlisted_identifiers':allowed_tokens,
          'indicators':classifiers,
          'no_source_export':True,
          'full_cpp_semantics_proven':False}
 def mask_cpp(source):
  # Preserve byte-offsets and newlines; mask comments and C++ strings/chars.
  # Raw C++ string literals are deliberately flagged as unknown.
  out=list(source); i=0; n=len(source); state='code'; escapes=False
  while i<n:
   c=source[i];nxt=source[i+1] if i+1<n else ''
   if state=='code':
    if c=='/' and nxt=='/':out[i]=' ';out[i+1]=' ';state='line';i+=2;continue
    if c=='/' and nxt=='*':out[i]=' ';out[i+1]=' ';state='block';i+=2;continue
    if c in ('"',"'"):
     out[i]=' ';state=c;escapes=False;i+=1;continue
   elif state=='line':
    if c=='\n':state='code'
    else:out[i]=' '
    i+=1;continue
   elif state=='block':
    if c=='*' and nxt=='/':out[i]=' ';out[i+1]=' ';state='code';i+=2;continue
    if c!='\n':out[i]=' '
    i+=1;continue
   else:
    if c!='\n':out[i]=' '
    if escapes:escapes=False
    elif c=='\\':escapes=True
    elif c==state:state='code'
    i+=1;continue
   i+=1
  return ''.join(out)
 def braced_containment(lines,condition_line,insert_line):
  # Return lexical brace containment only for IF blocks with explicit {}.
  # A braced IF containing the insertion is not equivalent to proven runtime
  # execution; unbraced, macros and preprocessor boundaries stay UNKNOWN.
  first=max(1,condition_line-1)
  last=min(len(lines),insert_line+10)
  chunk='\n'.join(lines[first-1:last])
  starts=[0]
  for m in re.finditer(r'\n',chunk):starts.append(m.end())
  cond_local=condition_line-first
  insert_local=insert_line-first
  if cond_local<0 or insert_local>=len(starts):
   return {'status':'UNKNOWN_BOUNDS'}
  if re.search(r'^\s*#',chunk,re.M) or 'R"(' in chunk:
   return {'status':'UNKNOWN_DIRECTIVE_OR_RAW_STRING'}
  masked=mask_cpp(chunk)
  anchor_start=starts[cond_local];line_end=masked.find('\n',anchor_start)
  if line_end<0:line_end=len(masked)
  ln=masked[anchor_start:line_end]
  m=re.search(r'\bif\s*\(',ln)
  if not m:return {'status':'UNKNOWN_IF_ANCHOR'}
  i=anchor_start+m.end();d=1
  while i<len(masked) and d:
   if masked[i]=='(':d+=1
   elif masked[i]==')':d-=1
   i+=1
  if d:return {'status':'UNKNOWN_IF_PAREN'}
  while i<len(masked) and masked[i].isspace():i+=1
  if i>=len(masked) or masked[i]!='{':
   return {'status':'UNKNOWN_UNBRACED_OR_MACRO'}
  begin=i;depth=1;i+=1
  while i<len(masked) and depth:
   if masked[i]=='{':depth+=1
   elif masked[i]=='}':depth-=1
   i+=1
  if depth:return {'status':'UNKNOWN_UNCLOSED_BRACE'}
  target=starts[insert_local]
  contains=begin<target<i
  return {'status':'BRACED_LEXICAL_SCOPE_ONLY',
          'brace_contains_target_line_start':contains,
          'brace_end_in_scan':True,
          'brace_span_lines':[first+chunk[:begin].count('\n'),first+chunk[:i].count('\n')]}
 def reference_lines(lines,word,lo,hi):
  out=[]
  rx=re.compile(r'\b'+re.escape(word)+r'\b')
  for idx in range(max(1,lo),min(len(lines),hi)+1):
   s=lines[idx-1]
   if not rx.search(s):continue
   tags=[]
   if re.search(r'\b(for|while)\s*\(',s):tags.append('LOOP_LINE')
   if re.search(r'\bif\s*\(',s):tags.append('IF_LINE')
   if re.search(r'\bconst\s+|\bstd::|\bauto\s+',s):tags.append('TYPE_OR_NAMESPACE_TOKEN')
   if re.search(r'\b'+re.escape(word)+r'\s*(?:=|\{)',s):tags.append('ASSIGNMENT_OR_INITIALIZER')
   if re.search(r'\b'+re.escape(word)+r'\s*(?:\.|->)',s):tags.append('MEMBER_METHOD')
   if not tags:tags=['OTHER_MENTION']
   out.append({'line':idx,'tags':tags,
               'line_sha256':hashlib.sha256(s.encode('utf-8')).hexdigest()})
  return out[:60]
 checks={
  'device':(device_lines,[(286,291),(290,291)],291,230,315),
  'instance':(instance_lines,[(448,455),(454,455)],455,400,515),
 }
 details={}
 for label,(lines,if_positions,insert_line,lo,hi) in checks.items():
  selected=[]
  for if_line,target in if_positions:
   p=parse_bounded_parentheses(lines,if_line,'if')
   if not p['extracted']:raise ValueError('PRE709_IF_PARSE_FAILED')
   selected.append({'line':if_line,'expression':lexical_role(p['text']),
                    'lexical_scope':braced_containment(lines,if_line,target)})
  p=parse_bounded_parentheses(lines,insert_line,'emplace_back')
  if not p['extracted']:raise ValueError('PRE709_INSERT_PARSE_FAILED')
  selection=report['pre708_conditions']['files'][label]
  if selection['conditions'][0]['expr_sha256']!=selected[0]['expression']['sha256'] or \
     selection['conditions'][1]['expr_sha256']!=selected[1]['expression']['sha256']:
   raise ValueError('PRE709_PRE708_IF_SHA_MISMATCH')
  insertion=lexical_role(p['text'])
  if selection['insert']['expr_sha256']!=insertion['sha256']:
   raise ValueError('PRE709_PRE708_INSERT_SHA_MISMATCH')
  details[label]={
   'conditions':selected,
   'insertion':{'line':insert_line,'expression':insertion},
   'requested_extensions_mentions':reference_lines(lines,'requested_extensions',lo,hi),
   'source_object_mentions_near_insert':reference_lines(lines,'enabled_extensions',lo,hi),
   'scope':'BOUNDED_CPP_LEXICAL_BRACE_SCOPE_AND_TOKEN_SUMMARY',
   'full_cpp_ast':False,
   'macros_and_unbraced_guards_exhaustively_resolved':False,
   'driver_to_application_mapping_verified':False,
  }
 agreement={
  'first_condition_equal_sha':details['device']['conditions'][0]['expression']['sha256']==details['instance']['conditions'][0]['expression']['sha256'],
  'second_condition_equal_sha':details['device']['conditions'][1]['expression']['sha256']==details['instance']['conditions'][1]['expression']['sha256'],
  'insertion_argument_equal_sha':details['device']['insertion']['expression']['sha256']==details['instance']['insertion']['expression']['sha256'],
 }
 report['pre709_lookup_guards']={
  'stage':'PRE709_V51_EXTENSION_SELECTION_LOOKUP_GUARDS',
  'files':details,
  'textual_pair_consistency':agreement,
  'sources_authenticated':True,
  'no_source_export':True,
  'string_literal_values_exported':False,
  'complete_cpp_control_flow_proven':False,
  'runtime_enabled_extensions':'NOT_VERIFIED',
  'signed_apk_binary_equivalence':'UNVERIFIED',
  'gpu_or_renderer_changed':False,
  'fps_gain_proven':False,
 }
 report['analysis_type']='PRE709_BOUNDED_SOURCE_LOOKUP_AND_LEXICAL_SCOPE_ONLY'
 report['status']=('PASS_AUTHENTICATED_V51_EXTENSION_LOOKUP_GUARDS_LEXICAL_ONLY'
   if all(agreement.values()) and all(
      item['expression']['no_source_export'] for x in details.values()
      for item in x['conditions'])
   else 'BLOCK_PRE709_STRUCTURE_NOT_AUTHENTICATED')
"""
def code(manifest,archive,run,attempt):
    src=pre708.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE709_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE708_KAGGLE_REMOTE.json',MARKER),
        ('PRE708_V51_KAGGLE_CONDITION_ARGUMENT_SYNTAX_READONLY',
         'PRE709_V51_KAGGLE_EXTENSION_LOOKUP_GUARDS_READONLY'),
        ("print('PRE708_KAGGLE_GATE=","print('PRE709_KAGGLE_GATE="),
        ("print('PRE708_REPORT=","print('PRE709_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE709_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE709 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre709.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre709-purpose','metadata':{},
                  'source':['Authenticated V51 Vulkan extension-list lexical scope review; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre709-readonly','metadata':{},
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
        assert MARKER in src and 'BRACED_LEXICAL_SCOPE_ONLY' in src
        assert 'PASS_AUTHENTICATED_V51_EXTENSION_LOOKUP_GUARDS_LEXICAL_ONLY' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE709_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE709_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE709_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE709_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre709.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE709_PRIVATE_KERNEL='+KERNEL)
    print('PRE709_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
