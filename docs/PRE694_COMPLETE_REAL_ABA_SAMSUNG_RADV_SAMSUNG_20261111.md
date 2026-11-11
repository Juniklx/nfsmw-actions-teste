# PRE694 — A/B/A concluído: Samsung Proprietary → RADV Xclipse v1.8.0 → Samsung Proprietary (11/11/2026)

## Verificação dos artefatos

- Os cinco arquivos do `nfsmw3.zip` foram extraídos e auditados em leitura; ZIP CRC **PASS**; tamanho **222,499 bytes**, SHA256 `c975a3800f2a89afb2c4312fcdedcacf4975bb1a89b1a289609a062e22cc4cf1`. Hashes de status, captura e manifesto conferidos contra `PRE694_PHASE_CAPTURE_VALIDATED.txt`. **30/30 amostras não vazias**, exatamente uma SurfaceView NFSMW avançando.
- `SAMSUNG_A2` rótulo de fase confirmado pelo manifesto, **driver de fato confirmado por** `driverID: SamsungProprietary`, `driverName: Samsung Proprietary driver`, `driverInfo: SPAL Driver version: 25.3.3`. Interna 1920×1080, limite 60 FPS, Vulkan `MAILBOX`, quatro imagens, atualização do compositor 120Hz (`8333333 ns`).
- Sessão A2 única no log de **16:35:14.002 a 16:39:35.322** (**261,320 s; 4m21s**). SurfaceFlinger 16:37:00–16:37:39, 3.653 triplas válidas, 2.314 presents únicos, 1.339 duplicatas removidas; **2.312 intervalos contínuos**, sem conflitos de timestamps. Lacuna de **1.040,949 ms** excluída por perda de cobertura de snapshots; **não** é travada comprovada.
- Baselines A1 e B lidos dos pacotes de auditoria preservados, com métricas originalmente computadas do mesmo método de `actual_present_ns`. V51 e sua assinatura/certificado permanente não foram alterados.

## Comparação real — janela ordenada de aproximadamente 39 segundos por fase

| Métrica | Samsung A1 | RADV B | Samsung A2 |
|---|---:|---:|---:|
| FPS estimado de presents contínuos | 59.998 | 59.988 | **59.976** |
| Presents únicos | 2,329 | 2,319 | 2,314 |
| Intervalos contínuos válidos | 2,327 | 2,317 | 2,312 |
| Desvio-padrão real do intervalo | 3.847 ms | **3.738 ms** | 3.996 ms |
| 8–9 ms | 242 | 214 | 250 |
| 25 ms | 238 | 195 | 243 |
| Alternâncias diretas 8↔25 ms | **278** | **216** | **271** |
| Intervalos arredondados ≥33 ms | 2 | 7 | 4 |
| Marcadores `[vigilante]` | 0 | 0 | 0 |
| Duplicidade C3 `copia_duplicada=true` | 1 | 1 | 1 |

**Comparação:** o RADV apresenta **21.31% menos alternâncias** em relação à média descritiva de Samsung A1/A2 (274.5), e **4.69% menos desvio-padrão** (3.922 ms contra 3.738 ms). O retorno ao driver Samsung reproduziu a maior alternância — um resultado consistente com associação ao driver. Entretanto, RADV teve **7 intervals ≥33ms**, contra **2/4** no Samsung, incluindo **um de 50ms**. Assim, **não é correto declarar que RADV é uniformemente mais fluido ou estável**. Os três mantêm FPS médio estimado ~60 e **não houve ganho de FPS**.

## Eventos C3, watchdog e C2 na Samsung A2

