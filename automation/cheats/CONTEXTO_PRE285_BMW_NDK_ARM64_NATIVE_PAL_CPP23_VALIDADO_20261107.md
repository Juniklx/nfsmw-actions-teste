# NFSMW Android — PRE285: ARM64 NDK real, CMake isolado e sintaxe PAL C++23 aprovados (2026-11-07)

## Estado preservado e motivo
- Usuário confirmou no Samsung Galaxy S24 FE que **BMW M3 GTR normal adicionada pelo save PRE260 ao perfil MARCEK é selecionável e dirigível** na APK **V37** (`io.github.nfsmwrecomp`). No tuning aparecem somente as opções `Visual`, pois o código original classifica `IsHeroCar` e oculta `Peças/Desempenho`. Ainda não existem níveis de upgrade da BMW medidos no telefone. Fi̇at Punto e fichas Junkman preservados.
- PRE279/280: `sub_82582F70` chama método virtual via vtable **+12**, mas o destino ainda é desconhecido; `sub_82582A40` é uma candidata a `RefreshHeader` que acessa a seleção sem checagem nula.
- PRE283/284: sonda proposta `NFSMW_PRE283_VTABLE_TARGET_TRACE` registra `ctr.u32` já existente em guest PC `0x825837D4`, limitada a **12 mensagens**, desligada por macro. PRE284 recompôs a sequência de fontes da V37 e validou C++ host/SDK. **Não havia compilação Android ARM64**.
- PRE285 visa somente compilar a instrumentação no Android NDK ARM64 e fazer checagem de sintaxe PAL. Sem gerar APK, assinar, alterar saves ou tocar na chave permanente.

## Execuções e resolução de falhas no teste
1. Run **42330683152** (falha de *verificador*, não de compilação do módulo): script truncava stdout de `llvm-nm` aos 600 caracteres finais e não encontrava o callback. Log `PRE285_STATUS FAILED`, relatório apontou `Missing unmangled native callback from NDK object`. Corrigida a coleta para examinar stdout completo, sem alterar o módulo.
2. Run **42330897631** (workflow *success*, status técnico parcial): NDK Android ARM64 compilou o callback, verificou ELF AArch64 e símbolo C único; CMake produziu biblioteca estática isolada. A verificação avulsa do código PAL falhou por `simde/x86/sse.h` ausente dos caminhos de include e `std::byteswap` usado com C++20. Fica registrada como `PARTIAL_GUEST_SOURCE_SYNTAX_UNVERIFIED` — não falha do projeto Android.
3. Run **42331146370** (workflow *success*, status técnico parcial): descoberto o caminho real `nativo/sdk/thirdparty/simde`, eliminando o erro de cabeçalho; ainda faltava `std::byteswap`, recurso do **C++23**, no teste PAL.
4. **Run final 42331362650 — GITHUB ACTIONS SUCCESS, `PRE285_STATUS AUDIT_OK`**: módulo real NDK + biblioteca isolada CMake + código PAL C++23 aprovaram as verificações.

**Execução conclusiva:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42331362650

## Fonte, integridade e evidência produzida
- Código reproduzível: `automation/kaggle/pre285_bmw_arm64_ndk_logger_preflight.py`, workflow `.github/workflows/nfsmw-pre285-bmw-arm64-native-preflight.yml`. Gatilho `automation/kaggle/pre285_requests/20261107_arm64_vtable_logger_retry3_cpp23.json`.
- Base PRE99 autenticada por SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, restaurada em espaço temporário de GitHub Actions. Reproduzida cadeia de fonte V37: PRE117, PRE128, PRE131, PRE133, PRE157, PRE165, PRE170, PRE180, PRE194, PRE246 (8 sites dinheiro), PRE247 (16 sites totais) — hashes conferidos.
- Shard PAL `workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp`: SHA256 original `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`, prévia PRE283 SHA256 `1ce6208a0848955df6e918e7d56a28616afbf822e5a05b9747e4300e37bbaba9`, inserção reversível.
- Callback nativo `nativo/app/src/nfsmw_cheats_trace_pre284.cpp` SHA256 `5114d0835ab15fbc99f424185c77fc369f563bf69dccdf7a6c8e1e894c5ca11f`, registrado uma única vez no `nativo/app/CMakeLists.txt` temporário.

