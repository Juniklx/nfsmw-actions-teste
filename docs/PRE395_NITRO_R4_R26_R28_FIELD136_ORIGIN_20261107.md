# PRE395 — origem de r26/r28 e uso de r31+136 na rotina Nitro (2026-11-07)

## Evidência

- GitHub Actions [42438573836](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42438573836): `completed/success`. Artifact `13600129527`, relatório `PRE395_NITRO_REFERENCE_ORIGINS.json`, status `AUDIT_OK`.
- Snapshot PRE99 e `nfsmw_recomp.66.cpp` autenticados com SHA256 da fonte `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`.
- Função `sub_82424AF0` com 545 linhas; toda a pesquisa foi **somente leitura**, com janelas de código limitadas.

## Achados estruturais

| Elemento | Origem ou uso observado | Implicação |
|---|---|---|
| `r26` | linha relativa 37: `r26.u64 = ctx.r4.u64` | Parâmetro adicional de entrada da rotina, **tipo/owner ainda desconhecido** |
| `r26+20` | leituras float relativas 279 e 391 | Valor usado na fórmula do Nitro; não demonstra pointer player-car |
| `r28` | linha 92: `r28.s64 = ctx.r11.s64 + 12188`, com `ctx.r11.s64 = -2113536000` na linha 90 | Base obtida de constante numérica (aparentemente dados globais), **não player por si só** |
| `r28` offsets | `-4788`, `-4`, `0`, `+156` | Valores float de cálculo/comparação |
| `r31+136` | linhas 148 e 174: leituras `REX_LOAD_U32(r31.u32 + 136)`, comparadas com `2` | Campo numérico usado no fluxo condicional; sem classificação semântica |

- PRE393 run `42438407333` identificou três leituras de `r31+296` (r30/r11/r8) que acessam offsets relativos a outra estrutura e alimentam cálculos float. A inferência mais provável é uma tabela de parâmetros Nitro, **não uma identificação provada do veículo**.
- Em conjunto com PRE392 (V45), o `LR=0x824252DC` igual nos 20 checkpoints de dois slots mostra que **o LR isolado não discrimina os objetos**.
- **`ctx.r4` é uma nova referência estrutural a investigar**, mas não há prova de que seja um veículo, um controlador humano ou um owner; foi apenas observado que `r26` o copia. O registro `r31+136` também não comprova classe do carro.

## Próximo gate técnico

Examinar os destinos das chamadas de `sub_82424AF0` e seus argumentos de entrada para caracterizar `ctx.r4` sem assumir que se trata do jogador; ou desenvolver instrumento passivo que compare `r3/r4` e a rotina de input entre jogador e IA. Só depois de vínculo independente, testar filtro fail-closed com controles negativos IA. Não reescrever stores Nitro agora.

## Preservação

V45 PRE390 instalada/executada e callback PRE383 confirmado no teste PRE392, mas cheat ainda OFF. V44 e anteriores preservadas; save `MARCEK`, controle PG-9076/touch, 1920×1080, shaders, física, proteções térmicas e chave permanente intocados. Próxima APK deve ter `versionCode` maior que 45 e certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
