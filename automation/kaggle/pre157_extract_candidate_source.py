#!/usr/bin/env python3
"""PRE157: verify PRE99 and extract exact Vulkan candidate files (read-only)."""
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

TARGETS = {
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp": "68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48",
 "workspace/nativo/sdk/src/ui/presenter.cpp": "e4db870dbeae984f9ef28957dafff6c4758471780fe1ac108b5501ebd341c208",
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_submission_tracker.cpp": "ae776d6e76d324c035b1c1c6e9083d4fdf94b7bb53a329f82f58650399b9a478",
 "workspace/nativo/app/src/nfsmw_nativo_destinos.cpp": "b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385",
}
OUT = Path("/tmp/nfsmw_pre157_verified_source")
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="nfsmw_pre157_") as tmp:
 archive=Path(tmp)/"pre99.tar.gz"
 download(drive_client(), archive)
 digest,_,size=sha_file(archive)
 if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 checksum failed")
 verified=[]
 seen=set()
 with tarfile.open(archive,"r:gz") as tar:
  for member in tar:
   if member.name not in TARGETS:continue
   if member.name in seen or not member.isfile() or member.size>2_000_000:
    raise ValueError("Unsafe or duplicate member")
   seen.add(member.name)
   stream=tar.extractfile(member)
   if stream is None:raise ValueError("Source unreadable")
   blob=stream.read()
   sha=hashlib.sha256(blob).hexdigest()
   if sha!=TARGETS[member.name]:raise ValueError("Source hash failed")
   target=OUT/member.name.replace("workspace/","",1)
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(blob)
   verified.append({"path":member.name,"sha256":sha,"size":len(blob)})
 if seen!=set(TARGETS):raise ValueError("Target missing")
 (OUT/"PRE157_MANIFEST.json").write_text(json.dumps({"stage":"PRE157","verified":True,"snapshot_sha256":digest,"files":verified,"readonly":True,"apk_built":False},indent=2)+"\n")
 print("PRE157 verified sources:",len(verified))
