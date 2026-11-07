#!/usr/bin/env python3
"""PRE289D: inspect scopes of existing GitHub OAuth refresh token without printing tokens.
Read-only: no Drive writes, no signing material, no game files, no secret rotation.
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

OUT=Path("/tmp/nfsmw-pre289d/PRE289D_EFFECTIVE_DRIVE_OAUTH_SCOPES.json")
DRIVE="https://www.googleapis.com/auth/drive"
DRIVE_FILE="https://www.googleapis.com/auth/drive.file"
DRIVE_READONLY="https://www.googleapis.com/auth/drive.readonly"
FOLDER="1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh"

def get_credential():
    creds=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
          token_uri="https://oauth2.googleapis.com/token",
          client_id=os.environ["GOOGLE_CLIENT_ID"],
          client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    creds.refresh(Request())
    return creds

def safe_error(exc):
    # Report only allow-listed OAuth error identifiers, not response bodies
    # (which can contain account identifiers and sensitive request details).
    message=str(exc).lower()
    codes=("invalid_grant","invalid_client","unauthorized_client",
           "invalid_scope","access_denied","interaction_required",
           "temporarily_unavailable","invalid_request")
    matches=[code for code in codes if code in message]
    return {"error_type":type(exc).__name__,
            "oauth_error_code":matches[0] if len(matches)==1 else "UNCLASSIFIED",
            "http_status":getattr(getattr(exc,"resp",None),"status",None)}

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    record={"stage":"PRE289D_EFFECTIVE_OAUTH_SCOPES_READONLY",
            "status":"STARTED","timestamp":datetime.now(timezone.utc).isoformat(),
            "uploads_attempted":False,"creds_modified":False,
            "apk_modified":False,"signer_accessed":False,
            "secrets_printed":False}
    try:
        c=get_credential()
        record["oauth_refresh_succeeded"]=True
        # Google's token-info service introspects the *current access token*.
        # Token never enters our output or exception messages.
        token_scopes=None
        try:
            import requests
            response=requests.get("https://oauth2.googleapis.com/tokeninfo",
                      params={"access_token":c.token},timeout=20)
            if response.status_code==200:
                token_scopes=response.json().get("scope","").split()
                record["scope_source"]="google_tokeninfo"
            else:
                record["tokeninfo_http_status"]=response.status_code
        except Exception as exc:
            record["tokeninfo_error_type"]=type(exc).__name__
        if token_scopes is None and c.granted_scopes is not None:
            token_scopes=list(c.granted_scopes)
            record["scope_source"]="oauth_refresh_response"
        if token_scopes is None:
            record["status"]="SCOPE_NOT_DETERMINED"
        else:
            token_scopes=set(token_scopes)
            record["drive_scopes"]={
               "drive_full":DRIVE in token_scopes,
               "drive_file":DRIVE_FILE in token_scopes,
               "drive_readonly":DRIVE_READONLY in token_scopes,
               "drive_metadata_readonly":"https://www.googleapis.com/auth/drive.metadata.readonly" in token_scopes,
               "drive_appdata":"https://www.googleapis.com/auth/drive.appdata" in token_scopes
            }
            record["status"]="FULL_DRIVE_SCOPE_PRESENT" if DRIVE in token_scopes else "NO_FULL_DRIVE_SCOPE_IN_CURRENT_TOKEN"
        # This is contextual only. isAppAuthorized=false alone is not proof that
        # the Drive API cannot upload when a broader OAuth scope is present.
        d=build("drive","v3",credentials=c,cache_discovery=False)
        try:
            f=d.files().get(fileId=FOLDER,fields="id,mimeType,isAppAuthorized,capabilities(canAddChildren)",
                        supportsAllDrives=True).execute()
            record["folder"]={"found":True,"can_add_children":f.get("capabilities",{}).get("canAddChildren"),
                              "is_app_authorized":f.get("isAppAuthorized")}
        except Exception as exc:
            record["folder"]={"found":False,"error":safe_error(exc)}
    except Exception as exc:
        record["status"]="OAUTH_REFRESH_OR_CLIENT_FAILED"
        record["error"]=safe_error(exc)
    OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE289D_STATUS",record["status"])
    print("PRE289D_SCOPE_SOURCE",record.get("scope_source"))
    print("PRE289D_DRIVE_SCOPES",json.dumps(record.get("drive_scopes",{})))
    print("PRE289D_FOLDER",json.dumps(record.get("folder",{})))
    print("PRE289D_UPLOAD_ATTEMPTED",False)
    print("PRE289D_AUTH_ERROR",json.dumps(record.get("error",{})))
    return 0

if __name__=="__main__":sys.exit(main())
