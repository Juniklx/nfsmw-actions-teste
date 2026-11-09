# PRE582_HANDOFF_PRE579_PRE581_BMW_TORQUE_ONLY_20261109

**Data:** 2026-11-09 (America/Bahia). **Projeto:** NFSMW-Recompiled-Mobile, APK release V48 PRE452, BMW M3 GTR carreira `type=41`. Este é um checkpoint de diagnóstico, não uma liberação de tunagem.

## PRE579 — teste A/B com save MARCEK após restauração

- O usuário disse **"Consegui carregar o save normalmente"** após a orientação de restaurar os dois arquivos `NFS/ZDIR.BIN` e `NFS/ZZDATA4.BIN` originais depois do experimento PRE573. Como a saída do rollback com hashes **não foi fornecida**, tratar o resultado como relato de controle pós-restauração, não inspeção remota das duas cópias originais.
- O `nfsmw.log` novo foi analisado localmente: 112.350 bytes, 665 linhas, SHA256 **`83522f3f328bc9385c8fb9ebf20b6f0b668f4a7519db08a4d38d4881ffa37cde`**. Horário inicial `01:42:45.174`, montagem `/storage/emulated/0/NFSMW_PTBR` às `01:42:45.934`, quatro aberturas do contêiner do perfil `MARCEK` de **62.688 bytes** com `XamContentCreate ... 00000000` às `01:42:52.872`, `01:42:53.438`, `01:42:53.470` e `01:42:56.600`. Leitura de recurso relacionado ao ambiente da carreira; o log não imprime prova de carga de carreira, mas o usuário confirmou sucesso no jogo.
- Sessão PRE573 com dados experimentais combinados: captura mostra `MARCEK está corrompido.`; o contêiner de save também tinha abertura bem-sucedida. Não significa corrupção permanente do arquivo. O controle com dados originais aumenta fortemente a hipótese de incompatibilidade introduzida pelo pacote combinado `GLOBAL/ATTRIBUTES.BIN`/ZDIR; **causa/estrutura ainda não identificada**. Relatório de base: `docs/PRE579_DEVICE_AB_MARCEK_RESTORED_LOG_20261109.md`.

## PRE580 — controle de recurso original com alteração mínima de motor BMW

- GitHub Actions [42563826158](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42563826158), relatório `docs/PRE580_PTBR_BMW_MOTOR_ONLY_PRIVATE_CONTROL_METADATA.json`, `AUDIT_OK`.
- Variante de diagnóstico construída contra a origem PAL/USA de `GLOBAL/ATTRIBUTES.BIN`, cuja identidade com recurso original PT-BR foi comprovada em PRE563. **Original e candidato continuam com 697.856 bytes**, mesmo `VLT`, mesmas coleções, mesmos 2399 exports, mesmos `RefSpec/PtrN` e mesmo contador original do motor no `pvehicle`. Somente as 9 amostras de torque do motor stock BMW foram multiplicadas por **1,05 artificial, exclusivamente para diagnóstico**. Apenas **24 bytes individuais** efetivamente diferem, na faixa absoluta do recurso **139313–139347**; não muda o resto da física nem qualquer categoria no catálogo.
- Os dois fragmentos foram enviados com readback ao Drive privado, pasta https://drive.google.com/drive/folders/150gpKDX4iJvIh4KsJe0UOz9tPJxgBLN- :
  - `PRE580_ZDIR_TORQUE_ONLY.bin`, 33.312 B, SHA256 `d1dcf673ac06b56967d0596e06f55d106e4a14f0eddf3b71da7007147eaa5f9d` (muda apenas o checksum EA do registro 805 para `3ca3a5a9`, tamanho original);
  - `PRE580_ZZDATA4_FIRST341_TORQUE_ONLY.bin`, 698.368 B, SHA256 `fc768236881516fd33871eddf7defc25d616ba32a5360dd4d9f5d342670293b1`.
- Hash do `NFS/ZZDATA4.BIN` **COMPLETO** esperado se o fragmento for aplicado corretamente a uma cópia do arquivo PT-BR original: **`95dff1f0e8f72ac54b3039d7627f406bf90b67fe66bee937776846464ea054aa`**. O ZIP PT-BR fonte foi completamente verificado via streaming. Não trocar o arquivo real de 401.068.032 bytes pelo fragmento de 698.368 bytes.
- Nenhum arquivo de jogo, save ou APK do telefone foi alterado pela PRE580; carregamento guest/efeito físico/tunagem comprável continuam não demonstrados.

## PRE581 — aplicação e rollback manuais, aguardando usuário

- [Run 42564037065](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42564037065), `AUDIT_OK`, `docs/PRE581_SHEVERY_TORQUE_ONLY_STATIC_PREFLIGHT_RESULT.json`: sintaxe dos dois scripts válida; entradas falsas abortam sem sobrescrever; rollback com backups ausentes aborta. **Não executados no telefone**.
- Scripts específicos, **não substituir pelos PRE573**:
  - `automation/device/pre581_apply_bmw_torque_only_shevery.sh`
  - `automation/device/pre581_restore_bmw_torque_only_shevery.sh`
  - Guia: `docs/PRE581_MANUAL_BMW_TORQUE_ONLY_CONTROL_20261109.md`.
- Os scripts exigem os dois fragmentos PRE580 e o GAME_ROOT `/storage/emulated/0/NFSMW_PTBR` observado no log, jogo fechado e hashes originais verificados. Montam uma cópia completa local de ZZDATA4, alteram a região na cópia, verificam o SHA completo, só então criam backups `.pre581_original_backup` e ativam o teste. O usuário **não executou PRE581**, e não deve reaplicar a PRE573 combinada.
- Após `PRE581_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`, se o usuário optar por testar, abrir a mesma V48 e `MARCEK` e observar se o save carrega. Isso diferencia genericamente alteração mínima de layout VLT reconstruído, **sem provar causalidade completa ou liberar nenhuma tunagem**. Guardar log e executar o rollback PRE581 depois de fechar o jogo.
- O usuário previamente aceitou descartar save/criar outro se necessário; essa decisão dispensa gate de isolamento, mas **não instrui a apagar saves**.

**Status:** controle PRE579 do save carregável confirmado pelo usuário; PRE580/581 `AUDIT_OK` apenas em servidor/CI e Drive privado; nenhuma V49 compilada, assinatura permanente não acessada, Nitro PRE398/PG9076/gráficos/resolução/física geral/proteções térmicas intactos. O cap observado na sessão foi 60 FPS, a meta do projeto permanece 120 sem alteração neste gate.
