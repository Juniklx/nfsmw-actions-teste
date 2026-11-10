// PRE672 C++17 strict mock-only host regression; no Vulkan driver or game invoked.
#include "pre672_gpu_timestamp_capability_failclosed_host.h"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
using namespace nfsmw::pre672;
static Capability Good(){
 Capability c;
 c.explicit_diagnostic_request=true;
 c.graphics_queue=true;
 c.timestamp_compute_and_graphics=true;
 c.timestamp_valid_bits=48;
 c.timestamp_period_ns=1.6;
 c.pfns_present=true;
 c.subpass_multiview_status_known=true;
 c.view_mask=0;
 c.per_tile_mode_status_known=true;
 c.per_tile_mode_active=false;
 c.stages_support_checked=true;
 c.stages_supported=true;
 c.command_slots=2;
 return c;
}
int main(){
 static_assert(!kDefaultEnabled && kQueriesPerSlot==8 && kPairsPerSlot==4);
 Capability c{};
 assert(!Supported(c));
 c=Good();
 assert(Supported(c));
 auto reject=[&](auto f){auto x=c;f(x);assert(!Supported(x));};
 reject([](Capability& x){x.explicit_diagnostic_request=false;});
 reject([](Capability& x){x.graphics_queue=false;});
 reject([](Capability& x){x.timestamp_compute_and_graphics=false;});
 reject([](Capability& x){x.timestamp_valid_bits=0;});
 reject([](Capability& x){x.timestamp_valid_bits=65;});
 reject([](Capability& x){x.timestamp_period_ns=0;});
 reject([](Capability& x){x.timestamp_period_ns=std::numeric_limits<double>::infinity();});
 reject([](Capability& x){x.timestamp_period_ns=std::numeric_limits<double>::quiet_NaN();});
 reject([](Capability& x){x.pfns_present=false;});
 reject([](Capability& x){x.subpass_multiview_status_known=false;});
 reject([](Capability& x){x.view_mask=1;});
 reject([](Capability& x){x.view_mask=0x80000000u;});
 reject([](Capability& x){x.per_tile_mode_status_known=false;});
 reject([](Capability& x){x.per_tile_mode_active=true;});
 reject([](Capability& x){x.stages_support_checked=false;});
 reject([](Capability& x){x.stages_supported=false;});
 reject([](Capability& x){x.command_slots=0;});
 reject([](Capability& x){x.command_slots=17;});
 GuardedLifecycle a;
 c.explicit_diagnostic_request=false;
 assert(!a.Configure(c) && !a.Enabled());
 c=Good();
 assert(a.Configure(c)&&a.Enabled()&&a.QueryCount()==16);
 assert(!a.Configure(c));
 assert(!a.BeginSlot(0,false,VkFenceOutcome::Success)); // reset inside pass illegal
 assert(!a.BeginSlot(0,true,VkFenceOutcome::NotReady));
 assert(a.BeginSlot(0,true,VkFenceOutcome::Success));
 assert(!a.BeginSlot(0,true,VkFenceOutcome::Success));
 assert(a.ReadyToEndRenderPass(0)); // empty recorded slot has no dangling pair
 assert(!a.BeginPair(0,false,false));
 assert(!a.BeginPair(0,true,true)); // deferred sky not recorded
 uint32_t first=99,last=99;
 assert(a.QueryPair(0,0,first,last)&&first==0&&last==1);
 for(uint32_t i=0;i<4;++i){
   assert(a.BeginPair(0,true,false));
   assert(!a.ReadyToEndRenderPass(0)&&!a.ReadyToEndCommandBuffer(0));
   assert(!a.BeginPair(0,true,false));
   assert(!a.EndPair(0,false));
   assert(a.EndPair(0,true));
   assert(a.QueryPair(0,i,first,last));
   assert(first==i*2 && last==i*2+1);
 }
 assert(!a.BeginPair(0,true,false));
 assert(!a.QueryPair(0,4,first,last));
 assert(a.ReadyToEndCommandBuffer(0));
 assert(a.Submitted(0,VkSubmitOutcome::Success));
 assert(!a.Submitted(0,VkSubmitOutcome::Success));
 assert(!a.BeginSlot(0,true,VkFenceOutcome::Success)); // pending query
 assert(!a.Reclaim(0,VkFenceOutcome::NotReady,QueryOutcome::Success,true));
 assert(!a.Reclaim(0,VkFenceOutcome::Success,QueryOutcome::NotReady,true));
 assert(!a.Reclaim(0,VkFenceOutcome::Success,QueryOutcome::Success,false));
 assert(a.Reclaim(0,VkFenceOutcome::Success,QueryOutcome::Success,true));
 assert(a.BeginSlot(1,true,VkFenceOutcome::Success));
 assert(a.QueryPair(1,0,first,last)&&first==8&&last==9);
 assert(a.QueryPair(1,3,first,last)&&first==14&&last==15);
 assert(a.ReadyToEndCommandBuffer(1));
 assert(a.Submitted(1,VkSubmitOutcome::Success));
 assert(a.Reclaim(1,VkFenceOutcome::Success,QueryOutcome::Success,true));
 // Strict failure on explicit Vulkan-style fence or query ERROR, even if other
 // evidence (availability etc.) is missing.
 GuardedLifecycle b;
 assert(b.Configure(Good()));
 assert(!b.BeginSlot(0,true,VkFenceOutcome::Error));
 assert(!b.Enabled()&&b.Faulted());
 GuardedLifecycle q;
 assert(q.Configure(Good()));
 assert(q.BeginSlot(0,true,VkFenceOutcome::Success));
 assert(q.ReadyToEndCommandBuffer(0));
 assert(q.Submitted(0,VkSubmitOutcome::Success));
 assert(!q.Reclaim(0,VkFenceOutcome::Error,QueryOutcome::Success,true));
 assert(q.Faulted()&&!q.Enabled());
 GuardedLifecycle z;
 assert(z.Configure(Good()));
 assert(z.BeginSlot(0,true,VkFenceOutcome::Success));
 assert(z.Submitted(0,VkSubmitOutcome::Success));
 assert(!z.Reclaim(0,VkFenceOutcome::Success,QueryOutcome::Error,false));
 assert(z.Faulted()&&!z.Enabled());
 GuardedLifecycle t;
 assert(t.Configure(Good()));
 assert(t.BeginSlot(0,true,VkFenceOutcome::Success));
 assert(!t.Submitted(0,VkSubmitOutcome::Error));
 assert(!t.Enabled()&&t.Faulted());
 std::cout
   <<"PRE672_MULTIVIEW_DEFAULT_DENY=PASS\n"
   <<"PRE672_PER_TILE_UNKNOWN_OR_ENABLED_DENY=PASS\n"
   <<"PRE672_TIMESTAMP_VALID_BITS_AND_PERIOD_GUARDS=PASS\n"
   <<"PRE672_RESET_REQUIRES_OUTSIDE_RENDERPASS=PASS\n"
   <<"PRE672_DEFERRED_SKY_BLOCKED=PASS\n"
   <<"PRE672_UNBALANCED_TIMESTAMP_PAIR_BLOCKED=PASS\n"
   <<"PRE672_BOUNDED_QUERY_INDICES=PASS\n"
   <<"PRE672_FENCE_AND_SUBMIT_ERRORS_FAIL_CLOSED=PASS\n"
   <<"PRE672_QUERY_AVAILABILITY_REQUIRED=PASS\n"
   <<"PRE672_HOST_MODEL_ONLY=true\n"
   <<"PRE672_REAL_VULKAN_POOL_CREATED=false\n"
   <<"PRE672_REAL_DEVICE_MEASURED=false\n"
   <<"PRE672_ARM64_COMPILED=false\n"
   <<"PRE672_APK_BUILT=false\n"
   <<"PRE672_FPS_GAIN_PROVEN=false\n";
}
