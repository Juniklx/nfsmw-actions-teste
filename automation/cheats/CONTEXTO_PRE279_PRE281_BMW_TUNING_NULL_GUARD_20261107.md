# NFSMW Android — PRE279–PRE281: caminho virtual de RefreshHeader e guarda de seleção nula, sem APK (2026-11-07)

## Estado anterior confirmado
- Android **V37** do pacote `io.github.nfsmwrecomp` segue instalado/testado, com BMW M3 GTR normal adicionada ao save `MARCEK` via PRE260. Usuário confirmou que é selecionável e dirigível; a oficina só apresenta `Visual` para essa BMW. Outras versões de BMW/prólogo Razor não foram alteradas.
- PRE261–PRE278 identificaram `IsHeroCar` que oculta `Peças` e `Desempenho`. `sub_8256F818` produz uma lista de pacotes apenas se `GetMaxLevel` retornar valor positivo; `GetMaxLevel` (`sub_823E5988` candidato) e suas funções auxiliares possuem gravações de memória guest. As PRE275–277 não autorizaram chamadas extras ao sistema de atributos.
- PRE278 confirmou em `sub_82582F70` (PAL) a construção de lista protegida por sentinela de lista vazia, mas deixou pendente a seleção usada em `RefreshHeader()`.

## PRE279 — despacho virtual
- GitHub Actions **success**, run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42328099622, `PRE279_STATUS AUDIT_OK`.
- Backup PRE99 autenticado SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Função `sub_82582F70` (PAL `nfsmw_recomp.11.cpp`, SHA256 `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`), perto da linha 1216: `r29` (this) → vtable em `[r29+0]` → chamada indireta da entrada **+12** (provável `RefreshHeader`) depois de uma chamada virtual ao subobjeto `r29+44` com entrada **+60** (provável `SetInitialOption`). Após a chamada +12, `sub_82587498` libera a lista temporária.
- No PRE99 foram examinados 131 C++ PAL e 6 arquivos de metadados gerados; **não** apareceu na listagem um binário de vtable no diretório gerado do app. **O destino do endereço da vtable+12 continua não comprovado**.
- Entre as funções próximas, forte candidata `sub_82582A40` em `nfsmw_recomp.83.cpp` (fonte SHA256 `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`) devido à ordem/endereço e chamadas relacionadas à física. Ranking heurístico **não prova identidade**.
- Relatório no Drive: https://drive.google.com/file/d/1IsTGbPrHtwxlM8RcevO_FOo5oLioKTCd/view

## PRE280 — risco concreto de seleção nula na candidata
- GitHub Actions **success**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42328348316, `PRE280_STATUS AUDIT_OK`.
- Corpo `sub_82582A40` com 786 linhas. Logo no início duas chamadas virtuais (pela vtable +20), a primeira retornando ponteiro em `ctx.r3`; após `ctx.r11=ctx.r3`, há `r31=REX_LOAD_U32(ctx.r11+20)` **sem comparação com zero entre a chamada e o acesso**. Também `REX_LOAD_U32(ctx.r3+24)` após a segunda chamada sem checagem prévia. O primeiro acesso precede o único `sub_823E4370` (linha 92), candidato forte à prévia `PreviewPerfPkg`.
- **Nenhuma comparação com zero antes da chamada `sub_823E4370`** dentro do prefixo auditado; há checagens posteriores, relacionadas a outros objetos. Corresponde estruturalmente ao código público `CustomizePerformance::RefreshHeader()` que chama `GetSelectedPart()->GetPhysicsType()/GetUpgradeLevel()` antes de verificar seleção.
- Ainda não há correspondência definitiva via dados de vtable. Falha de renderização/crash na BMW **não observada**; risco potencial se menu for habilitado e não houver pacote.
- Relatório no Drive: https://drive.google.com/file/d/14xtZ_8wj07aNIlWJ2J5D8P31Pvj9lQS2/view

## PRE281 — prévia guardada, DESLIGADA, somente em memória
- GitHub Actions **success**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42328564650, `PRE281_STATUS AUDIT_OK`; teste C++ host `PRE281_HOST_NULL_GUARD_256_CASES_PASS`, **256 casos simulados**, nenhum código recompilado guest compilado.
- Script `automation/kaggle/pre281_bmw_null_header_guard_dryrun.py`; alteração de C++ **apenas em memória**, base PAL `nfsmw_recomp.83.cpp` SHA256 `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`, prévia SHA256 `b71f40a1fd1770fba249192ef03c78a641f575e8a6bca9511efedf75dad54a7e`.
- Logo após a primeira chamada virtual (na linha PPC original correspondente ao retorno em 0x82582A60) e antes do primeiro `r11+20`, inserção proposta **somente quando macro** `NFSMW_PRE281_BMW_EMPTY_HEADER_GUARD_ENABLE` estiver **definida e ativada**:
  `if (ctx.r3.u32 == 0) goto loc_82582F64;`
- `loc_82582F64` é o bloco comum de restauração da pilha/salida no final da rotina. A prévia foi validada byte a byte como reversível, com mesmas contagens de `REX_LOAD/STORE`, chamadas virtuais e funções guest. **Não mexeu no código persistente, não gerou APK nem aplicou a correção à V37**.
- Este guard pode impedir acesso nulo na primeira etapa **se** a função candidata for mesmo RefreshHeader; não prova que o UI saiba exibir uma categoria vazia ou voltar corretamente. Não cria pacotes de upgrade, não recupera valores reais da BMW e não altera a classificação HeroCar.
- Relatório PRE281 no Drive: https://drive.google.com/file/d/1GeONtYOT5oMs6JRBxxCXpRlN22EZehhj/view

## Próximo passo
1. Resolver a função efetiva referenciada na **vtable+12** da tela `CustomizePerformance`. O dump PRE99 gerado não contém tabela binária pronta; considerar dados `default.xex`/artefatos autorizados que já existam no Drive, mas sem solicitar material sensível e sem supor equivalência entre PAL e USA.
2. Com identidade e ciclo de vida provados, testar numa árvore **descartável** a coexistência PRE264 (menu BMW com recurso OFF por padrão) + PRE281 (guarda null OFF por padrão), **sem** ainda liberá-los na V38.
3. Só construir uma V38 diagnóstica após resolver menu vazio e manter toda instrumentação/controle/SDL/C3 da V37; `versionCode>37`, `io.github.nfsmwrecomp`, **mesmo certificado permanente SHA256** `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nunca recriar assinatura, não tocar credenciais nem usar debug.
4. V37, perfil MARCEK, Fiat Punto, BMW M3 GTR, vouchers Junkman, outros saves, gráficos/shaders, 1920×1080, iPega PG-9076, limite de FPS atual e proteções térmicas permanecem como antes. Não confundir sucesso de script com instalação, teste de carro ou FPS comprovado.
5. `CONTEXTO_NFSMW.md` canônico no Drive ainda estava desatualizado na PRE237 na conferência desta sessão (~556 KB). Registrar este adendo no GitHub sem sobrescrever o documento; para atualizar o Drive futuramente, fazer backup integral e conciliar PRE238–281.

## Estado inequívoco
- **PRE279–PRE281 ações GitHub success**: auditorias/scripts de fontes, mock host apenas; comprovados.
- **Destino concreto da vtable +12**: não comprovado.
- **Tratamento no Android e upgrades da BMW**: ainda não testados.
- **V38 compilada/assinada/instalada**: não.
