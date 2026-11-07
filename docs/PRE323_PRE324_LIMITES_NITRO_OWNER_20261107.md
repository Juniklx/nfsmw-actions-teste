# PRE323–PRE324: limites do Nitro e rastreamento da origem do objeto (2026-11-07)

## PRE323 — Verificado
GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42403902852 terminou `success`, e script de auditoria PAL autenticada retornou `PRE323_STATUS AUDIT_OK`. Fonte `sub_82424AF0` preservada, sem APK/build/alteração de guest.

- **Ponteiro do objeto:** `r31.u64 = ctx.r3.u64` (linha relativa 32). O código registra somente que o objeto vem do primeiro argumento, não se ele é do jogador.
- **Limite inferior:** `f30` é carregado via `lfs f30,-4788(r28)` (linhas 97–100) de dados globais. Auditoria não leu o float final do jogo, portanto valor numérico ainda sem prova.
- **Capacidade/limite superior:** `f28` carrega inicialmente `lfs f28,156(r28)` (linhas 289–292) e recebe modificação `fadds f28,f0,f28` (linha 405) no caminho de consumo; não assumir `1.0` como limite estático em todos os cenários.
- **Stores já confirmados PRE322:** 1 calcula subtração, 2 aplica clamp inferior; 3 calcula adição, 4 aplica clamp superior; site 5 caminho alternativo de `f30`. Não é adequado substituir todas as cinco gravações.

PRE323B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42404018936 exibiu trechos limitados da função, conferindo as linhas acima. Leitura de código não comprova legitimidade da escrita em todas as fases do jogo.

## PRE324 — Atribuição do proprietário em investigação
Workflow https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42404187781 iniciado: examina somente o snapshot PRE99 PAL autenticado, buscando referências explícitas a `sub_82424AF0`, para identificar caller/objeto quando houver. Limitação antecipada: chamadas indiretas/vtable podem não conter referência textual.

**Critério de segurança para ativação:** é necessário estabelecer ao menos alvo semântico, owner do jogador, capacidade legítima, ativação explícita OFF por padrão e modo OFF estritamente idêntico à lógica do jogo. PRE309 existe como política C++ sintética, ainda não conectada ao Android. Nenhum cheat real habilitado na V41; nenhuma V42 gerada neste passo.

Preservar chave permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`, save MARCEK, V39/V40/V41, gráficos/controles/termal.
