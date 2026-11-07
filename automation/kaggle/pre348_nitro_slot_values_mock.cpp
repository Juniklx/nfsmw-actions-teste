#include "pre336_nitro_address_diversity.hpp"
#include "pre348_nitro_slot_values.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
int main() {
  nfsmw_pre336::Diversity map;
  nfsmw_pre336::Snapshot old{};
  nfsmw_pre348::Meter meter;
  nfsmw_pre348::Snapshot snap{};
  assert(map.lookup_slot(0xBFA9E7FCu)==0);
  assert(map.observe(1,0xBFA9E7FCu,old));
  assert(map.lookup_slot(0xBFA9E7FCu)==1);
  assert(meter.record(1,1,0x3F800000u,snap));
  assert(snap.slot==1 && snap.written_float_bits==0x3F800000u);
  assert(meter.record(1,1,0x3F000000u,snap));
  assert(snap.events_for_slot_site==2);
  assert(!meter.record(1,1,0x3E800000u,snap));
  assert(meter.record(1,1,0x3E000000u,snap));
  assert(snap.events_for_slot_site==4);
  assert(map.observe(1,0xBFB0BF7Cu,old));
  assert(map.lookup_slot(0xBFB0BF7Cu)==2);
  assert(meter.record(1,2,0x3F400000u,snap));
  assert(snap.slot==2 && snap.events_for_slot_site==1);
  assert(meter.record(3,1,0x3F500000u,snap));
  assert(snap.site==3 && snap.slot==1);
  assert(!meter.record(6,1,0x3F800000u,snap));
  assert(!meter.record(1,0,0x3F800000u,snap));
  assert(!meter.record(1,17,0x3F800000u,snap));
  std::cout<<"PRE348_MOCK_STATUS AUDIT_OK\n";
  std::cout<<"PRE348_OWNER_VERIFIED false\n";
}
