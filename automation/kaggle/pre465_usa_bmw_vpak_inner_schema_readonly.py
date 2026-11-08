#!/usr/bin/env python3
"""PRE465: verified structural survey of original USA VPAK BIN/VLT for BMW M3 GTR.
Read-only, bounded <2 MiB strict Drive Range 206; no asset bytes in reports.
No claim that PC layout, USA data, or hashed proximity proves usable BMW upgrades.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate

OUT=Path("/tmp/nfsmw-pre465/report.json")
EXPECTED_VPAK_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
TARGETS=("BMWM3GTR","BMWM3GTRE46","m3gtre46careerstart","UpgradeSpecs",
         "eFEPartUpgradeLevels","JunkmanMod","EngineRacer","SuspensionRacer")
MASK=0xffffffff

def hash32(name):
    if not name:return 0
    v=name.encode("latin-1")
    a=b=0x9e3779b9;c=0xABCDEF00;n=len(v);i=0
    def mix(a,b,c):
        a=((a-b-c)&MASK) ^ (c>>13)
        b=((b-c-a)&MASK) ^ ((a<<8)&MASK)
        c=((c-a-b)&MASK) ^ (b>>13)
        a=((a-b-c)&MASK) ^ (c>>12)
        b=((b-c-a)&MASK) ^ ((a<<16)&MASK)
        c=((c-a-b)&MASK) ^ (b>>5)
        a=((a-b-c)&MASK) ^ (c>>3)
        b=((b-c-a)&MASK) ^ ((a<<10)&MASK)
        c=((c-a-b)&MASK) ^ (b>>15)
        return a&MASK,b&MASK,c&MASK
    while n>=12:
        a=(a+int.from_bytes(v[i:i+4],"little"))&MASK
        b=(b+int.from_bytes(v[i+4:i+8],"little"))&MASK
        c=(c+int.from_bytes(v[i+8:i+12],"little"))&MASK
        a,b,c=mix(a,b,c)
        n-=12;i+=12
    c=(c+len(v))&MASK
    suffix=v[i:]
    if len(suffix)>8:c=(c+int.from_bytes(suffix[8:],"little"))&MASK
    if len(suffix)>4:b=(b+int.from_bytes(suffix[4:8],"little"))&MASK
    if suffix:a=(a+int.from_bytes(suffix[:4],"little"))&MASK
    return mix(a,b,c)[2]

def selftest():
    known={"default":0xEEC2271A,"car":0xA13753EB,"gameplay":0x5CEA9D46}
    got={x:hash32(x) for x in known}
    if got!=known:raise ValueError("VaultLib Jenkins lookup2 self-test failed")
    return {"lookup2_canonical_test_vectors":True,
            "vectors":{k:f"{v:08x}" for k,v in got.items()}}

def chunks(blob,name):
    pos=0;entries=[]
    while pos+8<=len(blob) and len(entries)<32:
        tag=blob[pos:pos+4]
        if any(x<0x20 or x>0x7e for x in tag):break
        lbe=int.from_bytes(blob[pos+4:pos+8],"big")
        lle=int.from_bytes(blob[pos+4:pos+8],"little")
        possible=[(end,size) for end,size in (("big",lbe),("little",lle))
                  if size>=8 and size<=len(blob)-pos]
        if len(possible)!=1:
            if not possible:break
            raise ValueError("Ambiguous "+name+" chunk endianness at "+str(pos))
        endian,size=possible[0]
        entries.append({"tag":tag.decode("ascii"),"relative_offset":pos,
                        "declared_size":size,"length_endianness":endian})
        pos+=size
    tail=blob[pos:]
    return entries, {"parsed_bytes":pos,"remaining_bytes":len(tail),
                     "remaining_all_zero":not any(tail)}

def find_all(blob,needle,limit=24):
    out=[];pos=0;total=0
    while True:
        idx=blob.find(needle,pos)
        if idx<0:break
        total+=1
        if len(out)<limit:out.append(idx)
        pos=idx+1
    return total,out

def get_names(bin_data,chunks_list):
    if not chunks_list or chunks_list[0]["tag"]!="StrE":
        raise ValueError("Expected BIN string-table chunk StrE missing")
    if chunks_list[0]["relative_offset"]!=0:
        raise ValueError("First BIN string table not at start")
    end=chunks_list[0]["declared_size"]
    if not 300<=end<=len(bin_data):raise ValueError("Bad BIN string table size")
    string_blob=bin_data[8:end]
    parts=string_blob.split(b"\x00")
    allnames=[]
    for part in parts:
        if not part or len(part)>120:continue
        if any(x<32 or x>126 for x in part):continue
        allnames.append(part.decode("ascii"))
    return allnames

def audit():
    regression=selftest()
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("Authenticated USA VPAK SHA changed")
    if raw[:4]!=b"VPAK" or raw[4:8]!=b"\x01\x00\x00\x00":
        raise ValueError("VPAK header/version mismatch")
    count,string_off,string_size=struct.unpack_from("<III",raw,4)
    if count!=1:raise ValueError("Unexpected VPAK vault count")
    nameidx,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if binoff!=128 or binlen!=354959 or vltoff!=355136 or vltlen!=342720:
        raise ValueError("VPAK vault layout mismatches PRE463")
    bin_data=raw[binoff:binoff+binlen]
    vlt_data=raw[vltoff:vltoff+vltlen]
    bin_chunks,bin_tail=chunks(bin_data,"BIN")
    vlt_chunks,vlt_tail=chunks(vlt_data,"VLT")
    if not bin_chunks or bin_chunks[0]["tag"]!="StrE":
        raise ValueError("VPAK BIN StrE signature missing")
    if not vlt_chunks or vlt_chunks[0]["tag"]!="DepN":
        raise ValueError("VPAK VLT DepN signature missing")
    names=get_names(bin_data,bin_chunks)
    rx=re.compile(r"(BMW|M3GTR|UPGRADE|FEPart|Junkman|Engine|Suspension|Transmiss|Brakes|Tires|Induct|Nitro)",re.I)
    related=list(dict.fromkeys(s for s in names if rx.search(s)))
    matches={}
    for t in TARGETS:
        h=hash32(t)
        result={"lookup2_hash":f"{h:08x}"}
        for label,data in (("BIN",bin_data),("VLT",vlt_data)):
            ntxt,tpos=find_all(data,t.encode("ascii"))
            be_count,be_pos=find_all(data,h.to_bytes(4,"big"))
            le_count,le_pos=find_all(data,h.to_bytes(4,"little"))
            result[label]={"text_count":ntxt,"text_offsets":tpos,
               "hash_big_endian_count":be_count,"hash_big_endian_offsets":be_pos,
               "hash_little_endian_count":le_count,"hash_little_endian_offsets":le_pos}
        matches[t]=result
    return {
      "stage":"PRE465_USA_BMW_VPAK_BIN_VLT_STRUCTURAL_HASH_PROBE",
      "status":"AUDIT_OK","source_vpak_sha256":EXPECTED_VPAK_SHA,
      "source_edition":"USA reference only; PAL runtime not verified",
      "hash_regression":regression,"vault_name":"db",
      "bin_chunks":bin_chunks,"bin_parse_tail":bin_tail,
      "vlt_chunks":vlt_chunks,"vlt_parse_tail":vlt_tail,
      "bin_string_count_candidate":len(names),
      "bin_strings_related_to_tuning":related[:150],
      "target_name_hash_cross_reference":matches,
      "hash_presence_is_not_record_field_or_upgrade_validation":True,
      "bmw_usable_upgrade_parts_identified":False,
      "pal_catalog_validated":False,
      "safe_to_enable_bmw_tuning":False,
      "assets_exported":False,"save_touched":False,
      "signed_apk_built":False,
      "requested_byte_ranges_total":reader.total,
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"stage":"PRE465_USA_BMW_VPAK_BIN_VLT_STRUCTURAL_HASH_PROBE",
          "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
          "assets_exported":False,"save_touched":False,"signed_apk_built":False}
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE465_STATUS",result["status"],flush=True)
    print("PRE465_CHUNKS",result.get("bin_chunks"),result.get("vlt_chunks"),flush=True)
    print("PRE465_NAMED_FIELDS",len(result.get("bin_strings_related_to_tuning",[])),flush=True)
    print("PRE465_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
