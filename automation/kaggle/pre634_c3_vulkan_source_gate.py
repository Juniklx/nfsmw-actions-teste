#!/usr/bin/env python3
"""PRE634: read-only, SHA-pinned source gate; never builds an APK.
PRE99 is historical: this does not prove byte equivalence with running V49.
"""
from __future__ import annotations
import hashlib, json, re, tarfile, tempfile, sys
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre194_c3_guard_pal_diagnostic_patch import (
    BASE_SHA, PATCHED_SHA, OLD, NEW, MARKER, patch_verified
)

OUT=Path("/tmp/nfsmw-pre634-source-audit")
TARGETS={
 "c3_pal":"workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp",
 "vulkan_presenter":"workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp",
 "ui_presenter":"workspace/nativo/sdk/src/ui/presenter.cpp",
 "command_processor":"workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp",
 "submission_tracker":"workspace/nativo/sdk/src/ui/vulkan/vulkan_submission_tracker.cpp",
 "game_system":"workspace/nativo/app/src/nfsmw_nativo_sistema.cpp",
 "sdl_app_context":"workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp",
}
PINS={
 "c3_pal":BASE_SHA,
 "vulkan_presenter":"eada548b2f683707a14ab8e6dd2c49b0381ac6542e901413fc94e5801fba74d5",
 "ui_presenter":"e4db870dbeae984f9ef28957dafff6c4758471780fe1ac108b5501ebd341c208",
 "command_processor":"b723f9480c3f4909dcc469d74ad42b154e1c700597cae4050504770700bf0058",
}
PATTERNS={
 "c3_pal":["CrearTexturaEnHilo","AplazarCopia","SubirTextura","RecogerEnlaces",
  "PrepararTextura","PlanearHuella","AntesDeEnviar","UsarRanura","epoca_subida_",
  "texturas_a_subir_","en_vuelo_[indice].copia"],
 "vulkan_presenter":["PaintAndPresentImpl","vkQueuePresentKHR","vkAcquireNextImageKHR",
  "vkQueueSubmit","vkWaitForFences","CreateSwapchainForVulkanSurface",
  "present_hilo_propio","present_perfil_pintado"],
 "ui_presenter":["PaintAndPresent","RefreshGuestOutput","present_hilo_propio"],
 "command_processor":["RefreshGuestOutput","Swap","Present"],
 "submission_tracker":["AwaitSubmissionCompletion","AcquireFenceToAdvanceSubmission"],
 "game_system":["GPU real por Swap","CostePresentar","TiempoGpu","Presentar"],
 "sdl_app_context":["SDL_WaitEvent","SDL_Delay","SDL_PumpEvents"],
}
def sha(b): return hashlib.sha256(b).hexdigest()
def landmarks(blob,items):
    rows=blob.decode("utf-8","replace").splitlines()
    return {word:{"count":sum(word in s for s in rows),
      "first_lines":[j+1 for j,s in enumerate(rows) if word in s][:12]}
      for word in items}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence={"stage":"PRE634","status":"FAIL_CLOSED",
      "date_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"PRE99 authenticated snapshot plus in-memory PRE194 patch",
      "exact_v49_source_confirmed":False, "read_only":True,
      "apk_built":False,"signing_key_accessed":False,
      "android_source_modified":False,"drive_modified":False,"files":[]}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre634_") as d:
            archive=Path(d)/"pre99.tar.gz"
            download(drive_client(),archive)
            digest,_,size=sha_file(archive)
            evidence["archive_sha256"]=digest
            evidence["archive_bytes"]=size
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 integrity failed")
            evidence["pre99_verified"]=True
            reverse={v:k for k,v in TARGETS.items()}
            blobs={}; counts={k:0 for k in TARGETS}
            with tarfile.open(archive,"r:gz") as t:
                for m in t:
                    k=reverse.get(m.name)
                    if k is None:continue
                    counts[k]+=1
                    if counts[k]!=1 or not m.isfile() or m.size>2000000:
                        raise ValueError("duplicate/unsafe member")
                    f=t.extractfile(m)
                    if f is None:raise ValueError("member unreadable")
                    b=f.read()
                    if len(b)!=m.size:raise ValueError("short source")
                    blobs[k]=b
            if any(v!=1 for v in counts.values()):
                raise ValueError("missing source")
            for k,path in TARGETS.items():
                b=blobs[k]; h=sha(b)
                if k in PINS and h!=PINS[k]:
                    raise ValueError("historical pinned source differs")
                evidence["files"].append({"role":k,"path":path,"bytes":len(b),
                    "sha256":h,"pinned":k in PINS,
                    "landmarks":landmarks(b,PATTERNS[k])})
            base=blobs["c3_pal"]
            if base.count(OLD)!=1 or MARKER in base:
                raise ValueError("C3 patch anchor not unique")
            patched=patch_verified(base)
            if (sha(patched)!=PATCHED_SHA or patched.count(MARKER)!=1
              or patched.replace(NEW,OLD,1)!=base):
                raise ValueError("PRE194 in-memory patch not reversible")
            if not all(x in OLD and x in NEW for x in (b"ApagarEnlaces",b"return false")):
                raise ValueError("C3 fail-closed branch not retained")
            evidence["c3_guard"]={"patch_sha256":sha(patched),
                "failure_guard_preserved":True,"reversible":True,
                "origin_of_second_upload":"NOT_PROVEN"}
            evidence["pacing"]={"vulkan_landmarks_found":True,
                "8_25ms_mechanism":"NOT_PROVEN",
                "physical_frame_timestamps":"NOT_AVAILABLE_IN_STATIC_AUDIT"}
            evidence["status"]="AUDIT_OK_PRE99_ONLY"
    except Exception as e:
        evidence["error_type"]=type(e).__name__
    finally:
        (OUT/"PRE634_SOURCE_AUDIT.json").write_text(
            json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE634_STATUS="+evidence["status"])
        print("PRE634_PRE99_VERIFIED="+str(evidence.get("pre99_verified",False)))
        print("PRE634_SOURCE_FILES="+str(len(evidence["files"])))
        print("PRE634_EXACT_V49_SOURCE_VERIFIED=false")
        print("PRE634_APK_BUILT=false")
        print("PRE634_SIGNING_KEY_ACCESSED=false")
    return 0 if evidence["status"]=="AUDIT_OK_PRE99_ONLY" else 1
if __name__=="__main__":
    sys.exit(main())
