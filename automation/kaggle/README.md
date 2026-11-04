# NFSMW — integração Kaggle PRE100 (teste isolado)

## Estado

A infraestrutura do teste está instalada, mas **nenhuma execução foi iniciada**. Não substitui o notebook existente `juniklx/nfsmw`.

O workflow `.github/workflows/nfsmw-kaggle-pre100.yml` pode iniciar automaticamente quando um arquivo de solicitação `.json` é publicado em `automation/kaggle/requests/` na branch `main`, ou manualmente via `workflow_dispatch`.

## Segurança

- Este repositório é **público**. Nunca enviar aqui código recompilado do jogo, APKs, ISO, chave privada, senhas ou tokens.
- Cadastrar somente o token de acesso no **GitHub Actions Secret** de nome `KAGGLE_API_TOKEN`. Não salvar token em commits ou mensagens.
- A primeira execução cria um **novo notebook privado de teste**: `juniklx/nfsmw-automacao-smoke-pre100`. O notebook existente `juniklx/nfsmw` não é modificado.
- O smoke test apenas cria `/kaggle/working/NFSMW_PRE100_SMOKE_RESULTADO.json` e imprime um marcador. Não restaura snapshot, não usa Drive, não acessa chaves e não faz compilação.
- NÃO colocar uma solicitação de execução em `requests/` antes de confirmar a configuração do segredo.

## Autenticação uma única vez

1. Kaggle: `https://www.kaggle.com/settings/api` → gerar um token de API (formato atual de access token).
2. GitHub: `https://github.com/Juniklx/nfsmw-actions-teste/settings/secrets/actions` → New repository secret → nome `KAGGLE_API_TOKEN` → valor do token.
3. Informar ao ChatGPT apenas que o segredo foi configurado (nunca enviar o valor). O ChatGPT poderá publicar uma solicitação inofensiva no repositório.
4. O push da solicitação iniciará o workflow, que usa `kaggle kernels push`. Verificar resultado em GitHub Actions e no notebook privado de smoke test.

## Próximas etapas, depois do smoke test

Planejar notebook de trabalho e integração com Google Drive, restauração verificada do PRE99 e execução idempotente da PRE98. **Não** automatizar patches ou builds de release antes das verificações de integridade e controles de autorização. Preservar SHA-256 do certificado permanente, versionCode e backups originais.
