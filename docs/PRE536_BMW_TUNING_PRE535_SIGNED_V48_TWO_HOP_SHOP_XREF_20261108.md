# PRE536_BMW_TUNING_PRE535_SIGNED_V48_TWO_HOP_SHOP_XREF_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW-Recompiled-Mobile (Need for Speed: Most Wanted 2005, Xbox 360 PAL recompilado para Android), investigação da tunagem comprável e persistente da BMW M3 GTR da carreira. **Base preservada:** APK release V48 PRE452, `io.github.nfsmwrecomp`, versionCode 48, SHA256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`; Nitro infinito PRE398, controle PG-9076, touch, 1920×1080, cap 120 FPS, shaders, efeitos, física e proteção térmica. Save `MARCEK` intacto; certificado permanente de assinatura SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nenhuma V49 construída ou testada nesta etapa.

## PRE535 — auditoria read-only de duas camadas de chamadas na V48 PAL original
- [GitHub Actions 42536895518](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42536895518) **`AUDIT_OK`**, relatório `docs/PRE535_V48_PAL_SHOP_TWO_HOP_PLT_GRAPH_READONLY.json`.
- Fonte: mesmo APK **assinado V48** do Drive `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`, mesma `lib/arm64-v8a/libmain.so` PAL SHA256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`, ambos reautenticados. `.plt` ELF original de 17.107 entradas de realocação `R_AARCH64_JUMP_SLOT` e **15.598** nomes guest numéricos resolvidos (método PRE533).
- **Cinco raízes de análise estática:** lista `sub_8256F818`, vizinha da oficina `sub_8256CBC8`, chamadora da lista `sub_82582F70`, e rotinas que historicamente escrevem campo offset +12 `sub_8256BFC8` e `sub_82564D80`. **Não existe prova de que as escritas de offset +12 sejam dinheiro, cobrança ou compra.**
- **72 funções vizinhas imediatas**, **76 funções distintas auditadas**, somando **63.192 bytes de código ARM64**; dados inspecionados na runner apenas em memória e diretivas/metadados numéricos publicados, sem artefato binário do jogo.
- Alcance de **até duas chamadas guest** por raiz: lista **30 funções distintas**; vizinha `sub_8256CBC8` **34**; chamadora `sub_82582F70` **58**; escritora A `sub_8256BFC8` **17**; escritora B `sub_82564D80` **119**. Estes conjuntos incluem diversos utilitários partilhados, não um caminho sequencial executado.
- Interseção das raízes de menu com as raízes de escrita: **12 funções numéricas** excluindo as próprias raízes. Identidades observadas: `sub_820E25C0`, `sub_82152A38`, `sub_8215CB08`, `sub_821E02C0`, `sub_8227FD70`, `sub_82282A70`, `sub_82284CC0`, `sub_82284E88`, `sub_822BCE60`, `sub_822CC740`, `sub_822FEB70`, `sub_823EAE40`.
- Um exemplo de convergência verificada (2 chamadas no máximo em cada ramo):
  - lista menu → `sub_8256F818` → `sub_8215CB08`;
  - vizinha menu → `sub_8256CBC8` → `sub_8215CB08`;
  - escritora histórica B → `sub_82564D80` → `sub_825693C0` → `sub_8215CB08`.
- Outro exemplo: chamadora de lista `sub_82582F70` → `sub_82587498` → `sub_820E25C0`, enquanto escritora histórica A `sub_8256BFC8` → `sub_825878C8` → `sub_820E25C0`.
- Os percursos são **arestas estáticas ARM64 BL mapeadas pela PLT original**, **não traces de execução**; uma função compartilhada pode ser utilitário (memória, mensagens, categorias, física genérica, etc.). Não lhe atribuir semântica, não inferir existência de um caminho de checkout nem aprovar modificação da coleção BMW.

## Limitações e próximo gate seguro
1. **Continuam não comprovados:** nome/endereço da implementação guest `Physics::Upgrades::SetPackage`, se a V48 efetivamente executou `libmain.so` PAL no S24 FE, carregamento do VPAK experimental PRE502/PRE518, resolução de `engine/bmwm3gtr_upgrade_engine_pre499`, preço/desbloqueio efetivo, aplicação de potência, compra, rollback e persistência.
2. Não confundir fórmula do código PC (PRE524, custo PAL de tabela nível global 4 = **98.000** como **hipótese de preço para único motor local**) com custo realmente exibido na BMW, nem equiparar `REX_STORE_U32(+12)` a débito monetário. PRE526 demonstrou risco de cobrança antes de instalação na fonte PC, ainda sem equivalência guest provada.
3. **PRE537 proposta:** auditar de maneira read-only as **12 interseções**, distinguindo auxiliares genéricos dos candidatos específicos da oficina por tamanho, densidade de chamadas, sinais estruturais e ocorrência em diversos chamadores, sem deduzir significado apenas por endereço. Observar quando há caminho real até alguma rotina com `SetPackage` por evidências de implementação ou instrumentação passiva. Nenhuma build V49 ou compra antes do gate.
4. Antes de teste ativo, exigir cópia isolada e **save descartável**. Nunca usar o save `MARCEK` para uma transação experimental, não ligar flags PRE479/PRE483, não modificar ISO/ZIP original, ZDIR/ZZDATA, V48, controle PG-9076, proteção térmica ou chave release.

**Estado exato:** PRE535 auditoria PAL ELF estática concluída; 12 interseções confirmadas; **SetPackage guest desconhecido**, loja BMW não habilitada, APK V49 não construída, instalação não testada, físico não medido, save MARCEK não modificado.