## Resultados da PRE285 final
- **Android NDK 28.2.13676358**, ABI `aarch64-linux-android26`, SDK headers reais. `clang++` compilou módulo de log em **objeto ELF64 AArch64**, 255856 bytes, SHA256 `95a1bd8bd40f0ae4f3f5902f9d122c05f18c4fca7031da03cf07e5ea278402c6`.
- `llvm-nm`: **uma única definição C sem mangling** `NFSMW_PRE283_VTABLE_TARGET_TRACE`, verificado.
- **CMake de teste isolado** com toolchain oficial Android compilou uma biblioteca estática `libnfsmw_pre285_logger.a` ARM64, 2837050 bytes, SHA256 `e1fd65d5c0712d587d40f9917739c1a122d226ae2551194cdd61788a68ae32ab`. **NÃO é a biblioteca de produção `libmain.so`**, nem contém o jogo completo.
- `nfsmw_recomp.11.cpp`: **`clang++ -std=c++23 -fsyntax-only` no NDK aprovado**, com `NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE=1` exclusivamente no processo de sintaxe. As rotinas do jogo não foram executadas e a macro não foi habilitada em nenhuma APK.
- Relatório JSON técnico original da execução final arquivado no Google Drive, sem saves nem assinatura: https://drive.google.com/file/d/1luOI4dpllauM_rIeV0yaoXPXtTk2XAd-/view

## Limitações — NÃO extrapolar aprovação
- **Nenhuma APK V38** foi compilada, assinada, instalada ou executada. `actual_game_libmain_linked=false`; a biblioteca `libmain.so` completa com SDL, C3, shaders/asset e Android Gradle ainda exige teste de integração.
- Níveis de upgrades da BMW não foram medidos. A classe `HeroCar` ainda mantém Peças e Desempenho ocultos. PRE264 (desbloqueio por modelo 41, sem filtro de propriedade) e PRE281 (proteção nula em função virtual ainda sem identidade provada) **não foram ativados**.
- `GetMaxLevel` possui efeitos guest nas estruturas de referências: não introduzir sete chamadas extras. A estratégia segura segue sendo diagnosticar destino da vtable em uma futura versão experimental usando **Fiat Punto** (sem desbloquear BMW), depois resolver proteção de lista vazia e escopo de garagem.
- `PRE285_STATUS AUDIT_OK` comprova **somente as etapas NDK/objeto/sintaxe/arquivo CMake isolado acima**, e não finalização do aplicativo.

## Próximo passo recomendado
1. **PRE286: teste de vinculação real do alvo nativo PAL `nfsmw` / `libmain.so` sem gerar APK ou tocar no certificado**, usando árvore V37 descartável, CMake toolchain do Android e flags originais de C++23, com a sonda PRE283 **OFF por padrão** primeiro. Confirmar vínculo e símbolo no DSO, depois considerar diagnóstico com macro ON. Caso Gradle externo configure assinatura obrigatória, não improvisar com debug ou criar chave; apenas relatar bloqueio, sem executar tarefas de packaging.
2. Futuras V38 (se aprovada): package `io.github.nfsmwrecomp`, versionCode **38 ou maior**, **mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, jamais recriar key, expor credenciais ou assinar debug.
3. Preservar integralmente V37, save MARCEK e demais perfis, Fiat, BMW, Junkman, PG-9076, 1920×1080, limite de FPS atual, shaders, gráficos, física e proteções térmicas. Sem alegação de ganho FPS ou alteração de prólogo Razor.
4. `CONTEXTO_NFSMW.md` canônico no Drive continua terminando perto da PRE237 na última verificação, mas os adendos PRE238–285 estão no GitHub. Não substituir histórico grande sem **backup e conciliação integral**. Esta nota registra o próximo resultado sem sobrescrever o contexto existente.

**Estado inequívoco:** PRE285 NDK ARM64 nativo + CMake isolado + sintaxe PAL C++23 = comprovado; link completo do jogo, APK V38, teste no S24 FE e upgrades da BMW = não comprovados.
