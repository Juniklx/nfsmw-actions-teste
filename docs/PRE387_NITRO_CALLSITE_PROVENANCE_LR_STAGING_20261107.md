# PRE387 — Nitro player-owner: PRE375 / PRE377 / PRE382 / PRE386 evidências (2026-11-07)

## Origem e cenário
- V44 PRE370 assinada, instalada e testada no Galaxy S24 FE. PRE372 observou XInput `0x2000` precedendo o início de consumo de Nitro em slot 1 na exploração livre e slot 2 na corrida. O usuário confirmou expressamente **exploração livre primeiro, corrida com IA depois** (adendo PRE374).
- Essa correlação é forte evidência temporal, mas o `owner` semântico do veículo ainda **não** foi demonstrado. Jamais fixar slot 1/2 ou endereço guest no cheat.

## PRE375 — fonte PAL autenticada
- Run [42433536119](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42433536119), artifact `13597823879`, `AUDIT_OK`.
- 129 shards PAL do PRE99 conferidos, SHA256 PRE99 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- `sub_82424AF0` está em `nfsmw_recomp.66.cpp` (fonte SHA256 `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`), corpo 545 linhas.
- `r31.u64 = ctx.r3.u64` na linha relativa 32, loads `r31+296` três vezes e loads/stores `r31+252` quatro/cinco vezes. Busca textual de `82424AF0` encontrou somente sua definição nos shards; **não significa ausência de despachantes indiretos**.
- Dez chamadas `REX_CALL_INDIRECT_FUNC(ctr.u32)` são chamadas **feitas pela rotina**, não identificam seu caller.

## PRE377 — LR na entrada, fonte autenticada
- Run [42433732833](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42433732833), artifact `13598845903`, `AUDIT_OK`.
- Logo após `REX_FUNC_PROLOGUE();` no corpo PAL, antes de a própria função modificar LR: `// mflr r12`, `ctx.r12.u64 = ctx.lr;` linha relativa 20. Portanto existe um ponto **anterior** à alteração de LR para amostrar o endereço de retorno de entrada.
- Não prova que LR diferencie jogador e adversários; não confundir LR de entrada com os novos valores escritos no próprio corpo em `ctx.lr = 0x82424AF8` etc.

## PRE379/PRE380/PRE382 — proposta reversível
- `automation/kaggle/pre379_nitro_lr_entry_staging.py` propõe inserção em memória de callback `NFSMW_PRE379_NITRO_ENTRY_TRACE(ctx.lr,ctx.r3)` imediatamente após a prologue, sem alterar LOAD/STORE guest.
- Primeira canary PRE380 run `42433903449` falhou `ValueError` devido à âncora textual rígida (não provar causa sem stderr). Corrigida a aceitação de indentação com expressão regular de linha exata, run **[42434040838](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42434040838)** passou `AUDIT_OK`, artifact `13598443111`: fonte SHA256 conferido, reversão exata, fonte proposta SHA256 `8d9a07cba126315c72e5c11b06b60d1ba9f4a6dc4e50c5fccdb34e57ca2a12df`, zero alterações de guest accesses. Fonte original **não foi escrita em disco** nesse teste.

## PRE383/PRE384/PRE386 — callback host e compilação sintética
- `automation/kaggle/pre383_nitro_lr_slot_callback_staging.py`: proposta de callback limitado por slot (amostragem potência de dois, até ordinal 1024/slot), usando `g_pre336_nitro_address_diversity.lookup_slot(base+252)`, **sem desreferenciar memória guest**. Quando o slot ainda é desconhecido, não associa owner. Proposta **não está integrada em APK**.
- Primeira PRE384 run `42434222187` falhou compilação sintética. Novo diagnóstico em run `42434324463` identificou `\\n` literal dentro de comentário C++ ocultando `REXLOG_INFO`. Corrigida somente formatação textual do callback no commit `4fe36688236d025da2c52f8b3fa212a6dd8f41ba`.
- Retry **[42434391604](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42434391604)** `completed/success`, artifact `13599070670`, `AUDIT_OK`: composição do callback PRE317+PRE337+PRE349+PRE383, reversão exata, `g++ -std=c++17 -Wall -Wextra -Werror -fsyntax-only` em ambiente host com mock do logger, zero novos guest LOAD/STORE.
- **Limites:** só sintaxe C++ host, não compilação ARM64 ou execução no telefone; **não foram observados LR reais por carro**. `owner_verified=false`, `apk_built=false`, `cheat_enabled=false`.

## Próximo gate antes de V45
- Revisar a ordem de aplicação da cadeia de patches no builder atual V44, hashes originais e inclusão do callback. Primeiro compor em workspace temporário e testar ARM64 sem assinatura; exigir ausência de alterações guest e de duplicação dos patches, e preservação do controle PG-9076/touch.
- Se for criada V45, usar `versionCode=45`, mesmo pacote `io.github.nfsmwrecomp` e certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não recriar a chave, não modificar save `MARCEK` e manter V44 como fallback.
- A V45 seria **apenas diagnóstica**, para comparar `guest_lr` e slot entre carro sozinho e corrida. O LR pode ser idêntico para jogador/IA; isso não atesta player owner e não autoriza cheat global.
