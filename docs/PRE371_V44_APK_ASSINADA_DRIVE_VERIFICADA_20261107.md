# PRE371 — V44 PRE370 corrigida, assinada e publicada (2026-11-07)

## Resultado verificado
- Retry GitHub Actions **42429087936**, job **128573735742**, status `completed/success`.
- Artefato **13597024385**, com `pre367-v44-report.json` e `nfsmw-v44-nitro-input-correlation-verified.apk`.
- Relatório `status=PRE367_V44_PASSIVE_NITRO_INPUT_CORRELATION_SIGNED_VERIFIED_ARTIFACT`, `phase=COMPLETE`, `gradle_release_succeeded=true`, `signed_apk_verified=true`, `drive_upload_success=true`.
- APK: `NFSMW_V44_PRE367_NITRO_INPUT_CORRELATION_PASSIVE.apk`, pacote `io.github.nfsmwrecomp`, **versionCode 44**, tamanho **47.104.689 bytes**, SHA-256 **`f8026ead836c26446ddb7d2034c2239bcfecf78272cfb528ac780d12907dd6f0`** calculado independentemente no ZIP GitHub extraído.
- Verificação local: `ZipFile.testzip() == None` (CRC de todos entries íntegro); `NFSMW_PRE364_XINPUT_USER0` encontrado em `lib/arm64-v8a/librexruntime.so`, `NFSMW_PRE348_NITRO_SLOT_VALUES` encontrado em `lib/arm64-v8a/libmain.so`.
- Certificado APK v2 permanente comparado no relatório SHA-256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, sem mudança de keystore.
- PRE316, PRE336, PRE348 confirmados em `libmain.so`; PRE364 confirmada em `librexruntime.so`. Dez bibliotecas ARM64 presentes, assets PAL/USA preservados.
- Drive APK ID `13Pd3-Q1nMp7gfyjlgGtxszbErQJc6Jpn`, URL https://drive.google.com/file/d/13Pd3-Q1nMp7gfyjlgGtxszbErQJc6Jpn/view ; leitura de metadados Google Drive confirmou nome, 47.104.689 bytes e pasta `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`. Relatório da rotina de upload contém `remote_md5_matches=true` e `folder_verified=true`.
- Run original com falha `42426649208`: gerou APK candidata, mas verifier exigia marcador host em `libmain.so`. Commit de correção `ee9a34b879926eb1f305862c0a3a2e99eca6a8e2` passou a verificar `librexruntime.so`, sem alterar a sonda nem a lógica Nitro.

## Limitações e próximo teste
- **Comprovado:** APK V44 compilada, permanentemente assinada, verificada, publicada no Drive. **Não comprovado:** instalação da V44 no Galaxy S24 FE, abertura, produção de logs de XInput PRE364, identificação player-car, desempenho ou Nitro infinito.
- V44 é diagnóstico passivo para correlacionar transições do usuário 0 com checkpoint PRE348 por slot. `owner_verified=false`, `nitro_button_verified=false`, `cheats_enabled=false`; não presumir que o slot 1 é o jogador nem mapear botão Nitro sem teste.
- Backup separado do save `MARCEK` antes de instalar **sobre** V43, sem desinstalar ou apagar dados; manter V43 e V42 como fallback. Testar exploração livre, apertar/soltar Nitro em janelas conhecidas, depois corrida com IA; enviar novo `nfsmw.log`. Comparar timestamps PRE364, PRE348, PRE336. Não tratar correlação temporal como prova independente exclusiva.
- Conservar pacote, assinatura permanente, controles touch/PG-9076, resolução 1920×1080, shaders, física, limite térmico. FPS objetivo 120, mas sem alegação de ganho.
