#!/usr/bin/env python3
"""PRE169: fetch *authenticated PRE99* three input/UI source files for private optimization review. No code changes."""
from __future__ import annotations
import hashlib,json,tarfile,tempfile,zipfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

SOURCES={
 "workspace/nativo/sdk/src/input/sdl/sdl_input_driver.cpp":"be93c7ae7297489d369abff7c86becf29373c127fa7e6dbbc802dd7a09452728",
 "workspace/nativo/sdk/include/rex/input/sdl/sdl_input_driver.h":None,
 "workspace/nativo/sdk/src/ui/windowed_app_context.cpp":"5fcc1b8bccf18082f323ccc6d55a98419b5a5bb34618dd2d36516f0bc8d15a10",
 "workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp":"f4ae379985adc2343fabde1e2eeebf048997482a8cfe17ef5839e69f8e66ffdc",
 "workspace/nativo/sdk/include/rex/ui/windowed_app_context.h":"191793f542abd19c822a9037988fafc56dc3b1edcaedf67eeb21445ef844faf9",
}
def main():
 out=Path('/tmp/nfsmw-pre169-input-audit');out.mkdir(parents=True,exist_ok=True)
 details=[]
 with tempfile.TemporaryDirectory(prefix='nfsmw_pre169_') as d:
  archive=Path(d)/'PRE99.tar.gz'
  download(drive_client(),archive)
  sha,_,sz=sha_file(archive)
  if sha!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES: raise RuntimeError('PRE99 snapshot SHA / size mismatch')
  with tarfile.open(archive,'r:gz') as tf,zipfile.ZipFile(out/'PRE169_PRE99_SOURCE_REVIEW.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
   found=set()
   for m in tf:
    if m.name not in SOURCES:continue
    if m.name in found or not m.isfile() or m.size>1500000:raise RuntimeError('Invalid/duplicated source entry')
    f=tf.extractfile(m)
    if f is None:raise RuntimeError('Missing bytes')
    raw=f.read(); h=hashlib.sha256(raw).hexdigest()
    if SOURCES[m.name] is not None and SOURCES[m.name]!=h:raise RuntimeError('PRE99 source hash mismatch: '+m.name)
    z.writestr(m.name.removeprefix('workspace/'),raw)
    details.append({'name':m.name,'sha256':h,'bytes':len(raw)})
    found.add(m.name)
   required={name for name,hash_ in SOURCES.items() if hash_ is not None}
   if not required.issubset(found):raise RuntimeError('Missing required verified files '+repr(required-found))
   z.writestr('PRE169_REPORT.json',json.dumps({'stage':'PRE169','verified_source_sha256':sha,'source_modified':False,'files':details},indent=2))
 print('PRE169_SOURCE_AUTHENTICATED',len(details),'of',len(SOURCES))
 for f in details: print('SOURCE',f['name'],'SHA256',f['sha256'],'bytes',f['bytes'])
if __name__=='__main__':main()
