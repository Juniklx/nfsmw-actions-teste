# NFSMW PRE151 — Análise da coleta PRE150: Vulkan e térmica pareados na V31

**Data:** 2026-11-04, Galaxy S24 FE, Brasil/Bahia (UTC−03:00). **Estado:** análise offline dos três arquivos enviados pelo usuário, sem rebuild nem modificação do jogo.

## 1. Fontes e integridade

- `nfsmw.log` — 3472116 bytes, SHA-256 `778d646bb68d393d3bc9857c8b87e7ea11184e80028e2a8110b11b5243b5372e`.
- `nfsmw_pre150_v31_profiler_termico_20261104_201147.txt` — 153855 bytes, SHA-256 `0fed36187718932fb1d0a8c0e1662eddbea535440a84088d4e72be6215376f52`.
- `nfsmw_pre150_v31_profiler_erros_20261104_201147.txt` — 147195 bytes, SHA-256 `853be140adf19d50037251a1157614bb83fd9015d5fc149fb5fbf55e601d7350`.
- Contexto de referência: `CONTEXTO_NFSMW.md`, seção PRE150, consultada no projeto. Sessões anteriores do mesmo `nfsmw.log` excluídas pela âncora 20:11:49.733.

## 2. Execução constatada

- `versionCode=31` verificado pelo script; Shizuku UID 2000; `am start` retornou 0, `LaunchState: COLD` e abriu `GameActivity`. O primeiro marcador de execução da sessão aparece em `nfsmw.log` às 20:11:49.733.
- `VulkanPresenter` criou swapchain 1920×1080, MAILBOX, com quatro imagens **solicitadas**. Limite 120 FPS e resolução interna 1920×1080 registrados; não afirmar quatro imagens concedidas.
- `STATUS_FINAL=COLETA_CONCLUIDA` no arquivo `termico`; o arquivo `erros` contém saída normal roteada pelo rish e marcador final `FIM_MONITOR_EPOCH=1793834273` e `LOG_COPIADO=/sdcard/Download/nfsmw_pre150_v31_profiler_20261104_201753.log`. O nome `erros` não indica uma falha por si só.
- As 100 amostras numeradas aparecem **uma única vez** no conjunto de dois arquivos: 49 marcadores em `termico`, 51 em `erros`. Há 100 pares `epoch/local/decorrido` e 100 estados térmicos. O shell dividiu a saída entre canais; temperaturas HAL parciais não devem ser inventadas ou atribuídas a outras amostras.
- O período da captura remota foi de **364 s** de relógio real (20:11:49 a 20:17:53), embora o parâmetro fosse 300 s com 100 amostras; aproximadamente 64 s adicionais decorreram de overhead das consultas e encaminhamento de saída. Não tratar como 300 s de relógio exatos.
- O último log de jogo termina com pausa/segundo plano às 20:17:03; o monitor continuou até 20:17:53. Não misturar essa cauda térmica com FPS do jogo em primeiro plano.

## 3. Evolução térmica

| Primeiro registro com estado | Horário local | Amostra: `decorrido_s` |
|---|---|---:|
| 0 | 20:11:49 | 0 |
| 1 | 20:12:50 | 51 |
| 2 | 20:13:35 | 87 |
| 3 | 20:16:49 | 246 |

- **SKIN:** 53 leituras atribuíveis à janela de amostra; primeira 35.3 °C, máxima 45.1 °C, última 43.8 °C. Apenas `Current temperatures from HAL`, sem reaproveitar `Cached temperatures`.
- **BAT:** 58 leituras atribuíveis à janela de amostra; primeira 35.1 °C, máxima 45.2 °C, última 45.0 °C. Apenas `Current temperatures from HAL`, sem reaproveitar `Cached temperatures`.
- **AP:** 59 leituras atribuíveis à janela de amostra; primeira 40.8 °C, máxima 65.3 °C, última 49.5 °C. Apenas `Current temperatures from HAL`, sem reaproveitar `Cached temperatures`.
- O pico de AP (processador) não é a temperatura externa do aparelho. `SKIN` é o indicador térmico de superfície. `status=3` (severo) apareceu perto do fim da sessão do jogo, e não permite estimar FPS após a pausa de 20:17:03.
- **Limitação GPU DEVFREQ:** `cur_freq/min_freq/max_freq/available_frequencies` foram fragmentados nos dois fluxos por rish; aparecem combinações internamente inconsistentes. Não reportar 252 MHz como frequência real sustentada, nem inferir o teto de frequência a partir de linhas desalinhadas. Necessária coleta em formato atômico por amostra, caso clocks sejam indispensáveis.
- **Limitação bateria:** `dumpsys battery` também imprimiu histórico `Sending ACTION_BATTERY_CHANGED` de horários **anteriores**. As temperaturas da bateria usadas acima provêm do HAL contemporâneo, não dessas linhas históricas.

## 4. Perfil Vulkan e FPS estimado

