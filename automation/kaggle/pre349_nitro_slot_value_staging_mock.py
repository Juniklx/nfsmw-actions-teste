#!/usr/bin/env python3
from pre349_nitro_slot_value_staging import baseline,inject,reverse,MARKER
old=baseline()
new=inject(old)
assert new!=old
assert reverse(new)==old
assert new.count(MARKER)==1
assert "lookup_slot(guest_address)" in new
assert new.count("NFSMW_PRE336_NITRO_DIVERSITY")==1
assert new.count("NFSMW_PRE316_NITRO_CYCLE")==1
assert new.count("REX_STORE_U32(")==old.count("REX_STORE_U32(")
assert new.count("REX_LOAD_U32(")==old.count("REX_LOAD_U32(")
for source in [old.replace("NFSMW_PRE336_NITRO_DIVERSITY","INVALID"),new]:
    try:inject(source)
    except ValueError:pass
    else:raise AssertionError("PRE349 must reject non-baseline or repeated instrumentation")
print("PRE349_MOCK_STATUS AUDIT_OK")
print("PRE349_GUEST_LOAD_STORE_DELTA 0")
print("PRE349_OWNER_VERIFIED false")
