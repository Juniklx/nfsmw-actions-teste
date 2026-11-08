# NFSMW Android — PRE427–PRE429: proveniência e correlação passiva da contagem de upgrades (2026-11-08)

## Estado inicial e restrições
- V46 PRE401 é baseline funcional e testada no S24 FE para Nitro infinito global (PRE407/408). Pacote `io.github.nfsmwrecomp`, versionCode 46, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- BMW M3 GTR no save MARCEK é dirigível; com menu bypassado, Peças/Desempenho aparecem, mas entradas de Transmissão exibem `Option title`, `20/20`, `999.999.999`. Não comprar.
- Estas três etapas usam snapshot PRE99 autenticado e são somente leitura ou patch em memória; não compilam, assinam nem instalam APK, não modificam save e não abrem credenciais de assinatura. Não provam número real de pacotes da BMW/Punto.

## PRE427 — proveniência da estrutura global
- [Run 42451519154](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451519154): `PRE427_STATUS AUDIT_OK`, quatro funções SHA-pinned/localizadas.
- Entrada de personalização `sub_8256B440` (`nfsmw_recomp.15.cpp`, 248 linhas, SHA256 `414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a`) usa `lis -32058; addi -9752` para produzir `r31`, base global; armazena ponteiro de carro guest em `[r31+4]` e ponteiro de pvehicle guest em `[r31+8]`. A rotina contém guarda inicial por byte global: não supor que evento ocorra para toda troca de carro, embora PRE273 descreva caminho de relinquish/take-control.
- Montador de lista `sub_8256F818` (`nfsmw_recomp.57.cpp`, 230 linhas, SHA256 `a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c`) usa a mesma constante de base global (em `r30`) e passa `r30+8` como argumento `r3` da chamada `sub_823E5988`. Coincidência de endereço da estrutura estática foi verificada **no código PAL**, não em runtime.
- `sub_823E5988` (`nfsmw_recomp.28.cpp`, 155 linhas, SHA256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`) consulta tabela/atributos pelo argumento `r4`, chama helpers e altera contador de referência U16 em `+18`. Não invocar artificialmente nem supor pureza. Identidade e níveis de BMW ainda sem medição real.
- `sub_8256CB60` localizado em `nfsmw_recomp.101.cpp`, SHA256 `4ca7b1a401ab9a0ea4e07f57e011a8750461b289aa4031f5b9d3801bb227086c`; faz switch de categoria `0..6`, devolvendo `3` ou `4`, e `-1` para valor acima de `6`. Isso parece um limite por categoria, não um nível exclusivo de veículo.

## PRE428 — helpers de atributos
- [Run 42451675734](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451675734): `PRE428_STATUS AUDIT_OK`.
- `sub_8214B858` em `nfsmw_recomp.50.cpp`, 95 linhas, SHA256 `f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d`: acessa estruturas de atributo, chama `sub_82148718` e `sub_8214E9E0`, decrementa contador U16 +18 e retorna indicador booleano.
- `sub_8214EDA8` em `nfsmw_recomp.83.cpp`, 86 linhas, SHA256 `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`: interpreta ponteiros/flags de atributo e retorna valor via caminhos distintos. Não foi provado modelo BMW específico nem ausência de efeitos no sistema de atributos.

## PRE429 — prévia correlacionada entrada/lista, DESLIGADA
- [Run 42451836847](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451836847): `PRE429_STATUS AUDIT_OK`, `PRE429_CORRELATION_MOCK_PASS_114_EVENTS`.
- `automation/kaggle/pre429_bmw_entry_level_correlation_dryrun.py` propôs, **somente em memória**, dois marcadores sob `NFSMW_PRE429_TUNING_LEVEL_TRACE_ENABLE` DESATIVADO por padrão:
  - Após store de pvehicle em `sub_8256B440`, loga endereço base manager, ponteiro guest opaco do TuningCar, ponteiro guest do pvehicle.
  - Após retorno da primeira chamada normal de `sub_823E5988` em `sub_8256F818`, loga endereço base manager, categoria `0..6`, contagem candidata retornada.
- Duas transformações byte a byte reversíveis, sem alteração das contagens de leituras/escritas guest nem chamadas guest; SHA256 de prévias `71ee78f8549956a0ebed025eb0d1e030287fff6e109d4d9dce7e39c3af084bfe` (entrada) e `cff8182d10604f4cba67b427cb5e45a26d38c7e3481f3dba17f7d77a9a61cd4f` (lista).
- **Mock host não é compilação nem teste Android**. Endereço `tuning_car` é guest pointer e **não identifica automaticamente BMW/Punto**. Para correlacionar eventos, usar sequência, categoria e o mesmo manager em sessões isoladas, verificando o caminho de RelinquishControl/TakeControl; não supor que evento de entrada seja produzido em toda troca de carro. Nem todas as categorias serão necessariamente consultadas em uma visita.
- Módulo auxiliar C++ é apenas string de prévia, não foi integrado ao CMake. Não há pacote V47, instrumentação ativa nem níveis reais medidos.

## Próximo passo recomendado
1. Revisar estágio de build V46 e a atual árvore efetiva antes de tentar integrar PRE429, confirmando baselines de todos os patches e se a seleção PAL/PTBR do dispositivo é a pertinente.
2. Um futuro build diagnóstica V47 só deve acrescentar instrumentação passiva, com logs limitados e sem chamadas adicionais à física/atributos, preservar integralmente V46 e save, assinar com certificado permanente igual e incrementar versionCode.
3. Após backup do save, testar **BMW e Fiat Punto em sessões separadas**, sem comprar opções inválidas, juntando `ENTRY` e `LEVEL` por ordem/evento/manager e verificando os resultados na tela.
4. Sem essas medições, não desbloquear novos pacotes, alterar preços ou física, nem alegar conserto ou FPS.
5. Adicionar estas evidências ao `CONTEXTO_NFSMW.md` do Drive somente depois de backup integral + confirmação do texto atual, mantendo todo o histórico. Este adendo do GitHub não equivale a sincronização do Drive.
