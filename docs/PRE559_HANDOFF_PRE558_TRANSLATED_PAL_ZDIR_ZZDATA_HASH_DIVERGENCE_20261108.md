# PRE559_HANDOFF_PRE558_TRANSLATED_PAL_ZDIR_ZZDATA_HASH_DIVERGENCE_20261108

**Projeto NFSMW-Recompiled-Mobile, BMW M3 GTR carreira (`type=41`), V48 PRE452.** Os valores do S24 FE foram fornecidos pelo usuário em texto copiado do Shevery; NÃO lidos remotamente pelo GitHub Actions. Em 2026-11-08 (Bahia), usuário confirmou executar pasta extraída, sem ISO, com tradução PT-BR baseada na PAL.

## Evidências originais PAL previamente autenticadas
- PRE551/PRE557: `NFS/ZDIR.BIN` com 1.390 registros de 24 bytes, **33.360 bytes**, SHA-256 `7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee`.
- PRE557: `NFS/ZZDATA4.BIN` com **401.068.032 bytes**, SHA-256 do membro original completo `8b0e6c09b9e55e78d319521b634119055ad6fb2f144aa13660f60bdea7cf05d3`; CRC32 `b46a396c`.
- PRE551: no PAL original, `GLOBAL\\ATTRIBUTES.BIN` possui hash de nome **`0x9775379a`**, linha original **806** do ZDIR, arquivo nº 4, deslocamento **355.932.160 bytes**, tamanho de recurso **697.856 bytes**, reserva **698.368 bytes** com 512 zeros verificados. A linha 806 NÃO pode ser reaproveitada diretamente na tradução sem checar seu próprio índice.

## Relato real do Shevery da pasta traduzida
O usuário executou `find/stat/sha256sum` e colou a saída:
- `NFS/ZDIR.BIN`: **33.312 bytes**, SHA-256 **`832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf`**.
- `NFS/ZZDATA4.BIN`: **401.068.032 bytes**, SHA-256 **`7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`**.
- Logo, os dois SHA-256 diferem do PAL original. O ZDIR traduzido tem **48 bytes a menos**, equivalentes ao espaço de dois registros de 24 bytes; **isso NÃO prova que dois registros específicos foram excluídos**, nem que o recurso de atributos se manteve no mesmo setor.
- O ZZDATA4 traduzido possui mesmo tamanho total do original, mas **conteúdo diferente**. Não supor que os 512 bytes de padding original ou o SHA do `GLOBAL/ATTRIBUTES.BIN` são iguais na tradução.

## PRE558, auditoria concluída no GitHub Actions
- Run [42551489746](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42551489746): `AUDIT_OK`, documento `docs/PRE558_PAL_PTBR_HASH_COMPARISON_READONLY.json`.
- O job validou os hashes e os tamanhos reportados pelo usuário contra metadados originais PAL autenticados de PRE551/PRE557, **sem acesso ao telefone**. Registrou `on_device_read_this_CI=false`, `translation_attributes_resource_offset_verified=false`, `original_ZDIR_row_806_transferable_to_translation=false`.
- Prova do método de leitura de registros feita localmente com arquivo **sintético** de 33.312 bytes usando `od -An -v -tu4` e `awk`; não prova compatibilidade específica de todos os comandos no Android/Shevery.
- Helper inofensivo: `automation/device/pre558_translated_pal_zdir_attributes_record_readonly.sh`. Faz varredura somente leitura de `*/NFS/ZDIR.BIN`, seleciona estritamente o hash SHA-256 fornecido, converte os registros de seis palavras de 32 bits e procura `0x9775379a`. Imprime só índice, archive, setor, tamanho, checksum, sem caminho absoluto ou dados do jogo.

## Próximo gate obrigatório
1. No Shevery, obter índice, setor e tamanho do `GLOBAL\\ATTRIBUTES.BIN` da **pasta PT-BR real**, usando o hash do nome e leitura somente do ZDIR. Se não houver registro, investigar formato/hash/tradução, sem transplantar dados do PAL original.
2. Validar limites e derivar o hash do recurso de atributos traduzido por leitura parcial **sem qualquer escrita**.
3. Só depois tentar overlay de teste reversível em cópia descartável, nunca em `MARCEK`, e verificar loader guest, nova coleção BMW `ExpN`, catálogo, custo, instalação, física e persistência.
4. Preservar APK V48, assinatura, V46/V47, Nitro PRE398, PG-9076, gráficos, FPS, proteção térmica, dados traduzidos e save `MARCEK`.

**Status:** divergência entre índices e arquivos traduzidos = comprovada a partir dos hashes e tamanhos reportados pelo usuário; posição do recurso traduzido = ainda não identificada; BMW tunável = não habilitada; nenhum APK, arquivo de jogo ou save foi alterado.
