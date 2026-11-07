#pragma once
// PRE316: bounded passive Nitro cycle telemetry; no guest memory access.
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>

namespace nfsmw_pre316 {
struct Snapshot {
  std::uint32_t site, samples, min_bits, max_bits, last_bits, threshold_events;
};
struct Site {
  std::atomic<std::uint32_t> samples{0}, min_bits{0x7f800000},
      max_bits{0}, last_bits{0}, threshold_events{0};
  std::atomic<std::uint32_t> last_band{0xffffffffu};
};
struct Monitor {
  Site sites[5]{};
  static std::uint32_t bits(float x) noexcept {
    std::uint32_t u=0;
    std::memcpy(&u,&x,sizeof(u));
    return u;
  }
  static float number(std::uint32_t u) noexcept {
    float f;
    std::memcpy(&f,&u,sizeof(f));
    return f;
  }
  static std::uint32_t band(float f) noexcept {
    if (f<=0.005f) return 0;
    if (f<=0.05f) return 1;
    if (f<=0.25f) return 2;
    if (f<0.75f) return 3;
    if (f<0.95f) return 4;
    if (f<0.995f) return 5;
    return 6;
  }
  bool observe(std::uint32_t site, std::uint32_t value_bits,
               Snapshot& out) noexcept {
    if (site<1 || site>5) return false;
    float f=number(value_bits);
    if (!std::isfinite(f) || f<0.f || f>1.01f) return false;
    Site& s=sites[site-1];
    // Serialization of logs is not guaranteed. Snapshot is monotonic stats.
    const auto n=s.samples.fetch_add(1,std::memory_order_relaxed)+1;
    auto mn=s.min_bits.load(std::memory_order_relaxed);
    while (value_bits<mn && !s.min_bits.compare_exchange_weak(
             mn,value_bits,std::memory_order_relaxed)) {}
    auto mx=s.max_bits.load(std::memory_order_relaxed);
    while (value_bits>mx && !s.max_bits.compare_exchange_weak(
             mx,value_bits,std::memory_order_relaxed)) {}
    s.last_bits.store(value_bits,std::memory_order_relaxed);
    const std::uint32_t b=band(f);
    const auto previous=s.last_band.exchange(b,std::memory_order_relaxed);
    bool changed=(previous!=b);
    // Always observe first sample and powers-of-two milestones up to 8192.
    bool checkpoint=(n==1 || (n<=8192 && (n&(n-1))==0));
    // Event cap to prevent unbounded logging when crossings oscillate.
    auto events=s.threshold_events.load(std::memory_order_relaxed);
    bool event=false;
    if(changed) {
      while(events<36u && !s.threshold_events.compare_exchange_weak(
           events,events+1,std::memory_order_relaxed)) {}
      event=(events<36u);
    }
    if (!event && !checkpoint) return false;
    out={site,n,s.min_bits.load(std::memory_order_relaxed),
      s.max_bits.load(std::memory_order_relaxed),value_bits,
      s.threshold_events.load(std::memory_order_relaxed)};
    return true;
  }
};
} // nfsmw_pre316
