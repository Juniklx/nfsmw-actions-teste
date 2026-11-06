# NFSMW Android — PRE250: resgate da V37 e correção do envio ao Drive (2026-11-06)

## Diagnóstico do run original

- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42304603209
- Run `42304603209`: `completed/failure` no GitHub devido ao gate final `Require fully validated ...`. Não atribuir a falha à compilação do Android.
- Log final: `PRE170 stopped at UPLOAD_NEW_APK_TO_PRIVATE_DRIVE ResumableUploadError validation subphase APK_ALL_GATES_PASSED`.
- Relatório extraído do artifact `13547111581`: `gradle_release_succeeded=true`, `signed_apk_verified=true`, `drive_upload_success=false`, status `NAO_VALIDADO` originalmente porque exigia também upload ao Drive.
- O relatório confirma `versionCode=37`, pacote `io.github.nfsmwrecomp`, cert DER v2 SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, bibliotecas ARM64, assets PAL/USA preservados, marcadores PRE194/PRE246/PRE247 presentes.
- São **16 sondas passivas**: 8 stores dinheiro, 5 candidatos nitro, 3 candidatos Speedbreaker. `gameplay_cheats_enabled=false`. Sem leituras guest extras e sem reescrita dos stores.
- APK: 47.101.893 bytes; SHA-256 `96eed924c22c32e67af5977fc96c581e780472298e8e49da817a39496a51b852`; MD5 local `279620146e39d33c1d65bb109722e1bf`.
- Extração local de ZIP `13547111581`: ZIP do artifact e ZIP do APK passam teste de CRC; SHA do APK coincide integralmente com o relatório; `libmain.so` PAL SHA-256 `09264bac6460d12dbc55d7e95ed8b22d17460d6c9c98906ea8a74fd97e5c4ed0`; marcadores `NFSMW_PRE246_CHEATS_DIAG` e `NFSMW_PRE247_CHEATS_DIAG` encontrados.

## Resgate e persistência sem recompilação

- Upload **direto do APK** por conector Google Drive **sucesso**, ID `19EDaOuc3l8PtBg6F-2KhCo7HtVt9ftGi`:
  https://drive.google.com/file/d/19EDaOuc3l8PtBg6F-2KhCo7HtVt9ftGi/view
- Nome: `NFSMW_V37_PRE247_PASSIVE_DIAGNOSTIC.apk`; metadata do Drive confirmam 47.101.893 bytes na pasta `02_APKs` ID `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`. O SHA-256 foi validado no arquivo local antes do envio; a igualdade remota foi verificada por referência de origem e tamanho, **não por novo download completo do Drive**.
- ZIP de backup com o APK original e relatório JSON salvo com sucesso, ID `16CEuuFTCg-XECbzEyIm16FErt8I8hmOB`:
  https://drive.google.com/file/d/16CEuuFTCg-XECbzEyIm16FErt8I8hmOB/view
- Tamanho ZIP remoto confirmado 45.725.638 bytes. A V37 foi resgatada sem compilar novamente, sem reabrir ou alterar a chave, sem sobrescrever V35/V36 nem saves.
- Razão mais específica do `ResumableUploadError` não foi confirmada; não alegar que foi cota, autenticação ou rede.
- Automação horária de checagem do run desativada depois da conclusão e recuperação.

## Estado e próxima ação

- A **V37 está compilada, assinada e recuperada no Drive**, mas **ainda não foi instalada, aberta ou testada no Galaxy S24 FE**.
- Cheats não ativáveis nesta V37; é somente instrumentação passiva. Nenhum ganho de FPS, correção C3 ou funcionamento real de dinheiro/nitro/Speedbreaker comprovado.
- Instalar a V37 como atualização somente após garantir backup de saves, sem desinstalar versão que já use certificado permanente; confirmar touch e iPega PG-9076 e eventuais problemas gráficos. Em sessão controlada, coletar `nfsmw.log` e correlacionar marcadores PRE246/PRE247 com variação real dos recursos.
- Continuam preservados resolução interna 1920×1080, limite atual de 60 FPS, shaders, efeitos, física e proteções térmicas.
- Este adendo deve ser incorporado ao `CONTEXTO_NFSMW.md` canônico do Drive com backup antes de qualquer substituição. Versões anteriores que declaram V36 como última build são históricas e agora foram superadas pela V37 **compilada e validada**, não por teste no dispositivo.
