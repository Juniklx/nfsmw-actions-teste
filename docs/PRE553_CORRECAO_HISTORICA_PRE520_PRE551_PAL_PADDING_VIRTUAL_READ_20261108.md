# PRE553_CORRECAO_HISTORICA_PRE520_PRE551_PAL_PADDING_VIRTUAL_READ_20261108

**Data local:** 2026-11-08 / 2026-11-09 UTC. **Projeto:** NFSMW-Recompiled-Mobile, tunagem BMW M3 GTR carreira. **Correção factual ao checkpoint PRE552**, mantendo todo o histórico do `CONTEXTO_NFSMW.md` intacto.

## Correção do crédito técnico: PRE520 já validara o preenchimento original PAL

- A PRE520 **já havia confirmado** a existência de **512 bytes de preenchimento zero no original PAL `ZZDATA4.BIN`**: [GitHub Actions 42531089216](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42531089216), `AUDIT_OK`, relatório `docs/PRE520_ORIGINAL_PAL_ZZDATA4_SECTOR_PADDING_READONLY.json`.
- O relatório PRE520 autenticou `NFSMW_PAL.zip` Drive ID `1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz`, membro ZIP `NFS/ZZDATA4.BIN` **401.068.032 bytes** inflados, CRC32 **`b46a396c`**, recurso original offset **355.932.160**, `GLOBAL/ATTRIBUTES.BIN` **697.856 bytes** SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`, **341 setores** (698.368 bytes), **512/512 zeros**, recurso novo proposto 698.004 e **364 bytes livres**. PRE520 explicitamente não validava carregamento guest e não criava overlay.
- A PRE551 [GitHub Actions 42545104414](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42545104414), `AUDIT_OK`, **repetiu independentemente** a autenticação do membro ZIP inteiro e a comprovação do padding 512 zeros. **Portanto a validação direta dos 512 zeros NÃO foi uma descoberta inédita da PRE551.** A declaração de novidade no checkpoint PRE552 precisa ser lida à luz desta correção.
- **Contribuição integrada da PRE551:** na mesma execução, reconstruiu VPAK sintético PRE502 em RAM e simulou a leitura do candidato via ZDIR com **SHA256 `d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6`**, checksum EA **`4d05584a`**, registro ZDIR SHA256 `6d0b1744073a50756dcdd296ff5c7ede7dfba35b7a9928e0de5be28f3a18fa78`, preenchimento restante **364 zeros**, utilizando **a cópia dos setores reais recém-lidos**. A combinação dos dois componentes num mesmo teste com leitura virtual RAM é uma ampliação de cobertura, não prova de loader real.
- A PRE518 já montara hipoteticamente os bytes do VPAK e ZDIR em memória, sem ler bytes de `ZZDATA4` PAL; a PRE551 acrescentou o acoplamento dos setores PAL reais na mesma simulação. Não atribuir a PRE551 a invenção do checksum, ZDIR ou empacotamento anterior.

## Estado factual e próximo gate

1. **Dados/arquivo**: VPAK sintético estruturalmente válido para as verificações de layout e endereçamento existentes; ORIGINAL PAL preservado; padding confirmado já desde PRE520 e revalidado na PRE551.
2. **Carregamento em jogo**: não testado nem provado no Galaxy S24 FE; a execução guest do loader, importação de coleção `engine/bmwm3gtr_upgrade_engine_pre499`, `ExpN/RefSpec` na memória do jogo e aplicação de torque seguem **não demonstradas**.
3. **Compra/persistência**: nenhum `SetPackage` guest identificado com prova funcional, nenhuma transação aprovada, save `MARCEK` não tocado, nenhuma APK V49 feita. O próximo teste produtivo precisa instrumentar de forma passiva qual edição/mount VFS está ativa no celular e realizar um ensaio **não transacional, reversível, com dados e save isolados**, antes de liberar preços/compras.
4. **Preservações**: APK release V48 PRE452, Nitro PRE398, iPega PG-9076/touch, 1920×1080, limite 120 FPS, gráficos/shaders/efeitos/física e proteção térmica intactos; chave/certificado release permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` não acessado. Não publicar arquivos de jogo ou senhas.

**Conclusão:** esta é uma correção de cronologia e reivindicação de novidade; não desfaz os resultados `AUDIT_OK` das PRE520 ou PRE551, e não adiciona prova de execução guest.
