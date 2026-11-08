# NFSMW Android — PRE425/PRE426: proveniência de argumentos e prévia de contagem passiva (2026-11-08)

## Baseline preservada
- APK V46 PRE401 (versionCode 46, pacote `io.github.nfsmwrecomp`), Nitro global confirmado pelo usuário e log PRE407/PRE408; arquivo APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`; assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- BMW M3 GTR no save `MARCEK`: menus de Peças/Desempenho acessíveis com bypass de menu, mas algumas opções de Transmissão exibiram `Option title`, `20/20` e `999.999.999`. Não comprar entradas inválidas.
- Auditorias usam backup de fonte PRE99 autenticado. Nenhuma APK nova, instalação, mutação do save ou aplicação de patch de runtime ocorreu nestas etapas.

## PRE425 — execução corrigida e validada
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451057300 — `PRE425_STATUS AUDIT_OK`, sem erros.
- Verificou SHA-256 e funções em quatro shards PAL:
  - `sub_8256B440` (`nfsmw_recomp.15.cpp`), armazena o campo de ponteiro/veículo em `r31+8` na linha relativa 137.
  - `sub_823E5988` (`nfsmw_recomp.28.cpp`), 155 linhas com três saídas; tem stores de memória guest, incluindo campo U16 `+18`. **Não chamar artificialmente**.
  - `sub_8256F818` (`nfsmw_recomp.57.cpp`), 230 linhas e duas chamadas a `sub_823E5988` nas linhas relativas 38 e 114. Em ambos os casos, `r3` é preparado como `r30+8`, onde `r30` vem de endereço estático; o tipo de categoria é preservado em `r26`.
  - `sub_82582F70` (`nfsmw_recomp.11.cpp`), chama `sub_8256F818` na linha relativa 696 e percorre a lista resultante.
- **Limite essencial:** não está provado que o endereço `r30+8` usado pela função de níveis seja idêntico ao endereço do campo `r31+8` capturado no diagnóstico de entrada PRE274. O teste host PRE274 não prova a igualdade de ponteiros no jogo, nem identifica qual carro gerou cada retorno. Não tratar nomes de variáveis nos mocks como identidade confirmada.

## PRE426 — prévia de captura passiva, DESLIGADA
- Primeira auditoria: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451252701 — `AUDIT_OK`. Execução final da revisão: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451276573 — `PRE426_STATUS AUDIT_OK` e `PREVIEW_OK`.
- Script `automation/kaggle/pre426_bmw_count_probe_dryrun.py` efetuou **somente em memória** transformação reversível de `sub_8256F818`, fonte SHA256 `a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c`.
- Instrumentação de prévia: após o retorno **existente** da primeira chamada a `sub_823E5988`, registra `performance_type` (em `r26`) e `existing_return_count` (em `r21`), sob flag `NFSMW_PRE426_BMW_COUNTS_ENABLE` **desligada por padrão**. Nenhuma chamada guest ou acesso de memória guest adicionado. Não faz dereferência de ponteiro guest. Orçamento de até 64 mensagens de log por processo.
- Prévia SHA256 `1910dbd638b09df99568c08e94defbf48e039fce862e4b1a1dace0511dc4ef0a`; teste host isolado `PRE426_PASSIVE_BOUNDED_HOST_MOCK_128_CASES_PASS`. **Esse mock não compila/roda o jogo, não valida Android/telemetria e não mede níveis da BMW ou do Punto**. Módulo C++ auxiliar não foi integrado ao CMake; não há APK.
- Essa instrumentação pode medir uma contagem candidata sem chamar artificialmente a rotina potencialmente mutável, mas por si só não correlaciona resultado a modelo/carro. A interpretação de contagem como `GetMaxLevel` ainda é candidata estrutural, não símbolo definitivamente confirmado.

## Próximo passo recomendado
1. Resolver a correlação do retorno com a seleção efetiva do carro: identidade de modelo/tuning car por fonte ou captura passiva independente, e distinguir sessões BMW/Fiat Punto.
2. Revisar um projeto de integração em árvore descartável, com flag desativada e prova de preservação do caminho normal. Não habilitar compras ou opções inválidas.
3. Qualquer V47 requer versionCode >46, mesmo certificado permanente, backups, respeito a 1920x1080, shaders/física, touch/PG-9076 e proteções térmicas. Não alegar ganho de FPS.
4. Atualizar `CONTEXTO_NFSMW.md` canônico no Drive com este adendo **após backup integral e checagem de marcadores de versões recentes**, sem apagar histórico ou rebaixar V46 para status anterior. Até a leitura de 2026-11-08, o arquivo no Drive terminava em PRE408; este registro GitHub não constitui atualização do Drive.
