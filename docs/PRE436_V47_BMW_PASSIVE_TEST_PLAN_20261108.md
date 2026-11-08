# PRE436 — Protocolo seguro de teste da eventual V47 diagnóstica (BMW versus Fiat Punto)

**Estado do protocolo:** preparado antecipadamente, **não comprova** que a PRE434 compilou/publicou uma APK. Antes de instalar, conferir no GitHub Actions o status PRE434 e o relatório de assinatura/artefato no Drive.

## Pré-requisitos obrigatórios

- Confirmar PRE434 com `completed/success`, APK íntegra, pacote `io.github.nfsmwrecomp`, versionCode **47**, certificado permanente SHA256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, e os **dois** marcadores PRE429 presentes no `libmain.so`. Não instalar APK não verificada.
- Fazer cópia/exportação integral do save **MARCEK** e verificar sua existência **antes** de atualizar; não editar a BMW, o Punto ou os upgrades. Preservar também a APK V46 PRE401 e o backup de dados.
- Uma APK com versionCode 47 não é normalmente substituível diretamente por versionCode 46 no Android. **Não presumir rollback por instalação da V46 sobre a V47.** Não desinstalar nem apagar dados como atalho; toda reversão deve respeitar os backups e o mecanismo real de downgrade.
- Manter resolução interna 1920×1080, shaders, efeitos, física, controle PG-9076/touch e proteções térmicas. O Nitro PRE398 permanece integrado, mas a V47 ainda precisa de teste no aparelho.

## Captura em duas sessões isoladas

**Sessão BMW:** iniciar o aplicativo de um processo limpo, abrir perfil MARCEK, selecionar a BMW M3 GTR de carreira (não a de prólogo) e entrar na personalização. Abrir Desempenho e navegar entre as categorias disponíveis para gerar **somente as chamadas normais do jogo**. Não confirmar compra, não selecionar opção inválida `Option title` / `20/20` / `999.999.999`. Sair; copiar o `nfsmw.log` dessa sessão antes de abrir o jogo com outro carro. Guardar com nome descritivo contendo BMW e V47.

**Sessão Fiat Punto:** encerrar completamente o processo e abrir novamente, escolher o Punto no mesmo perfil e repetir a navegação nas categorias de Desempenho. Não comprar upgrades durante o teste. Guardar o segundo `nfsmw.log` separadamente e registrar em texto qual carro foi selecionado em cada execução. Não combinar logs de ambos os carros num único arquivo.

## Interpretação rigorosa

- Procurar `[NFSMW_PRE429_ENTRY]` (base manager, ponteiros guest opacos) e `[NFSMW_PRE429_LEVEL]` (categoria `0..6`, `candidate_count`). Os ponteiros guest **não identificam** modelo BMW ou Punto por si só. O rótulo do carro vem da sessão de teste identificada pelo usuário.
- O teste da PRE429 limita a emissão a 16 entradas e 112 eventos de categoria por processo. **Ausência de evento não significa que a BMW tem zero pacotes.**
- A `candidate_count` é um retorno intermediário observado, **não** garantia de uma peça disponível ou comprável. Não modificar menu, preço, catálogo, física ou atributos com base apenas nesta contagem.
- `automation/kaggle/pre435_bmw_passive_log_analyzer.py` aceita `--log <arquivo> --car bmw` ou `--car punto`, analisa separadamente e não expõe endereços guest no relatório. Múltiplos eventos ENTRY no mesmo arquivo são classificados como ambíguos; não forçar correlação.
- Reunir ainda observação visual dos menus, qualquer erro e `NFSMW_PRE398_GLOBAL_NITRO_FULL` para confirmar regressões. Se a V47 travar, parar o experimento e conservar logs/save sem tentar comprar ou consertar a ROM no aparelho.

## Evidências necessárias para uma conclusão

1. PRE434: run ID, resultado final, hash SHA256 da APK, pasta/id Drive, certificado permanente, versionCode, testes de ZIP/ELF/DEX.
2. Instalação no S24 FE: confirmação **separada**; não inferir do build.
3. Duas sessões: logs originais separados, identificação externa do carro, resultados por categoria, marcadores de entrada/lista e eventual ausência.
4. Só após os dados, investigar se a BMW está limitada por atributo do modelo, pacote indisponível ou fluxo de UI, sem comprar opções inválidas. Não afirmar correção da tunagem ou aumento de FPS antes de teste.

**Baseline funcional preservada:** V46 PRE401 SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, Nitro infinito global funcional conforme PRE407. Protocolo PRE436 não cria APK, não usa credenciais e não modifica save.
