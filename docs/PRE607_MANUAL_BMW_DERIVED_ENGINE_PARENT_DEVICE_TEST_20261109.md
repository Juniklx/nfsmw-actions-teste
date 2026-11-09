# PRE607 — teste de herança do segundo motor BMW (PRE606 → Galaxy S24 FE)

**Estado na preparação:** PRE604 [42590630384](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42590630384) e PRE605 [42590907933](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42590907933) deram `AUDIT_OK` em auditoria estática e em memória. PRE606 [42591196366](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42591196366) deu `AUDIT_OK` na geração com hash/CRC/ZIP completo e armazenamento privado. A compatibilidade com a V48 **não foi testada**.

## Hipótese e variáveis

A PRE573 usou uma nova coleção `engine/bmwm3gtr_upgrade_engine_pre499`, com pai `default` e limite de motor BMW 1; ocorreu aviso de save corrompido. Os testes PRE587 (coleção não vinculada e contador 0) e PRE592 (coleção vinculada e contador 0) permitiram carregar MARCEK. PRE604 demonstrou que o Punto original tem segundo motor pai `punto`, enquanto o clone BMW PRE502 herdava diretamente `default`. Isso NÃO prova que herança é a causa da PRE573.

A PRE606 mantém o VPAK combinado PRE502 (novo ExpN, PtrN, coleção, RefSpec de 2 itens e limite engine=1) e modifica **só 4 bytes do parent da coleção nova**, de `eec2271a` (`default`) para `cd88083f` (`bmwm3gtr`). VPAK final 698.004 bytes, SHA256 `11c122bf9b32011fd3955498517e51f2f1f11551bc2bbd9f448201bc4ef862f3`, checksum EA `31aef5d7`. Não faz tunagem comprável nem mede ganho de torque.

## Arquivos privados PRE606

Pasta de fragmentos: https://drive.google.com/drive/folders/1AR2uE0Oel80gciW7xSjEJEIKjnG9wC4I

- `PRE606_ZDIR_BMW_CHILD_PARENT_CORRECTED.bin`, 33.312 bytes, SHA256 **`f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2`**.
- `PRE606_ZZDATA4_FIRST341_BMW_PARENT_CORRECTED.bin`, 698.368 bytes, SHA256 **`93327b44eb54b0ec9b14e51e7b35da9071e9531454c49819c35e6e6172c284a5`**.
- O SHA256 esperado de **`NFS/ZZDATA4.BIN` completo, 401.068.032 bytes**, após aplicação exata ao original: **`1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146`**.
- **Não substituir `ZZDATA4.BIN` inteiro pelo fragmento de 698.368 bytes!** O script sobrepõe apenas o primeiro bloco de 341 setores numa cópia completa.

## Procedimento manual, somente se o usuário optar por testar no dispositivo

**Antes:** a última confirmação do usuário foi PRE592 aplicada e carreira `MARCEK` carregada. **Ainda não foi informado rollback PRE592.** Fechar completamente a V48, então executar script PRE592 original em Shevery:

```sh
sh /sdcard/Download/pre592_restore_bmw_refspec_pointer_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```

**Condição obrigatória:** saída `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`. Se não aparecer, não executar PRE607; preservar erros e backups.

Depois baixar os dois fragmentos PRE606 do Drive para `/sdcard/Download/PRE606`, sem renomear. Baixar do GitHub os scripts:

- `automation/device/pre607_apply_bmw_child_parent_corrected_shevery.sh`
- `automation/device/pre607_restore_bmw_child_parent_corrected_shevery.sh`

Salvar scripts na pasta `/sdcard/Download/`. Com V48 fechada e espaço disponível para cópia temporária integral de 401 MB, executar:

```sh
sh /sdcard/Download/pre607_apply_bmw_child_parent_corrected_shevery.sh "/storage/emulated/0/NFSMW_PTBR" "/sdcard/Download/PRE606"
```

O script verifica tamanho/hash dos originais ZDIR e ZZDATA4, fragmentos PRE606 e SHA do ZZDATA4 completo reconstruído antes de mover os arquivos; preserva backups originais `*.pre607_original_backup`. Se falhar, não repetir às cegas. Saída esperada: `PRE607_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`.

**Teste:** abrir a mesma APK release V48 intacta e perfil `MARCEK`. Verificar se há aviso `MARCEK está corrompido` ou se a carreira carrega; se carregar, tentar entrar na oficina BMW M3 GTR e observar a lista de peças — sem presumir que itens novos apareçam ou possam ser comprados. Registrar o novo `nfsmw.log` e a saída PRE607. O teste pode modificar saves pelo funcionamento normal do jogo; scripts não editam saves.

**Rollback pós-teste** (ou antes de tentar outro candidato), sempre com jogo completamente fechado:

```sh
sh /sdcard/Download/pre607_restore_bmw_child_parent_corrected_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```

Esperar `PRE607_RESTORE=ORIGINAIS_VERIFICADOS`. Se houver falha ou interrupção durante a cópia/rename, preservar arquivos temporários e backups para auditoria; não limpar app nem excluir dados. Ninguém executou essa sequência no telefone até agora.

## Interpretação

- **Carrega com PRE607:** compatibilidade de uma nova coleção BMW herdando da coleção original, mesmo com contador de motor 1, até o ponto de carregamento da carreira. A herança passa a ser suspeita forte de diferença relevante em relação à PRE573, mas ainda não temos prova de que a oficina tenha peças compráveis.
- **Não carrega com PRE607:** a mudança de pai isolada não resolveu a incompatibilidade do contador 1. Continuar por outro eixo, como registro VLT/Export e runtime do segundo RefSpec, sem apagar MARCEK nem reaplicar PRE573.

**Preservar:** APK V48 PRE452 (sem V49), package `io.github.nfsmwrecomp`, assinatura permanente certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG9076/touch, 1920x1080, meta cap 120 FPS, efeitos/shaders/física geral e segurança térmica. Cap de 60 FPS visto em logs anteriores não é alterado nesta etapa.
