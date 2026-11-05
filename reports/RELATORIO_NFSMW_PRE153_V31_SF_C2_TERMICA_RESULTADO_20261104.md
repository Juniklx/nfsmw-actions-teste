# NFSMW PRE153 — Resultado real PRE152: SurfaceFlinger × C2 × Vulkan × térmica (Galaxy S24 FE)

**Data/sessão:** 04/11/2026, 21:12:49–21:17:12 (UTC−03:00). **Estado:** análise offline de dois arquivos reais enviados pelo usuário. A execução PRE152 no aparelho está comprovada. **V31 preservada, sem nova compilação/otimização confirmada.**

## Evidência de origem e integridade

- `nfsmw_pre152_v31_surfaceflinger_20261104_211249_13212.txt` — 128033 bytes; SHA-256 `9a423721b1bc9ebf37909d1557bd7fb44e4e3cd8be45e1af77469ebaaf13548f`; Drive `06_Logs_e_Medicoes`: https://drive.google.com/file/d/1-P7UVO5bjJGFc0EAyUnd0DARZ1NSAGN6/view .
- `nfsmw.log` — 4407073 bytes; SHA-256 `30715ef0f76367452f6128651a696627e0afb7420a46fcd94b64d21895d55d71`; possui várias sessões anteriores, portanto **analisar somente 21:12:50–21:17:12 nesta etapa**. Drive: https://drive.google.com/file/d/1CtEjIIeIr0Jtor_8ZgLEHAT2qbaZsvaO/view .
- `UID_SHELL=2000`; `VERSION_CODE=31`; `Status: ok`; `Activity: ...GameActivity`; `AM_START_RC=0` no TXT; monitor terminou `STATUS_FINAL=COLETA_ENCERRADA`, `REMOTE_RC=0`, com **12 amostras**. 
- `SF_TIMESTATS_DISABLE_TENTADO=1` indica tentativa de limpeza; **não existe evidência positiva do retorno de `-disable`**. Evitar afirmar que foi concluída a limpeza do contador global.
- Jogo com swapchain Vulkan **1920×1080 / MAILBOX**, **quatro imagens solicitadas** (não necessariamente concedidas); limite 120 FPS no log às 21:12:50. Nenhum novo APK ou ajuste foi aplicado.

## Descoberta principal: FPS apresentados realmente diminuem

A camada correta tem nome `SurfaceView[io.github.nfsmwrecomp/...GameActivity]@0(BLAST)#57137`, e não a camada `VRI-...` de UI, que tem ~2 FPS e **não deve ser confundida com o jogo**. O `averageFPS` reportado pelo TimeStats é cumulativo; por isso a série válida usa `(totalFrames_atual − totalFrames_anterior)/(epoch_atual − epoch_anterior)`.

| Hora final | Frames no intervalo | Segundos | SurfaceView FPS | Thermal Status | SKIN | GPU max_freq (segunda leitura, valor bruto) |
|---|---:|---:|---:|---:|---:|---:|
| 21:13:31 | 2246 | 21 | 106.95 | 0 | 37.0 °C | 1000000 |
| 21:13:52 | 2084 | 21 | 99.24 | 1 | 40.5 °C | 1095000 |
| 21:14:13 | 2167 | 21 | 103.19 | 1 | 41.5 °C | 900000 |
| 21:14:35 | 2516 | 22 | 114.36 | 2 | 41.7 °C | 900000 |
| 21:14:56 | 2443 | 21 | 116.33 | 2 | 42.2 °C | 900000 |
| 21:15:17 | 2384 | 21 | 113.52 | 2 | 43.3 °C | 600000 |
| 21:15:38 | 2261 | 21 | 107.67 | 2 | 43.6 °C | 545000 |
| 21:15:59 | 2122 | 21 | 101.05 | 2 | 43.9 °C | 545000 |
| 21:16:20 | 2069 | 21 | 98.52 | 2 | 44.1 °C | 500000 |
| 21:16:41 | 2034 | 21 | 96.86 | 2 | 44.4 °C | 450000 |
| 21:17:02 | 1917 | 21 | 91.29 | 2 | 44.5 °C | 400000 |

- Amostra final cumulativa: `totalFrames=26299`, `averageFPS=109.488`. **109,488 é a média cumulativa, não o FPS do último intervalo**, que é **91.29**.
- Entre as amostras 1→12: 24243 quadros / 232 s = **104.50 FPS** médios no trecho, com 11 intervalos válidos.
- Pico do intervalo às **21:14:56 = 116.33 FPS**; último às **21:17:02 = 91.29 FPS**; variação relativa **-21.5%**, sem controle rigoroso de cena/temperatura.

