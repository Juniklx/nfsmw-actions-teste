# NFSMW Android — PRE278: lista de pacotes vazia e atualização da tela Performance da BMW (2026-11-07)

## Objetivo e estado do aparelho
- Usuário testou BMW M3 GTR **normal** adicionada por save PRE260 no perfil MARCEK da **V37**: BMW está na garagem e pode ser dirigida. No tuning da BMW, apenas **Visual** aparece, porque `IsHeroCar` oculta `Peças` e `Desempenho`. O Fiat Punto, dinheiro, Junkman e demais perfis devem continuar preservados.
- PRE277 confirmou gravações em estruturas de atributos, inclusive incremento U16 `r30+18` em `sub_8214E928`; não existem evidências de que 7 chamadas artificiais `GetMaxLevel` sejam inofensivas. **Não forçar novas chamadas.**
- Finalidade PRE278: entender como o jogo trata lista de pacotes vazia e localizar a atualização final da tela no código PAL, antes de implementar qualquer patch de menu.

## Fonte decompilada pública consultada
Repositório `dbalatoni13/nfsmw`, arquivo `src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CarCustomize.cpp`:
- `CustomizePerformance::Setup()` chama `gCarCustomizeManager.GetPerformancePartsList(type,part_list)` no ramo de oficina normal, percorre a lista com `while (!part_list.IsEmpty())`, chama `SetInitialOption(...)` e, ao final, **chama `RefreshHeader()` sem condicionar a lista não vazia**.
- `CustomizePerformance::RefreshHeader()` inicia com `PreviewPerfPkg(GetSelectedPart()->GetPhysicsType(), GetSelectedPart()->GetUpgradeLevel())` e usa `GetSelectedPart()` repetidamente, sem guarda nula explícita nesses pontos.
- `CustomizeManager.cpp`: `GetPerformancePartsList` repete `i < Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`; se o número for zero, não adiciona partes. A causa de ausência de categorias no **menu principal** é `CustomizeMain::BuildOptionsList()` + `IsHeroCar`. Isso **não prova** que BMW tem zero pacotes; os números reais não foram medidos.
- É possível haver lógica de segurança adicional em métodos virtuais compilados não identificados; por isso, queda ao abrir tela vazia é **risco potencial, não crash observado**.

## PRE278 — PAL autenticado, auditable
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42327319397 — **success**, `PRE278_STATUS AUDIT_OK`.
- Script `automation/kaggle/pre278_bmw_performance_empty_list_static.py`; workflow `.github/workflows/nfsmw-pre278-bmw-performance-empty-list-readonly.yml`. Backup PRE99 autenticado SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Função PAL candidata `sub_82582F70`, em `nfsmw_recomp.11.cpp`, hash de fonte SHA-256 `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`: **1.231 linhas**, **32 chamadas guest diretas**.
- Uma chamada à função de montagem da lista de desempenho `sub_8256F818` (linha relativa 696 do corpo). Em seguida, bloco em linhas 705–712: `lwz r11,96(r1)`, `addi r10,r1,96`, `cmplw cr6,r11,r10`, `beq cr6,0x82583568`. Padrão fortemente consistente com checagem de lista encadeada vazia usando a sentinela do objeto local. **A iteração está protegida**, não há evidência ainda de seleção nula tratada na atualização final.
- No fim de `sub_82582F70` há duas chamadas via ponteiro/vtable (`bctrl` / `REX_CALL_INDIRECT_FUNC(ctr.u32)`) seguidas da chamada direta `sub_82587498` com `r3 = r1+96`, consistente com liberação/destruição da lista local. Por ser chamada virtual, **não foi possível mapear conclusivamente `RefreshHeader` ao endereço guest nesta PRE278**.
- Essa função também já contém consultas `sub_823E5988` em blocos próprios; abrir a tela introduz funcionamento normal pré-existente de nível, mas não autoriza chamadas artificiais.
- Relatório técnico ZIP/JSON sem saves pessoais: https://drive.google.com/file/d/1qcHT36Fkco6qJzC7TKa-FILfEALlrfPh/view
- Resultado explicitamente registra `refresh_header_guest_function_proven=false` e `zero_package_handling_in_android_proven=false`. Logo o sucesso do GitHub Actions valida **apenas o scanner estático**, não o patch.

## Decisão para PRE279
1. Localizar o destino concreto da chamada virtual `RefreshHeader` na vtable/tabela de funções guest (e a de `SetInitialOption`) ou pesquisar candidatos por chamadas ao método `GetSelectedPart` e `PreviewPerfPkg`, **sem escrita**.
2. Investigar uma guarda fail-closed para `GetSelectedPart()==nullptr` **antes** de `PreviewPerfPkg`, preservando navegação e recuperação da tela. Não presumir que proteger só uma ocorrência seja suficiente.
3. Só depois pensar em ativação opcional e restrita à BMW de garagem; manter `IsHeroCar` global inalterado, código do prólogo/Razor intocado, e evitar telas vazias.
4. Não permitir pacotes de desempenho fictícios, não presumir 7 níveis válidos, nem alterar physics/atributos. Uma futura V38 (se aprovada) exige versão Android >37, `io.github.nfsmwrecomp`, **certificado permanente idêntico** SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; nunca debug, credenciais ou chave recriada.
5. V37 e save MARCEK **não** foram alterados durante PRE277/PRE278. Não houve APK nova compilada/assinada/instalada nem teste de FPS. Preservar 1920×1080, limite FPS atual, gráficos, física, touch e PG-9076, limites térmicos, backups, outros perfis e Junkman.
6. `CONTEXTO_NFSMW.md` do Drive continua desatualizado terminando na PRE237. Adendo GitHub mantém o progresso sem apagar histórico; consolidar no Drive após backup integral e reconciliação das PRE238–278.

## Evidência versus hipótese
- Verificado em código público: `Setup` chamando `RefreshHeader` após montagem/iteração, uso não guardado de `GetSelectedPart()` no trecho citado.
- Evidência estática PAL: loop de lista com teste de sentinela, duas chamadas virtuais, nenhuma identidade final comprovada da atualização de header.
- Não verificado: níveis BMW, existência de pacotes por categoria, crash real, segurança de acesso com lista vazia, patch BMW funcionando, compilação V38.
