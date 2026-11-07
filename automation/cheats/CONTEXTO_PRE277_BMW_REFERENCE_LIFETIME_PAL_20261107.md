# NFSMW Android — PRE277: análise do ciclo de referências dos atributos PAL (2026-11-07)

## Estado do projeto que esta etapa respeita
- Na V37 Android `io.github.nfsmwrecomp`, usuário confirmou que a BMW M3 GTR **normal**, incluída via save PRE260 no perfil MARCEK, pode ser selecionada e dirigida. No tuning BMW, somente a categoria Visual aparece. O bloqueio de Peças/Desempenho é coerente com `IsHeroCar`, analisado PRE261–264.
- PRE269–276 encontraram o caminho `sub_8256F818` → `sub_823E5988` (candidato a `Physics::Upgrades::GetMaxLevel`), mas os níveis reais de pacotes BMW no aparelho **não foram obtidos**. PRE275–276 encontraram gravações guest `+18`; não é seguro considerar esse caminho livre de efeitos laterais.
- V37, save MARCEK, Punto, Junkman, demais perfis, APKs antigos e assinatura permanente não foram modificados nesta etapa.

## PRE277 — auditoria executada e evidência
- **GitHub Actions `42326983611`: sucesso**, log `PRE277_STATUS AUDIT_OK`; https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42326983611
- Script reproduzível `automation/kaggle/pre277_bmw_attribute_ref_lifetime_readonly.py`, workflow `.github/workflows/nfsmw-pre277-bmw-attribute-ref-lifetime-readonly.yml`; leitura do PRE99 autenticado (SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`). 131 shards PAL examinados.
- **`sub_821485E8`** em `nfsmw_recomp.87.cpp` (SHA256 `6f6b5dcf9dd23be3e5e6c0aa441e9b7d7c61d78a640f2a0b2a51ab7e6324d226`), 175 linhas: **4 gravações guest**, todas endereçadas a `ea` ou `r28+0`, portanto não todas comprovadamente fora da pilha. Das 4, três gravam ponteiro encontrado ou 0 no endereço fornecido pelo chamador `r28+0`. Chamadas diretas `sub_821464C0` e `sub_821465F0`. O comportamento sugere busca por registro em uma árvore/tabela e devolução por parâmetro; a classificação exata de estrutura não está comprovada.
- **`sub_8214E928`** em `nfsmw_recomp.16.cpp` (SHA256 `9e4d89c6760f54efdf635d91cb5e682702b3ce0fa7344e997b23dfea5dfd98b4`), 91 linhas: **10 stores guest** (3 de frame direto de pilha, um `ea` potencial stack e 6 endereços não-classificados como pilha); estrutura de 16 bytes escrita nos deslocamentos `r31+0/4/8/12`, consulta `sub_82145C50` em ramo condicionado; **1 escrita U16 em `r30+18` com `lhz r11,18(r30); addi r6,r11,1; sth r6,18(r30)`**. Este bloco incrementa em 1 o contador da estrutura apontada por `r30` quando não nula. Uso como *reference count* é hipótese plausível, **não prova pareamento de ciclo de vida em todos os ramos**.
- O pai `sub_82148718` mantém 13 stores guest, inclusive U16 em `r11+18`, `r8+18`, e chamadas dos dois auxiliares acima. `sub_8214E9E0` inclui duas escritas U16 em `r11+18`. A PRE277 não provou o balanceamento de todas essas operações.
- Relatório JSON de auditoria, sem save pessoal e sem material privado, arquivado no Drive: https://drive.google.com/file/d/1kePSF9sXPo66-efqL6ABO5Z85iY2oDa6/view
- O GitHub Actions aprovou **a auditoria de somente leitura**, não a segurança de alterar o jogo. `PRE277_REFERENCE_BALANCED False` significa **ausência de comprovação**, não bug de vazamento comprovado. `PRE277_EXTRA_CALLS_SAFE False` permanece.

## Próxima decisão recomendada
1. **Não** adicionar chamadas novas `GetMaxLevel` a partir de `TakeControl` (PRE273); os dois novos auxiliares reforçam que o código manipula estruturas mutáveis.
2. Para aproximar solução do tuning BMW, evitar busca infinita pela cadeia de *refcount*: investigar **a seleção de pacote já existente e os caminhos para lista vazia** (`GetPerformancePartsList` → `GetSelectedPart` → `CustomizePerformance::RefreshHeader`) no PAL. Desenhar guarda contra seleção nula, sem invocar `GetMaxLevel` artificialmente.
3. Alternativamente, buscar offline dados de atributos do modelo BMW e números de upgrades sem executar funções guest; sem esses dados, **não inventar valores**.
4. Uma futura V38 exigirá teste controlado, versionCode **>=38**, certificado permanente **exatamente** SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; manter package `io.github.nfsmwrecomp`, resolução 1920×1080, gráficos, efeitos, física, FPS cap atual, PG-9076 e limites térmicos. Não criar chave nova, não pedir credenciais nem usar assinatura debug.
5. O `CONTEXTO_NFSMW.md` canônico no Drive continuava terminando em PRE237 na última consulta, embora o progresso atual esteja na PRE277. **Consolidar com backup e reconciliação**, não substituir documento completo de >500 KB por um resumo.

## Situação final da PRE277
- Fonte PAL autenticada e auditoria SHA-validada: **sim**.
- Código alterado, novas chamadas guest, APK compilada/assinada/instalada: **não**.
- Níveis reais de 7 categorias BMW, instalação de Junkman e menu Performance funcionando: **não comprovados**.
- Relato de sucesso de dirigibilidade PRE260 permanece válido; BMW no prólogo/Razor não alterada.
