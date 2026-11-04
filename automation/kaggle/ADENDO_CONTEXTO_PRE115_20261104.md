## 99. Atualização consolidada PRE98–PRE115: automação, backup, ImGui e NDK (2026-11-04)

**Este adendo é cronologicamente mais recente que o cabeçalho histórico do documento (que ainda menciona V19/PRE53). O estado atual de referência é a V26; não foi gerada V27.**

### Evidências auditadas

- PRE98, execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41803202464: APK V25 SHA-256 35850d4ac0830d957a7f01e403f905bc8e8a4497904983654d0f608450420610 e V26 SHA-256 d8aebdaaf75df75739b47148f69ecfcdf1add37422416249375e31eca7812092. De dez bibliotecas ARM64, somente librexruntime.so mudou. A V26 contém os textos NEED FOR SPEED / MOST WANTED, SETTINGS / ANDROID e SAVE SETTINGS. Sua presença no binário não comprova execução dessa janela.
- PRE99/PRE104, execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41802874297: TAR PRE99 Drive ID 1qXEY5JXUdvZB4CuqPvXARz8TY-FArdzb; 874780689 bytes; SHA-256 integral af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39; MD5 95feb430df12bb1c6d9d82885ef9cdce; 28911 membros sem entradas especiais, caminhos duplicados ou inseguros identificados. Fonte settings_overlay.cpp PRE92 SHA-256 5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034.
- PRE107, execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41805685718: a etapa de restauração isolada em /tmp passou e registrou PRE107: RESTAURACAO_ISOLADA_VALIDADA. O workflow global falhou apenas ao publicar o resultado por conflito git push. O JSON original foi perdido; evidência do log preservada no GitHub. O workspace ativo do Kaggle não foi restaurado.
- PRE106, execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41805240882: a classe SettingsStyle em nativo/sdk/include/rex/ui/style.h define lifecycle_live verde. Rótulos de CVAR em settings_overlay.cpp usam ImGui::TextColored e LifecycleColor, independentes de ImGuiCol_Text.
- PRE109/PRE110, execuções https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41807950032 e https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41808392487: fluxo SettingsDialog / ImGui auditado no C++ preservado. A paleta global em imgui_drawer.cpp contém verdes. Sete cores globais sem PushStyleColor local declarado: MenuBarBg, ScrollbarBg, SeparatorActive, SeparatorHovered, SliderGrabActive, TextSelectedBg e TitleBgCollapsed. Isso não prova que todas sejam usadas na tela.
- PRE108/PRE111, execução conclusiva https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41809297640: proposta de dry-run com 75 linhas, aplicada apenas em memória, alterando etiquetas Android (branco suave, ouro, coral) e cinco cores locais (ScrollbarBg, SliderGrabActive, TextSelectedBg, SeparatorHovered, SeparatorActive). O número de PushStyleColor e PopStyleColor no Android foi ajustado de 20 para 25, mantendo 11 no desktop. Hash hipotético da fonte proposta 19102b563eb4cdd6c81d4a6bfa5bbc8cadfbb1e030247f535633cbc11524e069. Nenhuma fonte ativa foi modificada.
- PRE112 inicial, https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41812292925: fragmento C++ compilou, mas ambas as fontes completas falharam igualmente com a opção inadequada C++20, pois rex/types.h utiliza std::byteswap.
- PRE112B, https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41812605079: usando C++23 e cabeçalhos reais do projeto, o fragmento, o settings_overlay.cpp original e a cópia temporária com PRE111 passaram na compilação sintática completa do host. Backup e fontes foram novamente conferidos por SHA-256. **É uma verificação host C++23, não um teste do NDK; este último foi validado separadamente na PRE113B.**


### Automação PRE100–PRE103 e isolamento das credenciais

- PRE100/PRE101: GitHub Actions [41800099248](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41800099248) enviou o notebook de smoke privado ao Kaggle, recebeu estado `COMPLETE` e validou marcador de saída da mesma execução. Trata-se de smoke test, **não** de execução de NFSMW ou build de APK.
- PRE102: [41800823947](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41800823947) executou a sondagem isolada, mas os segredos Google do notebook disparado por API não ficaram disponíveis; status de acesso ao Drive **não validado**. Não houve restauração.
- PRE103: [41802218266](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41802218266) validou o acesso direto do GitHub Actions ao Google Drive com segredos protegidos do repositório, conferindo metadados e manifesto PRE99. O TAR completo só foi baixado e recalculado na PRE104.

### PRE113A–PRE113B — compilador Android ARM64

