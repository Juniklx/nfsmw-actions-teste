#!/usr/bin/env python3
"""PRE738: read-only reconstruction of CatchUp inheritance and RAM-only reversible candidate.

This does not patch any ISO, ZIP, APK, save, game installation or source tree.
The five attribute values may be shared with Quick Race: NOT approved for release.
"""
import argparse
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from googleapiclient.http import MediaFileUpload

from pre105_read_settings_source import drive_client
from pre733_iso_range_catchup import RemoteRange, ISO_ID, EXPECTED_SIZE, find_volume, all_files, REPORT_FOLDER, SECTOR
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash

EXPECTED_ZDIR_SHA="96c275a628f24e101f4fad9cb0531594c31effd870f64de3056c0e958e362ae6"
RESOURCE_SHA="20ab91640147f15f95b3d6e634e8164d40050a71b8dd49313a883571706d6522"
RESOURCE_SIZE=2113536
RESOURCE_LOCATIONS=((4,148738),(4,180686))
NAME_HASH=0x51EAFEC3
CATCHUP_HASH=0x10DB04E6
COLLECTION_KIND=0x8E112EB7
GAMEPLAY_CLASS=0x5CEA9D46
MAX_RECORDS=50000

def get_source(drive):
    metadata=drive.files().get(fileId=ISO_ID,fields="id,size").execute()
    if metadata.get("id")!=ISO_ID or int(metadata.get("size",0))!=EXPECTED_SIZE:
        raise ValueError("USA ISO metadata mismatch")
    reader=RemoteRange(drive._http.credentials,ISO_ID,EXPECTED_SIZE)
    base,rs,rz=find_volume(reader)
    files={name.upper():(sect,size) for name,sect,size in all_files(reader,base,rs,rz)}
    ze=files.get("NFS/ZDIR.BIN")
    if ze is None or ze[1]!=33360:raise ValueError("USA ZDIR unavailable")
    reader.seek(base+ze[0]*SECTOR)
    zdir=reader.read(ze[1])
    if hashlib.sha256(zdir).hexdigest()!=EXPECTED_ZDIR_SHA:
        raise ValueError("USA ZDIR hash mismatch")
    rows=[]
    for i,(h,arc,sector,total,size,crc) in enumerate(struct.iter_unpack("<IiIIiI",zdir)):
        if h==NAME_HASH:rows.append((arc,sector,size,crc))
    if len(rows)!=2 or [(a,s) for a,s,_,_ in rows]!=list(RESOURCE_LOCATIONS):
        raise ValueError("USA gameplay ZDIR entries not pinned")
    sources=[]
    for arc,sector,size,crc in rows:
        zz=files.get(f"NFS/ZZDATA{arc}.BIN")
        if zz is None or size!=RESOURCE_SIZE or sector*SECTOR+size>zz[1]:
            raise ValueError("Resource boundaries changed")
        reader.seek(base+zz[0]*SECTOR+sector*SECTOR)
        blob=reader.read(size)
        if hashlib.sha256(blob).hexdigest()!=RESOURCE_SHA:raise ValueError("Resource SHA changed")
        if ea_data_hash(blob)!=crc:raise ValueError("Original gameplay resource CRC mismatch")
        sources.append(blob)
    if sources[0]!=sources[1]:raise ValueError("Original duplicated gameplay resources differ")
    return sources[0],rows[0][3],reader.requests


