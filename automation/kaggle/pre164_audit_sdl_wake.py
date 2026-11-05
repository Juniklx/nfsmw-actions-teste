#!/usr/bin/env python3
"""PRE164: authenticated PRE99 SDL wake-source audit. Read-only."""
from __future__ import annotations
import hashlib,json,re,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FILES=[
"workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp",
"workspace/nativo/sdk/src/ui/windowed_app_context.cpp",
"workspace/nativo/sdk/src/ui/window_sdl.cpp",
"workspace/nativo/sdk/src/ui/rex_app.cpp",
"workspace/nativo/sdk/include/rex/ui/windowed_app_context_sdl.h",
"workspace/nativo/sdk/include/rex/ui/windowed_app_context.h",
"workspace/nativo/sdk/src/input/sdl/sdl_input_driver.cpp"]
EXPECTED_MAIN="f4ae379985adc2343fabde1e2eeebf048997482a8cfe17ef5839e69f8e66ffdc"
KEY=re.compile(r"NotifyUILoop|CallInUIThread|ExecutePendingFunctions|PendingFunctions|SDL_WaitEvent|SDL_Delay|SDL_PushEvent|SDL_PeepEvents|RunMainMessageLoop|ProcessEvent\(|wakeup_event_type_|condition_variable|push_attempted|push_success|SDL_EVENT_|pending_functions_",re.I)
def main():
 out=Path('/tmp/nfsmw-pre164-source-audit');out.mkdir(parents=True,exist_ok=True)
 rows=[]
 with tempfile.TemporaryDirectory(prefix='nfsmw_pre164_') as d:
  archive=Path(d)/'pre99.tar.gz'
  download(drive_client(),archive)
  sha,_,sz=sha_file(archive)
  if sha!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:raise ValueError('PRE99 integrity mismatch')
  with tarfile.open(archive,'r:gz') as tar:
   found=set()
   for member in tar:
    if member.name not in FILES:continue
    if member.name in found or not member.isfile() or member.size>1_000_000:raise ValueError('Unexpected/unsafe source entry')
    found.add(member.name);stream=tar.extractfile(member)
    if stream is None:raise ValueError('Unreadable source')
    data=stream.read();digest=hashlib.sha256(data).hexdigest()
    if member.name==FILES[0] and digest!=EXPECTED_MAIN:raise ValueError('SDL main source hash mismatch')
    lines=data.decode('utf-8').splitlines()
    matches=[i for i,line in enumerate(lines) if KEY.search(line)]
    interesting=set(range(0,min(len(lines),360))) if member.name==FILES[0] else set()
    if member.name!=FILES[0]:
     for i in matches:interesting.update(range(max(0,i-7),min(len(lines),i+12)))
    rows.append({'path':member.name,'sha256':digest,'size':len(data),'line_count':len(lines),
                 'matches':[i+1 for i in matches],
                 'excerpts':[{'line':i+1,'text':lines[i]} for i in sorted(interesting)[:480]]})
   if FILES[0] not in found:raise ValueError('SDL main source missing from PRE99')
 report={'stage':'PRE164_SDL_WAKE_SOURCE_AUDIT','verified_snapshot_sha256':EXPECTED_SHA256,
         'verified_snapshot_size':EXPECTED_BYTES,'source_modified':False,'apk_built':False,'files':rows}
 (out/'PRE164_SDL_WAKE_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('PRE164_SOURCE_VERIFIED',len(rows),'of',len(FILES))
 for row in rows:
  print('==== SOURCE',row['path'],'SHA256',row['sha256'],'====')
  for line in row['excerpts']:
   if row['path']!=FILES[0] or 65<=line['line']<=225:
    if row['path']==FILES[0] or line['line'] in row['matches'] or any(abs(line['line']-i)<=3 for i in row['matches']):
     print(f"{line['line']:03d}: {line['text']}")
if __name__=='__main__':main()
