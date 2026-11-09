# PRE573 — aplicar fragmentos experimentais PRE572 ao NFS PT-BR no Shevery (manual)

**Estado:** scripts preparados para teste **somente mediante execução deliberada pelo usuário**; a PRE572 é `AUDIT_OK`, mas o loader guest/garagem/compra/física/save ainda não foram testados.

## O que muda com a autorização do usuário

Em 2026-11-09, o usuário informou: **"Não precisa proteger o save, eu vou criar outro depois"**. Portanto, **não exigir Pasta Segura nem isolamento de `MARCEK`** como pré-requisito para avançar. Isso **não é uma ordem para excluir saves automaticamente**, nem dispensa backup dos dados originais do jogo.

## Arquivos de dados já preparados

Pasta privada Drive: https://drive.google.com/drive/folders/1Knbcge-AtyM7OoFxEMafQGXIrfs-lnGe

- `PRE572_ZDIR_PTBR_BMW_TESTE_FRAGMENT.bin` — 33.312 bytes, SHA-256 `d625d5f7195c7b1596c03d2632f87de3a34cec69da902b6604e82949677e4832`
- `PRE572_ZZDATA4_PRIMEIROS_341_SETORES_BMW_TESTE.bin` — 698.368 bytes, SHA-256 `29a62931ee0cb68e96100014260d41d0f627d8348bdcc6406e529ad0482bb7eb`

Estes **não são o ZZDATA4 completo**; jamais substituir `ZZDATA4.BIN` diretamente pelo fragmento de 698.368 bytes. A PRE572 verificou que o arquivo de 401.068.032 bytes completo, após substituição só dos primeiros 341 setores, terá SHA-256 `4eca61a0969bd1311e7b664f073ecaab50c950b43b10bb4438858ff3c57b665e`. O arquivo original possui SHA-256 `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`.

## Aplicação: somente após localizar a pasta EXATA usada no jogo

Não se conhece por análise remota o caminho local completo da pasta extraída no Galaxy S24 FE. O usuário precisa confirmar o **GAME_ROOT** contendo o diretório `NFS/` e permitir ao Shevery ler e gravar nele. Não inferir caminho `/sdcard/...` automaticamente.

1. Copiar os dois fragmentos da pasta Drive para uma pasta acessível no telefone, por exemplo `/sdcard/Download/PRE572/`, sem renomeá-los.
2. Salvar os arquivos `automation/device/pre573_apply_bmw_ptbr_shevery.sh` e `automation/device/pre573_restore_bmw_ptbr_shevery.sh` no armazenamento do telefone.
3. Fechar totalmente a V48; não usar `am force-stop` automaticamente nem limpar dados Android.
4. No Shevery, executar a aplicação **apenas se quiser experimentar**:
```sh
sh /sdcard/Download/pre573_apply_bmw_ptbr_shevery.sh "/CAMINHO/EXATO/DA/PASTA_DO_JOGO" "/sdcard/Download/PRE572"
```
O script aborta se o jogo estiver aberto, se faltar arquivo, se os hashes do ZIP PT-BR da instalação ou dos fragmentos divergirem, ou se encontrar arquivos de backup de tentativa anterior. Ele cria uma cópia integral *temporária* do `ZZDATA4.BIN` de 401 MB, sobrepõe os 341 primeiros setores **na cópia**, verifica o hash completo e preserva os originais com sufixo `.pre573_original_backup` antes de ativar as versões experimentais. É necessário espaço livre para a cópia e permissões de gravação; falha de armazenamento ou interrupção pode exigir restauração manual usando os backups.
5. Só depois de receber `PRE573_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`, abrir a V48 e testar o carregamento. Inicialmente **não comprar peças nem gravar conclusões de desempenho**; investigar logs/erros e se o menu de BMW mudou. A ausência de crash não prova que a coleção foi aceita.
6. Para restaurar os dados originais após fechar V48:
```sh
sh /sdcard/Download/pre573_restore_bmw_ptbr_shevery.sh "/CAMINHO/EXATO/DA/PASTA_DO_JOGO"
```

## Restrições

- O save é considerado descartável **por escolha do usuário**, mas os scripts não apagam dados de jogador.
- Não gera APK V49, não altera a assinatura, Nitro PRE398, PG-9076, gráficos, efeitos, 1920×1080, 120 FPS nem proteção térmica.
- O teste em dispositivo **não foi realizado**; carregamento guest, catálogo, preço, compra, motor e persistência permanecem sem verificação.
- **Nunca** copiar o patch de primeiros 341 setores como `ZZDATA4.BIN` final; usar exclusivamente o script verificador no armazenamento acessível.
