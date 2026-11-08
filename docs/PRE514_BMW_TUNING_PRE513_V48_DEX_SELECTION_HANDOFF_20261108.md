# PRE514_BMW_TUNING_PRE513_V48_DEX_SELECTION_HANDOFF_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW-Recompiled-Mobile; tunagem BMW M3 GTR `bmwm3gtr` na carreira. **Baseline atual:** APK V48 PRE452 assinado, Nitro infinito PRE398, PG-9076, save `MARCEK`. **Fronteira:** somente leitura, sem novos APKs, patches VPAK ou alteração de saves.

## PRE513 — análise de código Java compilado da V48 distribuída
- [GitHub Actions 42527679678](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42527679678): `AUDIT_OK`; relatório `docs/PRE513_ORIGINAL_V48_ANDROID_DEX_GAME_ROOT_SELECTION_READONLY.json`.
- Fonte: **APK V48 original** `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk` (Drive ID `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`), tamanho **47.104.233 bytes**, SHA256 **`c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`**, validado antes da inspeção. O APK não foi reempacotado ou modificado.
- `classes.dex`: **8.680.496 bytes**, SHA256 **`b98bd2f2c7bc54a4442e638d641f8a353665f4a6220d2d1051d7af805e4a1dab`**. O script `androguard==4.1.3` percorreu **137 classes** alvo ou suas classes aninhadas, **710 métodos** desse subconjunto, com cinco classes principais: `Ajustes`, `Ediciones`, `GameActivity`, `MotorNativo` e `SetupActivity`. Os dados foram limitados a nomes de classes/métodos e famílias de invocações; nenhuma string de usuário, APK ou DEX bruto foi publicado.
- **Provas estáticas na versão distribuída:**
  - `GameActivity.openContentFd` possui código compilado (15 instruções) e **três invocações** identificadas como relacionadas a `Uri/ContentResolver`; `GameActivity.onCreate` contém 170 instruções com invocações de `Intent` e da seleção de edição; `getLibraries` tem 19 instruções e `getArguments` tem 2.
  - `Ajustes.uriIso` possui 12 instruções com invocações `Uri`; `Ajustes.argumentos` (221 instruções no overload principal registrado) referencia métodos de ajustes/edição e arquivos; `Ajustes.edicion`, `iso`, `isoMirada` e `isoSinMirar` estão presentes no DEX.
  - `Ediciones.deXex` e `Ediciones.paraJugar` têm bytecode compilado; `MotorNativo.argumentos` contém 331 instruções, com invocações aos ajustes e arquivos.
  - O pool DEX contém `android.intent.action.OPEN_DOCUMENT` e `takePersistableUriPermission` como literais, e nomes relacionados a `EDICIONES` e `getLibraries`. Isso fundamenta a existência de um caminho de seleção de URI persistente no app, mas **não identifica a escolha particular feita no S24 FE**.
- Confirmado na PRE511 que a biblioteca nativa `librexruntime.so` da mesma V48 contém `DiscImageDevice`, `HostPathDevice` e mensagens de `Runtime::SetupVfs`. A PRE513 complementa essas evidências pelo lado Java, mas a combinação de duas provas estáticas **NÃO equivale a um trace de montagem efetiva**.

## Próxima etapa e restrições
1. **PRE515 sugerida:** identificar o encadeamento de argumentos de `Ajustes.uriIso` / `Ajustes.argumentos` / `MotorNativo.argumentos` e `GameActivity.getArguments`, sem publicar caminhos pessoais. Distinguir origem Android selecionada (pasta `HostPathDevice` versus imagem ou content URI `DiscImageDevice`) **apenas se houver log da sessão, versão instalada/edição confirmada ou telemetria direta**. A PRE455 registrou logs de menus, mas não prova esse ramo.
2. Verificar loader guest de `ZDIR.BIN`, `ZZDATA4.BIN`, `GLOBAL\\ATTRIBUTES.BIN`, resolução da nova coleção `engine/bmwm3gtr_upgrade_engine_pre499` e checksum `0x296ad9ed`. A PRE502 é somente estrutura in-memory com nível 1 e torque +5% **sintético**, não patch funcional.
3. Depois investigar catálogo `FECarPartInfo`, custos válidos, `Physics::Upgrades`, identificação BMW `type=41`, compra/instalação/física/persistência em **save descartável**. `MARCEK` não deve ser modificado.
4. Não gerar V49 nem trocar V48 antes das provas. Manter pacote `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, touch/PG-9076, 1920×1080, cap 120 FPS, shaders/efeitos/física e limitação térmica. PRE479/PRE483 permanecem desligados.

**Distinção de status:** compilação V48 original validada; PRE513 análise estática de DEX comprovada; montagem de origem de jogo na sessão V48 **não comprovada**; V49 tunável **não compilada**; compra de BMW **não realizada**.
