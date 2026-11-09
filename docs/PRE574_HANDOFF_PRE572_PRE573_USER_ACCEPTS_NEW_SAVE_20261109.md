# PRE574_HANDOFF_PRE572_PRE573_USER_ACCEPTS_NEW_SAVE_20261109

**Data local:** 2026-11-09, America/Bahia. **Projeto:** NFSMW-Recompiled-Mobile, BMW M3 GTR da carreira type 41, versão Android assinada V48 PRE452. Objetivo: liberar tunagem real, com peças compráveis/instaláveis, efeito físico e persistência. **Ainda não liberada.**

## Nova orientação explícita do usuário sobre o save

Em 2026-11-09, o usuário declarou: **"Não precisa proteger o save, eu vou criar outro depois"**. Essa decisão é posterior à PRE571 e **substitui a exigência de isolar/proteger o save `MARCEK` como bloqueio para experimentar a BMW na V48**. Não insistir em Pasta Segura/Knox, perfil isolado ou auditoria de save como condição obrigatória. Um novo perfil poderá ser criado pelo usuário depois. **Isso não autoriza que scripts apaguem saves, limpem dados do app, reinstalem APK ou modifiquem credenciais automaticamente.** A possibilidade de perder progresso ao testar é aceita pelo usuário; os ativos originais da tradução, código, APK e assinatura continuam protegidos por integridade e backups.

## PRE572 — fragmentos experimentais privados preparados

- [Run 42560268270](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42560268270) `AUDIT_OK`. Script `automation/kaggle/pre572_prepare_ptbr_bmw_private_patch_fragments.py`, evidência `docs/PRE572_PTBR_BMW_PRIVATE_PATCH_BUNDLE_METADATA.json`.
- O ZIP PT-BR original do Drive id `1M95wS9iqrMI-p328Wual7TreqfaPgdL0` foi verificado por leitura autenticada; o arquivo `NFS/ZZDATA4.BIN` foi conferido por streaming DEFLATE e hash completo de origem `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`. Sem escrita no ZIP ou na pasta do telefone.
- ZDIR tradução em `GLOBAL/ATTRIBUTES.BIN`: índice 805, arquivo 4, setor 0, recurso original 697.856 bytes; candidato BMW sintético PRE502/564/566 (+5% torque **somente vetor de experimento**, contador motor 0→1) contém 698.004 bytes; checksum EA experimental `4d05584a`; usa 341 setores (698.368 bytes) deixando 364 bytes zero. Nova coleção `engine/bmwm3gtr_upgrade_engine_pre499` **ainda não aceita em runtime guest**.
- Pasta privada criada em `NFSMW_Android/03_Scripts_e_Patches/PRE572_BMW_PTBR_TESTE_EXPERIMENTAL_20261109`: https://drive.google.com/drive/folders/1Knbcge-AtyM7OoFxEMafQGXIrfs-lnGe
- Fragmento de índice **apenas para teste**, 33.312 bytes, id `1T1rwU8LrCWfcDK3WAls-KCmlGHVvmokw`, nome `PRE572_ZDIR_PTBR_BMW_TESTE_FRAGMENT.bin`, SHA-256 `d625d5f7195c7b1596c03d2632f87de3a34cec69da902b6604e82949677e4832`.
- Fragmento de substituição dos primeiros 341 setores **não é arquivo ZZDATA4 completo**, 698.368 bytes, id `13Y6URyUhNpb4wZDN9os0WuMRa7a_WmcU`, nome `PRE572_ZZDATA4_PRIMEIROS_341_SETORES_BMW_TESTE.bin`, SHA-256 `29a62931ee0cb68e96100014260d41d0f627d8348bdcc6406e529ad0482bb7eb`.
- O **hash completo esperado** para `NFS/ZZDATA4.BIN` de 401.068.032 bytes após substituir apenas a região inicial é `4eca61a0969bd1311e7b664f073ecaab50c950b43b10bb4438858ff3c57b665e`. CRC32 esperado `3b994656`. Demais bytes do arquivo são preservados no cálculo. O ZIP PT-BR não contém membro autônomo `GLOBAL/ATTRIBUTES.BIN` (0 entradas diretas com esse nome).
- Os dois fragmentos tiveram conferência após upload no Drive. **Nenhum arquivo completo modificado para uso no jogo foi enviado**, e nenhum ativo do dispositivo foi alterado.

## PRE573 — protocolo Shevery manual e auditoria offline

- Scripts GitHub:
  - `automation/device/pre573_apply_bmw_ptbr_shevery.sh`
  - `automation/device/pre573_restore_bmw_ptbr_shevery.sh`
  - Guia `docs/PRE573_MANUAL_SHEVERY_BMW_TEST_PROTOCOL_20261109.md`
- [Run 42560674054](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42560674054), `AUDIT_OK`, relatório `docs/PRE573_SHEVERY_SCRIPTS_STATIC_PREFLIGHT_RESULT.json`: sintaxe `sh -n`, hashes esperados e recusa de arquivos falsos antes de escrever, provados em runner Linux. **Não foi testado nem executado no Samsung/Shevery**.
- O script só aceita uma pasta de jogo `GAME_ROOT` fornecida explicitamente pelo usuário e uma pasta contendo os dois fragmentos. Exige V48 fechada; hashes completos originais e fragmentos exatos; cria cópia temporária completa do ZZDATA4, substitui 341 setores na **cópia**, valida SHA-256 do arquivo completo, e só então renomeia originais para `.pre573_original_backup` e ativa arquivos de teste. Há script de restauração. Interrupções, espaço insuficiente, restrições de permissão e falhas entre renomes ainda são riscos reais; não instruir uso do fragmento parcial como `ZZDATA4.BIN` inteiro.
- Os scripts **não alteram saves automaticamente**. Ao testar a V48 com dados experimentais o próprio jogo poderá alterar o progresso, e o usuário disse aceitar criar outro depois.

## Próximo passo obrigatório

1. Usuário copiar os dois fragmentos do Drive ao telefone e identificar o diretório exato `GAME_ROOT/NFS` da **pasta PT-BR extraída**; não inventar caminho no Android nem assumir que o executor GitHub alcança o S24 FE. Preflight no Shevery: existência, permissão e espaço livre, e que a V48 esteja fechada.
2. Executar **deliberadamente** `pre573_apply_bmw_ptbr_shevery.sh` somente com caminho confirmado e após considerar o risco do teste. Manter backup dos ativos originais. Não pedir backup do save `MARCEK` como gate.
3. Abrir V48 e coletar log/resultado do carregador real `ZDIR/ZZDATA4/VPAK`, aceitação da coleção BMW e menu de desempenho, sem assumir que abrir sem crash significa aceitação da coleção. Se falhar, usar script de restore e analisar logs.
4. Só após prova guest, implementar catálogo FE/preço/checkout e física e validar persistência numa nova carreira, se o usuário desejar. Não fabricar V49 ou modificar assinatura por antecipação.

**Proteções persistentes:** APK V48/V46/V47, package `io.github.nfsmwrecomp`, certificado release SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG-9076/touch, 1920×1080, 120 FPS, gráficos, shaders, física geral e proteções térmicas.

**Status final:** PRE572 fragmentos privados e hash completo previsto `AUDIT_OK`; PRE573 sintaxe/recusa sintética `AUDIT_OK`; aplicação no aparelho, guest loader, tunagem disponível, compra e save ainda **não verificados**. A decisão do usuário elimina o gate de preservar save, não a exigência de proteger/validar os arquivos-fonte da tradução.
