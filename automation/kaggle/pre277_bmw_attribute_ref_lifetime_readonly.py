#!/usr/bin/env python3
"""PRE277: authenticated PAL reference-lifetime helper audit (read only).

Extends PRE276 to sub_821485E8/sub_8214E928 and locates side-effect
patterns: guest writes, +18 U16 updates, direct callees, branches.
All findings are static; do not claim balanced reference counts.
No guest calls, no game patch/build, no user save or signing access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre277/PRE277_BMW_ATTRIBUTE_REF_LIFETIME_HELPERS.json")
ROOT="workspace/nativo/app/generated/default/"
TARGETS=("sub_821485E8","sub_8214E928")
PARENTS=("sub_82148718","sub_8214E9E0")
MAX_SOURCE_BYTES=7_000_000
STORE=re.compile(r"\bREX_STORE_U(8|16|32|64)\(\s*([^,]+?)\s*,")
LOAD=re.compile(r"\bREX_LOAD_U(?:8|16|32|64)\(")
CALL=re.compile(r"(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\);")
GUEST_OPCODE=re.compile(r"^\s*//\s*(?:lhz|lha|sth|stw|lwz|addi|addis|subf|subfic|mtctr|bl|bne|beq|bge|ble|bctrl|blr)\b")
U16_PLUS18=re.compile(r"\+\s*18\b")

def around(lines,i,pre=9,post=8):
    return [{"relative_line":j+1,"code":lines[j].strip()[:185]}
            for j in range(max(0,i-pre),min(len(lines),i+post+1))]

def inspect(source,fn,path,digest):
    body=body_for_function(source,fn)
    lines=body.splitlines()
    if len(lines)>30000:raise ValueError("Unexpectedly huge guest function")
    writes=[]
    calls=[]
    ops=[]
    for i,line in enumerate(lines):
        w=STORE.search(line)
        if w:
            addr=w.group(2).strip()
            is_stack=addr.startswith("ctx.r1.")
            writes.append({
                "line":i+1,"width_bits":int(w.group(1)),
                "address":addr[:150],
                "scope":"DIRECT_STACK" if is_stack else "NONSTACK_OR_UNRESOLVED",
                "u16_plus18":int(w.group(1))==16 and U16_PLUS18.search(addr)!=None,
                "preceding_guest_ops":[v.strip()[:145] for v in lines[max(0,i-15):i]
                    if GUEST_OPCODE.search(v)][-11:],
                "code_context":around(lines,i,5,4)
            })
        m=CALL.search(line)
        if m:
            calls.append({
              "line":i+1,"callee":m.group(1),
              "preceding_guest_ops":[v.strip()[:160] for v in lines[max(0,i-10):i]
                   if v.strip().startswith("//")][-7:]
            })
        if line.lstrip().startswith("//") and GUEST_OPCODE.search(line):
            if len(ops)<100:ops.append({"line":i+1,"opcode":line.strip()[:155]})
    plus18=[w for w in writes if w["u16_plus18"]]
    return {
      "function":fn,"file":path,"sha256":digest,
      "lines":len(lines),"guest_loads":len(LOAD.findall(body)),
      "guest_stores":len(writes),"guest_stores_by_width":dict(Counter(w["width_bits"] for w in writes)),
      "nonstack_or_unresolved_stores":sum(w["scope"]!="DIRECT_STACK" for w in writes),
      "u16_plus18_stores":len(plus18),"u16_plus18_context":plus18[:20],
      "all_store_context":writes[:85],"direct_calls":calls[:80],
      "direct_callee_names":sorted(set(c["callee"] for c in calls)),
      "interesting_guest_ops":ops[:90],
      "body_excerpt":body[:24000],
      "body_excerpt_truncated":len(body)>24000,
      "proven_pure":False
    }

def audit():
  with tempfile.TemporaryDirectory(prefix="pre277_") as dir_name:
    arch=Path(dir_name)/"pre99.tar.gz"
    download(drive_client(),arch)
    digest,_,size=sha_file(arch)
    if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
        raise ValueError("Authenticated PRE99 fingerprint mismatch")
    found={}
    files_scanned=0
    with tarfile.open(arch,"r:gz",errorlevel=2) as tar:
      for member in tar:
        path=member.name.lstrip("./")
        if not member.isfile() or not path.startswith(ROOT) or not path.endswith(".cpp"):
            continue
        if member.size>MAX_SOURCE_BYTES:raise ValueError("Oversized generated C++ shard")
        f=tar.extractfile(member)
        if f is None:raise ValueError("Missing source member")
        raw=f.read()
        if len(raw)!=member.size:raise ValueError("Short source member")
        files_scanned+=1
        present=[fn for fn in TARGETS+PARENTS
          if ("DEFINE_REX_FUNC("+fn+")").encode() in raw]
        if not present:continue
        source=raw.decode("utf-8","replace")
        sha=hashlib.sha256(raw).hexdigest()
        for fn in present:
          if fn in found:raise ValueError("Duplicate guest function "+fn)
          found[fn]=inspect(source,fn,path,sha)
    if files_scanned<120 or set(found)!=set(TARGETS+PARENTS):
        raise ValueError("Missing guest function or PAL shard")
    parent=found["sub_82148718"]
    deps=parent["direct_callee_names"]
    if not all(fn in deps for fn in TARGETS):
        raise ValueError("PRE276 callee chain no longer matches authenticated source")
    runtime_safe=False
    result={
      "stage":"PRE277_BMW_ATTRIBUTE_REFERENCE_LIFETIME_PAL_READONLY",
      "status":"AUDIT_OK",
      "authenticated_pre99_sha256":digest,
      "pal_cpp_shards_scanned":files_scanned,
      "function_reports":found,
      "next_depth_call_graph":{
        fn:r["direct_callee_names"] for fn,r in found.items()
      },
      "two_new_helpers_summary":{
        fn:{"guest_stores":found[fn]["guest_stores"],
            "u16_plus18":found[fn]["u16_plus18_stores"],
            "unknown_or_nonstack_guest_stores":found[fn]["nonstack_or_unresolved_stores"],
            "direct_callees":found[fn]["direct_callee_names"]}
        for fn in TARGETS},
      "reference_balance_proven":False,
      "safe_to_invoke_getmaxlevel_seven_extra_times":runtime_safe,
      "actual_bmw_upgrade_limits_observed":False,
      "decision":"PRESERVE_ORIGINAL_GUEST_CALLS_ONLY",
      "limitations":[
        "Instruction context may suggest refcount increment/decrement but neither object identity nor net balance is proven",
        "A zero direct-store function may still have effects in non-PPC helper calls",
        "No PAL runtime values or BMW-specific game attributes loaded on a device",
        "Read-only PRE99 generated code, not a V37 execution trace",
        "No source modifications, APK builds, save edits, signing or additional game calls"
      ],
      "source_modified":False,"apk_built":False,"save_modified":False,"signer_accessed":False
    }
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Run id must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE277_BMW_ATTRIBUTE_REFERENCE_LIFETIME_PAL_READONLY",
            "status":"FAILED","apk_built":False,"source_modified":False}
    try:result=audit()
    except Exception as e:
        result["error_type"]=type(e).__name__
        result["phase"]="AUTHENTICATED_SOURCE_FUNCTION_SCAN"
    result["github_run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE277_STATUS",result["status"])
    print("PRE277_NEW_HELPERS",result.get("two_new_helpers_summary"))
    print("PRE277_REFERENCE_BALANCED",result.get("reference_balance_proven"))
    print("PRE277_EXTRA_CALLS_SAFE",result.get("safe_to_invoke_getmaxlevel_seven_extra_times"))
    if result["status"]!="AUDIT_OK":print("PRE277_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
