# PRE482 — Cadeia de instalação, preço e persistência da tunagem BMW (somente código-fonte)

**Data:** 2026-11-08
**Objetivo:** preparar a integração de tunagem REAL, não apenas o menu, para a BMW M3 GTR tipo 41 no NFSMW Android recompilado. O alvo do usuário é a BMW da carreira; distinção exata entre as chaves `bmwm3gtr`, `m3gtre46careerstart` e o carro tipo 41 ainda exige verificação no runtime.
**Estado de segurança:** análise de leitura de código. Nenhum patch de executável, VPAK, APK, save ou dados do jogo foi escrito.

## Proveniência confirmada

- PRE467: `GLOBAL\\ATTRIBUTES.BIN` do arquivo PAL original do usuário e da ISO USA têm o mesmo SHA-256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`. Equivalência somente para esse arquivo.
- PRE473: BMW `bmwm3gtr` e `m3gtre46careerstart` possuem contadores 0 em seis categorias e Nitro 3, coincidindo com a instrumentação de V48. Punto 4/4/3/3/3/4/3.
- PRE477: BMW e Punto têm layouts físicos distintos, comprovados por hashes de cada base `engine, transmission, chassis, tires, brakes, induction`.
- PRE481 [run 42514250936](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42514250936), relatório `docs/PRE481_PAL_BMW_FAMILY_PERFORMANCE_PROFILES_READONLY.json`: entre nomes de BMW presentes em StrE, apenas `bmwm3gtr` e `m3gtre46careerstart` possuem coleções nas classes físicas analisadas. `bmwm3gtre46`, `BMWM3GTR` e `BMWM3GTRE46` aparecem na tabela de strings, mas não como coleções nessas classes. **Esses perfis não são declarados níveis compráveis.**

## Fluxo original de frontend verificado por leitura de código de referência

**Fonte:** código aberto de engenharia reversa [`dbalatoni13/nfsmw`](https://github.com/dbalatoni13/nfsmw); corresponde ao modelo de código original, não prova de identidade da execução do Xbox PAL Android.

| Etapa | Função e arquivo de referência | Fato constatado |
|---|---|---|
| Máximo global de pacotes | `CarCustomizeManager::GetMaxPackages`, `CustomizeManager.cpp` linhas ~400–419 | Valores: pneus3, freios4, chassis3, transmissão4, motor4, indução3, nitro3 |
| Quantidade oferecida para veículo | `CarCustomizeManager::GetNumPackages`, mesmo arquivo ~421 | Retorna `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`, não o máximo global |
| Cálculo do preço | `CarCustomizeManager::GetPartPrice`, mesmo arquivo ~261–268 | Converte nível da lista do veículo em nível global e chama `UnlockSystem::GetPerfPackageCost` |
| Origem do preço | `UnlockSystem::GetPerfPackageCost`, `UnlockSystem.cpp` ~731–741 | Consulta `LookupFEPartInfo(unlockable,level)`, retorna o campo `Cost` quando disponível; **retorna zero se a referência estiver ausente** (não confundir com preço legítimo comprovado) |
| Instalação | `CarCustomizeManager::InstallPerfPkg`, `CustomizeManager.cpp` ~369–385 | `SetInstalledPhysics(type,level)` seguido de `WriteRecordIntoPhysics(ThePVehicle)`. Ao falhar, zera o nível e reaplica, e a função chama `PreviewPerfPkg` ao final |
| Alteração em registro FE | `FECustomizationRecord::SetInstalledPhysics`, `VehicleDB.hpp` ~103–106 | Simples atribuição a `InstalledPhysics.Part[id]`, sem validar catálogo ou integridade |
| Aplicação ao pvehicle | `FECustomizationRecord::WriteRecordIntoPhysics`, `VehicleDB.cpp` ~1049–1054 | Encaminha para `Physics::Upgrades::SetPackage(attributes, InstalledPhysics)`; retorna false se o pacote falhar |
| Retorno a registro | `FECustomizationRecord::WritePhysicsIntoRecord`, mesmo arquivo ~1056 | `Physics::Upgrades::GetPackage(attributes,InstalledPhysics)` |
| Estrutura de pacote | `PhysicsUpgrades.hpp` | `Package.Part[7]` (índices `Tires=0,Brakes=1,Chassis=2,Transmission=3,Engine=4,Induction=5,Nos=6`) e `Junkman` |
| Descrição do controle | `FECustomize.hpp` | Níveis `PPL_STOCK=0` a `PPL_LEVEL_6=6`, Junkman=7; tela com sete categorias físicas |

**Fontes GitHub verificadas:**
- [CustomizeManager.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CustomizeManager.cpp) (blob `607e8f23654941577aff2392b5ae6d39c66bf036`)
- [VehicleDB.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Frontend/Database/VehicleDB.hpp) (blob `2f2ee372110e9f4228c6bb2a4f1a00a388b21021`)
- [VehicleDB.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Frontend/Database/VehicleDB.cpp) (blob `cca3059dc9d16af9b64fe0de6b4a93a84d42abdb`)
- [UnlockSystem.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Frontend/Careers/UnlockSystem.cpp) (blob `4209ab53cf5471396206f35da3095cc63d914b3d`)
- [PhysicsUpgrades.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Physics/PhysicsUpgrades.hpp) (blob `12fe46773114b7a85fb476beba24a247e6aae73b`)

**Lacuna importante:** `PhysicsUpgrades.cpp` desse repositório está vazio; portanto **não há implementação-fonte confirmada** nesse local de `SetPackage`, `SetLevel`, `GetMaxLevel` e `GetPackage`. É necessário estudar as funções recompiladas PAL ou outra fonte verificável para essas semânticas. NÃO inferir que apenas elevar `*_upgrades` seja suficiente para aplicar uma sequência de dados físicos.

## Implicações para a modificação da BMW

1. Para ampliar `GetNumPackages` da BMW, o `pvehicle` precisa de contadores legítimos por categoria; PRE473 confirma o 0 original. Criar número fictício não fornece `RefSpec` válido nem curva física.
2. Cada nível disponível precisa corresponder a dados físicos completos e referenciados de uma variante BMW; PRE481 encontrou dois perfis originais, não uma progressão de 3/4 níveis. **Não reutilizar parâmetros do Punto como se fossem da BMW.**
3. A oficina precisa encontrar `FECarPartInfo` e preços adequados, sem aceitar fallback silencioso de `0` para pacote sem registro.
4. O código de referência grava `InstalledPhysics.Part[id]` e chama `SetPackage`; teste definitivo exige fazer instalação, abandonar a garagem, salvar e recarregar em **save descartável**, conferindo física e preço. Um roundtrip simulado em host não substitui isso.
5. A função de referência `InstallPerfPkg` reverte falha para nível zero, **não necessariamente para o nível anterior**. Antes de introduzir uma nova via de instalação BMW, deve existir um mecanismo transacional que preserve o nível anterior em caso de falha.
6. Restringir por *identidade do carro real* e *chave de atributos runtime*, não somente por `type=41` extraído de logs de menu.
7. Isolar o Nitro PRE398: nenhuma alteração `nos`, seus flags ou suas coleções.
8. A primeira implementação deve permanecer desativada até conferir as fases de fonte → perfil BMW → catálogo → preço → compra → aplicação → salvar → carregar → teste de corrida.

## Próximo incremento de código

Implementar em host (sem conexão ao jogo) um modelo de **transação de compra de upgrades** que preserve um snapshot anterior e restaure exatamente esse estado diante de qualquer falha na validação, no preço ou no teste de aplicação. Usar o bloqueio PRE479 como requisito. Testar regressões para BMW type 41, variantes não correspondentes, Punto, pacote sem FEPartInfo, falha de SetPackage, Nitro protegido e save MARCEK. O código C++ não deve fazer writes em guest memory, saves ou binários até validação separada.

**Estado:** V48 estável mantida; nenhuma V49; PRE479 guarda C++ OFF e PRE478 contrato Python OFF; save `MARCEK` intacto pelos procedimentos de análise. Não afirmar que runtime BMW tuning já funciona.
