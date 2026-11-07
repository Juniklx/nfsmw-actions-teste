# NFSMW-Recompiled-Mobile — PRE260: BMW M3 GTR experimental save para MARCEK (2026-11-06)

## Solicitação e fonte
- Após autorização para simular a BMW sem substituir o Punto, o usuário exportou o save **novo** `nfsmw_partidas_2026-11-06_2134.zip` (21h34, 6/11/2026).
- Fonte original no chat, **não enviada ao GitHub nem ao Drive**. Tamanho do ZIP 99.908 bytes, SHA-256 `de922d87a6a858f8eebfccb6599e3dcb3f68719cb8b0454469d3aefe5921fb4f`, 17 entradas, CRC ZIP válido.
- Save atual MARCEK: `saves/MARCEK/actual/MARCEK`, SHA-256 `cf033e6d63e3e8e643c3141eb0c6d83af994888f0d314092af0c51e4b15cd907`. Réplica nativa `B13EBABEBABEBABE/454107D9/00000001/MARCEK/MARCEK` idêntica. Oito saves `actual`/`anterior` da exportação passaram MD5 e 3 CRC32 EA. Quatro réplicas nativas condizentes com os `actual`.

## Estado preservado do perfil MARCEK antes da edição
- Dinheiro **3.000**, Fiat Punto ativo **car_number 81**, carro normal de carreira na garagem 0 e bloco de peças 31.
- Quantidades reais Junkman **após uso em gameplay**: freios 8, motor 7, nitro 8, turbo 8, suspensão 7, pneus 7, transmissão 7, mais 3 tokens de saída da prisão. Total 55 tokens (não restaurar as 8 unidades anteriores). A comparação com o ZIP PRE256 confirmou que 4 fichas tinham sido consumidas/retiradas.
- O registro do carro 82 (linha 1), bloco de peças 32, garagem índice 1 ainda estavam livres. Não havia BMW existente.
- Os outros perfis `NAME`, `CC`, `T`, o histórico de carreira e a cópia `anterior` do MARCEK foram mantidos.

## ZIP experimental criado e validado no contêiner
- Arquivo **somente de teste**, armazenado localmente para download pelo usuário, **não enviado ao Drive**: `NFSMW_PRE260_MARCEK_BMW_M3GTR_JUNKMAN_ATUAL_20261106.zip` (99.674 bytes), SHA-256 `c2ecf95c83d0f11a1e52114ec5f9dc860a9fc2b742016691e381b0db223ad223`.
- BMW **normal/fim de carreira**, com snapshot público `sprintstate/nfs-mw-save-editor/assets/unique_cars/blacklist/boss_car_snapshot_BMW_M3_GTR.json` (408 bytes de bloco de peças, SHA-256 `4e6f3c7fdb5735e402ea0eb113848acb9783d81ac680a47a0b066184eca1b1b4`); `car_number 82`, bloco 32, garagem 1. **Não** é `M3GTRCAREERSTART` do prólogo.
- Cópia do save foi construída e testada em memória segundo `nfsmw_pre259_bmw_dryrun_mc02.py`; o arquivo gerado foi comparado byte a byte com a simulação. Novo save MARCEK SHA-256 `ad0c0a70bb53c63b2ed0c62692f192e0cb1048083cd272a67346a568952e9b8f`.
- Resultado: **somente 2 membros alterados** (saves MARCEK `actual` e réplica nativa), os outros 15 mantidos **byte a byte**. MD5 + 3 CRCs de todos os 8 saves válidos; ZIP CRC válido; ativo/dinheiro/Fiat/Junkman sem alterações. Cópia `anterior` e outros perfis intocados. Reexecução de auditoria independente confirmou id carro 82, assinatura normal BMW, peça 32, garagem 1.
- Artefatos locais: `nfsmw_pre260_gerar_bmw_mc02.py` (gerador fail-closed), `NFSMW_PRE260_RELATORIO_VALIDACAO_BMW_MARCEK.json` (sem bytes de save), ZIP experimental.
- Relatório JSON arquivado no Drive: https://drive.google.com/file/d/1mgvOKC5XywvgV2Hs71z4lloajTFnSFyt/view

## Escopo limitado e procedimento de ensaio
- **Apenas integridade estática do save/ZIP confirmada.** Não afirmar que BMW já apareceu, dirigiu, persistiu ou que roteiro Razor foi alterado. Importação e teste físico no Galaxy S24 FE **pendentes**.
- Antes de importar: guardar o ZIP original de 21h34 e, preferencialmente, fazer **nova exportação de segurança** para evitar perda de progresso posterior. Fechar jogo e importar ZIP experimental pela função **Importar partidas** do próprio app. Abrir perfil MARCEK, verificar Punto **e** BMW, selecionar e conduzir BMW, confirmar dinheiro e Junkman, fechar e reabrir e comprovar persistência. Em erro, importar ZIP original e relatar o comportamento/log.
- A BMW de fim de carreira adicionada à garagem não concede vitória contra Razor nem impede a sabotagem/perda do carro original: essas são tarefas separadas. Não modificar carreira fictícia sem encontrar transições DDay/cutscenes.
- APK não compilada/reinstalada; V37 `io.github.nfsmwrecomp` permanece. Não tocar assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, saves, controles, gráficos, física, 1920x1080, limite 60 FPS e regras térmicas.

## Fluxo histórico
- Esta nota PRE260 é **adendo** ao `CONTEXTO_NFSMW.md` canônico, que ficou em versão antiga (última atualização registrada PRE237) na leitura feita em 06/11. Sincronizar após backup da versão íntegra mais recente, nunca sobrescrever com histórico parcial.
