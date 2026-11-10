#!/usr/bin/env python3
"""PRE651 static fail-closed V51 release authorization, no APK or signing access.
Only approves reusing the *proven* V50 recipe plus PRE648 native counter.
Cannot claim GPU timing/FPS or runtime test on the Samsung.
"""
from __future__ import annotations
import argparse,ast,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path.cwd()
P638=HERE/"docs/PRE638_V50_SIGNED_RELEASE_RESULT.json"
P647=HERE/"docs/PRE647_V50_GPU_SOURCE_ANCHORS_RESULT.json"
P648=HERE/"docs/PRE648_V50_SHADER_COUNTER_ARM64_VERIFIED.json"
P649=HERE/"docs/PRE649_V50_GPU_COUNTER_HOST_OVERHEAD_VERIFIED.json"
H=HERE/"automation/kaggle/pre648_shader_pass_counter.h"
SRC648=HERE/"automation/kaggle/pre648_v50_shader_pass_counts_arm64_noapk.py"
SRC638=HERE/"automation/kaggle/pre638_build_signed_v50_c3_two_request_diag.py"
SRC652=HERE/"automation/kaggle/pre652_build_signed_v51_gpu_shader_counts_diag.py"
OUT=Path("/tmp/nfsmw-pre651/PRE651_V51_GPU_RELEASE_PREFLIGHT_NOAPK.json")

CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
HASH_HEADER="9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe"
SHA_V50="7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe"
SHA_REAL_ARM64="214ff9b9e41ab823f4a78f172199eee330f23257eb44e65a22fdb174bd2cbb1e"
SHA_STAGED="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
SHA_BASE="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def assert_eq(value,expected,reason):
    if value!=expected:
        raise ValueError(reason)

def module(path:Path):
    if not path.is_file():raise ValueError("PRE651 missing repo source "+str(path))
    return ast.parse(path.read_text(encoding="utf-8"),filename=str(path))

