# NFSMW Android — PRE271: sonda passiva dos limites de desempenho, pré-teste de memória (2026-11-07)

## Estado do problema
- Usuário confirmou BMW M3 GTR normal adicionada via save PRE260 ao perfil MARCEK, selecionável e dirigível na V37. No tuning, só aparece Visual; Peças e Desempenho são ocultados pela regra HeroCar. A BMW de prólogo M3GTRCAREERSTART e a carreira/Razor não foram alteradas.
- PRE269/270 confirmaram estruturalmente o caminho da função de contagem `sub_823E5988` (PAL) e do builder `sub_8256F818`. O guest helper usa dados de atributos da física; não há valores reais medidos da BMW nem prova de pacote instalável.

## PRE271 — resultado verificado
- Execução GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42324435134 **success**, `PRE271_STATUS AUDIT_OK`.
- Backup PRE99 autenticado; fonte exata `workspace/nativo/app/generated/default/nfsmw_recomp.28.cpp`, SHA-256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`.
- Script `automation/kaggle/pre271_bmw_getmaxlevel_passive_logger_dryrun.py` desenvolveu transformação **SOMENTE EM MEMÓRIA**, desativada por padrão (`NFSMW_PRE271_BMW_LEVEL_DIAGNOSTIC`). Prévia do arquivo modificado SHA-256 `9405becf180d43d5f18af9bf33016e751ba655e39bb54e3edd6839e20317a211`.
- Captura em variáveis **host** dos parâmetros guest de entrada `r3` (ponteiro pvehicle) e `r4` (categoria 0–6); captura `ctx.r3.s32` no final de **3 saídas da função**. A consulta é passiva e não modifica o valor retornado. Nenhuma leitura/gravação extra de memória guest no código proposto.
- Verificações: 3 saídas com gancho, reversibilidade byte a byte da função e do arquivo, número original de `REX_LOAD/STORE` e funções preservados. Módulo externo pré-visualizado em memória com contador atômico, até 8 registros por categoria (limite global de 56 mensagens).
- Mock host C++ compilou e passou `PRE271_PASSIVE_LOG_BOUNDED_56_OK`, limite de 56. **Não é compilação do código do jogo nem teste no Android.**
- Relatório técnico sanitizado arquivado no Drive: https://drive.google.com/file/d/1XkpxgQBRbDq4floXSoer5-h-mIT3v89V/view

## Limitações importantes
- **Nenhuma APK V38 foi compilada, assinada, instalada ou testada. Nenhuma instrumentação foi ativada no jogo.** O arquivo de código recompilado não foi substituído em backup persistente ou no Drive; o script e relatório são o que foi arquivado.
- A função `GetMaxLevel` pode NÃO ser executada para a BMW quando o menu Desempenho está oculto. Portanto mesmo uma V38 com essa sonda poderia não capturar os sete valores de BMW sem um caminho de leitura validado e limitado a contexto seguro.
- Ponteiro pvehicle guest não revela o modelo do carro: correlacionar com escolha de veículo no aparelho e evidências adicionais, sem concluir automaticamente que logs pertencem à BMW.
- Módulo de logging ainda precisaria ser vinculado via CMake e compilado no ambiente Android, preservando todas as rotinas V37; não tratar a prévia como patch de release pronto.
- O resultado de `GetMaxLevel` pode ser zero; liberar apenas o menu principal sem proteção em `CustomizePerformance::RefreshHeader()` pode causar acesso inválido, **risco teórico, não crash confirmado**.
- Para compilar próxima APK: package `io.github.nfsmwrecomp`, versionCode **38 ou maior**, assinatura permanente **mesmo certificado** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, nunca recriar chave, nunca debug. Preservar save MARCEK, Punto, Junkman, gráficos, física, PG-9076, 1920×1080, proteções térmicas e limite de FPS.
- Próximo passo: identificar via instrumentação em ponto **garantido de montagem da BMW** ou por dados de atributos a quantidade por categoria, preparando diagnóstico que não dependa de entrar em menu oculto. Somente então testar habilitação seletiva, com backup e fallback.

## Histórico
- `CONTEXTO_NFSMW.md` canônico no Drive permanece defasado até PRE237 na última leitura. Antes de anexar atualizações PRE238–271, criar backup íntegro e conciliar histórico. Não substituir histórico de 550 KB por esta síntese.
