#!/usr/bin/env python3
"""PRE330 reproducible read-only Nitro PRE247 destination consistency audit."""
import argparse
import collections
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

RX = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\].*?\[NFSMW_PRE247_CHEATS_DIAG\] meter_candidate=(\d+) addr=0x([0-9A-Fa-f]{8}) written_f32_bits=0x([0-9A-Fa-f]{8})')
GAP_SECONDS = 90

def analyze(lines):
    raw=[];markers=0
    for line in lines:
        if 'NFSMW_PRE247_CHEATS_DIAG' not in line: continue
        markers += 1
        m=RX.search(line)
        if not m: continue
        timestamp,site,address,value=m.groups()
        site=int(site)
        if site not in (1,2,3,4,5): continue
        raw.append((dt.datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S.%f'),site,address.upper()))
    raw.sort()
    starts=[]
    for item in raw:
        if item[1]!=1: continue
        if not starts or (item[0]-starts[-1]).total_seconds()>GAP_SECONDS:
            starts.append(item[0])
    groups=[]
    for i,start in enumerate(starts):
        next_start=starts[i+1] if i+1<len(starts) else None
        events=[v for v in raw if v[0]>=start and (next_start is None or v[0]<next_start) and (v[0]-start).total_seconds()<GAP_SECONDS]
        counts=collections.Counter(x[1] for x in events)
        addresses=sorted({x[2] for x in events})
        groups.append({
          'start_log_local':start.isoformat(sep=' '),
          'end_log_local':events[-1][0].isoformat(sep=' ') if events else None,
          'counts':{str(k):counts[k] for k in range(1,6)},
          'addresses':addresses,
          'same_destination_within_group':len(addresses)==1,
        })
    all_addresses=sorted({x[2] for x in raw})
    return {
      'stage':'PRE330_V41_NITRO_MULTIGROUP','status':'AUDIT_OK' if raw else 'NO_EVENTS',
      'all_pre247_markers':markers,'nitro_events':len(raw),'group_count':len(groups),
      'groups':groups,'nitro_addresses':all_addresses,
      'same_destination_in_all_groups':bool(groups) and len(all_addresses)==1,
      'owner_verified':False,'independent_android_processes_verified':False,
      'note':'90s gaps are temporal groups only. PRE247 logs are capped at 12 per site per process; no semantic proof of player vehicle.',
      'apk_built':False,'guest_modified':False,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--log',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    data=args.log.read_bytes()
    result=analyze(data.decode('utf8',errors='replace').splitlines())
    result['log_sha256']=hashlib.sha256(data).hexdigest()
    result['log_bytes']=len(data)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('PRE330_STATUS',result['status'])
    print('PRE330_GROUPS',result['group_count'])
    print('PRE330_NITRO_EVENTS',result['nitro_events'])
    return 0 if result['status']=='AUDIT_OK' else 1
if __name__=='__main__':raise SystemExit(main())
