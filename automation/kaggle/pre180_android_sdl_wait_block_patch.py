#!/usr/bin/env python3
"""PRE180: experimental Android SDL WaitEvent sentinel spin fix.

Only applies to an authenticated, exact-byte SDL 3.5.0 PRE99 source. The
Android-specific inner wait pump is made non-sentinel-creating, and the
blocking timeout accounts for joystick and sensor polling requirements.
No game C++/Java/graphics/thermal files are modified by this patch module.
"""
from __future__ import annotations
import hashlib

SOURCE_SHA = '7e05fa10e57246a7c32f9cb4e27d3faa06bbaea8a8aa603e9ce11fbc75ffc516'
HELPER_ANCHOR=b"#endif // !SDL_PLATFORM_ANDROID\n\nbool SDL_WaitEvent(SDL_Event *event)\n"
HELPER_NEW=b"""#endif // !SDL_PLATFORM_ANDROID

#ifdef SDL_PLATFORM_ANDROID
// NFSMW_PRE180: preserve SDL joystick/sensor polling when blocking the UI loop.
// Android's WaitEvent path must not generate a poll sentinel on each iteration.
static Sint64 SDL_AndroidGetPollingIntervalNS(void)
{
    Sint64 poll_intervalNS = SDL_MAX_SINT64;
#ifndef SDL_JOYSTICK_DISABLED
    if (SDL_WasInit(SDL_INIT_JOYSTICK) && SDL_update_joysticks) {
        if (SDL_JoysticksOpened()) {
            poll_intervalNS = SDL_min(poll_intervalNS, EVENT_POLL_INTERVAL_NS);
        } else {
            poll_intervalNS = SDL_min(poll_intervalNS, ENUMERATION_POLL_INTERVAL_NS);
        }
    }
#endif
#ifndef SDL_SENSOR_DISABLED
    if (SDL_WasInit(SDL_INIT_SENSOR) && SDL_update_sensors && SDL_SensorsOpened()) {
        poll_intervalNS = SDL_min(poll_intervalNS, EVENT_POLL_INTERVAL_NS);
    }
#endif
    return poll_intervalNS;
}
#endif // SDL_PLATFORM_ANDROID

bool SDL_WaitEvent(SDL_Event *event)
"""
ANDROID_WAIT_OLD=b"""#ifdef SDL_PLATFORM_ANDROID
    for (;;) {
        SDL_PumpEventsInternal(true);

        if (SDL_PeepEvents(event, 1, SDL_GETEVENT, SDL_EVENT_FIRST, SDL_EVENT_LAST) > 0) {
            return true;
        }

        Uint64 delay = -1;
        if (timeoutNS > 0) {
            Uint64 now = SDL_GetTicksNS();
            if (now >= expiration) {
                // Timeout expired and no events
                return false;
            }
            delay = (expiration - now);
        }
        Android_PumpEvents(delay);
    }
#else
"""
ANDROID_WAIT_NEW=b"""#ifdef SDL_PLATFORM_ANDROID
    for (;;) {
        // NFSMW_PRE180: a sentinel here wakes the Android condition repeatedly.
        // Only the nonblocking SDL_PollEvent path needs the poll sentinel.
        SDL_PumpEventsInternal(false);

        if (SDL_PeepEvents(event, 1, SDL_GETEVENT, SDL_EVENT_FIRST, SDL_EVENT_LAST) > 0) {
            return true;
        }

        Sint64 delay = -1;
        if (timeoutNS > 0) {
            Uint64 now = SDL_GetTicksNS();
            if (now >= expiration) {
                // Timeout expired and no events
                return false;
            }
            delay = (Sint64)(expiration - now);
        }
        // Continue polling for hotplug, open joysticks and active sensors.
        const Sint64 polling = SDL_AndroidGetPollingIntervalNS();
        if (polling != SDL_MAX_SINT64 && (delay < 0 || polling < delay)) {
            delay = polling;
        }
        Android_PumpEvents(delay);
    }
#else
"""

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def replace_once(source:bytes,old:bytes,new:bytes,label:str)->bytes:
    if source.count(old)!=1 or new in source:
        raise ValueError(f'PRE180 mismatch or already patched: {label}')
    return source.replace(old,new,1)

def patch_verified(source:bytes)->bytes:
    if sha(source)!=SOURCE_SHA:
        raise ValueError('PRE180 source SHA mismatch (exact PRE99 SDL_events.c required)')
    after=replace_once(source,HELPER_ANCHOR,HELPER_NEW,'Android polling helper')
    after=replace_once(after,ANDROID_WAIT_OLD,ANDROID_WAIT_NEW,'Android wait loop')
    if after.count(b'NFSMW_PRE180')!=2:
        raise ValueError('PRE180 marker mismatch')
    # SDL_PollEvent's initial sentinel pump is preserved exactly.
    if after.count(b'SDL_PumpEventsInternal(true)')!=source.count(b'SDL_PumpEventsInternal(true)')-1:
        raise ValueError('unexpected change in sentinel pump count')
    if b'SDL_WaitEventTimeoutNS(event, 0)' not in after:
        raise ValueError('SDL PollEvent changed unexpectedly')
    if b'SDL_JoysticksOpened()' not in HELPER_NEW or b'SDL_SensorsOpened()' not in HELPER_NEW:
        raise ValueError('input polling not preserved')
    return after

if __name__=='__main__':
    import zipfile,io,pathlib
    arc=pathlib.Path('/mnt/data/NFSMW_PRE179_SDL3_READONLY_SOURCE_42092841777.zip')
    if arc.exists():
        with zipfile.ZipFile(arc) as o, zipfile.ZipFile(io.BytesIO(o.read('PRE179_SDL3_READONLY_AUDIT.zip'))) as z:
            source=z.read('matched/3_workspace_nativo_sdk_thirdparty_sdl3_src_events_SDL_events.c')
        updated=patch_verified(source)
        print('PRE180_EXACT_VERIFIED',sha(source),'->',sha(updated),'bytes',len(updated))
        try:patch_verified(updated)
        except ValueError:print('PRE180_REAPPLICATION_REFUSED_OK')
        else:raise AssertionError('PRE180 duplicate patch not rejected')
    else:
        print('PRE180 patch module syntax ready, authenticated PRE179 source not local')