- PRE113A: [41813703799](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41813703799) identificou ausência do NDK exato na imagem padrão do runner, sem acessar o jogo.
- PRE113B: [41814082266](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41814082266), status `SINTAXE_ANDROID_ARM64_CPP23_VALIDADA`. Instalou em runner temporário o NDK **28.2.13676358**, usou `aarch64-linux-android26-clang++` e C++23, confirmou `__ANDROID__` e `__aarch64__` e verificou novamente os hashes do PRE99/PRE92/PRE111. **A fonte original e a proposta PRE111 passaram integralmente no teste sintático Android ARM64**. Isso não envolve linkagem, Gradle, empacotamento, assinatura ou teste de execução no Galaxy S24 FE.

### PRE114–PRE115 — cabeçalho do menu

- PRE114 inicial: [41818104687](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818104687) executou a análise, porém falhou na publicação do relatório por erro HTTP 500 do GitHub. Não é falha da fonte. PRE114B: [41818329320](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818329320) concluiu com `success` e relatório `automation/kaggle/status/pre114_header_scroll.json`.
- Na fonte `settings_overlay.cpp` PRE92, `ImGui::Begin("Settings##rex")` inicia na linha 264, o cabeçalho `##mw_header` começa na linha 350–351, os textos ficam nas linhas 354–357, a busca vem na linha 372 e a categoria na 379. Nenhum reset de rolagem explícito foi localizado nessa fonte. **Não houve medição do estado real de `GetScrollY` no aparelho.**
- PRE115: [41818700875](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41818700875), status `PRE115_PROPOSTA_SCROLL_ARM64_VALIDADA_NAO_APLICADA`. Dry-run de **17 linhas** propõe **somente em Android** `if (mobile_layout && ImGui::IsWindowAppearing()) ImGui::SetScrollY(0.0f)`, sem alterar cores, controles ou desktop. Fonte original e proposta passaram `-std=c++23 -fsyntax-only` com NDK Android ARM64/API 26. Hash SHA-256 hipotético do código proposto: `73b38386c4630fbf108cbe2aaab85919fe3461268173076bea9b545460b4bfd5`. **Nenhum patch foi aplicado à V26, nem houve nova APK ou teste no S24 FE**.
- A hipótese de rolagem persistente é **plausível, mas não confirmada**; clipping, escala e caminho de renderização alternativo continuam possibilidades abertas. Não misturar PRE111 (tema) com PRE115 (scroll) antes de obter evidência que permita distinguir efeitos.

### Próximo passo atualizado

1. Testar **a V26 já existente** no Galaxy S24 FE, abrindo Settings, rolando a lista manualmente até o topo e verificando se os textos `NEED FOR SPEED / MOST WANTED` e `SETTINGS / ANDROID` aparecem. Fechar e reabrir para comparar. Registrar observação/captura, se possível; nenhum resultado desse teste foi informado.
2. Se o cabeçalho aparecer quando a rolagem voltar ao topo, testar a hipótese PRE115 separadamente em futura build controlada. Se não aparecer mesmo no topo, priorizar medir clipping, janela efetiva, escala e posição dos elementos antes de alterar o código.
3. Preservar V26, PRE99, as propostas PRE111/PRE115 e backups. Ainda **não há V27**, nem comprovação visual de correção das cores ou ganho de FPS. Eventual build posterior: versionCode > 26, mesmo pacote e certificado permanente, sem acessar ou revelar segredos.

### Situação e próximo passo

1. Manter V26 como APK de referência, sem declarar que o novo tema está funcionando integralmente no Galaxy S24 FE. A tela ainda exige investigação visual do cabeçalho e de possíveis estilos herdados.
2. A compilação sintática Android ARM64 já foi validada na PRE113B; continuar a investigação do comportamento em tempo de execução do cabeçalho. Não aplicar o patch diretamente ao workspace Kaggle sem verificar a árvore ativa e guardar backup.
3. Não criar V27 automaticamente, não tocar na assinatura permanente e não publicar build debug como release. Eventual nova versão terá versionCode maior que 26, pacote io.github.nfsmwrecomp e mesmo certificado SHA-256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b.
4. Preservar 1920x1080, limite 120 FPS, gráficos, shaders, física, PG-9076 e proteções térmicas. Não há ganho de FPS comprovado nessas etapas.
5. Relatórios e scripts estão registrados no repositório privado Juniklx/nfsmw-actions-teste, em automation/kaggle/status. Credenciais não são armazenadas nesse repositório.