- **Sem alerta `[vigilante]`** nos ~4m21s do log A2. A1 também apresentou zero em ~4m30s, e B zero em ~7m49s. A PRE692 histórica teve travadas no RADV, não repetidas na B; isso não demonstra correção ou ausência de risco em sessões longas.
- **C3 reapareceu na A2 em 16:35:39.577**, `indice=0`, `en_vuelo=1`, `frame=textura_frame=1373`, `epoca_ahora=epoca_primera=1373`, `offset_primera=0`, `offset_segunda=51872`, `mismos_comandos=true`, `subir=true`, `trabajo_huella=0`, `datos_bytes=43648`. Guard `[NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true]`: desligou o thread auxiliar e preservou fallback normal. A assinatura comum não prova conteúdo da cópia idêntico nem a origem do defeito.
- Na janela SF, relatórios internos C2 terminados às **16:37:14.732** e **16:37:34.746**: respectivamente **1.200/1.201 Swaps em ~20s**, 1.156/1.166 dentro de 15–18ms, GPU real por Swap **9,00/8,98ms** (métrica GPU emitida um milissegundo antes da linha de histograma). A taxa interna e timestamps SF não são intercambiáveis.
- O log A2 registrou quatro eventos `[tiron] fotograma de`: **66,5ms, 99,6ms, 99,3ms, 112,9ms**, todos às **16:35**, fora da janela SF. Não relacioná-los à cauda de intervalos capturados 16:37.

## Interpretação e próximo passo

- **Hipótese plausível:** a sequência frequente de presents curtos (~8ms) e longos (~25ms) pode contribuir para a sensação de fluidez semelhante à de 30 FPS apesar da média de ~60 FPS. O efeito perceptivo e a causa técnica exata **não foram medidos diretamente**.
- As diferenças são observacionais; não medimos repetibilidade estatística em múltiplas rondas A/B/A, nem estado térmico/clock/energia/cenas absolutamente idênticos. A fase A2 foi mais curta que a fase B. Não atribuir causalidade exclusivamente ao driver ou tratar como otimização comprovada.
- **Recomendação:** manter APK **V51** e fallback C3, sem alterações gráficas, de física, CPU/GPU clocks, controlo PG-9076, segurança térmica ou assinatura permanente. Se a prioridade é evitar intervalos longos, Samsung continua referência prudente; se é minimizar alternância 8↔25ms, RADV merece teste subjetivo adicional, com ressalvas de estabilidade. Para otimização real, próximo estudo read-only do caminho de temporização Vulkan/SurfaceFlinger sob 120Hz e limite de 60 FPS, com medição térmica simultânea e desenho de teste pareado antes de patch.

## Arquivos preservados

- Original A2 no Google Drive (verificar metadados e hash): https://drive.google.com/file/d/1GWMcMaxVlpdKBc-2pUwTEmMAcM_P5hcX/view (SHA256 `c975a3800f2a89afb2c4312fcdedcacf4975bb1a89b1a289609a062e22cc4cf1`, bytes readback idênticos).
- Originais A1 e B armazenados em Drive conforme os checkpoints PRE694 anteriores; B original: https://drive.google.com/file/d/1VSS7F52_t1XCgbdotMp7tsrT6-odqwZ5/view.
- JSON de comparação `NFSMW_PRE694_ABA_COMPARACAO_VERIFICADA_20261111.json`; A2 JSON; analisador read-only; ZIP de evidências **sem nfsmw.log bruto** como apêndice.

**STATUS PRE694:** A1_REAL_PASS, B_REAL_PASS, A2_REAL_PASS, COMPLETE_ABA, ALL_C3_SHARED, ZERO_WATCHDOG_IN_RECORDED_SESSIONS, RADV_CENTRAL_JITTER_LOWER_OBSERVED, RADV_LONG_TAIL_WORSE_OBSERVED, DRIVER_CAUSALITY_UNPROVEN, FPS_GAIN_UNPROVEN, NO_NEW_APK.


## Auditoria reproduzível e fonte privada
- [ZIP sem log bruto com JSON e analisador](https://drive.google.com/file/d/1TPG4bQ-fcYbFlFihFjltflgJyyUsKixy/view)
- [ZIP bruto A2 armazenado somente no Drive](https://drive.google.com/file/d/1GWMcMaxVlpdKBc-2pUwTEmMAcM_P5hcX/view)
- [Relatório canônico de análise no Drive](https://drive.google.com/file/d/1F0YYoltmuJHStWNR7e4BpB1P19Dox_dE/view)

**Sem upload de log bruto, código proprietário, APK, credenciais ou chave privada ao GitHub público.**
