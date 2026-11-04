# NFSMW — PRE119B adicionada ao notebook original do Kaggle (2026-11-04)

## Comprovação da edição feita sem navegador

- Solicitação atual: usuário pediu que a assistência adicionasse o script diretamente, pois não tinha acesso ao navegador.
- Notebook Kaggle confirmado por pull de leitura: `juniklx/nfsmw`; [abrir no Kaggle](https://www.kaggle.com/code/juniklx/nfsmw).
- Execução de descoberta somente leitura: [GitHub Actions 41830024991](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41830024991), `success`; confirmou `kernel-metadata.json` com ID correto e **3 células** anteriores.
- Primeira tentativa de edição [41829794941](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41829794941) falhou com **404 no endpoint de status da sessão**, sem baixar ou alterar o notebook. Esse 404 não significava notebook inexistente.
- Segunda tentativa [41830201701](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41830201701) terminou com `success` em todas as etapas: `kaggle kernels pull`, preparação idempotente de uma célula, `kaggle kernels push --no-run`, nova leitura e comparação do conteúdo.
- Relatório sanitizado `automation/kaggle/status/pre119b_kaggle_notebook_cell.json`, `status=PRE119B_CELULA_INSERIDA_E_CONFERIDA_SEM_EXECUTAR`.
- Antes: **3 células**; depois: **4 células**, preservando as três anteriores e os metadados originais. SHA-256 do notebook obtido antes: `d32fe090374211c623840fa0431daaabba713cb2542f3c1a136bd1328477bdf7`. Célula PRE119B salva e conferida por SHA-256 `c2ff90772213a7f7ffd4b63cf6e1e40dcca151984e7bda569e46cdc6f684f664`.
- A versão anterior do notebook continua recuperável pelo histórico de versões do Kaggle. O novo código foi inserido como **última célula**, e contém a PRE119B de auditoria somente leitura mais uma tentativa de chamar `nfsmw_sync_logs()` caso o hook esteja definido.
- `--no-run` equivale a salvar nova versão sem execução. Portanto **NÃO** foram executadas as quatro células, `/kaggle/working` não foi inspecionado, nenhum JSON de auditoria nova foi gerado no Drive, não houve APK V27, patch, assinatura ou leitura de chaves.

## Próxima decisão com segurança

Para obter o resultado da **árvore Kaggle ativa**, é necessária uma execução real da célula ou do notebook na sessão apropriada. Não disparar automaticamente o notebook inteiro sem confirmar o conteúdo/efeitos das outras três células, pois podem realizar procedimentos de build ou alterações no projeto. Uma execução Kaggle isolada em outra sessão não comprovaria a árvore de trabalho da sessão original.

Se a PRE119B for executada futuramente com a árvore presente em `/kaggle/working`, ela salvará `NFSMW_PRE119_ARVORE_ATIVA_*.json` em `/kaggle/working/NFSMW_Kaggle_Logs` e acionará `nfsmw_sync_logs()` se definido. Só após o relatório, avaliar backup e patch PRE117. Respeitar a assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`, versionCode > 26 e os limites gráficos/térmicos anteriores.

O arquivo canônico `CONTEXTO_NFSMW.md` no Drive não foi modificado; a limitação de escrita OAuth HTTP 403 permanece documentada em histórico anterior.
