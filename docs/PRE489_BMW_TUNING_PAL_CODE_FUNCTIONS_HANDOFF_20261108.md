# PRE489_BMW_TUNING_GUEST_CODE_HANDOFF_20261108

**Data:** 2026-11-08  
**Escopo:** continuidade da modificação de tunagem real da BMW M3 GTR no NFSMW Xbox 360 PAL recompilado para Android, a partir do PRE484. **Nenhuma APK com essa capacidade foi produzida.**

## Base imutável

- APK estável V48 PRE452, assinatura permanente, Nitro infinito PRE398, controles PG-9076, renderização/física original e save do usuário `MARCEK` preservados.
- O VPAK do `GLOBAL\\ATTRIBUTES.BIN` PAL do usuário tem SHA-256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`, idêntico ao USA para esse arquivo (PRE467).
- O usuário solicitou capacidade de comprar/instalar upgrades **verdadeiros** para BMW; apenas mostrar opções no menu não satisfaz o objetivo. Módulo de guarda C++ PRE479 e simulação transacional PRE483 permanecem offline e desligados.

## PRE485 — catálogo integral de funções convidadas (PAL PRE99)
- [Run 42515287736](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42515287736) `AUDIT_OK`.
- Fonte autenticada do próprio usuário: PRE99 `tar.gz` 874.780.689 bytes; SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Leitura em memória de **129** fontes geradas, indexando **56.338** funções convidadas; nenhum arquivo de jogo ou código gerado foi publicado.
- `sub_82582F70` é a única chamadora direta identificada de `sub_8256F818` (construtor de opções de garagem já instrumentado). `sub_8256F818` chama `sub_823E5988` duas vezes. `sub_823E5988` possui **18 chamadoras** distintas e resolve um valor de atributo, retornando zero em caminhos específicos (PRE456).
- **477 funções** atenderam a critério amplo de quatro ou mais offsets coincidentes. Esse resultado é *heurístico*, não prova identificação de física.
- Relatório `docs/PRE485_ORIGINAL_PAL_UPGRADE_CALL_GRAPH_CANDIDATES_READONLY.json`.

## PRE486 — agrupamento por registrador e contagem de chamadas
- [Run 42515573950](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42515573950) `AUDIT_OK`, mesmas 129 fontes/56.338 funções.
- **969** candidatos estruturais após combinar acessos agrupados por registrador e chamadas repetidas; **158** usam pelo menos cinco dos sete offsets por registrador.
- `sub_82582F70`, `nfsmw_recomp.11.cpp`, 1.231 linhas: chama ambas `sub_8256F818` e `sub_823E5988`; tem código de menu amplo, mas nenhum nome de função de física comprovado.
- `sub_82142B38` e `sub_82141B48` tocam todos os offsets num mesmo registrador com instruções `stw` — comportamento de preenchimento/inicialização, não prova de `GetMaxLevel`.
- Relatório `docs/PRE486_PAL_GUEST_UPGRADE_REGISTER_CANDIDATES_READONLY.json`.

## PRE487 — separação READ/WRITE
- [Run 42515778816](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42515778816) `AUDIT_OK`; 34 funções fazem leituras `lwz` de cinco ou mais offsets em mesmo registrador, sem incluir `r1` pilha. Os rankings têm **70** candidatos combinados após filtros, incluindo padrões de leitura de `Package`.
- Exemplos *não confirmados* de leituras de sete offsets no mesmo registrador: `sub_82203AB8`, `sub_82752E10`, `sub_82694EC0`. Esses padrões também ocorrem em tipos genéricos, logo não rotular como `Physics::Upgrades::GetMaxLevel`.
- `sub_823E5988` consulta descritores dinamicamente; a ausência de acessos diretos aos sete offsets não a exclui como implementação do getter relevante.
- Relatório `docs/PRE487_PAL_PHYSICS_UPGRADE_READ_WRITE_CANDIDATES.json`.

## PRE488 — vizinhança da consulta de nível
- [Run 42515970372](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42515970372) `AUDIT_OK`, análise de 14 funções convidadas selecionadas, com instruções PPC, contagem de gravações e dependências, sem publicar código-fonte gerado completo.
- `sub_823E5988` consulta atributo; já demonstrada relação com as contagens da oficina, mas **nome semântico GetMaxLevel ainda não confirmado**.
- `sub_823E5AA0`: 65 linhas; chama `sub_823E5988`, depois registra um valor de `r3` em `0(r30)` e chama `sub_823E4370`; pode ser adaptador de consulta, ainda não identificado.
- `sub_823E5B08`: 1.457 linhas; chama `sub_823E5988`, `sub_823E4850`, `sub_823E5420`, entre outros; contém muitas operações de acesso/gravação e interações complexas com atributos, **mas não está comprovada como SetLevel ou SetPackage**.
- `sub_823E6560`: 338 linhas; chama `sub_823E41C0`, `sub_823E5420`, `sub_823E5988` e `sub_823E5B08`; sete chamadores identificados. Sua função precisa ainda não foi determinada.
- `sub_823E67E8`: 545 linhas; chama `sub_823E5988` e `sub_823E5B08`, além de outras rotinas; também requer identificação antes de qualquer hook.
- Essas chamadas são **evidência de dependência, não de equivalência funcional**. Na fase atual, as assinaturas e as rotas de escrita ainda não foram validadas em execução, e não se deve produzir uma V49 habilitando tunagem.
- Relatório `docs/PRE488_PAL_UPGRADE_FUNCTION_NEIGHBORHOOD_READONLY.json`.

## Fonte de referência auxiliar
- Repositório `dbalatoni13/nfsmw`, `src/Speed/Indep/Src/Physics/PhysicsUpgrades.hpp` expõe as declarações `GetMaxLevel`, `GetLevel`, `SetLevel`, `SetPackage`, `GetPackage` e `Package.Part[7]`, porém `PhysicsUpgrades.cpp` está vazio. Os endereços da edição PC NÃO são transferíveis para PAL Xbox. Esta fonte documenta interfaces e não valida execução.
- O fluxo de `CarCustomizeManager::InstallPerfPkg` na mesma referência aplica `SetPackage` e tem reversão que pode zerar nível, justificando a proteção offline PRE483.

## Próximo passo verificável
1. **PRE490**: desambiguar funções `sub_823E5B08`, `sub_823E6560`, `sub_823E67E8` por análise detalhada de registradores de argumentos `r3-r6`, instruções que mutam atributos, condições de retorno e padrões de chamadas no **código PAL autenticado**. Conferir se alguma corresponde efetivamente a `GetLevel`, `SetLevel` ou `SetPackage`, sem rotular antes de prova.
2. Mapear identidade real `type=41` ↔ `pvehicle bmwm3gtr` em **runtime sem escrita**, com controle Punto type74; não aplicar ao carro de prólogo por acidente.
3. Projetar os perfis físicos BMW de nível 1–N com dados de engenharia provados, preços `FECarPartInfo` reais e roundtrip em save descartável; se faltar catálogo, permanecer OFF.
4. Integrar somente após testes seguros no runtime, mantendo Nitro, físico e save original. A versão V48 permanece baseline.

**Garantia:** PRE485–PRE488 fizeram apenas leitura de fonte autorizada e gravaram scripts/relatórios privados. Nenhum arquivo de jogo, save `MARCEK`, APK, biblioteca ou chave de assinatura foi modificado. Ainda não há tunagem funcional na BMW.
