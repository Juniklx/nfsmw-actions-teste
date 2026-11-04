# NFSMW — PRE126B falhou no certificado do APK; PRE126C em execução (2026-11-04)

## Resultado real da PRE126B

- GitHub Actions [41841914257](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41841914257) terminou com `conclusion=failure`.
- Relatório com `run_id=41841914257`, `phase=SELECT_APK_AND_VERIFY`, `verification_subphase=APK_SIGNER_CERTIFICATE_FINGERPRINT`, `validation_failure_code=APK permanent signing certificate mismatch`.
- Gradle `assembleRelease` compilou com `exit_code=0`; a APK provisória tinha 47.068.029 bytes e SHA-256 `acff72fea66a8164dd0a65706efbde5e09dc292a0a1825f06fc4b8b36f6a4225`.
- `signed_apk_verified=false`, `drive_upload_success=false`. **Não instalar, distribuir ou tratar essa APK provisória como validada.** O pacote provisório não foi enviado ao Google Drive.
- O backup PRE99, a PRE117 exata, o certificado da chave do Drive e a V26 de referência passaram antes desse bloqueio. A divergência relatada pelo `apksigner` pode ser de formatação/extração textual ou uma assinatura efetivamente diferente; **isso ainda não foi determinado**. Não retirar a exigência de certificar o APK.

## PRE127 — verificação independente de assinatura APK v2

- Criado `automation/kaggle/pre127_apk_v2_certificate_audit.py` no GitHub privado. Usa apenas biblioteca padrão Python, consulta a assinatura v2 do APK, extrai exatamente um certificado DER e calcula seu SHA-256.
- **Teste executado localmente** na APK original `NFSMW_V26_PAL_USA_PRE96_VISUAL_EXPERIMENTAL.apk` (Drive ID `1HcWA8UFugXNO4IPPH8kgUcX5CwP4UobW`): retornou certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. A função rejeita assinaturas v2 ausentes, signatários múltiplos ou blocos malformados.
- Essa leitura não substitui `apksigner verify`; a PRE126C **continua exigindo a validação criptográfica original pelo apksigner** e o certificado permanente exato.

## PRE126C — recompilação controlada

- Código `automation/kaggle/pre126_build_signed_v27_pal_usa.py` atualizado, importando o verificador PRE127.
- Inclui a própria V26 como fixture: certificado APK v2 precisa corresponder ao permanente antes de começar a compilação.
- Na APK V27 nova, `apksigner verify --verbose --print-certs` precisa passar; o certificado v2 extraído precisa corresponder a `1ba7...d104b`; se o CLI fornecer digest incompatível com o DER, a build é bloqueada. As impressões digitais públicas e a etapa exata ficam no relatório sanitizado.
- **Nenhuma regra de release foi desabilitada**: `versionCode=27`, pacote `io.github.nfsmwrecomp`, todas as 10 bibliotecas ARM64, `libmain_usa.so` e shaders PAL/USA preservados, runtime recompilado diferente de V26, assinatura permanente.
- Solicitada execução [PRE126C #41847601544](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41847601544), acionada pelo arquivo `automation/kaggle/build_pre126_requests/PRE126C_APK_V2_SIGNATURE_20261104.json`, commit `f558893e7e4ab32a5870b6ec243e6f53f23e9222`.
- Relatório de fonte de verdade: `automation/kaggle/status/pre126_v27_signed_release.json`, exigir **`run_id=41847601544`**, pois é sobrescrito por execuções subsequentes.
- A PRE126C estava `in_progress` durante a elaboração deste documento. **Não há sucesso, upload ou APK V27 aprovado ainda confirmado.**
- O acompanhamento automático existente foi atualizado para continuar pela PRE126C; nenhum passo do usuário é necessário enquanto ela executa.

## Preservação e teste

- V26, PRE99, notebook Kaggle, chave permanente `.p12`, credenciais privadas, contador do Drive, fotos e outros backups não foram alterados pelo diagnóstico.
- Não declarar ganho de FPS/ajuste gráfico realizado; PRE117 visa exclusivamente o scroll aninhado de Settings.
- Somente após APK aprovada e upload confirmado: instalação no Galaxy S24 FE e teste manual Settings fora de DeX e em DeX, toque, PG-9076, CVARs extremos e `SAVE SETTINGS`.
