# PRE587 — protocolo manual de isolamento de VLT na BMW (após PRE581 bem-sucedida)

**Novo checkpoint remoto:** [PRE586 run 42565596510](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42565596510), `AUDIT_OK`. Este experimento **ainda não foi executado no Samsung Galaxy S24 FE**. A PRE586 conserva uma nova coleção VLT sintética `engine/bmwm3gtr_upgrade_engine_pre499`, mas restaura o contador original do motor da BMW (0) e a referência ativa `RefSpec` no `pvehicle`. Assim testa a compatibilidade do loader/registro de nova coleção sem efetivar tuning da BMW.

**Comparações:** PRE573 combinado falhou ao carregar `MARCEK`; PRE581 com nove torques stock BMW ×1,05, estrutura original preservada, **carregou `MARCEK`**, confirmado pelo usuário e por novo log com leitura do recurso de `ZZDATA4.BIN` no offset 0. A próxima variável isolada é VLT/coleção nova **não referenciada no veículo ativo**, não ganho de potência.

## Fragmentos PRE586 — apenas private Drive

Pasta: https://drive.google.com/drive/folders/17KJCMPZ-LwCZZv7SBD1WPU0SIPZpporD

- `PRE586_ZDIR_VLT_NEW_COLLECTION_UNLINKED.bin`: 33.312 bytes, SHA256 `3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025`.
- `PRE586_ZZDATA4_FIRST341_UNLINKED_VLT.bin`: 698.368 bytes, SHA256 `11f233a7a22df3822573a3a52af50f7c9b27f4b5c5cba77fdaad3c4e03041271`.
- O recurso VPAK experimental tem 698.004 bytes, checksum EA `820a01ba`. O `ZZDATA4.BIN` COMPLETO, após aplicar esses 341 setores a uma cópia do original, deve ter SHA256 **`524c22622039086c9207f25b3a82823fb62d8879e70d0142730bca2b5cdda996`**. Nunca substituir o arquivo completo pelo fragmento parcial. Outro fator em investigação: o nome da coleção nova não consta na tabela de strings original `StrE`, e a compatibilidade runtime disso não foi provada.

## Passo a passo SE o usuário optar por ensaio

1. **Primeiro, com a V48 fechada, RESTAURAR o teste PRE581 antes de tentar outro**. O jogo está atualmente com dados PRE581 (segundo o usuário); o script PRE587 aceita apenas hashes originais PT-BR e deverá rejeitar a aplicação se a PRE581 continuar ativa:
```sh
sh /sdcard/Download/pre581_restore_bmw_torque_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```
Confirmar `PRE581_RESTORE=ORIGINAIS_VERIFICADOS`. Não limpar dados do aplicativo, apagar `MARCEK` ou modificar chave/assinatura.
2. Baixar os dois fragmentos PRE586 do Drive para uma pasta separada, por exemplo `/sdcard/Download/PRE586/`, com **nomes intactos**. Baixar os scripts GitHub `automation/device/pre587_apply_bmw_unlinked_vlt_shevery.sh` e `automation/device/pre587_restore_bmw_unlinked_vlt_shevery.sh` (por exemplo em `/sdcard/Download/`).
3. Fechar a V48, garantir espaço livre para a cópia temporária de 401.068.032 bytes, backups e permissões Shevery. Executar:
```sh
sh /sdcard/Download/pre587_apply_bmw_unlinked_vlt_shevery.sh "/storage/emulated/0/NFSMW_PTBR" "/sdcard/Download/PRE586"
```
O script verifica hashes de origem, fragmentos e o arquivo completo já modificado numa cópia temporária; preserva `*.pre587_original_backup`. Esperar `PRE587_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`. NÃO executar se faltar arquivo ou já houver backup PRE587 antigo.
4. Abrir a APK V48 original (inalterada), verificar se a carreira `MARCEK` carrega. Não esperar opção de tunagem nova: `pvehicle` original permaneceu com 0 níveis motor extra. Guardar o `nfsmw.log` do teste e relatar sucesso ou mensagem exibida.
5. **Encerrar o jogo e restaurar** se não for manter temporariamente a variante experimental:
```sh
sh /sdcard/Download/pre587_restore_bmw_unlinked_vlt_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```
A saída esperada é `PRE587_RESTORE=ORIGINAIS_VERIFICADOS`. Se houver erro, não executar novo script, preserve saída e backups.

## Interpretação do experimento

- Carregar `MARCEK` com PRE587: o pacote estrutural com nova coleção VLT **não vinculada ao `pvehicle`** foi compatível com o carregamento até esse ponto. Maior suspeita recai sobre contador motor, ligação RefSpec / relação combo, não prova definitiva de qual.
- Erro `MARCEK está corrompido` com PRE587: a simples presença/repack da coleção nova ou a atualização de VLT/ExpN/PtrN/StrE/tamanho já pode causar rejeição. Necessita análise mais fina; não prova que o save seja irrecuperável.
- Nenhuma destas variantes habilita compra na oficina; o objetivo final de tunagem BMW continua separado da mera compatibilidade da coleção no loader.

**Integridade:** preserva APK V48, package `io.github.nfsmwrecomp`, certificado permanente, Nitro PRE398, PG-9076/touch, gráficos e proteção térmica. A decisão do usuário de poder criar novo save elimina o requisito de sandbox de saves, não autoriza limpar dados automaticamente. O cap observado nos logs foi 60 FPS, a meta segue 120.
