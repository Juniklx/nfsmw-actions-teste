# PRE510_BMW_TUNING_PRE508_PRE509_VFS_HANDOFF_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW-Recompiled-Mobile Xbox 360 PAL/PT-BR/USA Android. **Objetivo:** BMW M3 GTR da carreira com níveis de desempenho realmente compráveis, instaláveis e persistentes, sem danificar Nitro infinito PRE398, controle PG-9076, shaders/física, APK V48, assinatura permanente ou save MARCEK.

**Estado verificado:** PRE508 e PRE509 foram auditorias de **somente leitura** da fonte **histórica PRE99** autenticada com SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. **Não comprovam diretamente a semântica ou montagem do APK V48 atual.** Nenhuma V49, VPAK editado, alteração de ISO, chave ou save foi realizada.

## PRE508 — evitar falsa identificação de loader por comentários

- Run inicial [42524977351](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42524977351) **falhou** porque um hash SHA-256 `host_path_file.cpp` fora transcrito como 57 caracteres em vez dos 64 da PRE505. O script foi corrigido ao valor exato do relatório anterior, sem modificar qualquer fonte. Não confundir a falha do script com problema de integridade do backup.
- Run final [42525120679](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42525120679): `AUDIT_OK`, relatório `docs/PRE508_HISTORICAL_NATIVE_LOADER_SOURCE_ANCHORS_READONLY.json`. Quatro arquivos originais com hashes verificados; excertos pequenos e redigidos somente no log privado do runner, relatórios contêm apenas metadados.
- `android/app/src/main/cpp/nativo/nativo_android.cpp` linha **537** menciona `attributes.bin` **exclusivamente em comentário sobre mapeamento do controle/HUD**, não em rotina de carregamento de atributos. `host_path_file.cpp` linhas **123, 160/164, 448** citam ZZDATA em **comentários sobre rastreamento de I/O e cache**, não no código de abertura desses recursos.
- Fluxo real de API evidenciado: `xboxkrnl_io.cpp` chama `REX_KERNEL_FS()->OpenFile` (por volta da linha 535); `virtual_file_system.cpp` resolve caminho com `ResolvePath` (linhas 218-220) e chama `entry->Open` (linha 337). Isso é análise estática da fonte PRE99.

## PRE509 — código não-comentado de montagem e abertura física

- [Run 42525446142](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42525446142) `AUDIT_OK`; relatório `docs/PRE509_HISTORICAL_VFS_MOUNT_CALLPATH_READONLY.json`; nove arquivos originais first-party analisados, incluindo `host_path_entry.cpp` e `host_path_device.cpp`. Foram mascarados comentários `//` e `/* */` antes da seleção de chamadas.
- `nativo/sdk/src/system/runtime.cpp`, `Runtime::SetupVfs`, linhas **320–358**: guarda `game_data_root_`; quando a origem é **URI de conteúdo Android** ou **arquivo regular de imagem**, cria `DiscImageDevice(mount_path, abs_game_root)`; quando é **pasta**, cria `HostPathDevice(mount_path, abs_game_root, !REXCVAR_GET(allow_game_relative_writes))`, inicializa e registra o dispositivo no VFS. A variável `allow_game_relative_writes` tem default **false** na fonte histórica (PRE508 `virtual_file_system.cpp`, linhas 18–21). Portanto, o caminho por pasta é **somente leitura por padrão**.
- `nativo/sdk/src/filesystem/virtual_file_system.cpp`, `ResolvePath` linhas ~105–134: normaliza caminho guest, identifica mount e resolve entrada via `device->ResolvePath(relative_path)`.
- `nativo/sdk/src/filesystem/devices/host_path_device.cpp` linhas ~44–55 define `HostPathDevice`; `ResolvePath` ~120–124 passa para `root_entry_->ResolvePath(path)`.
- `nativo/sdk/src/filesystem/devices/host_path_entry.cpp` linhas **53–85**: recusa abertura para escrita quando somente leitura; para arquivo físico abre `FileHandle::OpenExisting(host_path_,desired_access,...)` e cria `HostPathFile`. `host_path_file.cpp` contém `HostPathFile::ReadSync` (~746).
- `xboxkrnl_io.cpp` linha 535 usa `REX_KERNEL_FS()->OpenFile` e o VFS do runtime. Este é o **encadeamento estático** guest/virtual/host identificado na fonte histórica. Não afirmar por ele que o jogo em V48 abriu `GLOBAL\\ATTRIBUTES.BIN` pelo mesmo trajeto, ou que a modificação do ZDIR seria aceita.

## Próximo passo técnico e portas de segurança

1. **Cruzar com a V48 ativa**, verificando fonte/bundle/manifest efetivo, modalidade de seleção (pasta, imagem local ou URI Android), hashes da árvore e logs reais. Uma captura anterior com PT-BR pasta não é prova da modalidade/versão atual.
2. Determinar onde o carregador **guest** lê `ZDIR.BIN`/`ZZDATA4.BIN` e o VPAK `GLOBAL\\ATTRIBUTES.BIN`, para identificar uma estratégia de teste **reversível e independente dos dados originais**; não substituir ZIP/ISO/jogo nem alterar o save MARCEK sem validação.
3. A PRE502 provou apenas repack estrutural in-memory: estoque e uma engine BMW sintética +5% como vetor de teste, com `engine_upgrades=1`, **sem física medida, compra, catálogo FE ou loader PAL testado**. Não apresentar +5% como configuração final escolhida pelo usuário.
4. `ZDIR` PAL/USA preserva checksum original `0x296ad9ed`, mas não há algoritmo de substituição ou semântica do campo `total` conhecidos; não presumir CRC32. Não declarar V49 segura.
5. Antes de liberar mod, verificar `Physics::Upgrades::{GetMaxLevel,SetLevel,SetPackage}`, identidade BMW tipo41 ↔ `bmwm3gtr`, níveis reais, `FECarPartInfo` e preço, retorno transacional, física em corrida e persistência no **save descartável**. PRE479 e PRE483 permanecem OFF.
6. Preservar APK V48 PRE452, Nitro PRE398, controles/touch/PG-9076, 1920×1080, limite 120 FPS, gráficos/shaders/física, proteções térmicas, certificado permanente de release SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` e save `MARCEK`.

**Proveniência:** PRE508 [42525120679](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42525120679), PRE509 [42525446142](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42525446142), documentos privados de metadados do GitHub. Nenhum asset original do jogo, save, chave ou APK foi produzido ou modificado.
