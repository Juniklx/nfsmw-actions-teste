# PRE697 — V51 VulkanPresenter / BucleVblank: auditoria de delta somente leitura

**Status 2026-11-11:** workflow de auditoria CRIADO; **execução e resultado ainda NÃO confirmados**. Nenhuma correção funcional ou APK V52 autorizada.

## Base verificável

- [PRE696 autenticada, run 43100424122](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43100424122): `completed/success`; `PASS_AUTHENTICATED_RECIPE_ONLY`, 7 fontes, replay PRE99/V50/V51 validado por hashes.
- [Contexto canônico no Drive](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view): adendo PRE696 FINAL preservado.
- O replay **não prova** identidade byte a byte com a `libmain.so` assinada.
- PRE694/PRE695: intervalos `actualPresent` próximos de 8/25ms apesar de `desiredPresent` estável em torno de 16,67ms. Causalidade não estabelecida.

## Escopo estrito

[Workflow PRE697](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre697-v51-presenter-vblank-delta-readonly.yml), commit `0c22d21433d9b427ea26336b8dbdf30873d2834a`.

A auditoria exige os hashes PRE99, replay V50 + patch PRE648 somente em memória e ZIP histórico autenticado por SHA256, antes de comparar:

1. `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp`: histórico `eada548b2f683707a14ab8e6dd2c49b0381ac6542e901413fc94e5801fba74d5`, receita V51 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`.
2. `nativo/app/src/nfsmw_nativo_sistema.cpp`: histórico `23c772caca92c639ca7a479eb118d623ba29910b8504c98c56a5ce969d339338`, receita V51 `b8bc3f3cfbd9e53755387cdb3aca61961093873bb995dea8648a753920d09be2`.

O relatório registra apenas hashes, número e tipos de hunks, números de linha e presença de identificadores relevantes. Não publica conteúdo de fonte, ROM/ISO, logs privados, credenciais ou dados do dispositivo. Se faltar qualquer arquivo/pin, o gate deve falhar fechado.

## Critério de conclusão

Consultar novo run real, exigir `completed/success`, checar `PRE697_STATUS=PASS_AUTHENTICATED_RECIPE_AND_SOURCE_DELTA_ONLY`, `PRE697_DELTA_FILES=2`, validar JSON/CRC e comparar hunks. Não atribuir a discrepância de pacing à alteração lexical sem análise temporal e medição de fase.

**Sem alteração:** V51 `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, efeitos/shaders/física, touch/iPega PG-9076, saves e limites térmicos.

**Próxima investigação após PASS:** avaliar pontos mínimos e não invasivos para traço temporal sincronizado `guest vblank → vkQueuePresentKHR/frame ready → SurfaceFlinger actualPresent`; nenhuma proposta de otimização ou FPS melhorado foi comprovada.


---

## Resultado final verificado — PRE697 (11/11/2026)

A execução GitHub Actions [43102881692](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43102881692), job `130798583689`, terminou `completed/success`; log: `PRE697_STATUS=PASS_AUTHENTICATED_RECIPE_AND_SOURCE_DELTA_ONLY`, `PRE697_SOURCE_FILES=7`, `PRE697_DELTA_FILES=2`, `PRE697_DELTA_HUNKS=2`, `PRE697_SOURCE_TO_SIGNED_ELF_EQUIVALENCE=false`, `PRE697_FPS_GAIN_PROVEN=false`.

O ZIP do artifact GitHub `13893221148` contém JSON e Markdown, 3.575 bytes, SHA256 `50a25898c3c89383adced519af23910dea54557738d17970390fc657a4df9fdd`; CRC ZIP `PASS`. Cópia privada no Drive: [NFSMW_PRE697_V51_SOURCE_DELTA_43102881692.zip](https://drive.google.com/file/d/1lqiHSz41Ig2Urtr7FWlG6116pozl2Ytn/view), pasta `06_Logs_e_Medicoes`; download de volta teve mesmo tamanho, SHA256 e CRC.

Resultado autenticado dos dois arquivos:

| Fonte | Diff contra histórico | Posição na V51 | Identificadores de pacing nos blocos |
|---|---|---|---|
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | 1 linha substituída | 122 | nenhum dos 12 pesquisados |
| `nativo/app/src/nfsmw_nativo_sistema.cpp` | 6 linhas inseridas | 33–38 | nenhum dos 12 pesquisados |

Os arquivos têm o fingerprint esperado da receita V51. Isso é uma **comparação lexical**, não prova equivalência funcional nem que o delta cause ou exclua a oscilação 8↔25ms. O código exato alterado não foi exportado; nenhuma instrumentação temporal foi feita nesta etapa. A cadência irregular de `actualPresent` persiste como hipótese de investigação; ainda faltam correlação de frames e timestamps sincronizados entre motor/queue/fence/SurfaceFlinger.

**Próximo gate proposto (não executado): PRE698 — verificar a viabilidade e preparar protocolo de medição temporal read-only**, priorizando ferramentas e coletores já validados em PRE690/PRE694 e Perfetto FrameTimeline quando disponível; não mudar `MAILBOX`, FPS cap, gráficos, shader, efeitos, física, input/touch/PG-9076, save, driver, credenciais, APK, assinatura ou limites térmicos. Requer medir antes de sugerir alteração funcional.

**Estado final:** PRE697_SOURCE_DELTA_AUDIT_PASS; TWO_CHANGED_HUNKS_AUDITED; ZERO_MONITORED_PACING_TERMS_IN_DIFF; ZIP_SHA_CRC_AND_DRIVE_READBACK_PASS; NO_CAUSAL_ATTRIBUTION; NO_APK_V52; NO_SOURCE_PATCH; NO_FPS_GAIN_PROVEN.
