# NFSMW Android — PRE272: busca do ponto seguro após inicializar BMW em tuning (2026-11-07)

## Contexto
- Perfil MARCEK: BMW M3 GTR normal adicionada pelo save PRE260 e dirigível, relato do usuário. Tuning só mostra Visual; bloqueio HeroCar em menu PAL demonstrado PRE261–264. V37 ainda é a APK instalada e preservada.
- PRE269/270: consulta de níveis via `sub_823E5988` PAL, correspondente forte a `Physics::Upgrades::GetMaxLevel`, devolve 0 se categoria não corresponde e obtém valor de tabela de atributos. `sub_8256F818` consulta esse helper e não cria pacotes se retorno <=0. `sub_8256CB60` retorna 3/4 níveis máximos genéricos, -1 fora 0–6.
- PRE271 (sucesso): sonda passiva **somente em memória**, desligada por padrão, 3 saídas instrumentáveis, zero novas leituras/escritas guest, host mock limita 56 logs. **Não prova que GetMaxLevel será chamado enquanto BMW tem menu bloqueado; não houve APK nova.**
- Objetivo PRE272: localizar rotina de inicialização do carro quando usuário entra no tuning, para poder futuramente medir sete categorias mesmo sem mostrar Peças/Desempenho. Referência da decompilação: `CarCustomizeManager::TakeControl()`, que recebe `TuningCar`, prepara `ThePVehicle` via `WriteRecordIntoPhysics` e depois permite abrir menus.

## Resultado PRE272
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42324803450 — **success**, `PRE272_STATUS AUDIT_OK`.
- Scanner hash-autenticado PRE99 percorreu C++ gerado PAL e classificou por heurística **106 funções candidatas**, incluindo referências ao objeto global do manager `0x82C5D9E8` (código PPC `lis ...,-32058` / `addi ...,-9752`), chamadas às funções `sub_8256*`, e stores em campos próximos. Relatório inicial registra top pontuação `sub_8256F818`, `sub_82578AB8`, `sub_82582F70`, `sub_8256F2F8`, `sub_82576DD0`, `sub_82577248`.
- **Importante:** pontuação alta de `sub_8256F818` é falso positivo para TakeControl: essa rotina já foi correlacionada à montagem de listas de performance. As demais pontuações **não demonstram** que `TakeControl()` foi identificado. Nenhuma alteração de código ou teste Android foi realizada; não usar esses nomes em patch sem confrontar o fluxo.
- Dados do relatório PRE272: https://drive.google.com/file/d/1E5KjXHXijd2fCcTFPmHMz4EqfXTex0lW/view

## Próximo trabalho recomendado
1. Reduzir candidatos com cruzamento de chamadas de `CustomizeMain::CustomizeMain` e campos efetivamente gravados por `CarCustomizeManager::TakeControl`, não só score do endereço global.
2. Com função identificada, verificar que `ThePVehicle` foi inicializado e que é o BMW de carreira, não o carro `M3GTRCAREERSTART` de prólogo; só então planejar medição no instante seguro.
3. Antes de ativar menu principal, proteger `CustomizePerformance::RefreshHeader` de lista vazia; uma opção zero gera retorno `GetMaxLevel <=0`. Nenhum pacote específico da BMW foi medido até agora.
4. Manter APK V37, save MARCEK, Punto, Junkman, shaders, física, toque/PG-9076, 1920×1080, FPS, proteções térmicas e `NFSMW_PRE194_C3` inalterados.
5. Futuras builds `versionCode>=38` com pacote `io.github.nfsmwrecomp` e **mesmo** certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, sem recriar chave e sem assinatura debug. Não afirmar V38 pronta.
6. Consolidar esta nota no `CONTEXTO_NFSMW.md` do Drive somente depois de backup e conciliação de histórico a partir da PRE238. A cópia canônica consultada estava desatualizada na PRE237.

## Evidências e limitações
- PRE272 só fez varredura estática autenticada, sem material privado de assinatura ou saves, sem APK compilada/assinada, sem ativar cheats.
- A busca por `TakeControl()` ainda não está concluída. Alteração de menu BMW permanece bloqueada até validação.
