# PRE405 — V46 Nitro global: APK assinada, hash e publicação verificados (2026-11-08)

## Evidência verificada
- Workflow GitHub Actions [42439306990](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42439306990) concluiu `completed/success`; etapa de build e gate de assinatura concluíram `success`.
- Artifact `13601234697` contém `pre401-v46-report.json` e `nfsmw-v46-global-nitro-all-cars-verified.apk`; ZIP do artifact com CRC OK.
- APK obtida desse artifact: `NFSMW_V46_PRE401_GLOBAL_NITRO_FULL_ALL_CARS.apk`, **47.105.541 bytes**, SHA-256 **`ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`** calculado localmente. ZIP da APK íntegro, 872 entradas.
- Pacote `io.github.nfsmwrecomp`, `versionCode=46`; `apk_validation.signed_certificate_sha256_match=true`, `signed_schemes_verified=true` no relatório. Certificado v2 SHA-256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`** corresponde ao certificado permanente; não houve recriação de chave.
- `lib/arm64-v8a/libmain.so` contém `NFSMW_PRE398_GLOBAL_NITRO_FULL`, `NFSMW_PRE348_NITRO_SLOT_VALUES` e `NFSMW_PRE383_NITRO_CALLSITE`; `lib/arm64-v8a/librexruntime.so` contém `NFSMW_PRE364_XINPUT_USER0`. Outras bibliotecas obrigatórias e assets PAL/USA passaram pelo gate.
- Google Drive APK ID **`1UEmKsia6yhGBleO9eCFkeLbRz54myj4M`**, URL https://drive.google.com/file/d/1UEmKsia6yhGBleO9eCFkeLbRz54myj4M/view ; metadados Drive conferidos: nome correto, **47.105.541 bytes** e pasta `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`. Relatório do upload registra `remote_md5_matches=true` e `folder_verified=true`.

## O que a V46 altera e não altera
- Aplicação da PRE398 em cima do builder PRE390: nos 5 stores da função Nitro `sub_82424AF0` para `r31+252`, substitui o valor de saída por float32 **1,0**, bits `0x3F800000u`, sem mudar endereço ou quantidade de stores, sem filtro player-only, LR ou slot. PRE399 validou fonte, reversibilidade e outros stores inalterados. **Cheat global está compilado/assinado na APK**, mas **efeito no jogo ainda não comprovado**.
- Usuário autorizou explicitamente que adversários recebam Nitro infinito. A alteração não autoriza outros cheats, e Speedbreaker/dinheiro não tiveram seus stores de jogo alterados.
- Instrumentação anterior PRE316/PRE336/PRE348/PRE364/PRE383 preservada; resolução 1920×1080, shaders, física, suporte touch/PG-9076 e proteções térmicas devem ser preservados.

## Estado da validação
- **Comprovado:** build ARM64, APK de versão 46, assinatura permanente, hash, integridade ZIP e upload no Drive.
- **Não comprovado:** instalação da V46 no Galaxy S24 FE, abertura do jogo, medidor de Nitro permanecer 100% ao segurar o botão, Nitro ativo para adversários, estabilidade em transição de modos ou qualquer ganho de FPS. Não confundir `cheat_enabled=true` no staging com experiência funcional testada.

## Próximo teste
1. Guardar backup independente do save `MARCEK` e V45 como fallback; instalar V46 **sobre V45, sem desinstalar ou limpar dados**, dado package e certificado idênticos.
2. Dirigir sozinho e **segurar Nitro por um período que normalmente esgotaria a barra**, observando medidor e efeito prático da aceleração. Soltar e repetir.
3. Iniciar corrida com IA; observar Nitro do próprio carro, funcionamento do jogo e qualquer regressão. O Nitro dos adversários é difícil de comprovar apenas pela interface; inspecionar logs PRE398 e PRE348 por slot.
4. Fechar jogo normalmente, enviar novo `nfsmw.log`, separar sessão V46 dos prefixos históricos. Checar `PRE398_GLOBAL_NITRO_FULL`, `PRE348_NITRO_SLOT_VALUES`, C3, crashes.
5. Se crash ou regressão, retornar à V45 sem desinstalar e preservar logs/saves.

Ressalva: o objetivo de 120 FPS não foi demonstrado nas versões anteriores, cujos logs registraram cap 60; a V46 trata Nitro, não FPS.
