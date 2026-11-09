# PRE540_BMW_TUNING_PRE539_V48_GUEST_823EAE40_CALLSITES_20261108

**Data local:** 2026-11-08 (UTC do CI já pode aparecer como 2026-11-09). **Projeto:** NFSMW-Recompiled-Mobile; Xbox 360 PAL para Android. Continuação de PRE538 com **investigação somente leitura** para habilitar no futuro a tunagem realmente comprável, instalada e persistente da BMW M3 GTR carreira, tipo 41. A APK baseline **V48 PRE452**, o Nitro infinito PRE398, PG-9076/touch, gráficos/shaders/física, resolução interna 1920×1080 e limite 120 FPS são preservados, assim como o save `MARCEK`. Certificado release permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` não acessado.

## PRE539 — investigação da função guest pouco difundida sub_823EAE40
- [GitHub Actions 42538596295](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42538596295), resultado **`AUDIT_OK`**, relatório `docs/PRE539_ORIGINAL_V48_PAL_823EAE40_SEVEN_CALLERS_READONLY.json`.
- Origem reautenticada: APK original **V48** Drive ID `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`, SHA-256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`; biblioteca PAL `lib/arm64-v8a/libmain.so` SHA-256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`. Símbolos `sub_...` definidos em `.dynsym`, chamadas `BL` ligadas pelos deslocamentos originais `.rela.plt`/PLT AArch64, 15.598 destinos guest. A análise não modifica o binário e não executa o jogo.
- **Função alvo:** `sub_823EAE40`, corpo AArch64 de **2.964 bytes**. **7 funções caller distintas** e **9 sítios `BL`** resolvidos:
  - `sub_8226B228` — 1 sítio no offset de código nativo `+872`;
  - `sub_8226B4C0` — 1 sítio `+48`;
  - `sub_8254E908` — 1 sítio `+996`;
  - `sub_8255C1C8` — 1 sítio `+508`;
  - `sub_82566BE8` — **2** sítios `+580` e `+1016`;
  - `sub_8256CE68` — **2** sítios `+220` e `+468`;
  - `sub_82584880` — 1 sítio `+556`.
- A função alvo tem exatamente **4 chamadas de saída guest**, uma para cada `sub_823EB290`, `sub_823EB3B0`, `sub_823E4130` e `sub_823E4588`. Nenhuma foi demonstrada como manipulação de upgrades.
- Análise de contexto de **12 mnemonics anteriores** para cada um dos nove `BL`:
  - **5 de 9** sítios possuem exatamente a sequência `str, str, bl, ldr, mov, mov, add, add, str, add, str, str` (`sub_8226B228` +872, `sub_8255C1C8` +508, `sub_82566BE8` +580/+1016, `sub_82584880` +556).
  - Um **sexto** sítio (`sub_8256CE68` +468) compartilha **as 10 últimas** instruções dessa sequência, mas as duas primeiras são `rev, stp`, não `str, str`.
  - Os outros **3 de 9** sítios exibem sequências diferentes (`sub_8226B4C0` +48, `sub_8254E908` +996, `sub_8256CE68` +220). Portanto não afirmar que seis sítios possuem 12 mnemonics idênticas. Essa correção foi feita após nova verificação exata do JSON publicado.
- A inspeção registra pistas limitadas de escrita de registradores de argumentos próximos das chamadas, **sem resolver proveniência completa, valores, assinaturas, parâmetros ou transações**. O mesmo padrão de prólogo/chamada pode aparecer em helpers genéricos.
- Dois percursos previamente reconhecidos na PRE535 seguem estruturalmente existentes: lista `sub_82582F70 → sub_8256CE68 → sub_823EAE40`, e rotina histórica de escrita `sub_82564D80 → sub_8254E908 → sub_823EAE40`. **Não há comprovação de que a rotina de escrita modifique dinheiro ou que a função alvo seja `SetPackage`**, nem execução observada na V48 no Galaxy S24 FE.

## Consequência para a direção da investigação
1. **PRE541 proposta:** usar as assinaturas de instruções e as quatro funções chamadas por `sub_823EAE40` para caracterizar qual tipo de auxiliar ela é (atributos, leitura ou operação genérica) sem atribuir significado por proximidade de endereço. Priorizar uma prova de função guest realmente capaz de aplicar um upgrade, como `SetPackage`, em vez de ampliar indefinidamente interseções genéricas.
2. PRE502/PRE518 (BMW com coleção `engine/bmwm3gtr_upgrade_engine_pre499`, contador de engine upgrades 0→1 e torque experimental +5%) permanecem **RAM-only**. A aceitação de `ExpN` adicional pelo loader guest, resolução do hash e `RefSpec`, preço/desbloqueio da BMW e aplicação da física **não foram demonstradas**.
3. Não executar compra experimental no save `MARCEK`; PRE526 identificou risco de cobrança antes de falha de instalação **somente no código PC de referência**, não no guest PAL. Quando houver prova de loader/aplicação, testar em cópia isolada e save descartável, com rollback e regressões.
4. Não modificar original ISO, ZIP, ZDIR, ZZDATA, APK V48 nem credenciais/chave permanente. Preservar Nitro PRE398, PG-9076, gráficos, física e restrições térmicas. Não declarar V49 build, instalação ou funcionamento sem evidência.

**Status verificado:** PRE539 auditoria estática `AUDIT_OK`, **7 callers/9 BL**, 5 sítios com 12 mnemonics idênticas, um sexto com sufixo de 10; **SetPackage guest desconhecida**, tunagem BMW não habilitada, APK V49 não construída, saves intactos, ganhos reais de potência/FPS não medidos.
