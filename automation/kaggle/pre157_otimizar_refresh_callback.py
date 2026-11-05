#!/usr/bin/env python3
"""PRE157: guarded std::function move in verified PRE99/V31 source only."""
import argparse,hashlib,json
from pathlib import Path
REL="nativo/sdk/src/ui/presenter.cpp"
PRE99_SHA="e4db870dbeae984f9ef28957dafff6c4758471780fe1ac108b5501ebd341c208"
OLD="""    if (!RefreshGuestOutputImpl(guest_output_mailbox_writable_, frontbuffer_width,
                                frontbuffer_height, refresher, writable_properties.is_8bpc)) {"""
NEW="""    // NFSMW_PRE157: by-value callback consumed only once. Avoid extra copy.
    if (!RefreshGuestOutputImpl(guest_output_mailbox_writable_, frontbuffer_width,
                                frontbuffer_height, std::move(refresher),
                                writable_properties.is_8bpc)) {"""
def sha(b):return hashlib.sha256(b).hexdigest()
def optimize(data):
 if sha(data)!=PRE99_SHA:raise ValueError("PRE99 source hash mismatches")
 src=data.decode("utf-8")
 if src.count(OLD)!=1 or "std::move(refresher)" in src or "#include <utility>" not in src:raise ValueError("Patch anchor missing or already applied")
 return src.replace(OLD,NEW,1).encode("utf-8")
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",type=Path,required=True)
 parser.add_argument("--apply",action="store_true")
 args=parser.parse_args()
 p=args.root/REL
 raw=p.read_bytes();nextblob=optimize(raw)
 if args.apply:p.write_bytes(nextblob)
 print(json.dumps({"stage":"PRE157","sha_before":sha(raw),"sha_after":sha(nextblob),"applied":args.apply}))
