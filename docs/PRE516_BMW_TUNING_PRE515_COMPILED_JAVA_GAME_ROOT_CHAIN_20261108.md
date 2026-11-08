# PRE516_BMW_TUNING_PRE515_COMPILED_JAVA_GAME_ROOT_CHAIN_20261108

**Data:** 2026-11-08. **Baseline de gameplay:** V48 PRE452 publicada, Nitro infinito PRE398, PG-9076, 1920×1080, cap configurável, save `MARCEK` preservado. **Objetivo do desenvolvimento:** BMW M3 GTR da carreira (type=41) com motor/desempenho realmente comprável, instalável e persistente, sem alterar a física original por palpite. **Feature experimental OFF; V49 não construída.**

## PRE515: métodos de entrada e seleção reais no código compilado V48
- [GitHub Actions 42528214393](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42528214393) `AUDIT_OK`; relatório `docs/PRE515_V48_DEX_GAME_ROOT_METHOD_REFS_READONLY.json`.
- Origem: V48 original do Drive ID `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`, **47.104.233 bytes**, SHA256 **`c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`**, hash revalidado antes de inspecionar bytecode. Foram examinados **17 métodos** alvos em DEX, e o relatório contém somente nomes/refências compiladas pré-selecionadas, não APK/DEX bruto ou preferências de usuário.
- `SetupActivity.onActivityResult` inclui chamadas a `Intent.getData`, `ContentResolver.takePersistableUriPermission`, `Uri.toString`, `Ajustes.iso`, `Ajustes.nombreIso` e `Ajustes.isoSinMirar`; isso confirma **um caminho compilado** que armazena uma URI de documento selecionada.
- `Ajustes.iso` usa `SharedPreferences.getString` para ler e `SharedPreferences$Editor.putString/apply` para gravar a configuração; `Ajustes.uriIso` referencia `Uri.fromFile` e `Uri.parse`, demonstrando suporte ao tratamento de URI/caminho local no código.
- `SetupActivity.edicionAlJugar` usa `Ajustes.iso`, `Ajustes.uriIso`, `IsoXex.mirar` e `Ediciones` para selecionar edição ou fallback. `Ajustes.edicion` chama `xexIso` e `Ediciones.paraJugar`; `Ediciones.deXex` consulta sua tabela compilada.
- `GameActivity.onCreate` possui `Intent.getStringExtra`, `Intent.getStringArrayExtra`, `Ediciones.porId`, prepara o motor e referencia o campo `GameActivity.argumentos`. `GameActivity.getArguments` consulta esse campo.
- `GameActivity.getLibraries` lê os campos `GameActivity.edicion` e `Ediciones$Edicion.libreria` no bytecode, confirmando o vínculo **estático** entre edição selecionada e biblioteca ARM64. O programa da V48 contém `libmain.so` e `libmain_usa.so` (PRE511), mas nenhuma identificação da edição **efetivamente executada na sessão** foi demonstrada nesta etapa.
- `GameActivity.openContentFd` usa `Uri.parse` e `ContentResolver.openFileDescriptor`, confirmando existência de ponte para descritores Android de URIs de conteúdo.
- `Ajustes.argumentos` invoca `MotorNativo.argumentos`, `Ajustes.edicion` e parâmetros de jogo; `MotorNativo.argumentos` consulta configurações gráficas e caminhos. Evidências de chamadas e campos do bytecode, **não execução em dispositivo**.

## Conclusão: cadeia estática confirmada, ramo efetivo desconhecido
- Cadeia da V48: `SetupActivity` (seleção de arquivo/edição) → `Ajustes.iso/uriIso/edicion` (persistência e interpretação) → `Ajustes.argumentos/MotorNativo.argumentos` → `GameActivity.getArguments/getLibraries` → runtime que tem `HostPathDevice/DiscImageDevice` (PRE509 e PRE511).
- Isto **não prova** que a sessão BMW/Punto de 08/11 usou uma imagem de disco, URI Android ou pasta. A análise PRE455 dos logs privados dos menus não capturou a origem de montagem e os logs brutos não estão disponíveis na pasta de medições do Drive. Não inferir modalidade pela simples existência dos métodos ou pelo nome de uma pasta.
- Ainda faltam aceitar nova coleção `ExpN/CollectionLoad`, semântica de `ZDIR` `0x296ad9ed`, e `FECarPartInfo` com catálogo/preço, funções `Physics::Upgrades` e compra/persistência em **save descartável**. PRE502 é repack estrutural **somente RAM** com vetor sintético +5%, não tuning funcional nem ganho de FPS.

## Próximo passo recomendado, sem mexer em V48
1. Obter um único registro **da sessão real** que identifique `Runtime::SetupVfs`/ `game_data_root` e/ou a modalidade da URI/pasta, junto de `versionCode=48` lido no dispositivo. O Android atual pode exigir exportação explícita do log, mas não instalar nova APK para coletar o dado sem necessidade.
2. Não expor caminhos pessoais nem copiar logs completos sem necessidade: derivar apenas indicadores de arquivo/pasta/URI e instante da sessão. Não declarar pasta só por ausência de marcador de imagem.
3. Enquanto não houver essa prova, auditorias podem examinar `ZDIR` original e loader guest de forma **somente leitura** para preparar repack independente e reversível.
4. Manter V48 assinado por certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`, Nitro PRE398, touch/iPega PG-9076, qualidade gráfica, 1920×1080/120 FPS quando configurado, física e proteção térmica, e save MARCEK intacto.

**Status:** PRE515 auditoria de código estático V48 = **confirmada**; seleção de origem da sessão e funcionamento de tunagem BMW = **não comprovados**; APK V49 = **não criada**; save `MARCEK` = **não modificado** neste trabalho.
