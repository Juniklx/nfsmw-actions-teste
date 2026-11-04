#!/usr/bin/env python3
"""PRE120: read-only safe structural inspection of existing Kaggle notebook cells.

Reports cell statement categories, call identifiers and risky-operation flags.
Never records source, arguments, string literals, environment or secrets.
Used to decide if initiating original notebook is safe. Does not run notebook.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

EXPECTED_NOTEBOOK = "juniklx/nfsmw"
EXPECTED_P119_MARKER = "# NFSMW_PRE119B_AUDITORIA_AUTOSYNC_V1"

def identifier(node: ast.AST) -> str:
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute): return identifier(node.value) + "." + node.attr
    if isinstance(node, ast.Call): return identifier(node.func) + "()"
    if isinstance(node, ast.Subscript): return identifier(node.value) + "[]"
    return type(node).__name__

def cell_text(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src,list) else str(src)

def analyze_code(source: str) -> dict:
    signals = {
        "shell_magic_or_bang": any(s.lstrip().startswith(("!","%")) for s in source.splitlines()),
        "python_exec_eval": bool(re.search(r"\b(exec|eval|compile)\s*\(", source)),
        "subprocess_or_system": bool(re.search(r"\b(subprocess|os\.system|Popen|runpy|os\.exec|os\.spawn)\b", source)),
        "file_write_api": bool(re.search(r"\b(write_text|write_bytes|to_csv|to_excel|mkdir|unlink|rmtree|shutil\.move|shutil\.copy|open\s*\(|\.update\s*\()", source)),
        "drive_api_refs": bool(re.search(r"googleapiclient|google\.auth|drive\.files|GoogleDrive|gdown|drive\.mount", source,re.I)),
        "kaggle_secrets_refs": bool(re.search(r"kaggle_secrets|UserSecretsClient|get_secret",source)),
        "game_build_refs": bool(re.search(r"gradlew|assembleRelease|cmake|ninja|ndk-build|apksigner|zipalign",source,re.I)),
        "network_refs": bool(re.search(r"requests|urllib|http|https|download|kaggle",source,re.I)),
        "original_notebook_modifying_refs": bool(re.search(r"kernels push|kernels delete|kaggle kernels|write_text\s*\(|write_bytes\s*\(",source,re.I)),
        "possible_credential_refs": bool(re.search(r"PASSWORD|TOKEN|PRIVATE_KEY|KEYSTORE|CREDENTIAL",source,re.I)),
        "pre119b_cell_marker": EXPECTED_P119_MARKER in source,
    }
    sanitized = {
        "characters": len(source),
        "line_count": len(source.splitlines()),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "flags": signals,
    }
    if signals["shell_magic_or_bang"]:
        sanitized["parse"] = "SKIPPED_NOTEBOOK_MAGIC"
        return sanitized
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        sanitized["parse"] = "SYNTAX_ERROR_OR_MAGIC"
        return sanitized
    sanitized["parse"]="OK"
    sanitized["top_level_statements"]=[type(stmt).__name__ for stmt in parsed.body[:35]]
    # Only function/class names; no expression values, args or literal strings.
    sanitized["defined_symbols"]=[n.name for n in parsed.body
                                  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))][:25]
    allcalls=[]
    for n in ast.walk(parsed):
        if isinstance(n,ast.Call):
            name=identifier(n.func)
            if name not in allcalls:allcalls.append(name)
    sanitized["call_names"]=allcalls[:65]
    sanitized["calls_truncated"]=len(allcalls)>65
    # Never automatically claim this notebook safe for full execution.
    sanitized["run_all_cells_automatically_authorized"]=False
    return sanitized

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--folder",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    root=Path(args.folder).resolve()
    metadata=json.loads((root/"kernel-metadata.json").read_text(encoding="utf-8"))
    if metadata.get("id")!=EXPECTED_NOTEBOOK or metadata.get("kernel_type")!="notebook":
        raise ValueError("Unexpected Kaggle notebook identity")
    code_file=metadata.get("code_file","")
    if not isinstance(code_file,str) or not code_file.endswith(".ipynb"):
        raise ValueError("Unsupported notebook file extension")
    nb_path=(root/code_file).resolve()
    if nb_path.parent!=root:raise ValueError("Notebook path outside pull directory")
    raw=nb_path.read_bytes()
    if len(raw)>18*1024*1024:raise ValueError("Notebook exceeds expected size")
    nb=json.loads(raw.decode("utf-8"))
    if nb.get("nbformat")!=4 or not isinstance(nb.get("cells"),list):
        raise ValueError("Not nbformat4")
    cells=[]
    for i,cell in enumerate(nb["cells"]):
        report={"index":i,"cell_type":cell.get("cell_type")}
        source=cell_text(cell)
        if cell.get("cell_type")=="code":
            report.update(analyze_code(source))
        else:
            report["source_sha256"]=hashlib.sha256(source.encode("utf-8")).hexdigest()
            report["characters"]=len(source)
        cells.append(report)
    data={
        "etapa":"PRE120_AUDIT_ORIGINAL_KAGGLE_NOTEBOOK_CELLS",
        "github_run_id":args.run_id,
        "target":EXPECTED_NOTEBOOK,
        "original_notebook_sha256":hashlib.sha256(raw).hexdigest(),
        "metadata_id_verified":True,
        "cell_count":len(cells),
        "pre119b_cell_count":sum(c.get("flags",{}).get("pre119b_cell_marker",False) for c in cells),
        "cells":cells,
        "notebook_source_saved_to_report":False,
        "source_literal_values_saved_to_report":False,
        "notebook_executed":False,
        "notebook_modified":False,
        "game_files_accessed":False,
        "drive_credentials_accessed":False,
        "apk_built":False,
        "signing_key_accessed":False,
        "run_all_cells_automatically_authorized":False,
        "status":"PRE120_NOTEBOOK_ESTRUTURA_AUDITADA_SEM_EXECUTAR",
        "utc":datetime.now(timezone.utc).isoformat(),
    }
    out=Path(args.report)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE120 original Kaggle notebook structurally inspected:",
          len(cells),"cells; no source logged, no code run")

if __name__=="__main__":
    main()
