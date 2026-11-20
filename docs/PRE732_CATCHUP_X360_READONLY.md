# PRE732 — Catch-Up de carreira no Xbox 360 (somente leitura)

Objetivo do usuário: eliminar rubber-banding dos rivais em **todas** as corridas de carreira, incluindo Blacklist, sem afetar quick race, física normal, polícia, save ou gráficos.

## Evidências verificadas em código público
- PC: ExOptsTeam/NFSMWExOpts/NFSMWExtraOptions/ExtraOptionsStuff.h, NoCatchUp (duas vtables + controlador e opções do menu de corrida rápida). Endereços x86 NÃO se aplicam ao PPC/XEX.
- PC: MagicIbrar/nfsmw-unity/NFSMW_RE/specs/races.md §5.3, campo CatchUp do evento (carreira/challenge), versus fluxo distinto de quick race. Ainda não se provou paridade X360.
- PC: s-b-repo/nfsmw-2005-re/docs/attribute_cracks_verified.json: hashes de CatchUp, CatchUpIntegral, CatchUpDerivative, CatchUpSkill, CatchUpOverride e CatchUpSpread.
- Xbox 360: Juniklx/NFSMW-Recompiled-Mobile/nativo/app/src/nfsmw_recortes_carrera.cpp mapeia estado/tipo de corrida, MAS NÃO identifica a rotina de Catch-Up.
- Base de release verificada: V52 PRE731 produzida em GitHub Actions run 44432954802; certificado permanente mantido. Esta auditoria NÃO modifica a V52.

## O que este PR faz
Acrescenta auditor reversível, sem escrita, dos 6 hashes candidatos em arquivos **já extraídos** e um CI público exclusivamente sintético. Não analisa dados comprimidos dentro de ISO/ZIP/XEX, não autentica a semântica dos hashes Xbox 360 e não fornece offsets de patch.

Na área PRIVADA em que game_root já foi extraída, rodar:
python3 automation/actions_only/pre732_auditar_catchup_atributos.py --input /caminho/privado/game_root --output /caminho/privado/pre732.json

O relatório é privado e contém só nome/offset/contagem de ocorrência, não bytes do jogo. Não adicionar ISO, XEX, APK, chaves, tokens nem o relatório com conteúdo privado ao GitHub público.

## Próximos gates
1. Obter (sem publicar) a árvore de atributos REAL das corridas no Xbox 360 USA; comparar herança/valores da flag em eventos normais e Blacklist. Um hash encontrado não é evidência suficiente.
2. Mapear a leitura da flag no guest PPC/recompilado e excluir efeitos em quick race/challenge, sem substituir cegamente bytes.
3. Criar patch de gameplay desativado por padrão, reversível, com testes de regressão e logs sem segredos.
4. Só então gerar APK com mesmo certificado e versionCode maior que a release instalada; validar no Galaxy S24 FE, preservando save e recursos gráficos.

**Estado PRE732:** códigos e testes sintéticos; nenhum patch de gameplay, APK ou teste físico.
