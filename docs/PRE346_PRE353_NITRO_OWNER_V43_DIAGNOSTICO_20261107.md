# PRE346–PRE353: investigação do owner Nitro e V43 de telemetria individual (2026-11-07)

## PRE346 — busca textual independente no snapshot PRE99
- GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42421838788, job `128551732581` `completed/success`.
- Artefato `13593273459` aberto, JSON `PRE346_PLAYER_CAR_SOURCE_REFERENCES.json`, status `AUDIT_OK`.
- Fonte PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39` autenticada.
- **1.134 arquivos nativos escaneados**, **0** arquivos com nomes explícitos `player car / player vehicle` e equivalentes nos diretórios examinados, excluindo código gerado e dependências terceirizadas.
- A ausência de nomes lexicais é **inconclusiva** quanto à existência de um ponteiro do jogador, pois o código recompilado pode não preservar símbolos semânticos.

## PRE348–PRE350 — observação individual sem mutação
- PRE348: `automation/kaggle/pre348_nitro_slot_values.hpp` mantém contagem por site (1–5) **e slot (1–16)**, em checkpoints com potências de dois, guardando apenas bits float já escritos; **sem ler ou alterar guest memory**.
- `pre336_nitro_address_diversity.hpp` recebeu apenas `lookup_slot(guest_address)`, que consulta a tabela já registrada. `slot=0` permanece desconhecido/overflow.
- PRE349: `automation/kaggle/pre349_nitro_slot_value_staging.py` injeta passivamente a PRE348 **após a PRE337** no callback de trace PRE247, com reversão exata e checagem de 0 alterações em `REX_STORE_U32`/`REX_LOAD_U32`.
- PRE350 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42422168386, job `128552726040`, `completed/success`: mocks Python, C++ e compilação `g++ -std=c++17` do callback composto concluídos. **Esses testes não validam, isoladamente, o link ARM64 do jogo nem a execução no aparelho**.
- Como os valores são publicados por slot, a V43 poderá revelar se slots de múltiplas instâncias consomem Nitro em paralelo; isso **não identifica automaticamente qual é o player**.

## PRE352 — V43 diagnóstica assinada — verificar estado
- Derivada do builder PRE340 da V42: `automation/kaggle/pre352_build_signed_v43_nitro_slot_values_passive.py`.
- `versionCode=43`, pacote `io.github.nfsmwrecomp`, nome planejado `NFSMW_V43_PRE352_NITRO_SLOT_VALUES_PASSIVE.apk`.
- Chave e certificado permanente da V42 mantidos, SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, verificação obrigatória.
- Novo marcador `NFSMW_PRE348_NITRO_SLOT_VALUES` exigido no `libmain.so` e na APK, além dos marcadores PRE316/PRE336, C3/BMW, todas as bibliotecas, shaders e pacote prévio.
- PRE352 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42422376260, job `128553361644`. **Estado na última consulta antes deste documento: ainda `in_progress`**, não declarar APK compilada/assinada nem upload validado.
- Disparo commit `b11caa34645918730a3a11fc9aeee84f293f3435`. Readback PRE353 `docs/generated/PRE353_PRE352_RUN_STATUS.json` permite localizar run ID, mas não comprova APK.

## Plano de teste quando a V43 estiver validada
1. Preservar backup externo do save `MARCEK`. Instalar atualização **sobre a V42, sem desinstalar ou apagar dados**; só após conferência independente de APK, assinatura e versionCode.
2. Testar exploração livre com apenas veículo do jogador; usar Nitro por alguns segundos e deixar recarregar. Registrar janela temporal.
3. Testar corrida com quatro carros (jogador+3 IA): ficar inicialmente sem Nitro próprio durante período conhecido, depois pressionar e soltar Nitro em intervalos identificáveis; coletar log completo. Preferir gravar manualmente a sequência de ação sem presumir que IA não usa Nitro.
4. Comparar PRE336 (diversidade) e PRE348 (floats por slot e site) dentro de cada sessão. **A resposta a comandos humanos produz apenas inferência contextual, não player owner semanticamente verificado** se IA ou outros sistemas também acionam a rotina.
5. Não ativar cheat que modifique a função `sub_82424AF0` em todas as instâncias. Buscar referência independente, verificável e teste negativo IA para qualquer mudança player-only.

## Estado de segurança
- Nitro infinito, Speedbreaker infinito e dinheiro ilimitado permanecem desativados.
- Nenhuma alteração deliberada de comportamento de consumo; nem gráficos (1920x1080), controles PG-9076/touch, shaders, física, limites térmicos ou save.
- V41 e V42 permanecem artefatos de referência. Próxima versão deve sempre incrementar versionCode, manter certificado original, evitar recriar chave.
