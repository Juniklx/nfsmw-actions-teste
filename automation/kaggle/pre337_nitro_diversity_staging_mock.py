#!/usr/bin/env python3
"""PRE337 mock: PRE317 -> PRE337 reversible staging with zero guest access delta."""
from pre247_pal_meter_passive_probe_patch import CPP_TEXT
from pre317_nitro_cycle_staging import inject as inject_pre317
from pre337_nitro_diversity_staging import inject, reverse

base=inject_pre317(CPP_TEXT)
changed=inject(base)
assert changed!=base
assert reverse(changed)==base
assert changed.count('NFSMW_PRE336_NITRO_DIVERSITY')==1
assert changed.count('NFSMW_PRE316_NITRO_CYCLE')==1
assert changed.count('NFSMW_PRE247_CHEATS_DIAG')==1
assert changed.count('REX_LOAD_U32(')==base.count('REX_LOAD_U32(')
assert changed.count('REX_STORE_U32(')==base.count('REX_STORE_U32(')
assert 'observe(site, guest_address, snapshot)' in changed
assert changed.index('NFSMW_PRE336_NITRO_DIVERSITY')<changed.index('if (seen >= 12u) return;')
try:
    inject(changed)
except ValueError:
    pass
else:
    raise AssertionError('PRE337 reapplication must fail')
try:
    inject(CPP_TEXT)
except ValueError:
    pass
else:
    raise AssertionError('PRE337 cannot skip PRE317')
print("PRE337_MOCK_STATUS AUDIT_OK")
print("PRE337_MOCK_ASSERTIONS 11")
