# PRE571_HANDOFF_PRE567R_PRE570_V48_SAVE_ISOLATION_GATE_20261109

**Data local:** 2026-11-09 (America/Bahia). **Projeto:** NFSMW-Recompiled-Mobile, BMW M3 GTR carreira `type=41`, APK release V48 PRE452. Objetivo é tunagem comprável, instalável, física real e save persistente, **ainda NÃO habilitada**. O experimento de motor +5% e contador 0→1 permanece unicamente um vetor sintético de teste.

## Recuperação exata do contexto PRE567 — PRE567R

- O workflow PRE567 [42557734548](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42557734548) terminou em `failure`, inicialmente por `HTTP 502` na atualização de Drive e, no retry, por uma falha no gate de publicação do relatório, após a atualização do Drive ser aplicada.
- A auditoria independente PRE567R [42558361828](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42558361828), `AUDIT_OK`, comprovou **dois backups byte a byte iguais ao contexto anterior**: 859.770 bytes, SHA256 `074c43bb4d3781e64b7c37bfb9efa92f5ebf1505d11227434901e0ba4f6e1f36`.
- O arquivo canônico `CONTEXTO_NFSMW.md`, Drive id `1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB`, foi lido novamente: **864.277 bytes**, SHA256 **`7227982889c1cbcadb6ce41eb7408289f42d5305eecc5afdcf848f5a4a5c5be4`**. Corresponde exatamente ao backup prefixado + delimitador + handoff PRE567 do GitHub. Atualização comprovada apesar do status final da execução original.

## PRE568 — exata APK V48: duas raízes de dados nos argumentos do app

- [PRE568 run 42558650729](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42558650729), relatório `docs/PRE568_V48_ANDROID_SAVE_ROOT_STATIC_READONLY.json`, `AUDIT_OK`. APK original 47.104.233 bytes autenticada por SHA256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`, sem modificação.
- Bytecode compilado `Ajustes.carpetaDatos` chama `getExternalFilesDir`, enquanto `MotorNativo.carpetaUsuario` chama `getFilesDir` (armazenamento privado do pacote). `MotorNativo.argumentos` usa `carpetaUsuario`; `Ajustes.argumentos` usa `carpetaDatos`. Strings compiladas observadas `--user_data_root` e `--game_data_root`. São **duas raízes de argumentos do aplicativo**, porém isso NÃO comprova que todas as rotinas de save guest estejam isoladas.
- `Ajustes.gamertag` usa `SharedPreferences` e não demonstra que mudar a tag crie um diretório de save separado.

## PRE569 — caminho de importação de partidas na inicialização

- [PRE569 run 42559005223](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42559005223), relatório `docs/PRE569_V48_SAVE_IMPORT_STATIC_READONLY.json`, `AUDIT_OK` somente leitura.
- Call graph no DEX autenticado: `MotorNativo.preparar` invoca `MotorNativo.traerPartidas`; `traerPartidas` invoca `Ajustes.carpetaDatos` e `MotorNativo.copiarArbol`. Há uma relação estática de importação/cópia com a pasta externa de dados, mas os argumentos reais, condições de execução, direção e destino da cópia **não foram determinados pela auditoria de referências**.
- A PRE569 não observou o telefone nem modificou o save `MARCEK`.

## PRE570 — código de cópia de árvore verificado, sobreposição não determinada

- O primeiro run PRE570 falhou porque o script usava nomes de campos PRE568 em um relatório PRE569; corrigido antes de nova execução. [PRE570 retry run 42559255950](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42559255950), relatório `docs/PRE570_V48_SAVE_IMPORT_STATIC_READONLY.json`, `AUDIT_OK`.
- O método `MotorNativo.copiarArbol` da APK V48 original contém chamadas diretas a `File.listFiles`, `File.isDirectory`, `File.mkdirs`, `FileInputStream.<init>`, `FileOutputStream.<init>`, `InputStream.close`, `OutputStream.close`, `volcar` e chamada recursiva a `copiarArbol`.
- Isso **comprova a presença de um mecanismo de cópia de arquivos na preparação**, mas NÃO resolve: se há guarda antes da cópia; se o destino já existente pode ser substituído; qual diretório guest de save é realmente usado; se `MARCEK` estaria em risco num perfil experimental. Não concluir gravação automática ou overwrite sem fluxo de controle/trace real.

## Próximo gate técnico obrigatório

1. Antes de alterar a pasta PT-BR ou construir V49, verificar **fluxo de controle e argumentos de `preparar → traerPartidas → copiarArbol`**, inclusive origens, destino e condições que impedem a sobreposição. A presença de `FileOutputStream` torna necessário um exame específico de não sobrescrita, não constitui prova automática dela.
2. Confirmar, por instrumentação/experimento não destrutivo quando for viável, a raiz *efetiva* de arquivos guest de save sob `--user_data_root`, a relação com `--game_data_root` e a edição nativa realmente carregada. O aplicativo V48 e seus saves do S24 FE NÃO foram lidos remotamente.
3. Só habilitar teste de loader VPAK com **cópia íntegra e reversível** da tradução PT-BR, save isolado comprovadamente inacessível ao fluxo `MARCEK`, e sem checkout/transação. O arquivo `ZZDATA4.BIN` esparso de PRE566 não é jogável e não pode ser usado no dispositivo.
4. Após aceite guest de `engine/bmwm3gtr_upgrade_engine_pre499` (ainda não demonstrado), investigar separadamente disponibilidade FE/catálogo, preço, instalação, física e persistência antes de qualquer modificação funcional.
5. Preservar V48 PRE452, versões anteriores, package `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG-9076/touch, 1920×1080, cap 120 FPS, gráficos/shaders/física e proteção térmica. Nunca pedir senhas. Nenhuma APK nova nesta sequência.

**Estado:** PRE567R/PRE568/PRE569/PRE570 retry `AUDIT_OK`. Contexto PRE567 recuperado; rotas Java compiladas de dados e usuário identificadas; importação/cópia existente mas sem segurança comprovada para save existente. Original PAL/PT-BR e APK V48 não alterados; BMW tunável, compra, instalação, física e persistência ainda não comprovadas.
