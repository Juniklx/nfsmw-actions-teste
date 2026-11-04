# NFSMW — PRE114B: diagnóstico estático do cabeçalho ImGui (2026-11-04)

## Evidências verificadas

- Run inicial PRE114 [41818104687](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818104687): inspeção C++ concluiu com marcador `HEADER_SCROLL_CLIP_ESTATICO_AUDITADO`, mas workflow global falhou no `git push` (GitHub HTTP 500). Nenhuma fonte alterada.
- Run repetida PRE114B [41818329320](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818329320): `success`; relatório `automation/kaggle/status/pre114_header_scroll.json`.
- PRE99 TAR e três fontes C++ de UI revalidadas por SHA-256 antes da auditoria. O backup e o workspace original permaneceram intocados.
- Ordem no `settings_overlay.cpp`: `ImGui::Begin("Settings##rex")` (linha 264), `BeginChild("##mw_header")` (linha 351), texto título (linha 356), subtítulo (linha 357), `EndChild` (linha 359), campo de busca (linha 372) e categoria (linha 379).
- Em `settings_overlay.cpp`, **0 chamadas** de `GetScrollY` / `GetScrollMaxY` e **0 chamadas** de `SetScrollY` / `SetNextWindowScroll` / `SetScrollHereY`; não é realizado um reset explícito de rolagem nessa fonte.
- `imgui_dialog.cpp` despacha `OnDraw`, e `imgui_drawer.cpp` chama `ImGui::NewFrame`, renderiza os diálogos, executa `ImGui::Render` e encaminha os dados a `RenderDrawLists`.

## Interpretação e limites

Na captura anterior da V26, o campo de busca e a categoria aparecem, mas o título mobile esperado não está visível. Como o código desenha o cabeçalho antes desses itens e não define explicitamente a rolagem na abertura, uma rolagem persistente do ImGui é **uma hipótese plausível**, não uma causa demonstrada. Também podem contribuir clipping, escala, ordem ou estado de janela; nenhum valor de `GetScrollY` ou retângulo de recorte foi medido no Galaxy S24 FE.

PRE115 foi preparada como alteração **diagnóstica isolada**: no ramo Android e somente quando `ImGui::IsWindowAppearing()`, chamar `ImGui::SetScrollY(0.0f)`. O objetivo é validar a compilabilidade da proposta antes de qualquer teste no dispositivo; isso não garante corrigir o cabeçalho. Não misturar inicialmente com o tema PRE111, para distinguir causas.

Nenhuma V27 foi compilada, nenhuma assinatura acessada ou modificada, nenhum APK alterado. Preservar o certificado permanente e versionCode maior que 26 em qualquer build futura.

O `CONTEXTO_NFSMW.md` canônico do Drive ainda não foi atualizado com esses resultados; este registro deve ser incorporado em adendo posterior sem reescrever o histórico.

## PRE115 — dry-run da rolagem ao abrir Settings (2026-11-04)

- Execução: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818700875 — **workflow global success**.
- Relatório `automation/kaggle/status/pre115_scroll_dryrun.json`, `status=PRE115_PROPOSTA_SCROLL_ARM64_VALIDADA_NAO_APLICADA`.
- Backup PRE99 integral e fonte `settings_overlay.cpp` PRE92 verificados novamente por SHA-256. Fonte original SHA-256 `5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034`; proposta apenas em memória/árvore efêmera com SHA-256 `73b38386c4630fbf108cbe2aaab85919fe3461268173076bea9b545460b4bfd5`.
- Diff de **17 linhas**: depois de confirmar `settings_visible`, apenas quando `mobile_layout && ImGui::IsWindowAppearing()`, chamar `ImGui::SetScrollY(0.0f)`. Nenhuma cor, desenho, valor de CVAR ou controle alterado.
- Toolchain usado: NDK **28.2.13676358**, `aarch64-linux-android26-clang++`, `-std=c++23 -fsyntax-only`.
- **Original e proposta** passaram com exit code 0. Portanto a proposta é sintaticamente compatível com a árvore PRE99 para Android ARM64.
- **Não foi aplicada ao projeto ativo, não houve linkagem/APK/assinatura, nem teste no Galaxy S24 FE.** Esse resultado não prova que o `GetScrollY()` atual seja diferente de zero nem que zerá-lo resolva o cabeçalho.
- Próximo teste discriminante sem nova APK: no menu V26, rolar o conteúdo até o início (gesto para baixo sobre a área rolável) e observar se o cabeçalho aparece. Fechar/reabrir o menu e comparar. Se permanecer ausente no topo, investigar clipping, escala e janela alternativa antes de usar o patch PRE115.
- O adendo do GitHub deve ser incorporado ao `CONTEXTO_NFSMW.md` canônico do Drive, que não foi modificado nesta etapa.
