# NFSMW — PRE119B: correção da sincronização do relatório Kaggle (2026-11-04)

## O que foi verificado neste turno

- Arquivos `LEIA_PRIMEIRO_NFSMW.md` e `CONTEXTO_NFSMW.md` lidos; o contexto canônico ainda está desatualizado relativamente às etapas PRE116–PRE119 e sua atualização no Drive foi bloqueada anteriormente por OAuth HTTP 403. Não reescrever o original sem garantia de backup e autorização.
- `automation/kaggle/status/pre117_single_scroll.json`: `PRE117_SCROLL_UNICO_ARM64_VALIDADO_NAO_APLICADO`, run [41825894541](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41825894541) com `success`. Backup PRE99 e fonte PRE92 íntegros, diff de 30 linhas, Android ARM64 C++23 passou, nenhuma APK V27 criada.
- `automation/kaggle/status/pre118_build_tree.json`: `PRE118_PRE99_BUILD_TREE_AUDITADO_SEM_APLICAR`, run [41827163959](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41827163959), `success`. PRE99 íntegro, fonte PRE92 e diff PRE117 reproduzidos; Gradle e CMake públicos presentes. **Não inspecionou a sessão Kaggle ativa** e não validou assinatura de release.
- Pesquisa Google Drive por `NFSMW_PRE119_ARVORE_ATIVA` e `PRE119`: **nenhum relatório encontrado** no momento da consulta.
- Problema na PRE119 anterior: o script colocava o JSON em `/kaggle/working/`, mas `nfsmw_kaggle_autosync_logs_v1.py` monitora exclusivamente `/kaggle/working/NFSMW_Kaggle_Logs/` com sufixos `.json/.log/.txt`.
- PRE119B foi criada para corrigir só o **destino do relatório** e a unicidade do timestamp, preservando as verificações originais e a política somente leitura. Script: `automation/kaggle/pre119b_auditar_arvore_autosync.py` no repositório privado. Anexo de conversa: `nfsmw_pre119b_arvore_kaggle_autosync.py`; SHA-256 local `27b615820290bd0fa76374afcc7ccfc43d490c84631abc9a693375ca0afe82de`.
- Validação local: `python -m py_compile` passou; execução fora do Kaggle concluiu `NENHUMA_BASE_UNICA_VALIDADA_NAO_APLICAR` gerando JSON, **sem patch**. Isso não valida a árvore Kaggle.
- Para transmitir, executar PRE119B na **mesma sessão Kaggle que contém a árvore real** e com o hook de autosync previamente ativado. A função `nfsmw_sync_logs()` pode forçar a sincronização após gerar o relatório. Pasta destino Drive: `NFSMW_Android/06_Logs_e_Medicoes`, ID `1yw1Z83O0d83CoQccjYREYfhxAF17eHD-`.
- Nenhum token, senha, keystore, código do jogo ou APK foi publicado pelo script PRE119B; não aplicar PRE117 ao projeto ativo até confirmar o SHA-256 da fonte e do Gradle da árvore efetiva.

## Decisão após PRE119B

Se `BASE_KAGGLE_PRE92_IDENTIFICADA_SEM_PATCH`, revisar o relatório e preparar um patch PRE120 com backups e pré-condições exatas, **sem executar automaticamente**. Se `DIVERGENTE_NAO_APLICAR` ou `NENHUMA_BASE_UNICA_VALIDADA_NAO_APLICAR`, investigar o estado real (sessão reiniciada, árvore diferente, código já alterado ou Gradle divergente) sem sobrescrever arquivos. Antes de uma V27 confirmar versionCode > 26 e reutilização do certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; jamais criar/alterar chave.
