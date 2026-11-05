# NFSMW — PRE156 A1 — coleta pareada V31 (4 de novembro de 2026)

**Estado:** primeira sessão de campo da PRE156 concluída e analisada offline. **A/A com duas execuções ainda NÃO concluído.** O arquivo `nfsmw.1.log` é um log histórico com a parte inicial da sessão de 22h49, e `nfsmw.log` é sua continuação após rotação; não são duas execuções distintas.

## 1. Fontes originais e cadeia de custódia

| Arquivo anexado original | Tamanho | SHA-256 |
|---|---:|---|
| `nfsmw_pre152_v31_surfaceflinger_20261104_224943_20690.txt` | 127253 bytes | `0f67a19b0c79fd85ad19004ad03bbb5a5bfd5164e27ffa98c2143051fd9c94b0` |
| `nfsmw.1.log` | 5241102 bytes | `8f5e0f51197a484e6c4c12ae95f80a3e66fd28e167d8e2fa5ae1a1854217ede9` |
| `nfsmw.log` | 89989 bytes | `ee5d9ff59c8b15f6595732c0693437de3650afee4b27d3179061e5f07c5919e7` |

Os três arquivos brutos foram copiados sem editar seu conteúdo para `NFSMW_Android/06_Logs_e_Medicoes`:
- [SurfaceFlinger original](https://drive.google.com/file/d/1RS68AK7hzzx_T5yk61o2LYfDbcm-0YPt/view)
- [nfsmw.1.log, histórico + início](https://drive.google.com/file/d/1otYLKLrxPBD4pkf4muRmxwa3dlx8c2tM/view)
- [nfsmw.log, continuação](https://drive.google.com/file/d/1nqljCJ7VQYbzlickp8Mw9ODBdoK07N2V/view)
- [CSV — 12 amostras e 11 intervalos](https://drive.google.com/file/d/1OlmHFXItuDpZPTjoHYYtbkNqAQF_S2TT/view)

O relatório ignora todas as sessões antigas do log histórico e usa somente 2026-11-04 22:49:43–22:53:58. A geração separa os fluxos antes e depois da rotação; as amostras permanecem na mesma sessão, com contador cumulativo do C2 crescente.

## 2. Validação da sessão física

- Começo do script em **22:49:43 (-03:00)**, `UID_SHELL=2000`, `VERSION_CODE=31`, `AM_START_RC=0`, `GameActivity` confirmado; swapchain registrado às 22:49:44 em **1920×1080, MAILBOX e quatro imagens solicitadas**. `ENABLE_RC=0`.
- 12 amostras SurfaceFlinger no mesmo `SurfaceView[...GameActivity]@0(BLAST)#59208`, 11 diferenças válidas de contador, com intervalos de 21 segundos. A camada `VRI` de UI não entra no FPS.
- `STATUS_FINAL=COLETA_ENCERRADA`, `REMOTE_RC=0`. `SF_TIMESTATS_DISABLE_TENTADO=1` indica tentativa de limpeza global, **não prova isoladamente que a desativação obteve êxito**.
- Log inicia `conduciendo` às 22:50:01, muda para `cinematica` às 22:50:02 e retorna a `conduciendo` às **22:50:50** (âncora de início da jogabilidade estática). A transição `pausa` às 22:53:57 ocorre **após** a última amostra de 22:53:55.
- Configurações registradas: jogo 1920×1080 internos, limite 120 FPS, modo virtual 1280×720 @120Hz. Não há patch, mudança de APK nem versão nova nesta etapa.

## 3. Desempenho na jogabilidade estática

A primeira janela inteiramente após o início da jogabilidade, **22:51:07–22:51:28**, registra `totalFrames` crescendo 8.408→10.776, ou **112.762 FPS**. No último intervalo, **22:53:34–22:53:55**, o contador cresce 24.127→26.204, ou **98.905 FPS**. Diferença observada **-12.29%**. Não usar o `averageFPS` cumulativo como taxa instantânea.

No motor, janelas C2 próximas, mas não quadro a quadro alinhadas:

| Métrica | Janela 22:51:44 | Janela 22:53:44 | Mudança observada |
|---|---:|---:|---:|
| FPS C2 estimados por delta `presentados`/20s | 112.45 | 100.50 | -10.63% |
| GPU real por Swap | 7.05 ms | 8.41 ms | +19.29% |
| `RefreshGuestOutput: despues` | 1.13 ms | 3.24 ms | +186.73% |

- 12 relatórios C2, com 11 deltas de FPS calculáveis e 11 calibrações acumuladas de timestamps GPU exibidas como `1.000`. Arredondamento dos fatores impede afirmar igualdade matemática absoluta do clock.
- **44 relatórios** de `PaintAndPresent` com 600 quadros cada = **26.400 quadros** instrumentados. `vkQueuePresentKHR` média por janela **1.516 ms**; `PaintAndPresent` média **1.711 ms**; parcela média **88.6% do apresentador, NÃO do quadro todo**. Primeira/última janela de `vkQueuePresentKHR` = **0.27/3.36 ms**.
- `RefreshGuestOutput: despues` e `vkQueuePresentKHR` são parcialmente sobrepostos e não devem ser somados. A espera CPU de apresentação não é, por si só, prova de gargalo do compositor Android.

## 4. Termal, bateria e limitações do teste

- `Thermal Status`: 0 na amostra de 22:50:04; 1 a partir de 22:50:46; 2 a partir de 22:51:28 até o fim. `SKIN` **36,8→44,6 °C**, `BAT` **36,2→45,1 °C** e `AP` **45,6→65,8 °C** nas pontas; AP não representa temperatura da pele.
- GPU devfreq: primeiro `cur_freq/max_freq` bruto **1095000/1095000**; último **450000/400000** na primeira leitura e 450000/450000 na segunda. São leituras sequenciais, não atômicas; a inconsistência cur>max no mesmo registro não autoriza inferir frequências físicas exatas ou throttling exclusivo.
- **Bateria descarregando: 19%→13%** em ~4 min. Não há confirmação de modo Economia de energia, mas essa condição torna a sessão inadequada como par A/A controlado com outra coleta de carga distinta.
- Referência histórica [PRE153](https://drive.google.com/file/d/1Inv-jPEwlkYx_O_4RgpU3kV5Em0MHXyX/view): SurfaceView pico **116,33** e último **91,29 FPS**, com SKIN inicial **35,6 °C**. PRE156-A1 tem **36,8 °C** iniciais e perfil de FPS distinto. Isso demonstra que existem resultados entre sessões, **não que uma tenha sido mais eficiente**, pois bateria, temperatura de entrada e janelas não foram igualadas.

## 5. Decisão e próximo passo

**Resultado:** queda de FPS apresentado de **12.3%** após o início da jogabilidade estática nesta sessão, acompanhada de aumento de custo GPU e de espera em `vkQueuePresentKHR`, e de status térmico 0→2. Consistente com pressão térmica, mas não demonstra causalidade única, tampouco defeito independente no SurfaceFlinger. O teste A/A da PRE156 **continua incompleto**; o par de logs rotativos não conta como segunda sessão.

**Recomendação para recomeçar o protocolo A/A válido:** carregar naturalmente para faixa **50–80%**, depois desconectar e aguardar resfriamento, sem burlar políticas térmicas. Registrar SKIN inicial semelhante (ideal diferença ≤1 °C), bateria aproximada, mesmo modo história e carro parado, repetir a mesma V31 em duas sessões separadas com resfriamento entre elas. A coleta das 22:49 permanece como evidência diagnóstica, mas não entra como par de controle com bateria muito diferente. Não prosseguir com novo ensaio a apenas 13% de bateria.

**Restrições:** preservar V31 `io.github.nfsmwrecomp`, 1920×1080 internos, 120 FPS, shaders, efeitos, física, controle PG-9076, configuração privada, APKs, back-ups e proteções térmicas. Nenhum ganho de FPS comprovado, nenhuma V32 gerada, nenhum patch de sincronização aplicado. A próxima release, se vier a ser tecnicamente justificada, exige `versionCode>=32` com a mesma assinatura permanente.
