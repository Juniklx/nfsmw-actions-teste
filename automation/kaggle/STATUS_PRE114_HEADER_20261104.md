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
