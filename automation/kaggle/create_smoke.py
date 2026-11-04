#!/usr/bin/env python3
"""Generate a harmless Kaggle smoke-test notebook (no game/Drive/keys)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

KERNEL_ID = "juniklx/nfsmw-automacao-smoke-pre100"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    nb_file = out / "nfsmw_automacao_smoke.ipynb"
    metadata = {
        "id": KERNEL_ID,
        "title": "NFSMW Automacao Smoke PRE100",
        "code_file": nb_file.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "nfsmw-intro",
                "metadata": {},
                "source": [
                    "# NFSMW - PRE100: smoke test da integracao Kaggle\n",
                    "Notebook de teste isolado. Nao baixa backups, nao altera fontes, nao compila APKs e nao acessa credenciais de assinatura.\n",
                ],
            },
            {
                "cell_type": "code",
                "id": "nfsmw-smoke",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": [
                    "from datetime import datetime, timezone\n",
                    "from pathlib import Path\n",
                    "from json import dumps\n",
                    "result = {'etapa': 'PRE100_KAGGLE_AUTOMACAO_SMOKE', 'status': 'EXECUTADO', 'utc': datetime.now(timezone.utc).isoformat(), 'altera_projeto': False, 'chaves_acessadas': False}\n",
                    "path = Path('/kaggle/working/NFSMW_PRE100_SMOKE_RESULTADO.json')\n",
                    "path.write_text(dumps(result, indent=2), encoding='utf-8')\n",
                    "print('NFSMW PRE100 SMOKE OK -', path.name)\n",
                ],
            },
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_file.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    (out / "kernel-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print('Notebook smoke preparado:', KERNEL_ID)


if __name__ == '__main__':
    main()