def consts(tree):
    result={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for t in node.targets:
                if isinstance(t,ast.Name):
                    try:result[t.id]=ast.literal_eval(node.value)
                    except (ValueError,TypeError,OverflowError):pass
    return result

def fn_body(tree,name):
    xs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    if len(xs)!=1:raise ValueError("PRE651 missing/nonunique production function "+name)
    return ast.unparse(xs[0])

def evidence():
    r638=json.loads(P638.read_text())
    r647=json.loads(P647.read_text())
    r648=json.loads(P648.read_text())
    r649=json.loads(P649.read_text())
    if not (
        r638.get("status")=="PRE638_V50_SIGNED_DIAGNOSTIC_VERIFIED"
        and r638.get("run_id")=="42748358853"
        and r638.get("run_conclusion")=="success"
        and r638.get("app",{}).get("version_code")==50
        and r638.get("app",{}).get("package_id")=="io.github.nfsmwrecomp"
        and r638.get("app",{}).get("certificate_sha256")==CERT
        and r638.get("app",{}).get("sha256")==SHA_V50
        and all(r638.get("gates",{}).get(x) is True for x in (
          "gradle_release_succeeded","signed_apk_verified",
          "permanent_certificate_verified","apk_v2_certificate_verified",
          "all_four_bmw_callbacks_exported_once","pal_usa_shaders_preserved",
          "pre398_nitro_marker_present","pre194_c3_guard_present","pre635_trace_marker_present",
          "drive_upload_success","drive_upload_remote_md5_matches"))
        and r638.get("gates",{}).get("c3_fallback_bypass") is False
        and r647.get("status")=="AUDIT_OK_SOURCE_RECIPE"
        and r647.get("github_run_id")==42762305482
        and r647.get("v50_staged_c3_sha256")==SHA_BASE
        and r647.get("limits",{}).get("exact_compiled_source_manifest_from_PRE638") is False
    ):
        raise ValueError("PRE651 V50 signed baseline or staged source gate failed")
    ee=r648.get("evidence",{})
    if not (
        r648.get("status")=="AUDIT_OK"
        and r648.get("run_id")=="42764731926"
        and r648.get("native_build_ok") is True
        and r648.get("native_cmake_ok") is True
        and r648.get("linked_library_sha256")==SHA_REAL_ARM64
        and r648.get("pre99_sha256")=="af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
        and ee.get("pre638_original_source_sha256")==SHA_BASE
        and ee.get("pre648_diagnostic_source_sha256")==SHA_STAGED
        and ee.get("pre648_counter_header_sha256")==HASH_HEADER
        and ee.get("pre648_source_exact_reverse_verified") is True
        and ee.get("pre648_counter_fixed_size_bytes")==1638400
        and ee.get("pre648_marker_linked_in_real_arm64_elf") is True
        and ee.get("pre635_c3_guard_preserved_in_arm64_elf") is True
        and ee.get("pre398_nitro_preserved_in_arm64_elf") is True
        and r648.get("apk_created") is False
        and r648.get("signing_accessed") is False
        and r648.get("shaders_modified") is False
        and r648.get("fps_gain_proven") is False
        and r648.get("signed_v50_elf_source_equivalence_verified") is False
        and r648.get("zip_sha256")=="6b472feb1ab95903d9d228e401ce44f4e8b2222bc53477732af50bf7c39aa808"
    ):
        raise ValueError("PRE651 verified PRE648 real ARM64 report mismatch")
    checks=r649.get("host_checks",{})
    if not (r649.get("status")=="AUDIT_OK_HOST_ONLY"
        and r649.get("github_run_id")==42794598045
        and r649.get("previous_gate",{}).get("PRE648_run_id")==42764731926
        and r649.get("previous_gate",{}).get("arm64_libmain_sha256")==SHA_REAL_ARM64
        and checks.get("asan_ubsan_passed") is True
        and checks.get("host_invariants_passed") is True
        and checks.get("static_observer_passed") is True
        and checks.get("estimated_counter_bytes")==1638400
        and r649.get("limits",{}).get("android_gpu_measured") is False
        and r649.get("limits",{}).get("fps_gain_proven") is False):
        raise ValueError("PRE651 PRE649 sanitized CPU-only test missing")
    return r638,r648,r649

def sources():
    if sha(H.read_bytes())!=HASH_HEADER:
        raise ValueError("PRE651 counter header not equal to approved PRE648 ARM64 header")
    header=H.read_text(encoding="utf-8")
    a=SRC648.read_text(encoding="utf-8")
    b=SRC638.read_text(encoding="utf-8")
    c=SRC652.read_text(encoding="utf-8")
    assert_eq(a.count("shader_por_pase_pre648_.Anotar("),2,"PRE651 expected only normal/emitted-sky counter sites")
    for term in (
       "std::array<uint32_t, kCasillas> casillas_{}",
       "static constexpr uint32_t kVs = 160;",
       "static constexpr uint32_t kPs = 160;",
       "static constexpr uint32_t kCategorias = 16;",
       "if (vs_mas_uno == 0 || vs_mas_uno >= kVs ||",
       "ps_mas_uno >= kPs || categoria >= kCategorias",
       "static_assert(ContadorShaderPases::kMemoriaContadores == 1638400)"
    ):
        if term not in header:raise ValueError("PRE651 counter invariant absent: "+term[:48])
    for term in ("[nativo] PRE648 GPU_SHADER10s draws=",
       "InformeShaderPre648();","shader_por_pase_pre648_.Anotar(clave.vs, clave.ps,",
       "shader_por_pase_pre648_.Anotar(c.vs_mas_uno, c.ps_mas_uno, c.categoria, true);",
       "pre648_source_exact_reverse_verified","PRE648 double application refused"):
        if term not in a:raise ValueError("PRE651 source diagnostic invariant missing: "+term[:48])
    if any(term in header for term in ("vkCmdDraw(", "vkCmdDrawIndexed(", "vkCmdBindPipeline(")):
        raise ValueError("PRE651 header unexpectedly modifies Vulkan commands")
    x=consts(module(SRC638))
    y=consts(module(SRC652))
    if not (x["VERSION"]==50 and x["EXPECTED_CERT"]==CERT
       and y["VERSION"]==51
       and y["EXPECTED_CERT"]==CERT
       and y["EXPECTED_PACKAGE"]=="io.github.nfsmwrecomp"
       and y["SOURCE_SHA"]==SHA_STAGED
       and y["HEADER_SHA"]==HASH_HEADER):
        raise ValueError("PRE651 V50/V51 version, source or signing identity mismatch")
    stage=fn_body(module(SRC652),"stage_v51")
    verify=fn_body(module(SRC652),"verify_v51")
    main=fn_body(module(SRC652),"main")
    guard=fn_body(module(SRC652),"require_pre651")
    for name,code,required in (
        ("stage",stage,("shader.stage_source(root)","SOURCE_SHA","HEADER_SHA",
           "pre638_c3_fallback_bypass","pre638_v49_callbacks_nitro_preserved")),
        ("verify",verify,("v50.verify_v50(apk, sdk, v30, progress)",
           "PRE648 GPU_SHADER10s","EXPECTED_CERT","pre398_global_nitro_present")),
        ("main",main,("require_pre651()","v49.VERSION = VERSION","v49.APK_NAME = APK_NAME",
            "v49.stage_v49 = stage_v51","v49.verify_v49 = verify_v51","v49.main()")),
        ("guard",guard,("v50.require_pre637()","GATE.is_file()","HEADER_SHA"))):
        for fragment in required:
            if fragment not in code:
                raise ValueError("PRE651 V51 builder "+name+" missing production contract "+fragment)
    # Static scope forbids introducing any new credential provider, key generation, debug
    # signing, power/thermal bypass, or shader rewrites inside the V51 wrapper.
    forbidden=("keytool","debug.keystore","signingConfigs.debug",
      "generate_key","genkey","override-status","cmd thermalservice",
      "shaders.nfsp=","vkCmdDraw(","vkCmdDrawIndexed(")
    for frag in forbidden:
        if frag in c:
            raise ValueError("PRE651 V51 wrapper contains prohibited operation "+frag)
    return {"header_sha256":sha(H.read_bytes()),
      "pre648_source_recipe_sha256":sha(SRC648.read_bytes()),
      "pre652_builder_sha256":sha(SRC652.read_bytes()),
      "production_wrapper_ast_contract":True,
      "fixed_counter_bytes":1638400,"log_interval_s":10,
      "no_new_signing_provider_found":True,
      "apk_build_path_guarded_by_pre651_report":True}

def audit(run_id:str):
    r638,r648,r649=evidence()
    safety=sources()
    return {
      "stage":"PRE651_V51_GPU_RELEASE_PREFLIGHT",
      "status":"AUDIT_OK_NO_APK",
      "github_run_id":run_id,
      "preflight_approved":True,
      "target_version_code":51,
      "package_id":"io.github.nfsmwrecomp",
      "certificate_sha256":CERT,
      "approved_source_sha256":SHA_STAGED,
      "approved_counter_header_sha256":HASH_HEADER,
      "pre648_verified_arm64_sha256":SHA_REAL_ARM64,
      "pre638_signed_v50_apk_sha256":SHA_V50,
      "pre638_signed_v50_drive_id":r638["app"]["drive_file_id"],
      "pre648_native_run_id":42764731926,
      "pre649_host_run_id":42794598045,
      "pre649_host_sanitizers":True,
      "checks":safety,
      "limits":{
        "pre638_to_pre648_byte_identical_v50_elf_proven":False,
        "source_staging_executed_in_pre651":False,
        "android_native_build_of_v51_executed":False,
        "phone_gpu_shader_counts_measured":False,
        "android_fps_gain_verified":False,
        "no_shader_spirv_optimization":True,
      },
      "signing_material_accessed":False,
      "apk_built":False,
      "user_saves_modified":False,
      "fps_gain_proven":False,
      "next_gate":"PRE652 optional signed V51 diagnostic using original certificate only, must verify full ARM64 APK and Drive upload before any phone claim",
      "timestamp_utc":datetime.now(timezone.utc).isoformat()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not args.run_id.isdigit():raise ValueError("PRE651 numeric GitHub run ID required")
        j=audit(args.run_id)
    except Exception as e:
        j={"stage":"PRE651_V51_GPU_RELEASE_PREFLIGHT","status":"FAILED",
           "error_type":type(e).__name__,
           "error_summary":str(e)[:220] if isinstance(e,ValueError) else "static preflight failure",
           "apk_built":False,"signing_material_accessed":False}
    OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for k,v in (("STATUS",j["status"]),
      ("TARGET_VERSION",j.get("target_version_code","none")),
      ("CERT_POLICY","PERMANENT_ONLY"),
      ("APK_BUILT",False),
      ("SIGNING_ACCESSED",False),
      ("ERROR_TYPE",j.get("error_type","none"))):
        print("PRE651_"+k+"="+str(v))
    return 0 if j["status"]=="AUDIT_OK_NO_APK" else 1

if __name__=="__main__":raise SystemExit(main())
