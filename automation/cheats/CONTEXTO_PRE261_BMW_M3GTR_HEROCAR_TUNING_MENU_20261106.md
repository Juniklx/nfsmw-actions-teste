# NFSMW Android — PRE261: menu de tuning da BMW M3 GTR, diagnóstico de HeroCar (2026-11-06)

## Relato em aparelho (observação do usuário)
- Na **V37 instalada** com o ZIP experimental PRE260, o usuário confirmou **que selecionou e dirigiu a BMW M3 GTR**.
- Problema novo: ao acessar tuning/customização da BMW, **somente a opção Visual aparece; não aparecem Peças e Desempenho**.
- A BMW do PRE260 é a variante normal/final `BMW M3 GTR`, car_number 82, adicionada no save MARCEK com Fiat Punto 81 preservado. Não é a variante `M3GTRCAREERSTART`.
- Até este momento, **não** há observação de crash ou perda de progressão, nem evidência de que haja peças de desempenho instaláveis para esse modelo no motor. Não afirmar isso sem testar.

## Causa identificada em fonte decompilada pública
Referência consultada, `dbalatoni13/nfsmw`:
1. `src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CarCustomize.cpp`, `CustomizeMain::BuildOptionsList()` (linhas aproximadas 2067–2082):
```cpp
bool isReallyHeroCar = gCarCustomizeManager.IsHeroCar();
if (!gCarCustomizeManager.IsInBackRoom()) {
    if (!isReallyHeroCar) {
        AddCustomOption(..., CC_PARTS);
        iPerfIndex = AddCustomOption(..., CC_PERFORMANCE);
    }
    AddCustomOption(..., CC_VISUAL);
} else {
    if (!isReallyHeroCar) {
        AddCustomOption(..., CC_PARTS);
        AddCustomOption(..., CC_PERFORMANCE);
    }
    AddCustomOption(..., CC_VISUAL);
}
```
2. `src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CustomizeManager.cpp`, `CarCustomizeManager::IsHeroCar()` (linhas aproximadas 1387–1389):
```cpp
return TuningCar->GetType() == CARTYPE_BMWM3GTRE46;
```
- **Conclusão com suporte direto do código:** o frontend deliberadamente oculta Peças/Desempenho da BMW M3 GTR detectada por tipo, independentemente dos flags de posse inseridos no MC02. O relato do usuário é coerente com esse controle.
- **Ressalva:** fontes decompiladas públicas cobrem várias versões e NÃO provam ainda equivalência de endereços/instruções com o APK USA/PAL V37. Não foi testado patch.

## Dependências adicionais do menu
- `CustomizeManager.cpp` `GetNumPackages(type)` usa `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`; `GetPerformancePartsList` cria ofertas apenas quando esse máximo permite. Portanto, ocultação do menu é causa imediata dos itens faltantes, mas **apresentar a categoria não prova que haja pacotes disponíveis ou que a física suporte upgrades**.
- `CarCustomize.cpp` `CustomizePerformance::Setup()` inclui outras condições `IsHeroCar()`, especialmente para fichas Junkman na backroom (linha aproximada 4994) e opção adicional posterior (linha ~5022). `CustomizeMain::NotificationMessage()` usa `IsHeroCar` ao tratar acesso à backroom; não modificar função global cegamente.
- Objetivo legítimo: oferecer menu de peças/desempenho da BMW **somente quando segura e validada**, sem trocar assinatura/modelo da BMW, nem alterar física do jogo original indiscriminadamente.

## Próximo experimento proposto (não executado)
1. Auditar correspondência do ramo `CustomizeMain::BuildOptionsList()` e `CarCustomizeManager::IsHeroCar()` nos **fontes PAL recompilados autenticados** e capacidades `GetMaxLevel` de `CARTYPE_BMWM3GTRE46`. Se não existirem pacotes de desempenho para essa variante, considerar UI de tuning offline por save somente com modelo de física validado, e não prometer 'todos upgrades'.
2. Preparar patch **desligado por padrão ou restrito ao modelo de BMW própria da carreira em menus da garagem**, sem mudar o teste de HeroCar global e sem alterar o fluxo do prólogo/Razor; verificar que outros carros e o carro especial do prólogo preservam comportamento original.
3. Build futura com `versionCode > 37`, mesmo package e certificado permanente. Testar no aparelho: opção Peças/Desempenho visível, categorias possuem opções válidas, seleção/compra, instalação, salvar/reabrir, Junkman, Punto, BMW, controle PG-9076, gráficos e estabilidade. Backups e possibilidade de rollback obrigatórios.
4. O save MC02 MARCEK PRE260 **já aceita e permite dirigir BMW** conforme relato; não modificar ZIP por tentar reparar um bloqueio de menu que depende do código.
5. Não atribuir o problema a checksum de save ou falta de fichas Junkman sem evidência.

## Estado e segurança
- **Confirmação em Android:** BMW disponível para dirigir; customização reduzida a Visual.
- **Causa identificada em código público:** check `IsHeroCar` do tipo BMW M3 GTR e ocultação de duas categorias.
- **Patch no APK:** nenhum. V37 continua a última compilação instalada, certificação permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`.
- **Razor/prólogo:** sem patch e sem vitória provada; independente deste problema de tuning.
- **Drive canônico `CONTEXTO_NFSMW.md`:** só atualizar após preservar backup e conciliar histórico; adendo GitHub evita perda desta constatação.
