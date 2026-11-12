# PRE703 source-only stage derived from VERIFIED PRE696 recipe.
# This runs only in the ephemeral GitHub Actions runner; no APK build or signing.
import hashlib, json, re, tempfile
from pathlib import Path
from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client
from googleapiclient.http import MediaIoBaseDownload
import http.client, time
from pre107_restore_isolated import restore
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre638_build_signed_v50_c3_two_request_diag as v50
import pre648_v50_shader_pass_counts_arm64_noapk as p648
import pre652_build_signed_v51_gpu_shader_counts_diag as p652

PIN_PRE99 = 'af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39'
PIN_V50 = '1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92'
PIN_V51 = '9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2'
PIN_BACKEND = 'b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385'
PIN_APK = '207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b'
PIN_CERT = '1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b'
CHECKS = {
  'presenter': ('nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp', [
    r'VK_PRESENT_MODE_MAILBOX_KHR', r'vkCreateSwapchainKHR',
    r'vkQueuePresentKHR', r'vkAcquireNextImageKHR',
    r'PaintAndPresentImpl', r'AcquireQueue']),
  'presenter_header': ('nativo/sdk/include/rex/ui/vulkan/presenter.h', [r'VulkanPresenter']),
  'graphics_cvar': ('nativo/app/src/nfsmw_ajustes_graficos.cpp', [
    r'nfsmw_limite_fps', r'video_mode_refresh_rate']),
  'vblank_thread': ('nativo/app/src/nfsmw_nativo_sistema.cpp', [
    r'BucleVblank', r'VdQueryVideoMode', r'Interrupcion\s*\(\s*0\s*,\s*2']),
  'backend': ('nativo/app/src/nfsmw_nativo_destinos.cpp', [r'Vk',r'vkQueueSubmit']),
  'java_args': ('android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java', [
    r'--nfsmw_limite_fps=', r'--nfsmw_resolucion_interna=']),
  'java_settings': ('android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java', [
    r'limite_fps']),
}
def resilient_pre99_download(drive, destination):
    # Retry ONLY a failed 8-MiB chunk; downloader advances on complete chunk.
    req=drive.files().get_media(fileId=BACKUP_ID, supportsAllDrives=True)
    with destination.open('wb') as stream:
        transfer=MediaIoBaseDownload(stream, req, chunksize=8*1024*1024)
        consecutive_faults=0
        while True:
            try:
                _, finished=transfer.next_chunk(num_retries=4)
            except (http.client.IncompleteRead, ConnectionResetError,
                    ConnectionAbortedError, BrokenPipeError, TimeoutError, OSError) as ex:
                consecutive_faults+=1
                if consecutive_faults>9:
                    raise RuntimeError('PRE696_PRE99_DOWNLOAD_EXHAUSTED_CHUNK_RETRIES') from ex
                print('PRE696_PRE99_CHUNK_RETRY='+str(consecutive_faults),flush=True)
                time.sleep(min(2**consecutive_faults,20))
                continue
            consecutive_faults=0
            if finished:break
    if destination.stat().st_size!=EXPECTED_BYTES:
        raise ValueError('PRE696_PRE99_SIZE_MISMATCH_AFTER_RETRIES')
def sha(b): return hashlib.sha256(b).hexdigest()
gate=json.loads(Path('docs/PRE652_V51_SIGNED_GPU_SHADER_DIAGNOSTIC_VERIFIED.json').read_text())
apk=gate.get('apk',{})
assert gate.get('status')=='SIGNED_AND_DRIVE_VERIFIED'
assert apk.get('sha256')==PIN_APK and apk.get('version_code')==51
assert apk.get('permanent_certificate_sha256')==PIN_CERT
assert EXPECTED_SHA256==PIN_PRE99 and p652.SOURCE_SHA==PIN_V51
assert p652.HEADER_SHA=='9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe'
v50.require_pre637()
result={'stage':'PRE696_V51_VULKAN_PACING_SOURCE_READONLY',
   'status':'FAIL_CLOSED', 'source_recipe':'PRE99+PRE431+PRE638+PRE648_in_memory',
   'signed_apk_sha256_from_prior_gate':PIN_APK,'signed_source_binary_equivalence_proven':False,
   'apk_built':False,'arm64_compiled':False,'apk_modified':False,
   'shaders_modified':False,'active_sources_modified':False,
   'signing_material_accessed':False,'device_settings_modified':False,
   'saves_accessed':False,'thermal_modified':False,
   'fps_gain_proven':False,'causal_pacing_attribution_proven':False,
   'files':{}}
