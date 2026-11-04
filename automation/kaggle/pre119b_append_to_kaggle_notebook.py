#!/usr/bin/env python3
"""Append PRE119B to the existing user's Kaggle notebook, without executing.

Only prepares an exact single-cell addition for 'kaggle kernels push --no-run'.
Preserves existing cells, metadata, settings and notebook ID byte-for-byte at
the parsed JSON level; produces a sanitized SHA-based report. Never handles
signing keys or Google OAuth credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_KERNEL = "juniklx/nfsmw"
MARKER = "# NFSMW_PRE119B_AUDITORIA_AUTOSYNC_V1"
SCRIPT = Path("automation/kaggle/pre119b_auditar_arvore_autosync.py")
MAX_NOTEBOOK_BYTES = 18 * 1024 * 1024


def canonical_cells(nb: dict) -> list[dict]:
    return [{"cell_type": c.get("cell_type"), "source": c.get("source", [])}
            for c in nb["cells"]]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_string(cell: dict) -> str:
    raw = cell.get("source", "")
    return "".join(raw) if isinstance(raw, list) else str(raw)


def prepare(base: Path) -> dict:
    metafile = base / "kernel-metadata.json"
    if not metafile.is_file():
        raise ValueError("Kaggle metadata missing")
    meta_data = metafile.read_bytes()
    meta = json.loads(meta_data.decode("utf-8"))
    if meta.get("id") != EXPECTED_KERNEL or meta.get("kernel_type") != "notebook":
        raise ValueError("Unexpected Kaggle notebook identity/type: refusing to edit")
    code_file = meta.get("code_file")
    if not isinstance(code_file, str) or not code_file.endswith(".ipynb"):
        raise ValueError("Expected ipynb metadata code_file")
    notebook_path = (base / code_file).resolve()
    if notebook_path.parent != base.resolve():
        raise ValueError("Unsafe notebook path in Kaggle metadata")
    original_bytes = notebook_path.read_bytes()
    if len(original_bytes) > MAX_NOTEBOOK_BYTES:
        raise ValueError("Notebook unexpectedly large")
    nb = json.loads(original_bytes.decode("utf-8"))
    if nb.get("nbformat") != 4 or not isinstance(nb.get("cells"), list):
        raise ValueError("Not an nbformat4 notebook")
    if not nb["cells"]:
        raise ValueError("Empty notebook, refusing to overwrite")
    for c in nb["cells"]:
        if c.get("cell_type") not in ("code", "markdown", "raw"):
            raise ValueError("Unexpected existing cell type")
    before_cells = canonical_cells(nb)
    existing = [i for i, cell in enumerate(nb["cells"])
                if MARKER in source_string(cell)]
    if len(existing) > 1:
        raise ValueError("Duplicate PRE119B cells detected")
    report = {
        "kernel": EXPECTED_KERNEL,
        "original_notebook_sha256": sha(original_bytes),
        "original_metadata_sha256": sha(meta_data),
        "cell_count_before": len(nb["cells"]),
        "pre119b_cell_present_before": bool(existing),
        "existing_cells_preserved": True,
        "kaggle_original_version_backup": "Kaggle notebook revision history",
        "game_workspace_modified": False,
        "code_executed": False,
        "signing_credentials_accessed": False,
    }
    script = SCRIPT.read_text(encoding="utf-8")
    if not script.startswith("#!/usr/bin/env python3") or 'def main() -> None:' not in script:
        raise ValueError("Unexpected PRE119B source, refusing to embed")
    # Import future, definitions and report creation are all within this cell.
    # On the next user-initiated notebook run, the final cell generates the
    # report; if nfsmw_sync_logs() was initialized, it syncs to Google Drive.
    auto_sync = (
        "\n# PRE119B: sincronizar somente o novo relatório, se o hook já estiver ativo.\n"
        "_nfsmw_pre119b_sync = globals().get('nfsmw_sync_logs')\n"
        "if callable(_nfsmw_pre119b_sync):\n"
        "    try:\n"
        "        _nfsmw_pre119b_result = _nfsmw_pre119b_sync()\n"
        "        print('PRE119B: hook de sincronização executado')\n"
        "    except Exception as _nfsmw_pre119b_exc:\n"
        "        print('PRE119B: sincronização não confirmada -', type(_nfsmw_pre119b_exc).__name__)\n"
        "else:\n"
        "    print('PRE119B: hook nfsmw_sync_logs não ativo nesta execução')\n"
    )
    code = MARKER + "\n" + script + auto_sync
    code_hash = sha(code.encode("utf-8"))
    if existing:
        if len(existing) != 1 or existing[0] != len(nb["cells"]) - 1:
            raise ValueError("PRE119B already present but is not last cell")
        if source_string(nb["cells"][-1]) != code:
            raise ValueError("Existing PRE119B cell is not identical to current source")
        report["update_type"] = "ALREADY_PRESENT_IDENTICAL"
        report["appended_cell"] = False
    else:
        nb["cells"].append({
            "cell_type": "code",
            "id": "nfsmw-pre119b-audit",
            "metadata": {"tags": ["nfsmw-pre119b", "read-only"]},
            "execution_count": None,
            "outputs": [],
            "source": code.splitlines(keepends=True),
        })
        report["update_type"] = "APPENDED_ONE_READONLY_CELL"
        report["appended_cell"] = True
    if canonical_cells(nb)[:len(before_cells)] != before_cells:
        raise ValueError("Existing cell source changed unexpectedly")
    if len(nb["cells"]) != len(before_cells) + (0 if existing else 1):
        raise ValueError("Wrong cell delta")
    if metafile.read_bytes() != meta_data:
        raise ValueError("Kaggle metadata changed unexpectedly")
    new_bytes = (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    notebook_path.write_bytes(new_bytes)
    report.update({
        "cell_count_after": len(nb["cells"]),
        "prepared_notebook_sha256": sha(new_bytes),
        "pre119b_cell_source_sha256": code_hash,
        "metadata_unchanged": metafile.read_bytes() == meta_data,
        "notebook_code_file": code_file,
        "push_requires_no_run": True,
    })
    return report


def check(base: Path, expected_hash: str, expected_count: int) -> dict:
    meta = json.loads((base / "kernel-metadata.json").read_text(encoding="utf-8"))
    if meta.get("id") != EXPECTED_KERNEL:
        raise ValueError("Unexpected notebook identity after Kaggle pull")
    path = base / meta["code_file"]
    nb = json.loads(path.read_text(encoding="utf-8"))
    if len(nb["cells"]) != expected_count:
        raise ValueError("Kaggle notebook cell count differs after push")
    last = source_string(nb["cells"][-1])
    if MARKER not in last or sha(last.encode("utf-8")) != expected_hash:
        raise ValueError("PRE119B cell missing or changed in Kaggle readback")
    return {
        "kaggle_pull_readback_confirmed": True,
        "cell_count_verified": len(nb["cells"]),
        "pre119b_cell_source_sha256_verified": True,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("prepare", "check"), required=True)
    p.add_argument("--folder", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    reportfile = Path(args.report)
    reportfile.parent.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        data = prepare(Path(args.folder))
    else:
        prior = json.loads(reportfile.read_text(encoding="utf-8"))
        verified = check(
            Path(args.folder), prior["pre119b_cell_source_sha256"],
            prior["cell_count_after"]
        )
        data = {**prior, **verified}
    reportfile.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print("PRE119B Kaggle notebook:", args.phase, data.get("update_type"),
          "cells:", data.get("cell_count_after"))


if __name__ == "__main__":
    main()
