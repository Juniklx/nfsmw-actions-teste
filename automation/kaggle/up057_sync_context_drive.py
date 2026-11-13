#!/usr/bin/env python3
"""UP057: fail-closed append of verified public upstream 0.5.7 audit to Drive canon; no app edits."""
import argparse, hashlib,io,os
from pathlib import Path
CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1KTJ7jJd3UkR3Q6Hlr86kL8JNoWA4JfxQ"
EXPECTED_BYTES=1380405
EXPECTED_SHA="b0f50b6508337b37a46da5f345d25b690ca4cf8897ad57f03cd010cd93b07816"
DOC=Path("docs/NFSMW_UPSTREAM_V057_V51_FEASIBILITY_AUDIT_20261112.md")
UPSTREAM_COMMIT="08b67e47219d90c0d6af8dee0a3570bb7b467e42"
def sha(b): return hashlib.sha256(b).hexdigest()
def compose(before,doc):
 if len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:raise ValueError("UP057_CANONICAL_CONTEXT_DRIFT")
 s=before.decode("utf-8")
 if "PRE728_SECONDARY_REPORT_SHA_PINNED_PASS" not in s[-1600:] or s.count("# PRE728 ")!=1:raise ValueError("UP057_PRE728_TAIL_NOT_VERIFIED")
 if "## ATUALIZAÇÃO VERIFICADA — UPSTREAM V0.5.7" in s:raise ValueError("UP057_DUPLICATE_CONTEXT")
 if not doc.startswith("# NFSMW — auditoria de viabilidade") or UPSTREAM_COMMIT not in doc or "sem" not in doc.lower():raise ValueError("UP057_AUDIT_DOC_DRIFT")
 if len(doc)>14000 or "BEGIN PRIVATE KEY" in doc or "NFSMW_ASSINATURA_CREDENCIAIS.properties" in doc:raise ValueError("UP057_DOC_SAFETY_GATE")
 intro="\n\n---\n\n## ATUALIZAÇÃO VERIFICADA — UPSTREAM V0.5.7 (2026-11-12)\n\nAuditoria somente leitura de commits e fontes públicos de victorgbd/NFSMW-Recompiled-Mobile v0.5.7, publicada em 11/11/2026. Identificou GSR1, GSR2 e Lossless Scaling Frame Generation; nenhum ganho de FPS real foi medido ou comprovado em 1920×1080 na V51. Não alterou APK, fontes privadas, chave, gráficos, saves ou térmica. A versão V51 permanece instalada como baseline, e PRE729 (viabilidade de captura observacional no aparelho) continua próximo gate principal.\n\n"
 after=(s.rstrip("\n")+intro+doc.rstrip()+"\n\n---\n").encode("utf-8")
 if len(after)<=len(before)+1000:raise ValueError("UP057_CONTEXT_APPEND_TOO_SHORT")
 if after.decode("utf-8").count("## ATUALIZAÇÃO VERIFICADA — UPSTREAM V0.5.7")!=1:raise ValueError("UP057_DUPLICATE_HEADER")
 return after
def drive():
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 keys=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
 if any(not os.environ.get(k) for k in keys):raise ValueError("UP057_GOOGLE_AUTH_MISSING")
 c=Credentials(token=None,refresh_token=os.environ[keys[0]],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ[keys[1]],client_secret=os.environ[keys[2]])
 c.refresh(Request())
 return build("drive","v3",credentials=c,cache_discovery=False)
def read(api,id):
 b=api.files().get_media(fileId=id,supportsAllDrives=True).execute(num_retries=4)
 if not isinstance(b,bytes):raise ValueError("UP057_DRIVE_NOT_BYTES")
 return b
def main():
 p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--apply",action="store_true")
 a=p.parse_args();doc=DOC.read_text(encoding="utf-8")
 if a.self_test:
  assert EXPECTED_BYTES>1000000 and len(EXPECTED_SHA)==64
  assert BACKUP_ID!=CONTEXT_ID and UPSTREAM_COMMIT in doc and doc.startswith("# NFSMW")
  print("UP057_LOCAL_AUDIT_CHECKPOINT_PASS=TRUE");return
 if not a.apply:p.error("--apply required")
 api=drive();before=read(api,CONTEXT_ID);backup=read(api,BACKUP_ID)
 if before!=backup or len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:raise ValueError("UP057_BACKUP_NOT_IDENTICAL_FAIL_CLOSED")
 after=compose(before,doc)
 from googleapiclient.http import MediaIoBaseUpload
 media=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False)
 w=api.files().update(fileId=CONTEXT_ID,media_body=media,fields="id,size",supportsAllDrives=True).execute(num_retries=4)
 if w.get("id")!=CONTEXT_ID or int(w.get("size",-1))!=len(after):raise ValueError("UP057_WRITE_METADATA_MISMATCH")
 rb=read(api,CONTEXT_ID)
 if rb!=after or sha(rb)!=sha(after) or sha(read(api,BACKUP_ID))!=EXPECTED_SHA:raise ValueError("UP057_CONTEXT_READBACK_MISMATCH")
 print("UP057_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
 print("UP057_CONTEXT_ID="+CONTEXT_ID)
 print("UP057_BACKUP_ID="+BACKUP_ID)
 print("UP057_CONTEXT_NEW_SIZE="+str(len(rb)))
 print("UP057_CONTEXT_NEW_SHA256="+sha(rb))
 print("UP057_APK_SOURCE_SIGNING_MODIFIED=FALSE")
if __name__=="__main__":main()
