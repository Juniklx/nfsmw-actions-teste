#!/usr/bin/env python3
"""PRE688: verify user-provided private phone logs without touching game, APK or signature."""
import datetime,hashlib,io,json,os,re,tempfile,zipfile
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
PINS={
 'status':('1RmAoFCEeO057KmraclfDeryoCDusEkhr',320,'30cc15952b72b265c014505cb21cfbe9c7ba8df7ddd92cbdb206fd63afeb69e6'),
 'sf':('1gHbmHPjp_2Wji9sVWrv49-apZYulxhkv',1348,'a8a004c19613fd381cb612e68dc8623ae186bac14c9e934c44d8db6fdc41da63'),
 'log':('15xO-DGiB-rOUL-TqD3BtCr0arC9ff5YH',1635318,'ec8cc88753c6dad79d28bc3550316007119f8f4639ecbcb985dcd2470c90229d'),
}
PRIVATE_DIR='1yw1Z83O0d83CoQccjYREYfhxAF17eHD-'
def sha(b):return hashlib.sha256(b).hexdigest()
def get(d,file_id):
    b=io.BytesIO();download=MediaIoBaseDownload(b,d.files().get_media(fileId=file_id),chunksize=4*1024*1024)
    done=False
    while not done:_,done=download.next_chunk()
    return b.getvalue()
