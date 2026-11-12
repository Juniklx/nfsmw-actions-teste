#!/usr/bin/env python3
"""PRE715: bounded source alias, predicate and push_back audit in private Kaggle.
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
import pre711_generate_private_v51_kernel as pre711
import pre712_generate_private_v51_kernel as pre712
import pre713_generate_private_v51_kernel as pre713
import pre714_generate_private_v51_kernel as pre714

KERNEL="juniklx/nfsmw-pre715-v51-types-precedence-readonly"
TITLE="NFSMW PRE715 V51 Types Precedence Readonly"
MARKER="NFSMW_PRE715_KAGGLE_REMOTE.json"
PARENT_FINAL="   else 'BLOCK_PRE714_NEGATION_OR_CONTAINER_UNRESOLVED')"
EXTRA=r"""
 # PRE715: two evidence classes: a C++ compiler *synthetic fixture* for operator
 # precedence; and authenticated V51 lexical type-declaration probes. NEVER
 # treat the fixture as the shipped code's AST, nor output arbitrary source.
 import subprocess
 import shutil
 import tempfile
 def p715_hash(v):return hashlib.sha256(v.encode('utf-8')).hexdigest()
 def p715_find_balanced_angle(s,index):
  depth=0
  for j in range(index,len(s)):
   if s[j]=='<':depth+=1
   elif s[j]=='>':
    depth-=1
    if depth==0:return j
  return None
 def p715_vector_declaration(lines,index,target_hash):
  original=lines[index-1]
  masked=mask_cpp(original)
  m=re.search(r'\bstd\s*::\s*vector\s*<',masked)
  if not m:return {'status':'STD_VECTOR_NOT_PRESENT','line':index}
  beg=m.end()-1
  end=p715_find_balanced_angle(masked,beg)
  if end is None:return {'status':'TEMPLATE_UNBALANCED','line':index}
  inner=masked[beg+1:end].strip()
  tail=masked[end+1:].strip()
  nm=re.match(r'(?:(?:const|volatile)\s+)?([A-Za-z_]\w*)\s*(?:;|=|\{|$)',tail)
  target=(nm.group(1) if nm else None)
  recognized={'bool':'BOOL','char':'CHAR','void':'VOID','std':'STD',
              'string':'STRING','string_view':'STRING_VIEW','VkExtensionProperties':'VK_EXTENSION_PROPERTIES'}
  public_tokens=sorted({recognized[x] for x in re.findall(r'\b[A-Za-z_]\w*\b',inner) if x in recognized})
  return {'status':'SIMPLE_STD_VECTOR_DECLARATION_LEXICAL' if nm else 'TYPE_FOUND_DECLARATION_NOT_RESOLVED',
   'line':index,'line_sha256':p715_hash(original),
   'type_expr_sha256':p715_hash(inner),
   'type_has_bool_pointer':bool(re.search(r'\bbool\s*\*',inner)),
   'type_has_const_char_pointer':bool(re.search(r'\bconst\s+char\s*\*',inner)),
   'type_has_string_view':bool(re.search(r'\bstring_view\b',inner)),
   'type_contains_pointer_syntax':'*' in inner,
   'recognized_type_tokens':public_tokens,
   'declared_variable_sha256':p715_hash(target) if target else None,
   'declared_variable_matches_pushback_receiver':p715_hash(target)==target_hash if target else False,
   'has_semicolon_terminator':bool(re.search(r';\s*$',tail)),
   'has_initializer_equal':bool(re.search(r'=',tail)),
   'cpp_type_inferred_only':True,
   'lifetime_and_ownership_proven':False,'source_text_exported':False}
 def p715_requested_declaration(lines,forline):
  # Limited 180-line lookback, classify types with no source text or arbitrary IDs.
  begin=max(1,forline-180)
  matches=[]
  for i in range(begin,forline):
   ln=mask_cpp(lines[i-1])
   if not re.search(r'\brequested_extensions\b',ln):continue
   pre=ln.split('requested_extensions',1)[0]
   types=re.findall(r'\bstd\s*::\s*(unordered_map|map|unordered_set|set|vector|array)\s*<',pre)
   maycont=bool(re.search(r'\brequested_extensions\s*(?:=|\{|\()',ln))
   matches.append({'line':i,'declaration_candidate':bool(types),
    'container_type':types[-1] if types else None,
    'map_type_has_bool_pointer_before_name':bool(re.search(r'\bbool\s*\*',pre)),
    'map_type_has_string_or_view_before_name':bool(re.search(r'\b(?:string|string_view)\b',pre)),
    'has_initializer_or_ctor_after_name':maycont,
    'line_sha256':p715_hash(lines[i-1])})
  return {'range_lines':[begin,forline-1],
   'requested_extensions_mentions':len(matches),
   'typed_declaration_candidates':sum(1 for x in matches if x['declaration_candidate']),
   'candidates':matches[:8],
   'multiline_type_declarations_fully_resolved':False,
   'actual_cpp_type_proven':False,
   'source_text_exported':False}
 def p715_fixture_compiler():
  compiler=shutil.which('clang++') or shutil.which('g++') or shutil.which('c++')
  if not compiler:return {'status':'COMPILER_UNAVAILABLE',
    'not_original_v51_cpp':True,'precedence_compiler_proven':False}
  # Fixed original-free C++ fixture verifies !*entry->second parses as !( *(entry->second) ).
  code=r'''#include <cstdint>
 struct Entry { bool* second; };
 bool condition(Entry* iterator) { return !*iterator->second; }
 int main() {
   bool b=false; Entry e{&b};
   if (!condition(&e)) return 41;
   b=true;
   if (condition(&e)) return 42;
   return 0;
 }'''
  try:
   with tempfile.TemporaryDirectory(prefix='pre715-cpp-') as work:
    path=Path(work)/'fixture.cpp'
    output=Path(work)/'fixture.out'
    path.write_text(code,encoding='utf-8')
    cmd=[compiler,'-std=c++20','-Wall','-Wextra','-Werror','-O0',str(path),'-o',str(output)]
    built=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
    if built.returncode!=0:return {'status':'SYNTHETIC_COMPILE_FAILED',
      'compiler_family':'clang' if 'clang' in Path(compiler).name else 'gcc_or_other',
      'not_original_v51_cpp':True,'precedence_compiler_proven':False}
    ran=subprocess.run([str(output)],capture_output=True,text=True,timeout=15)
    ok=ran.returncode==0
    return {'status':'SYNTHETIC_CPP_COMPILE_RUN_PASS' if ok else 'SYNTHETIC_CPP_RUNTIME_FAILED',
      'compiler_family':'clang' if 'clang' in Path(compiler).name else 'gcc_or_other',
      'compiler_fixture_source_sha256':p715_hash(code),
      'condition_false_when_pointed_bool_true':ok,
      'condition_true_when_pointed_bool_false':ok,
      'precedence_compiler_proven':ok,
      'not_original_v51_cpp':True,'cpp_type_of_actual_source_proven':False}
  except (Exception) as error:
   return {'status':'COMPILER_FIXTURE_EXCEPTION',
     'exception_class':type(error).__name__,
     'not_original_v51_cpp':True,'precedence_compiler_proven':False}
 # Locate actual V51 declaration only; no synthetic substitution in authentic path.
 probes={}
 for label,lines,forline,guard in (
  ('device',device_lines,283,290),
  ('instance',instance_lines,445,454)):
  p=parse_bounded_parentheses(lines,guard,'if')
  if not p['extracted']:raise ValueError('PRE715_REAL_SECOND_IF_PARSE_FAILED')
  expected=report['pre714_negation_container']['files'][label]['negated_expression_structure']
  if p715_hash(p['text'].strip())!=expected['expr_sha256']:
   raise ValueError('PRE715_PRE714_GUARD_HASH_DRIFT')
  normalized=mask_cpp(p['text']).replace(' ','').replace('\t','')
  shape=bool(re.fullmatch(r'!\*[A-Za-z_]\w*->second',normalized))
  probes[label]={'guard_line':guard,
    'exact_pattern_bang_deref_iterator_member_second':shape,
    'expression_sha256':p715_hash(p['text'].strip()),
    'operator_precedence_supported_by_cpp_syntax':shape,
    'requested_extensions_declaration':p715_requested_declaration(lines,forline),
    'actual_cpp_operand_type':'NOT_VERIFIED','actual_cpp_runtime_result':'NOT_VERIFIED'}
 prior=report['pre714_negation_container']['files']['instance']
 target_sha=report['pre712_alias_guard_audit']['files']['instance']['second_guard_body_push_back']['calls'][0]['receiver_hash']
 probes['instance']['vector_declaration_line356']=p715_vector_declaration(instance_lines,356,target_sha)
 fixture=p715_fixture_compiler()
 report['pre715_type_precedence_audit']={
  'stage':'PRE715_V51_CPP_PRECEDENCE_AND_DECLARATION_AUDIT',
  'authenticated_source_sha_checked':True,
  'source_probe':probes,
  'synthetic_cpp_fixture':fixture,
  'synthetic_fixture_distinct_from_actual_source':True,
  'actual_source_ast_or_cfg_proven':False,
  'actual_source_cpp_type_proven':False,
  'runtime_enabled_extensions':'NOT_VERIFIED',
  'source_to_signed_apk_elf_equivalence':'UNVERIFIED',
  'vk_google_display_timing_enabled':'NOT_VERIFIED',
  'source_text_exported':False,'secrets_accessed':False,
  'apk_built':False,'apk_modified':False,'fps_gain_proven':False}
 report['analysis_type']='PRE715_AUTHENTICATED_V51_TYPE_DECLARATIONS_PLUS_SYNTHETIC_CPP_PRECEDENCE'
 report['status']=('PASS_PRE715_AUTHENTICATED_SOURCE_CPP_PRECEDENCE_SEPARATE_EVIDENCE'
  if all(probes[x]['exact_pattern_bang_deref_iterator_member_second'] for x in ('device','instance'))
     and probes['instance']['vector_declaration_line356']['declared_variable_matches_pushback_receiver']
     and probes['instance']['vector_declaration_line356']['status']=='SIMPLE_STD_VECTOR_DECLARATION_LEXICAL'
  else 'BLOCK_PRE715_SOURCE_DECLARATION_NOT_RESOLVED')
