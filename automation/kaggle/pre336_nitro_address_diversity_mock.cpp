#include "pre336_nitro_address_diversity.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
int main() {
  nfsmw_pre336::Diversity d;
  nfsmw_pre336::Snapshot out{};
  assert(!d.observe(0,0xBFA9E7FCu,out));
  assert(!d.observe(1,0,out));
  assert(d.observe(1,0xBFA9E7FCu,out));
  assert(out.object_slot==1 && out.unique_objects==1 && !out.overflow);
  assert(d.observe(2,0xBFA9E7FCu,out));
  assert(out.object_slot==1 && out.site_mask==3);
  assert(d.observe(3,0xBFA9E7FCu,out));
  assert(out.object_slot==1 && out.site_mask==7);
  assert(d.observe(1,0xA00000FCu,out));
  assert(out.object_slot==2 && out.unique_objects==2);
  assert(d.observe(4,0xA00000FCu,out));
  assert(out.object_slot==2 && out.site_mask==9);
  // Populate all 16 slots; attempt a 17th different address, fail closed.
  for(std::uint32_t k=2;k<16;++k) {
    assert(d.observe(1,0x90000000u+k*256u,out));
  }
  bool was_logged=d.observe(1,0x800000FCu,out);
  assert(d.exceeded.load());
  assert(d.unique.load()==16);
  assert(!was_logged || (out.overflow && out.object_slot==0));
  assert(!d.observe(2,0xffffffffu,out));
  std::cout<<"PRE336_MOCK_STATUS AUDIT_OK\n";
  std::cout<<"PRE336_SLOTS 16\n";
  std::cout<<"PRE336_NO_OWNER_CLAIM true\n";
}
