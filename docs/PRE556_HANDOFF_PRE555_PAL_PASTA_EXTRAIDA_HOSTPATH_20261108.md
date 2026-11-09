# PRE556_HANDOFF_PRE555_PAL_PASTA_EXTRAIDA_HOSTPATH_20261108

**Checkpoint:** 2026-11-08 (Bahia), ação PRE555 no GitHub Actions [42549478061](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42549478061), relatório `docs/PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_READONLY.json`, `status=AUDIT_OK`. **Alvo:** BMW M3 GTR da carreira, `type=41`, habilitar melhorias de desempenho genuínas que sejam carregadas, exibidas, compradas, instaladas e persistidas em save descartável antes de qualquer alteração na experiência real.

## Nova informação confirmada pelo usuário e pelo Shevery
- A V48 em execução no Galaxy S24 FE apresentou `versionCode=48 minSdk=26 targetSdk=35` e processo PID 7430. A leitura de `/proc/7430/maps` não foi autorizada. O logcat por PID era acessível mas não retornou marcadores de montagem; segunda amostra teve somente 5 linhas, com mesmo PID. Não inferir falha da montagem nem edição nativa a partir desses dados.
- O usuário confirmou explicitamente neste chat em 2026-11-08 que **executa por pasta extraída, sem ISO**, com tradução PT-BR baseada na PAL. Essa informação define a forma de uso do telefone; **não é telemetria da implementação interna da V48**.
- As rotinas compiladas V48 examinadas em PRE515 incluem `SetupActivity.edicionAlJugar`, `Ajustes.iso/uriIso/xexIso`, `Ediciones` e `GameActivity.getLibraries`. A V48 original autenticada PRE511 possui marcadores de `HostPathDevice` e `DiscImageDevice`. A biblioteca `libmain.so` efetivamente carregada no telefone ainda não foi observada diretamente.

## PRE555: transição código de arquivo extraído (prova histórica)
- GitHub Actions PRE555 ID `42549478061` concluiu `AUDIT_OK`; entrada `automation/kaggle/pre555_requests/trigger_pal_extracted_folder_hostpath_source_gate_20261108.json`.
- Verificou novamente SHA256 do snapshot privado PRE99, seis fontes com hashes fixados em PRE509, excluindo comentários antes da análise. Os dados-fonte ficaram temporariamente no executor privado; apenas contagens, nomes e hashes de trechos foram publicados.
- Em `workspace/nativo/sdk/src/system/runtime.cpp`, o código autenticado verifica URI Android ou arquivo de imagem e seleciona `DiscImageDevice`; o ramo `else` para diretório seleciona `HostPathDevice`, inicializa e registra o dispositivo. A rota histórica prossegue por `VirtualFileSystem::ResolvePath/OpenFile`, `HostPathDevice::ResolvePath`, `HostPathEntry::Open` / `FileHandle::OpenExisting`, `HostPathFile::ReadSync` e `REX_KERNEL_FS()->OpenFile`.
- Essa **arquitetura histórica** é compatível com a pasta extraída informada pelo usuário. Não há prova por instrumentação de que a V48 executou essas linhas específicas. Priorizar a rota de pasta extraída; não planejar solução exclusivamente por repack de imagem/ISO.

## Arquivos originais PAL, teste sintético e limite crítico
- PRE551 havia validado o ZIP PAL original: `NFS/ZZDATA4.BIN` de 401.068.032 bytes, CRC32 `b46a396c`; índice `ZDIR` original SHA256 `7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee` e registro 806 para `GLOBAL\\ATTRIBUTES.BIN`.
- O registro identifica deslocamento original 355.932.160 no arquivo `ZZDATA4`; recurso de 697.856 bytes com reserva de 698.368 bytes e exatamente **512 zeros** de padding original. PRE520 já havia comprovado originalmente esses zeros; PRE551 fez conferência independente e teste de leitura virtual em RAM.
- O pacote BMW sintético, 698.004 bytes, motor 0→1, vetor de torque artificial +5%, coube na mesma área com 364 zeros remanescentes; SHA256 do pacote RAM `d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6`. Isso NÃO foi carregado pelo guest real.
- **NÃO HOUVE COMPARAÇÃO** byte a byte dos arquivos do diretório traduzido do S24 FE contra o ZIP PAL original. A tradução pode alterar conteúdo ou índices: não substituir arquivos traduzidos nem supor identidade de `ZDIR.BIN`/`ZZDATA4.BIN`.

## Próximos gates
1. Analisar leitor guest `ZDIR`/`ZZDATA4` e aceitação `GLOBAL/ATTRIBUTES.BIN`/coleção `engine/bmwm3gtr_upgrade_engine_pre499`, com testes estritamente temporários.
2. Comparar não destrutivamente os arquivos reais da pasta traduzida com o original PAL quando for possível obter hashes e tamanhos suficientes, sem exigir publicação de arquivos pessoais.
3. Somente depois, preparar overlay/repack em cópia descartável dos dados extraídos, save descartável e teste no carregador real, seguindo `FECarPartInfo`, custo, `SetPackage`, física, compra e persistência.
4. Preservar V48 PRE452, V46/V47, assinatura/certificado, save `MARCEK`, Nitro PRE398, iPega PG-9076, gráficos e proteção térmica. **Não construir nem instalar V49** antes de prova de loader e isolamento dos dados.

**Estado final:** fonte de jogo via pasta extraída = confirmada pelo usuário. Caminho histórico `HostPathDevice` = verificado em fonte PRE99. Execução do HostPathDevice na V48, paridade de arquivos da tradução, carregamento da modificação e tunagem BMW funcional = **não comprovados**. APK, dados do jogo e save não foram modificados neste checkpoint.
