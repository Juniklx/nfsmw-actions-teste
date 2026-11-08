# PRE525_BMW_TUNING_PRE520_PRE524_PAL_FRONTEND_PRICING_HANDOFF_20261108

**Data:** 2026-11-08. **Projeto:** Need for Speed: Most Wanted (2005) Xbox 360 PAL, recompilação Android. **Objetivo autorizado:** torná-la BMW M3 GTR da carreira realmente tunável, com nível, preço, compra, instalação, física e persistência, preservando a APK **V48 PRE452** (SHA-256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`), Nitro infinito PRE398, controle PG-9076, save `MARCEK` e certificado permanente de assinatura SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. **Feature OFF. Não existe V49 jogável nem compra BMW validada.**

## PRE520 — padding real da PAL autenticado
- [Run 42531089216](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42531089216), `AUDIT_OK`, relatório `docs/PRE520_ORIGINAL_PAL_ZZDATA4_SECTOR_PADDING_READONLY.json`. O ZIP original `NFSMW_PAL.zip` no Drive `1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz` foi lido via HTTP 206 estrito. O membro comprimido `NFS/ZZDATA4.BIN` teve CRC32 integral `b46a396c` e tamanho descompactado **401.068.032 bytes** confirmados.
- O `GLOBAL\\ATTRIBUTES.BIN` PAL na linha ZDIR **806**, offset no `ZZDATA4.BIN` **355.932.160 bytes**, é idêntico ao VPAK original USA, **697.856 bytes**, SHA-256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`. A PRE520 leu **os 512 bytes reais de padding PAL**, confirmando que **todos os 512 são 0x00**. A alocação de 341 setores possui **698.368 bytes** e admite **em termos de espaço apenas** o VPAK experimental PRE518 de **698.004 bytes**, sobrando **364 bytes**, sem deslocar o próximo recurso. **Isso NÃO aprova alteração de ZIP/ISO, nem comprova aceitação pelo carregador.**

## PRE521 — recurso autêntico de catálogo da oficina
- [Run 42531332000](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42531332000), `AUDIT_OK`, relatório `docs/PRE521_USA_FE_ATTRIB_FRONTEND_CARPARTS_STRUCTURE_READONLY.json`. A ISO USA original possui `GLOBAL\\FE_ATTRIB.BIN` no `ZZDATA0.BIN`, offset **162.392.064**, tamanho **113.856 bytes**, SHA-256 `8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528`, checksum EA `4ec7acf5` igual ao ZDIR. O recurso é `VPAK` com vault `frontend` (BIN 53071 bytes; VLT 60576 bytes), **414 coleções** da classe frontend `0x85885722`, incluindo `carparts` e **21 filhos diretos**.
- Prova independente no código-fonte público reconstruído PC `dbalatoni13/nfsmw`, commit `80993f35224c61d2f1b135beba76c6f8234c7940`: `GameFlow.cpp::LoadFrontEndVault` carrega `GLOBAL\\FE_ATTRIB.BIN`; `UnlockSystem.cpp::LookupFEPartInfo` percorre `frontend` filhos de `carparts` e compara `feCarPartName` e `feCarPartInfo.Level`, retornando `FECarPartInfo.Cost`. `FEReflected.hpp` fornece layout de 12 bytes `Level: int32, Rep: float, Cost: float`, enum níveis 0 a 7 e categorias `TIRES=4, BRAKES=5, CHASSIS=6, TRANSMISSION=7, ENGINE=8, INDUCTION=9, NOS=10`. **É código de referência PC, não prova de chamadas executadas no Xbox PAL Android.**

## PRE522 — custos e níveis reais recuperados
- Duas tentativas falharam por supor que `PtrN` do `frontend` tivesse mesma organização do `ATTRIBUTES.BIN`. Corrigido parser só da PRE522: `FE_ATTRIB.BIN` possui `PtrN` de **22560 bytes**, com **4 bytes finais zero** após instruções de 12 bytes. Não alterar o parser de física nem o recurso original.
- [Run 42531787428](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42531787428) `AUDIT_OK`, relatório `docs/PRE522_USA_FE_CARPARTS_COST_ARRAYS_READONLY.json`: **21 arrays** `FECarPartInfo` válidos, 7 categorias de desempenho identificadas por enum, cada uma com níveis/custos reais; todos originalmente do VPAK USA SHA supracitado. Valores `Cost` por níveis 1,2,3,4 (— quando não há nível):
  - **Motor:** 5500, 14200, 29800, 98000.
  - **Transmissão:** 4800, 12200, 32000, 75200.
  - **Chassi/suspensão:** 3600, 7600, 10000, —.
  - **Freios:** 3100, 5200, 11400, 26800.
  - **Pneus:** 1400, 4800, 11800, —.
  - **Indução:** 5400, 25000, 76000, —.
  - **NOS:** 4900, 12500, 18000, —.
- Registros de nível 0 são custo 0; nível 7 `UNIQUE` presente em várias categorias com custo 0. Nenhuma conclusão de loja BMW ou preço aplicável à categoria deve ser tirada **antes de confirmar contagem/nível selecionado e transação**.

## PRE523 — identidade PAL do catálogo da oficina (novidade decisiva)
- [Run 42531993233](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42531993233), `AUDIT_OK`, `docs/PRE523_ORIGINAL_PAL_FE_ATTRIB_BINARY_IDENTITY_READONLY.json`. `NFS/ZZDATA0.BIN` dentro do `NFSMW_PAL.zip` foi validado integralmente por **CRC32 `11d904ba`** e tamanho **369.948.672 bytes**, 54 requisições de intervalos 206. Registro ZDIR PAL linha **666**, `GLOBAL\\FE_ATTRIB.BIN` em archive 0 offset **162.392.064**, global sector 79293; recurso PAL **113.856 bytes**, SHA-256 **`8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528`**, checksum EA **`4ec7acf5`**.
- **PAL e USA FE_ATTRIB.BIN originais são byte-identicos**; portanto as tabelas de preço PRE522 são valores originais *também da PAL*. Isso **não prova** quais preços ou pacotes o runtime Xbox/Android aplicou à BMW no menu nem que qualquer compra esteja autorizada.

## PRE524 — atenção à fórmula de nível, preço e pacote único BMW
- [Run 42532309034](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42532309034) `AUDIT_OK`, `docs/PRE524_BMW_PC_REFERENCE_FE_PRICE_SCENARIOS_READONLY.json`. Fonte primária pública reconstruída **PC** `CustomizeManager.cpp` no commit `80993f35224c61d2f1b135beba76c6f8234c7940`:
  `num_pkgs = Physics::Upgrades::GetMaxLevel(ThePVehicle, type)`,
  `part_level = i+1`, `catalogue_level = GetMaxPackages(type) - GetNumPackages(type) + part_level`.
  `GetMaxPackages(ENGINE)=4`. `UnlockSystem::GetPerfPackageCost` consulta `FECarPartInfo` no nível global resultante.
- Com a BMW **original** (`engine_upgrades=0`), 0 itens motor. Punto original (`engine_upgrades=4`) tem 4 opções, mapeando lvl1 → custo original 5500. **Com a BMW experimental PRE502 (`engine_upgrades=1`)**, *se* o Xbox usar exatamente a fórmula do PC, o único item local `part_level=1` mapeia para **nível global 4 e custo original PAL/USA 98000**. **Não confundir o custo da categoria motor nível global 1 (5500) com o potencial preço do único pacote BMW (98000).**
- Esse é um **cenário de fórmula**, não compra realizada, não valida unlock/availability/carrinho, nem efeito em física. A PRE524 tinha um flag `same_source_resource_PAL_USA_FE_price_identity_verified=false` porque não cruzava PRE523 no próprio script; a PRE523 **separadamente comprova** a identidade PAL do catálogo. Não promover `actual_Xbox_guest_unlock_price_formula_verified`, `BMW_package_purchase_unlock_status_verified` nem `BMW_Physics_SetPackage_or_save_roundtrip_verified` a verdade.

## Gatilhos técnicos pendentes
1. Validar no **guest PAL recompilado**, não somente na fonte PC, `CarCustomizeManager::GetPerformancePartsList`, `GetMaxPackages`, `GetPartPrice` e `Physics::Upgrades::GetMaxLevel/SetLevel/SetPackage` com nova coleção `engine/bmwm3gtr_upgrade_engine_pre499` de PRE502. A PRE455 já mostrou BMW tipo41 motor0 versus Punto tipo74 motor4, mas não compra/instalação.
2. Provar que loader PAL aceita VPAK com `ExpN` adicional e coleção cujo hash não aparece em `StrE` original; comprovar como escolhe `ZDIR/ZZDATA` em runtime. O checksum EA calculado para PRE518 `4d05584a` e padding PAL zero **resolvem só segurança estrutural de alocação**.
3. Não ativar flags PRE479/PRE483, não criar V49, não modificar ISO/ZIP, ZDIR, ZZDATA, APK V48 ou saves. Só depois de gates de loader e física, planejar experimento **reversível e isolado**, com save descartável, compra real, custo correto, corridas, regressões Nitro PG-9076, gráficos/120FPS e thermal.

**Attestation:** PRE520–PRE524 usaram fontes públicas, logs e dados originais autenticados, com extração apenas transitória privada em memória e relatórios metadata; não foram escritos/distribuídos assets de jogo, APKs novas, saves ou credenciais. Instalação V49 = não, compra de upgrades BMW = não, ganho de potência medido = não.
