# PRE333 — Referências cruzadas à assinatura estrutural do Nitro, PAL PRE99 (2026-11-07)

## Resultado confirmado
- GitHub Actions run: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42411376197
- Job `128520060406` terminou `completed/success`; relatório interno `PRE333_STATUS AUDIT_OK`, snapshot PRE99 autenticado e 129 shards PAL verificados.
- Artefato GitHub `13589213971` baixado e inspecionado. Resumo `docs/generated/PRE328_PRE333_SANITIZED_STATUS.json` retorna `candidate_count=315`, `candidate_functions=301`, `candidates_truncated=true`, `owner_verified=false`.
- Scanner: `automation/kaggle/pre333_pal_nitro_layout_xrefs_readonly.py`. Critério: pelo menos 3 offsets da lista {52,72,88,252,296} usando mesmo registrador-base dentro de uma função, ou 2 offsets incluindo 252; não interpreta os tipos das estruturas.

## Assinatura Nitro de referência
- `sub_82424AF0`, shard `nfsmw_recomp.66.cpp`, base `r31`, encontrou todos cinco offsets `[52,72,88,252,296]`, conforme fonte autenticada PRE323.
- Outras cinco entradas tinham todos cinco offsets também: `sub_822040B0` (base `ctx.r11`), `sub_825904F0` (base `r31`), `sub_8270BF50` (base `r31`), `sub_82719CB0` (base `r31`) e `sub_828A61D8` (base `r31`). **São coincidências estruturais candidatas, não classes/callers do Nitro verificados.**
- A lista de 90 melhores resultados possui 6 entradas com cinco offsets, 14 com quatro, 70 com três. Arquivo completo tem 315 entradas, então o conjunto de 90 é truncado.

## Crítica metodológica
- A ocorrência numérica do mesmo offset em código recompilado é muito comum (inclusive campos de stack ou estruturas não relacionadas).
- O critério ainda **não verificou tipos/semântica de ponteiro, se `r31` vem de `ctx.r3`, ou se há leitura/escrita em float em `+252`**. Portanto, 315 hits NÃO equivalem a 315 possíveis objetos Nitro.
- Não usar essa busca para afirmar player owner ou habilitar cheat. É preciso qualificar os seis candidatos que compartilham cinco offsets com condições de fluxo de dados mais estritas.

## Próximo gate
- Auditoria direcionada aos seis candidatos para checar origem do registrador-base e padrão específico de `REX_LOAD_U32`/`REX_STORE_U32` no campo `+252`.
- Após eliminar coincidências estruturais, exigir referência independente ao veículo do jogador e controle negativo com NPC antes de qualquer implementação Nitro infinito.

## Integridade
Nenhum patch, APK, assinatura, save `MARCEK`, controle ou configuração gráfica/térmica foi alterado pela PRE333. V41 permanece referência e nenhuma V42 foi gerada.
