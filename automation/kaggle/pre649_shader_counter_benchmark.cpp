// PRE649: Linux host ONLY. Measures approximate CPU overhead of PRE648's
// in-memory counter, not Android GPU timing, power or gameplay FPS.
#include "pre648_shader_pass_counter.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <numeric>
#include <vector>

using nfsmw::nativo::pre648::ContadorShaderPases;
using Clock=std::chrono::steady_clock;
struct Event {
 uint32_t vs,ps,pass;
 bool sky;
};
struct Sample { double baseline_ns, counter_ns, summarize_ns; };
static volatile uint64_t output_sink=0;

#if defined(__GNUC__)
#define PRE649_NOINLINE __attribute__((noinline))
#else
#define PRE649_NOINLINE
#endif

// The baseline imitates ONLY the event-field reading. No real Vulkan commands.
PRE649_NOINLINE uint64_t baseline(const std::vector<Event>& events) {
 uint64_t sum=0;
 for (const auto &x:events)
  sum+=x.vs*3ull + x.ps*5ull + x.pass*7ull + uint64_t(x.sky);
 return sum;
}
PRE649_NOINLINE uint64_t instrumented(const std::vector<Event>& events, ContadorShaderPases& counter) {
 uint64_t sum=0;
 for (const auto &x:events) {
  sum+=x.vs*3ull + x.ps*5ull + x.pass*7ull + uint64_t(x.sky);
  counter.Anotar(x.vs,x.ps,x.pass,x.sky);
 }
 return sum;
}
static double elapsed_ns(Clock::time_point a,Clock::time_point b) {
 return std::chrono::duration<double,std::nano>(b-a).count();
}
static double median(std::vector<double> v) {
 std::sort(v.begin(),v.end());
 return v.at(v.size()/2);
}
static std::vector<Event> make_events(size_t n, bool diverse) {
 std::vector<Event> e;
 e.reserve(n);
 uint32_t state=0x92346ab5u;
 for(size_t i=0;i<n;++i) {
  state=1664525u*state+1013904223u;
  const uint32_t v=(state%150)+1; // n150 highest observed range
  const uint32_t p=(state%143);    // PS=0 allowed depth-only
  const uint32_t pass=(state%12);
  const bool sky=(i%97==0);
  if (diverse) e.push_back(Event{v,p,pass,sky});
  else e.push_back(Event{(i%9)+1,(i%21)+1,2,sky});
 }
 return e;
}
static int check() {
 auto ctr=std::make_unique<ContadorShaderPases>();
 // Exhaustive valid boundaries and all invalid one-off boundaries.
 ctr->Anotar(1,0,0,false);
 ctr->Anotar(159,159,15,true);
 ctr->Anotar(160,3,0,false);
 ctr->Anotar(2,160,0,false);
 ctr->Anotar(2,3,16,false);
 ctr->Anotar(0,3,0,false);
 auto r=ctr->ExtraerYLimpiar();
 if (r.total!=2 || r.normales!=1 || r.cielo_aplazado_emitido!=1 || r.fuera_de_rango!=4) return 2;
 if (ctr->ExtraerYLimpiar().total!=0) return 3;
 if (ContadorShaderPases::kMemoriaContadores!=1638400) return 4;
 // A report must be a pure snapshot and never count a pending, un-emitted sky.
 auto s=ctr->ExtraerYLimpiar(); if(s.total!=0)return 5;
 ctr->Anotar(151,143,8,true); // actual emission - high shader IDs
 r=ctr->ExtraerYLimpiar();
 if (r.total!=1 || r.cielo_aplazado_emitido!=1 || r.primeros[0].vs_mas_uno!=151
     ||r.primeros[0].ps_mas_uno!=143)return 6;
 return 0;
}
static Sample run(const std::vector<Event>& events,ContadorShaderPases& counter,bool invert) {
 double b,c,s;
 uint64_t z1,z2;
 if(invert) {
  auto a=Clock::now(); z2=instrumented(events,counter); auto d=Clock::now();
  c=elapsed_ns(a,d)/events.size();
  a=Clock::now();auto report=counter.ExtraerYLimpiar(); d=Clock::now();
  s=elapsed_ns(a,d);
  if(report.total!=events.size()||report.cielo_aplazado_emitido==0||report.fuera_de_rango!=0)
   std::exit(7);
  a=Clock::now(); z1=baseline(events); d=Clock::now();
  b=elapsed_ns(a,d)/events.size();
 } else {
  auto a=Clock::now(); z1=baseline(events); auto d=Clock::now();
  b=elapsed_ns(a,d)/events.size();
  a=Clock::now(); z2=instrumented(events,counter); d=Clock::now();
  c=elapsed_ns(a,d)/events.size();
  a=Clock::now();auto report=counter.ExtraerYLimpiar(); d=Clock::now();
  s=elapsed_ns(a,d);
  if(report.total!=events.size()||report.cielo_aplazado_emitido==0||report.fuera_de_rango!=0)
   std::exit(8);
 }
 if(z1!=z2)std::exit(9);
 output_sink=output_sink+z1;
 return Sample{b,c,s};
}
int main(){
 const int fail=check();
 if(fail){std::cerr<<"PRE649_FAIL_CODE="<<fail<<"\n";return fail;}
 auto counter=std::make_unique<ContadorShaderPases>();
 constexpr size_t N=300000;
 for(const bool diverse : {false,true}){
  auto events=make_events(N,diverse);
  run(events,*counter,false); // warmed independent of measured samples
  std::vector<double> b,c,s;
  for(int trial=0;trial<9;trial++){
   auto x=run(events,*counter,trial%2==0);
   b.push_back(x.baseline_ns);
   c.push_back(x.counter_ns);
   s.push_back(x.summarize_ns);
  }
  const double bm=median(b),cm=median(c),sm=median(s);
  if(!(std::isfinite(bm)&&std::isfinite(cm)&&std::isfinite(sm))||
      bm<=0||cm<=0||sm<=0)return 10;
  std::cout<<"PRE649_SCENARIO="<<(diverse?"DIVERSE":"REPEATED")<<"\n"
           <<"PRE649_DRAWS_PER_TRIAL="<<N<<"\n"
           <<"PRE649_TRIALS=9\n"
           <<"PRE649_BASELINE_MEDIAN_NS_PER_DRAW="<<bm<<"\n"
           <<"PRE649_WITH_COUNTER_MEDIAN_NS_PER_DRAW="<<cm<<"\n"
           <<"PRE649_COUNTER_INCREMENTAL_MEDIAN_NS_PER_DRAW="<<(cm-bm)<<"\n"
           <<"PRE649_REPORT_MEDIAN_MS="<<(sm/1000000.0)<<"\n";
 }
 std::cout<<"PRE649_HOST_INVARIANTS=PASS\n"
          <<"PRE649_VULKAN_DRIVER_EXECUTED=false\n"
          <<"PRE649_ANDROID_BENCHMARK=false\n"
          <<"PRE649_FPS_GAIN_PROVEN=false\n"
          <<"PRE649_FIXED_COUNTER_BYTES="<<ContadorShaderPases::kMemoriaContadores<<"\n";
 return 0;
}
