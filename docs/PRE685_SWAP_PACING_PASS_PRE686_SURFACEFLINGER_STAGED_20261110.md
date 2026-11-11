# PRE685 — fluidez dos Swaps V51; PRE686 — coleta de apresentacao preparada

Data de referencia: 2026-11-10 (Bahia; artefatos UTC 2026-11-11).

## PRE685: verificado (nenhuma APK)

- GitHub Actions auditoria: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42939712263
  - Run `42939712263`, job `130258342439`, `completed/success`.
- Arquivo de relatorio privado no Drive: `NFSMW_PRE685_V51_SWAP_PACING_20261111_013251.zip`, file ID `1DXBieBfXNtcN1JsOqI2BrT43b2rUISke`, tamanho `3026` bytes, SHA256 `038bdcb72df154691c3a3d747d413e13f800d11cf64c1cf43a3e9619718278ae`. ZIP CRC PASS. JSON, CSV e README.
- Input verificado: log real PRE656 V51, tamanho `576129`, SHA256 `649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7`.
- Histogramas **internos C2 entre Swaps**, 7 janelas coerentes com deltas do contador `presentados`.
- Nas 5 ultimas janelas: `6002` intervalos, `5784` em 15–18ms (96,368%), `162` em 18–25ms, `56` abaixo de 15ms, `0` acima de 25ms.
- Nas 2 ultimas janelas inteiramente em jogabilidade (carro parado): `2401` intervalos, `2314` em 15–18ms, `64` em 18–25ms, `23` abaixo de 15ms, `0` acima de 25ms; estimados 59,994 e 59,999 FPS pelos contadores cumulativos.
- Nas 2 primeiras janelas, incluindo menus/carregamentos/transicoes, houve 8 e 5 intervalos acima de 25ms, com pior quadro de 99,9ms e 109,8ms.
- Log mostra 1920x1080 internos, cap 60, Vulkan MAILBOX, quatro imagens solicitadas e mensagem `vsync implicito no`. Nao equivale a timestamps reais de composicao do Android.

## Sincronizacao canônica: verificada

- GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42940265729 , job `130260121291`, `completed/success`.
- Arquivo original `NFSMW_Android/CONTEXTO_NFSMW.md`, Drive ID `1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB`, alterado in-place, final `1136230` bytes, SHA256 `ece8bc86c700df98ef4adbb53be49c87a363d2ef0a924b8c231e29c85a71cb79` (verificado em leitura separada).
- Backup privado identico antes da mudanca, ID `1QxGq0kqiJnaMaKgERZgMO3JaMifNGEAB`.
- Recibo privado de readback: `NFSMW_PRE685_CONTEXT_SYNC_20261111_013729.json`, ID `1NXRZycasTqE87waBiCRhiERbskgLwuPF`, PASS.

## PRE686: ferramenta preparada, sem teste real no aparelho

- Script publico `automation/termux/nfsmw_pre686_surfaceflinger_timestats.sh`.
- Usa o Shizuku/rish ja preparado pelo usuario; modos `start`, `stop`, `abort`. O `start` limpa e habilita **temporariamente contadores globais de medicao do SurfaceFlinger**; o `stop` filtra somente a camada NFSMW da saida e desabilita os contadores. Nao modifica clocks, termica, APK nem jogo.
- Fonte oficial: https://developer.android.com/topic/performance/issues/slow-session ; `dumpsys SurfaceFlinger --timestats` fornece FPS e histograma present-to-present **da camada apresentada**, distinto dos contadores internos do motor.
- Validado apenas `bash -n` e teste sintetico local de filtragem para excluir outras camadas. **Nao testado no S24 FE.** Samsung Android pode negar/alterar o suporte de `dumpsys`; se nenhum layer NFSMW aparecer, nao assumir sucesso e nao fabricar FPS.
- Para uma amostra real, usuario precisa executar a coleta no aparelho e fornecer o TXT filtrado e o `nfsmw.log` gerado na mesma sessao. GitHub Actions nao acessa o dispositivo a distancia.

Identidade V51 PRE652 e certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` inalterados. Nenhum ganho FPS comprovado. Cvars efetivas de desfoque/sombras ainda nao medidas.
