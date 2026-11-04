# NFSMW — PRE116/PRE117: rolagem dupla no menu Android (2026-11-04)

## Nova evidência visual relatada no Galaxy S24 FE

O usuário enviou captura atual do menu Settings **fora do modo DeX**. Na imagem, os textos do cabeçalho `NEED FOR SPEED / MOST WANTED` e `SETTINGS / ANDROID` **aparecem**. Isso corrige a hipótese anterior de que o cabeçalho estaria completamente oculto nessa condição; **não** significa que o menu esteja correto.

O usuário relatou **uma rolagem dentro de outra** e área de rolagem interna **muito pequena fora do DeX**. A captura é consistente com dois controles/áreas de rolagem: barra externa da janela e barra curta na área de variáveis. A imagem mostra elementos verdes herdados do tema apesar do amarelo/grafite parcial. O `120 fps / 8.3ms` do overlay é uma leitura instantânea na captura, não um benchmark nem ganho de desempenho demonstrado.

## Auditoria PRE116 concluída

- GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41825528723, job `success`, status `PRE116_NESTED_SCROLL_ESTATICO_CONFIRMADO`.
- Relatório: `automation/kaggle/status/pre116_nested_scroll.json`.
- PRE99 integral e fonte PRE92 `workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp` novamente verificados por SHA-256.
- O ImGui `Settings##rex` (linha 264 da fonte) não desativa a rolagem da janela principal: flags existentes `NoCollapse|NoMove|NoResize`.
- O `ImGui::BeginChild("##cvars", ImVec2(0, -30.0f), false)` na linha 503 é executado também em Android; o respectivo `EndChild` está na linha 729.
- O botão `SAVE SETTINGS` (linha 740) tem **52 unidades lógicas de altura em Android**, mais outros controles e separadores, mas o child usa uma reserva de apenas **30 unidades lógicas**. Isso é uma explicação de código coerente com a barra interna diminuta e overflow da root.
- O desktop (não Android) tem ainda `BeginChild("##cats", ...)` para categorias, dentro de uma ramificação distinta.
- A auditoria estática **não mediu** `GetScrollY`, altura final do child nem retângulos de clip do dispositivo. Não há conclusão de pixels exatos.
- Consequência: **PRE115 (reset da rolagem ao abrir) deixa de ser a opção prioritária**, porque não elimina os dois donos de rolagem.

## Direção da proposta PRE117

- Preparado um dry-run de **scroll único** para Android: manter `Settings##rex` como área rolável; não entrar no `##cvars` child nessa plataforma. Assim o cabeçalho, filtros, CVARs e botão salvar seguem um fluxo único com rolagem contínua.
- Preservar `BeginChild/EndChild` da lista no desktop **não Android** e sua lógica anterior.
- Essa estratégia **não mantém o cabeçalho fixo durante a rolagem**: ele sai da vista naturalmente, e o rodapé é alcançado deslizando até o fim. É um compromisso explícito para evitar uma lista quase sem altura útil no celular.
- **DeX continua sendo Android** (`mobile_layout=true`), então essa proposta também altera o comportamento do menu dentro do DeX. É preciso testá-lo depois; não declarar comportamento DeX preservado sem evidência.
- PRE117, enquanto não testada: sem patch na árvore ativa, sem APK, sem assinatura, sem instalação no S24 FE. Não combinar de início com as mudanças de cor PRE111 nem com o reset PRE115.

## Próximo passo

Conferir o relatório PRE117 da sintaxe real NDK 28.2 ARM64/API26. Se aprovado, preparar aplicação reversível somente após verificar a árvore alvo e preservação da assinatura permanente. Para demonstrar sucesso visual, exigir novo teste no **Galaxy S24 FE fora do DeX**, verificando rolagem única, acesso às primeiras/últimas variáveis, capacidade de salvar e touch/PG-9076, depois verificar DeX.

O `CONTEXTO_NFSMW.md` canônico no Google Drive **não foi atualizado** por esta auditoria: tentativa anterior de escrita via credencial GitHub retornou HTTP 403. Backup canônico anterior permanece preservado. Este documento privado é adendo a ser incorporado quando a atualização for autorizada.

## PRE117 concluída — evidência da compilação sintática (2026-11-04)

- [GitHub Actions PRE117 — run 41825894541](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41825894541), `job.conclusion=success`.
- Relatório persistido: `automation/kaggle/status/pre117_single_scroll.json`, `status=PRE117_SCROLL_UNICO_ARM64_VALIDADO_NAO_APLICADO`.
- PRE99 TAR completo e fonte PRE92 revalidados por SHA-256, fonte original `5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034`.
- Diff unificado de **30 linhas**, restrito a dois blocos: linha 503 condiciona `BeginChild("##cvars")` a `!mobile_layout`; linha 729 condiciona o `EndChild()` correspondente a `!mobile_layout`. O `PushID/PopID` permanece intacto, assim como o restante dos controles, cores e Save Settings.
- SHA-256 **apenas hipotético** da fonte com PRE117: `8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af`.
- Toolchain: NDK `28.2.13676358`, compilador `aarch64-linux-android26-clang++`, `-std=c++23 -fsyntax-only`, com includes reais da árvore PRE99 restaurada em pasta efêmera.
- Ambos os arquivos C++ completos passaram: original `exit_code=0` e proposta `exit_code=0`.
- Status de segurança: `active_workspace_modified=false`, `apk_built=false`, `signing_key_accessed=false`, `device_rendering_tested=false`. **Não houve V27 e não foi comprovada a correção visual.**
- Não declarar DeX preservado: no Android, `mobile_layout` é true tanto no telefone normal quanto no DeX. Se instalada futuramente, PRE117 deverá ser testada nos dois modos.
- Uma única área rolável implica que o cabeçalho e os filtros rolam com a lista; o botão SAVE SETTINGS é alcançado no final. Esse é um compromisso deliberado para não reduzir ainda mais a altura da lista em telas pequenas.
- O tema PRE111 e o experimento PRE115 continuam como propostas separadas e **não foram incorporados** à PRE117.

**Próxima etapa segura:** verificar a árvore ativa e preservar backup antes de um patch controlado; planejar build experimental com `versionCode > 26` e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` intacto, mas apenas após validar os pré-requisitos de assinatura sem ler/expor segredos. Na APK resultante, testar rolagem fora do DeX, DeX, acesso aos primeiros e últimos CVARs, SAVE SETTINGS, controles touch e PG-9076, sem alterar 1920×1080, 120 FPS, gráficos, física ou proteções térmicas.

O `CONTEXTO_NFSMW.md` canônico no Drive permanece sem esse adendo por limitação de escrita OAuth HTTP 403; não alegar que foi atualizado.
