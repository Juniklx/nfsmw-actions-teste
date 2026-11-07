#!/usr/bin/env python3
"""PRE334 synthetic-only qualification and fail-closed test."""
from pre334_pal_nitro_layout_qualification_readonly import qualify

sample = """
DEFINE_REX_FUNC(sub_82424AF0) {
REX_FUNC_PROLOGUE();
r31.u64 = ctx.r3.u64;
ctx.r3.u64 = REX_LOAD_U32(r31.u32 + 52);
temp.u32 = REX_LOAD_U32(r31.u32 + 252);
REX_STORE_U32(r31.u32 + 252, temp.u32);
ctx.r9.u64 = REX_LOAD_U32(r31.u32 + 296);
}
DEFINE_REX_FUNC(sub_825904F0) {
REX_FUNC_PROLOGUE();
r31.u64 = ctx.r3.u64;
temp.u32 = REX_LOAD_U32(r31.u32 + 252);
// write is missing, should fail
ctx.r9.u64 = REX_LOAD_U32(r31.u32 + 296);
}
"""
a=qualify(sample,"sub_82424AF0","r31")
b=qualify(sample,"sub_825904F0","r31")
assert a["base_from_r3_near_entry"]
assert a["load_252_count"]==1
assert a["store_252_count"]==1
assert a["load_296_count"]==1
assert a["shape_matches_nitro"]
assert b["store_252_count"]==0
assert not b["shape_matches_nitro"]
assert not a["owner_verified"]
print("PRE334_MOCK_STATUS AUDIT_OK")
print("PRE334_MOCK_ASSERTIONS 8")
