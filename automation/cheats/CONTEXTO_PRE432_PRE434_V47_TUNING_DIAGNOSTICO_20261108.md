# NFSMW Android — PRE432 e PRE434: diagnóstico passivo de tuning BMW (08/11/2026)

## Base imutável
- Referência instalada/testada: V46 PRE401, versionCode 46, pacote `io.github.nfsmwrecomp`, Nitro global infinito comprovado por usuário em PRE407, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, certificado PERMANENTE SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Save `MARCEK` e APK V46 devem permanecer intactos. BMW M3 GTR mostra opções inválidas após bypass localizado do menu: `Option title`, `20/20`, `999.999.999`; **nunca comprar essas peças**.
- O `CONTEXTO_NFSMW.md` do Google Drive foi sincronizado até PRE431 na PRE433 (run `42465557317`, `SYNC_OK`), com backup integral anterior `CONTEXTO_NFSMW_BACKUP_PRE433_20261108.md`. A linha PRE432 nesse contexto ainda afirma resultado pendente; a evidência seguinte atualiza esse status.

## PRE432 — resultado final CONFIRMADO
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42465261331 — `completed/success`.
- Log verificado: `PRE432_STATUS AUDIT_OK`; `PRE432_NATIVE_VALIDATION_COMPLETE`; CMake `True`; build nativo ARM64 `True`; ELF ARM64 `True`; flag compilador presente nos **dois shards gerados** `nfsmw_recomp.15.cpp` e `nfsmw_recomp.57.cpp`; duas definições dinâmicas de callback `NFSMW_PRE429_TRACE_ENTRY: 1` e `NFSMW_PRE429_TRACE_LEVEL: 1`.
- Build *nativa* `libmain.so` com sequência de source equivalente à V46, sem Gradle, APK, assinatura, save ou execução no Galaxy S24 FE. Não prova níveis reais de BMW/Punto nem correção do catálogo.

## PRE434 — preparação e execução de APK V47, AINDA NÃO VALIDADA
- Script: `automation/kaggle/pre434_build_signed_v47_bmw_passive_diag.py`, usa a rotina original de build/assinatura V46 PRE401 com `VERSION_CODE=47`, nome de artefato separado `NFSMW_V47_PRE434_BMW_PASSIVE_TUNING_DIAGNOSTIC.apk`, adicionando **apenas** as duas sondas passivas PRE429 via CMake já validado.
- Mantém todos os patches e validações de PRE401, incluindo PRE398 (cinco stores de Nitro infinito), bypass localizado do menu BMW, shaders e demais libs. Ativa `NFSMW_PRE429_TUNING_LEVEL_TRACE_ENABLE` apenas nos dois shards, registra até 16 eventos de entrada e 112 eventos de lista por processo, sem chamadas extras à física, escritas guest ou alteração de peças.
- A verificação antes de qualquer upload exige APK assinada com o mesmo certificado permanente por `apksigner`, pacote correto, versionCode 47, SHA/CRC e bibliotecas, marcadores de Nitro/C3 preservados, mais os dois marcadores PRE429 e **exatamente uma** definição de cada símbolo na `libmain.so` ARM64.
- Primeira execução PRE434: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42481733136 — **failure cedo no `py_compile`**, devido a continuação de linha no YAML. Não criou APK e não acessou assinatura. Corrigido em commit `e439a8e262471d2e8ad09a54dba7a0ae69418829`.
- Segunda execução PRE434: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42481812845 — **em andamento** na última consulta (etapa `Build V47 signed BMW passive diagnostic...`). Não afirmar sucesso, APK, assinatura, Drive upload ou instalação sem consultar resultado e relatório final.
- A V47 é **exclusivamente diagnóstica**: não corrige menus de upgrade, não adiciona pacotes e não altera preços/física. Se for produzida, verificar assinatura permanente e instalar como atualização preservando dados; recomenda-se backup do save antes de qualquer teste. Testar BMW e Fiat Punto em sessões separadas, sem compras, inspecionando `NFSMW_PRE429_ENTRY` e `NFSMW_PRE429_LEVEL` no `nfsmw.log`, e correlacionar sequencialmente os dados.
- Resolução interna 1920×1080, efeitos/shaders/física/PG-9076 e proteções térmicas mantidos. Não declarar 120 FPS ou qualquer ganho de desempenho.
- Próxima atualização de `CONTEXTO_NFSMW.md` do Drive: após resultado final da PRE434, novo backup integral e adendo verificável com run, status, APK/certificado/versão/Drive id quando existirem. Não substituir histórico por resumo.
