# PRE588_HANDOFF_PRE586_UNLINKED_VLT_PRE587_20261109

**Data local:** 2026-11-09 (America/Bahia). **Projeto:** NFS Most Wanted (2005) Xbox 360 USA → Android, release V48 PRE452, BMW M3 GTR carreira type 41. Checkpoint posterior à PRE585 e ao controle de carregamento real da PRE581.

## Estado consolidado comprovado pela PRE584/PRE585

- O usuário executou o script PRE581 no Samsung Galaxy S24 FE e apresentou a saída `PRE581_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`; depois confirmou: **"Consegui carregar agora"** ao abrir a mesma carreira `MARCEK`.
- O `nfsmw.log` anexado e lido localmente tinha **217.837 bytes, 1.303 linhas, SHA256 `c7f3cf03d26c35b3f51a4dda1109034dc0ffe31de5e5f7f4e6ac32e760265af1`**. O arquivo contém duas sessões; **somente a segunda, iniciada às 01:58:25, é a PRE581**. Ela montou `/storage/emulated/0/NFSMW_PTBR`, leu **697.856 bytes de `NFS/ZZDATA4.BIN` no offset 0**, abriu `MARCEK` de 62.688 bytes quatro vezes com retorno `XamContentCreate=00000000`. O sucesso da carreira foi declarado pelo usuário e é compatível com o log; não é uma conclusão derivada somente do retorno do kernel.
- Com PRE573 combinada, usuário relatou `MARCEK está corrompido`; após rollback dos dados originais, o save carregou; com PRE581 torque-only original-layout, carregou novamente. **A variante de torque mínima é compatível com carregar o save; NÃO provou potência +5%, compra, upgrade, física real, persistência ou desbloqueio da oficina.**
- A PRE585 [42565493339](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42565493339) atualizou `CONTEXTO_NFSMW.md` com backup/readback, **895.872 bytes, SHA256 `ba60e6dd573b3958b64b7e1fc29a355d9afee99b6f05fb218dde53702d3676d6`**. Handoff anterior: `docs/PRE584_HANDOFF_PRE581_TORQUE_ONLY_MARCEK_SUCCESS_LOG_20261109.md`.

## PRE586 — novo candidato estrutural VLT **sem ligação com o pvehicle**

- [GitHub Actions run 42565596510](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42565596510), `AUDIT_OK`, relatório `docs/PRE586_PTBR_BMW_UNLINKED_VLT_PRIVATE_METADATA.json`.
- Foi recriado o recurso sintético combinado PRE502/572, que possui nova coleção `engine/bmwm3gtr_upgrade_engine_pre499`, novo export, layout físico e entrada `PtrN`; **apenas** dois vínculos ativos com a BMW da carreira foram devolvidos aos valores originais: contador `pvehicle` **0** e ponteiro de `RefSpec` original **256660**. O recurso novo fica **não referenciado pelo motor ativo da BMW**; a estrutura `VLT/ExpN/PtrN` ampliada permanece para testar aceitação estrutural do carregador. O nome da nova coleção continua ausente na tabela original `StrE`; ainda não se sabe se isso é permitido.
- O VPAK candidato possui **698.004 bytes**, SHA256 **`a7e37cd5679f8a25d552049d9d0324b81fb74abe3b87c81a65348dbaa9fff7d7`**, checksum EA **`820a01ba`**. Em relação ao VPAK PRE502 combinado, **4 bytes de valor** diferem nos dois campos restaurados (não são novas edições desconhecidas). O arquivo ZDIR PT-BR continua com registro 805, archive 4, setor 0.
- Pasta privada no Drive: https://drive.google.com/drive/folders/17KJCMPZ-LwCZZv7SBD1WPU0SIPZpporD
- Fragmentos com readback:
  - `PRE586_ZDIR_VLT_NEW_COLLECTION_UNLINKED.bin`, **33.312 bytes**, SHA256 **`3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025`**;
  - `PRE586_ZZDATA4_FIRST341_UNLINKED_VLT.bin`, **698.368 bytes**, SHA256 **`11f233a7a22df3822573a3a52af50f7c9b27f4b5c5cba77fdaad3c4e03041271`**.
- O SHA256 previsto do `ZZDATA4.BIN` **completo** de 401.068.032 bytes, após aplicar somente os primeiros 341 setores a uma cópia do original, é **`524c22622039086c9207f25b3a82823fb62d8879e70d0142730bca2b5cdda996`**. O ZIP original PT-BR foi verificado integralmente por streaming; sem publicação do arquivo completo alterado nem mudança no telefone. Esses fragmentos **NÃO são jogo completo**.

## PRE587 — scripts manuais de teste e rollback

- [GitHub Actions run 42565935803](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42565935803) `AUDIT_OK`, `docs/PRE587_SHEVERY_UNLINKED_VLT_STATIC_PREFLIGHT_RESULT.json`: scripts passam em `sh -n`, abortam com hashes errados sem escrever, rollback sem backups recusa. Primeira execução anterior 42565834509 também foi bem-sucedida, mas emitiu **nome de relatório “TORQUE_ONLY” incorreto**; rótulo foi corrigido no segundo run.
- Scripts exclusivos PRE587:
  - `automation/device/pre587_apply_bmw_unlinked_vlt_shevery.sh`
  - `automation/device/pre587_restore_bmw_unlinked_vlt_shevery.sh`
  - Guia `docs/PRE587_MANUAL_BMW_UNLINKED_VLT_GUEST_TEST_20261109.md`.
- O teste **AINDA NÃO FOI EXECUTADO NO S24 FE**. Antes dele, o usuário precisa **fechar a V48 e RESTAURAR o experimento PRE581**, usando `pre581_restore_bmw_torque_only_shevery.sh` na pasta real `/storage/emulated/0/NFSMW_PTBR`, e confirmar `PRE581_RESTORE=ORIGINAIS_VERIFICADOS`. PRE587 exige hashes PT-BR originais e falhará se o patch PRE581 continuar aplicado.
- Somente depois pode baixar os fragmentos PRE586, aplicar PRE587 com backup de arquivos originais de jogo `.pre587_original_backup`, abrir V48 e verificar se a mesma carreira `MARCEK` carrega. A PRE587 está preparada para rejeitar arquivos inesperados e preservar backups, mas **a etapa no telefone é manual**. Analisar novo log da execução antes de fazer novo patch.
- Se PRE587 carregar, indica compatibilidade de **nova coleção VLT não vinculada** até o ponto testado e desloca suspeita para `pvehicle`/RefSpec/contador da PRE573; se der aviso de corrupção, a presença da coleção/VLT expandido já é incompatível neste teste, sem comprovar exatamente qual subestrutura. Não concluir causa sem novo experimento.

**Restrições permanentes:** manter APK V48 PRE452, package `io.github.nfsmwrecomp`, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG9076/touch, 1920×1080, meta 120 FPS (cap observado nas sessões 60), gráficos/shaders/física geral e proteção térmica. Sem acesso a chave, senha, alteração de APK ou save pelo runner. O usuário aceitou criar outra carreira quando necessário, sem ordenação de apagamento automático.

**Status:** PRE586 privado `AUDIT_OK`; PRE587 CI `AUDIT_OK`; aplicação em dispositivo **pendente**; BMW tunável/comprável/instalável/persistente **não comprovada**.
