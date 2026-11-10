#include "pre666_pass_bounded_sampler.h"
#include <cassert>
#include <cstdint>
#include <iostream>
using nfsmw::pre666::PassBoundedModel;
using nfsmw::pre666::Action;
using nfsmw::pre666::Draw;
static_assert(!nfsmw::pre666::kDefaultEnabled);
static_assert(nfsmw::pre666::kQueriesPerSlot==8);
constexpr Draw target{2,62,58,false},non_target{2,43,37,false},sky{2,62,58,true};
static void decision(nfsmw::pre666::Decision d,Action a,uint32_t q=0) {
  assert(d.action==a);if(a!=Action::None) assert(d.query_local==q && q<8);
}
int main() {
  PassBoundedModel m;
  assert(!m.BeginWorkSlot(false,true,true));
  decision(m.BeforeDraw(target),Action::None);
  assert(!m.BeginWorkSlot(true,false,true));
  assert(m.UnsafeReuseRejects()==1);
  assert(!m.BeginWorkSlot(true,true,false));
  assert(m.BeginWorkSlot(true,true,true));
  decision(m.BeforeDraw(target),Action::Begin,0);
  decision(m.BeforeDraw(target),Action::None);
  decision(m.BeforeEndRenderPass(),Action::End,1);
  assert(m.Balanced());
  // SAME shader/category in another render pass must start a NEW pair.
  decision(m.BeforeDraw(target),Action::Begin,2);
  decision(m.BeforeDraw(non_target),Action::End,3);
  decision(m.BeforeDraw(sky),Action::None);
  decision(m.BeforeDraw(target),Action::Begin,4);
  decision(m.BeforeEndCommandBuffer(),Action::End,5);
  assert(m.Starts()==3 && m.Ends()==3 && m.Balanced());
  decision(m.BeforeDraw(target),Action::Begin,6);
  decision(m.BeforeEndRenderPass(),Action::End,7);
  assert(m.Balanced());
  // All extra target bursts must be ignored and never exceed query 7.
  for(uint32_t i=0;i<30;i++) {
    decision(m.BeforeDraw(target),Action::None);
    decision(m.BeforeDraw(non_target),Action::None);
  }
  assert(m.Starts()==4 && m.Ends()==4 && m.SkippedBursts()==30);
  assert(m.BeginWorkSlot(true,true,true));
  assert(m.Starts()==0 && m.Ends()==0);
  decision(m.BeforeDraw(target),Action::Begin,0);
  m.AbandonRecording();
  assert(m.RecordingAborts()==1 && !m.Enabled());
  decision(m.BeforeDraw(target),Action::None);
  assert(!m.BeginWorkSlot(true,false,true));
  assert(m.UnsafeReuseRejects()==2);
  assert(m.BeginWorkSlot(true,true,true));
  // Exhaustive-ish deterministic stress: explicit pass changes force balancing.
  uint32_t seed=0xc291dff1;
  uint32_t emitted=0;
  for(uint32_t i=0;i<1000000;i++) {
    seed=seed*1664525u+1013904223u;
    const auto d=m.BeforeDraw((seed&15u)==1u ? target:non_target);
    if(d.action!=Action::None) {
      assert(d.query_local<8);
      ++emitted;
    }
    if(i%97==0) {
      const auto end=m.BeforeEndRenderPass();
      if(end.action!=Action::None){assert(end.query_local<8);++emitted;}
    }
  }
  const auto finish=m.BeforeEndCommandBuffer();
  if(finish.action!=Action::None){assert(finish.query_local<8);++emitted;}
  assert(m.Balanced());
  assert(m.Starts()<=4 && m.Ends()<=4 && emitted==m.Starts()+m.Ends());
  std::cout<<"PRE666_HOST_PASS_BOUNDARY_TEST=PASS\n"
           <<"PRE666_DEFAULT_ENABLED=false\n"
           <<"PRE666_QUERY_BUDGET_PER_SLOT=8\n"
           <<"PRE666_MAX_BURSTS_PER_SLOT=4\n"
           <<"PRE666_EXPLICIT_PASS_END=PASS\n"
           <<"PRE666_FENCE_CHECK_IS_SIMULATED=true\n"
           <<"PRE666_REAL_VULKAN_COMMANDS=false\n"
           <<"PRE666_REAL_ARM64_COMPILE=false\n"
           <<"PRE666_APK_BUILT=false\n"
           <<"PRE666_GPU_SHADER_TIME_MEASURED=false\n"
           <<"PRE666_FPS_GAIN_PROVEN=false\n";
}
