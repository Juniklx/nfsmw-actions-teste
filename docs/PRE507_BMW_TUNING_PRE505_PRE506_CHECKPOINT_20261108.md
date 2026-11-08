# PRE507_BMW_TUNING_PRE505_PRE506_CHECKPOINT_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW Xbox 360 PAL recompilado Android, repo `Juniklx/nfsmw-actions-teste`. **Objetivo:** tunagem real, comprável e persistente da BMW M3 GTR na carreira. **Estado:** feature DESLIGADA, V48 PRE452 permanece referência, nenhuma V49 nem VPAK editado instalado, Nitro PRE398, iPega PG-9076, assinatura permanente e save `MARCEK` preservados nos testes desta etapa.

## PRE504 — comparação de nomes de coleções originais, somente leitura
- [Run 42523199651](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42523199651), `AUDIT_OK`; `docs/PRE504_ORIGINAL_STRE_VLT_COLLECTION_NAME_COVERAGE_READONLY.json`.
- Entre **2.339 coleções** originais em VLT, **1.274** têm hash de nome correspondente entre **1.920 nomes** de StrE e **1.065** não têm. Isso refuta a exigência estrutural universal de que toda coleção original esteja nomeada na StrE, mas **NÃO comprova** que a PAL aceite uma nova coleção sem nome nem que resolva `engine/bmwm3gtr_upgrade_engine_pre499` em runtime.
- Primeira tentativa da PRE504 falhou pelo nome do campo usado no script, corrigido antes da execução `AUDIT_OK`.

## PRE505 — localização de caminhos do carregamento nativo (snapshot histórico)
- [Run 42523779079](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42523779079), `AUDIT_OK`; `docs/PRE505_PRE99_NATIVE_ASSET_LOADER_PATHS_READONLY.json`.
- PRE99 autenticado SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, **874.780.689 bytes**, é código histórico, **NÃO** a árvore V48 instalada.
- Foram examinados **755 arquivos first-party**, **24.746.022 bytes** de código, 48 arquivos com correspondências textuais. Marcadores prioritários:
  - `workspace/android/app/src/main/cpp/nativo/nativo_android.cpp` linha **537**: referência textual a `ATTRIBUTES.BIN`; SHA `0453fea3ec0ca4a5e4ce4e926e3b1d1fd46dc38a402d89ba73a400afc7b7ad73`.
  - `workspace/nativo/sdk/src/kernel/xboxkrnl/xboxkrnl_io.cpp` linhas **84, 444, 445, 531**: marcadores ZZDATA, caminho guest e chamada nativa; SHA `40869526201fbed631b7bb506c83680edc02b2f4a6701f31a19b1a068c622015`.
  - `workspace/nativo/sdk/src/filesystem/devices/host_path_file.cpp` linhas **123,160,164,448**: ZZDATA; SHA `7dace8159023592ee8008a3798aea6a1856bc8e003492b9c4cce65346`.
  - `workspace/nativo/sdk/src/filesystem/virtual_file_system.cpp` linhas **20,218-220,337**: roteamento de arquivos.
- As ocorrências são **busca textual**, não prova da semântica do carregador ou suporte a substituição de VPAK. Nenhum trecho bruto de fonte ou recurso de jogo foi publicado. **Próximo:** inspecionar especificamente as funções/linhas indicadas, cruzar com fonte ou bundle efetivos da V48, e verificar o caminho real de `GLOBAL\\ATTRIBUTES.BIN`.

## PRE506 — comparação PAL/USA do índice de ATTRIBUTES.BIN
- [Run 42524004532](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42524004532), `AUDIT_OK`; `docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json`.
- A edição PAL possui `GLOBAL\\ATTRIBUTES.BIN` no `ZZDATA4.BIN`, linha **806** do ZDIR, offset de arquivo **355.932.160** e tamanho original **697.856 bytes**. São **341 setores de 2.048 bytes**: capacidade de **698.368 bytes**, folga de **512 bytes**. A hipótese PRE502 ocupa **698.004 bytes**, deixando **364 bytes** na mesma alocação; o próximo registro inicia em **356.630.528**, sem sobreposição.
- O campo checksum original ZDIR PAL `0x296ad9ed` coincide com o USA `0x296ad9ed`; o campo `total` difere (**PAL 890205**, USA **890206**) e **sua semântica não foi estabelecida**. A PRE503 demonstrou que o checksum original **não corresponde** a `zlib.crc32` dos bytes do recurso, logo não modificá-lo por palpite.
- O VPAK original PAL/USA desse recurso tem SHA-256 idêntico `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad` (PRE467). **A PRE506 não leu bytes de padding do ZZDATA4 PAL**, portanto folga de alocação não significa padding zero PAL comprovado, nem autoriza substituição.

## Limites atuais e próximo experimento
1. **Não gerar V49 ainda.** O VPAK PRE502 é cópia em memória com perfil sintético +5% somente para teste; o usuário não pediu esse percentual como calibração final. Não existe catálogo FE verificadamente comprável nem teste real de física no runtime PAL.
2. Investigar exclusivamente código do loader e sistema virtual de arquivos, sem editar ROM/save/APK. Identificar se o Android V48 abre recursos por arquivo solto, índice ZDIR ou asset próprio; estudar os caminhos PRE505 e a versão de fonte efetiva no app.
3. Identificar semântica do campo checksum/total da PAL e confirmar segurança de repack, preferencialmente com análise somente leitura.
4. Depois validar `type=41` ↔ pvehicle `bmwm3gtr`, funções PAL `GetMaxLevel/SetLevel/SetPackage`, catálogo `FECarPartInfo`, preços, instalação e roundtrip em **save descartável** com regressões para Punto/Nitro. PRE479/PRE483 permanecem OFF até esses testes.
5. Conservar V48 PRE452, controles PG-9076, Nitro PRE398, 1920×1080 e 120 FPS, assinatura de release permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote Android inalterado e save `MARCEK`.

**Nota:** nesta rodada somente scripts de auditoria, workflows e relatórios de metadados privados foram criados no GitHub. Nenhuma mídia do jogo, APK, save, chave ou credencial foi gerada, substituída ou acessada pelos auditores.
