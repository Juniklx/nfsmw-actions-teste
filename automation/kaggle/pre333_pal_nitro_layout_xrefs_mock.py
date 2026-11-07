#!/usr/bin/env python3
"""PRE333 synthetic-only shared field-offset candidate regression."""
from pre333_pal_nitro_layout_xrefs_readonly import candidates
sample = """
DEFINE_REX_FUNC(sub_82424AF0) {
REX_FUNC_PROLOGUE();
r31.u64 = ctx.r3.u64;
// comment with r31.u32 + 52 must be ignored
ctx.r6.u64 = REX_LOAD_U32(r31.u32 + 52);
ctx.r6.u64 = REX_LOAD_U32(r31.u32 + 72);
r29.s64 = r31.s64 + 88;
REX_STORE_U32(r31.u32 + 252, temp.u32);
ctx.r9.u64 = REX_LOAD_U32(r31.u32 + 296);
}
DEFINE_REX_FUNC(sub_82424E58) {
REX_FUNC_PROLOGUE();
ctx.r8.u64 = REX_LOAD_U32(ctx.r3.u32 + 52);
ctx.r9.u64 = REX_LOAD_U32(ctx.r3.u32 + 72);
}
DEFINE_REX_FUNC(sub_82425078) {
REX_FUNC_PROLOGUE();
ctx.r8.u64 = REX_LOAD_U32(ctx.r3.u32 + 252);
ctx.r9.u64 = REX_LOAD_U32(ctx.r3.u32 + 296);
}
"""
a=candidates(sample,"synthetic.cpp")
assert len(a)==2,a
target=next(x for x in a if x["function"]=="sub_82424AF0")
assert target["offsets"]==[52,72,88,252,296],target
assert target["register_base"]=="r31",target
assert target["score"]==5
assert target["has_nitro_field"] is True
other=next(x for x in a if x["function"]=="sub_82425078")
assert other["offsets"]==[252,296]
assert not any(x["function"]=="sub_82424E58" for x in a)
print("PRE333_MOCK_STATUS AUDIT_OK")
print("PRE333_MOCK_ASSERTIONS 7")
