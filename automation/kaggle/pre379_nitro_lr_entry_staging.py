#!/usr/bin/env python3
"""PRE379: reversible Nitro entry ctx.lr/ctx.r3 *proposal*, not a deployed cheat.
Requires SHA-pinned PRE99 PAL shard; no APK or guest memory operations.
"""
from __future__ import annotations
import hashlib,re
from pathlib import Path
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS
SYMBOL="sub_82424AF0"
MARKER="NFSMW_PRE379_NITRO_ENTRY"
CALL='  NFSMW_PRE379_NITRO_ENTRY_TRACE(static_cast<unsigned int>(ctx.lr), ctx.r3.u32);\n'
PROTOTYPE='extern "C" void NFSMW_PRE379_NITRO_ENTRY_TRACE(unsigned int, unsigned int) noexcept;\n'
ANCHOR="  REX_FUNC_PROLOGUE();\n"
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def propose(original:str)->str:
    if MARKER in original or "NFSMW_PRE379_NITRO_ENTRY_TRACE" in original:
        raise ValueError("PRE379 was already applied")
    body=body_for_function(original,SYMBOL)
    # Match exact generated line while preserving its original indentation.
    anchors=list(re.finditer(r"(?m)^[ \\t]*REX_FUNC_PROLOGUE\\(\\);\\r?\\n",body))
    if len(anchors)!=1 or body.count("ctx.r12.u64 = ctx.lr;")!=1:
        raise ValueError("PRE379 expected one prologue and one mflr")
    m=anchors[0]
    if m.start()>body.index("ctx.r12.u64 = ctx.lr;"):
        raise ValueError("PRE379 prologue does not precede mflr")
    patched=body[:m.end()]+CALL+body[m.end():]
    # The runtime label is in a separate native C++ callback to be supplied in a later phase.
    if original.count(body)!=1:raise ValueError("Nonunique Nitro function")
    output=original.replace(body,patched,1)
    first=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9a-fA-F]{8}\)",output)
    if first is None:raise ValueError("No generated function declaration")
    output=output[:first.start()]+PROTOTYPE+output[first.start():]
    if output.count(CALL)!=1 or output.count(PROTOTYPE)!=1 or reverse(output)!=original:
        raise ValueError("PRE379 exact reversal failed")
    if output.count("REX_LOAD_U32(")!=original.count("REX_LOAD_U32("):
        raise ValueError("PRE379 extra guest load")
    if output.count("REX_STORE_U32(")!=original.count("REX_STORE_U32("):
        raise ValueError("PRE379 guest store modification")
    return output
def reverse(patched:str)->str:
    if patched.count(CALL)!=1 or patched.count(PROTOTYPE)!=1:
        raise ValueError("PRE379 marker mismatch on reversal")
    return patched.replace(CALL,"",1).replace(PROTOTYPE,"",1)
def verify_raw(original:bytes)->dict:
    spec=TARGETS["nitro"]
    if sha(original)!=spec["sha256"]:
        raise ValueError("PRE379 input PAL Nitro shard SHA mismatch")
    src=original.decode("utf-8")
    staged=propose(src)
    return {"status":"STAGED_IN_MEMORY_REVERSIBLE","original_sha256":sha(original),
      "proposed_sha256":sha(staged.encode()),"source_file":spec["file"],
      "reverse_exact":True,"extra_guest_loads":0,"guest_stores_rewritten":0,
      "owner_verified":False,"cheat_enabled":False,"apk_built":False,
      "runtime_callback_compiled":False,
      "limitation":"Records incoming PowerPC LR and r3 as callsite/object hypotheses; no owner identity proved."}
