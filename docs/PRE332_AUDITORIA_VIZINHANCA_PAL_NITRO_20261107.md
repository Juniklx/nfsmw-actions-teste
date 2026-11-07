# PRE332 — Auditoria de vizinhança PAL do Nitro: 129 shards, sete métodos (2026-11-07)

## Fonte e integridade
- Snapshot PRE99 original autenticado pelo SHA-256 e tamanho fixados no PRE104.
- Original Nitro localizado e autenticado por hash individual no `workspace/nativo/app/generated/default/nfsmw_recomp.66.cpp`.
- Script `automation/kaggle/pre332_nitro_pal_neighborhood_readonly.py`; workflow `.github/workflows/nfsmw-pre332-pal-nitro-neighborhood.yml`.
- Primeira run `42410914389` concluiu `AUDIT_OK`, mas analisou só o shard 66 e encontrou uma das sete funções. Esse resultado não comprovava ausência das outras.
- Script corrigido para percorrer todos os arquivos `nfsmw_recomp.<n>.cpp` PAL; reexecução `42411097708` (job `128519209101`) `completed/success`, relatório `PRE332_STATUS AUDIT_OK`, `PRE332_METHODS_FOUND 7`, `PRE332_OWNER_VERIFIED False`.
- Artefato **13589107516** baixado e inspecionado; fonte do resumo `docs/generated/PRE328_PRE332_SANITIZED_STATUS.json` lida e conferida.

## Sete funções identificadas
| Função | Shard PAL | Linhas na função | Ocorrências textuais do offset 252 | Ocorrências de dispatch indireto |
|---|---|---:|---:|---:|
| `sub_82424820` | `nfsmw_recomp.100.cpp` | 183 | 0 | 12 |
| `sub_82424940` | `nfsmw_recomp.46.cpp` | 99 | 0 | 0 |
| `sub_824249E0` | `nfsmw_recomp.107.cpp` | 172 | 0 | 6 |
| `sub_82424AF0` | `nfsmw_recomp.66.cpp` | 545 | 18 | 30 |
| `sub_82424E58` | `nfsmw_recomp.113.cpp` | 363 | 0 | 3 |
| `sub_82425078` | `nfsmw_recomp.36.cpp` | 87 | 0 | 6 |
| `sub_82425100` | `nfsmw_recomp.60.cpp` | 170 | 0 | 6 |

Ocorrências textuais de dispatch contam, por exemplo, instruções `mtctr`, `bctrl` e chamada `REX_CALL_INDIRECT_FUNC` — **não equivalem ao número de chamadas efetivamente executadas**. Da mesma forma, `offset 252` conta linhas de código e comentários PPC, não stores runtime.

## Estrutura relevante comprovada por PRE323
- `r31 = ctx.r3` no início da função Nitro, via `mr r31,r3`.
- `r31+88` é passado como ponteiro para chamada virtual pelo deslocamento +44 da tabela.
- Campo `r31+72` retorna ponteiro usado para chamar slot virtual +152.
- `r31+52` é lido como outro ponteiro; `r31+296` participa da ramificação de consumo.
- `r31+252` armazena os floats da operação Nitro, corroborado no runtime pela PRE329/PRE330.
- **Nenhum desses fatos identifica semanticamente o proprietário**. Endereços vizinhos no código não demonstram que os métodos compartilham classe ou vtable.

## Segurança e próximo passo
- Sem build/APK, sem patch, sem assinatura, sem save `MARCEK`, sem alterações gráficos/controles/térmica.
- Investigar em etapa separada a origem e a semântica dos ponteiros `r31+52`, `+72`, `+88`, `+296` com fonte PAL autenticada. O único critério para afirmar player owner continua uma correlação independente e verificável entre objeto Nitro e carro controlado pelo jogador, com caso negativo NPC/IA.
- Nitro infinito não funcional; V41 permanece referência. Não gerar V42 baseada apenas na PRE332.
