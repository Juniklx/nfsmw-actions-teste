# PRE602_HANDOFF_PRE599_PRE601_PPC_GUEST_FALSE_POSITIVES_20261109

**Data:** 2026-11-09. **Projeto:** NFSMW-Recompiled-Mobile, V48 PRE452, BMW M3 GTR carreira. **Estado do telefone:** PRE592, aparentemente ainda aplicada; usuário confirmou carregamento MARCEK, mas não comunicou rollback ou hash atual dos arquivos.

## Evidência basal

PRE591 com contador BMW engine=0, nova coleção VLT e RefSpec ativo com dois itens carregou MARCEK (usuário; log SHA256 842fbc19031e81adb7988ad3e2fbd2de35850ce19abde581681025c4172ed1b9). PRE502/PRE573 estruturalmente idêntico exceto contador 1 falhou com aviso MARCEK corrompido; após rollback original o save carregou. PRE596 AUDIT_OK identificou a única diferença no VPAK: byte absoluto 256619 (inteiro big-endian em 256616, BIN relativo 256488). A hipótese principal continua contador 0→1 OU resolução/uso da segunda referência, sem causa guest comprovada.

## PRE599 — fonte PPC original autenticada

GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42581301120, AUDIT_OK. Relatório: docs/PRE599_BMW_GUEST_COUNTER_PPC_PROVENANCE_READONLY.json. Baixou fonte privada PRE99 (874780689 bytes; SHA256 af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39), auditou 129 arquivos gerados e 56338 funções, inspecionou oito funções por comentários PPC delimitados. Nenhum código fonte gerado completo publicado.

- sub_82203AB8 (nfsmw_recomp.59.cpp) leu os sete offsets 40,44,48,52,60,68,72 em sequência no mesmo registrador com stores posteriores; tem aspecto de cópia/marshalling, NÃO prova GetMaxLevel.
- sub_82752E10 (nfsmw_recomp.98.cpp) também leu sete campos e alternou stores, sem chamadas guest; outro falso positivo para a heurística de GetMaxLevel.
- sub_82582F70 (nfsmw_recomp.11.cpp) tem três padrões lwz 40(rX) seguidos de mtctr e bctrl, típicos de slot de chamada virtual, NÃO prova que a origem seja pvehicle.engine_upgrades.

## PRE600 — varredura quantitativa e triagem

GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42581735543, AUDIT_OK. Relatório: docs/PRE600_GUEST_COUNTER_BRANCH_CANDIDATES_READONLY.json. Percorreu 129 fontes/56338 funções. Encontrou 1587 acessos lwz no offset decimal 40 em funções compatíveis com o padrão textual pesquisado (não se podem classificar esses acessos como motor). Destes, 193 tinham forma de dispatch indireto mtctr/bctrl. 512 outros padrões combinavam comparação e desvio condicional, mas sem prova de objeto pvehicle ou função GetMaxLevel.

O cruzamento apenas dos 30 candidatos mais bem ranqueados pela PRE600 com os 80 candidatos anteriores da PRE487 selecionou sub_8216A928 e sub_821EFC18. Não declarar esse cruzamento como exaustivo entre os 512 padrões.

## PRE601 — correção de dois candidatos falsos positivos

GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42582195386, AUDIT_OK. Relatório: docs/PRE601_TWO_GUEST_COUNTER_FUNCTION_CALLERS_READONLY.json. Autenticou novamente o PRE99; analisou contexto PPC e chamadores nomeados de ambas as funções em todo o conjunto gerado.

- sub_8216A928 (nfsmw_recomp.59.cpp, 221 linhas de função): lê offset 40(r31) em r3, testa ponteiro contra zero, acessa memória em 0(r3), extrai destino da vtable e realiza mtctr/bctrl. Comportamento é de ponteiro/objeto, não de limite numérico de motor. Um único chamador direto nomeado foi observado: sub_8216A8C0 (nfsmw_recomp.16.cpp). Isso não descarta chamadas indiretas.
- sub_821EFC18 (nfsmw_recomp.31.cpp, 144 linhas): começa com r31=r3, lê offset 40(r31) para r11, compara r11 com zero; quando não nulo, executa stw r30,8(r11) e chama sub_821E5508 com esse objeto. Comportamento também de ponteiro/objeto, não limite motor. Zero chamadores diretos nomeados no padrão pesquisado, sem excluir chamadas indiretas.
- Ambas as candidatas GetMaxLevel anteriores foram rebaixadas. GetMaxLevel, SetLevel, pvehicle base-pointer provenance e guest lookup da segunda referência NÃO foram identificados; não substituir a falta de prova por guesses de função.

## Próxima abordagem

Pesquisar proveniência real de ponteiro de pvehicle a partir de usos e lookups específicos autenticados, em vez de qualquer lwz offset 40 em objeto desconhecido. Considerar separadamente exigência de registro da nova coleção de motor na StrE/Export (PRE499 indicava que hash/nome da coleção sintética não consta na StrE original) e a validação da segunda referência quando pvehicle engine count passa a 1. A causalidade exata permanece não provada. Não reaplicar o pacote combinado PRE573, não gerar V49 por hipótese, não promover tunagem BMW como comprável, instalada, física ou persistente.

Antes de qualquer novo teste no Samsung Galaxy S24 FE, confirmar estado PRE592 e fechar V48; restaurar usando o script específico pre592_restore_bmw_refspec_pointer_only_shevery.sh, exigindo PRE592_RESTORE=ORIGINAIS_VERIFICADOS. Não executar rollback remotamente nem apagar MARCEK.

## Preservações

APK release V48 PRE452, package io.github.nfsmwrecomp, SHA256 certificado 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b, Nitro PRE398, PG9076/touch, resolução interna 1920x1080, qualidade completa e proteções térmicas. Cap desejado 120 FPS, cap observado nos logs 60. PRE599/PRE600/PRE601 não alteraram dados do jogo, save, APK, credenciais nem certificação. O arquivo original PRE99 foi inspecionado de maneira temporária, sem publicar fonte gerada.
