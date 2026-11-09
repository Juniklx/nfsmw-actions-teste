# PRE608_HANDOFF_PRE604_607_BMW_CHILD_ENGINE_PARENT_20261109

**Atualização:** 2026-11-09, America/Bahia. Recompilação estática Xbox 360 USA Need for Speed Most Wanted (2005) → Android, Galaxy S24 FE. Referência operacional: **V48 PRE452** `io.github.nfsmwrecomp`, certificado release permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.

## Estado real anterior

- PRE592: variante PTBR `GLOBAL/ATTRIBUTES.BIN` com coleção motor BMW sintética nova, `RefSpec` ativo (stock+novo) e limite motor **0**; **usuário confirmou carregar MARCEK**, log anterior SHA256 `842fbc19031e81adb7988ad3e2fbd2de35850ce19abde581681025c4172ed1b9`. **Último estado informado no S24 FE é PRE592 aplicada. Não há relato de rollback.**
- PRE573 / PRE502: o mesmo recurso combinado e RefSpec ativo com limite motor **1**, parent original da nova coleção `default` (eec2271a), mostrou `MARCEK está corrompido`. Restaurando dados originais o perfil voltou a carregar. PRE596 comprovou que PRE591 com limite 0 vs PRE502 com limite 1 diferem somente no VPAK offset 256619 (inteiro BE 256616, BIN 256488), porém NÃO prova que o contador em si seja inválido.
- PRE599–601: reconheceram leituras de `40(rX)` em funções que na verdade manipulam ponteiros, e GetMaxLevel/SetLevel seguem não identificados.

## PRE604 — comparação original de herança e StrE

