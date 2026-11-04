#!/usr/bin/env python3
"""PRE119B: audit mounted Kaggle NFSMW build tree, read-only.

Writes a JSON report to NFSMW_Kaggle_Logs monitored by the established
nfsmw_sync_logs() hook. Does not read signing files or modify game sources.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PRE92_SHA = "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"
PRE117_SHA = "8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af"
PRE99_GRADLE_SHA = "ef570ba95703cb54df3c0e503fec6bce11aaa0f640e907208bdfb22bd8711230"
ROOT_NAME = "NFSMW_V20_BUILD_KAGGLE_ISOLADO"
REL_SOURCE = Path("nativo/sdk/src/ui/overlay/settings_overlay.cpp")
REL_GRADLE = Path("android/app/build.gradle.kts")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scan(root: Path) -> dict:
    src, gradle = root / REL_SOURCE, root / REL_GRADLE
    record = {"arvore": root.name, "fonte_existe": src.is_file(), "gradle_existe": gradle.is_file()}
    if src.is_file():
        h = sha256_file(src)
        record["fonte_sha256"] = h
        record["fonte_estado"] = "PRE92_BASE_INTACTA" if h == PRE92_SHA else (
            "PRE117_JA_APLICADA" if h == PRE117_SHA else "DIVERGENTE_NAO_APLICAR"
        )
        record["fonte_bytes"] = src.stat().st_size
    if gradle.is_file():
        ghash = sha256_file(gradle)
        record["gradle_sha256"] = ghash
        record["gradle_igual_pre99"] = ghash == PRE99_GRADLE_SHA
        # Inspect public build indicators only; never report source content.
        text = gradle.read_text(encoding="utf-8", errors="replace")
        record["pacote_esperado_referenciado"] = "io.github.nfsmwrecomp" in text
        record["assinatura_permanente_referenciada"] = "nfsmwPermanente" in text
        record["version_code_dinamico"] = bool(re.search(r"\bversionCode\s*=\s*(?!\d+\b)", text))
        record["assinatura_de_release_validada"] = False
    gen = root / "nativo"
    if gen.is_dir():
        record["cpp_nativo_total"] = sum(1 for _ in gen.rglob("*.cpp"))
        record["shaders_nfsp_total"] = sum(1 for _ in gen.rglob("*.nfsp"))
    record["alvo_selecionavel_pela_auditoria"] = (root.name == ROOT_NAME and
        record.get("fonte_estado") == "PRE92_BASE_INTACTA" and
        record.get("gradle_igual_pre99") is True)
    return record


def main() -> None:
    base = Path("/kaggle/working")
    candidates = [base / ROOT_NAME, base / "NFSMW_V20_RESTAURACAO_ISOLADA", base / "NFSMW-Recompiled-Mobile-main"]
    if base.is_dir():
        candidates += [p for p in base.iterdir() if p.is_dir() and (p / REL_SOURCE).is_file()]
    unique = {str(p.resolve()): p for p in candidates if p.is_dir()}
    reports = [scan(x) for x in sorted(unique.values(), key=lambda p: str(p))]
    selected = [x for x in reports if x.get("alvo_selecionavel_pela_auditoria")]
    status = "BASE_KAGGLE_PRE92_IDENTIFICADA_SEM_PATCH" if len(selected) == 1 else "NENHUMA_BASE_UNICA_VALIDADA_NAO_APLICAR"
    result = {
        "etapa": "PRE119_AUDIT_ARVORE_ATIVA_KAGGLE",
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "arvores": reports,
        "apk_compilado": False,
        "patch_aplicado": False,
        "arquivos_de_jogo_modificados": False,
        "assinatura_ou_senhas_acessadas": False,
        "proximo_passo": "Revisar este relatorio antes de criar backup/aplicar PRE117; assinatura precisa de preflight separado.",
    }
    # Auto-sync scans only this exact directory.
    output_dir = (base / "NFSMW_Kaggle_Logs") if base.is_dir() else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / ("NFSMW_PRE119_ARVORE_ATIVA_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f") + ".json")
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("=== NFSMW PRE119B - SOMENTE LEITURA ===")
    print("STATUS:", status)
    for r in reports:
        print("ARVORE:", r["arvore"], "SOURCE:", r.get("fonte_estado", "ausente"),
              "GRADLE_PRE99:", r.get("gradle_igual_pre99", False))
    print("RELATORIO:", out)
    print("AUTOSYNC:", "pasta monitorada" if base.is_dir() else "ambiente fora do Kaggle")
    print("Nenhum patch, build ou assinatura foi realizado.")


if __name__ == "__main__":
    main()
