#!/usr/bin/env python3
"""PRE154: read-only provenance and Vulkan presenter audit of PRE99 used for V31.
Requires Google Drive read OAuth credentials in environment; never accesses APK
release signing, restores the workspace, modifies Drive, builds or patches files.
"""
from __future__ import annotations
import hashlib, json, os, re, tarfile, tempfile, sys
from pathlib import Path
from datetime import datetime, timezone

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

FILES = [
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp",
 "workspace/nativo/sdk/src/ui/presenter.cpp",
 "workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp",
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_device.cpp",
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_submission_tracker.cpp",
 "workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp",
 "workspace/nativo/sdk/include/rex/ui/vulkan/presenter.h",
 "workspace/nativo/sdk/include/rex/ui/presenter.h",
 "workspace/nativo/app/src/nfsmw_nativo_sistema.cpp",
 "workspace/nativo/app/src/nfsmw_nativo_destinos.cpp",
 "workspace/nativo/app/src/nfsmw_nativo_destinos.h",
]
PRE136_KNOWN = {
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp":"68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48",
 "workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp":"b723f9480c3f4909dcc469d74ad42b154e1c700597cae4050504770700bf0058",
 "workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp":"f4ae379985adc2343fabde1e2eeebf048997482a8cfe17ef5839e69f8e66ffdc",
}
HISTORICAL_ZIP_HASHES = {
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp":"eada548b2f683707a14ab8e6dd2c49b0381ac6542e901413fc94e5801fba74d5",
 "workspace/nativo/sdk/src/ui/presenter.cpp":"e4db870dbeae984f9ef28957dafff6c4758471780fe1ac108b5501ebd341c208",
 "workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp":"b723f9480c3f4909dcc469d74ad42b154e1c700597cae4050504770700bf0058",
}
PATTERNS = {
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp":[
   r"PaintAndPresentImpl",r"vkQueuePresentKHR",r"vkQueueSubmit",
   r"vkAcquireNextImageKHR",r"AwaitSubmissionCompletion",r"present_perfil_pintado",
   r"present_hilo_propio",r"vkWaitForFences",r"CreateSwapchainForVulkanSurface",
   r"kTrozoPresentar",r"PintadoVolcarSiToca",r"AcquireQueue"],
 "workspace/nativo/sdk/src/ui/presenter.cpp":[
   r"PaintAndPresent",r"RefreshGuestOutput",r"ConsumeGuestOutput",
   r"present_hilo_propio",r"host_present_from_non_ui_thread",r"host_present_ignore_implicit_vsync",
   r"SetGuestOutputPaintConfig"],
 "workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp":[
   r"RefreshGuestOutput",r"Swap",r"frame_current",r"Present",r"guest_output"],
 "workspace/nativo/sdk/src/ui/vulkan/vulkan_submission_tracker.cpp":[
   r"AwaitSubmissionCompletion",r"AcquireFenceToAdvanceSubmission",r"WaitForFences"],
 "workspace/nativo/app/src/nfsmw_nativo_sistema.cpp":[
   r"TiempoGpu\(",r"GPU real por Swap",r"presentados_intervalo",r"MarcaGpuFinalNs",
   r"escala_real_ns_",r"escala_marcas_ns_",r"CostePresentar\(",r"NFSMW_INFORME_SEGUN",r"void Presentar\("],
 "workspace/nativo/app/src/nfsmw_nativo_destinos.cpp":[
   r"TiempoGpu\(",r"MarcaGpuFinalNs",r"VkQueryPool",r"vkGetQueryPoolResults",
   r"timestampPeriod",r"CostePresentar\(",r"Gpu"],
}
REPORT=Path("/tmp/nfsmw-pre154-source-audit.json")
R={"stage":"PRE154_V31_EXACT_SOURCE_PROVENANCE","status":"NOT_VALIDATED",
  "phase":"START","source_archive_verified":False,"source_modified":False,
  "apk_built":False,"release_credentials_accessed":False,"drive_modified":False,
  "files":[],"observations":[],"historical_reference_zip_is_not_assumed_exact":True}

