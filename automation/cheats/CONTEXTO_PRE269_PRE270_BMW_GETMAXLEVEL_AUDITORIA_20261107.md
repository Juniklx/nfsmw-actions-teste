# NFSMW Android — PRE269/PRE270: identificação estática do retorno de GetMaxLevel (2026-11-07)

## Motivação comprovada em aparelho
- BMW M3 GTR normal adicionada em MARCEK por save PRE260: usuário conseguiu **dirigir**. Só a opção Visual aparece no tuning; Peças e Desempenho ficam ocultas.
- PRE262–PRE268 mapearam a regra `IsHeroCar` no menu PAL, mas não descobriram quantos pacotes de desempenho a BMW possui. Nenhum patch de menu V38 foi compilado ou executado.

## PRE269 — auditoria de dataflow do chamador
- GitHub Actions run **42323844085**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42323844085; **success**, `PRE269_STATUS AUDIT_OK`.
- Backup PRE99 SHA-256 autenticado `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Código PAL SHA-pinned em `nfsmw_recomp.11.cpp`, `.34.cpp`, `.90.cpp`, `.57.cpp`. **Somente leitura**.
- `sub_8256F818` (PAL, em `nfsmw_recomp.57.cpp`), função consistentemente mapeada a `CarCustomizeManager::GetPerformancePartsList()`, salva argumento categoria em `r26` e lista de peças em `r25`, usa manager global `r30` e chama `sub_823E5988` com `r3=manager+8` e `r4=tipo`. Primeiro resultado retornado via `r3` é movido para `r21` e comparado a zero; ramo `ble cr6,0x8256F990` sai sem criar peças quando `r21<=0`.
- Segundo retorno de `sub_823E5988` é usado para calcular o nível de desbloqueio; `sub_8256CB60` chamado uma vez fornece limite máximo genérico por tipo. Dentro do loop há alocação de `44` bytes por registro de item de menu, consistente com `SelectablePart` da fonte pública.
- `sub_8256D2B8` possui `switch` por categoria `513–519`, prepara strings, usa `sub_8256F9D8` para distinção de turbo, e obtém hash: evidência indica que está ligada a `GetUnlockHash`, **não** deve ser descrita como `GetPerformancePartsList` (hipótese antiga PRE268 corrigida).
- `sub_8256F9D8` retorna teste booleano depois de `sub_823E6DC0` comparado com 1, consistente com `IsTurbo`; mapeamento ainda não validado dinamicamente.
- Relatório PRE269 privado (JSON técnico, sem save/credenciais): https://drive.google.com/file/d/1fK6LAQqQnkXcThnVW7DknNIKxxZU7mVr/view

## PRE270 — corpo real das funções convidadas
- GitHub Actions run **42324094963**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42324094963; **success**, `PRE270_STATUS AUDIT_OK`. 131 arquivos PAL examinados. Teste C++ host da regra 'não usar seleção quando pacotes<=0' passou em 26 casos, **não** é teste de jogo.
- `sub_823E5988` localizado em `workspace/nativo/app/generated/default/nfsmw_recomp.28.cpp`, SHA-256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`. Função de 155 linhas compara `r4` com entradas de uma tabela de 28 bytes; se a categoria não existe, retorna 0. Consulta dados de atributos por `sub_8214B858` / `sub_8214EDA8` e retorna inteiro lido da estrutura; possui três caminhos `blr`. Não possui comparação explícita com o tipo BMW `41`. Mapeamento fortemente consistente com `Physics::Upgrades::GetMaxLevel(pvehicle,type)`, mas sem medição dos atributos do veículo.
- `sub_8256CB60` localizado em `nfsmw_recomp.101.cpp`, SHA-256 `4ca7b1a401ab9a0ea4e07f57e011a8750461b289aa4031f5b9d3801bb227086c`. Retorna **3 ou 4**, dependendo do tipo da categoria `0–6`, e `-1` para categoria fora da faixa. Corresponde estruturalmente a `CarCustomizeManager::GetMaxPackages()`.
- **Não há valores numéricos efetivos de `GetMaxLevel` da BMW medidos no dispositivo**. Uma contagem zero é possível e gera lista vazia no builder. Já `CustomizePerformance::RefreshHeader()` da fonte decompilada utiliza `GetSelectedPart()` sem verificar nulidade naquele ponto. Risco de tela vazia/erro após abrir menu sem tratamento — ainda não observou crash.
- Relatório PRE270 privado (ZIP JSON técnico): https://drive.google.com/file/d/1MQiZHCJoXeJ_EjhZVPjDowMpXXFriOCG/view

## Próximo passo e preservações
- PRE271: projetar e ensaiar **sonda passiva de retornos do próprio `sub_823E5988`**, preservando argumentos por variáveis host, sem novos loads/stores de memória convidada; logging limitado por categoria, **OFF por padrão**. Não prometer dados da BMW se nenhuma chamada ocorrer enquanto a categoria estiver bloqueada.
- A futura V38, se houver, deve usar `io.github.nfsmwrecomp`, `versionCode>=38`, mesma chave/certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, jamais assinatura debug. Backups, saves, Fiat Punto, Junkman, C3 guard, SDL/touch/PG-9076, gráficos/1920x1080/física/limite térmico preservados.
- **PRE269/270 não construíram/assinaram APK, não modificaram save nem disponibilizaram opções de performance.**
- `CONTEXTO_NFSMW.md` canônico no Drive ainda desatualizado na PRE237 na última leitura; esta nota no GitHub deve ser incorporada depois de backup e conciliação com PRE238–271, sem substituir o histórico grande.
