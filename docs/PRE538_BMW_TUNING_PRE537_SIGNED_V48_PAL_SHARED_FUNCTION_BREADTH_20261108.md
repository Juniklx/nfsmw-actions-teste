# PRE538_BMW_TUNING_PRE537_SIGNED_V48_PAL_SHARED_FUNCTION_BREADTH_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW-Recompiled-Mobile, Need for Speed: Most Wanted (2005), Xbox 360 PAL → Android, investigação da tunagem real da BMW M3 GTR carreira. **Base preservada:** APK release V48 PRE452, Nitro PRE398, controle físico PG-9076, save `MARCEK`, gráficos, física, 1920×1080, teto 120 FPS, limites térmicos e certificado release permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.

## PRE537 — evidência estrutural guest, não funcional
- [Execução PRE537 42537704457](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42537704457) `AUDIT_OK`; `docs/PRE537_ORIGINAL_V48_PAL_SHARED_NODES_STRUCTURAL_TRIAGE_READONLY.json`.
- APK original V48 SHA-256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`, `libmain.so` PAL SHA-256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3` reautenticados antes da leitura.
- Todo o conjunto de **56.338** funções numéricas guest foi varrido, nenhuma omitida, **21.439.048 bytes ARM64** cobertos e **76.786** instruções `BL` guest resolvidas pela PLT original. `.rela.plt` mantém **17.107** JUMP_SLOT, **15.598** entradas guest.
- Métrica de **chamadores distintos** = número de funções guest cujas instruções `BL` resolvem para a função-alvo. **Regiões** = agrupamento por 16 bits superiores do endereço guest. Essas métricas não demonstram nenhuma ação executada em jogo.

| Função guest | Corpo ARM64 (bytes) | Chamadores distintos | BL recebidos | Regiões |
|---|---:|---:|---:|---:|
| `sub_823EAE40` | 2964 | 7 | 9 | 5 |
| `sub_822CC740` | 488 | 27 | 30 | 6 |
| `sub_821E02C0` | 352 | 29 | 32 | 17 |
| `sub_82284CC0` | 428 | 35 | 102 | 12 |
| `sub_822FEB70` | 684 | 55 | 93 | 18 |
| `sub_82282A70` | 244 | 78 | 140 | 14 |
| `sub_820E25C0` | 32 | 145 | 290 | 18 |
| `sub_82284E88` | 316 | 161 | 237 | 17 |
| `sub_822BCE60` | 472 | 181 | 970 | 24 |
| `sub_82152A38` | 420 | 294 | 595 | 46 |
| `sub_8227FD70` | 316 | 346 | 1014 | 19 |
| `sub_8215CB08` | 1732 | 562 | 1030 | 66 |

### Achados e limitações
- `sub_823EAE40`: **2.964 bytes**, **741 instruções**, **7 chamadores distintos**, **9 BL de entrada** em 5 regiões. Chamadores verificados: `sub_8226B228`, `sub_8226B4C0`, `sub_8254E908`, `sub_8255C1C8`, `sub_82566BE8`, `sub_8256CE68`, `sub_82584880`. PRE535 demonstrou o caminho de lista `sub_82582F70→sub_8256CE68→sub_823EAE40` e o de escrita histórica B `sub_82564D80→sub_8254E908→sub_823EAE40`. **Isso não prova o papel da função.**
- `sub_822CC740`: **27 chamadores** (30 BL, 6 regiões). Outro ponto relativamente restrito para investigar, sem classificação funcional.
- `sub_820E25C0`: corpo **32 bytes/8 instruções**, sem `BL` de saída, **145 chamadores**; sinal de auxiliar altamente reutilizado, não identidade confirmada de rotina de memória.
- `sub_8215CB08` possui **562 chamadores** em **66 regiões**, **1.030 BL** de entrada; essa presença ampla reduz a especificidade do nó para identificação de transação/instalação. Outros nós amplamente chamados incluem `sub_8227FD70` (346), `sub_82152A38` (294) e `sub_822BCE60` (181).
- **Nenhuma** das 12 interseções foi identificada positivamente como `Physics::Upgrades::SetPackage`, `Checkout`, débito monetário, carregador VPAK ou instalação de pacote. Nomes PC continuam sem mapeamento funcional guest; auditoria estática não equivale a execução no S24 FE.

## Próximo gate — PRE539, ainda sem patches
1. Investigar os **7 chamadores** da função menos difundida `sub_823EAE40` e as instruções próximas aos respectivos `BL` para distinguir código comum de relação com a oficina. Usar assinatura estrutural/fluxo verificado, não nomes presumidos. Como alternativa, revisar os 27 chamadores de `sub_822CC740`.
2. Não construir V49 nem testar compra até demonstrar loader aceitando `engine/bmwm3gtr_upgrade_engine_pre499`, função real de aplicação do pacote, preço/rollback e física, primeiro em ambiente isolado com **save descartável**. O preço 98.000 do nível global 4, baseado na fórmula do código PC e catálogo PAL, permanece condicional à lógica guest.
3. Manter sem alterações APK V48, save `MARCEK`, iPega PG-9076/touch, Nitro PRE398, 1920×1080, até 120 FPS, shaders/efeitos/física/thermal e a chave permanente. Não criar/recriar chave nem acessar credenciais.

**Status:** PRE537 `AUDIT_OK` somente leitura, 12 nós caracterizados estruturalmente, **SetPackage guest não identificado**, tuning BMW não funcional, APK nova não feita, instalação/persistência não testadas, nenhum ganho físico ou FPS medido.