"""
def code(manifest,archive,run,attempt):
    src=pre714.code(manifest,archive,run,attempt)
    if src.count(PARENT_FINAL)!=1:raise ValueError('PRE715_PARENT_GATE_DRIFT')
    src=src.replace(PARENT_FINAL,PARENT_FINAL+'\n'+EXTRA)
    replacements=[
        ('NFSMW_PRE714_KAGGLE_REMOTE.json',MARKER),
        ('PRE714_V51_KAGGLE_NEGATION_CONTAINER_READONLY',
         'PRE715_V51_KAGGLE_TYPES_PRECEDENCE_READONLY'),
        ("print('PRE714_KAGGLE_GATE=","print('PRE715_KAGGLE_GATE="),
        ("print('PRE714_REPORT=","print('PRE715_REPORT="),
    ]
    for a,b in replacements:
        if a not in src:raise ValueError('PRE715_MISSING_PARENT_TOKEN '+a)
        src=src.replace(a,b)
    compile(src,'<PRE715 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    src=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre715.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    notebook={'nbformat':4,'nbformat_minor':5,
         'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
         'cells':[{'cell_type':'markdown','id':'pre715-purpose','metadata':{},
                  'source':['Authenticated V51 bounded C++ alias, condition callee and push_back lexical dataflow; no runtime Vulkan.']},
                  {'cell_type':'code','id':'pre715-readonly','metadata':{},
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
        assert MARKER in src and 'PRE715_AUTHENTICATED_V51_TYPE_DECLARATIONS_PLUS_SYNTHETIC_CPP_PRECEDENCE' in src
        assert 'PASS_PRE715_AUTHENTICATED_SOURCE_CPP_PRECEDENCE_SEPARATE_EVIDENCE' in src
        assert "'runtime_enabled_extensions':'NOT_VERIFIED'" in src
        assert 'GOOGLE_REFRESH_TOKEN' not in src and 'KAGGLE_API_TOKEN' not in src
        assert re.sub('[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.partition('/')[2]
        meta,note=build({},b'f','123','1')
        assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_internet']
        assert len(note['cells'])==2
        print('PRE715_SYNTHETIC=7_PASS')
        return
    if not all((a.manifest,a.archive,a.output,a.run_id)):
        p.error('missing required input')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
        p.error('numeric run IDs only')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),manifest.get('backend_sha256'))!=(
      'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE715_INVALID_AUTHENTICATED_V51_MANIFEST')
    byname={e['path']:e['sha256'] for e in manifest['entries']}
    if byname.get(pre706.DEVICE)!=pre706.DEVICE_SHA or byname.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE715_DEVICE_INSTANCE_HASH_MISMATCH')
    archive=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(byname):
       raise ValueError('PRE715_ARCHIVE_BAD')
    meta,notebook=build(manifest,archive,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre715.ipynb').write_text(json.dumps(notebook,indent=2)+'\n')
    print('PRE715_PRIVATE_KERNEL='+KERNEL)
    print('PRE715_V51_SOURCE_COUNT='+str(len(byname)))

if __name__=='__main__':
    main()
