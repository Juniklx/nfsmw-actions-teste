# PRE530_BMW_TUNING_PRE528_PRE529_GUEST_PAL_CALLGRAPH_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW-Recompiled-Mobile, Xbox 360 PAL para Android, objetivo de habilitar personalização verdadeira da BMW M3 GTR da carreira (type 41). **Baseline intocada:** V48 PRE452 release `io.github.nfsmwrecomp` versionCode 48, Nitro infinito PRE398, PG-9076, shaders, 1920×1080, cap 120 FPS e save `MARCEK`. Assinatura release permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. **NENHUMA V49, nenhuma alteração de saves, nenhuma instalação/compra experimental neste estágio.**

## PRE528 — guest PAL gerado: varredura autenticada de chamadas de contagem e atributos

- Execução [GitHub Actions 42534546432](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42534546432): `AUDIT_OK`; relatório `docs/PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_READONLY.json`.
- Fonte privada **histórica PRE99**, TAR SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39` e 874.780.689 bytes, validada antes da leitura. Foram varridos **129 arquivos C++ PAL recompilados**, **56.338 funções**, **135.601.739 bytes de código gerado**. O scanner verificou SHA-256 fixos de cinco shards/rotinas antes de analisar. Nenhum código do jogo foi publicado, alterado ou compilado novamente.
- Âncoras geradas, apenas identidades numéricas:
  - `sub_8256B440` — entrada histórica investigada pela PRE429 (arquivo `.15.cpp`, SHA `414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a`).
  - `sub_8256F818` — construção da lista de categorias da oficina (arquivo `.57.cpp`, SHA `a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c`). **Duas** chamadas diretas a `sub_823E5988`; caller direto identificado `sub_82582F70`.
  - `sub_823E5988` — consulta da quantidade de upgrades/atributo (arquivo `.28.cpp`, SHA `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`). **23** pontos de chamada diretos distribuídos no código gerado. O corpo original possui **dois** pontos de retorno de zero em `ctx.r3` e **um** retorno do valor lido do atributo. A própria função chama `sub_8214B858` e `sub_8214EDA8`.
  - `sub_8214B858` — verificação de atributos, **12** chamadas diretas no conjunto analisado (arquivo `.50.cpp`, SHA `f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d`).
  - `sub_8214EDA8` — rotina de leitura de atributo, **65** chamadas diretas no conjunto analisado (arquivo `.83.cpp`, SHA `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`).
- Os locais de chamada foram extraídos de **instruções executáveis geradas**, não de comentários. O valor de uma chamada pode ser zero por mais de um motivo; as contagens históricas BMW/Punto da V47 não identificaram qual ramo foi executado para a BMW na versão V48.
- Importante: apesar de serem fontes **guest PAL**, são o backup **PRE99**, não bytecode de V48 ligado e executado no S24 FE. A compilação V48 acrescentou instrumentação passiva à receita; não inferir igualdade exata de implementação por proximidade de endereços.

## PRE529 — cruzamento entre menu, vizinhos de categoria e escrita de campo +12

- Execução [GitHub Actions 42534824686](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42534824686): `AUDIT_OK`; relatório `docs/PRE529_PAL_GUEST_SHOP_NEIGHBORS_MONEY_STORES_READONLY.json`.
- Em novo percurso autenticado do mesmo PRE99, foram examinadas **12 funções numéricas** com contadores de loads/stores, branches e chamadas, sem publicar os corpos do código.
- `sub_8256CBC8` (arquivo `.126.cpp`, 389 linhas geradas) realiza **três** chamadas à consulta `sub_823E5988`; tem **um caller direto** `sub_825757F0`. Seu papel concreto no fluxo de checkout **não foi identificado**.
- `sub_8256C2F0` (arquivo `.100.cpp`, 244 linhas) tem **seis** callsites diretos, incluindo a lista `sub_8256F818`. Não atribuir a ela a etiqueta `GetPartPrice` sem provas.
- `sub_82582F70` (arquivo `.11.cpp`, 1.231 linhas) é o único caller direto de `sub_8256F818`, no grafo estático examinado. A atividade em tempo de execução **não foi observada** nesta auditoria.
- As rotinas históricas relacionadas a gravações de um campo de offset `+12` na PRE239, `sub_8256BFC8` e `sub_82564D80`, apresentam **três + cinco = oito instruções `REX_STORE_U32`** em endereços com offset 12. `sub_8256BFC8` tem apenas um caller direto observado, `sub_82572D10`. **Crítico:** a auditoria **NÃO** prova que essas escritas constituem débito monetário, compra de pacote ou qualquer transação de upgrade; tampouco que `sub_82564D80` não tenha callers indiretos.
- Nenhum endereço equivalente ao `Physics::Upgrades::SetPackage` foi identificado de forma verificável, e a cadeia `Checkout→InstallPerfPkg→SetPackage` continua **hipótese de equivalência** baseada nos nomes/estruturas da fonte pública reconstruída PC. A PRE526 comprovou apenas na fonte PC a possibilidade de cobrança antes de falha na instalação; não no guest Android.
- A PRE502/PRE518 continua sendo VPAK **sintético +5%** e `engine_upgrades=1` reconstruído e validado **em memória**. Ainda não entrou no loader, física, loja, APK nem save. PRE522/523 confirmaram preços originais PAL do `FE_ATTRIB.BIN`, mas **98.000** para BMW nível único permanece interpretação condicional da regra de preço PC (PRE524), não compra real.

## Próximo gate PRE531 sem alterações de gameplay

1. A partir do mapa PRE528/529, investigar, por **inspeção de fonte guest** e ancoragem estrutural, as funções candidatas responsáveis pela aplicação do pacote e pelo roundtrip `FECustomizationRecord` → `Physics::Upgrades::SetPackage`, **sem inventar nomes, endereços nem declarar execução**.
2. Provar ligação com a **árvore efetivamente compilada V48**, de preferência com fonte/manifesto verificado ou instrumentação totalmente passiva futura; a fonte PRE99 não satisfaz isso sozinha.
3. Só avançar à experiência de loader VPAK e compra quando existir protocolo reversível isolado **e save descartável**. Nunca comprar upgrades no perfil MARCEK ou instalar versão que possa cobrar sem devolver dinheiro após falha.
4. Preservar V48, Nitro PRE398, controles físicos/touch, resolução, gráficos, física, limites térmicos e **certificado permanente**. Não abrir/sequer usar credenciais em auditorias estáticas.

**Status inequívoco:** PRE528/PRE529 **auditoria estática PAL histórica aprovada**; SetPackage guest **não identificado**, checkout guest **não comprovado**, V48 efetiva **não testada por essas auditorias**, tuning BMW **não funcional**, nova build **não feita**, save **não alterado**, ganhos de desempenho/física **não medidos**.
