# PRE407 — V46 global Nitro funciona; decisão da IA não está instrumentada (2026-11-08)

## Base verificada
- Novo arquivo `nfsmw.log` enviado pelo usuário. SHA-256 **`f7955f5e7dcd69dec69660e3c2a50ceb41dd779b9952f3f2c1169713e338fbd7`**, 529.809 bytes, 2.238 linhas.
- Janela da sessão: `2026-11-08 00:14:05.210` a `00:16:06.986`.
- **Depoimento do usuário:** Nitro infinito funcionou no teste em jogo; ele notou que os oponentes parecem não aproveitar o recurso infinito.
- PRE398 único às **00:14:30.053**: `NFSMW_PRE398_GLOBAL_NITRO_FULL active=1 affects_all_objects=1 full_bits=0x3F800000`.
- **82** checkpoints `NFSMW_PRE348_NITRO_SLOT_VALUES`; os 82 têm `written_f32_bits=0x3F800000` (float32 1.0). Os sites observados foram **1 e 2**; slots efêmeros **1,2,3,4**. Todos esses quatro slots têm checkpoints 100%; nos sites 3–5 não houve checkpoint PRE348 nesta sessão.
- `NFSMW_PRE336_NITRO_DIVERSITY`: 30 entradas, `distinct=4`, sem `overflow=true`. Há 44 entradas PRE383 e 65 PRE364, das quais seis eventos têm `buttons=0x2000`; isso é **input humano do usuário 0**, não entrada dos veículos IA.
- Na sequência: slot 1 aparece às **00:14:30.053**; slot 2 às **00:15:17.968**, slot 3 às **00:15:24.968**, slot 4 às **00:15:26.268**. Slot é índice por ordem de observação, não identidade/espécie de participante confirmada.
- A mensagem `NFSMW_PRE194_C3` às 00:14:26.183 desativou o thread de ligação de texturas por divergência, evento técnico distinto do Nitro. Não houve texto `FATAL EXCEPTION` nem `SIGSEGV` neste log, não equivale a prova de estabilidade universal.
- Startup registrou resolução interna **1920×1080** e `limite de FPS 60`; a V46 não comprovou 120 FPS.

## Conclusão
- **Comprovado por instrumentação:** o patch ativo faz as gravações do Nitro permanecerem 100% em quatro destinos distintos (sites observados 1/2); usuário confirmou Nitro infinito funcionando em seu carro.
- **Não comprovado:** quais destinos são adversários, se cada IA aciona Nitro, com que frequência/tempo, se a força do boost é mantida, ou se o comportamento estratégico mudou. O log **não contém sinal de comando de Nitro por IA**.
- **Hipótese compatível:** a IA continua usando as decisões originais de boost, pois PRE398 altera cinco gravações de nível do medidor sem alterar política de decisão de IA. Um carro pode ter recurso infinito e usá-lo de modo intermitente. Também é possível que IA use Nitro conforme lógica própria, sem a telemetria atual permitir observar isso.
- **Não é necessário mudar o cheat global para corrigir algo que não foi demonstrado como bug.** Se o usuário desejar aumentar uso de Nitro pela IA, primeiro localizar e instrumentar passivamente a rotina de decisão/efeito do Nitro por veículo, distinguindo efeitos de mudanças na física e balanceamento; evitar simplesmente forçar o mesmo botão XInput para todos os carros.
- Preservar V46, save `MARCEK`, chave permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, gráficos/shaders/física/controles e proteções térmicas. Não gerar V47 sem objetivo técnico e testes fail-closed.

Relatório JSON local: `PRE407_V46_NITRO_GLOBAL_ANALISE_IA.json`.
