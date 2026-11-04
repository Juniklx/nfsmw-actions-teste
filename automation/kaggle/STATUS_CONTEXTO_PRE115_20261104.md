# NFSMW — sincronização do CONTEXTO_NFSMW.md até PRE115 (2026-11-04)

## Resultado e rastreabilidade

- Arquivo canônico no Google Drive: `CONTEXTO_NFSMW.md`, ID `1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB`, **não alterado** pelas tentativas PRE115.
- Conteúdo original confirmado pelo Drive: **304.632 bytes**, SHA-256 `3eac545625a9dce8f08fa62a07dd567ea0fc81a95d043b8fdbbf25253c3bdff0`.
- Tentativa 1: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41821409579 — falhou em `VERIFY_EVIDENCE` por referência incorreta ao arquivo de relatório PRE112, sem acessar o contexto do Drive.
- Tentativa 2: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41821541425 — evidências confirmadas e arquivo canônico lido, mas API Google recusou `files.copy`; operação interrompida antes de alterar o original.
- Cópia de segurança feita pela conexão Google Drive já autorizada, **independentemente do workflow**: ID `1fcbDBOvCB4Cxb89yrP26hh6vfz4-by-Q`, nome `CONTEXTO_NFSMW_BACKUP_ANTES_PRE115_20261104_1132UTC.md`, na pasta `NFSMW_Android`. O conector confirmou **304.632 bytes, conteúdo idêntico** ao original na leitura.
- Tentativa 3: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41821883741 — o backup foi validado por tamanho e MD5 no workflow, porém a API Google recusou `files.update` com **HTTP 403**. Isso indica que a credencial OAuth usada no GitHub não tem autorização suficiente para essa escrita; ainda não identificamos se a restrição decorre de escopo ou permissão específica.
- Resultado: **sem substituição nem atualização do ID canônico**, com backup original preservado. Não solicitar nem revelar segredos de OAuth.
- Adendo cronológico com fontes verificadas no GitHub: `automation/kaggle/ADENDO_CONTEXTO_PRE115_20261104.md`; inclui PRE100–PRE115, V26, PRE99, IMGUI, NDK e ressalvas.
- Foi produzida também uma versão consolidada local usando os **bytes atuais do Drive**, anexando um adendo PRE115 ao final (sem reescrever histórico): `CONTEXTO_NFSMW_CONSOLIDADO_PRE115.md`, **311.148 bytes**, SHA-256 `81155b8c87414540639d9278c8313d3b71c329b5c357cc65ce58de86ddf09cee`. Esse artefato é disponibilizado no chat para substituição manual ou posterior upload autorizado. Seu SHA não é o hash do arquivo canônico atualmente no Drive.

## Próxima ação

1. Se desejar automatizar escrita no Drive por GitHub Actions, revisar o **escopo/permissões** do OAuth conectado sem compartilhar valores, e repetir verificação de escrita apenas após autorização apropriada. Não sobrescrever o documento canônico com credencial somente leitura.
2. Alternativamente, substituir o `CONTEXTO_NFSMW.md` no Drive pela versão consolidada do chat mediante upload manual, **preservando o ID** quando possível. Conferir o SHA-256 da versão final e manter backup.
3. Não alterar V26, backup PRE99, propostas PRE111/PRE115 ou assinatura. A hipótese de rolagem como causa do cabeçalho oculto ainda precisa do teste manual da V26 no S24 FE.
