# NFSMW — PRE120: segurança antes de executar o notebook Kaggle original (2026-11-04)

## Resultado confirmado

- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41831030088 — **success**.
- Relatório privado sanitizado: `automation/kaggle/status/pre120_notebook_cell_audit.json`, `PRE120_NOTEBOOK_ESTRUTURA_AUDITADA_SEM_EXECUTAR`.
- O alvo foi `juniklx/nfsmw`, obtido via `kaggle kernels pull ... -m` **somente leitura**, sem `push` e sem executar células; ID e formato do notebook conferidos.
- **4 células**, sendo as três originais preservadas na PRE119B e a quarta célula de auditoria PRE119B adicionada no GitHub run 41830201701.
- Célula 0: código Python com 325 linhas, SHA-256 `27d02b480e156b98733b2033b4c35f7de8cd5bbae53d0674836b2045cce10e3a`. A análise AST identificou `tarfile.open`, `tar.add`, `MANIFEST.write_text`, `upload`, `drive.files().create`, `credentials.refresh`, `UserSecretsClient`: **faz operações de arquivo e Google Drive**, não segura para disparar indiscriminadamente como dependência de uma auditoria.
- Célula 1: Markdown (6 caracteres), sem execução.
- Célula 2: código Python com 75 linhas, SHA-256 `eb613b338b294bc0363b8a933b56ed1655822acfeb2cebc7f800ce6225494929`. AST identificou `UserSecretsClient`, leitura Drive `drive.files().get_media`, `SCRIPT_LOCAL.write_bytes`, `exec`, `compile`. A rotina executa código Python baixado do Drive; seu conteúdo **não foi auditado nesta etapa**.
- Célula 3: PRE119B, SHA-256 `c2ff90772213a7f7ffd4b63cf6e1e40dcca151984e7bda569e46cdc6f684f664`, gera relatório de hashes e opcionalmente chama `nfsmw_sync_logs()` se o hook estiver ativo. Não aplica patch.
- O relatório armazena somente SHA, identificadores de chamadas e indicadores de risco; **não publica os textos completos das células, literais de código, credenciais, APKs ou material privado**.
- Pesquisa do Drive por `NFSMW_PRE119_ARVORE_ATIVA` e `PRE119B` até este turno: nenhum relatório correspondente localizado. PRE119B inserida **não** implica execução.
- Limitação técnica essencial: `kaggle kernels push` sem `--no-run` executa **o notebook inteiro em execução Kaggle**, não uma célula seletiva dentro de uma sessão interativa já existente. A árvore original que existe ou existiu em um processo interativo Kaggle não pode ser presumida presente nessa nova execução. **Não tentar a execução completa agora**, pois células originais fazem TAR/upload e execução dinâmica de script externo.
- Mesmo um notebook isolado que execute apenas PRE119B em sessão recém-criada produziria hashes de uma árvore possivelmente inexistente e **não comprovaria o estado do ambiente ativo do usuário**.

## Próxima ação segura

Aguarda-se uma forma autorizada de executar somente a célula PRE119B na sessão Kaggle que contém a árvore, sem desencadear as células originais. Enquanto isso, o projeto pode continuar por inspeções `read-only` nos backups já verificados, sem criar V27. Quando houver novo relatório real `NFSMW_PRE119_ARVORE_ATIVA_*.json` no Drive, conferir caminho, horário e SHA da fonte/Gradle antes de aplicar qualquer patch.

**Estado preservado:** V26, PRE99, versões anteriores e assinatura permanente sem alteração; PRE117 tem somente compilação sintática ARM64 aprovada, sem teste funcional. O `CONTEXTO_NFSMW.md` canônico do Drive segue sem os novos adendos por OAuth HTTP 403 em tentativas anteriores; este adendo fica no GitHub privado.
