# PRE328 — Readback autônomo dos relatórios GitHub Actions (2026-11-07)

## Bloqueio operacional identificado
O conector GitHub permite `fetch_file`/commits e leitura de logs mediante run ID, mas as chamadas disponíveis nesta conversa **não forneceram a listagem dos run IDs**. As PRE325, PRE325B, PRE326 e PRE327 foram publicadas, porém a execução e seus relatórios não estavam comprovados somente por commits de trigger. Buscar PRE325/PRE327 no Drive também não localizou relatórios específicos.

## Modificação aplicada (apenas CI)
- Script `automation/kaggle/pre328_publish_sanitized_audit_status.py`: transforma relatórios JSON das auditorias em **resumos estritamente allowlisted**, publicáveis via GitHub Contents API e token temporário do próprio GitHub Actions.
- Teste sintético `automation/kaggle/pre328_publish_sanitized_audit_status_mock.py` e workflow `.github/workflows/nfsmw-pre328-sanitized-status-privacy-mock.yml`, execução ainda não verificada.
- Workflows PRE325 e PRE327 atualizados para permissão `contents: write` somente no job e etapa `if: always()` de publicação do resumo. Não altera código do jogo, PRE99, APK, chave, save ou gráficos.
- Trigger PRE325 com status: `2aa0a616f45ccdfe9222e301c82233e5d673b8d7`.
- Trigger PRE327 com status: `525684c190821e514e79b731fe78a40c332cabb4`.
- Destinos previstos para o readback:
  - `docs/generated/PRE328_PRE325_SANITIZED_STATUS.json`
  - `docs/generated/PRE328_PRE327_SANITIZED_STATUS.json`
- Em consulta após os triggers, **ambos ainda retornavam 404** pelo conector GitHub; isso **não prova falha do workflow**, apenas ausência dos arquivos no instante da consulta.

## Dados que não são publicados
Sem tokens OAuth, certificados, senhas, nomes dos arquivos escaneados, trechos de código, endereços guest, conteúdo de logs, nomes de usuário, raw hits ou exceptions. O resumo é feito de status, contagens, indicadores booleanos e metadados da execução.

## Segurança da interpretação
- `AUDIT_OK` significa que a auditoria estrutural interna concluiu, não que owner do Nitro seja o jogador.
- `NO_REPORT` significa ausência do JSON previsto, não sucesso da varredura.
- PRE327 pode terminar `AUDIT_OK` mesmo se nenhum arquivo binário candidato estiver no snapshot; checar `files_inspected` e `bytes_inspected` antes de qualquer conclusão.
- A V41 no Galaxy S24 FE segue como referência de runtime do ciclo Nitro. Nitro infinito permanece desativado; nenhuma V42 foi criada.
- Próximo gate: ler os arquivos de status quando aparecerem. Se permanecerem ausentes, verificar a execução e o erro real no GitHub Actions antes de adicionar novos scans.
