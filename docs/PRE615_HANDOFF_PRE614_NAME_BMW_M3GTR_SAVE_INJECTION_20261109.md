# PRE615 — BMW M3 GTR adicionada ao perfil NAME por edição offline de MC02 (2026-11-09)

**Fonte:** usuário solicitou repetir a inclusão da BMW no save novo e anexou `nfsmw_partidas_2026-11-09_0813.zip`. Foi lido no contêiner local. **Dados de save pessoais NÃO foram publicados no GitHub/Drive**. Somente os hashes e metadados técnicos a seguir foram registrados. A nova exportação modificada foi criada no sandbox local do chat e entregue diretamente ao usuário, sem upload dos seus saves ao GitHub ou Drive.

## ZIP atual e validações

- ZIP original anexo: **80.??? B (tamanho exato não usado neste gate)**, SHA256 **`3f95ab67c9c33b157dad71d8f9bff4a92159c148b21edb1c831bda142d7752c4`**, **13 entradas**, CRC ZIP correto. Manifesto: `NFS Most Wanted Recompiled: partidas exportadas el 2026-11-09 08:13`, `motor=nativo`, `version=0.5.6`.
- Contém `NAME`, `MARCEK`, `CC`, `T` e as respectivas cópias de save. Todos os 8 saves atuais/anteriores passaram **MC02 62.688 B, versão interna 0x10D, MD5 do payload e 3 checksums EA CRC32**; a réplica nativa e `actual` do NAME eram iguais.
- Novo perfil **NAME**: save SHA256 original `aa401b6e3f6a35a27e57dac2ddec144704949089b0b04e5420ce7e1b0d22e76d`; **nenhum carro registrado** na tabela de 119 carros, saldo **0**, car active `0x12345678` (sentinela sem carreira iniciada), rank 16. O nome/alias e progresso existentes foram mantidos byte a byte.
- Perfil **MARCEK**: save SHA256 `574b3fe386ea38ad41963a148d67dcff0a14f951b86d78660dfac14ff5070c33`; contém BMW normal de fim de carreira já inserida pela PRE260 e pilotada pelo usuário na V37: carro número 82, assinatura nativa `23cc4a4e4e085fb3`, flags `0042`/misc `000f`, parts slot 32, career slot 1. Trata-se de **BMW de fim de carreira**, não da variante inicial `M3GTRCAREERSTART`. O próprio bloco de peças BMW existente de 408 B no MARCEK foi usado como doador, sem precisar fabricar um template de outro jogo.

## Construção local PRE614 (nenhuma alteração de APK ou game assets)

- Gerador fail-closed `/mnt/data/nfsmw_pre614_injetar_bmw_name_mc02.py` (apenas no sandbox da sessão; não foi enviado ao GitHub). Ele se recusa a editar input ZIP/SAVE com SHA diferente, CRC/MD5 inválido, registro ocupado ou layout imprevisto.
- **NAME novo tinha zero carros**, então alocou primeira linha livre da tabela de carros número **81**, parts slot **31** (bloco de índice 0), career slot **0**; reutilizou assinatura e bloco visual/peças BMW de MARCEK (apenas marker de slot adaptado). Flags `0x0042` + misc `0x000F` de BMW pink-slip mantidos. O apontador de carro ativo `NAME` mudou de sentinela `0x12345678` para carro 81, conforme estratégia de corrigir active pointer do editor público de saves. A garagem/career pursuit slot 0 foi inicializada em estado limpo (heat/counters zerados, MaxBusted=3, padding AA nativo).
- Regiões de diferença permitidas no save NAME: CRC headers 0x10–0x1b, active 0x4034–0x4037, owned record 0x6221–0x6234, parts block 0x9CD5–0x9E6C, pursuit record 0xE2F5–0xE32C, MD5 0xF4D0–0xF4DF. O teste de diferença byte a byte encontrou **227 bytes totais** alterados, sendo **203 fora de checksums/MD5**. Validação de offsets se recusaria a continuar se tivesse alterado regiões não planejadas.
- Reparou o MD5 do payload e os três CRCs EA big-endian. Releitura validou integridade nativa do arquivo modificado.
- Nome do arquivo entregue: **`NFSMW_PRE614_NAME_BMW_M3GTR_EXPERIMENTAL_20261109.zip`**, **81.110 B**, SHA256 **`edab070c5006524c124e4e60e62d5a404398f389b2ea6784031a1049ee2c2a28`**.
- Save NAME modificado: SHA256 **`6ff1dce2634284bc0a49fe306bdf0ed921554df86c9032df7a871fa8633fb416`**.
- **EXATAMENTE dois membros ZIP editados**, os demais **11 idênticos byte a byte**:
  - `saves/NAME/actual/NAME`;
  - `B13EBABEBABEBABE/454107D9/00000001/NAME/NAME`.
  - O `saves/NAME/anterior/NAME` ficou original. Perfis `MARCEK`, `CC`, `T`, cabeçalhos e manifesto preservados. Uma segunda auditoria independente confirmou lista/ordem de membros, os dois únicos diffs, a réplica nativa do novo save, as regiões alteradas, o template doador, o dinheiro e alias, e CRC ZIP correto.

## Importação e próximos resultados pendentes

- **Ainda não foi importado no Samsung Galaxy S24 FE** nem visto BMW na garagem do perfil NAME sob PRE607. Não alegar sucesso de gameplay, compra ou tunagem. O arquivo foi apenas gerado, verificado estaticamente e disponibilizado ao usuário no chat (sandbox; não há ID de Drive).
- A cópia enviada pelo usuário refere-se à exportação das **08:13**; se houver progresso posterior nos perfis antes da importação, uma importação de ZIP inteiro poderá restaurar o estado dessa exportação. Orientar fazer backup pela função Exportar Partidas antes de importar e confirmar hora dos arquivos.
- **Procedimento:** fechar V48, salvar cópia do ZIP original 08:13, usar **Importar Partidas** no próprio app selecionando ZIP PRE614, abrir somente perfil **NAME**, verificar BMW M3 GTR normal na garagem, opção de dirigir, acesso a `Personalizar → Desempenho → Motor`, evitar assumir compra funcional; sair e reabrir e exportar novo save/log. Não restaurar PRE607 nem misturar patches de game data durante teste.
- Como NAME está no estado de carreira inicial sem veículo possuído, a inclusão de BMW como primeiro carro ativo pode afetar sequência do prólogo e progresso. Se travar ou der save corrompido, restaurar ZIP original e preservar o novo log. Esse risco é real mesmo com todos os checksums corretos.
- Não modificar assinatura permanente, V48 PRE452, package `io.github.nfsmwrecomp`, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG-9076, touch, 1920x1080, meta FPS 120, gráficos/física geral/thermal.
- **Fonte externa conferida:** código atual do `sprintstate/nfs-mw-save-editor` `core/snapshot_injection.py`, `core/savefile.py`, `core/switch_format.py`, `core/checksums.py` e bundle de BMW; modelo de alocação de carro número 81+slot, parts slot 31+índice, carreira/pursuit slot, integridade MC02. Edição de fato foi construída sobre o **template BMW extraído do próprio save MARCEK fornecido**, e não depende de correspondência integral da versão atual do template público.
- **Conclusão PRE615:** ZIP experimental e integridade estrutural **validados localmente**, teste no jogo **pendente**. PRE607 ainda último game-data patch informado ativo no aparelho. Não publicar o ZIP pessoal em GitHub/Drive e não apagar perfis.
