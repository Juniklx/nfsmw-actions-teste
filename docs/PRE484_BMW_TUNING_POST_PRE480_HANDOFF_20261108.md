# PRE484_BMW_TUNING_HANDOFF_20261108 — progresso pós-PRE480

**Objetivo:** desenvolver tunagem real da BMW M3 GTR no NFSMW-Recompiled-Mobile Android, com upgrades físicos de motor, transmissão, suspensão, pneus, freios e indução, exibidos, comprados e persistidos corretamente. **Nenhuma versão jogável contém essa funcionalidade até a PRE483.** A APK válida continua V48 PRE452, Nitro PRE398 permanece protegido e o save `MARCEK` não deve ser usado como ambiente de teste.

## PRE481 — perfis da família BMW autenticados

- Workflow `NFSMW PRE481` [run 42514250936](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42514250936) `AUDIT_OK`. Relatório `docs/PRE481_PAL_BMW_FAMILY_PERFORMANCE_PROFILES_READONLY.json`, leitor `automation/kaggle/pre481_pal_bmw_family_profile_inventory_readonly.py`.
- Origem: `GLOBAL\\ATTRIBUTES.BIN` original PAL, idêntico ao USA no hash SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad` (PRE467). Nenhum byte de jogo alterado.
- A tabela StrE contém cinco nomes relevantes: `BMWM3GTR`, `BMWM3GTRE46`, `bmwm3gtr`, `bmwm3gtre46` e `m3gtre46careerstart`.
- Destes, **somente `bmwm3gtr` e `m3gtre46careerstart` possuem coleções físicas nas classes examinadas**.
- `bmwm3gtr` possui dados físicos de `engine`, `transmission`, `chassis`, `tires` e `brakes` e uma coleção `pvehicle` própria, mas não existe coleção `induction` com o mesmo hash.
- `m3gtre46careerstart` possui as mesmas cinco classes, mais `induction` e `pvehicle`. Todas as cinco estruturas compartilhadas têm hashes SHA distintos da variante `bmwm3gtr`; não são a mesma calibração.
- O nome `bmwm3gtre46` aparece em StrE mas não corresponde a coleção física nas seis classes examinadas. Não declarar que o banco inteiro não contém esse carro.
- **Nenhum dos dois perfis está comprovado como upgrade comprável.** Não tratar `careerstart` como nível superior por padrão nem copiar parâmetros Fiat Punto para BMW.

## PRE482 — fluxo de preço, compra e gravação confirmado por fonte de referência

Relatório detalhado `docs/PRE482_BMW_TUNING_FRONTEND_SAVE_TRANSACTION_SOURCE_AUDIT_20261108.md`, escrito e verificado no GitHub. Fonte de engenharia reversa `dbalatoni13/nfsmw` consultada, **não** executável Xbox PAL autenticado. Achados:

- `CarCustomizeManager::GetNumPackages` chama `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`; o máximo global é obtido de outra função (motor/transmissão 4, suspensão/pneus/indução/Nitro 3, freios 4).
- `GetPartPrice` consulta `UnlockSystem::GetPerfPackageCost`; este chama `LookupFEPartInfo` e pode retornar zero caso não exista dado de preço. Zero não comprova pacote legítimo.
- `InstallPerfPkg` atribui `InstalledPhysics.Part[type]` e chama `FECustomizationRecord::WriteRecordIntoPhysics`, que por sua vez usa `Physics::Upgrades::SetPackage`. Na falha, a referência reverte o nível da categoria para zero (não necessariamente o nível anterior).
- `FECustomizationRecord::WritePhysicsIntoRecord` usa `Physics::Upgrades::GetPackage`.
- O arquivo `PhysicsUpgrades.cpp` no código de referência estava vazio: **a implementação de `SetPackage`/seleção de perfil não está validada**. Persistência em arquivo real do usuário também não foi testada. Não confundir `SetInstalledPhysics` em memória com save em disco.

## PRE483 — primeiro modelo C++ de compra segura, isolado

- [GitHub Actions run 42514659147](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42514659147): `AUDIT_OK`, **44 verificações em Clang e 44 em GCC**.
- Código `automation/kaggle/bmw_tuning/pre483_bmw_transaction.hpp` e teste `pre483_bmw_transaction_test.cpp`; relatório `docs/PRE483_BMW_OFFLINE_TRANSACTION_GUARDS.json`.
- Simula atualização de `Package.Part[7]` em **cópia local**, preservando valor anterior e recursos quando falha validação de identidade, categoria, nível, registro FE de preço, créditos, aplicação física simulada ou serialização simulada. Testa explicitamente recusa do rótulo `MARCEK` e deixa o Nitro intacto.
- Bloqueio herdado de PRE479: `TryRealGameOperation` sempre devolve `RuntimeDisabled`; **nenhum hook, binário de jogo, APK ou save foi alterado**. Teste simulado não comprova física, preço real nem save persistente.

## Próxima etapa

1. Mapear no executável PAL ou no código recompilado específico `Physics::Upgrades::GetMaxLevel`, `SetPackage`, `SetLevel` e a seleção de coleções por nível, para descobrir como uma nova sequência BMW deve ser descrita e carregada (não inventar índices, parâmetros ou preços).
2. Validar que `type=41` do menu corresponde à chave de `pvehicle` que desejamos modificar; distinguir `bmwm3gtr` de `m3gtre46careerstart` em runtime.
3. Projetar e testar **offline** perfis BMW adicionais completos, com dados originais preservados, efeitos mensuráveis em física e níveis/catálogo de loja coerentes; impedir compras `Option title`, `20/20`, `999.999.999`.
4. Só depois integrar como módulo reversível e flag OFF em APK experimental assinada mantendo package `io.github.nfsmwrecomp`, certificado release, V48 intacta, PG-9076, shaders, Nitro e dados existentes. Validação de compra, reinicialização e save exige ambiente descartável, nunca `MARCEK`.

**Status verificável:** PRE481, PRE482 e PRE483 encerradas. BMW tunável no Android = **NÃO IMPLEMENTADA**. Nenhuma V49 foi construída. Tudo o que foi modificado nesta sequência foram scripts C++ de laboratório, workflows e relatórios no GitHub.
