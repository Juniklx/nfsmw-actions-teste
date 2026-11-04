# NFSMW — PRE118: auditoria da árvore de build PRE99 (2026-11-04)

## Execução confirmada

- GitHub Actions: [41827163959](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41827163959), conclusão global **success**.
- Script usado: `automation/kaggle/pre118_audit_build_tree.py`; relatório `automation/kaggle/status/pre118_build_tree.json`, status `PRE118_PRE99_BUILD_TREE_AUDITADO_SEM_APLICAR`.
- O TAR PRE99 foi baixado novamente e conferido integralmente por SHA-256 e tamanho, com **28.911 entradas**. Leitura limitada aos arquivos públicos de construção e à fonte PRE92, sem acessar chaves/credenciais.
- Fonte `workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp` SHA-256 `5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034`. A proposta exata PRE117 foi reconstruída novamente, com **30 linhas de diff** e SHA-256 hipotético `8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af`.
- Arquivos presentes no PRE99: `workspace/android/app/build.gradle.kts` (SHA-256 `ef570ba95703cb54df3c0e503fec6bce11aaa0f640e907208bdfb22bd8711230`), wrapper Gradle, `settings.gradle.kts`, CMakeLists do Android e `gradlew`.
- Wrapper Gradle **9.1.0**; arquivo Gradle público referencia pacote `io.github.nfsmwrecomp`, `minSdk=26`, `compileSdk=36`, motor `nfsmw.motor`, edição `nfsmw.edicion` e configuração `nfsmwPermanente`. O `versionCode` é **dinâmico** no Gradle, não um número literal pinado no backup; nenhuma release V27 foi compilada, assinada ou verificada.
- Contagens estruturais: **263 arquivos C++ gerados** sob `workspace/nativo`, **6 arquivos .nfsp**, um arquivo .so com arquitetura ARM64 em caminho auditado, mais arquivos de CMake e codegen ReXGlue. Essas contagens **não demonstram staging completo nem garantem que Gradle/CMake não precise de reconstruções**. A raiz `workspace/app/generated-android/` não aparece; há referências a `generated-android` no Gradle. O backup exclui cache Gradle global e material privado de assinatura.
- O relatório não leu nenhum arquivo de senha ou chave privada e marca `can_release_sign_now=false` por falta de validação de credenciais e certificado para uma nova build.

## Limitações

A PRE118 verificou apenas a **cópia arquivada PRE99** no GitHub runner; não validou o conteúdo atual de `/kaggle/working/NFSMW_V20_BUILD_KAGGLE_ISOLADO` nem outro workspace Kaggle. Kaggle normalmente executa notebooks em sessões isoladas, então não assumir que um workflow isolado possa modificar ou inspecionar uma sessão interativa já existente. A assinatura permanente não foi acessada; o certificado correto continua SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` e a próxima APK, se criada, exigirá `versionCode >26`.

## Próximo passo

Preparar **PRE119: auditoria somente leitura da árvore ativa Kaggle** para localizar, classificar por SHA-256 e selecionar explicitamente a fonte alvo antes de qualquer aplicação PRE117. Não aplicar PRE115 (rolagem zerada) nem PRE111 (tema) junto à correção de scroll único. Quando árvore ativa, assinatura e staging forem verificados, permitir patch reversível com backup e depois build/teste separado (normal sem DeX e com DeX). O texto canônico no Google Drive ainda não recebeu este adendo por limitação OAuth de escrita HTTP 403; registrar progresso no GitHub sem alegar sincronização canônica.
