# NFSMW — PRE475: causa da ausência de tunagem da BMW e inventário de perfis (2026-11-08)

## Estado validado
**Objetivo autorizado pelo usuário:** desenvolver capacidade de tunagem de desempenho da BMW M3 GTR da carreira no NFSMW Xbox 360 recompilado para Android. Preservar assinatura permanente, pacote, Nitro PRE398, controles, demais veículos e o save `MARCEK`.

**Versão jogável atual:** APK V48 PRE452. **Não existe V49 de tunagem**; auditorias PRE465–PRE474 são só de leitura. Fonte PAL original do usuário: `NFSMW_PAL.zip` (Google Drive), cujo `GLOBAL/ATTRIBUTES.BIN` foi confirmado byte a byte equivalente ao da ISO USA na PRE467: SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`. Essa identidade não implica igualdade de todo conteúdo PAL e USA, nem garante que o estado instalado seja idêntico ao disco.

## Auditorias executadas (GitHub Actions privadas)
| Etapa | Run | Resultado |
|---|---|---|
| PRE465 — BIN/VLT estrutura | [42508972507](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42508972507) | `AUDIT_OK`; StrE+cinco blocos VLT |
| PRE466 — ExpN exports | [42509147384](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509147384) | `AUDIT_OK`; 2399 registros exportados, 59 classes, 2339 coleções |
| PRE467 — identidade PAL/USA VPAK | [42509329234](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509329234) | `AUDIT_OK`; byte a byte SHA igual |
| PRE468 — coleções BMW | [42509485073](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509485073) | `AUDIT_OK`; 7 coleções `bmwm3gtr` e 7 `m3gtre46careerstart` |
| PRE469 — nomes classes completos | [42509657435](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509657435) | `AUDIT_OK`; somente 1/59 classes resolvida por strings BIN simples, requer hash de código |
| PRE470 — opcionais BMW | [42509851970](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42509851970) | `AUDIT_OK`; 3711 campos opcionais, índices válidos |
| PRE471 — ponteiros | [42510044893](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42510044893) | `AUDIT_OK`; quatro fixups de tipo `UpgradeSpecs` |
| PRE472 — arrays | [42510278604](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42510278604) | `AUDIT_OK`; arrays BIN válidos 1 elemento cada |
| PRE473 — contadores reais `pvehicle` | [42510870784](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42510870784) | `AUDIT_OK`; reprodução exata dos zeros BMW e positivos Punto dos logs V48 |
| PRE474 — referências `RefSpec` | [42511041055](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42511041055) | `AUDIT_OK`; BMW geralmente 1 referência, Punto 2 |

## Correção de interpretação: UpgradeSpecs usado em sons
A classe `pvehicle` gerada a partir do código original de MW [`pvehicle.h`](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Generated/AttribSys/Classes/pvehicle.h) prova:
- Hash campo `0x8AE8BEE0` = **ShiftSND**; hash `0x0E9BFB66` = **TurboSND**.
- Ambos têm **tipo `UpgradeSpecs`** (estrutura genérica `RefSpec+u32 UpgradeLevel`) mas representam **sons de troca de marcha e de turbo**, NÃO catálogo de upgrades de potência.
- Nos arrays PRE472, o `RefSpec` referenciado tem classes `0xDB01B754` = **shiftpattern**, `0x55624A85` = **turbosfx**; fontes abertas originais em [shiftpattern.h](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Generated/AttribSys/Classes/shiftpattern.h) e [turbosfx.h](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Generated/AttribSys/Classes/turbosfx.h). `UpgradeLevel` bruto 0 nesses quatro registros não determina níveis de desempenho. Não editar esses arrays para tunar BMW.

## Achado causal: 7 campos reais de desempenho na estrutura base `pvehicle`
A fonte primária `pvehicle.h`, blob Git `9689104544d2ab9f273db4ef25996adead073b81`, descreve campos Int32 big-endian da estrutura base:
```
engine_upgrades        +0x28
transmission_upgrades  +0x2C
nos_upgrades           +0x30
brakes_upgrades        +0x34
tires_upgrades         +0x3C
induction_upgrades     +0x44
chassis_upgrades       +0x48
```
PRE473 verificou os ponteiros das estruturas base no VPAK PAL/USA idêntico e leu valores (sem alterar nenhum byte):

| Perfil | engine | transmission | chassis | nos | tires | brakes | induction |
|---|---:|---:|---:|---:|---:|---:|---:|
| bmwm3gtr | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| m3gtre46careerstart | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| punto | 4 | 4 | 3 | 3 | 3 | 4 | 3 |
| racers (classe pai pvehicle) | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| default (classe pai pvehicle) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Esses valores reproduzem **exatamente** as contagens já observadas em runtime pela PRE455 V48, sendo forte prova direta de que os zeros provêm da configuração original de `pvehicle`, não de erro da recompilação Android. Não afirmar que o código de lookup é o único determinante; compras e menu envolvem outras estruturas.

## PRE474: arrays reais de RefSpec por categoria
Para o `pvehicle` de `bmwm3gtr` e `m3gtre46careerstart`, cada categoria **engine, transmission, chassis, tires, brakes** contém **um RefSpec** (array capacity=1/count=1) apontando para a própria coleção do carro na classe correspondente (engine 0xF1F5FBC7, transmission 0x07A7A3E5, chassis 0xAFA210F0, tires 0xBD38D1CA, brakes 0x36350867). O perfil regular BMW também contém **dois RefSpec de `nos`**, apontando para duas coleções por hash.
No Punto, as mesmas cinco categorias contêm **dois RefSpec** por categoria: (a) coleção `punto`, (b) coleção por hash `0xA6F0F405` (nome ainda não identificado). O Nitro e Indução não foram encontrados como **campos opcionais explícitos** no `pvehicle` de Punto (podem vir por herança). Na BMW, Indução também não apareceu explicitamente. Tamanho das listas `RefSpec` não equivale automaticamente ao número de upgrades no menu.

**Interpretação técnica:** para habilitar tuning completo na BMW, não basta mudar zeros -> 3/4. É necessário validar, para cada categoria, o conjunto de perfis/coleções de desempenho que a BMW pode usar em níveis superiores e como o menu/garagem e o save persistem esses níveis. A referência adicional do Punto não autoriza reutilizá-la no BMW.

## Próxima etapa recomendada: PRE476
1. Investigar quais coleções de `engine`, `transmission`, `chassis`, `tires`, `brakes`, `nos` e `induction` estão referenciadas por perfis tunáveis (Punto e outros) e quais heranças/nomes de configuração já existem para BMW. Identificar especificamente `0xA6F0F405` sem suposição.
2. Localizar layout e validade de registros `*\_upgrades` + `*\_current` e a função PAL de instalação/aplicação, assegurando valores de desempenho, preço e save; não inferir diretamente compra válida da contagem.
3. Projetar **mod específica** por variante BMW, com flag OFF, backup `MARCEK`, laboratório de save descartável e regressões Nitro, controls e outros veículos.
4. Só após gates de referência, persistência e integridade, preparar um preview reversível sem APK; construir V49 experimental apenas depois.

## Estado real
As PRE465–PRE474 somente leram arquivos e produziram metadados. Não modificaram APK, ISO, dados da BMW, assinatura, Nitro nem save. Até agora a tunagem experimental **não está implementada**. Os valores reais de catálogo e suportes de upgrade devem ser verificados antes de qualquer mod.
