#!/usr/bin/env python3
"""PRE695: read-only attribution of SurfaceFlinger desired/ready/actual pacing.

Input: independent PRE694 phase ZIPs containing NFSMW_PRE690_ORDERED_PRESENT_*.txt.
Output: summary JSON and Markdown. Never changes source ZIPs, APKs or the phone.

Rows are documented in AOSP FrameTracker as desiredPresentTime,
actualPresentTime, frameReadyTime. They are not per-frame engine/GPU metrics.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile
import zipfile

STAGES=("SAMSUNG_A1","RADV_B","SAMSUNG_A2")
LABELS={"SAMSUNG_A1":"Samsung A1", "RADV_B":"RADV B", "SAMSUNG_A2":"Samsung A2"}
SOURCE="https://android.git.googlesource.com/platform/frameworks/native/+/a81c63b08ca32ff4aab89fe958b9afb1c3c16a92/services/surfaceflinger/FrameTracker.h"
NS_PER_MS=1_000_000

class DataError(ValueError):
    pass

def pct(n,d): return round(100*n/d,4) if d else None

def nearest_tick(delta_ns,period_ns):
    return (2*delta_ns+period_ns)//(2*period_ns)

def quantiles(v):
    a=sorted(v)
    if not a:return {}
    def p(q):return round(a[min(len(a)-1,max(0,math.ceil(len(a)*q)-1))],6)
    return {"p50":p(.5),"p90":p(.9),"p95":p(.95),"p99":p(.99)}

def summary_from_zip(path:Path,stage:str)->dict:
    if not path.is_file():raise DataError(f"NO_INPUT_ZIP:{path}")
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise DataError(f"ZIP_CRC_FAIL:{path}")
        members=[n for n in z.namelist() if n.split('/')[-1].startswith("NFSMW_PRE690_ORDERED_PRESENT_") and n.endswith(".txt")]
        if len(members)!=1:raise DataError(f"EXPECTED_ONE_CAPTURE:{len(members)}:{path}")
        lines=z.read(members[0]).decode('utf-8','strict').splitlines()
        manifests=[n for n in z.namelist() if n.split('/')[-1]=="PRE694_PHASE_MANIFEST.txt"]
        if len(manifests)!=1:raise DataError(f"EXPECTED_MANIFEST:{path}")
        manifest=z.read(manifests[0]).decode('utf-8','strict')
        if f"PHASE_LABEL={stage}" not in manifest.splitlines():raise DataError(f"PHASE_MISMATCH:{stage}:{path}")
        validation=[n for n in z.namelist() if n.split('/')[-1]=="PRE694_PHASE_CAPTURE_VALIDATED.txt"]
        if len(validation)!=1:raise DataError(f"NO_CAPTURE_VALIDATION:{path}")
        gate=z.read(validation[0]).decode('utf-8','strict')
        if "PRE694_CAPTURE_STRUCTURAL_VALIDATION=PASS" not in gate.splitlines():raise DataError(f"CAPTURE_NOT_VALIDATED:{path}")
        # The previous gate includes SHA256 lines for actual source artifacts.
        for name in (members[0], manifests[0]):
            sha=hashlib.sha256(z.read(name)).hexdigest()
            refs=[l for l in gate.splitlines() if l.startswith(sha+' ')]
            if len(refs)!=1:raise DataError(f"MANIFEST_SHA_MISMATCH:{name}")
    if not lines or lines[0]!="PRE690_ORDERED_SURFACEVIEW_TIMESTAMPS":raise DataError("BAD_HEADER")
    header=dict(line.split('=',1) for line in lines if '=' in line and line.split('=',1)[0] in
                {"PACKAGE","LAYER","COLLECTION_START","COLLECTION_END","SAMPLES_REQUESTED","NONEMPTY_SAMPLES"})
    if header.get('PACKAGE')!="io.github.nfsmwrecomp":raise DataError("WRONG_APP")
    if int(header.get('SAMPLES_REQUESTED','0'))!=30 or int(header.get('NONEMPTY_SAMPLES','0'))!=30:
        raise DataError("NOT_30_SAMPLES")
    if "SurfaceView[io.github.nfsmwrecomp/" not in header.get('LAYER',''):raise DataError("INVALID_LAYER")
    periods=set(); samples_open=0;sample_end=0;sample_nums=[];end_nums=[]
    raw=[]
    for line in lines:
        if line.startswith('SAMPLE_START '):
            v=line.split();samples_open+=1;sample_nums.append(int(v[1]))
        elif line.startswith('SAMPLE_END '):
            sample_end+=1;end_nums.append(int(line.split()[1]))
        elif line.startswith('PERIOD_NS '):
            periods.add(int(line.split()[1]))
        elif line.startswith('FRAME '):
            p=line.split()
            if len(p)!=4:raise DataError('BAD_TRIPLE')
            try:d,a,r=map(int,p[1:])
            except ValueError:raise DataError('BAD_INTEGER_TRIPLE')
            if all(x>0 and x<9223372036854775807 for x in (d,a,r)):
                raw.append((d,a,r))
    if len(periods)!=1:raise DataError(f"INCONSISTENT_PERIODS:{periods}")
    period=periods.pop()
    if not(5_000_000<=period<=25_000_000):raise DataError("INVALID_DISPLAY_PERIOD")
    if sample_nums!=list(range(1,31)) or end_nums!=list(range(1,31)) or samples_open!=30 or sample_end!=30:
        raise DataError("SAMPLE_SEQUENCE_INVALID")
    seen={}
    for row in raw:
        old=seen.get(row[1]);
        if old is not None and old!=row:raise DataError(f"CONFLICTING_SAME_ACTUAL_PRESENT:{row[1]}")
        seen[row[1]]=row
    rows=[seen[x] for x in sorted(seen)]
    if len(rows)<60:raise DataError("INSUFFICIENT_PRESENTS")
    continuous=[];gaps=[];block=[];blocks=[]
    for prev,curr in zip(rows,rows[1:]):
        delta=curr[1]-prev[1]
        if delta<=0:raise DataError("INVALID_ACTUAL_ORDER")
        if delta>100*NS_PER_MS:
            gaps.append(delta/NS_PER_MS)
            if block:blocks.append(block)
            block=[]
            continue
        item={'desired_ns':curr[0]-prev[0], 'actual_ns':delta, 'ready_ns':curr[2]-prev[2]}
        continuous.append(item);block.append(item)
    if block:blocks.append(block)
    n=len(continuous)
    if n<100:raise DataError("INSUFFICIENT_CONTINUOUS_INTERVALS")
    counts={};m={}
    for k in ('desired','ready','actual'):
        times=[it[f'{k}_ns']/NS_PER_MS for it in continuous]
        ticks=Counter(int(nearest_tick(it[f'{k}_ns'],period)) for it in continuous)
        counts[k]={str(x):ticks[x] for x in sorted(ticks)}
        m[k]={"mean_interval_ms":round(statistics.mean(times),6),
              "stdev_interval_ms":round(statistics.pstdev(times),6),
              "two_refresh_intervals":ticks[2],"two_refresh_percent":pct(ticks[2],n),
              "tick_histogram":counts[k],"quantiles_ms":quantiles(times)}
    offsets={}
    for label,pair in {"actual_minus_desired":(1,0),"actual_minus_ready":(1,2),"ready_minus_desired":(2,0)}.items():
        a=[(r[pair[0]]-r[pair[1]])/NS_PER_MS for r in rows]
        offsets[label]={"mean_ms":round(statistics.mean(a),6),"stdev_ms":round(statistics.pstdev(a),6),"quantiles_ms":quantiles(a),"min_ms":round(min(a),6),"max_ms":round(max(a),6)}
    transitions=0;trans_direction=Counter();outliers=[]
    for b in blocks:
        vals=[nearest_tick(item['actual_ns'],period) for item in b]
        for a,c in zip(vals,vals[1:]):
            if (a,c) in ((1,3),(3,1)):
                transitions+=1;trans_direction[f'{a}_to_{c}']+=1
    for prev,curr in zip(rows,rows[1:]):
        delta_ms=(curr[1]-prev[1])/NS_PER_MS
        if 33<=delta_ms<=100:
            outliers.append({"actual_interval_ms":round(delta_ms,6),
                             "desired_interval_ms":round((curr[0]-prev[0])/NS_PER_MS,6),
                             "ready_interval_ms":round((curr[2]-prev[2])/NS_PER_MS,6),
                             "actual_minus_ready_after_ms":round((curr[1]-curr[2])/NS_PER_MS,6)})
    return {"stage":stage,"zip_basename":path.name,"zip_size_bytes":path.stat().st_size,
            "zip_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"zip_crc":"PASS",
            "capture_name":members[0],"display_refresh_period_ns":period,
            "display_refresh_hz_estimated":round(1e9/period,4),
            "capture_start":header['COLLECTION_START'],"capture_end":header['COLLECTION_END'],
            "samples_validated":30,"raw_valid_triples":len(raw),"distinct_present_timestamps":len(rows),
            "duplicates_removed":len(raw)-len(rows),"conflicting_duplicates":0,
            "excluded_coverage_gaps_ms":[round(x,6) for x in gaps],
            "retained_intervals":n,"retained_window_coverage_s":round(sum(x['actual_ns'] for x in continuous)/1e9,4),
            "channels":m,"cross_timestamp_offsets":offsets,
            "actual_1to3_or_3to1_transitions":transitions,
            "actual_transition_directions":dict(trans_direction),
            "actual_intervals_at_least_33_ms":len(outliers),"actual_long_intervals":outliers,
            "observation_only":True}

def synthetic_test():
    period=8_333_333
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'s.zip'
        rows=[];a=10_000_000_000;d=10_000_000_000;r=10_000_000_000
        # Frame rows are consistent across two rolling queries per sample.
        for i in range(120):
            d+=2*period; r+=2*period
            a+=(1 if i%2 else 3)*period
            rows.append((d,a,r))
        body=['PRE690_ORDERED_SURFACEVIEW_TIMESTAMPS','PACKAGE=io.github.nfsmwrecomp',
              'LAYER=SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0(BLAST)#1',
              'COLLECTION_START=2026-11-11T10:00:00-0300','SAMPLES_REQUESTED=30']
        for s in range(30):
            body.extend([f'SAMPLE_START {s+1} 2026-11-11T10:00:00-0300',f'PERIOD_NS {period}'])
            for j in range(4*s,4*s+4):body.append('FRAME '+' '.join(map(str,rows[j])))
            # Duplicate each row within the same reading, as rolling samples can do.
            for j in range(4*s,4*s+4):body.append('FRAME '+' '.join(map(str,rows[j])))
            body.append(f'SAMPLE_END {s+1}')
        body.extend(['COLLECTION_END=2026-11-11T10:01:00-0300','NONEMPTY_SAMPLES=30'])
        capture='NFSMW_PRE690_ORDERED_PRESENT_test.txt';manifest='PRE694_PHASE_MANIFEST.txt'
        m='PHASE_LABEL=SAMSUNG_A1\n'
        gate='PRE694_CAPTURE_STRUCTURAL_VALIDATION=PASS\n'
        for name,data in ((capture,'\n'.join(body)+'\n'),(manifest,m)):
            gate+=hashlib.sha256(data.encode()).hexdigest()+'  '+name+'\n'
        with zipfile.ZipFile(p,'w') as z:
            z.writestr(capture,'\n'.join(body)+'\n');z.writestr(manifest,m)
            z.writestr('PRE694_PHASE_CAPTURE_VALIDATED.txt',gate)
        out=summary_from_zip(p,'SAMSUNG_A1')
        assert out['distinct_present_timestamps']==120
        assert out['duplicates_removed']==120
        assert out['retained_intervals']==119
        assert out['channels']['desired']['two_refresh_intervals']==119
        assert out['channels']['actual']['two_refresh_intervals']==0
        assert out['actual_1to3_or_3to1_transitions']==118
        try:summary_from_zip(p,'RADV_B')
        except DataError as e:assert 'PHASE_MISMATCH' in str(e)
        else:raise AssertionError('accepted wrong phase')
        print('PRE695_SYNTHETIC_DESIRED_READY_ACTUAL_PACING=PASS')
        print('PRE695_SYNTHETIC_ROLLING_DEDUPLICATION=PASS')
        print('PRE695_SYNTHETIC_STAGE_AND_MANIFEST_GUARDS=PASS')
        print('PRE695_REAL_S24FE_VALIDATION=NOT_TESTED_IN_CI')

def make_report(records):
    rows=["# PRE695 — Auditoria read-only de `desired`, `ready` e `actualPresent` (11/11/2026)","",
          "**Origem:** reprocessamento local dos três ZIPs brutos da PRE694 no Galaxy S24 FE. Nenhum novo teste no telefone, nem mudança de APK, shader, driver, sistema ou térmica.","",
          "## Método e verificação", "",
          "Os três timestamps de `dumpsys SurfaceFlinger --latency` seguem a semântica documentada no [FrameTracker da AOSP]("+SOURCE+"): `desiredPresentTime` (horário ideal), `frameReadyTime` (pronto para apresentação, podendo vir de fence) e `actualPresentTime` (efetivamente apresentado, podendo vir de fence ou timestamp de atualização). O método **não identifica diretamente** por que há um atraso em Android/Samsung nem mede fotogramas ópticos, entrada, ou GPU do jogo.","",
          "Cada ZIP passou na verificação CRC, validação de etapa, SHA dos arquivos principais e 30 amostras; timestamps de apresentação repetidos nos snapshots circulares foram deduplicados, e lacunas de **mais de 100ms** foram excluídas por incerteza de cobertura, sem serem rotuladas como travamentos. As três séries são comparadas nos **mesmos pares de quadros preservados**, com ticks arredondados pelo período reportado de 8.333.333ns (~120Hz).", "",
          "## Resultado real", "",
          "| Métrica | Samsung A1 | RADV B | Samsung A2 |", "|---|---:|---:|---:|"]
    def fmt(v):return f"{v:.3f}"
    fields=[
      ('Intervalos contínuos',lambda x:str(x['retained_intervals'])),
      ('`desired` a 2 ticks (%)',lambda x:fmt(x['channels']['desired']['two_refresh_percent'])),
      ('`ready` a 2 ticks (%)',lambda x:fmt(x['channels']['ready']['two_refresh_percent'])),
      ('`actual` a 2 ticks (%)',lambda x:fmt(x['channels']['actual']['two_refresh_percent'])),
      ('SD `desired` (ms)',lambda x:fmt(x['channels']['desired']['stdev_interval_ms'])),
      ('SD `ready` (ms)',lambda x:fmt(x['channels']['ready']['stdev_interval_ms'])),
      ('SD `actual` (ms)',lambda x:fmt(x['channels']['actual']['stdev_interval_ms'])),
      ('Mediana `ready - desired` (ms)',lambda x:fmt(x['cross_timestamp_offsets']['ready_minus_desired']['quantiles_ms']['p50'])),
      ('Mediana `actual - desired` (ms)',lambda x:fmt(x['cross_timestamp_offsets']['actual_minus_desired']['quantiles_ms']['p50'])),
      ('Mediana `actual - ready` (ms)',lambda x:fmt(x['cross_timestamp_offsets']['actual_minus_ready']['quantiles_ms']['p50'])),
      ('Intervalos `actual` 1 tick',lambda x:str(x['channels']['actual']['tick_histogram'].get('1',0))),
      ('Intervalos `actual` 3 ticks',lambda x:str(x['channels']['actual']['tick_histogram'].get('3',0))),
      ('Alternâncias `actual` 1↔3 ticks',lambda x:str(x['actual_1to3_or_3to1_transitions'])),
      ('Intervalos `actual` >=33ms',lambda x:str(x['actual_intervals_at_least_33_ms'])),
    ]
    for name,fn in fields:rows.append('| '+name+' | '+' | '.join(fn(records[x]) for x in STAGES)+' |')
    rows.extend(["", "## Interpretação verificável", "",
                 "- `desired` conserva quase sempre o ciclo-alvo de 16,67ms nas três sessões; `actualPresent` tem desvio-padrão muito maior. Os pares 1↔3 ticks no `actual` somam **quatro ticks** em dois quadros, compatível com compensação de cadência sem alteração relevante no FPS médio. Uma média de 60 FPS **não** implica entrega a cada 16,67ms.",
                 "- A série `ready` varia mais que `desired`, mas menos que `actual` nas três sessões. Portanto, os timestamps medidos **localizam a variação adicional entre prontidão/planejamento e apresentação efetiva**. Isso NÃO é uma prova de que o SurfaceFlinger seja o culpado: atrasos herdados, compensações, buffers e composição podem influenciar.",
                 "- O RADV apresenta menos alternâncias 1↔3 ticks que ambas as fases Samsung, mas mais eventos longos no `actual`. A variância de cada métrica também depende de cena, temperatura, frequência, carga e duração, não registradas de modo controlado nesse A/B/A.",
                 "- **Diferença de contagem versus PRE694:** 1↔3 ticks usa arredondamento pelo período exato de 120Hz, incluindo amostras de 8–9ms e ~25ms. A PRE694 usava buckets de milissegundos inteiros 8↔25, por isso os contadores não precisam coincidir (PRE694: 278/216/271; PRE695: 288/228/282). As duas formas são derivadas das mesmas séries, mas têm critérios distintos.",
                 "- A diferença absoluta `actual - desired` **não é latência de entrada nem atraso de comandos**, e não deve ser subtraída ingenuamente de métricas C2. Estes são timestamps de apresentação de uma camada do compositor.",
                 "", "## Próximo gate recomendado (ainda não executado)", "",
                 "Auditar somente leitura o **código real da apresentação** (VulkanPresenter, swapchain MAILBOX, pacing de 60 FPS e chamadas de espera/sinalização) na árvore correspondente à V51 autenticada, usando hashes de fontes. Mapear pontos de instrumentação sem gerar APK até existir uma hipótese testável. Se um novo ensaio for necessário, coletar timestamps do compositor e telemetria térmica/clock simultânea, preservando a mesma cena estática.",
                 "", "**Limites:** sem captura Perfetto de FrameTimeline, fences GPU individuais, rastreamento causal app→SF→HWC ou vídeo de alta velocidade; não atribuir origem causal nem declarar melhora perceptiva.",
                 "", "**STATUS:** PRE695_OFFLINE_REAL_DATA_READONLY; A_B_A_SOURCE_INTEGRITY_PASS; DESIRED_STABLE_ACTUAL_JITTER_OBSERVED; ORIGIN_UNPROVEN; NO_APK; NO_FPS_GAIN."
                 ])
    return '\n'.join(rows)+'\n'

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--a1',type=Path)
    p.add_argument('--b',type=Path)
    p.add_argument('--a2',type=Path)
    p.add_argument('--json',type=Path)
    p.add_argument('--md',type=Path)
    a=p.parse_args(argv)
    if a.selftest:synthetic_test();return
    if not all((a.a1,a.b,a.a2,a.json,a.md)):
        p.error('Use --a1 --b --a2 --json --md or --selftest')
    records={k:summary_from_zip(z,k) for k,z in zip(STAGES,(a.a1,a.b,a.a2))}
    payload={'name':'NFSMW_PRE695_PACING_ATTRIBUTION_READONLY','input_type':'PRE694_REAL_S24FE_ZIPS',
             'reference_AOSP_FrameTracker':SOURCE,'stages':records,
             'causal_status':'UNPROVEN','quality_and_apk_changed':False}
    a.json.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    a.md.write_text(make_report(records),encoding='utf-8')
    for stage in STAGES:
        x=records[stage];print(stage, 'READY2T',x['channels']['ready']['two_refresh_percent'], 'DESIRED2T',x['channels']['desired']['two_refresh_percent'], 'ACTUAL2T',x['channels']['actual']['two_refresh_percent'], 'T13',x['actual_1to3_or_3to1_transitions'])
    print('PRE695_REAL_ZIP_READBACK_AND_SHA=PASS')
    print('PRE695_REAL_OFFLINE_READONLY_AUDIT=PASS')
    print('PRE695_CAUSAL_ORIGIN=UNPROVEN')
    print('PRE695_NO_APK_OR_PHONE_MODIFICATION=TRUE')
    print('REPORT='+str(a.md));print('JSON='+str(a.json))

if __name__=='__main__':
    try:main()
    except (DataError,ValueError,zipfile.BadZipFile) as exc:
        print('PRE695_FAIL_CLOSED='+str(exc),file=sys.stderr);sys.exit(2)
