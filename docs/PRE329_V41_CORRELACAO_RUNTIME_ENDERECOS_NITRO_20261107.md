# PRE329 — Correlação real dos endereços Nitro na V41 (2026-11-07)

## Fonte autenticada
Arquivo `nfsmw.log` fornecido novamente pelo usuário nesta conversa, lido localmente.
- SHA-256: `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc`
- Tamanho: **2.409.694 bytes**
- Linhas: **10.373**
- É o arquivo original PRE321, sem diferença de hash. Tem sessões concatenadas.
- Marcadores no arquivo inteiro: `NFSMW_PRE247_CHEATS_DIAG` **336**; `NFSMW_PRE316_NITRO_CYCLE` **58**.

## Janela V41 selecionada
Intervalo de coleta já identificado pela PRE321: `2026-11-07 15:47:58–15:48:47` (horários do log). Não atribuir os 336 registros PRE247 a essa sessão.

### PRE247: observação direta dos endereços escritos

| Site | Operação | Quantidade de logs | Endereço único observado | Primeiro horário | Último horário |
|---|---|---:|---|---|---|
| 1 | Nitro: consumo | 12 | `0xBFA9E7FC` | 15:47:58.877 | 15:47:59.062 |
| 2 | Nitro: clamp de consumo | 12 | `0xBFA9E7FC` | 15:47:58.877 | 15:47:59.062 |
| 3 | Nitro: recarga | 12 | `0xBFA9E7FC` | 15:48:03.410 | 15:48:03.594 |
| 4 | Nitro: clamp de recarga | 12 | `0xBFA9E7FC` | 15:48:03.410 | 15:48:03.594 |
| 5 | Nitro: caminho alternativo | 0 | Não observado | — | — |
| 7 | Speedbreaker | 12 | `0xBFA7CD34` | 15:48:00.945 | 15:48:01.194 |
| 8 | Speedbreaker | 12 | `0xBFA7CD34` | 15:48:00.945 | 15:48:01.195 |

São **48** logs PRE247 dos sites Nitro 1–4 e **24** de Speedbreaker 7–8 nessa janela, total **72**; número de logs não equivale ao número de stores reais devido ao limite de 12 por site.

- Os 12 pares de valores `written_f32_bits` dos sites **1 e 2** coincidem exatamente, inclusive horário de log.
- Os 12 pares de valores dos sites **3 e 4** também coincidem exatamente; 11/12 horários são textualmente iguais, e um difere em 1 ms, compatível com ordenação de logging.
- Os 4 sites Nitro compartilham o endereço na sessão. O Speedbreaker foi gravado noutro endereço.
- A função PAL Nitro autenticada pela PRE323 escreve o campo offset `+252` a partir de `r31`, com `r31=ctx.r3`. Assim, **o endereço base implícito neste registro é `0xBFA9E700`**, resultado aritmético `0xBFA9E7FC - 0xFC`, sem nova leitura da memória do jogo. Não pressupor estabilidade do ponteiro em outras execuções.

### PRE316 — janela real mais longa
- Os 58 eventos PRE316 V41 capturam checkpoint/esquema resumido de ciclos até 150 amostras de consumo e 2004 amostras de recarga por site, conforme PRE321.
- PRE247 é limitado aos **primeiros 12 registros por site**: ele **não revela diretamente** os endereços das amostras posteriores nem prova que um único objeto esteve ativo ao longo de todas as 2004 gravações.

## Conclusão comprovada e limites
**Comprovado:** os sites 1–4 registraram gravações para o mesmo destino `0xBFA9E7FC` na janela V41; paridade bit a bit dos sites 1/2 e 3/4; Speedbreaker registrou outra localização.

**Ainda NÃO comprovado:** o campo pertence ao carro do jogador de modo exclusivo, que o ponteiro é fixo entre sessões, que site 2/4 sempre é store final autoritativo ou que existe segurança para forçar valor. Endereço guest, por si só, não identifica semanticamente o owner.

**Próximo gate:** em workspace autenticado e descartável, preparar instrumentação passiva limitada por ponteiro/objeto e evento de contexto do veículo, sem escrita guest e sem habilitar cheats. Testar em aparelho de maneira controlada antes de qualquer patch opcional de Nitro.

## Integridade do projeto
Sem nova APK, assinatura, patch de Nitro, mudança do save MARCEK, controles, resolução, shaders ou limites térmicos. Manter V41 assinada como referência, pacote `io.github.nfsmwrecomp` e certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
