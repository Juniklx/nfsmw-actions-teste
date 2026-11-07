# PRE343 — V42 teste real do Nitro, log recebido em 2026-11-07

## Evidência fonte e integridade
- Usuário forneceu novo `nfsmw.log`; análise local somente leitura, SHA-256 `fafbc46401977eb3bdd71e8982a97b923cf9e15f138291f6abc2bd582025dfb9`, 2.760.655 bytes, 11.966 linhas.
- O log acumula sessões anteriores. **A sessão nova analisada** começa em `2026-11-07 19:22:06` (horário registrado no arquivo) e vai até `19:23:17.946`.
- Marcadores **somente da sessão V42**: 38 `NFSMW_PRE336_NITRO_DIVERSITY`; 58 `NFSMW_PRE316_NITRO_CYCLE`; 72 `NFSMW_PRE247_CHEATS_DIAG`. Totais históricos de arquivo inteiro são diferentes; não misturá-los.
- O novo marcador PRE336 é evidência concreta de que a APK V42 chegou a executar o callback instrumentado. Não confundir com comprovação de controles, FPS ou estabilidade por horas.

## PRE336 — diversidade observada
- Todos os 38 registros: `slot=1`, `distinct=1`, `overflow=false`. O `site_mask` evolui de `0x01` para `0x03`, `0x07` e `0x0F`: sites 1, 2, 3, 4 associados ao mesmo destino temporário.
- Logs por site: 1=8, 2=8, 3=11, 4=11, 5=0. Os checkpoints últimos de site 1/2 são `samples=128`; 3/4 são `samples=1024`. São contagens dos logs limitados por potência de dois, NÃO contagens totais de stores.
- PRE247 na mesma sessão: 12 registros por site 1/2/3/4 para `addr=0xBFA9E7FC`; Speedbreaker sites 7/8, 12 registros cada, em `0xBFA7CD34`. Mesmo endereço de Nitro visto na V41, mas não comprova identidade exclusiva do jogador.

## PRE316 — consumo e recarga confirmados
- Sites consumo 1/2: `n=150`, último float `8.1490725e-7`, aproximadamente zero; max observado `0.99333334`.
- Sites recarga 3/4: `n=1846`, último float `0.99527371`; min observado `0.00055555557`. O último checkpoint registrado **não prova término definitivo da recarga**, mas demonstra recuperação quase completa.
- Nenhum `FATAL EXCEPTION` ou `SIGSEGV` textual encontrado na sessão analisada; isso NÃO prova ausência de travamentos fora do trecho.
- Inicialização da sessão registra resolução interna `1920x1080` e **limite FPS 60**, diferente do objetivo de 120 FPS do projeto. Comparações de desempenho exigem configuração e condição térmica comparáveis; não há ganho de FPS comprovado.

## Conclusões e bloqueios
- **Verificado:** V42 executou, as sondas PRE316/PRE336/PRE247 funcionaram no novo runtime e o ciclo de consumo/recarga permaneceu observável.
- **Não verificado:** dono exclusivo player do slot 1, presença/ausência de NPCs com Nitro, execução sem falhas por período longo, teste PG-9076, 120 FPS ou cheat funcional.
- Um objeto observado não significa que só exista um objeto no jogo. PRE336 não classifica sem referência independente player/NPC.
- Nenhuma alteração de APK, save `MARCEK`, assinatura, gráficos, física ou proteção térmica foi aplicada na PRE343; ela apenas analisa o log.
- **Próximo gate recomendado:** teste controlado que provoque contextos distintos de veículo, ou fonte PAL independente demonstrando player owner. Não forçar float nem hardcode `0xBFA9E7FC`. Manter V42 diagnóstica e V41 como backup, certificado permanente e incrementar versionCode numa eventual V43.

## Arquivo de auditoria local
`PRE343_V42_NITRO_RUNTIME_AUDITORIA.json` gerado nesta conversa com contagens, checkpoints por site, fingerprint e ressalvas; não inclui dados de assinatura privados.

## Adendo de contexto do teste informado pelo usuário — 2026-11-07
O usuário esclareceu após a análise: **a coleta PRE343 da V42 foi realizada fora de corrida, em exploração livre, com apenas o próprio carro no mapa, sem adversários presentes**. Esta informação não foi deduzida do log; é descrição fornecida pelo responsável pelo teste.

Interpretação revisada: `distinct=1` e `slot=1` são consistentes com o único carro presente, reforçando a hipótese de que o objeto pertence ao jogador **naquela situação**. Porém, um objeto Nitro registrado não garante que a rotina não processaria veículos de IA em corridas, não identifica owner semanticamente e não demonstra ausência de outros objetos que não passaram pela função.

**Próximo experimento controlado com a mesma APK V42:** entrar numa corrida com veículos adversários, consumir e recarregar Nitro, coletar novo `nfsmw.log` e comparar diversidade PRE336, sem alterar jogo ou save. Se continuar um slot, ainda será necessário distinguir se a função é exclusiva do jogador ou se a IA não usa esse caminho. Não criar cheat com base somente nesses contadores.
