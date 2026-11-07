# NFSMW Android — PRE286: CMake do alvo PAL nativo, execução em andamento (2026-11-07)

## Estado de referência
- V37 com assinatura permanente, pacote `io.github.nfsmwrecomp`, permanece última APK testada. O usuário confirmou BMW M3 GTR normal adicionada por PRE260 ao save MARCEK, dirigível, mas o tuning só mostra Visual.
- PRE285 final GitHub Actions run `42331362650`: `AUDIT_OK`, NDK ARM64 compilou o logger PRE283, CMake estático isolado e `-fsyntax-only` do PAL em C++23 passaram. **Isto não comprova link da biblioteca real `libmain.so`.**
- Não ativar PRE264 (liberação por tipo, sem garantia de propriedade) nem PRE281 (guarda selecionada em rotina virtual ainda não confirmada), não invocar GetMaxLevel artificialmente.

## PRE286 — evidência já disponível
- Código novo reproduzível `automation/kaggle/pre286_bmw_real_pal_libmain_cmake_nosign.py`, workflow `.github/workflows/nfsmw-pre286-bmw-pal-libmain-cmake-nosign.yml`.
- PRE99 SHA-256 esperado/autenticado `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Teste sempre restaura fontes e reaplica a cadeia V37 de PRE284 **apenas em runner temporário**. Registra PRE283 no CMake; macro de rastreamento continua OFF por padrão.
- **Primeiro teste run `42332256954`:** workflow GitHub `success`, mas **status técnico `BLOCKED_PRODUCTION_CMAKE_CONFIGURE`**. O CMake original em `android/app/src/main/cpp/CMakeLists.txt` usa por padrão `NFSMW_MOTOR=xenos`, que exige o SDK externo `rexglue-sdk-android`, ausente da restauração; o erro foi `No hay un SDK preparado para Android`. Isso não aponta problema com fonte de V37.
- Auditoria de CMake identificou o caminho correto para **motor nativo**: `NFSMW_MOTOR=nativo`, `NFSMW_NATIVO_APP=app`, `NFSMW_NATIVO=${NFSMW_REPO}/nativo`. O arquivo `android/app/src/main/cpp/nativo/nativo.cmake` acrescenta `nativo/app` com SDK embutido `nativo/sdk` e target `nfsmw`, fonte candidata da `libmain.so`.
- Correção de parâmetros commit `9c4a253a9aba04cd451b4624c547088345e08951`; segunda execução lançada: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42332473337 .
- **Na última consulta, o run `42332473337` ainda estava `in_progress`** em `Restore V37 in ephemeral tree; configure/link original PAL native target only`. **Não** afirmar que `libmain.so` foi compilada, ligada ou teve símbolo encontrado antes de examinar o JSON final do artifact e o log.
- O script verifica NDK `28.2.13676358`, CMake `3.31.6`, procura alvo real que produz `libmain.so`, usa `-j2` e timeout limitado. Sempre omite Gradle `assembleRelease`, material de assinatura e APK; chaves e save não são acessados.
- Fonte/sha/certificado de referência mantidos; FUTURA V38, se aprovada, requer `versionCode >=38` e **mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, sem gerar chave nova, sem debug, sem senha exposta.

## Como retomar quando a execução terminar
1. Consultar **primeiro** `GitHub Actions run 42332473337`, job 128281873937 e último artifact `nfsmw-pre286-bmw-pal-libmain-cmake-preflight-42332473337`.
2. Ler `PRE286_BMW_REAL_LIBMAIN_PAL_CMAKE_LINK.json`, `status`, `cmake_configure`, `target_graph`, `selected_native_target`, `production_native_build`, `linked_library`.
3. Se `BLOCKED_PRODUCTION_CMAKE_CONFIGURE`, corrigir somente flags/paths com evidência da mensagem de erro. Se `BLOCKED_NO_REAL_LIBMAIN_TARGET`, identificar o nome exato em `build.ninja`, sem criar alvo fictício. Se `BLOCKED_PRODUCTION_NATIVE_LINK`, preservar erro e analisar dependências; nunca mascarar falha.
4. Se `AUDIT_OK`, confirmar ELF AArch64, libmain.so real e definição do callback. **Link nativo não significa APK V38 preparada, assinada ou testada.**
5. Registrar resultado final como adendo posterior; não sobrescrever `CONTEXTO_NFSMW.md` de ~500KB no Drive sem backup e conciliação de PRE238–286. Preservar V37, saves MARCEK/Fiat/Junkman, touch/PG-9076, 1920×1080, FPS cap atual, SDL, C3, gráficos, efeitos, física e térmica.

## Resultado conclusivo até esta nota
- Integração PRE285 nativa isolada: **aprovada**.
- PRE286 primeira tentativa: **CMake bloqueado por seleção padrão Xenos, não uma build PAL nativa**.
- PRE286 segunda tentativa: **execução iniciada e ainda sem artefato conclusivo na última consulta**.
- APK compilada/assinada/instalada ou níveis reais BMW medidos nesta etapa: **não**.
