#!/usr/bin/env python3
"""PRE497 — BMW engine performance endpoint prototype, original layout in RAM.

No user-approved horsepower target exists. 5% and 10% are SYNTHETIC
REGRESSION VECTORS ONLY, NOT selected game tuning or active upgrades.
Clone 96-byte original engine block and change only TORQUE[9] float words.
No guest code, save, APK, new collection or patched asset is written.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from pathlib import Path
from datetime import datetime,timezone
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre497/report.json")
MOTOR=Path("docs/PRE495_BMW_ENGINE_ORIGINAL_DONOR_COMPARE_READONLY.json")
LAYOUT=Path("docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json")
ENGINE_BYTES=0x60
TORQUE_BASE_OFFSET=8
TEST_GAIN_BP=(0,500,1000)
def sha(x):return hashlib.sha256(x).hexdigest()

def f32(v):return struct.unpack(">f",struct.pack(">f",v))[0]
def prototype(source,bps):
    if len(source)!=ENGINE_BYTES or not isinstance(bps,int) or not 0<=bps<=1000:
        raise ValueError("Invalid synthetic engine input/gain")
    cap,count,elem,flags=struct.unpack_from(">HHHH",source,0)
    if (cap,count,elem,flags)!=(9,9,4,0):
        raise ValueError("Authentic BMW engine TORQUE[9] header differs")
    inp=list(struct.unpack_from(">9f",source,TORQUE_BASE_OFFSET))
    if any(not math.isfinite(x) or x<0 or x>20000 for x in inp):
        raise ValueError("Source BMW engine curve outside plausible bounds")
    out=bytearray(source)
    for i,v in enumerate(inp):
        value=f32(v*(1+bps/10000))
        if not math.isfinite(value):raise ValueError("Non-finite synthetic float")
        struct.pack_into(">f",out,TORQUE_BASE_OFFSET+4*i,value)
    derived=bytes(out)
    if derived[:8]!=source[:8] or derived[44:]!=source[44:]:
        raise ValueError("Modified original engine data beyond torque float array")
    if struct.unpack_from(">HHHH",derived,0)!=(cap,count,elem,flags):
        raise ValueError("Engine TORQUE header was altered")
    values=list(struct.unpack_from(">9f",derived,TORQUE_BASE_OFFSET))
    if any(not math.isclose(v,inp[i]*(1+bps/10000),rel_tol=1e-6,abs_tol=1e-5)
           for i,v in enumerate(values)):
        raise ValueError("Incorrect simulated torque scaling")
    if bps and any(v<=inp[i] for i,v in enumerate(values)):
        raise ValueError("Synthetic positive gain failed to increase all samples")
    if not bps and derived!=source:
        raise ValueError("Zero gain must be original byte-for-byte")
    allowed=set(range(TORQUE_BASE_OFFSET,TORQUE_BASE_OFFSET+9*4))
    diffs=[i for i,(a,b) in enumerate(zip(source,derived)) if a!=b]
    if any(i not in allowed for i in diffs):
        raise ValueError("Modified an unexpected engine layout byte")
    for off in (0x50,0x54,0x58,0x5c):
        if derived[off:off+4]!=source[off:off+4]:
            raise ValueError("Flywheel/max-rpm/redline/idle changed unexpectedly")
    return {"synthetic_gain_basis_points":bps,
        "synthetic_gain_percent":bps/100,
        "original_peak_torque_sample":max(inp),
        "synthetic_peak_torque_sample":max(values),
        "synthetic_curve_samples":values,
        "output_engine_layout_sha256":sha(derived),
        "engine_layout_header_unchanged":True,
        "all_non_torque_bytes_identical":True,
        "all_mutations_within_nine_torque_words":True,
        "changed_layout_bytes":len(diffs)}
def audit():
    original_meta=json.loads(MOTOR.read_text())
    phys=json.loads(LAYOUT.read_text())
    if (original_meta.get("status")!="AUDIT_OK" or
        original_meta.get("pal_vpak_sha256")!=EXPECTED_VPAK_SHA or
        phys.get("status")!="AUDIT_OK" or
        phys.get("source_sha256")!=EXPECTED_VPAK_SHA):
        raise ValueError("Source provenance PRE495/PRE477 not verified")
    stock=phys["class_models"]["engine"]["collections"]["bmwm3gtr"]
    if not stock.get("has_bounded_layout") or original_meta["stock_engine_layout_sha256"]!=stock["sha256"]:
        raise ValueError("BMW engine original class block hash changed")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if len(raw)!=697856 or sha(raw)!=EXPECTED_VPAK_SHA:
        raise ValueError("Original PAL-equivalent game attribute fingerprint differs")
    _,bl,vl,bo,vo=struct.unpack_from("<IIIII",raw,16)
    if (bl,vl,bo,vo)!=(354959,342720,128,355136):
        raise ValueError("Expected original vault geometry absent")
    off=stock["bin_base_offset"]
    if not 0<=off<=bl-ENGINE_BYTES:
        raise ValueError("Original BMW engine layout outside source BIN")
    layout=raw[bo+off:bo+off+ENGINE_BYTES]
    if sha(layout)!=stock["sha256"]:
        raise ValueError("Engine bytes do not match PRE477 SHA")
    observed=list(struct.unpack_from(">9f",layout,TORQUE_BASE_OFFSET))
    reference=original_meta["original_torque_samples_stock"]
    if len(observed)!=len(reference) or any(abs(a-b)>1e-6 for a,b in zip(observed,reference)):
        raise ValueError("PRE495 original torque samples disagree")
    tests=[prototype(layout,bps) for bps in TEST_GAIN_BP]
    if tests[0]["output_engine_layout_sha256"]!=sha(layout):
        raise ValueError("Zero-gain regression not identity")
    if tests[2]["synthetic_peak_torque_sample"]<=tests[0]["original_peak_torque_sample"]:
        raise ValueError("Synthetic test did not increase modeled torque")
    return {"stage":"PRE497_PAL_BMW_ENGINE_PARAMETRIC_TORQUE_ENDPOINT_IN_RAM",
       "status":"AUDIT_OK",
       "authenticated_source_pal_vpak_sha256":EXPECTED_VPAK_SHA,
       "authentic_bmw_engine_collection":"bmwm3gtr",
       "original_engine_layout_sha256":stock["sha256"],
       "original_engine_layout_bytes":ENGINE_BYTES,
       "stock_original_torque_curve":observed,
       "test_vectors_not_user_selected":True,
       "synthetic_test_vectors":tests,
       "estimated_hp_or_game_acceleration_proven":False,
       "new_game_collection_created":False,
       "game_loader_acceptance_verified":False,
       "user_selected_power_target":None,
       "engine_profile_finalized_for_game":False,
       "module_intended_for_dry_run_only":True,
       "original_game_asset_written":False,
       "patched_binary_published":False,
       "apk_built":False,"save_modified":False,
       "tuning_enabled":False,
       "strict_ranges_transferred":reader.total}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as ex:r={"stage":"PRE497_PAL_BMW_ENGINE_PARAMETRIC_TORQUE_ENDPOINT_IN_RAM",
       "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:250],
       "original_game_asset_written":False,"patched_binary_published":False,
       "apk_built":False,"save_modified":False,"tuning_enabled":False}
    r["run_id"]=args.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE497_STATUS",r["status"])
    print("PRE497_SAMPLE_TESTS",len(r.get("synthetic_test_vectors",[])))
    print("PRE497_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