def validate(b):
    for key,(_,size,digest) in PINS.items():
        if len(b[key])!=size or sha(b[key])!=digest:raise ValueError('PRE688_BAD_PIN_'+key)
    status=b['status'].decode();sf=b['sf'].decode();log=b['log'].decode('utf-8','replace')
    if not all(x in status for x in ('PRE688_CAPTURE_VALIDATION=PASS_SINGLE_SURFACEVIEW_LAYER','PRE688_NO_SHEVERY_APP_INVOCATION=TRUE')):
        raise ValueError('PRE688_UNSUCCESSFUL_CAPTURE')
    markers=('COLLECTION_START=2026-11-11T00:34:18-0300','COLLECTION_END=2026-11-11T00:35:48-0300',
             'PRE688_NFSMW_SURFACEVIEW_LAYERS=1','PRE688_LABELED_PRESENT_HISTOGRAMS=1',
             'present2present histogram is as below:','displayRefreshRate = 120 fps')
    if any(m not in sf for m in markers):raise ValueError('PRE688_SF_FORMAT_CHANGED')
    if 'totalFrames = 5412' not in sf or 'averageFPS = 62.226' not in sf:
        raise ValueError('PRE688_SF_COUNTERS_CHANGED')
    bins={int(t):int(n) for t,n in re.findall(r'(\d+)ms=(\d+)',sf)}
    if sum(bins.values())!=5412 or any(bins.get(t)!=n for t,n in {8:597,16:4184,24:307,25:262}.items()):
        raise ValueError('PRE688_HIST_NOT_PINNED')
    rate=1000*5412/sum(t*n for t,n in bins.items())
    if round(rate,3)!=62.226:raise ValueError('PRE688_RATE_CANNOT_REPRODUCE')
    if '[2026-11-11 00:32:33.214]' not in log:raise ValueError('PRE688_SECOND_SESSION_NOT_FOUND')
    session=log.split('[2026-11-11 00:32:33.214]',1)[1]
    if 'VulkanPresenter: Created 1920x1080 swapchain' not in session or 'has become outdated' in session:
        raise ValueError('PRE688_NEW_GAME_SESSION_SURFACE_MISMATCH')
    if '00:36:36.144' not in session or '[vigilante] 5 s sin que se mueva' not in session:
        raise ValueError('PRE688_WATCHDOG_SIGNAL_MISSING')
    if '20 s sin que se mueva' in session:raise ValueError('PRE688_NEW_WATCHDOG_PATTERN_REVIEW')
    c2=re.findall(r'^\[2026-11-11 (\d\d:\d\d:\d\d\.\d{3})\].*C2: intervalos entre Swaps: (.*?); peor fotograma ([\d.]+) ms',log,re.M)
    four=[]
    for t,blob,_ in c2:
        if '00:34:18'<t<'00:35:48':
            four.append({x.rsplit(' ',1)[0]:int(x.rsplit(' ',1)[1]) for x in blob.split(' | ')})
    if len(four)!=4:raise ValueError('PRE688_NOT_FOUR_GAME_WINDOWS')
    totals={k:sum(w[k] for w in four) for k in four[0]}
    if sum(totals.values())!=4800 or totals['15-18']!=4685 or totals['18-25']!=92 or totals['<15 ms']!=23:
        raise ValueError('PRE688_C2_TOTALS_NOT_MATCHED')
    if any(v for k,v in totals.items() if k not in ('15-18','18-25','<15 ms')):
        raise ValueError('PRE688_C2_LONG_SWAPS_FOUND')
    return {
     'gate':'PRE688_REAL_S24FE_SURFACEFLINGER_ENGINE','status':'PASS_CAPTURE__JITTER_PRESENT__POST_CAPTURE_5S_WATCHDOG_CAUSE_UNKNOWN',
     'run_id':os.environ.get('GITHUB_RUN_ID'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'inputs':{k:{'drive_id':v[0],'bytes':v[1],'sha256':v[2]} for k,v in PINS.items()},
     'sf':{'from':'2026-11-11T00:34:18-0300','to':'2026-11-11T00:35:48-0300','display_hz':120,
            'total_frames':5412,'average_fps_reported':62.226,'average_fps_from_binned_intervals':round(rate,3),
            '8ms':597,'16ms':4184,'24_to_25ms':569,'8_and_24_to_25ms':1166,
            'nonideal_8_24_25_percent':round(100*1166/5412,3)},
     'engine':{'internal_resolution':'1920x1080','fps_cap':60,
               'four_c2_windows_count':4800,'four_c2_bins':totals,
               'surface_outdated_current_session':0,'watchdog_5s_after_capture':'00:36:36.144',
               'watchdog_20s_in_new_session':False,'old_C3_guard_still_triggers':True},
     'limits':{'histogram_has_ordered_presentation_timestamps':False,
               'stutter_cause_proven':False,'watchdog_caused_by_shevery_proven':False,
               'possible_post_capture_app_switch_undetermined':True,
               'fps_improved':False,'new_apk':False}}
def main():
    names=('GOOGLE_REFRESH_TOKEN','GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET')
    if any(not os.environ.get(k) for k in names):raise ValueError('PRE688_OAUTH_SECRET_NAME_MISSING')
    cred=Credentials(token=None,refresh_token=os.environ[names[0]],client_id=os.environ[names[1]],
       client_secret=os.environ[names[2]],token_uri='https://oauth2.googleapis.com/token')
    cred.refresh(Request())
    d=build('drive','v3',credentials=cred,cache_discovery=False)
    report=validate({k:get(d,v[0]) for k,v in PINS.items()})
    with tempfile.TemporaryDirectory() as td:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
        path=Path(td)/('NFSMW_PRE688_ACTIONS_VERIFIED_'+stamp+'.zip')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('PRE688_REPORT.json',json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False))
            z.writestr('PRE688_README.md',
                 'PRE688 validated original private phone logs. No public game log or private settings.\\n'
                 'Capture PASS; SurfaceFlinger pacing uneven; watchdog after window, cause unknown.\\n'
                 'No build, APK, shader, signing, frame pacing fix or FPS gain.\\n')
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:raise ValueError('PRE688_BAD_REPORT_CRC')
        item=d.files().create(body={'name':path.name,'parents':[PRIVATE_DIR]},
          media_body=MediaFileUpload(str(path),mimetype='application/zip',resumable=True),fields='id,size').execute()
        if item.get('size')!=str(path.stat().st_size) or sha(get(d,item['id']))!=sha(path.read_bytes()):
            raise ValueError('PRE688_PRIVATE_REPORT_READBACK_SHA_MISMATCH')
    print('PRE688_PRIVATE_INPUTS_SHA256=PASS')
    print('PRE688_REAL_5412_PRESENTATIONS=PASS')
    print('PRE688_NATIVE_C2_4800_SWAPS=PASS')
    print('PRE688_CAPTURE_SUCCESS=TRUE')
    print('PRE688_POST_CAPTURE_WATCHDOG=OBSERVED_CAUSE_UNKNOWN')
    print('PRE688_PRIVATE_DRIVE_REPORT_READBACK=PASS')
    print('PRE688_APK_OR_FPS_IMPROVEMENT=NONE')
if __name__=='__main__':main()
