# PRE592 — ensaio A/B do vínculo RefSpec BMW com contador de upgrades zero

**Estado:** PRE590 confirmou por relato do usuário e leitura do `nfsmw.log` que a PRE587, que acrescenta uma nova coleção VLT **não vinculada ao pvehicle**, permite carregar `MARCEK` e chegar à interface BMW (`type=41`). PRE591 [run 42567684579](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42567684579) criou uma variante isolando **apenas o ponteiro RefSpec**. O contador de upgrades do motor BMW continua **0** e a tunagem continua NÃO comprável. Nenhum novo APK foi compilado.

## Dados PRE591 preparados no Google Drive

Pasta: https://drive.google.com/drive/folders/1uCdI3KIIV6OPnlIXMaDLSW4nzwnhrAZ4

- `PRE591_ZDIR_BMW_REFSPEC_POINTER_ONLY.bin` — **33.312 bytes**; SHA256 `f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da`.
- `PRE591_ZZDATA4_FIRST341_REFSPEC_POINTER_ONLY.bin` — **698.368 bytes**; SHA256 `6ad6e5748115380ab057e65642b2bad0ce83f74282b4d80dbbc5b71f33c8c12d`.
- O VPAK original do PT-BR de 697.856 bytes é substituído por candidato estrutural de **698.004 bytes**, SHA256 `b84d1ec037b656063ded48f8ea1e075d6c8425ba438e6366d301fc308c7c9358`, checksum EA `98e13bed`.
- A única diferença de bytes contra a PRE586 (nova coleção não vinculada que carregou o save) fica nos offsets 642333, 642334, 642335 do VPAK, direcionando o RefSpec ativo do motor à lista `stock + novo`. O contador da BMW permanece 0. Não provar ainda leitura e validação no jogo.
- Hash do `NFS/ZZDATA4.BIN` **completo**, de 401.068.032 bytes, após sobrepor apenas a região inicial na cópia original: `522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29`.
- Os fragmentos de 698.368 bytes **NÃO podem** substituir o arquivo `ZZDATA4.BIN` inteiro.

## Procedimento no Samsung Galaxy S24 FE / Shevery

1. **Antes de aplicar PRE592:** fechar completamente o jogo e **restaurar PRE587**, que ainda é o estado ativo segundo a informação do usuário. Executar:
```sh
sh /sdcard/Download/pre587_restore_bmw_unlinked_vlt_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```
Exigir `PRE587_RESTORE=ORIGINAIS_VERIFICADOS`. Não tocar em arquivos do save durante o rollback. O script de aplicação PRE592 rejeita qualquer `ZDIR` ou `ZZDATA4` que não tenha os hashes originais PT-BR.
2. Baixar os dois fragmentos da pasta Drive acima em **`/sdcard/Download/PRE591`**, preservando nomes. Baixar os scripts GitHub:
  - `automation/device/pre592_apply_bmw_refspec_pointer_only_shevery.sh`
  - `automation/device/pre592_restore_bmw_refspec_pointer_only_shevery.sh`
e armazená-los, por exemplo, em `/sdcard/Download/`.
3. Com a V48 fechada, conferir espaço livre para cópia completa temporária de 401 MB e backups, e executar:
```sh
sh /sdcard/Download/pre592_apply_bmw_refspec_pointer_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR" "/sdcard/Download/PRE591"
```
A saída esperada é `PRE592_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`. O script faz as verificações hash e cria `*.pre592_original_backup` antes de trocar os arquivos. Se falhar ou interromper, NÃO reaplicar, verificar o estado dos backups e preservar a saída. **O script ainda não foi executado/validado no telefone**, apenas no CI.
4. Teste com o mesmo **APK V48** e o perfil **MARCEK**: verificar chegada ao menu, carregamento da carreira, entrada na oficina com BMW M3 GTR, e registrar/compartilhar `nfsmw.log` com horários. Não testar compra, porque o contador de upgrade continua zero.
5. Com a V48 fechada, restaurar a origem se a variante falhar ou se for avançar ao próximo ensaio:
```sh
sh /sdcard/Download/pre592_restore_bmw_refspec_pointer_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR"
```
Confirmar `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`.

## Interpretação

- Se MARCEK carregar: temos evidência de que a ligação RefSpec **sozinha com contador 0** não impediu a carreira. O erro PRE573 passará a apontar mais para a contagem do upgrade ou sua interação com o outro vínculo. Não afirmar automaticamente culpa do contador.
- Se a carreira falhar: o ponteiro RefSpec com destino à lista de duas opções é um possível causador; investigar integridade/semântica e loader antes de repetir.
- Se ocorrer novo erro `C3` gráfico, registrar separadamente; o log PRE587 apresentou um erro de comparação de textura, sem causalidade confirmada com BMW.

## Regras

Sem instalar/compilar V49, sem alterar pacote ou assinatura permanente, sem excluir perfis, sem reduzir resolução 1920×1080, sem modificar Nitro PRE398, PG-9076/touch, gráficos/física geral ou neutralizar térmicas. A cap observada em log continua 60 FPS, meta solicitada é 120 FPS, sem ajuste nesta etapa.

**Estado no encerramento de PRE591:** fragmentos remotos `AUDIT_OK`; este guia e scripts são protocolo preparado, **não teste concluído no dispositivo**.