def sha(b):return hashlib.sha256(b).hexdigest()

def excerpts(content, rxes):
    lines=content.decode("utf-8","replace").splitlines()
    compiled=[re.compile(rx,re.I) for rx in rxes]
    matches=[]
    for n,line in enumerate(lines):
        if any(rx.search(line) for rx in compiled): matches.append(n)
    # Keep targeted near-points only, with clear provenance, never full source.
    blocks=[]
    chosen=[]
    for n in matches:
        if len(chosen)>=65:break
        if any(abs(n - prev)<4 for prev in chosen):continue
        chosen.append(n)
        lo=max(0,n-2); hi=min(len(lines),n+4)
        blocks.append({"match_line":n+1,"excerpt":[
          {"line":i+1,"text":lines[i][:230]} for i in range(lo,hi)
        ]})
    return {"line_count":len(lines),"total_matching_lines":len(matches),
            "match_lines":[n+1 for n in matches[:250]],"blocks":blocks}

try:
    R["phase"]="DOWNLOAD_PRE99"
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre154_") as tmp:
        arc=Path(tmp)/"pre99.tar.gz"
        download(drive_client(),arc)
        R["phase"]="VERIFY_SNAPSHOT_HASH"
        actual,_,size=sha_file(arc)
        R["source_archive_sha256"]=actual
        R["source_archive_bytes"]=size
        if actual!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 hash/size mismatch")
        R["source_archive_verified"]=True
        R["phase"]="SELECT_SOURCES"
        with tarfile.open(arc,"r:gz",errorlevel=2) as tar:
            counts={k:0 for k in FILES}
            selected={}
            for mem in tar:
                if mem.name not in counts:continue
                counts[mem.name]+=1
                if counts[mem.name]>1 or not mem.isfile() or mem.size>2_000_000:
                    raise ValueError("duplicate or unsafe PRE99 source")
                fp=tar.extractfile(mem)
                if fp is None:raise ValueError("unreadable member")
                content=fp.read()
                if len(content)!=mem.size:raise ValueError("source short read")
                selected[mem.name]=content
            if any(counts[k]!=1 for k in FILES):raise ValueError("missing target files")
            for name in FILES:
                content=selected[name]
                row={"path":name,"sha256":sha(content),"bytes":len(content)}
                if name in PRE136_KNOWN:
                    row["pre136_status"]="MATCH" if row["sha256"]==PRE136_KNOWN[name] else "MISMATCH"
                    if row["pre136_status"]!="MATCH":raise ValueError("PRE136 source mismatch")
                if name in HISTORICAL_ZIP_HASHES:
                    row["historical_zip_match"]=(row["sha256"]==HISTORICAL_ZIP_HASHES[name])
                if name in PATTERNS:
                    row["code_audit"]=excerpts(content,PATTERNS[name])
                R["files"].append(row)
        R["phase"]="DONE"
        R["status"]="VERIFIED_PRE99_SOURCE_READ_ONLY"
        R["observations"]=[
          "PRE99 snapshot checksum and selected source SHA256 verified.",
          "Actual V31 source equivalence relies on PRE138 audited source restore and patch target scope; binary reproducibility not proven.",
          "Excerpts are directly from PRE99, not an unverified ZIP."
        ]
except Exception as ex:
    R["status"]="FAILED_NOT_VALIDATED"
    R["error_type"]=type(ex).__name__
    # Do not serialize provider errors, URLs, credentials, or arbitrary exception messages.
finally:
    R["utc"]=datetime.now(timezone.utc).isoformat()
    REPORT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE154 status="+R["status"]+" phase="+R["phase"]+" type="+str(R.get("error_type","none")))
sys.exit(0 if R["status"]=="VERIFIED_PRE99_SOURCE_READ_ONLY" else 1)
