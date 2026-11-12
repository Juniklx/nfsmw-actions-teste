#!/usr/bin/env python3
"""PRE703: read-only inspection of V51 Vulkan source in live Google Colab workspace.

Never touches APK, keystore, compiler, sources, or Android device. Writes only a
new, timestamped aggregate report to the configured logs directory.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys

EXPECTED_CPP_SHA256 = "68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48"
REPO = Path("/content/nfsmw_build/NFSMW-Recompiled-Mobile-main")
DRIVE = Path("/content/drive/MyDrive/NFSMW_Android")
CPP_REL = Path("nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp")
HDR_REL = Path("nativo/sdk/src/ui/vulkan/vulkan_presenter.h")
QUERIES = [
    "vkEnumerateDeviceExtensionProperties",
    "VK_GOOGLE_display_timing",
    "vkGetPastPresentationTimingGOOGLE",
    "vkGetRefreshCycleDurationGOOGLE",
    "VkPresentTimesInfoGOOGLE",
    "VkPresentTimeGOOGLE",
    "vkGetDeviceProcAddr",
    "vkCreateDevice",
    "vkCreateSwapchainKHR",
    "vkQueuePresentKHR",
    "VK_KHR_swapchain",
    "VK_PRESENT_MODE_MAILBOX_KHR",
    "VK_KHR_present_id2",
]

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def anchor_index(raw):
    # Report line numbers/occurrence counts, never source text.
    text = raw.decode("utf-8", errors="strict")
    lines = text.splitlines()
    out = {}
    for token in QUERIES:
        places = [i for i, line in enumerate(lines, 1) if token in line]
        out[token] = {"count_lines": len(places), "line_numbers": places[:40], "truncated": len(places) > 40}
    return out

def candidate_gate(sha, anchors):
    # Source fingerprint is mandatory, but not evidence of matching signed ELF.
    if sha != EXPECTED_CPP_SHA256:
        return "BLOCK_SOURCE_FINGERPRINT_NOT_AUTHENTICATED"
    if not anchors["vkQueuePresentKHR"]["count_lines"]:
        return "BLOCK_REQUIRED_PRESENT_ANCHOR_MISSING"
    return "PASS_SOURCE_RECIPE_FINGERPRINT_AND_PRESENT_ANCHOR_ONLY"

def local_tests():
    fake = b"vkQueuePresentKHR(dummy);\n// VK_GOOGLE_display_timing\n"
    a = anchor_index(fake)
    assert a["vkQueuePresentKHR"]["line_numbers"] == [1]
    assert a["VK_GOOGLE_display_timing"]["line_numbers"] == [2]
    assert a["vkCreateDevice"]["count_lines"] == 0
    assert candidate_gate(digest(fake), a) == "BLOCK_SOURCE_FINGERPRINT_NOT_AUTHENTICATED"
    assert candidate_gate(EXPECTED_CPP_SHA256, a) == "PASS_SOURCE_RECIPE_FINGERPRINT_AND_PRESENT_ANCHOR_ONLY"
    missing = anchor_index(b"int main(){}\n")
    assert candidate_gate(EXPECTED_CPP_SHA256, missing) == "BLOCK_REQUIRED_PRESENT_ANCHOR_MISSING"
    try:
        anchor_index(b"\xff")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("invalid encoding must fail")
    assert len(EXPECTED_CPP_SHA256) == 64
    print("PRE703_LOCAL_SYNTHETIC=7_PASS")


def main():
    if sys.argv[1:] == ["--self-test"]:
        local_tests()
        return 0
    if sys.argv[1:]:
        print("USAGE: python3 nfsmw_pre703_v51_google_timing_source_audit.py [--self-test]", file=sys.stderr)
        return 2
    report = {
        "pre": "PRE703",
        "scope": "live_colab_source_readonly_no_build",
        "expected_authenticated_v51_cpp_sha256": EXPECTED_CPP_SHA256,
        "root": str(REPO),
        "source_to_signed_elf_identical": "UNVERIFIED",
        "driver_google_display_timing_advertised": "USER_PRE702_SUMMARY_ONLY_NOT_RAW_REVERIFIED",
        "vk_device_extension_enabled_in_installed_v51": "NOT_VERIFIED",
        "vk_presentation_timestamps_captured": False,
        "apk_or_source_or_signing_modified": False,
    }
    source = REPO / CPP_REL
    if not source.is_file():
        report["gate"] = "BLOCK_COLAB_CPP_NOT_PRESENT"
    else:
        raw = source.read_bytes()
        report["cpp_bytes"] = len(raw)
        report["cpp_sha256"] = digest(raw)
        try:
            report["cpp_anchors"] = anchor_index(raw)
            report["gate"] = candidate_gate(report["cpp_sha256"], report["cpp_anchors"])
        except UnicodeDecodeError:
            report["gate"] = "BLOCK_CPP_UTF8_DECODE_FAILED"
        header = REPO / HDR_REL
        if header.is_file():
            hr = header.read_bytes()
            report["header_bytes"] = len(hr)
            report["header_sha256"] = digest(hr)
            try:
                report["header_anchors"] = anchor_index(hr)
            except UnicodeDecodeError:
                report["header_gate"] = "HEADER_UTF8_DECODE_FAILED"
        else:
            report["header_gate"] = "HEADER_NOT_FOUND_IN_EXPECTED_LOCATION"

    # Keep all pre-existing files intact. Logs are private project metadata only.
    log_dir = DRIVE / "06_Logs_e_Medicoes"
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    fname = f"PRE703_V51_GOOGLE_TIMING_SOURCE_AUDIT_{now}.json"
    report["time_utc"] = now
    path = log_dir / fname
    if not log_dir.is_dir():
        report["report_write_status"] = "DRIVE_LOG_DIRECTORY_NOT_MOUNTED"
        print(json.dumps(report, sort_keys=True, indent=2))
        return 3
    # Exclusive creation: no rewriting existing artifacts.
    with path.open("x", encoding="utf-8") as out:
        json.dump(report, out, sort_keys=True, indent=2, ensure_ascii=False)
        out.write("\n")
    print(f"PRE703_GATE={report['gate']}")
    print(f"PRE703_SOURCE_SHA256={report.get('cpp_sha256', 'NOT_AVAILABLE')}")
    print(f"PRE703_SOURCE_MATCHES_V51_RECIPE={str(report.get('cpp_sha256') == EXPECTED_CPP_SHA256).upper()}")
    print("PRE703_RELEASE_APK_MODIFIED=FALSE")
    print("PRE703_SOURCE_MODIFIED=FALSE")
    print("PRE703_GOOGLE_TIMING_RUNTIME=NOT_TESTED")
    print(f"PRE703_LOG_PATH={path}")
    return 0 if report["gate"].startswith("PASS_") else 4


if __name__ == "__main__":
    raise SystemExit(main())
