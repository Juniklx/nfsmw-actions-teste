#!/usr/bin/env python3
"""PRE165: guarded one-line SDL wake 1ms to 2ms. No control, Vulkan or thermal changes."""
from __future__ import annotations
import hashlib

PRE99_SHA="f4ae379985adc2343fabde1e2eeebf048997482a8cfe17ef5839e69f8e66ffdc"
OLD=b'SDL_Delay(1);  // NFSMW_DIAG37: hipotese, nao otimizacao comprovada.'
NEW=b'SDL_Delay(2);  // NFSMW_PRE165: experimento apenas apos wake SDL.'

def replace_once(data:bytes)->bytes:
    if data.count(OLD)!=1 or NEW in data:raise ValueError("PRE165 already applied or anchor mismatch")
    start=data.index(b'    ProcessEvent(event);')
    end=data.index(OLD)
    if start>=end or b'if (es_despertar && !HasQuitFromUIThread())' not in data[start:end]:
        raise ValueError("PRE165 wake-only event scope mismatch")
    return data.replace(OLD,NEW,1)

def patch_verified(data:bytes)->bytes:
    if hashlib.sha256(data).hexdigest()!=PRE99_SHA:
        raise ValueError("PRE165 exact PRE99 SDL source digest mismatch")
    return replace_once(data)

if __name__=="__main__":
    sample=b'    ProcessEvent(event);\n    if (es_despertar && !HasQuitFromUIThread()) {\n      '+OLD+b'\n    }\n'
    assert replace_once(sample).count(NEW)==1
    for invalid in [sample.replace(OLD,NEW),sample.replace(OLD,b'SDL_Delay(3);'),sample+OLD]:
        try:replace_once(invalid)
        except ValueError:pass
        else:raise AssertionError("PRE165 invalid patch accepted")
    print("PRE165_WAKE_ONLY_PATCH_TEST_PASSED; source digest enforced at build")
