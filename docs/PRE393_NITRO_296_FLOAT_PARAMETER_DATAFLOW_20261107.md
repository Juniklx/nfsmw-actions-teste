# PRE393 — Análise de `r31 + 296` no medidor Nitro PAL (2026-11-07)

## Evidência executada
- Run GitHub Actions [42438407333](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42438407333), `completed/success`; artifact `13599918607`, `PRE393_NITRO_296_DATAFLOW.json`, `AUDIT_OK`.
- Snapshot PRE99 autenticado; shard `nativo/app/generated/default/nfsmw_recomp.66.cpp` SHA-256 `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`. Função `sub_82424AF0`, 545 linhas.
- Três leituras textuais de `REX_LOAD_U32(r31.u32+296)`, conferidas pela contagem exata, nos trechos relativos 136, 267, 370. Nove referências textuais de `+252` dentro da mesma função (4 loads / 5 stores da PRE334).

## Fluxo observado
| Linha relativa | Destino da leitura de +296 | Acessos seguintes via referência |
|---|---|---|
| 136 | `r30.u64` | `r30+28`, `r30+24`, `r30+12`, `r30+20` |
| 267 | `ctx.r11.u64` | `r11+16` e `r11+0` |
| 370 | `ctx.r8.u64` | `r8+4` |

- Os valores nos offsets derivados entram por leituras `REX_LOAD_U32`, convertidas para ponto flutuante e usadas em fórmulas de consumo/recarga, comparações e interpolação. Na linha 370, por exemplo, após ler `r8+4`, a função já havia calculado e armazenado o resultado do Nitro em `r31+252`.
- **Inferência, não tipo comprovado:** `+296` parece apontar uma estrutura de parâmetros/tuning do Nitro, e não uma identidade semântica direta do carro do jogador. Os símbolos de tipo e significado original dos campos não aparecem na fonte.
- O caminho de entrada do Nitro também lê `r31+136` e utiliza referências `r26`/`r28`. A origem e finalidade dessas referências exigem análise separada; **não qualificá-las como player-car sem prova**.
- Uma auditoria textual limitada a janelas não exclui alias, ponteiros diferentes em caminhos alternativos ou dados estruturais relevantes em outro endereço.

## Decisão
- PRE392 V45 observou `LR=0x824252DC` em ambos os slots amostrados. **LR isolado não distingue o jogador.**
- PRE393 demonstra que os três acessos a `+296` são usados como fontes de parâmetros numéricos. Não habilitar cheat com base apenas em LR, `slot=1/2`, endereço guest fixo ou `+296`.
- Nenhum APK, arquivo do jogo, save `MARCEK`, assinatura, controle ou limite térmico foi modificado; `owner_verified=false`, `cheat_enabled=false`.
- **Próximo gate:** rastrear passivamente a origem das referências `r26`, `r28` e `r31+136` dentro da função Nitro, avaliando se existe ligação estrutural independente ao carro controlado. Se forem apenas constantes de física, descartar a hipótese. Preservar V45 como referência; eventual V46 requer `versionCode=46` e assinatura permanente original.
