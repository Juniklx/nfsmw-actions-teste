# PRE355 — V43: telemetria Nitro por slot em runtime, 2026-11-07

## Arquivo analisado (recebido do usuário)
- `nfsmw.log` recebido neste chat e lido por ferramenta local, em modo somente leitura.
- SHA-256: `b39ff5738a948800dfc94831b0241d705fa216c7d8543fa34d2016a006a04974`.
- 668.545 bytes, 2.766 quebras de linha, 2.767 fragmentos de linhas. Início `20:19:41.096`, último timestamp completo `20:22:27.418`; **o arquivo termina no meio de uma linha de timestamp** (`[2026-11-07 20:22:`). O registro pode estar incompleto.
- Marcadores: PRE348 **108**, PRE336 **50**, PRE316 **180**, PRE247 **72**.
- Resolução interna `1920×1080`, cap `60 FPS` no startup, aquém da meta do projeto de 120; sem prova de ganho de FPS.
- `FATAL EXCEPTION` e `SIGSEGV`: zero correspondências textuais no recorte; não é prova de estabilidade futura.

## Resultado confirmado: três slots Nitro com valores independentes

A PRE336 registrou `distinct=3`, `overflow=false`; PRE348 registrou checkpoints para os slots **1, 2 e 3**. Sites 1/2 são caminhos de consumo, sites 3/4 de recarga. Os pares 1/2 e 3/4 exibiram os mesmos bits nos checkpoints correspondentes. O site 5 não apareceu.

| Slot efêmero | Primeiro consumo | Consumo: primeiros e últimos checkpoints de site 1 | Primeira recarga | Recarga: primeiros e últimos checkpoints de site 3 | Maior `samples` (sites 1/3) |
|---|---|---|---|---|---|
| 1 | 20:21:51.378 | 0,99333 → 0,14667 | 20:21:58.078 | 0,00056 → 0,54778 | 128 / 1024 |
| 2 | 20:22:04.728 | 0,99667 → 0,98667 | 20:22:07.742 | 0,80056 → 0,87109 | 64 / 512 |
| 3 | 20:22:04.878 | 0,99667 → 0,78000 | 20:22:07.928 | 0,79389 → 0,85778 | 128 / 512 |

**Cuidado com checkpoints amostrados:** slot 2 teve mínimo 0,89333 e máximo 0,99667 nos checkpoints de consumo; o último voltou a 0,98667 após possível novo ciclo. A tabela inicial→final não descreve todos os eventos, nem prova um ciclo contínuo. Analogamente, valores de recarga podem oscilar entre ciclos. PRE348 registra apenas primeiro evento e potências de dois.

### Hipótese de owner
- O slot 1 foi o primeiro a apresentar consumo prolongado (de ~99,3% a ~14,7%) e recarga a partir de quase zero. O consumo registrado dos slots 2 e 3 começou cerca de 13 segundos depois.
- **Hipótese contextual:** slot 1 pode ser o veículo controlado pelo jogador, **mas não há vinculação comprovada ao input físico nem referência semântica ao player car**.
- Os números de slots são efêmeros e dependem da ordem de observação; não usar `slot=1` ou endereço guest fixo como filtro de cheat.
- A PRE344 anterior observou quatro objetos numa corrida de quatro carros confirmada pelo usuário. **Na PRE355 observamos três**, mas o novo log está cortado e não foi confirmada aqui a quantidade de carros do novo teste. Não inferir que havia somente três veículos ou que algum carro não tinha Nitro.

## Alertas gráficos separados do Nitro
- `20:21:04.794`: C3 texturas — thread de links desligada por divergência de índice em voo (PRE194).
- `20:21:37.495`: C3 amostragem de fingerprints desligada após 6130 recomprovações devido a divergência.
- Dois eventos C3 no recorte; não provar causalidade com a PRE348. Preservar shaders, gráficos e proteções térmicas.

## Estado e próximo passo
- **V43 PRE352 efetivamente executou** o callback PRE348 no Android; build e assinatura validadas anteriormente no GitHub. Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam desligados.
- Antes de fazer qualquer mudança de consumo, obter confirmação do usuário sobre quantidade de carros no teste da V43 e horários de uso deliberado do Nitro; preferir teste de controle com input conhecido e, finalmente, uma referência player-car independente no código.
- Nenhuma APK/guest/save foi modificada nesta auditoria. Preservar `MARCEK`, V41, V42, V43, controle PG-9076, 1920×1080, shaders e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
