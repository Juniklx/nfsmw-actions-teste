# NFSMW — Feedback V28, auditoria PRE130, correção PRE131 e build PRE132 V29

Data: 2026-11-04.

## Evidência real no Samsung Galaxy S24 FE

Após instalar e abrir a V28, o usuário mostrou captura de Settings confirmando:
- A tela mantém somente uma barra de rolagem, preservando a melhoria da V27/PRE117.
- O arrasto com o dedo **continua sem rolar** a lista fora da barra de scroll.
- O tema melhorou parcialmente, porém a estrutura, tipografia retrô e nomes técnicos CVAR continuam antigos; o redesign moderno não foi entregue pela V28.
- Nenhum FPS, configuração persistida, controles de jogo, desempenho, DeX ou funcionalidade touch resolvida foi comprovado por essa imagem.

## PRE130 — investigação da fonte real

Execução de auditoria somente leitura: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41865808432 .
Status `SOURCE_PATHS_AND_EVENTS_AUDITED`; SHA-256 do PRE99 conferido; `settings_overlay.cpp` PRE92 SHA `5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034` conferido.
Código relevante `workspace/nativo/sdk/src/ui/imgui_drawer.cpp` SHA-256 `1a62d13e81af3aac4837af06e90281b64bd282c78e6e5ce079d6ca930e8a5c24`. Contém `ImGuiDrawer::OnTouchEvent`: captura ponteiro touch nativo e atualiza `ImGuiIO.MousePos` e `MouseDown[0]` sem chamar o backend SDL3 padrão. PRE128 em Settings usava `ImGui::IsMouseDragging`, `IsWindowHovered`, `IsAnyItemActive`; as condições falharam no teste real. O motivo exato de cada condição não foi instrumentado, mas usar o ponteiro touch nativo é uma proposta mais direcionada.
Fonte antiga `kProggyTinyCompressedDataBase85`, tamanho 10, explica parte da aparência pixelada. O pacote já contém `android/app/src/main/res/font/michroma.ttf` (64344 bytes, SHA-256 `b62301163788bc5b7f8fcac0b74b184e34e1827e577b499ecb724da065098f87`), reutilizado sem publicar fonte standalone.

## PRE131 — proposta verificada em sintaxe ARM64

Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41868450408
Status `PRE131_ANDROID_ARM64_SYNTAX_PASSED`, ARM64 C++23 NDK `28.2.13676358`, Android API 26. Patches apenas em sessão efêmera da build, certificados não acessados, APK não construída nessa etapa.

Módulos GitHub:
- `automation/kaggle/pre131_native_touch_and_modern_ui_patch.py`
- `automation/kaggle/pre131_dryrun_android_ui.py`
- `.github/workflows/nfsmw-pre131-native-touch-modern-dryrun.yml`
- Relatório `automation/kaggle/status/pre131_touch_theme_arm64.json`

Mudanças:
- Mantém scroll único PRE117, sem alterações em controles físicos, PAL/USA ou renderização.
- Expõe no `ImGuiDrawer` apenas `IsTouchPointerActive()`, usando o estado nativo de `OnTouchEvent`.
- Em Settings Android acompanha posição do dedo, reconhece limiar vertical de 12 px e aplica scroll na janela raiz quando inicia em regiões passivas; não rouba eventos de widgets interativos.
- Registra estado por instância do diálogo e reinicializa ao soltar.
- Usa fonte Michroma do próprio projeto, embutida temporariamente em cabeçalho C++ Android, apenas para Settings; a fonte original continua padrão para outros overlays e desktop.
- Exibe rótulos mais legíveis, sem underscore, com contraste neutro; adiciona dica de busca e traduções visuais PT-BR. Os nomes de CVAR e regras de salvamento permanecem inalterados.
- ARM64 syntax passou para `settings_overlay.cpp` **e** `imgui_drawer.cpp`.

SHA-256 fonte final PRE131 Settings `9e95ab6637ec742be5d2f0d9aca94c8ce4f5f4f19f93ec94700183699b23ece7`; todos os cinco arquivos gerados estão listados no relatório e fixados na próxima build.

## PRE132 — build V29 assinada, pendente de conclusão

Workflow: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41869326935 .
Fonte: `automation/kaggle/pre132_build_signed_v29_pal_usa.py`, requisição `automation/kaggle/build_pre132_requests/PRE132_V29_S24FE_TOUCH_MODERN_20261104.json`, fluxo `.github/workflows/nfsmw-pre132-signed-v29-build.yml`.
Baseline imutável V28, Drive id `1OZngOrQNc5l8bqU1QOdNJf1JTk7n6x0f`, SHA-256 `6a06bb0ae4f310f5d93b6f1e4e4ae05763f3b83ee3de6a42b9f55eea02079caa`.
- Alvo package `io.github.nfsmwrecomp`, `versionCode=29`, mesma chave permanente (certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`).
- Preservar 10 bibliotecas ARM64, `libmain_usa.so`, shaders PAL/USA, runtime recompilado e verificado contra V28.
- APK deve sair apenas em artefato privado do Actions após todas as verificações, evitando a falha anterior de upload direto. Somente depois poderá ser transferida ao Drive e revalidada.
- Relatório esperado `automation/kaggle/status/pre132_v29_signed_release.json`, verificar seu `run_id=41869326935`.
- **A compilação V29 NÃO é prova do funcionamento do toque nem do redesign no aparelho.** Aguardar o resultado real e o teste manual no Galaxy S24 FE.

Automação `6aeb4db405e481918dd0e8afbb034764` atualizada para acompanhar V29 e avisar apenas quando APK validada for realmente disponibilizada, ou quando depender de ação humana. Preserve V28, V27, PRE99, backups e assinatura permanente.
