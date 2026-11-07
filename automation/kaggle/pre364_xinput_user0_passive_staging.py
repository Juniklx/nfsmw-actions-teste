#!/usr/bin/env python3
"""PRE364: reversible read-only XInput user0 button transitions on host-side merged state.
No guest memory reads/stores, no Nitro values changed, no player owner claims.
Only authorized on exact authenticated PRE99 input_system.cpp source digest.
"""
from pathlib import Path
import hashlib,re
SOURCE="nativo/sdk/src/input/input_system.cpp"
PRE99_SHA="ee84079f668806af48f3a739d53213523c77c55ed202eebe8c3110c474c7432a"
START="X_RESULT InputSystem::GetState(uint32_t user_index, X_INPUT_STATE* out_state) {"
END="X_RESULT InputSystem::SetState(uint32_t user_index, X_INPUT_VIBRATION* vibration) {"
OLD="""  if (out_state) {
    *out_state = merged;
  }
  return X_ERROR_SUCCESS;
}"""
MARKER="NFSMW_PRE364_XINPUT_USER0"
NEW="""  if (out_state) {
    // PRE364: sample native merged XInput; do not dereference guest pointers.
    if (user_index == 0u) {
      const std::uint32_t buttons = static_cast<std::uint16_t>(merged.gamepad.buttons);
      const std::uint32_t lt = merged.gamepad.left_trigger;
      const std::uint32_t rt = merged.gamepad.right_trigger;
      const std::uint32_t digital = buttons |
          ((lt >= 32u ? 1u : 0u) << 16) |
          ((rt >= 32u ? 1u : 0u) << 17);
      static std::atomic<std::uint32_t> last_digital{0xFFFFFFFFu};
      static std::atomic<std::uint32_t> changes{0u};
      const std::uint32_t previous =
          last_digital.exchange(digital, std::memory_order_relaxed);
      if (previous != digital) {
        const std::uint32_t seq = changes.fetch_add(1u, std::memory_order_relaxed) + 1u;
        if (seq <= 256u) {
          REXLOG_INFO("[NFSMW_PRE364_XINPUT_USER0] seq={} buttons=0x{:04X} lt={} rt={} digital=0x{:08X}",
                      seq, buttons, lt, rt, digital);
        }
      }
    }
    *out_state = merged;
  }
  return X_ERROR_SUCCESS;
}"""
INCLUDES="#include <atomic>\n#include <cstdint>\n#include <rex/logging/macros.h>\n"
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def inject(src:str)->str:
    if src.count(START)!=1 or src.count(END)!=1 or MARKER in src:
        raise ValueError("PRE364 source entry ambiguous/already staged")
    a=src.index(START);b=src.index(END,a)
    body=src[a:b]
    if body.count(OLD)!=1:raise ValueError("PRE364 native assignment anchor mismatch")
    if body.count("GetDeviceState(")!=1:raise ValueError("PRE364 host source shape mismatch")
    patched_body=body.replace(OLD,NEW,1)
    out=src[:a]+patched_body+src[b:]
    first=re.search(r"(?m)^#include [^\n]+\n",out)
    if first is None:raise ValueError("PRE364 missing C++ include section")
    out=out[:first.start()]+INCLUDES+out[first.start():]
    if out.count(MARKER)!=1 or reverse(out)!=src:raise ValueError("PRE364 reversal failed")
    if out.count("REX_STORE_U32(")!=src.count("REX_STORE_U32(") or out.count("REX_LOAD_U32(")!=src.count("REX_LOAD_U32("):
        raise ValueError("PRE364 guest operation delta")
    return out
def reverse(src:str)->str:
    if src.count(NEW)!=1 or src.count(INCLUDES)!=1:
        raise ValueError("PRE364 missing injection for reverse")
    return src.replace(NEW,OLD,1).replace(INCLUDES,"",1)
def apply(root:Path)->dict:
    src=Path(root)/SOURCE
    if not src.is_file():raise ValueError("PRE364 original host input source absent")
    before=src.read_bytes()
    if sha(before)!=PRE99_SHA:raise ValueError("PRE364 input source SHA differs from PRE99")
    text=before.decode("utf-8")
    output=inject(text)
    original=src.with_suffix(src.suffix+".pre364_original")
    if original.exists():raise ValueError("PRE364 prior backup exists")
    original.write_bytes(before)
    src.write_text(output,encoding="utf-8")
    if src.read_text(encoding="utf-8")!=output or original.read_bytes()!=before:
        raise ValueError("PRE364 staging readback failed")
    return {"stage":"PRE364","status":"STAGED_PASSIVE_ONLY",
      "host_source_original_sha256":sha(before),
      "host_source_staged_sha256":sha(output.encode()),
      "reverse_exact":True,"guest_loads_added":0,"guest_stores_rewritten":0,
      "player_owner_verified":False,"nitro_button_verified":False,
      "apk_built":False,"cheats_enabled":False,
      "bounded_log_events":256}
