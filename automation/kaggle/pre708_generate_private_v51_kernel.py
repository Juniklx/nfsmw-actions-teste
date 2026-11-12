#!/usr/bin/env python3
"""PRE708 — source-only, bounded condition & insertion argument syntax.
Authenticated V51 sources, private isolated Kaggle, no APK, patch or Vulkan runtime.
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
import pre707_generate_private_v51_kernel as pre707

KERNEL="juniklx/nfsmw-pre708-v51-condition-syntax-readonly"
TITLE="NFSMW PRE708 V51 Condition Syntax Readonly"
MARKER="NFSMW_PRE708_KAGGLE_REMOTE.json"
ANCHOR=" report['analysis_type']='PRE707_LEXICAL_INSERTION_AND_NEARBY_CONTROL_INDICATORS'"
INJECT=r"""
 # PRE708 — balanced argument parsing for authenticated V51 source lines. No C++ AST.
 def parse_bounded_parentheses(lines,line,keyword,max_lines=10):
  if line<1 or line>len(lines):
   return {'extracted':False,'reason':'OUTSIDE_FILE'}
  fragment='\n'.join(lines[line-1:min(len(lines),line+max_lines-1)])
  m=re.search(r'\b'+re.escape(keyword)+r'\s*\(',fragment)
  if not m:return {'extracted':False,'reason':'KEYWORD_NOT_FOUND'}
  start=m.end()
  depth=1
  quoted=None
  esc=False
  single_comment=False
  multi_comment=False
  out=[]
  i=start
  while i<len(fragment):
   ch=fragment[i]
   nxt=fragment[i+1] if i+1<len(fragment) else ''
   if single_comment:
    if ch=='\n':single_comment=False
    i+=1
    continue
   if multi_comment:
    if ch=='*' and nxt=='/':multi_comment=False;i+=2;continue
    i+=1;continue
   if quoted:
    out.append(ch)
    if esc:esc=False
    elif ch=='\\':esc=True
    elif ch==quoted:quoted=None
    i+=1;continue
   if ch=='/' and nxt=='/':single_comment=True;i+=2;continue
   if ch=='/' and nxt=='*':multi_comment=True;i+=2;continue
   if ch=='"' or ch=="'":quoted=ch;out.append(ch);i+=1;continue
   if ch=='(':depth+=1
   if ch==')':
    depth-=1
    if depth==0:
     return {'extracted':True,'text':''.join(out),'span_max_lines':max_lines}
   out.append(ch)
   i+=1
  return {'extracted':False,'reason':'UNBALANCED_OR_OUT_OF_BOUND'}
 def expr_summary(fragment,line,kind,parsed):
  if not parsed['extracted']:
   return {'line':line,'kind':kind,'extracted':False,
           'failure_reason':parsed['reason']}
  raw=parsed['text']
  # Output only recognized syntactic indicators and hashes, not raw source.
  expr=raw.strip()
  ops=sorted(set(re.findall(r'==|!=|<=|>=|&&|\|\||(?<![<>=!])<(?![<=])|(?<![<>=!])>(?![>=])',expr)))
  words=set(re.findall(r'\b[A-Za-z_]\w*\b',expr))
  allowed={
    'extensionName','extension','extensions','enabled_extensions',
    'requested_extensions','available_extensions','required_extensions',
    'optional_extensions','supported_extensions','device_extensions',
    'instance_extensions','strcmp','strncmp','find','contains','begin','end',
    'c_str','name','VkExtensionProperties','std','extension_properties',
    'extensionProperties','property','properties','extension_name'
  }
  literals=sorted(set(re.findall(r'\bVK_[A-Za-z0-9_]+\b',expr)))[:30]
  shape=('EMPTY' if not expr else
         'STRING_LITERAL' if expr.startswith('"') else
         'CALL_OR_CAST' if bool(re.search(r'\b[A-Za-z_]\w*\s*\(',expr)) else
         'MEMBER_ACCESS' if '.' in expr or '->' in expr else
         'IDENTIFIER_OR_COMPLEX')
  return {
   'line':line,'kind':kind,'extracted':True,
   'expr_sha256':hashlib.sha256(expr.encode('utf-8')).hexdigest(),
   'bytes':len(expr.encode('utf-8')),
   'syntax_shape':shape,'comparison_operators':ops,
   'recognized_identifier_tokens':sorted(words & allowed),
   'vulkan_macro_tokens':literals,
   'calls_strcmp':bool(re.search(r'\b(?:std::)?strcmp\s*\(',expr)),
   'calls_find':bool(re.search(r'\bfind\s*\(',expr)),
   'uses_extensionName':bool(re.search(r'\bextensionName\b',expr)),
   'uses_enabled_extensions':bool(re.search(r'\benabled_extensions\b',expr)),
   'member_access_count':len(re.findall(r'\.|->',expr)),
   'paren_pairs':expr.count('('),
   'starts_with_negation':expr.startswith('!'),
  }
 checks={
  'device':(device_lines,[286,290],291),
  'instance':(instance_lines,[448,454],455)
 }
 output={}
 for group,(lines,checks_lines,add_line) in checks.items():
  conditions=[]
  for line in checks_lines:
   parsed=parse_bounded_parentheses(lines,line,'if')
   conditions.append(expr_summary(lines,line,'if',parsed))
  inserted=expr_summary(lines,add_line,'emplace_back',
                        parse_bounded_parentheses(lines,add_line,'emplace_back'))
  parent=report['pre707_selection']['sites'][group]['insert']
  if not parent['container_insert_found']:
   raise ValueError('PRE708_PARENT_INSERT_NOT_AUTHENTICATED')
  output[group]={
    'conditions':conditions,
    'insert':inserted,
    'insert_container':'enabled_extensions',
    'insert_method':'emplace_back',
    'insertion_line':add_line,
    'syntax_scope':'EXACT_BOUNDED_PARENTHESIS_EXTRACTION_NOT_CPP_AST',
    'guard_nesting_proven':False,
    'requested_vs_advertised_semantics_proven':False,
    'runtime_extension_list':'NOT_VERIFIED'
  }
 audit_ok=all(c['extracted'] for group in output.values()
              for c in group['conditions']) and all(group['insert']['extracted']
              for group in output.values())
 report['pre708_conditions']={
  'stage':'PRE708_V51_CONDITION_ARGUMENT_SYNTAX',
  'files':output,
  'bounded_expressions_extracted':audit_ok,
  'source_hashes_verified':report['pre707_selection']['source_hashes_verified'],
  'string_literals_exported':False,
  'full_source_exported':False,
  'cpp_ast_proven':False,'guard_nesting_proven':False,
  'device_extensions_requested':'NOT_VERIFIED',
  'driver_extensions_advertised':'PRE702_USER_REPORT',
  'device_enabled_extension_names':'NOT_VERIFIED',
  'rendering_changed':False,
  'fps_gain_proven':False,
 }
 report['analysis_type']='PRE708_BOUNDED_CONDITION_ARGUMENT_SYNTAX_ONLY_NOT_RUNTIME'
 report['status']=('PASS_AUTHENTICATED_V51_CONDITION_ARGUMENT_SYNTAX_ONLY'
    if audit_ok and report['pre708_conditions']['source_hashes_verified']
    else 'BLOCK_CONDITIONS_OR_ARGUMENTS_UNRESOLVED')