def scan_vpak(blob):
    if blob[:4]!=b"VPAK":raise ValueError("Gameplay VPAK header absent")
    n,names_off,names_len=struct.unpack_from("<III",blob,4)
    if n!=272 or not (16+20*n<=names_off<=len(blob)-names_len):
        raise ValueError("Unexpected gameplay vault table")
    collections={}
    matches=[]
    duplicates=[]
    stats=Counter()
    for v in range(n):
        ns,bl,vl,bo,vo=struct.unpack_from("<IIIII",blob,16+20*v)
        if bo+bl>len(blob) or vo+vl>len(blob) or ns>=names_len:
            raise ValueError("Vault data out of bounds")
        zero=blob.find(b"\0",names_off+ns,names_off+names_len)
        if zero<0:raise ValueError("Vault name truncated")
        vault=blob[names_off+ns:zero].decode("ascii","replace")
        bdata=blob[bo:bo+bl]
        vdata=blob[vo:vo+vl]
        if bdata[:4]!=b"StrE" or len(bdata)<8:
            raise ValueError("Vault string header missing")
        str_end=int.from_bytes(bdata[4:8],"big")
        if not 8<=str_end<=len(bdata):raise ValueError("String chunk bounds wrong")
        names={}
        for tok in bdata[8:str_end].split(b"\0"):
            if 1<=len(tok)<=180 and all(32<=c<=126 for c in tok):
                item=tok.decode("ascii")
                names.setdefault(hash32(item),[]).append(item)
        chunks=[]
        p=0
        while p+8<=len(vdata):
            tag=vdata[p:p+4]
            if tag not in (b"DepN",b"StrN",b"DatN",b"ExpN",b"PtrN"):break
            sz=int.from_bytes(vdata[p+4:p+8],"big")
            if sz<8 or p+sz>len(vdata):raise ValueError("Malformed VLT section")
            chunks.append((tag,p,sz))
            p+=sz
        exp=[(p,sz) for tag,p,sz in chunks if tag==b"ExpN"]
        if len(exp)!=1:raise ValueError("No unique ExpN for "+vault)
        ep,esz=exp[0]
        count=int.from_bytes(vdata[ep+8:ep+12],"big")
        if count>MAX_RECORDS or count<1 or ep+12+20*count>ep+esz:
            raise ValueError("VLT ExpN count invalid")
        stats["exports"]+=count
        for j in range(count):
            export_id,kind,unused,length,off=struct.unpack_from(">IIIII",vdata,ep+12+20*j)
            if kind!=COLLECTION_KIND:continue
            if not (12<=length<=65536 and off+length<=ep):
                raise ValueError("Unexpected gameplay collection record")
            collection_hash,class_hash,parent_hash=struct.unpack_from(">III",vdata,off)
            if class_hash!=GAMEPLAY_CLASS:continue
            stat={
                "hash_hex":hex(collection_hash),
                "vault":vault,
                "name_candidates":names.get(collection_hash,[]),
                "parent_hash_hex":hex(parent_hash),
                "parent_hash":parent_hash,
                "record_size":length,
                "explicit_catchup":None,
            }
            key=CATCHUP_HASH.to_bytes(4,"big")
            rec=vdata[off:off+length]
            positions=[]
            pos=rec.find(key,12)
            while pos>=0:
                positions.append(pos)
                pos=rec.find(key,pos+1)
            if positions:
                if len(positions)!=1:raise ValueError("Multiple CatchUp keys in one collection")
                index=off+positions[0]
                # VLT Bool is 1-byte value + three trailing zero bytes.
                valuebytes=vdata[index+4:index+8]
                if valuebytes not in (b"\x00\x00\x00\x00",b"\x01\x00\x00\x00"):
                    raise ValueError("Unknown CatchUp bool representation")
                stat["explicit_catchup"]=int(valuebytes[0])
                stat["value_offset_absolute"]=vo+index+4
                matches.append({k:stat[k] for k in
                                ("vault","name_candidates","hash_hex","explicit_catchup",
                                 "value_offset_absolute","parent_hash_hex")})
            stats["collections"]+=1
            existing=collections.get(collection_hash)
            if existing is not None:
                duplicates.append({"collection_hash":hex(collection_hash),
                                   "vaults":[existing["vault"],vault]})
            else:
                collections[collection_hash]=stat
    return collections,matches,dict(stats),duplicates


def resolve(collections,collection_hash,patch=False):
    visited=set()
    node=collection_hash
    while node and node not in visited:
        visited.add(node)
        c=collections.get(node)
        if c is None:return "MISSING_PARENT"
        if c["explicit_catchup"] is not None:
            return 0 if patch else c["explicit_catchup"]
        node=c["parent_hash"]
    return "CYCLE" if node else "NO_EXPLICIT_FLAG"


