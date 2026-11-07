# PRE336 — Sonda passiva limitada de diversidade dos endereços do Nitro (2026-11-07)

## Motivação verificada
- PRE329/PRE330 viram `0xBFA9E7FC` em sites 1–4 durante quatro grupos do log V41, mas PRE247 limita a 12 registros/site/processo.
- PRE323 e PRE334 confirmam que o primeiro argumento da função PAL `sub_82424AF0` é usado como base para o medidor `+252`; não identificam o veículo do jogador.
- A auditoria do primeiro trecho da função PRE323 documenta chamadas virtuais via `r31+88`/slot `+44` e `r31+72`/slot `+152`. Não interpretá-las como prova de owner.

## Nova peça PRE336
- Cabeçalho `automation/kaggle/pre336_nitro_address_diversity.hpp`: monitor C++ host-only que **recebe apenas o destino de store já calculado**, sem desreferenciar memória guest nem alterar a escrita do jogo.
- Registra até 16 endereços distintos por processo e bitmask dos sites 1–5 associados a cada endereço. Publica apenas número da posição (identidade efêmera por processo), cardinalidade e contadores, **nunca endereços brutos**.
- Se houver mais de 16 endereços, aciona `overflow` e se recusa a classificar o destino em uma das posições existentes (fail-closed); nenhuma classificação de jogador/IA é implementada.
- Entradas site 0, site >5, endereço zero e sentinela 0xffffffff são rejeitadas. Checkpoints com limite logarítmico por site evitam logging por store.
- Teste C++ nativo `automation/kaggle/pre336_nitro_address_diversity_mock.cpp` cobre um endereço usado pelos sites 1/2/3, introdução de segundo objeto e sites independentes, preenchimento dos 16 slots, 17º endereço, rejeição de entradas inválidas e conservação do estado de owner como não verificado.
- Workflow `.github/workflows/nfsmw-pre336-nitro-address-diversity-mock.yml` compila o mock com g++ -std=c++17 -O2 -Wall -Wextra -Werror -pthread. Disparo via commit `aa844e88759bb87d5a1c1742a328f570357cff37`. Status permitido pelo PRE328 em `docs/generated/PRE328_PRE336_SANITIZED_STATUS.json`.

## Alcance e critérios de segurança
- **PRE336 é somente protótipo host-only; não foi integrado ao callback PRE247, não foi compilado em APK e não faz instrumentação no Galaxy S24 FE.**
- Até a validação C++ do CI, os mocks têm status **pendente**. O commit de trigger não equivale a sucesso do teste.
- Mesmo que dois endereços sejam observados, isso apenas sugere diversidade de objetos. Um único endereço observado não demonstra que NPC/IA não tem Nitro, nem que pertence ao jogador.
- Antes de integrar em eventual APK diagnóstica, confirmar regra de amostragem, ausência de impacto operacional, bind original do callback e teste real controlado; nunca usar endereços hardcoded.
- Ainda se exige referência **independente** do veículo do jogador para classificar owner. Sem essa referência, `owner_verified=false` é obrigatório e **não habilitar cheats**.

## Integridade
Não foram criados APK V42, patches de stores, alterações no save `MARCEK`, chave de assinatura, controles PG-9076, gráficos, física ou restrições térmicas. V41 segue referência.
