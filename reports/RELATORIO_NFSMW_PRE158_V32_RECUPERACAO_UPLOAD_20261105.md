# PRE158 — Recuperação da publicação da V32, sem recompilar

Data de registro: 2026-11-04 (Bahia), execução UTC em 2026-11-05.

## Evidência verificada

- GitHub PRE157 run `41954648085`: status final failure; entretanto Gradle exit 0, `gradle_release_succeeded=true`, `signed_apk_verified=true`, `pre157_callback_move_applied=true`, `verification_subphase=APK_ALL_GATES_PASSED`, versão 32.
- Erro de publicação PRE157: `ResumableUploadError`; o job de salvar o status ainda falhou em `git rebase` com alterações locais.
- GitHub PRE158 run `41957802293` baixou o mesmo artefato `13383197634`, validou-o e demonstrou `HTTP 403 insufficientPermissions` no upload via credenciais OAuth do GitHub. **Essa execução também terminou failure; ela não publicou a APK.**
- A APK já havia sido empacotada no artefato PRE157: 47.101.249 bytes, SHA-256 `47e983b7bd96308716d817dee555af787048932642f616ae237e746bc6cdb47b`, `io.github.nfsmwrecomp`, `versionCode=32`, certificado original permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Em recuperação via **conector Google Drive desta conversa**, upload da APK **teve sucesso** na pasta de APKs do projeto, ID `1tZX8aE0RJe6dXWLcZZ1BmAGguBoZN-GZ`. Após a publicação, o arquivo foi baixado novamente do Drive para a sandbox: 47.101.249 bytes, SHA-256 **igual** ao artefato PRE157, ZIP CRC íntegro e comparação byte a byte idêntica.
- Arquivo de preservação ZIP (APK + pre157-report.json) publicado no mesmo diretório: Drive ID `1PdIRWEoB-FTb3ns1qRHjdlaPSBrj7Pby`, 45.717.121 bytes.
- A APK V31 não foi modificada; a compilação de recuperação não gerou nova assinatura nem acessou senhas.
- **Ainda não testado no Galaxy S24 FE:** instalação/atualização da V32, gameplay, touch, iPega PG-9076, qualidade gráfica e FPS. Nenhum ganho comprovado.

## Próximo passo

Testar **V32** no S24 FE como atualização normal da V31 (sem desinstalar), preservando dados e opções 1920×1080/120 FPS; primeiro abrir jogo/controles e confirmar que nenhuma regressão visual ocorreu. Comparar desempenho depois contra os logs da V31. As credenciais OAuth do GitHub precisam de autorização de escrita no Drive antes de voltar a usar upload direto no Actions; **não alterar a chave de assinatura**.
