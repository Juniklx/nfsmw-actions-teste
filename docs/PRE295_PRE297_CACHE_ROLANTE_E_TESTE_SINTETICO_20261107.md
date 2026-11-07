# NFSMW PRE295–PRE297 — Política incremental SDK e pré-validação do cache de objetos ARM64

**Data:** 2026-11-07. **Resultado:** canário SDK + ensaio sintético aprovados. Sem alteração de APK/release V39, save MARCEK, assinatura permanente, fontes do jogo, renderização ou controle.

## PRE295: persistência incremental do cache SDK
- Workflow canário: `.github/workflows/nfsmw-pre295-297-cache-canary.yml`.
- Mantém o PRE140 como política obrigatória de verificação e escopo `nativo/sdk/src`. Restaura pela nova família de chaves rotativas com fallback para o cache legado, verifica a política, executa testes isolados, sela a política e salva usando chave única por `github.run_id`. Assim, não tenta sobrescrever chave imutável.
- Run aprovado [42382269949](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382269949) registrou `PRE297_STATUS AUDIT_OK`, `PRE297_PRE295_ROLLING_IMMUTABLE_KEYS_VERIFIED True`, `PRE297_SYNTHETIC_CCACHE_HITS 1` e `Cache saved with key: nfsmw-sdk-rolling-v2-Linux-42382269949`.
- Run aprovado adicional [42382484905](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382484905) verificou o launcher/política PRE296 usando fonte sintética, registrou `PRE297_STATUS AUDIT_OK`, `PRE297_SYNTHETIC_OBJECT_HASH_EQUAL True`, `PRE297_SYNTHETIC_CCACHE_HITS 1`, e salvou `nfsmw-sdk-rolling-v2-Linux-42382484905`.
- **Limite importante:** nos dois ensaios a restauração retornou a chave legada `nfsmw-pre99-sdkonly-ndk28-clang-ccache4-v1-Linux`. Embora salvar uma nova chave tenha sido confirmado, seu reuso como entrada restaurada na execução seguinte **ainda não foi demonstrado**. Investigar o escopo/seleção de chaves do Actions antes de ligar no workflow de release.
- O canário não executa o jogo nem gera APK. O novo cache rolante foi aplicado apenas neste workflow experimental. O build V39 permanece sem alterações.

## PRE296: camada separada para arquivos de objetos do motor
- Implementados no GitHub: `automation/kaggle/pre296_game_objects_cache_launcher.sh` e `automation/kaggle/pre296_game_objects_cache_policy.py`.
- A política exige diretório separado `RUNNER_TEMP/nfsmw-game-objects`, evita links simbólicos, impõe limites, recusa nomes sensíveis de arquivos, e nunca mistura o PRE140 SDK com a área de objetos do jogo.
- O launcher está **desligado por padrão**, requer `NFSMW_CACHE_GAME_OPT_IN=1`, restringe a origem às fontes C++ sob `nativo/app` ou `nativo/app_usa` e apenas encaminha a compilação elegível ao ccache. Sem a flag, usa o compilador diretamente.
- PRE296 é **experimental e não aprovado para persistir objetos reais do jogo no GitHub cache**: a validação de arquivos por extensão não comprova ausência de dados sensíveis embutidos nos objetos, e a política não foi exercitada com o conjunto completo de fontes/flags do jogo real.
- Nenhuma cache de objeto do jogo foi enviada ao GitHub Actions ou ao Drive.

## PRE297: medição cold/warm com arquivo sintético
- Script `automation/kaggle/pre297_synthetic_cache_validation.py`: executa duas compilações idênticas do mesmo arquivo C++ sintético e verifica SHA-256 dos objetos e contagem de hits de compilador.
- Canário inicial [42382269949](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382269949) deu um hit real de cache e igualdade de SHA-256.
- Canário posterior [42382484905](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382484905) passou usando **o próprio launcher PRE296 em modo opt-in**, com código sintético em diretório que replica a estrutura `nativo/app/generated/default`; política independente inspecionou e selou o cache sintético. Conclusões `AUDIT_OK`, 1 hit, SHA-256 igual e `REAL_GAME_CACHE_VALIDATED False`.
- Falhas anteriores foram em adaptadores do script de teste, não na compilação do jogo: argumentos CLI do ccache, formato do contador e ordem de `-c`. Os scripts foram corrigidos e o último canário passou.
- O valor de 1 hit demonstra funcionamento em **toy C++**, não ganho de FPS nem redução quantificada em `libmain.so` real. O tempo de 24–26 minutos de V38/V39 não deve ser considerado resolvido.

## Gates antes de incorporar às próximas versões
1. Verificar nova família de cache SDK sendo realmente restaurada, não somente salva, usando cache-key exata e política PRE140.
2. Executar estudo isolado de cold/warm no motor PAL real, mesmo código/flags/compiler, comparando SHA-256 do `libmain.so` final, símbolos e contadores de hits; não persistir objetos do jogo no cache entre jobs nessa primeira prova.
3. Validar modelo de confiança/permissões do repositório e dados embutidos em objetos antes de qualquer cache de artefatos proprietários.
4. Manter PRE140/139 íntegros, certificados e controles de ABI/certificação, com fallback de build limpa.
5. Só então integrar opção específica em **uma futura release** (versionCode >39). Nenhum patch da BMW/desbloqueio, assinatura ou save modificado.

**Status consolidado:** PRE295 canário de gravação de nova chave SDK aprovado; PRE296 launcher/política criados e validados com arquivo sintético, persistência real desabilitada; PRE297 cold/warm sintético aprovado, cold/warm real ainda pendente.


## Complemento PRE295B (readback independente)
- O canário [42382664244](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382664244) obteve **cache hit por chave exata** `nfsmw-sdk-rolling-v2-Linux-42382484905` e passou `PRE140_SDK_CCACHE_POLICY_PASS`; isso valida que a entrada foi persistida e pode ser relida.
- O canário [42382717266](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382717266) repetiu a restauração com `restore-keys` por prefixo, **selecionou novamente o cache legado** mesmo com chave rotativa gravada, executou teste sintético com 1 hit, e salvou chave `nfsmw-sdk-rolling-v2-Linux-42382717266`. Necessário corrigir/entender a prioridade do prefixo antes de promover à release.
- **Decisão de segurança:** PRE295 evoluiu para solução de canário verificável, não alteração de release; a versão V39 publicada não foi refeita. PRE296 não armazena objetos reais de jogos nos caches Actions.