with tempfile.TemporaryDirectory(prefix='nfsmw_pre696_') as td:
    tmp=Path(td); arc=tmp/'pre99.tar.gz'
    resilient_pre99_download(drive_client(),arc)
    digest,_,size=sha_file(arc)
    assert (digest,size)==(PIN_PRE99,EXPECTED_BYTES), 'PRE696_PRE99_HASH_MISMATCH'
    dest=tmp/'restore';dest.mkdir()
    restore(arc,dest);arc.unlink(missing_ok=True)
    root=dest/'workspace'
    replay=v46.replay_v46_sources(root,Path.cwd())
    assert replay['PRE398'].get('cheat_enabled') is True
    old=p434.ORIGINAL_STAGE
    def menu_one(folder):
        cmake=(folder/'nativo/app/CMakeLists.txt').read_text()
        assert cmake.count(v46.PRE292_REGISTER)==1
        return {'menu_registered_once':True}
    try:
        p434.ORIGINAL_STAGE=menu_one
        staged=v50.stage_v50(root)
    finally:
        p434.ORIGINAL_STAGE=old
    assert staged['pre638_v49_source_recipe_verified'] is True
    assert staged['pre638_c3_fallback_bypass'] is False
    assert staged['pre638_v49_callbacks_nitro_preserved'] is True
    assert staged['pre638_save_modified'] is False
    render=(root/'nativo/app/src/nfsmw_nativo_dibujos.cpp').read_bytes()
    backend=(root/'nativo/app/src/nfsmw_nativo_destinos.cpp').read_bytes()
    assert sha(render)==PIN_V50,'PRE696_V50_RENDERER_HASH_MISMATCH'
    assert sha(p648.patch_bytes(render))==PIN_V51,'PRE696_V51_RENDERER_INMEMORY_PATCH_MISMATCH'
    assert sha(p648.HEADER.read_bytes())==p652.HEADER_SHA,'PRE696_V51_HEADER_HASH_MISMATCH'
    assert sha(backend)==PIN_BACKEND,'PRE696_V51_BACKEND_HASH_MISMATCH'
    result['pre99_sha256']=digest
    result['renderer_v50_sha256']=sha(render)
    result['renderer_v51_inmemory_sha256']=PIN_V51
    result['backend_v51_sha256']=sha(backend)
    for label,(path,patterns) in CHECKS.items():
        b=(root/path).read_bytes()
        assert 0<len(b)<3*1024*1024 and b'\x00' not in b
        lines=b.decode('utf-8-sig').splitlines()
        hits={}
        for pattern in patterns:
            idx=[i for i,line in enumerate(lines,1) if re.search(pattern,line)]
            assert idx, 'PRE696_SOURCE_ANCHOR_ABSENT '+label+' '+pattern
            hits[pattern]={'count':len(idx),'lines':idx[:20]}
        result['files'][label]={'path':path,'sha256':sha(b),'bytes':len(b),'lines':len(lines),'anchors':hits}
        if label == 'presenter':
            assert sha(b)=='68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48', 'PRE703_V51_PRESENTER_FINGERPRINT_MISMATCH'
            isolated=Path('/tmp/nfsmw-pre703-auth-source')
            isolated.mkdir(parents=True,exist_ok=True)
            with (isolated/'vulkan_presenter.cpp').open('xb') as fp:
                fp.write(b)
result['status']='PASS_AUTHENTICATED_RECIPE_ONLY'
out=Path('/tmp/nfsmw-pre696');out.mkdir(parents=True,exist_ok=True)
(out/'PRE696_V51_SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
note=['# PRE696 — Código Vulkan/Vblank na receita autenticada V51',
  '', '**Status: PASS_AUTHENTICATED_RECIPE_ONLY**',
  '', 'PRE99 e replay V50/V51 verificados, sem igualar por bytes código reconstruído e ELF assinado.',
  '', 'Nenhuma APK, assinatura, shader, save ou configuração de sistema alterados.',
  '', 'Os seguintes arquivos contêm âncoras necessárias (linhas são indicadores lexicais, não medições):','']
for k,v in result['files'].items():
    note.append('- '+v['path']+': SHA256 '+v['sha256'])
note +=['','**Causa dos intervalos 8/25ms não demonstrada.**',
         'Próxima etapa: traços sincronizados do scheduler/apresentação antes de propor correção.']
(out/'PRE696_V51_SOURCE_AUDIT.md').write_text('\n'.join(note)+'\n')
print('PRE696_STATUS=PASS_AUTHENTICATED_RECIPE_ONLY')
print('PRE696_SOURCE_FILES='+str(len(result['files'])))
print('PRE696_SOURCE_TO_SIGNED_ELF_EQUIVALENCE=false')
print('PRE696_FPS_GAIN_PROVEN=false')
assert (Path("/tmp/nfsmw-pre703-auth-source/vulkan_presenter.cpp")).is_file()
print("PRE703_STAGE=PASS_AUTHENTICATED_V51_SOURCE_ISOLATED")
