# PRE370 — Falha da V44 PRE367 e correção do verificador XInput (2026-11-07)

## Evidência verificada da run com erro
- Execução GitHub Actions [42426649208](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42426649208), job `128566254456`, `completed/failure`.
- Artefato privado `13596935552`: apenas `pre367-v44-report.json`, **sem APK verificada**.
- Relatório: `gradle_release_exit_code=0`, `gradle_release_succeeded=true`, APK candidata 47.104.773 bytes e SHA-256 `c16c1fe2dda71743e714c41376684837aecc28a61cdf39e83f6f2653525def51`; **isso não é release aprovada**.
- Certificado v2 da APK candidata bateu com certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, mas `signed_apk_verified=false` porque o gate final parou em `verification_subphase=APK_PRE194_C3_PAL_MAIN_BINARY_MARKER`, `error_type=ValueError`.
- Marcadores anteriores Nitro PRE316/PRE336/PRE348 foram confirmados no `libmain.so`; gate PRE367 tentava exigir marcador da instrumentação XInput PRE364 **nesse mesmo PAL ELF**.
- A instrumentação PRE364 foi feita em `nativo/sdk/src/input/input_system.cpp`, que pertence ao runtime host. Portanto a hipótese causal forte é **verificador exigindo marcador da biblioteca errada**. Essa hipótese requer resultado da run corrigida para confirmação.

## Correção e nova compilação
- Commit `ee9a34b879926eb1f305862c0a3a2e99eca6a8e2`: `automation/kaggle/pre367_build_signed_v44_nitro_input_correlation_passive.py` agora procura `NFSMW_PRE364_XINPUT_USER0` dentro de `lib/arm64-v8a/librexruntime.so`, em dois gates. Também exige ELF válido. Continua verificando marcadores PAL PRE316/PRE336/PRE348 em `libmain.so`.
- Nenhum patch de jogo alterado pela correção; mudanças restritas à localização dos bytes de verificação na APK.
- Retry acionado pelo commit `1b7b9504ebf0596ec2f632c6bf2ace7ebd600545`: [run 42429087936](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42429087936), job `128573735742`.
- **Na consulta inicial desta documentação:** retry `in_progress`, ainda não havia APK V44 aprovada. Confirmar gates, artefato, SHA-256, certificado e upload/readback do Drive antes de recomendar instalação.
- V43 segue versão diagnóstica instalada/testada. `versionCode 44`, mesmo pacote `io.github.nfsmwrecomp` e chave permanente; save `MARCEK` intocado, sem cheats funcionais, gráficos/física/limites térmicos preservados.

## Próximo passo
Inspecionar conclusão do job `42429087936` e recuperar seu JSON de verificação. Só promover V44 a release validada após assinatura, marcadores PAL e runtime e upload ao Drive confirmados.
