# NFSMW Android — PRE273/PRE274: localizou TakeControl e validou correlação passiva de tuning com GetMaxLevel (2026-11-07)

## Evidência anterior no Galaxy S24 FE
- Na APK V37 do pacote `io.github.nfsmwrecomp`, usuário confirmou BMW M3 GTR normal da carreira **dirigível** no perfil MARCEK após importação do ZIP PRE260. Fiat Punto e Junkman anteriores foram mantidos.
- No tuning dessa BMW aparecem apenas opções **Visual**, pois o código decompilado identifica `IsHeroCar()` e oculte Peças/Desempenho. PRE262–PRE272 identificaram as funções de menu PAL e o caminho de GetMaxLevel, mas os sete valores efetivos da BMW ainda **não foram medidos**.
- A V37 permanece instalada e intacta. Nenhuma correção de vitória contra Razor/prólogo efetuada.

## PRE273 — análise de `CarCustomizeManager::TakeControl()`
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42325209725 — **success**, `PRE273_STATUS AUDIT_OK`.
- Backup PRE99 autenticado SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Fonte PAL `workspace/nativo/app/generated/default/nfsmw_recomp.15.cpp` SHA256 `414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a`: `sub_8256B440` (248 linhas na saída de auditoria, 8 chamadas diretas em código recompilado).
- Fluxo claro: `mr r29,r5` preserva 3º argumento recebido (candidato a `TuningCar`); testa e marca `g_bCustomizeManagerHasControl` (byte em global `-10064`); grava `r4` em `r31+0` (`EntryPoint`), `r29` em `r31+4` (`TuningCar`), copia 408 bytes de registro de customização em `r31+28`, inicializa pvehicle via `sub_821E02C0`/`sub_8214C420` e grava `ctx.r11` em `r31+8` (`ThePVehicle`). Seguem configuração de RideInfo/presenter e gravação de contador de carrinho `r31+444`. Sequência **fortemente consistente com a implementação pública de `CarCustomizeManager::TakeControl()`**, não prova por execução do binário V37.
- `sub_8256B5F8` (PAL `nfsmw_recomp.89.cpp`, SHA256 `813e62cb5fffc8a784cf4c589eb80923025360c2d77aa5af11a78d8ce6af85df`) desfaz o modo de personalização, zera byte global e limpa ponteiro de `r31+448`, consistente com `CarCustomizeManager::RelinquishControl()`.
- Cruzamento das chamadas: **2 locais** que chamam `sub_8256B440` (`sub_82577A48` e `sub_825852D8`), e **4 locais** para `sub_8256B5F8` (em 3 funções). Um dos chamadores de entrada `sub_825852D8` primeiro libera e depois chama `sub_8256B440` com `r4=1` e `r5` contendo carro escolhido.
- Relatório sanitizado no Drive: https://drive.google.com/file/d/1T-pwrdUmIs1bZ-H16pS4o6LKPo3ejmMZ/view

## PRE274 — ensaio passivo em memória, ambos os instrumentos desligados por padrão
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42325527254 — **success**, `PRE274_STATUS AUDIT_OK`, host mock `PRE274_ENTRY_GETMAXLEVEL_CORRELATION_HOST_PASS`.
- Fonte PAL `nfsmw_recomp.15.cpp`, exata acima. Inserção proposta **após** `REX_STORE_U32(r31.u32 + 8, ctx.r11.u32)` em `sub_8256B440`. Marcador `NFSMW_PRE274_TRACE_ENTRY`, compile guard `NFSMW_PRE274_TUNING_ENTRY_TRACE` **NÃO habilitado por padrão**. Dados candidatos: endereço manager `r31`, endereço guest de carro `r29`, campo pvehicle guest já disponível em `ctx.r11`; valor guest para correlação em chamadas de GetMaxLevel seria `r31+8`, e não a identidade de BMW.
- Fonte antes SHA256 `414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a`, prévia em memória SHA256 `73e30f64ed9fd804989f88989961007284c83b470cdbcd31f42d01bc4572e0a5`.
- Em paralelo, PRE271 aplicado **somente em memória** ao arquivo PAL `nfsmw_recomp.28.cpp` SHA256 base `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`; SHA256 de prévia `9405becf180d43d5f18af9bf33016e751ba655e39bb54e3edd6839e20317a211`. Três saídas de `sub_823E5988` instrumentáveis; macro `NFSMW_PRE271_BMW_LEVEL_DIAGNOSTIC` desabilitada por padrão.
- Preservadas as chamadas originais do jogo e contagens de `REX_LOAD/STORE`; reversibilidade byte a byte conferida em ambas fontes. Mock host C++ demonstrou correlação de `manager+8` com o ponteiro pvehicle guest usado ao consultar níveis, recusa categoria fora de faixa, limita 56 registros e reinicia ao mudar de carro.
- **Crítico:** nenhum código do jogo foi compilado, APK gerada, assinada, instalada ou testada. Não houve acesso às credenciais de assinatura ou save MARCEK. Os testes sintéticos **não** comprovam disponibilidade de pacotes da BMW.
- **Limitação estrutural:** `GetMaxLevel` ainda pode nem ser chamado pela BMW enquanto o menu Desempenho está oculto. Apenas registrar sua entrada em customização não fornece sete valores automaticamente. Evitar forçar entrada em listas vazias; analisar previamente se uma invocação adicional de `GetMaxLevel` a partir de pvehicle inicializado possui efeitos colaterais por suas duas funções auxiliares; identificar valores em dados de atributos como alternativa.
- Relatório sanitizado no Drive: https://drive.google.com/file/d/1yssFbgi3LEafYdGSV4mWJhvdPov_2TyI/view

## Próximo trabalho rigoroso
1. **PRE275:** auditar `sub_823E5988`, `sub_8214B858` e `sub_8214EDA8` quanto a gravações fora da pilha guest, riscos de ponteiros, caches e ciclo de vida; somente após provar efeitos controlados considerar consulta explícita dos 7 níveis no ponto TakeControl.
2. Caso seja seguro, montar instrumentação passiva **da BMW na garagem** separada de liberação dos menus (que segue desabilitada); testar em build diagnóstica V38 assinada pela chave original, com solicitação de backup e programa de teste restrito, não reduzir gráficos/efeitos/física.
3. **Nunca** alterar globalmente `IsHeroCar()` ou desbloquear telas de performance sem tratar `GetSelectedPart()==nullptr`.
4. Futuras APKs: `io.github.nfsmwrecomp`, versionCode **38 ou superior**, certificado SHA256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`** idêntico; nenhuma nova chave, assinatura debug ou senha exposta. Preservar V37, save, Fiat Punto, Junkman, PG-9076, shaders, 1920×1080, cap 60 atual e limites térmicos.
5. Consolidar esta nota no histórico canônico `CONTEXTO_NFSMW.md` do Drive **após backup completo e conciliação de PRE238–274**; última verificação mostrou esse documento terminando em PRE237. Não sobrescrever histórico de mais de 500 KB com resumo.

## Status inequívoco
- Fonte e fluxo de entrada: **correspondência estrutural muito forte**.
- Sonda PRE274: **validada só em código em memória e mock host**.
- Níveis reais da BMW: **não conhecidos**.
- APK V38: **não compilada ou instalada**; V37 e save permanecem preservados.
