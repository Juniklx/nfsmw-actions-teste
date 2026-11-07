#!/usr/bin/env python3
"""PRE358: non-secret readback of PRE357 player input source audit.

Queries only GitHub REST workflow metadata. No tokens, logs, APK bytes, signing
materials, raw build output, game assets or Drive content is published.
"""
import base64,json,os,urllib.request,urllib.error
from pathlib import Path

REPO=os.environ["GITHUB_REPOSITORY"]
TOKEN=os.environ["GITHUB_TOKEN"]
WORKFLOW="nfsmw-pre357-v43-nitro-slot-values-passive.yml"
TARGET="8d1a4a0a1f3423db3891b6d4e7b9a5171b546cfa"
HEADERS={"Authorization":f"Bearer {TOKEN}",
         "Accept":"application/vnd.github+json",
         "X-GitHub-Api-Version":"2022-11-28",
         "User-Agent":"nfsmw-pre341-nonsecret-run-observer"}
def get(uri):
    with urllib.request.urlopen(urllib.request.Request(uri,headers=HEADERS),timeout=30) as r:
        return json.load(r)
def main():
    endpoint=f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/runs?per_page=25"
    data=get(endpoint)
    runs=data.get("workflow_runs",[])
    filtered=[x for x in runs if x.get("head_sha")==TARGET]
    if not filtered:
        # retain null result instead of inventing a run ID
        summary={"stage":"PRE358_PRE357_RUN_LOOKUP","status":"NOT_FOUND","target_commit":TARGET,
                 "run_id":None,"run_status":None,"run_conclusion":None,
                 "owner_verified":False,"apk_built":False,"guest_modified":False}
    else:
        latest=sorted(filtered,key=lambda x:x.get("id",0),reverse=True)[0]
        summary={"stage":"PRE358_PRE357_RUN_LOOKUP","status":"FOUND",
                 "target_commit":TARGET,"run_id":latest["id"],
                 "run_status":latest.get("status"),
                 "run_conclusion":latest.get("conclusion"),
                 "html_url":latest.get("html_url"),
                 "owner_verified":False,"apk_built":False,
                 "guest_modified":False,
                 "note":"Run metadata only; source matches must be verified from the full audit artifact."}
    path="docs/generated/PRE358_PRE357_RUN_STATUS.json"
    uri=f"https://api.github.com/repos/{REPO}/contents/{path}"
    old=None
    try:old=get(uri).get("sha")
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    encoded=base64.b64encode((json.dumps(summary,indent=2)+"\n").encode()).decode()
    body={"message":"PRE358 publish sanitized PRE357 source audit run metadata [skip ci]",
          "branch":os.environ["GITHUB_REF_NAME"],"content":encoded}
    if old:body["sha"]=old
    req=urllib.request.Request(uri,headers=HEADERS,data=json.dumps(body).encode(),method="PUT")
    with urllib.request.urlopen(req,timeout=30) as res:
        if res.status not in (200,201):raise RuntimeError("publish failed")
    print("PRE358_STATUS",summary["status"])
    print("PRE358_RUN_ID",summary["run_id"])
    print("PRE358_RUN_STATUS",summary["run_status"])
    print("PRE358_RUN_CONCLUSION",summary["run_conclusion"])
if __name__=="__main__":main()
