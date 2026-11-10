# PRE683 — Auditoria nativa de flags gráficas V51 (2026-11-10)

## Evidências executadas

- Repositório GitHub público: `Juniklx/nfsmw-actions-teste`.
- Workflow `.github/workflows/nfsmw-pre683-v51-native-graphics-observability.yml`; solicitação via commit `5e8096926ed0dd49843c19c48e4e81cec08817b1`.
- GitHub Actions run **42913355889**, job **130169400098**: `completed / success`; inclusive etapa de upload e readback no Drive privado. https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42913355889
- Relatório privado `NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE683_V51_NATIVE_GRAPHICS_20261110_221942.zip`, Google Drive ID `1Xbpc7krliit4xke9ZFcltfN3117hMK0V`, tamanho **1532 bytes**, SHA256 `1c582777c12716d34947c66f26cc8dcfce2189263e1704f941ca6a8ba0efab0f`. Contém `PRE683_REPORT.json` e `PRE683_SUMMARY.md`; ZIP CRC validado diretamente.
- APK V51 PRE652 de entrada: Drive ID `1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws`, 47.104.417 bytes SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`, ZIP CRC integral aprovado.
- `lib/arm64-v8a/libmain.so` 41.772.192 bytes SHA256 `190b0c01f94b6a27f39a2f52a5ad63523ee8e158dd740e182e63a6f8905d234c`.
- `lib/arm64-v8a/libmain_usa.so` 41.749.696 bytes SHA256 `4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83`.
- `classes.dex` SHA256 `be3c0393307d5e0128eab4f0f590e44fc480581c4eedfc537c58fc58414cb689`.

## Resultado técnico delimitado

As duas bibliotecas ARM64 contêm os cinco nomes:
`nfsmw_nativo_sin_desenfoque`, `nfsmw_nativo_pcf_barato`, `nfsmw_sombras_sin_vegetacion`, `nfsmw_nativo_sombras_escala`, `nfsmw_sombras_corte`.

O DEX assinado contém os argumentos equivalentes com `--` e `=`. Esses resultados demonstram **referências estáticas** nos binários, não que as flags estão ativas com certos valores.

O log original PRE656 foi conferido por SHA256 `649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7`. Mostra resolução interna 1920x1080 e cap 60, mas **não registra valores explícitos dessas cinco opções**. A medição agregada `C2: 320 (cubo y desenfoque)` não comprova que o desfoque radial esteja ligado, pois agrupa operações.

A screenshot enviada pelo usuário antes de jogar mostra configurações fortes (Vulkan, sombras Xbox 360 / Ultra / Longe, desfoque ligado, reflexos altos, 16x anisotrópico), mas não equivale ao estado interno real de cvars.

## Próxima etapa PRE684 — medição mínima e reversível, sem promessa de otimização

1. Autenticar a **receita exata da V51**: PRE99 + PRE431/PRE638 + PRE648 + correções PRE654/PRE652. O ZIP `NFSMW-Recompiled-Mobile-main.zip` de 21MB é histórico e não representa sozinho o fonte exato da V51. Conferir hashes, marcadores, backups e saída ARM64; não reaplicar patches cegamente.
2. Planejar instrumentação de leitura: registrar **somente** os cinco valores gráficos relevantes na inicialização, primeiro na camada Java `MotorNativo.argumentos` / `GameActivity`, depois no motor nativo após o parse e no primeiro frame; preservar todas as cvars e comandos Vulkan, sem logar ISO, caminhos privados, saves ou credenciais.
3. Validar impacto zero funcional com preflight + teste de host/compilação ARM64 sem APK; decidir se build diagnóstica é necessária.
4. Se houver nova build, usar unicamente certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, package `io.github.nfsmwrecomp` e versionCode **superior a 51**; preservar V51 e demais APKs. Nada de assinatura debug.
5. Confirmar no Galaxy S24 FE via log; depois avaliar trabalho redundante de shader/pipeline sem desligar 1080p, sombras, blur, reflexos, física ou mecanismos térmicos. Resultado ainda não comprova melhoria FPS.

## Pendência documental

A sincronização anterior do contexto canônico `NFSMW_Android/CONTEXTO_NFSMW.md` foi solicitada via Actions, mas ainda não possui readback confirmado. Não declarar atualização realizada até verificar o arquivo original. Este registro GitHub é um adendo separado.

STATUS: `PRE683_GITHUB_ACTIONS_PASS`; `NATIVE_FLAGS_PRESENT`; `LIVE_CVARS_UNKNOWN`; `NO_NEW_APK`; `NO_FPS_GAIN`.
