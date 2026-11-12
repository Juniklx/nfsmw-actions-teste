#!/usr/bin/env python3
"""PRE727: authenticated Drive V51 PRE656 runtime log section audit, read-only."""
import argparse, hashlib, json, os, re
from pathlib import Path
ID='1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd'
SHA='649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7'
SIZE=576129
INSTANCE='Vulkan instance API version 1.4.0. Enabled layers and extensions:'
DEVICE='Enabled Vulkan device extensions:'
INST_EXPECT=['VK_KHR_surface','VK_KHR_android_surface','VK_EXT_debug_utils']
DEV_EXPECT=['VK_EXT_extended_dynamic_state3','VK_EXT_memory_budget','VK_KHR_swapchain']
RX=re.compile(r'^\[[^\]\r\n]{12,64}\] \[info\] \[core\] \[t\d+\] \* (VK_[A-Za-z0-9_]+)$')
def analyze(raw,sha=SHA,size=SIZE):
    if not isinstance(raw,bytes) or len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:
        raise ValueError('PRE727_RAW_V51_LOG_SHA_OR_SIZE_DRIFT')
    lines=raw.decode('utf-8').splitlines()
    def section(header):
        hits=[i for i,s in enumerate(lines) if header in s]
        if len(hits)!=1:raise ValueError('PRE727_VULKAN_SECTION_COUNT_DRIFT')
        names=[]
        for line in lines[hits[0]+1:hits[0]+35]:
            m=RX.fullmatch(line)
            if not m:break
            names.append(m.group(1))
        if len(names)!=len(set(names)):raise ValueError('PRE727_DUPLICATE_VK_EXTENSION')
        return hits[0]+1,names
    il,iv=section(INSTANCE);dl,dv=section(DEVICE)
    if not (il<dl and iv==INST_EXPECT and dv==DEV_EXPECT):
        raise ValueError('PRE727_V51_EXTENSION_LOG_SCHEMA_DRIFT')
    if b'VK_GOOGLE_display_timing' in raw:
        raise ValueError('PRE727_GOOGLE_TIMING_TOKEN_PRESENT')
    return dict(stage='PRE727_V51_REAL_APP_LOG_VULKAN_EXTENSION_SECTION_AUDIT',
      status='PASS_PRE727_V51_REAL_APP_REPORTED_VULKAN_EXTENSIONS',
      source_kind='REAL_V51_PRE656_ANDROID_APP_LOG_ARCHIVED_ON_DRIVE',
      source_file_id=ID,source_sha256=sha,source_bytes=size,
      source_total_lines=len(lines),source_session_date='2026-11-10',
      gpu='Samsung Xclipse 940',
      instance_header_line=il,device_header_line=dl,
      instance_extensions_reported_enabled=iv,device_extensions_reported_enabled=dv,
      instance_extensions_count=len(iv),device_extensions_count=len(dv),
      VK_GOOGLE_display_timing_reported_enabled_in_this_session=False,
      VK_GOOGLE_display_timing_anywhere_in_log=False,
      PRE702_device_advertised_GOOGLE_timing_user_report=True,
      distinction='PRE702_ADVERTISED_VS_PRE656_APP_LOG_REPORTED_ENABLED',
      app_log_is_not_independent_vulkan_api_interception=True,
      driver_vkCreateDevice_actual_pointer_contents='NOT_VERIFIED',
      runtime_requested_extension_map='NOT_VERIFIED',
      all_other_v51_sessions='NOT_VERIFIED',
      source_to_signed_elf_equivalence='UNVERIFIED',
      kaggle_executed=False,
      why_kaggle_not_needed='LOG_ONLY_VERIFICATION_NO_SOURCE_OR_BUILD',
      original_app_log_exported=False,raw_app_log_lines_exported=False,
      apk_modified=False,apk_compiled=False,signing_material_accessed=False,
      shaders_modified=False,fps_gain_proven=False)
def test():
    tag='[2026-11-10 08:54:09.247] [info] [core] [t14529] '
    sample=(tag+INSTANCE+'\n'+''.join(tag+'* '+n+'\n' for n in INST_EXPECT)
      +tag+'some other line\n'+tag+DEVICE+'\n'
      +''.join(tag+'* '+n+'\n' for n in DEV_EXPECT)+tag+'end\n').encode()
    a=analyze(sample,hashlib.sha256(sample).hexdigest(),len(sample))
    assert a['instance_extensions_reported_enabled']==INST_EXPECT
    assert a['device_extensions_reported_enabled']==DEV_EXPECT
    assert a['VK_GOOGLE_display_timing_reported_enabled_in_this_session'] is False
    for bad in [sample+b'garbage',sample.replace(b'VK_KHR_swapchain',b'VK_GOOGLE_display_timing')]:
        try:analyze(bad,hashlib.sha256(sample).hexdigest(),len(sample))
        except ValueError:pass
        else:raise AssertionError('PRE727_NEGATIVE_CANARY_UNSAFE')
    print('PRE727_SYNTHETIC_PARSER_PASS=TRUE')
def fetch():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    keys=('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET')
    if not all(os.environ.get(k) for k in keys):raise ValueError('PRE727_MISSING_DRIVE_ENV')
    c=Credentials(token=None,refresh_token=os.environ[keys[0]],
      token_uri='https://oauth2.googleapis.com/token',
      client_id=os.environ[keys[1]],client_secret=os.environ[keys[2]])
    c.refresh(Request())
    return build('drive','v3',credentials=c,cache_discovery=False).files().get_media(
      fileId=ID,supportsAllDrives=True).execute(num_retries=4)
def main():
    a=argparse.ArgumentParser()
    a.add_argument('--self-test',action='store_true')
    a.add_argument('--apply',action='store_true')
    a.add_argument('--out',type=Path)
    p=a.parse_args()
    if p.self_test:return test()
    if not p.apply or not p.out:a.error('--apply and --out required')
    data=fetch()
    if not isinstance(data,bytes):raise ValueError('PRE727_RAW_LOG_MISSING')
    result=analyze(data)
    p.out.parent.mkdir(parents=True,exist_ok=True)
    p.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PRE727_REAL_V51_LOG_SHA256_VERIFIED=TRUE')
    print('PRE727_V51_REPORTED_ENABLED_INSTANCE_EXTENSIONS='+str(result['instance_extensions_count']))
    print('PRE727_V51_REPORTED_ENABLED_DEVICE_EXTENSIONS='+str(result['device_extensions_count']))
    print('PRE727_GOOGLE_DISPLAY_TIMING_NOT_ENABLED_IN_THIS_LOG=TRUE')
    print('PRE727_V51_REAL_LOG_AUDIT_PASS=TRUE')
if __name__=='__main__':main()
