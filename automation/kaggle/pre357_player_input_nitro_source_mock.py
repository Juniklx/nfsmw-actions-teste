#!/usr/bin/env python3
from pre357_player_input_nitro_source_audit import occurrences,candidate
rows=["// SDL_EVENT_GAMEPAD_BUTTON_DOWN comment", 
"if(event.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN) {",
"bool nitrous=false;",
"if(event.type==SDL_EVENT_KEY_UP) {}"]
found=occurrences(rows)
assert len(found)==3, found
assert found[0][0]==1
assert "gamepad_button" in found[0][1]
assert "nitro" in found[1][1]
assert candidate("workspace/nativo/app/src/sdl_input_driver.cpp")
assert not candidate("workspace/nativo/app/generated/default/nfsmw_recomp.66.cpp")
assert not candidate("workspace/nativo/sdk/thirdparty/sdl3/test/testgamepad.cpp")
print("PRE357_MOCK_STATUS AUDIT_OK")
