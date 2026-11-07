#!/usr/bin/env python3
"""PRE289C: read-only Google Drive credential/folder/quota diagnosis.
No upload, no artifact download, no file creation, no secret values or emails.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from pre105_read_settings_source import drive_client
from pre289_build_signed_v38_bmw_passive import DEST_FOLDER

OUT=Path("/tmp/nfsmw-pre289c/PRE289C_DRIVE_403_READONLY.json")
EXPECTED_APK_BYTES=50_000_000
ALLOWED_REASONS={
    "insufficientFilePermissions","storageQuotaExceeded","rateLimitExceeded",
    "userRateLimitExceeded","dailyLimitExceeded","domainPolicy",
    "appNotAuthorizedToFile","forbidden","insufficientPermissions",
    "teamDriveMembershipRequired","numChildrenInNonRootLimitExceeded",
    "fileNotFound","notFound"
}

def safe_error(exc:Exception):
    status=getattr(getattr(exc,"resp",None),"status",None)
    reasons=[]
    if isinstance(exc,HttpError):
        try:
            payload=json.loads(exc.content.decode("utf-8","replace"))
            reasons=[e.get("reason","") for e in payload.get("error",{}).get("errors",[]) if isinstance(e,dict)]
            details=payload.get("error",{}).get("details",[])
            for item in details:
                if isinstance(item,dict) and isinstance(item.get("reason"),str):
                    reasons.append(item["reason"])
        except (ValueError,UnicodeDecodeError,AttributeError):pass
    return {"http_status":status,"error_type":type(exc).__name__,
            "reason_codes":[x if x in ALLOWED_REASONS else "OTHER" for x in sorted(set(reasons))]}

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE289C_DRIVE_403_READONLY_DIAGNOSTIC",
       "status":"STARTED","uploads_attempted":False,"files_modified":False,
       "secrets_emitted":False,"timestamp":datetime.now(timezone.utc).isoformat()}
    try:
        drive=drive_client()
        r["oauth_refresh_succeeded"]=True
        try:
            folder=drive.files().get(fileId=DEST_FOLDER,
                fields="id,mimeType,driveId,capabilities(canAddChildren,canListChildren,canReadRevisions),isAppAuthorized",
                supportsAllDrives=True).execute()
            r["folder"]={"found":True,
                "is_folder":folder.get("mimeType")=="application/vnd.google-apps.folder",
                "can_add_children":folder.get("capabilities",{}).get("canAddChildren"),
                "can_list_children":folder.get("capabilities",{}).get("canListChildren"),
                "is_app_authorized":folder.get("isAppAuthorized"),
                "is_shared_drive":bool(folder.get("driveId"))}
        except Exception as exc:
            r["folder"]={"found":False,"error":safe_error(exc)}
        try:
            about=drive.about().get(fields="storageQuota(limit,usage,usageInDrive),user(permissionId)").execute()
            quota=about.get("storageQuota",{})
            limit=quota.get("limit")
            used=quota.get("usage")
            free=None
            if limit is not None and used is not None:
                free=max(0,int(limit)-int(used))
            r["quota"]={"available":bool(quota),
                "limit_known":limit is not None,
                "enough_for_v38":None if free is None else free>=EXPECTED_APK_BYTES,
                "quota_at_or_above_limit":None if free is None else free==0}
            r["account_permission_id_present"]=bool(about.get("user",{}).get("permissionId"))
        except Exception as exc:
            r["quota"]={"error":safe_error(exc)}
        folder=r.get("folder",{})
        if folder.get("can_add_children") is False:
            r["status"]="FOLDER_WRITE_DENIED"
        elif folder.get("is_app_authorized") is False:
            r["status"]="APP_ACCESS_NOT_AUTHORIZED"
        elif r.get("quota",{}).get("quota_at_or_above_limit") is True:
            r["status"]="STORAGE_QUOTA_FULL"
        elif folder.get("can_add_children") is True and r.get("quota",{}).get("enough_for_v38") is True:
            r["status"]="READONLY_CHECKS_OK_403_REASON_STILL_UNKNOWN"
        else:
            r["status"]="INCONCLUSIVE_REVIEW_DETAIL"
    except Exception as exc:
        r["status"]="AUTH_OR_CLIENT_ERROR"
        r["error"]=safe_error(exc)
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE289C_STATUS",r["status"])
    print("PRE289C_FOLDER",json.dumps(r.get("folder",{}),ensure_ascii=False))
    print("PRE289C_QUOTA",json.dumps(r.get("quota",{}),ensure_ascii=False))
    print("PRE289C_UPLOAD_ATTEMPTED",False)
    return 0

if __name__=="__main__":sys.exit(main())
