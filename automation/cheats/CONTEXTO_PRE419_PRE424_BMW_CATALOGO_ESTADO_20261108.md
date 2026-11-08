# NFSMW — BMW M3 GTR: auditorias PRE419–PRE424 (2026-11-08)

## Escopo e baseline
- Projeto NFSMW-Recompiled-Mobile, BMW M3 GTR Razor no save MARCEK, car #82. Em uso, o bypass de menu PRE305/V40 tornou acessíveis Peças/Desempenho, mas a tela de Transmissão exibiu `Option title`, `20/20` e `999.999.999`. **Não comprar opções inválidas**.
- Baseline V46 PRE401, versionCode 46, pacote `io.github.nfsmwrecomp`, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, Nitro global comprovado por teste de usuário e log. Certificado de assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Todas as auditorias abaixo são **read-only**, contra arquivo PRE99 autenticado, sem APK/save/patcheamento/assinatura.

## Evidências verificadas
- PRE419: [run 42448274903](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42448274903), `PRE419_STATUS AUDIT_OK`; retificou caminho do helper: `sub_8256F818` no `nfsmw_recomp.57.cpp` e chamada em `sub_82582F70` linha relativa 696.
- PRE420: [run 42448680708](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42448680708), `PRE420_STATUS AUDIT_OK`; corpo do helper `sub_8256F818` tem 230 linhas; inicializa objetos de 44 bytes, associa flags de verificações e encadeia elementos em lista.
- PRE421: [run 42449552113](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42449552113), `PRE421_STATUS AUDIT_OK`; `sub_82582F70` usa sentinela da lista local na pilha, chama `sub_8256F818` e percorre/remove nós para processá-los. Ainda não há contagens reais de upgrades da BMW.
- PRE422: [run 42450058794](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42450058794), `PRE422_STATUS AUDIT_OK`; buscou símbolos e textos em 12.682 arquivos; 34 correspondências, todas em bibliotecas de terceiros, por substrings numéricas ou dados não relacionados. A busca não provou um símbolo nomeado `GetPerformancePartsList` no código gerado.
- PRE423: [run 42450444929](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42450444929), `PRE423_STATUS AUDIT_OK SCANNED 2060 MATCHED 17`; cruzou os endereços com `nfsmw_funcs.h`, `nfsmw_init.cpp`, `nfsmw_register.cpp`, `codegen.partition.json`. Os mapas registram endereços numéricos, não os nomes de alto nível.
- PRE424: primeira tentativa [42450728963](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42450728963) resultou `PARTIAL`/0 pontos por regex com escape indevido. Corrigido e executado novamente no [run 42450782110](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42450782110): `PRE424_STATUS AUDIT_OK`, duas chamadas esperadas verificadas. `sub_82581BD8` (`nfsmw_recomp.91.cpp`, 171 linhas, chama `sub_82582F70` na linha relativa 157). O chamador inicializa numerosos campos do objeto antes da chamada; **aparenta inicialização/constructor**, sem provar o nome de alto nível. `sub_82582F70` (1231 linhas) chama `sub_8256F818` na linha relativa 696.

## Relação com a fonte decompilada e cautelas
- PRE278 ([contexto do PRE278](CONTEXTO_PRE278_BMW_TUNING_EMPTY_LIST_REFRESHHEADER_20261107.md)) correlacionou a lógica pública de `CustomizePerformance::Setup()`, que chama `GetPerformancePartsList` e, depois da iteração, `RefreshHeader`, com o fluxo PAL `sub_82582F70`. A correlação estrutural **não substitui resolução definitiva de símbolo**.
- PRE279–281 ([contexto](CONTEXTO_PRE279_PRE281_BMW_TUNING_NULL_GUARD_20261107.md)) apontaram despacho virtual e risco potencial de seleção nula. Não há crash comprovado nem certeza de que esses guardas resolvam opções inválidas.
- A hipótese de lista vazia **não foi validada** para a BMW; não há valores observados de `GetMaxLevel`, identificação por categoria ou vinculação segura de pacote/título/preço.
- `sub_82581BD8` chamar setup após inicializar objeto é consistente com um construtor; isto não elimina a possibilidade de setup construir a lista de peças.

## Próxima etapa recomendada
1. Focar em obter **evidência passiva dos níveis efetivos por categoria** (`GetMaxLevel`) e das propriedades/títulos de cada opção, idealmente contrastando BMW e Fiat Punto, sem chamadas artificiais nem mutação de atributos.
2. Antes de qualquer futura APK, confirmar a árvore de fonte atual, a edição PAL/PT-BR realmente utilizada, os patches presentes e os pontos exatos de instrumentação para não repetir tentativas antigas.
3. Qualquer V47 futura: versionCode >46, mesmo certificado permanente, sem assinatura debug, preservar V46, saves, Nitro global, controle, 1920×1080, shaders/física e limites térmicos. Nunca comprar/confirmar peças com preço ou título inválidos.
4. Atualizar `CONTEXTO_NFSMW.md` no Drive apenas com backup e reconciliação de marcos PRE409–PRE424; na consulta de 2026-11-08 o texto disponível terminava em PRE408. Não afirmar que o Drive foi atualizado por esta nota.
