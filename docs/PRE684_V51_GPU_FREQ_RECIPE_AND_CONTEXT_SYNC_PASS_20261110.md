# PRE684 — auditoria da receita V51 e da telemetria GPU PRE656: PASS

Data de referência: 2026-11-10 (Bahia); relatório gerado 2026-11-11 UTC.

## Execuções verificadas

- GitHub Actions auditoria: **run 42935465892**, job **130244338759**, conclusão `completed/success`.
  - https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42935465892
- Commit de gatilho: `30bec0b1aa7065ff47f409656f0e19b7bd3687ab`.
- ZIP privado: `NFSMW_PRE684_V51_RECIPE_SHADER_FREQUENCY_20261111_005933.zip`, Drive ID `1AXjA3oiLABjKi9_cP7Jx_esHH0evOzS2`, 2.228 bytes, SHA256 `033ce359372741cb6dc86dfa607f8a9625a3e19b6ad20d9a27e801c16b198ab8`, CRC PASS. Contém `PRE684_REPORT.json` e `PRE684_README.md`.
- APK V51 PRE652 original: 47.104.417 bytes, SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`.
- Log PRE656 original: 576.129 bytes, SHA256 `649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7`.

## Evidência técnica

- Receita PRE651/PRE652 e cabeçalho PRE648 conferidos estruturalmente, com SHA256 do header `9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe`. O estágio V50 precede uma aplicação prevista do patch PRE648. **Não houve replay da árvore de fontes nem compilação ARM64** nesta etapa.
- Marcador textual `PRE648 GPU_SHADER10s` existe 1 vez em `lib/arm64-v8a/libmain.so` PAL e zero vezes em `libmain_usa.so` USA. Entre todas as bibliotecas .so da V51, o marcador está somente no PAL.
- O log real PRE656 do Galaxy S24 FE contém **14 linhas** `PRE648 GPU_SHADER10s`. Isso demonstra que a instrumentação PAL registrou eventos na sessão; sem leitura independente de mapeamentos de bibliotecas do processo, não declarar `/proc/maps` confirmado.
- Somatórios dos contadores em 14 janelas: **14.265.243 draws**, **14.258.146 normais**, **7.097 céu adiado**, **0 IDs inválidos**. Em cada linha, a lista publicada é parcial: 8 pares no primeiro registro, 12 em cada um dos 13 seguintes.
- Combinações mais frequentes nos pares publicados: `p2/VS62/PS58` (2.186.797 draws reportados) e `p1/VS43/PS37` (1.934.821). Não são medições de tempo ou causalidade de gargalo, e as listas truncadas não são a totalidade dos draws.
- Sete amostras `C2: GPU por Swap`: medianas de **2,95 ms** cena, **1,94 ms** cópias, **1,33 ms** rubrica *cubo e desfoque juntos*, **0,59 ms** sombras, **0,82 ms** reflexos e **7,56 ms** de intervalo entre trabalhos. Não interpretar o intervalo agregado como medição isolada de frame pacing.
- Nota de apresentação: no ZIP emitido pelo run aprovado, o campo JSON `reported_top8_draws` denomina os valores acumulados dos pares listados (8/12 por janela). O nome do campo foi tornado mais preciso no script do GitHub posteriormente; isso **não altera o ZIP assinado por hash nem os números do run**.

## Contexto canônico sincronizado e comprovado

- Backup original e idêntico: Drive ID **1ZhWEuV4javfU2EhDcmlK-9Zsp22rSJ2F**, salvo em `04_Backups`.
- Workflow de sincronização: GitHub run **42936427023**, job **130247509616**, `completed/success`. https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42936427023
- `NFSMW_Android/CONTEXTO_NFSMW.md` atualizado mantendo ID **1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB**; arquivo final **1.133.187 bytes**, SHA256 **163b67a4551cd778677e2d4b4b756cefd1bd2385b3a7f74eb3f586f75f3af84f**, readback confere com recibo.
- Recibo de sincronização privado: `NFSMW_PRE684_CONTEXT_SYNC_20261111_010619.json`, Drive ID **1WFuJhFAfUmYO3BV8BqE2kh22dsGeIisK**. Os resultados PRE681/PRE682/PRE683/PRE684 foram registrados no contexto.

## Limites e próximo gate PRE685

- A confirmação da presença de argumentos e strings não prova os valores de cvars ativos no S24 FE. O screenshot mostra as escolhas no menu, não o renderizador. O arquivo PRE656 confirma resolução interna 1920×1080 e cap 60 naquela sessão; o alvo de até 120 FPS não estava ativado.
- PRE684 não altera shaders, efeitos, física, controles, saves, térmicas, APK nem assinatura. V51 PRE652 e certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` preservados.
- PRE685: confirmar gráficos realmente aplicados e investigar *frame pacing*. Propor coleta limitada, verificável e reversível de cvars/argumentos e intervalos reais de apresentação; não atribuir percepção de 30 FPS a um shader sem evidência. Instrumentação Android futura exigirá autenticar árvore exata, versão incremental e assinatura permanente. Não tornar artefatos privados públicos.

STATUS: PRE684_ACTIONS_PASS; PRE684_PRIVATE_REPORT_PASS; CONTEXT_SYNC_PASS; GPU_COUNTS_OBSERVED; LIVE_CVARS_UNKNOWN; NO_APK; NO_FPS_GAIN.
