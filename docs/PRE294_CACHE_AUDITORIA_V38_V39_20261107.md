# NFSMW PRE294 — Auditoria de cache entre builds V38 e V39

**Data:** 2026-11-07. **Modo:** análise somente leitura dos scripts e logs existentes. **Não há alteração de APK, código do jogo, cache ativo, assinatura, chave, saves ou configuração de execução.**

## Evidências verificadas

- V38, GitHub Actions run [42354940551](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42354940551): cache Gradle por chave `nfsmw-pre99-gradle-ef570ba95703-jdk21-v1-Linux` com hit; cache PRE140 SDK por chave `nfsmw-pre99-sdkonly-ndk28-clang-ccache4-v1-Linux` com hit. Etapa principal 08:19:51–08:45:51 UTC (~26min), incluindo compilação, auditoria e upload que falhou no Drive. Build/apksigner concluídos no relatório, upload externo falhou.
- V39, run [42378263558](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42378263558): mesmos dois hits. Etapa principal 13:44:29–14:08:32 UTC (~24min), incluindo compilação, auditoria e upload ao Drive com sucesso.
- V39 restaurou Gradle cache ~386 MB (404.700.413 bytes de transferência do cache), status `GRADLE_CACHE_HIT=true`. Script PRE139 limita paths a `caches/modules-2` e `wrapper`, não armazena diretórios de Gradle build nem `build/` nativo.
- V39 restaurou PRE140 ccache SDK-only ~7 MB (7.640.895 bytes reportados como tamanho comprimido do cache), com validação de conteúdo local `files 379 bytes 7659924`.
- Após a V39, PRE140 seal registrou `files 469 bytes 15267774`. A etapa de `actions/cache/save@v4` foi **skipped** porque a chave já existia (`steps.sdk_ccache.outputs.cache-hit == 'true'`). Portanto, nenhum incremento desta execução foi persistido nessa mesma chave imutável.
- O launcher `automation/kaggle/pre140_sdk_only_ccache_launcher.sh` contém regra explícita de bypass: apenas `nativo/sdk/src/*` é encaminhado ao ccache; `nativo/app`, `nativo/app_usa` e os shards `generated/default/nfsmw_recomp.*.cpp` chamam o compilador diretamente. O script PRE140 de validação marca `game_translation_sources_cached: false`.
- O builder PRE293 recompõe PRE99 autenticado em diretório temporário, aplica patches e executa Gradle `assembleRelease`. Configura `CMAKE_BUILD_PARALLEL_LEVEL=2`, `--max-workers=2`. Isso preserva reprodutibilidade, mas não reaproveita objetos nativos de builds anteriores.
- O builder coleta `pre140_sdk_only_ccache_numeric_stats` ao final, mas logs resumidos não expõem as métricas de hit/miss. **Hit da ação de restauração não mede hit por unidade C++**.

## Diagnóstico

1. Causa estrutural principal confirmada: o código recompilado do jogo não está coberto pelo ccache PRE140; portanto, não há evidência de reuso de objetos do motor entre V38 e V39.
2. Causa estrutural secundária confirmada: a chave imutável exata do cache SDK teve hit e o save foi ignorado, perdendo os novos objetos SDK produzidos durante V39.
3. Contribuições adicionais possíveis, **não quantificadas**: custo de extração/verificação de PRE99, rebuild nativo, paralelismo em 2, linker e processos Gradle. Não atribuir percentuais nem prometer tempo de build.

## Próxima mudança proposta (PRE295, ainda não executada)

- Medir tempos por fase e estatísticas de chamadas cacheáveis, hits e misses por compilador, sem armazenar materiais sensíveis.
- Corrigir primeiro o fluxo imutável do cache PRE140: restaurar por prefixo e salvar em nova chave versionada depois de sucesso/verificação, com checagens de integridade e limite de tamanho; nunca sobrescrever chaves anteriores.
- Projetar **em separado** uma política de cache de objetos PAL/USA de C++ (não salvar fonte, XEX, APK, assets ou assinatura) com chave estrita de snapshot PRE99, digest final dos shards e patches, arquitetura, NDK/Clang, flags CMake, hashes de headers e versão do launcher. Evitar chaves baseadas só no `versionCode`; para recuperação incremental entre versões, verificar dependências/headers e mudanças na fonte realmente compilada.
- Validar com duas compilações em runner descartável: primeiro cold, segundo warm de fonte idêntica, auditando hash de `libmain.so` e símbolos, e comparando tempo e hits reais. Como objetos nativos do jogo podem conter código protegido, avaliar política e privacidade do repositório privado antes de persistir qualquer artefato.
- Nunca incluir credenciais ou chaves; não modificar assinatura permanente. **Não aplicar a mudança de cache à release V39 retroativamente.**

## Resultado

`PRE294_CACHE_AUDIT_REVIEWED` (inspeção documental/logs). Nenhum ganho de compilação foi implementado ou medido.
