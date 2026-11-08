# NFSMW PRE442 — Auditoria PAL de categoria 4 / Motor e possíveis saídas zero (08/11/2026)

## Evidências de aparelho já confirmadas (PRE438/PRE439)
- Logs privados separados, Fiat Punto `type=74` e BMW M3 GTR `type=41` no Galaxy S24 FE com APK diagnóstica V47 PRE434.
- `NFSMW_PRE429_LEVEL manager=0x82C5D9E8 category=4 candidate_count=4` no Punto, e `category=4 candidate_count=0` na BMW. Não foi observada outra categoria nos dois logs.
- Os logs completos continuam privados, fora do repositório GitHub. Fontes originais e hashes constam em `docs/PRE438_V47_LOGS_REAIS_BMW_VS_PUNTO_20261108.md`.

## PRE440 — cadeia de consulta PAL, somente leitura
- Execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489165527: `PRE440_STATUS AUDIT_OK`, cinco arquivos `nfsmw_recomp.*.cpp` com SHA-256 verificado contra snapshot autenticado PRE99. **Nenhum código guest executado ou modificado**.
- Chamador `sub_82582F70` (`.11.cpp`) passa tipo em `r24` via `ctx.r4 = r24` e chama `sub_8256F818` no bloco relativo 687–696. Em seguida, percorre a lista encadeada (linhas 704–713).
- Construtor `sub_8256F818` (`.57.cpp`) preserva `ctx.r4` em `r26`, prepara `ctx.r3=manager+8` e chama `sub_823E5988`. O retorno é colocado em `r21`. Na linha 48, se `r21<=0`, salta a `loc_8256F990`, antes do laço de alocação das opções. **Portanto a observação BMW 0 impede o laço normal de opções para essa chamada**.
- `sub_823E5988` (`.28.cpp`) percorre uma tabela de descritores por `ctx.r4`. Se não encontra chave correspondente, devolve `0` no bloco relativo 51–60; outros casos devolvem zero no bloco relativo 142–152. Quando encontra uma entrada, chama `sub_8214B858` para resolver atributo e, conforme o resultado, `sub_8214EDA8`. Pode retornar valor derivado de atributo, não sendo uma constante de modelo. A função possui **escritas de contadores de referência guest U16**; não a chamar artificialmente.
- `sub_8214B858` (`.50.cpp`, PRE428 run 42451675734) lê `[ctx.r3+4]`, devolve 0 se campo nulo, caso contrário resolve atributo (calls `sub_82148718`, `sub_8214E9E0`) e verifica `[out+8]`. Como o `r3` passado do chamador foi `manager+8`, isso consulta o descriptor associado ao contexto do veículo. **Não é a mesma medição que o `pvehicle=0` no evento de entrada da personalização PRE429**.
- **Limite:** a PRE429 mede somente o retorno final. Não foi registrado qual ramo da `sub_823E5988` causou o zero da BMW: descritor não encontrado, falha ao resolver atributo, valor zero ou outro caminho interno. Evitar explicações causais definitivas.

## PRE441 e PRE441B — mapeamento PAL de categorias
- Runs https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489366761 e https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489540474, ambos `AUDIT_OK`.
- No início da `sub_82582F70`, `category_offset = [screen+324] - 513`, switch 0–6. Cada ramo prepara `r24` que depois é passado a `sub_8256F818`:
  - `screen_category=513` → `r24=4` (**Motor**);
  - `514` → `3` (Transmissão);
  - `515` → `2` (Suspensão);
  - `516` → `6` (Nitro);
  - `517` → `0` (Pneus);
  - `518` → `1` (Freios);
  - `519` → `5` (Indução forçada).
- Confirmado pelo código da edição PAL e corroborado pela reconstrução pública `dbalatoni13/nfsmw` (consulta somente leitura) em `CarCustomize.cpp` e `PhysicsUpgrades.hpp`, que associa `PUT_ENGINE = 4`. O tipo interno `4` **é a consulta de Motor**, mas é também o valor inicial/default de `r24` no chamador; os logs PRE429 não contêm a categoria de tela `[screen+324]`, então não provar que o usuário visualmente abriu Motor em cada sessão apenas pelo log.
- `sub_8256CB60` mapeia o valor de categoria para limites estáticos (incluindo 4 para 4) apenas depois da contagem >0, e não autoriza alterar `0` da BMW ou fabricar upgrades.

## Conclusões e próximo passo
1. A rotina não fabrica os itens normais quando recebe **zero**. A discrepância `BMW=0, Punto=4` na mesma consulta é real e pode resultar de atributos/referências de catálogo específicos do carro. **Ainda não é prova de todos os níveis ou da causa precisa**.
2. **Não** mudar o resultado BMW de 0 para 4, nem desbloquear compra/stock/Junkman. Evitar opções inválidas `Option title`, `20/20`, `999.999.999`.
3. Sem nova APK, usar a **V47 já assinada** e, se o menu permitir, navegar pelas demais seis categorias de Desempenho em sessões isoladas BMW/Punto (sem comprar). Guardar logs separados e indicar as telas abertas; ausências de eventos não significam 0.
4. Se precisar distinguir o ramo que retorna zero, **projetar e validar em memória primeiro** uma eventual instrumentação de saídas sem novas chamadas guest ou leituras/escritas, sem reiniciar investigação do Nitro nem construir APK antes de revisar.
5. Preservar o save `MARCEK`, a V46 (Nitro infinito global comprovado em PRE407) e a V47, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução 1920×1080, shaders, efeitos, física, controle PG-9076 e proteções térmicas. Nenhum FPS extra comprovado.

**Status de auditoria:** PRE440 e PRE441B aprovadas; sem mudança de jogo, save, APK ou credenciais. O contexto canônico do Google Drive deve ser atualizado com cópia integral e leitura de verificação, sem substituir histórico.
