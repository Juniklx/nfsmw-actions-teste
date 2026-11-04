#!/usr/bin/env python3
"""Análise offline PRE152 de quadros efetivamente apresentados por camada.

Nunca modifica o log bruto nem aciona Android/Termux. O FPS de cada intervalo
é estimado por delta do contador cumulativo `totalFrames`, se a camada continua
com mesmo nome e o contador não reinicia. Não confundir média por camada com a
taxa de quadros do motor e nem medir FPS quando a superfície não atualiza.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

PKG = "io.github.nfsmwrecomp"
SAMPLE = re.compile(r"^=== SAMPLE (\d+) ===$")
EPOCH = re.compile(r"^SAMPLE_EPOCH=(\d+)")
LAYER = re.compile(r"^layerName\s*=\s*(.*?)\s*$")
TOTAL = re.compile(r"^totalFrames\s*=\s*(\d+)\s*$")
FPS = re.compile(r"^averageFPS\s*=\s*([\d.]+)\s*$")
THERM = re.compile(r"^Thermal Status:\s*(\d+)\s*$")


def read_samples(content):
    records = []
    rec = None
    active = None
    for line in content.splitlines():
        found = SAMPLE.fullmatch(line)
        if found:
            rec = {"sample": int(found.group(1)), "epoch": None,
                   "thermal_status": None, "layers": []}
            records.append(rec)
            active = None
            continue
        if rec is None:
            continue
        found = EPOCH.match(line)
        if found:
            rec["epoch"] = int(found.group(1))
            continue
        found = THERM.match(line)
        if found:
            rec["thermal_status"] = int(found.group(1))
            continue
        found = LAYER.match(line)
        if found:
            name = found.group(1)
            active = {"name": name, "total_frames": None, "reported_average_fps": None}
            if PKG in name:
                rec["layers"].append(active)
            else:
                active = None
            continue
        if active:
            found = TOTAL.match(line)
            if found:
                active["total_frames"] = int(found.group(1))
            found = FPS.match(line)
            if found:
                active["reported_average_fps"] = float(found.group(1))
    return records


def analyze(records):
    last = {}
    rows = []
    for rec in records:
        for layer in rec["layers"]:
            name, total, t = layer["name"], layer["total_frames"], rec["epoch"]
            row = {"sample": rec["sample"], "epoch": t, "thermal_status": rec["thermal_status"],
                   "layer_name": name, "total_frames": total,
                   "reported_cumulative_average_fps": layer["reported_average_fps"],
                   "delta_seconds": None, "delta_frames": None,
                   "fps_interval_estimate": None, "quality": "NO_PRIOR_SAMPLE"}
            if total is None or t is None:
                row["quality"] = "MISSING_COUNTER_OR_TIMESTAMP"
            elif name in last:
                prev_t, prev_frames = last[name]
                dt, df = t - prev_t, total - prev_frames
                row["delta_seconds"] = dt
                row["delta_frames"] = df
                if dt <= 0:
                    row["quality"] = "NON_POSITIVE_TIME_SPAN"
                elif df < 0:
                    row["quality"] = "COUNTER_RESET_OR_LAYER_REPLACEMENT"
                else:
                    row["quality"] = "VALID_DIFFERENCE"
                    row["fps_interval_estimate"] = round(df / dt, 3)
            if total is not None and t is not None:
                last[name] = (t, total)
            rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Arquivo PRE152 coletado pelo Termux")
    ap.add_argument("--json", required=True, help="Caminho do relatório de saída")
    args = ap.parse_args()
    inp = Path(args.input)
    out = Path(args.json)
    raw = inp.read_bytes()
    source = raw.decode("utf-8", "replace")
    recs = read_samples(source)
    rows = analyze(recs)
    result = {
        "stage": "PRE152",
        "source": inp.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "sample_count": len(recs),
        "game_layer_rows": len(rows),
        "valid_intervals": sum(x["quality"] == "VALID_DIFFERENCE" for x in rows),
        "caveats": [
            "Dados por camada só correspondem ao jogo se o layerName e a atividade coincidem.",
            "totalFrames deve ser cumulativo; reinicializações são tratadas como dados inválidos.",
            "FPS do SurfaceFlinger não é necessariamente FPS interno do jogo; compare janelas reais.",
            "Ausência de linha de camada não prova ausência de quadros no display.",
            "Os contadores TimeStats são globais e foram habilitados/limpos temporariamente.",
        ],
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PRE152: amostras={len(recs)} linhas_por_camada={len(rows)} "
          f"intervalos_validos={result['valid_intervals']}")
    print(f"JSON: {out}")


if __name__ == "__main__":
    main()
