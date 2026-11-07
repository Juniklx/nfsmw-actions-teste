# PRE330 — V41: consistência temporal dos endereços do Nitro (2026-11-07)

## Fonte e execução
- Entrada: arquivo original `nfsmw.log` fornecido pelo usuário, SHA-256 `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc`, 2.409.694 bytes.
- Análise Python **realmente executada** localmente, somente leitura, marcadores `NFSMW_PRE247_CHEATS_DIAG`.
- Resultado local: `PRE330_STATUS AUDIT_OK`; `PRE330_GROUPS 4`; `PRE330_PARSED_NITRO_EVENTS 192`; `PRE330_OWNER_VERIFIED False`.
- Dos 336 marcadores PRE247 totais (Nitro + Speedbreaker), foram identificados 192 registros de Nitro, sites 1–4.
- Agrupamento por início de novo bloco de site 1 afastado por mais de 90 segundos. **Grupos temporais NÃO equivalem automaticamente a processos Android distintos.**

## Grupos observados

| Início (log local) | Fim PRE247 (log local) | Site 1 | Site 2 | Site 3 | Site 4 | Site 5 | Destino dos sites 1–4 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 14:53:07.907 | 14:53:24.355 | 12 | 12 | 12 | 12 | 0 | `0xBFA9E7FC` |
| 14:57:49.329 | 14:57:54.048 | 12 | 12 | 12 | 12 | 0 | `0xBFA9E7FC` |
| 15:05:09.827 | 15:05:14.544 | 12 | 12 | 12 | 12 | 0 | `0xBFA9E7FC` |
| 15:47:58.877 | 15:48:03.594 | 12 | 12 | 12 | 12 | 0 | `0xBFA9E7FC` |

- **Confirmado:** nos 192 eventos logados, os quatro sites Nitro escreveram no mesmo endereço virtual guest `0xBFA9E7FC`; site 5 sem evento PRE247 em nenhum grupo.
- **Não confirmado:** a propriedade exclusiva por veículo/jogador, isolamento entre processos, estabilidade em outro aparelho/memória, identidade do store final, ou resultado do cheat.
- PRE247 tem limite de 12 linhas/site/processo e não identifica o destino de todos os stores posteriores; PRE316 cobre checkpoints mais longos, mas sem endereço por amostra.
- Base implícita, dada a fonte PAL verificada `r31=ctx.r3` e offset `+252`: `0xBFA9E700` apenas nestes registros, sem leitura extra da memória.

## Critério para prosseguir
Não aplicar patch de Nitro infinito com base apenas na estabilidade deste endereço. Requer-se evidência de `owner` em execução, correlação com referência autenticada de veículo do jogador, teste negativo com NPC/IA e, somente depois, opt-in fail-closed com OFF idêntico ao original.

## Integridade
PRE330 somente analisou log já coletado. Nenhuma APK, assinatura, segredo, save `MARCEK`, alteração de código do jogo ou ajuste gráfico/térmico foi feita.
