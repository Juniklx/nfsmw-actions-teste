# NFSMW Android — V37 diagnóstica autorizada e iniciada (2026-11-06)

## Evidência de autorização e disparo
- Usuário autorizou expressamente compilar a V37 diagnóstica preservando a assinatura permanente e os cheats desligados.
- GitHub Actions **run 42304603209**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42304603209
- Commit disparador: `6718ac89b5678ff5da9a84ecc490638292824bfc`
- Workflow: `.github/workflows/nfsmw-pre246-v37-passive-money-signed.yml`, alterado para diagnóstico passivo de **16 sites PAL**.
- Builder: `automation/kaggle/pre246_build_signed_v37_passive_money_trace.py`.
- Fonte autenticada: backup PRE99 SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, com patches prévios de input, SDL e C3 da PRE194.

## Escopo e verificações
- 8 pontos de gravação de dinheiro observados pela PRE246; 5 candidatos de nitro e 3 de Speedbreaker observados pela PRE247, **somente após os stores originais**.
- Nenhum cheat habilitado, nenhuma gravação original substituída e nenhuma leitura guest extra prevista.
- Novo `versionCode=37`; package `io.github.nfsmwrecomp`.
- Mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, jamais recriar chave nem expor senhas.
- APK previsto, **ainda não comprovado**, com nome `NFSMW_V37_PRE247_PASSIVE_MONEY_NITRO_SPEEDBREAKER_DIAGNOSTIC.apk`. Destino para publicação somente após os verificadores `verify_apk`: pasta privada `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`.
- O verificador exige marcador PRE246 e PRE247 no `libmain.so` PAL, C3 PRE194, SHA dos assets PAL/USA, assinatura v2 e `versionCode 37`.
- Preservar V35/V36 e saves, SDL/input do PG-9076/touch, resolução 1920×1080, cap atual 60 FPS, shaders/gráficos/física e proteção térmica. C3 `copia_duplicada=true` continua pendente.
- A V37 é diagnóstico, não uma correção de C3 nem uma prova de cheats ou ganho de FPS.

## Status no momento do registro
- Workflow com steps preparatórios (JDK, SDK/NDK, CMake, Gradle/ccache) aprovados e compilação/assinatura em andamento.
- **Não afirmar V37 compilada, assinada, instalada ou testada** até leitura de resultado final e relatório.
- Um monitor agendado foi criado para checar o run e informar o resultado sem exigir nova ação manual enquanto a build roda.

## Próximo passo
1. Conferir conclusão final do run e artifact privado JSON/APK.
2. Se falhou: auditar log/relatório, corrigir apenas causa confirmada e disparar nova build isolada (sem tocar na V36 ou chave).
3. Se assinou/validou: verificar URL e hash reais do APK no Drive e apresentar ao usuário para instalar/testar no Galaxy S24 FE.
4. Solicitar `nfsmw.log` de sessão real e analisar `NFSMW_PRE246_CHEATS_DIAG` / `NFSMW_PRE247_CHEATS_DIAG`; manter cheat desligado até avaliação funcional.
5. Incorporar evidências à versão canônica de `CONTEXTO_NFSMW.md` com backup antes de substituir conteúdo.