def simulate(source,crc):
    collections,matches,stats,dup=scan_vpak(source)
    if len(matches)!=5 or any(m["explicit_catchup"]!=1 for m in matches):
        raise ValueError("Expected exactly five true CatchUp declarations")
    if dup:
        # The graph has one identity per collection for inheritance purposes.
        # A collision means we cannot safely claim global inheritance coverage.
        raise ValueError("Nonunique gameplay collection hashes: "+str(len(dup)))
    changing=bytes(source)
    candidate=bytearray(source)
    for m in matches:
        loc=m["value_offset_absolute"]
        if candidate[loc:loc+4]!=b"\x01\x00\x00\x00":
            raise ValueError("Preimage value mismatch")
        candidate[loc]=0
    reverted=bytearray(candidate)
    for m in matches:reverted[m["value_offset_absolute"]]=1
    if bytes(reverted)!=source:
        raise ValueError("RAM-only reversibility failed")
    # This is only an in-memory feasibility test. No candidate resource is saved.
    post_sha=hashlib.sha256(candidate).hexdigest()
    post_crc=ea_data_hash(candidate)
    examples=[]
    totals=Counter()
    for key,c in collections.items():
        if c["vault"] in {"gpcore"}:continue
        # Reconstructed gameplay vaults: career race records and Blacklist bins.
        name=c["name_candidates"][0] if c["name_candidates"] else ""
        is_race = bool(re.search(r"(circuit|sprint|drag|lap_?ko|knockout|speedtrap|p2p)",name,re.I))
        is_career_bin = c["vault"].startswith("race_bin_") and c["vault"] != "race_bin_challenge"
        if not is_race and not is_career_bin:continue
        before=resolve(collections,key,False)
        after=resolve(collections,key,True)
        totals[f"baseline_{before}"]+=1
        totals[f"candidate_{after}"]+=1
        if len(examples)<30:
            examples.append({"vault":c["vault"],"collection_name":name,
                             "base":before,"candidate":after})
    return {
        "stage":"PRE738_USA_GAMEPLAY_CATCHUP_INHERITANCE_RAM_SIMULATION",
        "status":"ANALYSIS_ONLY",
        "original_resource_sha256_verified":True,
        "original_ea_crc_verified":True,
        "original_ea_crc_hex":hex(crc),
        "resource_vault_count":272,
        "source_structure":stats,
        "catchup_declarations":matches,
        "all_declared_values_true":True,
        "ram_candidate_changed_bytes":len(matches),
        "ram_candidate_sha256":post_sha,
        "ram_candidate_ea_crc_hex":hex(post_crc),
        "ram_candidate_reversed_exact":True,
        "coverage_heuristic":dict(totals),
        "coverage_examples":examples,
        "all_career_events_verified":False,
        "quick_race_unchanged_proven":False,
        "pc_x360_behavior_parity_proven":False,
        "modification_applied":False,
        "game_asset_exported":False,
        "apk_built":False,"signing_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True,type=Path)
    args=ap.parse_args()
    drive=drive_client()
    source,crc,requests=get_source(drive)
    report=simulate(source,crc)
    report["range_requests"]=requests
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE738_EXPLICIT_CATCHUP_DECLARATIONS="+str(len(report["catchup_declarations"])))
    print("PRE738_COLLECTIONS="+str(report["source_structure"]["collections"]))
    print("PRE738_RAM_REVERSAL_OK="+str(report["ram_candidate_reversed_exact"]))
    print("PRE738_COVERAGE="+json.dumps(report["coverage_heuristic"],sort_keys=True))
    name="NFSMW_PRE738_USA_CATCHUP_INHERITANCE_RAM_ONLY.json"
    up=drive.files().create(
        body={"name":name,"parents":[REPORT_FOLDER],"mimeType":"application/json"},
        media_body=MediaFileUpload(str(args.report),mimetype="application/json"),
        fields="id,name,parents").execute()
    if up.get("name")!=name or REPORT_FOLDER not in up.get("parents",[]):
        raise ValueError("Report Drive readback mismatch")
    print("PRE738_REPORT_DRIVE_ID="+up["id"])
    print("PRE738_NO_GAMEPLAY_PATCH_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