- Foram encontrados **50** relatórios de `PaintAndPresent`, cada um de 600 quadros: **30,000 quadros instrumentados** na sessão das 20h, sem somar sessões anteriores.
- Média não ponderada das 50 médias por bloco (todos têm 600 quadros): `vkQueuePresentKHR` **3.050 ms**, `PaintAndPresent` **3.207 ms**; participação aproximada **95.12% do tempo medido do apresentador**, não do frame completo. `vkQueueSubmit` **0.037 ms** e `adquirir` média registrada **0.00 ms** (arredondamento).
- A maior **chamada individual** indicada nos blocos de `vkQueuePresentKHR` foi **19.53 ms**. Não confundir esse pior caso com a média.
- Foram encontrados **15** relatórios C2, permitindo **14** estimativas de FPS entre relatórios consecutivos (delta de `presentados` dividido pelo tempo real). São FPS *estimados do fluxo do motor*, não a taxa aferida no compositor.

| Final da janela | FPS estimado | GPU real por Swap (ms) | Último Thermal Status amostrado |
|---|---:|---:|---:|
| 20:12:30 | 106.65 | 5.93 | 0 |
| 20:12:50 | 101.52 | 7.27 | 1 |
| 20:13:10 | 99.30 | 8.00 | 1 |
| 20:13:30 | 117.59 | 6.90 | 1 |
| 20:13:50 | 115.90 | 7.21 | 2 |
| 20:14:10 | 108.29 | 7.81 | 2 |
| 20:14:30 | 106.17 | 8.01 | 2 |
| 20:14:50 | 104.29 | 8.16 | 2 |
| 20:15:10 | 93.84 | 9.00 | 2 |
| 20:15:30 | 91.80 | 9.16 | 2 |
| 20:15:50 | 85.18 | 9.85 | 2 |
| 20:16:10 | 73.76 | 11.23 | 2 |
| 20:16:30 | 72.66 | 11.38 | 2 |
| 20:16:50 | 72.60 | 11.40 | 3 |

- Comparando apenas as janelas terminadas às **20:13:30** e **20:16:50**, ambas depois do marcador de direção às 20:13:04, houve **117.59→72.60 FPS** (−38.3%) e GPU **6.90→11.40 ms por Swap** (+65.2%). **A cena e a carga não foram controladas**. O trabalho da etapa GPU `escena` mudou de 2.01 para 4.30 ms e `reflejo` de 0.62 para 1.25 ms; isso não distingue complexidade visual de variação de eficiência/clocks.
- O profiler `vkQueuePresentKHR` começou com médias próximas de **0,2–0,5 ms** nas primeiras janelas e alcançou **7,06 ms** no bloco das 20:17:01. Esse aumento é temporalmente concomitante ao aquecimento; a espera não deve ser removida (potencialmente inclui pacing/compositor/pressão de fila/GPU).
- No log desta sessão não há linhas textuais `[error]` ou `[fatal]` às 20h; há avisos `[warning]` (incluindo tentativas de arquivos inexistentes). A ausência de `[error]` não prova estabilidade completa nem desempenho correto.

## 5. Diagnóstico e limites de inferência

1. **Pressão térmica comprovada:** Thermal Status 0→1→2→3, SKIN até 45.1 °C. A degradação de FPS e aumento dos tempos GPU e `vkQueuePresentKHR` são concomitantes. **Não é possível quantificar causalmente qual fração da queda decorre da térmica, e qual decorre da cena/GPU/filas.**
2. **`vkQueuePresentKHR` permanece a maior parcela dentro de `PaintAndPresent` (~95.1%)**, mas a GPU também está mais ocupada. Espera na apresentação pode ser consequência normal de disponibilidade dos buffers, compositor, queueing e frame pacing; não desativar sincronizações por intuição.
3. **A sessão PRE149 não é uma baseline controlada para ganho/regressão**: embora PRE149 tenha relatado média de 5.544 ms em `vkQueuePresentKHR`, cenários e estado térmico diferem. Nenhum ganho de FPS entre PRE149 e PRE150 foi provado.
4. **Sem mudança de APK:** manter V31, certificado permanente, 1920×1080, 120 FPS, shaders, física, PG-9076 e proteções térmicas.

## 6. Próximos passos propostos (sem nova participação imediata do usuário)

1. Preservar os três arquivos brutos exatamente como recebidos (hashes acima), este relatório e JSON analítico. Não reexecutar PRE150 por rotina.
2. Auditar de forma somente leitura a instrumentação e os contadores existentes de Vulkan/WSI e SurfaceFlinger; considerar se uma consulta de `SurfaceFlinger --timestats` é possível e interpretável por layer **sem recompilar**. Nenhum modo de apresentação ou termal policy deve ser alterado.
3. Para futuro teste realmente comparável, definir cenário de direção parado, aquecimento inicial, carga externa/ambiente e janela exata. Corrigir script de coleta para emitir **uma linha estruturada por amostra** e evitar despejar histórico de `dumpsys battery`; validar localmente antes de pedir outro teste físico.
4. Atualizar `CONTEXTO_NFSMW.md` com esta PRE151 como relatório pós-PRE150, marcando que a coleta **foi executada** e V31 foi validada; a fonte canônica existente só deve ser modificada com backup, leitura de versão corrente e confirmação de gravação.

**Arquivos analíticos:** `RELATORIO_NFSMW_PRE151_V31_PRE150_CORRELACAO_TERMICA_20261104.md` e `NFSMW_PRE151_V31_PRE150_DADOS_ANALISADOS_20261104.json`. **Sem nova APK compilada ou testada, sem alteração na assinatura.**
