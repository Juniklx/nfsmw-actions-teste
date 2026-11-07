# NFSMW Android — PRE262–PRE264: BMW M3 GTR menu de tuning PAL (2026-11-07)

## Contexto observado em aparelho
- Perfil MARCEK: BMW M3 GTR normal (car_number 82) adicionada via ZIP PRE260, Fiat Punto car_number 81 preservado, Junkman mantidas. Usuário confirmou que conseguiu **selecionar e dirigir** a BMW.
- Problema confirmado por relato do usuário: ao acessar tuning da BMW, **somente Visual** aparece, faltando **Peças** e **Desempenho**.
- APK V37 não foi alterada após o relato, e a função de importação de saves não é a causa aparente do bloqueio do menu.

## Causa no código decompilado público
Referência consultada: `dbalatoni13/nfsmw`, `CustomizeMain::BuildOptionsList()` em `src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CarCustomize.cpp` e `CarCustomizeManager::IsHeroCar()` em `CustomizeManager.cpp`.
- `IsHeroCar()` retorna verdadeiro quando `TuningCar->GetType() == CARTYPE_BMWM3GTRE46`, enum 41 em `Generated/CarTypes.hpp`.
- `BuildOptionsList()` esconde `CC_PARTS` e `CC_PERFORMANCE` quando é HeroCar, mas sempre mostra `CC_VISUAL`.
- Há outras barreiras `IsHeroCar()` em `CustomizePerformance::Setup()` e no acesso Junkman/backroom; abrir categorias não garante pacotes válidos nem compatibilidade com `Physics::Upgrades::GetMaxLevel`.

## PRE262 — auditoria PAL/USA
- GitHub Actions **sucesso**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42320678150
- PRE99 autenticado SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- 131 `.cpp` PAL, 131 `.cpp` USA; 140.339.148 bytes PAL e 140.332.832 bytes USA examinados.
- 16 instruções `cmpwi/cmplwi` com literal 41 em PAL, em 12 funções; mesma contagem USA.
- Forte candidato de `IsHeroCar`: `sub_8256FD30` PAL / `sub_8256FB38` USA. Corpo com chamada de consulta do tipo do veículo, `cmpwi cr6,r3,41`, retorna booleano `r3=0/1`; consistente com fonte pública, sem teste runtime independente.
- Política puramente sintética de deixar original HeroCar intacto e condicionar liberação local: **32 cenários aprovados**. Não compilou código do jogo.

## PRE263 — contexto e cruzamento de funções
- GitHub Actions **sucesso**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42320956876
- Função **`sub_82578988` PAL**, em `workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp`, SHA-256 `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`.
- Correspondente USA: `sub_82578790`, `nfsmw_recomp.5.cpp`, SHA-256 `b203c3695e6fb0d2278ca2a61490f721c4ab8db3612cc73060f6299158c7e8cc`.
- No corpo PAL, chamada `__imp__sub_822CC740` seguida de `cmpwi cr6,r3,41`; cria booleano com `r10=0`, `bne`, `r10=1`; depois, sob dois ramos de backroom, constrói 5 itens de menu com `__imp__sub_82575370`: 2 categorias condicionais para cada ramo e `Visual` sempre. **Mapeamento estrutural fortemente consistente com `CustomizeMain::BuildOptionsList()`.**
- `sub_82582F70` PAL (`.11.cpp`) contém mais duas comparações com 41, provavelmente relacionadas às regras internas de `CustomizePerformance::Setup()`; não remover cegamente.
- A versão da fonte PRE99 ainda é snapshot; correspondência de execução do bloco exato no APK V37 não foi medida dinamicamente.

## PRE264 — patch somente em memória, desligado por padrão
- GitHub Actions **sucesso**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42321383887
- Código de ensaio: `automation/kaggle/pre264_bmw_hero_menu_patch_dryrun.py`; usa mesmo SHA autenticado `nfsmw_recomp.5.cpp`.
- Única transformação simulada: dentro de `sub_82578988`, imediatamente após `cr6.compare<int32_t>(ctx.r3.s32, 41, xer);`, permitir `cr6.eq=false` **somente se** o compile guard `NFSMW_PRE264_BMW_MENU_ENABLE` estiver explicitamente habilitado e `ctx.r3.s32==41`.
- O macro **não está definido na compilação por padrão**, portanto alteração fica desativada. O bloqueio de HeroCar global, o de Junkman/backroom e toda a versão USA permanecem intactos.
- O teste validou: 7 loads e 3 stores guest originais em `sub_82578988` preservados; **zero leituras/escritas guest adicionais**, 5 chamadas de adicionar opção preservadas, alteração byte a byte revertível; candidate SHA256 in-memory `1dc5745263d68e186e66545f8795b2a11fffc8d5011aec74f3ce8a9256afe11c`.
- Host C++ mock: **320 cenários aprovados**, entre 80 tipos de carro, estado do guard e backroom. **Não é teste dentro do jogo**, nem compilação de `nfsmw_recomp.5.cpp` com SDK, nem APK.
- Build V37 atual: APK SHA-256 `96eed924c22c32e67af5977fc96c581e780472298e8e49da817a39496a51b852`; verificação local confirmou hash idêntico; `libmain.so` PAL SHA256 `09264bac6460d12dbc55d7e95ed8b22d17460d6c9c98906ea8a74fd97e5c4ed0`.

## Próxima etapa e restrições
1. Auditar `Physics::Upgrades::GetMaxLevel` e as listas de pacotes de desempenho para `CARTYPE_BMWM3GTRE46`, evitando mostrar telas sem conteúdo ou travamento. O fonte público `PhysicsUpgrades.cpp` não implementa essa função; ainda falta comprovar disponibilidade.
2. Caso viável, preparar patch integrado ao workflow de V38 **após** os patches atuais V37 (PRE194, PRE246, PRE247), sem reaplicar patches à árvore modificada e preservando originais/backups. Verificar compatibilidade com `nfsmw_recomp.5.cpp` antes de escrita.
3. Testar que a BMW adicionada à carreira exibe as categorias em uma build separada, mantendo proteção do prólogo/razor, e verificar seleção/compra/salvamento e ausência de pacote vazio/crash.
4. **Não** afirmar cheat Junkman da BMW nem tuning de motor funcional sem teste em aparelho. Não alterar save MARCEK, conta, economia, vídeo, física, shaders, PG-9076/touch, FPS, 1920×1080 e limites térmicos.
5. Para qualquer V38: pacote `io.github.nfsmwrecomp`, `versionCode >=38`, assinatura release permanente com certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; **nunca** gerar nova chave, nunca expor credenciais nem usar debug signing.
6. Atualizar CONTEXTO_NFSMW.md canônico no Drive somente depois de backup e conciliar histórico, pois cópia consultada continuava desatualizada na seção PRE237. Este documento GitHub consolida evidências PRE262–264 sem sobrescrever Drive.

## Status verificável
- **Causa do menu:** identificada na fonte decompilada e fortemente mapeada na recompilação PAL.
- **Transformação experimental PRE264:** validada apenas em memória e C++ mock, desligada por padrão.
- **Nova APK / patch de tuning instalado:** **não**.
- **Vitória contra Razor:** não implementada, distinta desta correção de menu.
