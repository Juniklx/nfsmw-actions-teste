#!/usr/bin/env python3
from pre364_xinput_user0_passive_staging import START,END,OLD,MARKER,inject,reverse
SRC='''#include <cstdint>
namespace rex {
X_RESULT InputSystem::GetState(uint32_t user_index, X_INPUT_STATE* out_state) {
  auto* driver = nullptr;
  driver->GetDeviceState(0, &state);
  X_INPUT_STATE merged = {};
''' + OLD + '''
X_RESULT InputSystem::SetState(uint32_t user_index, X_INPUT_VIBRATION* vibration) { return 0; }
}'''
patched=inject(SRC)
assert MARKER in patched
assert reverse(patched)==SRC
assert patched.count("GetDeviceState(")==SRC.count("GetDeviceState(")
assert patched.count("*out_state = merged;")==1
assert "user_index == 0u" in patched
assert "seq <= 256u" in patched
assert "lt >= 32u" in patched and "rt >= 32u" in patched
for bad in (patched, SRC.replace("GetDeviceState(","OtherDeviceState("), SRC.replace("*out_state = merged;","*out_state = unexpected;")):
    try:inject(bad)
    except ValueError:pass
    else:raise AssertionError("PRE364 fail-closed expected")
print("PRE364_MOCK_STATUS AUDIT_OK")
print("PRE364_OWNER_VERIFIED false")
