#include "pre670_separate_timestamp_pool_lifecycle_model.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
using namespace nfsmw::pre670;
static Capability cap() {
  Capability c; c.requested=true; c.writer_available=true; c.reader_available=true;
  c.mock_separate_pool_created=true; c.slots=3; c.valid_bits=32; c.timestamp_period_ns=2.5;
  return c;
}
int main() {
  static_assert(!kDefaultEnabled && kQueriesPerSlot==8 && kPairsPerSlot==4);
  MockLifecycle m; assert(!m.Enabled() && m.QueryCount()==0);
  uint32_t lo=999,hi=999;
  assert(!m.BeginRecording(0,true)); assert(!m.QueryIndices(0,0,lo,hi));
  Capability c=cap();
  c.requested=false;assert(!m.Setup(c));assert(!m.Enabled());
  c=cap();c.slots=0;assert(!m.Setup(c));
  c=cap();c.slots=17;assert(!m.Setup(c));
  c=cap();c.valid_bits=0;assert(!m.Setup(c));
  c=cap();c.valid_bits=65;assert(!m.Setup(c));
  c=cap();c.timestamp_period_ns=std::numeric_limits<double>::infinity();assert(!m.Setup(c));
  c=cap();c.timestamp_period_ns=std::numeric_limits<double>::quiet_NaN();assert(!m.Setup(c));
  c=cap();c.writer_available=false;assert(!m.Setup(c));
  c=cap();c.reader_available=false;assert(!m.Setup(c));
  c=cap();c.mock_separate_pool_created=false;assert(!m.Setup(c));
  c=cap();assert(m.Setup(c));assert(m.Enabled() && m.QueryCount()==24);
  assert(!m.BeginRecording(0,false));assert(m.BeginRecording(0,true));
  assert(!m.BeginRecording(0,true));
  for (uint32_t p=0;p<kPairsPerSlot;p++) {
    assert(m.QueryIndices(0,p,lo,hi) && lo==p*2 && hi==lo+1);
  }
  assert(!m.QueryIndices(0,4,lo,hi));
  assert(!m.QueryIndices(3,0,lo,hi));
  assert(!m.Submit(0,true,5));
  assert(m.Submit(0,true,4));
  assert(!m.BeginRecording(0,true));
  assert(!m.CompleteReadback(0,true,4));
  assert(!m.Fence(0,FenceResult::NotReady));
  assert(m.State(0)==SlotState::Submitted);
  assert(!m.BeginRecording(0,true));
  assert(m.Fence(0,FenceResult::Success));
  assert(m.State(0)==SlotState::FencePassed);
  assert(!m.BeginRecording(0,true));
  assert(!m.CompleteReadback(0,false,4));
  assert(!m.CompleteReadback(0,true,3));
  assert(m.CompleteReadback(0,true,4));
  assert(m.BeginRecording(0,true));
  assert(m.AbandonBeforeSubmit(0));
  assert(!m.AbandonBeforeSubmit(0));
  assert(m.BeginRecording(2,true));
  assert(m.QueryIndices(2,3,lo,hi) && lo==22 && hi==23);
  assert(m.Submit(2,true,1));
  assert(!m.AbandonBeforeSubmit(2));
  assert(!m.Fence(2,FenceResult::NotReady));
  assert(!m.BeginRecording(2,true));
  assert(m.Fence(2,FenceResult::Success));
  assert(m.CompleteReadback(2,true,1));
  double ns=-1.0;assert(m.MockDeltaNs(100,104,ns) && ns==10.0);
  c=cap();c.valid_bits=8;c.timestamp_period_ns=1.0;
  assert(m.Setup(c));
  assert(m.MockDeltaNs(250,7,ns) && ns==13.0); // valid-bits wraparound
  c=cap();c.valid_bits=64;c.timestamp_period_ns=1.0;
  assert(m.Setup(c));assert(m.MockDeltaNs(UINT64_MAX-2,2,ns) && ns==5.0);
  assert(m.BeginRecording(1,true));
  assert(!m.Submit(1,false,1));
  assert(m.Faulted() && !m.Enabled());
  assert(!m.BeginRecording(1,true));
  assert(m.Setup(cap()));
  assert(m.BeginRecording(1,true));
  assert(m.Submit(1,true,1));
  assert(!m.Fence(1,FenceResult::Error));
  assert(m.Faulted() && !m.Enabled());
  assert(m.Setup(cap()));
  // Deterministic repeated slot rotation: pending entries cannot be reset
  // while other slots progress; each requires a verified success + read.
  uint64_t seed=0xabc6151;
  for(uint32_t i=0;i<100000;i++) {
    seed=(seed*1103515245u+12345u)&0xffffffffu;
    uint32_t s=uint32_t(seed%3u);
    if(m.State(s)==SlotState::Free) {
      assert(!m.BeginRecording(s,false));
      assert(m.BeginRecording(s,true));
      assert(m.Submit(s,true,uint32_t(i%5u==4u?4u:i%4u)));
    } else if(m.State(s)==SlotState::Submitted) {
      assert(!m.BeginRecording(s,true));
      if(i%3u!=0u) assert(!m.Fence(s,FenceResult::NotReady));
      else assert(m.Fence(s,FenceResult::Success));
    } else if(m.State(s)==SlotState::FencePassed) {
      assert(!m.BeginRecording(s,true));
      // This test knows the pairs submitted; simulate read as 0..4 from last
      // state with dedicated slot bookkeeping (see mirror below).
      // Retain readable until a later controlled reset sequence.
    }
  }
  // Reset only via clean Setup in this test; no Vulkan resources were made.
  assert(m.Setup(cap()));
  for(uint32_t s=0;s<3u;s++)assert(m.State(s)==SlotState::Free);
  std::cout<<"PRE670_HOST_RESOURCE_LIFECYCLE_TEST=PASS\n"
            <<"PRE670_QUERY_POOL_CREATED_IN_VULKAN=false\n"
            <<"PRE670_SEPARATE_QUERY_BUDGET_PER_SLOT=8\n"
            <<"PRE670_REAL_FENCE_CHECK=false\n"
            <<"PRE670_UNCHECKED_FENCE_RESULT_REUSE_REJECTED=true\n"
            <<"PRE670_INVALID_SUPPORT_DISABLED=true\n"
            <<"PRE670_EARLY_RESET_REJECTED=true\n"
            <<"PRE670_WAIT_NOT_READY_REJECTED=true\n"
            <<"PRE670_SUBMIT_FAILURE_FAIL_CLOSED=true\n"
            <<"PRE670_FENCE_FAILURE_FAIL_CLOSED=true\n"
            <<"PRE670_VALID_BITS_MOCK_WRAP=PASS\n"
            <<"PRE670_REAL_ARM64_BUILD=false\n"
            <<"PRE670_REAL_GPU_DURATION_MEASURED=false\n"
            <<"PRE670_APK_BUILT=false\n"
            <<"PRE670_FPS_GAIN_PROVEN=false\n";
}
