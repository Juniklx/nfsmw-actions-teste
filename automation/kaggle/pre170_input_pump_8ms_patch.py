#!/usr/bin/env python3
"""PRE170: guarded Android-only SDL PumpEvents request throttle, 8 ms (experimental).

Strictly verifies authenticated PRE99 C++ and header bytes. Does not touch touch/PG9076
bridge state, SDL callback/event dispatch, Vulkan, assets, signing, or thermals.
"""
from __future__ import annotations
import hashlib

INPUT_SHA = "be93c7ae7297489d369abff7c86becf29373c127fa7e6dbbc802dd7a09452728"
HEADER_SHA = "ab2c1b5cd930fbc941882a720c540553da388b20ffcfc1f3ae3536abaa36d484"
CPP_INCLUDES = b"#include <array>\n#include <filesystem>\n"
CPP_INCLUDES_NEW = b"#include <array>\n#include <chrono>  // NFSMW_PRE170 Android input pump cadence\n#include <filesystem>\n"
HEADER_INCLUDES = b"#include <atomic>\n#include <mutex>\n"
HEADER_INCLUDES_NEW = b"#include <atomic>\n#include <cstdint>  // NFSMW_PRE170\n#include <mutex>\n"
HEADER_FIELD = b"  std::atomic<bool> sdl_pumpevents_queued_;\n"
HEADER_FIELD_NEW = (b"  std::atomic<bool> sdl_pumpevents_queued_;\n"
                    b"  std::atomic<std::int64_t> sdl_next_pump_ns_{0};  // NFSMW_PRE170\n")
OLD = b"""void SDLInputDriver::QueueControllerUpdate() {
  // Pump SDL events to ensure controller state is up to date.
  bool is_queued = false;
  sdl_pumpevents_queued_.compare_exchange_strong(is_queued, true);
  if (!is_queued) {
    attached_window_->app_context().CallInUIThread([this]() {
      SDL_PumpEvents();
      sdl_pumpevents_queued_ = false;
    });
  }
}
"""
NEW = b"""void SDLInputDriver::QueueControllerUpdate() {
#if REX_PLATFORM_ANDROID
  // NFSMW_PRE170: avoid redundant SDL pump requests closer than 8ms.
  // SDL hotplug polling is retained, and touch/PG bridge state is read
  // independently. Compare-and-swap bounds requests across guest threads.
  const int64_t now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::steady_clock::now().time_since_epoch()).count();
  constexpr int64_t kMinIntervalNs = 8'000'000;
  int64_t next_ns = sdl_next_pump_ns_.load(std::memory_order_relaxed);
  while (true) {
    if (now_ns < next_ns) return;
    if (sdl_next_pump_ns_.compare_exchange_weak(
            next_ns, now_ns + kMinIntervalNs,
            std::memory_order_relaxed, std::memory_order_relaxed)) break;
  }
#endif
  // Pump SDL events to ensure controller state is up to date.
  bool is_queued = false;
  sdl_pumpevents_queued_.compare_exchange_strong(is_queued, true);
  if (!is_queued) {
    attached_window_->app_context().CallInUIThread([this]() {
      SDL_PumpEvents();
      sdl_pumpevents_queued_ = false;
    });
  }
}
"""

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def replace_once(data: bytes, old: bytes, new: bytes, description: str) -> bytes:
    if data.count(old) != 1 or new in data:
        raise ValueError("PRE170 patch mismatch/previously applied: " + description)
    return data.replace(old, new, 1)

def patch_verified(cpp: bytes, header: bytes) -> tuple[bytes, bytes]:
    if sha(cpp) != INPUT_SHA or sha(header) != HEADER_SHA:
        raise ValueError("PRE170 requires exact verified PRE99 input CPP/header")
    cpp = replace_once(cpp, CPP_INCLUDES, CPP_INCLUDES_NEW, "chrono include")
    cpp = replace_once(cpp, OLD, NEW, "pump method")
    header = replace_once(header, HEADER_INCLUDES, HEADER_INCLUDES_NEW, "stdint include")
    header = replace_once(header, HEADER_FIELD, HEADER_FIELD_NEW, "atomic member")
    assert cpp.count(b"NFSMW_PRE170") == 2 and header.count(b"NFSMW_PRE170") == 2
    return cpp, header

if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).parent / "pre169_verified_source/nativo/sdk"
    if not root.exists():
        print("PRE170 patch syntax ready; source audit to run in verified runner")
    else:
        cpp = (root / "src/input/sdl/sdl_input_driver.cpp").read_bytes()
        header = (root / "include/rex/input/sdl/sdl_input_driver.h").read_bytes()
        a, b = patch_verified(cpp, header)
        assert a != cpp and b != header
        try: patch_verified(a, b)
        except ValueError: pass
        else: raise AssertionError("Double application not blocked")
        print("PRE170_PATCH_VERIFIED", sha(a), sha(b))
