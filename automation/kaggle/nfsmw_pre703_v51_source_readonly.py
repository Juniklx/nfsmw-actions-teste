#!/usr/bin/env python3
"""PRE703 Kaggle: source-only V51 Vulkan pacing audit. No Colab, builds or APK edits."""
import argparse
import datetime as datetime
import hashlib
import json
import os
from pathlib import Path

PIN = "68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48"
REL = Path("nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp")
TERMS = (
    "VK_GOOGLE_display_timing", "vkGetPastPresentationTimingGOOGLE",
    "vkGetRefreshCycleDurationGOOGLE", "VkPresentTimesInfoGOOGLE",
    "VkPresentTimeGOOGLE", "vkEnumerateDeviceExtensionProperties",
    "vkGetDeviceProcAddr", "vkCreateDevice", "vkCreateSwapchainKHR",
    "vkQueuePresentKHR", "VK_KHR_swapchain", "VK_PRESENT_MODE_MAILBOX_KHR",
    "VK_KHR_present_id2",
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def anchors(data):
    lines = data.decode("utf-8").splitlines()
    return {t: {"count": len(numbers), "lines": numbers[:40]}
            for t in TERMS
            for numbers in [[i for i, line in enumerate(lines, 1) if t in line]]}

def analyze(data):
    result = {"bytes": len(data), "sha256": sha(data)}
    try:
        result["anchors"] = anchors(data)
    except UnicodeDecodeError:
        return "BLOCK_SOURCE_NOT_UTF8", result
    if result["sha256"] != PIN:
        return "BLOCK_SOURCE_NOT_AUTHENTICATED_AS_V51_RECIPE", result
    if result["anchors"]["vkQueuePresentKHR"]["count"] == 0:
        return "BLOCK_PRESENT_ANCHOR_MISSING", result
    return "PASS_V51_RECIPE_SOURCE_ONLY", result

def find_sources(explicit):
    if explicit:
        root = Path(explicit).expanduser()
        candidate = root if root.name == REL.name else root / REL
        return [candidate] if candidate.is_file() else [], False
    seen = set()
    matches = []
    incomplete = False
    for base in (Path("/kaggle/working"), Path("/kaggle/input")):
        if not base.is_dir():
            continue
        for count, (folder, subdirs, filenames) in enumerate(os.walk(base, followlinks=False)):
            if count >= 15000:
                incomplete = True
                break
            subdirs[:] = [name for name in subdirs if name not in (
                ".git", ".gradle", ".cxx", "__pycache__", "node_modules",
                ".cache", "ndk", "venv", ".venv", "build", "outputs"
            )]
            if REL.name not in filenames:
                continue
            candidate = Path(folder) / REL.name
            if str(candidate).endswith(str(REL)) and not candidate.is_symlink():
                name = str(candidate)
                if name not in seen:
                    matches.append(candidate)
                    seen.add(name)
    return matches, incomplete

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--source-root", help="Existing Kaggle source root, if already restored")
    p.add_argument("--output-dir", default="/kaggle/working/NFSMW_Kaggle_Logs")
    args = p.parse_args()
    if args.self_test:
        a = anchors(b"vkQueuePresentKHR();\nVK_GOOGLE_display_timing\n")
        assert a["vkQueuePresentKHR"]["lines"] == [1]
        assert a["VK_GOOGLE_display_timing"]["lines"] == [2]
        assert a["vkCreateDevice"]["count"] == 0
        assert analyze(b"vkQueuePresentKHR();")[0].startswith("BLOCK_")
        assert analyze(b"\xff")[0] == "BLOCK_SOURCE_NOT_UTF8"
        assert len(PIN) == 64
        assert sha(b"") == hashlib.sha256(b"").hexdigest()
        print("PRE703_KAGGLE_SELFTEST=7_PASS")
        return 0
    sources, incomplete = find_sources(args.source_root)
    data = {
        "status": "PRE703_KAGGLE_READONLY",
        "expected_v51_recipe_sha256": PIN,
        "source_count": len(sources),
        "search_incomplete": incomplete,
        "source_to_signed_elf_equivalence": "UNVERIFIED",
        "pre702_google_timing": "ADVERTISED_USER_SUMMARY_NOT_RAW_REVERIFIED",
        "timing_extension_enabled_in_v51": "NOT_VERIFIED",
        "vk_present_timestamps_collected": False,
        "source_or_apk_modified": False,
        "fps_gain_proven": False,
    }
    if incomplete:
        data["gate"] = "BLOCK_DISCOVERY_INCOMPLETE"
    elif len(sources) == 0:
        data["gate"] = "BLOCK_NO_SOURCE_IN_KAGGLE"
    elif len(sources) > 1:
        data["gate"] = "BLOCK_MULTIPLE_SOURCE_CANDIDATES"
        data["candidate_hashes"] = [sha(s.read_bytes()) for s in sources]
    else:
        source = sources[0]
        data["source_path"] = str(source)
        data["gate"], data["presenter"] = analyze(source.read_bytes())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    path = Path(args.output_dir)
    path.mkdir(parents=True, exist_ok=True)
    dest = path / ("NFSMW_PRE703_KAGGLE_SOURCE_AUDIT_" + stamp + ".json")
    with dest.open("x", encoding="utf8") as out:
        json.dump(data, out, indent=2, sort_keys=True)
        out.write("\n")
    print("PRE703_ENVIRONMENT=KAGGLE")
    print("PRE703_GATE=" + data["gate"])
    print("PRE703_SOURCE_COUNT=" + str(len(sources)))
    print("PRE703_LOG=" + str(dest))
    print("PRE703_SOURCE_APK_MODIFIED=FALSE")
    return 0 if data["gate"].startswith("PASS_") else 4

if __name__ == "__main__":
    raise SystemExit(main())
