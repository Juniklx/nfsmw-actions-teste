#!/usr/bin/env python3
from pre346_player_car_named_source_readonly import select_lines
s='''
int get_player_car_ptr(void);
int playerVehicle = 3;
bool other_flag = true;
// get_player_car should be ignored in comment
void hello() {}
bool is_player_vehicle = true;
'''
a=select_lines(s)
assert len(a)==3,a
assert a[0]["tag"]=="explicit"
assert a[1]["tag"]=="explicit"
assert a[2]["tag"]=="explicit"
assert not select_lines("// playercar\n/* player vehicle */\n")
print("PRE346_MOCK_STATUS AUDIT_OK")
print("PRE346_MOCK_ASSERTIONS 5")
