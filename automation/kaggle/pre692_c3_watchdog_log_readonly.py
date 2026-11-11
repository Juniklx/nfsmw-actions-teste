#!/usr/bin/env python3
"""PRE692: readonly NFSMW watchdog/C3 chronology; never operates on the game.
Raw inputs stay local. Output is grouped JSON, not a raw log copy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

TS = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]")
CAP = re.compile(r"\[ajustes\] resolucion interna (\d+x\d+) y limite de FPS (\d+)")
TRACE = re.compile(r"\[NFSMW_PRE635_C3_TWOREQUEST_TRACE\] (.*)$")
GUARD = re.compile(r"\[NFSMW_PRE194_C3 indice_fuera=(\w+) referencia_distinta=(\w+) copia_duplicada=(\w+)\]")
START = re.compile(r"\[vigilante\] (5|20) s sin que se mueva ni un registro")
RECOVERY = re.compile(r"\[vigilante\] el juego ha vuelto a moverse despues de (\d+) s parado")
CAPTURE = re.compile(r"^COLLECTION_(START|END)=(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d{4})$", re.MULTILINE)
FIELDS = {"indice","en_vuelo","frame","textura_frame","epoca_ahora","epoca_primera",
          "offset_primera","offset_segunda","mismos_comandos","subir","trabajo_huella","datos_bytes"}
ABSOLUTE = {"frame","textura_frame","epoca_ahora","epoca_primera"}

def ts(row):
    m=TS.match(row)
    return datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S.%f") if m else None

def audit(path:Path,capture:Path|None=None):
    if not path.is_file() or path.stat().st_size>64*1024*1024:
        raise ValueError("PRE692_LOG_MISSING_OR_TOO_LARGE")
    raw=path.read_bytes()
    lines=raw.decode("utf8","replace").splitlines()
    sessions=[]
    current=None
    for line_number,row in enumerate(lines,1):
        when=ts(row)
        m=CAP.search(row)
        if m:
            if current: current["last_line"]=line_number-1
            current={"start":when,"first_line":line_number,"last_line":len(lines),
                     "resolution":m.group(1),"cap":int(m.group(2)),"driver":"UNKNOWN",
                     "trace":[],"guard":[],"episodes":[],"pending":None}
            sessions.append(current)
        if not current or not when: continue
        if "Vulkan: driver propio cargado con adrenotools:" in row:
            current["driver"]="RADV_XCLIPSE" if "vulkan.radeon.so" in row else "OTHER_CUSTOM"
        m=TRACE.search(row)
        if m:
            f=dict(re.findall(r"([a-z_]+)=([^\s]+)",m.group(1)))
            if not FIELDS.issubset(f): raise ValueError("PRE692_C3_TRACE_INCOMPLETE")
            current["trace"].append((when,line_number,{k:f[k] for k in sorted(FIELDS)}))
        m=GUARD.search(row)
        if m: current["guard"].append((when,line_number,m.groups()))
        m=START.search(row)
        if m:
            if current["pending"] is None:
                current["pending"]={"alert":when,"after20":None,"recovery":None,"duration":None}
            if m.group(1)=="20": current["pending"]["after20"]=when
        m=RECOVERY.search(row)
        if m:
            if current["pending"] is None:
                current["pending"]={"alert":None,"after20":None,"recovery":None,"duration":None}
            current["pending"].update({"recovery":when,"duration":int(m.group(1))})
            current["episodes"].append(current["pending"])
            current["pending"]=None
    output=[]
    unique=set()
    for s in sessions:
        if s["pending"]: s["episodes"].append(s["pending"])
        traces=[]
        for when,line,f in s["trace"]:
            guards=[g for g in s["guard"] if g[0]==when and g[1]==line+1]
            g=guards[0][2] if len(guards)==1 else None
            signature={k:v for k,v in f.items() if k not in ABSOLUTE}
            unique.add(json.dumps(signature,sort_keys=True))
            traces.append({
                "at":when.isoformat(timespec="milliseconds"),
                "paired_guard":len(guards)==1,
                "index_out_of_range":g[0] if g else None,
                "reference_differs":g[1] if g else None,
                "duplicate_copy":g[2] if g else None,
                "same_frame":f["frame"]==f["textura_frame"],
                "same_epoch":f["epoca_ahora"]==f["epoca_primera"],
                "signature_except_absolute_frame_epoch":signature,
            })
        first_guard=min((x[0] for x in s["guard"]),default=None)
        episodes=[]
        for e in s["episodes"]:
            episodes.append({
                "first_alert":e["alert"].isoformat(timespec="milliseconds") if e["alert"] else None,
                "20s_alert":e["after20"].isoformat(timespec="milliseconds") if e["after20"] else None,
                "recovered_at":e["recovery"].isoformat(timespec="milliseconds") if e["recovery"] else None,
                "reported_stall_s":e["duration"],
                "complete":e["recovery"] is not None,
                "alert_preceded_first_c3_guard":bool(first_guard and e["alert"] and e["alert"]<first_guard),
            })
        output.append({
            "session_start":s["start"].isoformat(timespec="milliseconds"),
            "first_line":s["first_line"],"last_line":s["last_line"],
            "driver":s["driver"],"internal_resolution":s["resolution"],"fps_cap":s["cap"],
            "c3_guards":len(s["guard"]),"pre635_traces":traces,
            "watchdog_episode_count":len(episodes),
            "recovered_count":sum(e["complete"] for e in episodes),
            "open_count":sum(not e["complete"] for e in episodes),
            "watchdog_episodes":episodes,
        })
    report={
        "stage":"PRE692_C3_WATCHDOG_READONLY","log_sha256":hashlib.sha256(raw).hexdigest(),
        "bytes":len(raw),"lines":len(lines),"session_count":len(output),
        "sessions":output,"unique_pre635_signatures":len(unique),
        "all_traces_paired":all(t["paired_guard"] for s in output for t in s["pre635_traces"]),
        "limits":{"stall_causality_unproven":True,"driver_causality_unproven":True,
                  "same_commands_not_same_texture_contents":True,
                  "watchdog_5s_20s_recovery_one_episode":True,
                  "open_episodes_are_not_assumed_recovered":True,
                  "no_apk_or_system_modified":True},
    }
    if capture is not None:
        if not capture.is_file() or capture.stat().st_size>5*1024*1024:
            raise ValueError("PRE692_CAPTURE_MISSING_OR_TOO_LARGE")
        bound=dict(CAPTURE.findall(capture.read_text(encoding="utf-8")))
        if set(bound)!={"START","END"}: raise ValueError("PRE692_CAPTURE_BOUNDARY_MISSING")
        begin=datetime.strptime(bound["START"],"%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
        end=datetime.strptime(bound["END"],"%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
        if end<=begin: raise ValueError("PRE692_CAPTURE_WINDOW_INVALID")
        report["capture_window"]={
            "start":begin.isoformat(),"end":end.isoformat(),
            "seconds":(end-begin).total_seconds(),
            "c3_guards_during":sum(begin<=datetime.fromisoformat(t["at"])<=end for s in output for t in s["pre635_traces"]),
            "watchdog_first_alerts_during":sum(bool(e["first_alert"] and begin<=datetime.fromisoformat(e["first_alert"])<=end)
                for s in output for e in s["watchdog_episodes"]),
            "absence_does_not_prove_no_microstutter":True,
        }
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--capture",type=Path)
    ap.add_argument("--output",type=Path)
    opts=ap.parse_args()
    result=audit(opts.log,opts.capture)
    payload=json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if opts.output: opts.output.write_text(payload,encoding="utf-8")
    else: print(payload,end="")
    print("PRE692_READONLY_AUDIT=PASS")
    print("PRE692_APK_AND_SYSTEM_UNCHANGED=TRUE")

if __name__=="__main__": main()
