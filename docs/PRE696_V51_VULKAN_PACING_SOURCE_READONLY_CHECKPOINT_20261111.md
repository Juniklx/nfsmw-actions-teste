# PRE696 — Fonte Vulkan / Vblank e frame pacing da V51

**Status em 2026-11-11: auditoria exploratória local PASS; autenticação remota da cadeia V51 QUEUED.** Esta não é uma recompilação nem uma alteração de APK.

## Evidência e separação de escopos

- A PRE694 foi concluída com três sessões reais Samsung A1 → RADV B → Samsung A2 no Galaxy S24 FE, V51 cap 60 e 1920x1080. A PRE695 reprocessou desired/ready/actual: a cadência desejada foi quase sempre 16,67ms, mas houve oscilação real 8/25ms no actualPresent. Causa não demonstrada.
- O ZIP histórico `NFSMW-Recompiled-Mobile-main.zip` (21.026.481 bytes, SHA256 `0ab7c949e62d377f444fb7b2489bc66d6387bd49b1798f184c4a953314064231`) foi inspecionado localmente, com CRC PASS, mas **não é a receita compilada da V51**.
- Auditoria Python local leu sete fontes C++/Java, localizou 11 âncoras obrigatórias e passou teste negativo/fail-closed. Arquivos preliminares, incluindo o analisador reproduzível, preservados em [ZIP privado Drive](https://drive.google.com/file/d/1XRqfX37hh7mnLi-jtha-6UEXDp-wHmlS/view). SHA256 do ZIP: `476effaef1ad86f1459a2850181a57acf14dd83c5b1311737856de3808b5cd50`; CRC e readback bit a bit PASS.
- No snapshot histórico, `nativo/app/src/nfsmw_nativo_destinos.cpp` tem SHA256 `b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385`, que coincide com pin de fonte autenticada anterior PRE665/PRE677 para **esse arquivo**, não para toda a árvore.
- Mecanismos encontrados historicamente: `BucleVblank()` lê `VdQueryVideoMode` e produz interrupções guest; `nfsmw_limite_fps` informa `video_mode_refresh_rate`; VulkanPresenter seleciona MAILBOX quando habilitado e suportado, usa `vkQueuePresentKHR`, aquisição antecipada `vkAcquireNextImageKHR` e fila de submissões. Isso identifica **candidatos**, não causa/latência medida.

## Gate PRE696 V51 autenticado (pendente)

- [Workflow PRE696](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre696-v51-vulkan-pacing-authenticated-readonly.yml), commit `62057a70c14d83442e1392e373cf295884b901fe`.
- [Run 43099187370](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43099187370): **QUEUED** na última consulta. Não promover a PASS antes de `completed/success` + relatório e validação do gate.
- O workflow verifica evidência assinada V51 PRE652 (APK SHA `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`), backup PRE99 com SHA autenticado, replay PRE431/V50 e patch diagnóstico PRE648 aplicado **somente em memória** para confirmar SHA. Depois registra hashes e linhas de sete arquivos, sem conteúdo bruto de fonte no artifact.
- A PRE695 CI [run 43095269762](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43095269762) também estava QUEUED; sua análise local das três capturas reais permanece independente da fila remota.

## Limites e próximo passo

O replay de receita em temp não prova igualdade binária da `libmain.so` assinada. A própria presença das chamadas Vulkan não mede sua duração nem comprova que compositor, driver ou motor causem a alternância 8↔25ms. Após gate fonte verificado, planejar trace sincronizado do caminho app → queue/ready → SurfaceFlinger/actual, sem interferência na jogabilidade e sem publicar dados brutos privados.

**Nenhum patch na fonte ativa, V52, assinatura, shader/SPIR-V, save, controle, gráfica, física, clock ou proteção térmica foi feito. Ganho de FPS não comprovado.**


## Atualização posterior — falha de rede identificada e retry isolado

- O [run PRE696 43099187370](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43099187370) terminou **completed/failure**: o download do arquivo PRE99 de ~875 MB falhou em `http.client.IncompleteRead` (`12827812 bytes read, 3949404 more expected` dentro de um bloco). **Não chegou ao replay** e portanto **não existe divergência de SHA de fonte, binário ou código de pacing observada nessa execução**.
- A correção aplicada **somente no workflow PRE696**, commit `23ae4d397c4498bf672da0ce28ccbbc75f4c6a07`, faz retry do bloco HTTP incompleto de 8 MiB, com limite e backoff; após o download exige 874.780.689 bytes e SHA256 PRE99 conhecido antes de restaurar a receita. Nenhuma rotina comum PRE105, APK, código Android, shader, assinatura, credencial ou save foi modificada.
- Novo [run PRE696 43100424122](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43100424122) **QUEUED na consulta de criação**, sem aprovação de fonte ainda. Resultado final deverá ser confirmado no job e JSON sanitizado.
- O contexto canônico no Drive já preservou o checkpoint local exploratório PRE696 e uma cópia integral anterior: [CONTEXTO_NFSMW.md](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view), SHA256 após checkpoint local `ea3a6eb6d5e27f89061a288b6648a687c7e06c4e2758d68f14224e743fe8cc79`; [backup anterior](https://drive.google.com/file/d/1Li6-sDPtP2QK-0Q9tTpapsEOTyQBP50u/view). O checkpoint local é **preliminar**; essa atualização posterior explicita o erro de rede e o novo gate.


## Resultado final posterior — PRE696 replay autenticado APROVADO

- **Run [43100424122](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43100424122) completed/success**, job `130789945224`. Log: `PRE696_STATUS=PASS_AUTHENTICATED_RECIPE_ONLY`, `PRE696_SOURCE_FILES=7`, `PRE696_SOURCE_TO_SIGNED_ELF_EQUIVALENCE=false`, `PRE696_FPS_GAIN_PROVEN=false`.
- O PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39` foi autenticado; replay V50 renderer SHA256 `1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92`; PRE648 aplicado em memória para conferir renderer V51 SHA256 `9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2`; backend autenticado `b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385`.
- Artefato GitHub ID `13892060839`: ZIP 2.892 bytes, SHA256 `d06e06d4dda54d4b50924ec5a404ef396c91cef2166f7b9e055f4b5910154075`, CRC PASS; privado no [Google Drive](https://drive.google.com/file/d/1JeOiiM0kei3dyLheQ2q5gNsNito5d4ku/view), download de volta conferido byte a byte. [Relatório completo privado](https://drive.google.com/file/d/1GJSH5_yDIZwMkI_O2_T5x65GVrYUAu7t/view).
- Comparação SHA256 real com snapshot histórico: **cinco arquivos iguais** (`presenter.h`, `nfsmw_ajustes_graficos.cpp`, `nfsmw_nativo_destinos.cpp`, `MotorNativo.java`, `Ajustes.java`); **dois diferentes** (`vulkan_presenter.cpp`: histórico 169.835 vs autenticado 169.876 bytes; `nfsmw_nativo_sistema.cpp`: 250.020 vs 250.253 bytes). **Não reutilizar linhas/code snippets do ZIP histórico como exatos da V51 nesses dois arquivos.**
- PRE696 confirma presença de mecanismos candidatos na **receita autenticada**, não igualdade entre código-fonte e ELF assinado, nem duração de chamadas, driver/compositor culpado ou ganho de FPS. **PRE697 proposta, ainda não executada:** análise diferencial mínima só leitura dos dois arquivos distintos e desenho de coleta sincronizada.
- Este resultado final **supera** os estados antigos `QUEUED` e a falha de download do run `43099187370` (falha transitória de transporte, reparada no workflow).

**Nenhum APK V52, shader, efeito, física, save, controlador, clock, assinatura ou política térmica foi alterado.**