## Pareamento com produção de quadros, custo GPU e Vulkan

- O mesmo `nfsmw.log` contém **13 relatórios C2** na sessão das 21:12; os relatórios C2 são de ~20 s e os TimeStats de ~21 s. As séries têm cadências diferentes, portanto **comparação qualitativa temporal**, não subtração quadro a quadro.
- No C2, os contadores por janela de 20 s caem de **2376 Swaps (≈118,8/s) às 21:14:31** para **1755 Swaps (≈87,75/s) às 21:17:11**. Os FPS apresentados pelo SurfaceView também declinam nos intervalos finais, sem prova de perda adicional sistemática atribuível ao compositor. Isso **não demonstra que SurfaceFlinger/vsync não tenham nenhuma influência**.
- O `GPU real por Swap` no C2 cresce de **6,61 ms às 21:13:31** para **9,47 ms às 21:17:11** (~43,3%). Essas medidas têm janelas distintas das leituras TimeStats.
- Há **45 janelas de 600 quadros** de `reparto de PaintAndPresent` na sessão (27.000 quadros instrumentados). Média simples das médias por janela: `vkQueuePresentKHR` = **2.076 ms** e `PaintAndPresent TOTAL` = **2.238 ms** (~92.8% do tempo dessa função, **não** do tempo do quadro completo). Primeira janela `vkQueuePresentKHR` **0.13 ms**, última **5.47 ms**. Não somar tempos sobrepostos nem remover espera de apresentação por hipótese.

## Mudanças térmicas e frequências — relevantes, mas não causais por si sós

- `Thermal Status`: 0 nas amostras 1–2, 1 nas 3–4 e 2 a partir da 5 (21:14:35). Nesta sessão **não houve amostra de status 3**.
- `SKIN`: **35,6→44,5 °C**; `BAT`: **35,0→44,4 °C**; `AP`: 43,4→64,6 °C entre primeira e última amostra (AP é sensor interno, não pele).
- Devfreq GPU no arquivo: primeira amostra `cur_freq=900000`, `max_freq=1095000`; última `cur_freq=400000`, `max_freq=400000` (valores brutos fornecidos pelo driver, não convertidos aqui em MHz). Isso é compatível com limitação dinâmica crescente. **Leituras são sequenciais e algumas trazem `cur_freq>max_freq` entre verificações**, sinal de atualização não atômica: não inferir curva completa de clocks nem valor garantido do teto.
- Há inclusive **116,33 FPS apresentados com status térmico 2** na amostra 6; portanto não se pode quantificar redução causada exclusivamente pela classificação térmica. Frequência, composição do quadro, contexto do jogo, fila e condição térmica podem mudar juntos.

## Conclusão e próximo passo

**Fato novo:** os FPS efetivamente contados na camada SurfaceView também caem; não é mero artefato do contador C2. As duas séries descem na fase final, junto à maior carga GPU e à redução das frequências máximas reportadas. **Não foi demonstrado gargalo específico do SurfaceFlinger nem que alterar `vkQueuePresentKHR`, o modo MAILBOX ou limites térmicos aumentaria o desempenho de modo seguro.**

**Próxima etapa recomendada (PRE154):** fazer auditoria somente leitura do código-fonte **exato** de V31 para identificar onde se medem os timestamps C2, quem controla a fila Vulkan, como se contam swaps e qual telemetria distingue GPU, CPU e compositor. Em seguida propor experimento controlado A/A com cenário, temperatura inicial e tempo iguais; evitar um A/B com qualidade reduzida ou bypass térmico. Nenhum novo teste no telefone é necessário antes dessa auditoria.

**Preservação:** pacote `io.github.nfsmwrecomp`, V31, resolução interna 1920×1080, limite 120 FPS, shaders, efeitos, física, controles e proteção térmica originais. Sem V32. Quando for necessária build futura, `versionCode>=32` e mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.

**Evidências derivadas:** `NFSMW_PRE153_V31_SURFACEFLINGER_INTERVALOS_20261104.csv` (intervalos, sem suavização artificial) e `NFSMW_PRE153_V31_SF_C2_TERMICA_DADOS_20261104.json` (12 amostras, 13 C2 e 45 janelas `PaintAndPresent`).
