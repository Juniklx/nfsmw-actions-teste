#!/usr/bin/env python3
"""PRE325B: offline unit checks for PRE325 search predicates. No Drive, game, APK or secrets."""
import re
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec

SRC=Path(__file__).with_name("pre325_nitro_dispatch_extended_readonly.py")
# Parse only the source AST: do not import the audit (which imports Drive dependencies).
import ast
tree=ast.parse(SRC.read_text(encoding="utf-8"))
assign=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PATTERNS" for t in x.targets))
patterns={}
for el in assign.value.elts:
    tag=ast.literal_eval(el.elts[0])
    call=el.elts[1]
    assert isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr=="compile"
    pattern=ast.literal_eval(call.args[0])
    patterns[tag]=re.compile(pattern,re.I if len(call.args)>1 else 0)
assert int("82424AF0",16)==2185382640
cases=[
 ("DEFINE_REX_FUNC(sub_82424AF0)",{"symbol","hex_address"}),
 ("r12.u64 = 0x82424AF0;",{"hex_address"}),
 ("target = 2185382640;",{"decimal_address"}),
 ("sub_82424AF01",set()),
 ("0x182424AF0",set()),
 ("21853826401",set()),
 ("unrelated()",set()),
]
for line,expected in cases:
    got={name for name,rx in patterns.items() if rx.search(line)}
    assert got==expected,(line,got,expected)
print("PRE325B_STATUS AUDIT_OK")
print("PRE325B_CASES",len(cases))
print("PRE325B_SCOPE offline matcher only; no runtime owner proof")
