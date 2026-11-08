# NFSMW Android — PRE430: validação da integração nativa dos dois marcadores BMW (2026-11-08)

## Referência verificada
- Estado atual consultado no GitHub: PRE429 `42451836847`, `AUDIT_OK`, dois marcadores em memória reversíveis e teste host sintético aprovado. **Não constitui teste Android ou medida de níveis BMW.**
- APK de referência **V46 PRE401**, Nitro infinito global testado pelo usuário, pacote `io.github.nfsmwrecomp`, versionCode 46, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`.
- No Drive, o `CONTEXTO_NFSMW.md` canônico ainda termina em PRE408 na leitura desta etapa. Não foi alterado.

## Execução PRE430
- Workflow: `.github/workflows/nfsmw-pre430-bmw-dual-native-link.yml`.
- Script: `automation/kaggle/pre430_bmw_dual_trace_native_link_nosign.py`.
- Execução solicitada: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42452283511 ; último estado observado na criação deste registro: **in_progress**, preparação de NDK/CMake. **Não marcar resultado final sem conferir execução e relatório.**
- Modo: fonte PRE99 autenticada restaurada em diretório descartável, replay de patches **base V37**, inclusão dos módulos PRE292 e PRE429, teste com compilação/link do target nativo original `nfsmw` → `libmain.so` ARM64, sem tarefa Gradle/assembleRelease nem assinatura. Falha segura em divergência de hashes, âncoras, CMake ou compilador.
- PRE429 registra em `sub_8256B440` o contexto do carro no início de personalização e em `sub_8256F818` o tipo e resultado candidato a contagem já retornada. Não adiciona nenhuma chamada guest; sem acesso novo à memória guest no código inserido. Por conta da compilação nativa temporária, o guard `NFSMW_PRE429_TUNING_LEVEL_TRACE_ENABLE` fica ligado **só no ensaio descartável**, não em APK instalada.
- **Limite técnico:** PRE430 usa a reconstrução de patches V37, **não reproduz integralmente a V46**, sobretudo PRE398 global Nitro. Seu êxito, se obtido, não prova coexistência final em V47 nem captura de contagens reais. O teste da flag compilador é limitado ao shard `nfsmw_recomp.57.cpp`; arquivo `.15.cpp` deve ser conferido à parte se necessário.

## Próximos gates
1. Confirmar `PRE430_STATUS`, `CMAKE_CONFIG`, `NATIVE_BUILD`, `ARM64_ELF` e definição do callback por log da execução correta.
2. Se aprovado, analisar prévia de integração na receita **V46** sem alterar lógica do Nitro, car settings, gráficos, SDL, controle ou mecanismo C3. Revisar ambos os shads/links e chamadas no binário.
3. Somente depois considerar APK diagnóstica versionCode **>46** com o mesmo certificado permanente. Preservar integralmente save `MARCEK`, V46 e backups, nunca comprar opções inválidas e não afirmar correção BMW ou ganho de FPS por simples build.
