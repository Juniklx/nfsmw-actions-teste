# NFSMW Android — cheats PAL/PT-BR: estado PRE246–PRE249C (2026-11-06)

Registro técnico para anexação à próxima atualização de `NFSMW_Android/CONTEXTO_NFSMW.md`.
Este arquivo documenta testes estáticos e protótipos PASSIVOS, **não cheats funcionais**.

## Resultados verificados

- **PRE246** — [GitHub Actions 42295940364](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42295940364), `completed/success`, `PRE246_PREFLIGHT_STATUS AUDIT_OK`, `PRE246_TRACE_SITES 8`: oito pontos PAL de saldo instrumentados depois dos `REX_STORE_U32`, no PRE99 autenticado restaurado em pasta temporária; stores originais não foram substituídos; nenhuma nova leitura da memória guest. Código da instrumentação: `automation/kaggle/pre246_passive_money_probe_patch.py`.
- **PRE247** — [GitHub Actions 42302751973](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42302751973), `completed/success`, `PRE247_PREFLIGHT_STATUS AUDIT_OK`, `PRE247_PASSIVE_SITES 16`: combinou oito pontos de dinheiro, cinco gravações candidatas de nitro (`sub_82424AF0`, campo PAL `+252(r31)`) e três candidatas de Speedbreaker (`sub_8246C2F0`, campo PAL `+132(r31)`). Usa somente endereços e bits de valor calculados pelo jogo. Os candidatos de nitro/Speedbreaker **ainda não têm semântica comprovada em execução**. Código: `automation/kaggle/pre247_pal_meter_passive_probe_patch.py` e `pre247_disposable_preflight.py`.
- **PRE248** — [GitHub Actions 42303147551](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42303147551), `completed/success`, `PRE248_STATUS AUDIT_OK MOCK_CXX True`: compilação e linkedição sintéticas em C++20 dos módulos de callback com logger SIMULADO; testes cobriram os 16 locais, limite de 12 registros por local (192 no total) e chamadas concorrentes. Isso NÃO valida o SDK real nem o Android.
- **PRE249C** — [GitHub Actions 42303819064](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42303819064), `completed/success`, `PRE249_STATUS AUDIT_OK HOST_REAL_REX_SYNTAX True`: teste de sintaxe `g++ -fsyntax-only` em host contra o cabeçalho REAL `rex/logging/macros.h` do PRE99 autenticado, usando `libspdlog-dev` e `libfmt-dev` no runner. Na execução PRE249B [42303623410](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42303623410), o compilador host falhou por falta de `spdlog/spdlog.h`; ao instalar a dependência no runner, a checagem passou. **Isso não valida linkedição Android nem Gradle/CMake final.**

## Integridade e limites

- Os testes PRE246–PRE249 ocorreram em árvores restauradas descartáveis ou em módulo isolado; **nenhuma APK V37 foi produzida por essas etapas**.
- Nenhum cheat foi ativado no jogo; não se afirmou dinheiro, nitro ou Speedbreaker infinitos em execução.
- Nenhum save, chave/certificado, pacote Android, biblioteca release, gráficos, shaders ou arquivo do Drive foi alterado por esses protótipos.
- Referência de release: **V36 PRE194**, pacote `io.github.nfsmwrecomp`, `versionCode=36`, certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Preservar Galaxy S24 FE, touch e controle iPega PG-9076, 1920×1080 interno, limite atual 60 FPS, shaders, efeitos, física, saves e proteções térmicas. Nenhum ganho de FPS foi demonstrado pelas auditorias de cheats.
- O pipeline V37 PASSIVO em `.github/workflows/nfsmw-pre246-v37-passive-money-signed.yml` foi **preparado mas não executado** nesta sequência. Não acionar build/assinatura enquanto permanecer a restrição do usuário de não compilar.

## Próximo ponto decisório

A instrumentação está suficientemente avançada para **planejar** um diagnóstico controlado na APK assinada, mas isto exigiria liberar explicitamente a compilação V37 (a restrição anterior foi `não compilar`) e, depois, realizar instalação/teste e entregar `nfsmw.log` do Galaxy S24 FE.

Antes de afirmar cheats efetivos, é necessário correlacionar as gravações observadas com dinheiro, nitro e Speedbreaker durante ações reais do jogo e avaliar compra/saves; só então ativar políticas reversíveis, desativadas por padrão, com versionCode crescente e certificado permanente idêntico. Não tratar `AUDIT_OK` estático como validação funcional.
