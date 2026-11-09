# PRE581 — controle A/B mínimo: BMW M3 GTR com apenas torque original alterado

**Resultado PRE580:** [GitHub Actions 42563826158](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42563826158), `AUDIT_OK`. Não alterou o S24 FE. Criou no Drive dois fragmentos privados:
- Pasta: https://drive.google.com/drive/folders/150gpKDX4iJvIh4KsJe0UOz9tPJxgBLN-
- `PRE580_ZDIR_TORQUE_ONLY.bin`: 33.312 bytes, SHA256 `d1dcf673ac06b56967d0596e06f55d106e4a14f0eddf3b71da7007147eaa5f9d`.
- `PRE580_ZZDATA4_FIRST341_TORQUE_ONLY.bin`: 698.368 bytes, SHA256 `fc768236881516fd33871eddf7defc25d616ba32a5360dd4d9f5d342670293b1`.

**Finalidade:** diferenciar o problema da PRE573, cuja variante COMBINADA adicionou coleção/ExpN/RefSpec/PtrN e mudou o limite de motor, da capacidade de carregar o recurso original com apenas 9 floats (+5% sintéticos no motor stock). Aqui NÃO foram criados itens de tunagem compráveis; NÃO é atualização final nem ganho de FPS. O VPAK mantém 697.856 bytes e o VLT original íntegro; 24 bytes individuais de 36 possíveis mudam, unicamente na curva de torque BMW original. O `pvehicle` e os limites de upgrade ficam idênticos aos originais.

## Execução manual somente após conferência de estado

- A sessão controle do usuário confirmou que `MARCEK` voltou a carregar normalmente após a orientação de rollback PRE573. O novo `nfsmw.log` do usuário (SHA256 `83522f3f328bc9385c8fb9ebf20b6f0b668f4a7519db08a4d38d4881ffa37cde`) registra montagem real de `/storage/emulated/0/NFSMW_PTBR`. Ainda não existe leitura externa hash-direta dos arquivos restaurados no telefone.
- Antes do teste, deixar o jogo **fechado**, baixar ambos os fragmentos PRE580 para a mesma pasta Android, por exemplo `/sdcard/Download/PRE580`, preservando seus nomes.
- Baixar do GitHub os scripts `automation/device/pre581_apply_bmw_torque_only_shevery.sh` e `automation/device/pre581_restore_bmw_torque_only_shevery.sh`. Supondo que o usuário os tenha salvo em `/sdcard/Download/`:
```sh
sh /sdcard/Download/pre581_apply_bmw_torque_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR" "/sdcard/Download/PRE580"
```
- O script verifica **hashes integrais originais dos arquivos do jogo** e dos dois fragmentos antes de criar a cópia temporal. Exige `NFS/ZZDATA4.BIN` de 401.068.032 bytes, e que nenhum backup PRE581 exista; preserva os originais `.pre581_original_backup`. Patch altera apenas os primeiros 698.368 bytes da CÓPIA integral de ZZDATA4 e verifica que o SHA256 COMPLETO ficou exatamente `95dff1f0e8f72ac54b3039d7627f406bf90b67fe66bee937776846464ea054aa`. Em caso de erro, **não prosseguir automaticamente nem apagar arquivos**; conferir a mensagem e os backups.
- Se a saída for `PRE581_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`, abrir V48 com o mesmo save `MARCEK` e responder ao resultado da carga: abriu normalmente / erro de corrupção / outro erro. Depois, se quiser, testar um percurso curto para verificar funcionamento do jogo, **sem declarar que liberou tunagem**. Guardar `nfsmw.log`.
- Após o teste, com a V48 completamente fechada:
```sh
sh /sdcard/Download/pre581_restore_bmw_torque_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```
Espera-se `PRE581_RESTORE=ORIGINAIS_VERIFICADOS`. Esse script não mexe no `MARCEK`, mas alterações do jogo em save durante uma sessão experimental são possíveis. Há risco de falta de espaço/permissão/interrupção, e em alguns cenários pode ser necessária restauração manual dos arquivos a partir dos backups gerados.

## Interpretação correta

- **PRE581 carrega o mesmo save:** o engine aceita ao menos a variante de alteração mínima, o que aumenta suspeita sobre estrutura, índices e relações da reconstrução combinada PRE502/572. Ainda não identifica qual elemento causou erro.
- **PRE581 também diz corrompido:** o resultado não isola causa; investigar checksum do recurso e comportamento do carregador, além de possível integridade dos dados do save.
- **Não reaplicar PRE573 nem usar o script PRE573 para os fragmentos PRE580.** Eles têm hashes e semântica diferentes.
- Jamais substituir o ZZDATA4 integral pelo fragmento de 698.368 bytes.

**Restrições:** V48, assinatura permanente, Nitro PRE398, iPega PG-9076/touch, 1920×1080, cap desejado 120 FPS, shaders/efeitos/física geral e térmicas preservados; nenhuma V49 gerada; não modificar dados ou saves do usuário remotamente.