- [Run 42590630384](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42590630384) `AUDIT_OK`, relatório `docs/PRE604_BMW_PARENT_ORIGINAL_PUNTO_STRE_READONLY.json`. Leu fonte VPAK autenticada SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`, reconstruiu em memória PRE502 e validou cada header de coleção.
- BMW engine stock coleção `cd88083f` com parent `eec2271a` (`default`). Punto engine stock `a6ee7a11` com parent `default`. Segundo motor Punto original `a6f0f405` com parent **`a6ee7a11`** (herda do primeiro motor), está em `VLT` e é resolvido por seu `RefSpec` com **2 referências** e contador original **4**.
- **O segundo motor original do Punto não possui nome na StrE** original (hash não encontrado), mas a coleção está em VLT e é referenciada no carro. PRE504 constata que **1065 das 2339 coleções VLT originais** não têm hash de nome na StrE. Não significa que qualquer nova coleção sem StrE terá aceitação garantida, mas a ausência de nome não é, por si só, prova de falha.
- Nova coleção sintética BMW `33b0fa80` gerada pela PRE502 foi clone da coleção stock, apenas com nome/hash novo, herdando diretamente `default` ao invés da BMW stock. **Hipótese:** ao selecionar nível de motor 1, a cadeia de herança da nova coleção pode diferir daquela esperada pelo motor; não foi demonstrada causalidade.

## PRE605 — controle de modificação mínima em RAM

- [Run 42590907933](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42590907933) `AUDIT_OK`, relatório `docs/PRE605_BMW_ENGINE_PARENT_ONLY_RAM_RESULT.json`.
- Partindo do VPAK combinado PRE502 **698004 B**, SHA256 `d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6`, modificou **somente os quatro bytes absolutos do parent da nova CollectionLoad em 520072–520075**, de `eec2271a` para `cd88083f`. O `RefSpec` com dois itens e o contador engine BMW **1** ficaram idênticos ao PRE502. Nenhum outro byte do VPAK mudou.
- VPAK candidato 698004 B SHA256 **`11c122bf9b32011fd3955498517e51f2f1f11551bc2bbd9f448201bc4ef862f3`**, checksum EA **`31aef5d7`**. Essa variante ainda NÃO havia sido aplicada a jogo, nem demonstrou ganhar torque.
- O parent corrigido foi uma hipótese de estrutura baseada em convenção original Punto, **não uma correção de gameplay comprovada**.

## PRE606 — material privado PT-BR com fonte/ZIP autenticados

- [Run 42591196366](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42591196366) `AUDIT_OK`, relatório `docs/PRE606_BMW_CORRECTED_PARENT_PRIVATE_PTBR_METADATA.json`. Verificou o ZIP PTBR completo por streaming, sem alterar fonte.
- Pasta privada: https://drive.google.com/drive/folders/1AR2uE0Oel80gciW7xSjEJEIKjnG9wC4I .
- `PRE606_ZDIR_BMW_CHILD_PARENT_CORRECTED.bin`: 33312 bytes SHA256 `f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2`, Drive ID `1DaeV8ouEkl97D0qJEW1Jab4pi9vh6FyR`.
- `PRE606_ZZDATA4_FIRST341_BMW_PARENT_CORRECTED.bin`: 698368 bytes SHA256 `93327b44eb54b0ec9b14e51e7b35da9071e9531454c49819c35e6e6172c284a5`, Drive ID `1acGG0hYYzcfYPRWDzpCeuAaUgAJoI7Nk`.
- Aplicando esses 341 setores apenas a uma **CÓPIA COMPLETA** de `NFS/ZZDATA4.BIN` PTBR original de **401068032 bytes**, hash esperado do arquivo resultante: **`1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146`**. Nunca substituir o ZZDATA4 inteiro pelo fragmento.
- `ZDIR.BIN` original, 33312 bytes SHA256 `832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf`. `ZZDATA4.BIN` original SHA256 `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`. Registro ZDIR 805 recebeu apenas tamanho 698004 e EA CRC 31aef5d7.

## PRE607 — scripts Shevery aguardando teste real

- [Run 42591593420](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42591593420) `AUDIT_OK`, `docs/PRE607_SHEVERY_CHILD_ENGINE_PARENT_STATIC_PREFLIGHT_RESULT.json`: `sh -n` passou, hashes exatos foram conferidos, entrada falsa abortou sem escrever, rollback sem backup abortou.
- Scripts no GitHub:
  - `automation/device/pre607_apply_bmw_child_parent_corrected_shevery.sh`
  - `automation/device/pre607_restore_bmw_child_parent_corrected_shevery.sh`
  - Guia `docs/PRE607_MANUAL_BMW_DERIVED_ENGINE_PARENT_DEVICE_TEST_20261109.md`.
- **PRE607 não foi executada no Galaxy S24 FE e nem testada pelo guest**. Se usuário quiser fazer o A/B, **precisa fechar V48 e restaurar a PRE592 anteriormente aplicada**, confirmando `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`. Só então baixar os fragmentos privados para `/sdcard/Download/PRE606` e aplicar PRE607 em `/storage/emulated/0/NFSMW_PTBR`. Os scripts exigem originais/hashes e gravam backups `.pre607_original_backup` antes de ativar.
- Saída esperada após aplicação `PRE607_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`; só então entrar na V48, tentar abrir MARCEK e acessar oficina BMW M3 GTR, anexar `nfsmw.log`. Não confundir carregamento com peças compráveis, compra/persistência e ganho físico.
- Rollback, sempre com jogo fechado: `pre607_restore_bmw_child_parent_corrected_shevery.sh`, exigir `PRE607_RESTORE=ORIGINAIS_VERIFICADOS`.
- Se ainda surgir `MARCEK está corrompido`, o parent ajustado **não resolveu**, e a hipótese de outro problema em lookup/ExpN/RefSpec volta a ser prioritária. Não reaplicar PRE573.
- Se carregar, hipótese de herança ganha força, mas a compra/instalação/tunagem física/persistência continuam pendentes.

**Regras de continuidade:** V48 intacta, Nitro PRE398, controle iPega PG9076/touch, 1920×1080, meta 120 FPS (logs 60), gráficos/shaders/efeitos/física geral e térmicas intactos. Nunca regenerar assinatura permanente nem tocar em senhas. O usuário aceita recriar save depois, mas não ordenou exclusão do MARCEK. **Nenhum build V49**.

**Status de publicação:** PRE604/605/606/607 `AUDIT_OK` CI; geração privada de fragmentos verificada; instalação no telefone e eficácia ainda **NÃO VERIFICADAS**.
