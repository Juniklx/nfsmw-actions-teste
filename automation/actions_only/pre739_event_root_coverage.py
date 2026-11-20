#!/usr/bin/env python3
"""PRE739: classify real career event roots vs checkpoint/shortcut records, private read-only.

Authenticated original USA gameplay VPAK; no ISO write, no patched asset persisted.
This is analysis of inheritance, not a proof of runtime career-only isolation.
"""
import argparse
import json
import re
from collections import Counter,defaultdict
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from pre105_read_settings_source import drive_client
from pre733_iso_range_catchup import REPORT_FOLDER
from pre738_gameplay_inheritance import get_source,scan_vpak,resolve

EVENT_PARENT_NAMES={
    0x2118efdb:"circuit",
    0x164a86f5:"p2p",
    0x489dacc5:"drag",
    0x1b298a8b:"lapknockout",
    0x8d217dc7:"speedtraprace",
    0x81ab0f13:"checkpointrace",
    0xd1e66b67:"race",
    0x45e21ddd:"basicrace",
}
BIN_RE=re.compile(r"race_bin_(0[1-9]|1[0-5])\Z")
ROOT_NAME_RE=re.compile(r"^race_bin_(0[1-9]|1[0-5])/(?![^/]+/)([^/]+)$")
GPCORE_DDAY_RE=re.compile(r"^16_[0-9].*")
NONRACE_SUSPECTS=("character","startgrid","checkpoint","shortcut","finishline","barrier","trigger","spawn",
                  "cop_","traffic","boss","racers","opponents","marker","position","camera")


def classify(key,c):
    vault=c["vault"]
    name=c["name_candidates"][0] if c["name_candidates"] else ""
    parent=c["parent_hash"]
    if vault == "gpcore" and GPCORE_DDAY_RE.fullmatch(name):
        return "gpcore_dday",name
    if not BIN_RE.fullmatch(vault):
        return None,None
    if name:
        m=ROOT_NAME_RE.fullmatch(name)
        if not m or not name.startswith(vault+"/"):
            return None,None
        suffix=m.group(2)
        if suffix.lower().startswith(NONRACE_SUSPECTS):
            return "unresolved_named_single_segment",name
        if parent in EVENT_PARENT_NAMES:
            return "bin_named_event_root",name
        return "bin_named_non_race_parent",name
    # No name in the vault string table: parent type must be a known race class.
    if parent in EVENT_PARENT_NAMES:
        return "bin_unnamed_event_candidate",hex(key)
    return None,None


def audit(drive):
    source,crc,range_calls=get_source(drive)
    cols,hits,stats,dups=scan_vpak(source)
    if len(hits)!=5 or dups:
        raise ValueError("Unexpected PRE738 source structure")
    table=[]
    classified=Counter()
    by_bin=defaultdict(lambda:Counter())
    missing=[]
    for key,c in cols.items():
        category,label=classify(key,c)
        if category is None:continue
        before=resolve(cols,key,False)
        after=resolve(cols,key,True)
        classified[category]+=1
        if category.endswith("event_root") or category=="gpcore_dday" or category=="bin_unnamed_event_candidate":
            by_bin[c["vault"]]["total"]+=1
            by_bin[c["vault"]]["before_"+str(before)]+=1
            by_bin[c["vault"]]["after_"+str(after)]+=1
            if before not in (0,1) or after not in (0,1):
                missing.append({"vault":c["vault"],"name":label,"reason":str(before)+"/"+str(after)})
        table.append({"category":category,"name":label,"key":hex(key),
                      "vault":c["vault"],"parent_class":EVENT_PARENT_NAMES.get(c["parent_hash"]),
                      "parent_hash":hex(c["parent_hash"]),
                      "explicit_bool":c["explicit_catchup"],
                      "baseline_effective":before,"simulated_effective":after})
    report={
        "stage":"PRE739_USA_CAREER_EVENT_ROOT_COVERAGE_READONLY",
        "status":"ANALYSIS_ONLY",
        "original_gameplay_vpak_sha_verified":True,
        "original_ea_crc_hex":hex(crc),
        "num_vaults":272,
        "num_collections":stats["collections"],
        "explicit_catchup_attributes":len(hits),
        "rule":"X360 collection in race_bin_01..15 with one path segment and known race-type parent; or unnamed direct race-type child; plus gpcore 16_*",
        "classification_counts":dict(classified),
        "candidate_event_count":sum(q["total"] for q in by_bin.values()),
        "by_vault":{k:dict(v) for k,v in sorted(by_bin.items())},
        "unresolved_effective_event_roots":missing,
        "event_table":table,
        "range_requests":range_calls,
        "all_career_events_proven":False,
        "quick_race_unchanged_proven":False,
        "blacklist_race_runtime_proven":False,
        "gameplay_modified":False,
        "apk_built":False,
        "signing_accessed":False
    }
    return report


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True,type=Path)
    o=p.parse_args()
    drive=drive_client()
    r=audit(drive)
    o.report.parent.mkdir(parents=True,exist_ok=True)
    o.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE739_EVENT_ROOT_CANDIDATES="+str(r["candidate_event_count"]))
    print("PRE739_CLASSIFICATIONS="+json.dumps(r["classification_counts"],sort_keys=True))
    print("PRE739_UNRESOLVED="+str(len(r["unresolved_effective_event_roots"])))
    print("PRE739_BY_VAULT="+json.dumps(r["by_vault"],sort_keys=True))
    name="NFSMW_PRE739_USA_CAREER_EVENT_ROOT_COVERAGE.json"
    up=drive.files().create(body={"name":name,"parents":[REPORT_FOLDER],"mimeType":"application/json"},
             media_body=MediaFileUpload(str(o.report),mimetype="application/json"),
             fields="id,name,parents").execute()
    if up.get("name")!=name or REPORT_FOLDER not in up.get("parents",[]):
        raise ValueError("Drive report verification failed")
    print("PRE739_REPORT_DRIVE_ID="+up["id"])
    print("PRE739_READ_ONLY_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
