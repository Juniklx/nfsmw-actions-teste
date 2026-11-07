#!/usr/bin/env python3
"""PRE332 synthetic-only structural regression; no Drive calls or game mutation."""
from pre332_nitro_pal_neighborhood_readonly import inspect
sample = """
DEFINE_REX_FUNC(sub_824249E0) {
REX_FUNC_PROLOGUE();
// mtctr r11
ctr.u64 = ctx.r11.u64;
// bctrl
ctx.lr = 0x82424A10;
REX_CALL_INDIRECT_FUNC(ctr.u32);
}
DEFINE_REX_FUNC(sub_82424AF0) {
REX_FUNC_PROLOGUE();
// mr r31,r3
r31.u64 = ctx.r3.u64;
// stfs f0,252(r31)
REX_STORE_U32(r31.u32 + 252, temp.u32);
}
DEFINE_REX_FUNC(sub_82424E58) {
REX_FUNC_PROLOGUE();
}
"""
r=inspect(sample)
assert r["nitro_present"]
assert r["methods_found"]==3
target=next(x for x in r["methods"] if x["symbol"]=="sub_82424AF0")
assert target["r3_mentions"]==1
assert target["offset_252_mentions"]==2
assert target["store_count"]==1
other=next(x for x in r["methods"] if x["symbol"]=="sub_824249E0")
assert other["indirect_dispatch_mentions"]>=1
assert next(x for x in r["methods"] if x["symbol"]=="sub_82424820")["present"] is False
print("PRE332_MOCK_STATUS AUDIT_OK")
print("PRE332_MOCK_ASSERTIONS 7")
