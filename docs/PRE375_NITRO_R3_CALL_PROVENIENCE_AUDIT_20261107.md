# PRE375 — Proveniência estática da base do Nitro PAL (2026-11-07)

## Execução e escopo

- GitHub Actions [42433536119](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42433536119), artefato `13597823879`, relatório `PRE375_NITRO_CONTEXT_PROVENANCE.json`, `status=AUDIT_OK`.
- Snapshot PRE99 autenticado SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Todos os **129** shards PAL `nfsmw_recomp.*.cpp` percorridos. Shard original `nfsmw_recomp.66.cpp` SHA-256 `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f` conferido.
- Rotina `sub_82424AF0`: **545 linhas**. Nos primeiros trechos há `r31.u64 = ctx.r3.u64` (linha relativa 32). Essa cópia estabelece a base dos acessos da rotina, **não é prova de qual veículo invocou a função**.

## Campos e fluxo verificados

- `+296`: três loads a partir de `r31` nas linhas relativas **136, 267 e 370**, usados como referências a outra estrutura (sem classificação de owner).
- `+252`: quatro loads nos trechos relativos **307, 373, 469 e 504** e cinco stores **379, 414, 510, 521, 528**. Corresponde à estrutura já qualificada na PRE334.
- Dez referências a `REX_CALL_INDIRECT_FUNC(ctr.u32)` aparecem dentro da função, de acordo com o relatório. Essas chamadas **saem da rotina; não revelam quem a invocou**.
- Busca textual global pelo símbolo/hexadecimal `82424AF0` nos 129 shards retornou exatamente **uma** linha, sua definição `DEFINE_REX_FUNC(sub_82424AF0)` em `nfsmw_recomp.66.cpp:16124`. Não foi localizada uma chamada textual direta, mas **despacho virtual/indireto, tabelas de função binárias e outros mecanismos continuam possíveis**.

## Relação com PRE372/PRE374

- O usuário confirmou exploração livre com somente seu carro e depois corrida com adversários na sessão V44. O bit XInput `0x2000` precedeu os primeiros consumos de Nitro em slots efêmeros diferentes (~17 ms e ~18 ms).
- Os resultados de PRE375 **não mudam** a classificação de owner: `owner_verified=false`. O mesmo `ctx.r3` muda de conteúdo entre invocações e não pode ser inferido do número do slot.
- Não usar `slot=1/2`, endereços guest fixos, nem mutação global de `sub_82424AF0` para cheats.

## Próximo gate sugerido

Investigar um identificador independente **do local/ramo da chamada em runtime** da função (por exemplo, endereço de retorno PowerPC `LR`, se demonstrado semanticamente válido no código gerado) e comparar sua diversidade entre veículos, com instrumentação limitada e passiva somente após verificação textual do contexto. Um `LR` igual para todos os carros não prova exclusividade de owner; um `LR` distinto pode ser pista de fluxo, não identificação por si só. Não gerar V45 nem alterar APK até comprovar acesso seguro às informações do chamador.

## Preservação

Somente auditoria dos fontes do snapshot em diretório temporário. Sem compilar APK, sem alterar guest loads/stores, save `MARCEK`, assinatura permanente, shaders, gráficos, físicas, controles ou proteção térmica.
