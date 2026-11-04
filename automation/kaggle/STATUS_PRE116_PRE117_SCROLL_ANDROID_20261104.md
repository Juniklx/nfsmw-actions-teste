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