"""
def code(manifest,archive,run,attempt):
    src=pre707.code(manifest,archive,run,attempt)
    if src.count(ANCHOR)!=1:raise ValueError("PRE708_PARENT_TEMPLATE_DRIFT")
    src=src.replace(ANCHOR,INJECT)
    for a,b in [
        ("NFSMW_PRE707_KAGGLE_REMOTE.json",MARKER),
        ("PRE707_V51_KAGGLE_DEVICE_EXTENSION_SELECTION_SITES_READONLY",
         "PRE708_V51_KAGGLE_CONDITION_ARGUMENT_SYNTAX_READONLY"),
        ("print('PRE707_KAGGLE_GATE=","print('PRE708_KAGGLE_GATE="),
        ("print('PRE707_REPORT=","print('PRE708_REPORT=")
    ]:
        if a not in src:raise ValueError("PRE708_RENAME_MARKER_DRIFT "+a)
        src=src.replace(a,b)
    compile(src,'<PRE708 private Kaggle notebook>','exec')
    return src

def build(manifest,archive,run,attempt):
    body=code(manifest,archive,run,attempt)
    meta={'id':KERNEL,'title':TITLE,'code_file':'pre708.ipynb','language':'python',
          'kernel_type':'notebook','is_private':True,'enable_gpu':False,
          'enable_internet':False,'dataset_sources':[],'competition_sources':[],
          'kernel_sources':[],'model_sources':[]}
    note={'nbformat':4,'nbformat_minor':5,
          'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},
          'cells':[{'cell_type':'markdown','id':'pre708-note','metadata':{},
                    'source':['NFSMW PRE708: read-only bounded condition arguments from authenticated V51.']},
                   {'cell_type':'code','id':'pre708-code','metadata':{},
                    'source':body.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
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
      body=code({'stage':'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE'},b'fake','123','1')
      assert "PRE708_V51_CONDITION_ARGUMENT_SYNTAX" in body
      assert "PASS_AUTHENTICATED_V51_CONDITION_ARGUMENT_SYNTAX_ONLY" in body
      assert "EXACT_BOUNDED_PARENTHESIS_EXTRACTION_NOT_CPP_AST" in body
      assert "guard_nesting_proven':False" in body
      assert all(x not in body for x in ('GOOGLE_REFRESH_TOKEN','KAGGLE_API_TOKEN','NFSMW_ASSINATURA_PERMANENTE'))
      assert re.sub(r'[^a-z0-9]+','-',TITLE.lower()).strip('-')==KERNEL.split('/')[1]
      meta,note=build({},b'no-archive','123','1')
      assert len(note['cells'])==2 and meta['is_private']
      assert not meta['enable_gpu'] and not meta['enable_internet']
      print('PRE708_GENERATOR_SYNTHETIC=8_PASS')
      return
    if not all((a.manifest,a.archive,a.output,a.run_id)):p.error('required inputs missing')
    if not re.fullmatch(r'[0-9]+',a.run_id) or not re.fullmatch(r'[0-9]+',a.attempt):
      p.error('run identifiers must be numeric')
    manifest=json.loads(a.manifest.read_text())
    if (manifest.get('stage'),manifest.get('pre99_sha256'),manifest.get('presenter_sha256'),
        manifest.get('backend_sha256'))!=(
        'PRE704_AUTHENTICATED_V51_UI_SOURCE_BUNDLE',
        pre704.PRE99,pre704.PRESENTER,pre704.BACKEND):
      raise ValueError('PRE708_UNAUTHENTICATED_V51_MANIFEST')
    entries={x['path']:x['sha256'] for x in manifest['entries']}
    if entries.get(pre706.DEVICE)!=pre706.DEVICE_SHA or entries.get(pre706.INSTANCE)!=pre706.INSTANCE_SHA:
      raise ValueError('PRE708_DEVICE_INSTANCE_HASH_MISMATCH')
    data=a.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
      if z.testzip() is not None or set(z.namelist())!=set(entries):
        raise ValueError('PRE708_SOURCE_ARCHIVE_MISMATCH')
    meta,note=build(manifest,data,a.run_id,a.attempt)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (a.output/'pre708.ipynb').write_text(json.dumps(note,indent=2)+'\n')
    print('PRE708_PRIVATE_KERNEL='+KERNEL)
    print('PRE708_FILE_COUNT='+str(len(entries)))
if __name__=='__main__':main()
