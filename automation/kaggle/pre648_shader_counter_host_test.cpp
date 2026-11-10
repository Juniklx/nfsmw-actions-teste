// PRE648: independent host fixture, not the Android game or proof of GPU timing.
#include "pre648_shader_pass_counter.h"
#include <cassert>
#include <cstdint>
#include <iostream>

using nfsmw::nativo::pre648::ContadorShaderPases;

int main() {
  ContadorShaderPases probe;
  probe.Anotar(11, 24, 2, false); // one normal Vulkan draw
  probe.Anotar(11, 24, 2, false); // same shader/pass
  probe.Anotar(11, 24, 3, false); // different pass
  probe.Anotar(11, 0, 1, false);  // depth-only, no fragment shader
  // Pending sky is NOT counted. This call models only actual deferred emission.
  probe.Anotar(5, 30, 2, true);
  probe.Anotar(0, 3, 2, false);  // invalid VS, fail closed
  probe.Anotar(500, 3, 2, false);  // out-of-range, fail closed
  const auto r=probe.ExtraerYLimpiar();
  assert(r.total==5 && r.normales==4 && r.cielo_aplazado_emitido==1);
  assert(r.fuera_de_rango==2);
  assert(r.primeros[0].vs_mas_uno==11 && r.primeros[0].ps_mas_uno==24);
  assert(r.primeros[0].categoria==2 && r.primeros[0].dibujos==2);
  bool depth_found=false, deferred_found=false, separate_pass_found=false;
  for (const auto& p:r.primeros) {
    depth_found |= p.vs_mas_uno==11 && p.ps_mas_uno==0 && p.categoria==1 && p.dibujos==1;
    deferred_found |= p.vs_mas_uno==5 && p.ps_mas_uno==30 && p.categoria==2 && p.dibujos==1;
    separate_pass_found |= p.vs_mas_uno==11 && p.ps_mas_uno==24 && p.categoria==3 && p.dibujos==1;
  }
  assert(depth_found && deferred_found && separate_pass_found);
  const auto cleared=probe.ExtraerYLimpiar();
  assert(cleared.total==0 && cleared.fuera_de_rango==0);
  // PRE646 observed genuine shader IDs up to VS n150, PS n142.
  probe.Anotar(151,143,8,false);
  probe.Anotar(152,0,8,false);  // highest index and depth-only
  const auto high=probe.ExtraerYLimpiar();
  assert(high.total==2 && high.normales==2 && high.fuera_de_rango==0);
  // Controlled repeated draws: bounded memory, and count exactly matches input.
  for (uint32_t i=0;i<200000;i++) {
    probe.Anotar((i%63)+1,(i%89)+1,(i%7),false);
  }
  const auto many=probe.ExtraerYLimpiar();
  assert(many.total==200000 && many.normales==200000 && many.cielo_aplazado_emitido==0);
  assert(many.fuera_de_rango==0);
  uint64_t sum=0;
  for (const auto& p:many.primeros) sum+=p.dibujos;
  assert(sum>0 && sum<=200000);
  assert(ContadorShaderPases::kMemoriaContadores==1638400);
  std::cout<<"PRE648_COUNTER_HOST_TEST=PASS\n"
           <<"PRE648_EXACT_INPUT_DRAWS=200000\n"
           <<"PRE648_DEPTH_ONLY=PASS\n"
           <<"PRE648_DEFERRED_SKY=PASS\n"
           <<"PRE648_FIXED_MEMORY_BYTES="<<ContadorShaderPases::kMemoriaContadores<<"\n";
}
