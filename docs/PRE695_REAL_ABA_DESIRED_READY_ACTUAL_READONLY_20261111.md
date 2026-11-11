# PRE695 — Auditoria read-only de `desired`, `ready` e `actualPresent` (11/11/2026)

**Origem:** reprocessamento local dos três ZIPs brutos da PRE694 no Galaxy S24 FE. Nenhum novo teste no telefone, nem mudança de APK, shader, driver, sistema ou térmica.

## Método e verificação

Os três timestamps de `dumpsys SurfaceFlinger --latency` seguem a semântica documentada no [FrameTracker da AOSP](https://android.git.googlesource.com/platform/frameworks/native/+/a81c63b08ca32ff4aab89fe958b9afb1c3c16a92/services/surfaceflinger/FrameTracker.h): `desiredPresentTime` (horário ideal), `frameReadyTime` (pronto para apresentação, podendo vir de fence) e `actualPresentTime` (efetivamente apresentado, podendo vir de fence ou timestamp de atualização). O método **não identifica diretamente** por que há um atraso em Android/Samsung nem mede fotogramas ópticos, entrada, ou GPU do jogo.

Cada ZIP passou na verificação CRC, validação de etapa, SHA dos arquivos principais e 30 amostras; timestamps de apresentação repetidos nos snapshots circulares foram deduplicados, e lacunas de **mais de 100ms** foram excluídas por incerteza de cobertura, sem serem rotuladas como travamentos. As três séries são comparadas nos **mesmos pares de quadros preservados**, com ticks arredondados pelo período reportado de 8.333.333ns (~120Hz).

## Resultado real

| Métrica | Samsung A1 | RADV B | Samsung A2 |
|---|---:|---:|---:|
| Intervalos contínuos | 2327 | 2317 | 2312 |
| `desired` a 2 ticks (%) | 99.871 | 99.914 | 99.697 |
| `ready` a 2 ticks (%) | 94.714 | 98.015 | 95.848 |
| `actual` a 2 ticks (%) | 79.244 | 82.046 | 78.504 |
| SD `desired` (ms) | 0.828 | 0.766 | 0.869 |
| SD `ready` (ms) | 2.078 | 1.550 | 1.952 |
| SD `actual` (ms) | 3.847 | 3.738 | 3.996 |
| Mediana `ready - desired` (ms) | 0.441 | 0.342 | 0.394 |
| Mediana `actual - desired` (ms) | 19.415 | 19.208 | 19.058 |
| Mediana `actual - ready` (ms) | 18.906 | 18.814 | 18.563 |
| Intervalos `actual` 1 tick | 242 | 214 | 250 |
| Intervalos `actual` 3 ticks | 239 | 195 | 243 |
| Alternâncias `actual` 1↔3 ticks | 288 | 228 | 282 |
| Intervalos `actual` >=33ms | 2 | 7 | 4 |

## Interpretação verificável

- `desired` conserva quase sempre o ciclo-alvo de 16,67ms nas três sessões; `actualPresent` tem desvio-padrão muito maior. Os pares 1↔3 ticks no `actual` somam **quatro ticks** em dois quadros, compatível com compensação de cadência sem alteração relevante no FPS médio. Uma média de 60 FPS **não** implica entrega a cada 16,67ms.
- A série `ready` varia mais que `desired`, mas menos que `actual` nas três sessões. Portanto, os timestamps medidos **localizam a variação adicional entre prontidão/planejamento e apresentação efetiva**. Isso NÃO é uma prova de que o SurfaceFlinger seja o culpado: atrasos herdados, compensações, buffers e composição podem influenciar.
- O RADV apresenta menos alternâncias 1↔3 ticks que ambas as fases Samsung, mas mais eventos longos no `actual`. A variância de cada métrica também depende de cena, temperatura, frequência, carga e duração, não registradas de modo controlado nesse A/B/A.
- **Diferença de contagem versus PRE694:** 1↔3 ticks usa arredondamento pelo período exato de 120Hz, incluindo amostras de 8–9ms e ~25ms. A PRE694 usava buckets de milissegundos inteiros 8↔25, por isso os contadores não precisam coincidir (PRE694: 278/216/271; PRE695: 288/228/282). As duas formas são derivadas das mesmas séries, mas têm critérios distintos.
- A diferença absoluta `actual - desired` **não é latência de entrada nem atraso de comandos**, e não deve ser subtraída ingenuamente de métricas C2. Estes são timestamps de apresentação de uma camada do compositor.

## Próximo gate recomendado (ainda não executado)

Auditar somente leitura o **código real da apresentação** (VulkanPresenter, swapchain MAILBOX, pacing de 60 FPS e chamadas de espera/sinalização) na árvore correspondente à V51 autenticada, usando hashes de fontes. Mapear pontos de instrumentação sem gerar APK até existir uma hipótese testável. Se um novo ensaio for necessário, coletar timestamps do compositor e telemetria térmica/clock simultânea, preservando a mesma cena estática.

**Limites:** sem captura Perfetto de FrameTimeline, fences GPU individuais, rastreamento causal app→SF→HWC ou vídeo de alta velocidade; não atribuir origem causal nem declarar melhora perceptiva.

**STATUS:** PRE695_OFFLINE_REAL_DATA_READONLY; A_B_A_SOURCE_INTEGRITY_PASS; DESIRED_STABLE_ACTUAL_JITTER_OBSERVED; ORIGIN_UNPROVEN; NO_APK; NO_FPS_GAIN.


## Arquivos privados preservados no Drive

- [Relatório PRE695](https://drive.google.com/file/d/145Ey9gnhEr0jxf6cfZ5w3DFa9SUG5-wd/view): 4.626 bytes, SHA-256 `8062cf89c6ea47f68d30280ff0a6600f56ae8fe5181ff1397c8a45ddb7ee751d`.
- [Pacote reproduzível PRE695](https://drive.google.com/file/d/1jVumhmYLlglj5SrMN0HEl3AdQ9YKdt0l/view): 12.591 bytes, SHA-256 `7540cc95405107f8b73a766f671048da10b2cd948e54797c795da6891210236a`; contém script e JSON, NÃO contém os ZIPs originais nem logs de jogo.
- [Contexto canônico PRE694 final](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view), a atualizar para PRE695 somente após backup e leitura de volta.

**Segurança:** síntese estatística e código próprio sem código de jogo, credenciais, assinaturas, dumps crus ou dados pessoais no GitHub. CI sintético remoto ainda não executado para o analisador PRE695.
