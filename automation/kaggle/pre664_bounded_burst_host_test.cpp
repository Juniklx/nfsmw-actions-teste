// PRE664 model tests. Not a Vulkan timestamp, frame pacing or Android benchmark.
#include "pre664_bounded_burst_sampler.h"
#include <array>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>

using nfsmw::pre664::Action;
using nfsmw::pre664::BoundedBurstModel;
using nfsmw::pre664::Draw;
static_assert(!nfsmw::pre664::kDefaultEnabled, "must fail closed by default");
static_assert(nfsmw::pre664::kQueriesPerSlot == 8, "separate query budget invariant");

int main() {
  constexpr Draw target{2, 62, 58, false};
  constexpr Draw other{2, 43, 37, false};
  constexpr Draw sky{2, 62, 58, true};
  BoundedBurstModel m;
  assert(!m.BeginSlot(false, true, true));
  assert(m.OnDraw(target).action == Action::None);
  assert(!m.BeginSlot(true, false, true));
  assert(m.UnsafeReuseRejects() == 1);
  assert(m.OnDraw(target).action == Action::None);
  assert(!m.BeginSlot(true, true, false));
  assert(m.OnDraw(target).action == Action::None);

  assert(m.BeginSlot(true, true, true));
  assert(m.OnDraw(other).action == Action::None);
  auto a = m.OnDraw(target);
  assert(a.action == Action::Begin && a.query == 0);
  assert(m.OnDraw(target).action == Action::None);
  a = m.OnDraw(other);
  assert(a.action == Action::End && a.query == 1);
  assert(m.OnDraw(sky).action == Action::None);
  for (uint32_t pair = 1; pair != 4; ++pair) {
    a = m.OnDraw(target);
    assert(a.action == Action::Begin && a.query == 2 * pair);
    a = m.OnDraw(other);
    assert(a.action == Action::End && a.query == 2 * pair + 1);
  }
  assert(m.OnDraw(target).action == Action::None);
  assert(m.StartedPairs() == 4 && m.CompletedPairs() == 4);
  assert(m.SkippedBursts() == 1);
  assert(m.EndCommandBuffer().action == Action::None);
  assert(m.BeginSlot(true, true, true));
  assert(m.OnDraw(target).action == Action::Begin);
  a = m.EndCommandBuffer();
  assert(a.action == Action::End && a.query == 1);
  assert(m.StartedPairs() == 1 && m.CompletedPairs() == 1);
  // Reject reuse without completed fence; do not claim actual fence check exists.
  assert(!m.BeginSlot(true, false, true));
  assert(m.OnDraw(target).action == Action::None);
  // Deterministic stress test: no query index >= 8 and start/end balanced.
  assert(m.BeginSlot(true, true, true));
  uint32_t begins = 0, ends = 0;
  uint32_t seed = 0x6425f17du;
  for (uint32_t i = 0; i < 1000000; ++i) {
    seed = seed * 1664525u + 1013904223u;
    a = m.OnDraw((seed & 3u) == 0 ? target : other);
    if (a.action != Action::None) assert(a.query < 8);
    if (a.action == Action::Begin) ++begins;
    if (a.action == Action::End) ++ends;
  }
  a = m.EndCommandBuffer();
  if (a.action == Action::End) ++ends;
  assert(begins == ends && begins <= 4);
  assert(m.CompletedPairs() == begins);

  // Host-only illustrative wall-clock cost. Not an approval threshold.
  constexpr uint32_t N = 500000;
  volatile uint64_t checksum = 0;
  m.BeginSlot(false, true, true);
  const auto start = std::chrono::steady_clock::now();
  for (uint32_t i = 0; i < N; ++i) {
    const auto d = m.OnDraw((i % 7u) ? other : target);
    checksum += static_cast<unsigned>(d.action);
  }
  const auto end = std::chrono::steady_clock::now();
  const double per_draw = std::chrono::duration<double, std::nano>(end - start).count() / N;
  assert(std::isfinite(per_draw) && per_draw >= 0.0);
  std::cout << "PRE664_HOST_MODEL_TEST=PASS\n"
    << "PRE664_DEFAULT_ENABLED=false\n"
    << "PRE664_MAX_PAIRS_PER_SLOT=4\n"
    << "PRE664_SEPARATE_QUERIES_PER_SLOT=8\n"
    << "PRE664_C2_POOL_MODIFIED=false\n"
    << "PRE664_VULKAN_COMMANDS_EXECUTED=false\n"
    << "PRE664_NATIVE_ANDROID_GPU_TIMED=false\n"
    << "PRE664_FPS_GAIN_PROVEN=false\n"
    << "PRE664_HOST_DISABLED_MODEL_NS_PER_DRAW=" << per_draw << "\n"
    << "PRE664_CHECKSUM=" << checksum << "\n";
}
