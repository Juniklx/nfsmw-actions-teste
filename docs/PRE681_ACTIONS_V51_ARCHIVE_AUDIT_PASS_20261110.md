# PRE681 — execução confirmada do GitHub Actions público (2026-11-10)

## Execução verificada

- Repositório: `Juniklx/nfsmw-actions-teste` (público).
- Workflow: `.github/workflows/nfsmw-pre681-v51-graphics-readonly.yml`.
- Solicitação de execução: commit `b71086808caa3c363128d53c15f755c57b1b6ab5`.
- GitHub Actions run: **42902067651**, job: **130130329684**, `completed/success`. URL: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42902067651 .
- Logs do job consultados diretamente, encerrando:
  - `PRE681_CODE_COMPILES=TRUE`
  - `PRE681_ACTIONS_V51_ARCHIVE_AUDIT=PASS`
  - `PRE681_DRIVE_PRIVATE_UPLOAD_READBACK=PASS`
  - `PRE681_DEVICE_GRAPHICS_SETTINGS=UNKNOWN`
  - `PRE681_APK_PATCH_OR_FPS_GAIN=NONE`
- O workflow verificou presença e uso das três variáveis `GOOGLE_REFRESH_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` pelo resultado da execução; seus **valores não foram lidos ou revelados** nesta auditoria.

## Artefato privado conferido

- Caminho: `NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE681_ACTIONS_V51_READONLY_20261110_211026.zip`.
- Google Drive file ID: `1QJEGzudsBiGqe5Q0cDleA1KwFGNm9xqK` (arquivo `shared=false` na consulta).
- Tamanho: **1465 bytes**. SHA-256: **6a05da090a40c93efc529d167d526155a2bbacd94bbd5cd379a677f16e80c470**.
- ZIP CRC: **PASS**. Conteúdo: `PRE681_REPORT.json` e `PRE681_README.md`.
- `PRE681_REPORT.json` confirma hashes/tamanhos dos insumos APK V51, snapshot-fonte arquivado e log PRE656, CRC APK, TOML de 121 chaves, igualdade exata do TOML APK/fonte, 4 âncoras em Ajustes.java, 6 em MotorNativo.java e marcadores DEX presentes.
- Sessão PRE656: **1920×1080 interna, limite 60 FPS**, modo de saída 1280×720/60 Hz.
- Defaults da APK V51 incluem `nfsmw_nativo_sin_desenfoque=true`, `nfsmw_nativo_pcf_barato=true` e `nfsmw_sombras_sin_vegetacion=true`. Não demonstram as preferências efetivas no S24 FE.

## Limites e sequência segura

- Este PASS é **auditoria de APK/fonte/log arquivados**, não acesso às preferências privadas do celular. Não prova gráficos completos, FPS melhorado, nem equivalência visual, e não constitui build Android nova.
- Nenhum patch/recompilação, mudança de assinatura, versionCode, controles, shaders ou efeitos. V51 PRE652 permanece release de referência, certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Como o repositório antigo foi tornado público, revisar os **artefatos de APK históricos** ainda acessíveis e antigos workflows com acesso a Secrets antes de ampliar a automação.
- Próximo gate real: obter dados de preferências do aparelho de forma autorizada ou evidência visual suficiente para determinar blur/sombras realmente ativos, preservando dados pessoais e saves; somente depois planejar mudança gráfica.
- **Pendência documental:** acrescentar este adendo ao `CONTEXTO_NFSMW.md` canônico no Drive (mantendo backup e ID). Este registro GitHub não substitui aquela atualização.
