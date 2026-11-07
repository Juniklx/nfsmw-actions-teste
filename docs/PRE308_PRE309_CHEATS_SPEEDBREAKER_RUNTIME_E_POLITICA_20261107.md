# PRE308–PRE309 — Continuação dos cheats Nitro, Speedbreaker e Dinheiro (2026-11-07)

## Base de evidência

- Log V40 enviado pelo usuário em 2026-11-07: 3.241 linhas, sessão anterior V39 e sessão V40 presentes no mesmo arquivo; observar carimbo de data/hora antes de agregá-las.
- PRE247 marcou **24 eventos de site 7 e 24 de site 8**, distribuídos em duas sessões. Todos usaram o mesmo endereço virtual guest `0xBFA7CD34`; **não interpretar como endereço estável entre dispositivos/sessões futuras**.
- Site 7: valores bits `0x3F8015D8` (20), `0x3F802BB1` (4); valores float cerca de 1,0006666–1,0013334. Site 8: `0x3F800000` (24) = 1,0. Sites 1–6 não apareceram nesse log; isso **não prova ausência das outras funções**. PRE247 usa limite máximo de 12 logs por site **por processo**, justificando 24 eventos nas duas sessões.
- O arquivo `pre247_pal_meter_passive_probe_patch.py` mapeia sites 1–5 para candidato `nitro`, campo +252 em `sub_82424AF0`; sites 6–8 para candidato `speedbreaker`, campo +132 em `sub_8246C2F0`. Os nomes são hipóteses estruturais, não identificação funcional confirmada em corrida.
- PRE308 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396222544 **AUDIT_OK** inspecionou o shard PAL `nfsmw_recomp.24.cpp` SHA-256 `e5cf7f0f0b7369615432845bbbfdcf0786f6a4646b0872dfb037fc6a6c320b71` (snapshot PRE99 autenticado). Stores identificados linhas relativas **115 (site 6), 148 (site 7), 158 (site 8)**.
- PRE308B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396360249 **success**, comprovou que site 6 subtrai um delta do campo +132, site 7 calcula/adiciona delta sob condição, e site 8 grava valor limitado após comparação. A sequência 7→8 próximo de 1,0 corresponde a ajuste e limitador; **não habilitar clamp de 1.0 nos sites 7/8 antes de identificar consumo de Speedbreaker na condução e capacidade efetiva**.
- PRE309 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396555371 **AUDIT_OK**, quatro grupos de verificações com C++ host. Código `automation/kaggle/pre309_cheats_optin_policy.hpp` e `pre309_cheats_optin_policy_mock.py`. Chaves `nitro`, `speedbreaker`, `money` iniciam desligadas; retorno do valor original quando qualquer gate falha; operações não-finitas ou fora do domínio não são alteradas; restauração de desligado validada. O campo Money é **pass-through intencional**, sem alteração ou pesquisa de saldo durante o teste.
- O PRE309 **não está conectado ao código do jogo**; a prova é somente C++ host, sem compilação Android/ARM64, nenhuma nova APK ou testes de cheats reais. Não afirmar três cheats funcionais.

## Contexto paralelo V40

- PRE305 V40 assinada e entregue no Drive, recebeu teste real no S24 FE: BMW modelo 41 abre categorias antes bloqueadas. Capturas mostram Nitro com rótulo/preço coerentes, Transmissão com `Option title`, `20/20` e preço `999.999.999`, sugerindo dados/índices inválidos **não atribuídos causalmente** sem diagnóstico de lookups. Não comprar/aplicar melhorias experimentais sem backup do save.
- Log trouxe `[NFSMW_PRE292_BMW_MENU] ... type=41`, `[NFSMW_PRE283_BMW_VTABLE]` em vários momentos, e novos registros de escrita/atualização do save `MARCEK`. Não afirmar integridade do save apenas porque ele abriu; preservar backup.
- Investigação da oficina suspensa por escolha do usuário. Priorizar cheats agora, sem desfazer o gate ou a versão V40.

## Próxima ação sugerida

1. Instrumentar/observar, **sem escrever valores**, a diminuição do medidor candidato +132 durante uso real do Speedbreaker, e +252 quando acionar Nitro; não depender somente de logs capturados no menu.
2. Associar esses eventos a contexto de jogo/veículo/edição e verificar se os campos são realmente usados para consumir recarga.
3. Só então integrar os gates PRE309 na árvore PAL isolada, com ativação explícita, modo padrão desligado, testes de regressão ARM64 e comparação com jogo não alterado. Não acrescentar acesso genérico à memória guest; utilizar somente contexto já calculado nos stores.
4. Dinheiro ilimitado exige validação do saldo e do contexto das oito gravações PRE239/246, incluindo débitos legítimos e proprietário do objeto, antes de qualquer mudança.
5. V41, se futura release experimental, deve incrementar versionCode para 41, manter package `io.github.nfsmwrecomp` e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Preservar V39/V40 e save `MARCEK`, 1920x1080, gráficos, controles, proteção térmica.

**Nenhum cheat funcional implementado ou testado no aparelho ainda.**
