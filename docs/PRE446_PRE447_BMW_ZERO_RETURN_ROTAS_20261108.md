# NFSMW Android — PRE446/PRE447: auditoria dos motivos possíveis do retorno zero (08/11/2026)

## Referências verificadas
- Logs reais V47 PRE444 (privados, não publicados): BMW M3 GTR `type=41` devolveu `candidate_count` **0** em Motor, Transmissão, Suspensão, Pneus, Freios e Indução forçada, mas **3** em Nitro; Fiat Punto `type=74` devolveu **4,4,3,3,3,4,3** nos sete tipos, incluindo Nitro 3. PRE445 sincronizou resultados com contexto canônico Drive. Os números são **valores retornados pela consulta**, não peças ou upgrades compráveis confirmados.
- APK V47 PRE434 SHA256 `ce2de9311b80670f7f4700e426ad1a77d6cd87a836df5ae3b36d4ec872cc7461`, pacote `io.github.nfsmwrecomp`, versionCode 47, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Versão V46 PRE401 continua referência de Nitro infinito validado em gameplay.

## PRE446 — somente leitura
- Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42495952223 — `PRE446_STATUS AUDIT_OK`.
- Script `automation/kaggle/pre446_bmw_zero_branch_readonly.py` verificou hashes de quatro shards PAL extraídos do backup PRE99 autenticado.
- `sub_823E5988` (`.28.cpp`, SHA256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`) tem três caminhos relevantes: (1) falta de entrada correspondente na cadeia de descritores, com `ctx.r3=0` na linha relativa **52**; (2) retorno normal de valor lido de atributo na linha relativa **104**, que pode ser zero; (3) saída de fallback com `ctx.r3=0` na linha relativa **144**, englobando várias causas.
- Chamadas internas a `sub_8214B858` e `sub_8214EDA8` confirmadas por fonte, mas **nenhum ramo específico executado pela BMW foi identificado**. A primeira rotina verifica campos do descritor e pode devolver falso. A montagem de lista em `sub_8256F818` salta o laço de criação normal dos itens quando o retorno da primeira consulta é <=0.
- A ausência global e permanente de um descritor de categoria parece menos compatível com o fato de que o Punto encontra resultados positivos para os mesmos sete tipos; **isto é inferência, não comprovação**, porque a tabela pode ter estado/contexto de runtime não auditado.

## PRE447 — prévia em memória, flag OFF
- Primeira run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496091952 — `failure` devido a comparação exata de linha ignorar indentação de C++. Não modificou nada persistente no jogo. Correção registrada no script.
- Run corrigida https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496205722 — `PRE447_STATUS AUDIT_OK`.
- Script `automation/kaggle/pre447_bmw_lookup_route_probe_dryrun.py`. Prévia produz hash SHA256 `aac0b47f03a43044899a5fd7150cd0691eee79f35b2c42f413919f0c61d9d230` a partir de original `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`.
- Prévia gera três marcadores de saída na função guest `sub_823E5988`, nas linhas relativas originais **60, 126, 153**, razão 1 (descritor de categoria ausente), 2 (caminho de leitura de valor de atributo, cujo valor pode ser zero ou positivo) e 3 (saída de fallback com várias subcausas). Usa `ctx.lr` e `ctx.r4` já presentes na entrada para filtrar apenas a **primeira chamada normal** do construtor `sub_8256F818` por `lr=0x8256F83C`. Sem chamadas guest, sem loads/stores guest adicionais, flag `NFSMW_PRE447_LOOKUP_ROUTE_ENABLE` desligada por padrão, transformação fonte reversível bit a bit.
- **Apenas preview estático.** Callback C++ ainda **não foi implementado, compilado/linkado**, não há CMake, APK V48, logs de rota do Galaxy S24 FE nem hipótese causal resolvida. A prévia não modifica a APK V47 ou o save.

## Próximo passo tecnicamente seguro
1. Fazer pré-compilação nativa ARM64 da fonte V47 equivalente incluindo o *callback* de rota com flag ligada **somente em árvore descartável**, verificando os três retornos, ambos marcadores PRE429, Nitro PRE398, CMake, contagem de símbolos e nenhuma escrita guest extra.
2. Somente depois avaliar APK V48 **diagnóstica** (versionCode >=48, mesmo certificado PERMANENTE), preservando V46/V47 e backups; V48 não deve modificar upgrades nem contornar HeroCar globalmente. Testar no aparelho somente após validação de assinatura.
3. Na eventual captura, distinguir BMW e Punto em sessões separadas, identificar (categoria, razão, valor) por consulta já existente; até lá não declarar qual rota gerou os zeros.
4. Não comprar `Option title`, `20/20`, `999.999.999`, não trocar `candidate_count=0` por 4, não escrever em saves, não chamar `sub_823E5988` artificialmente (efeitos de contador de referência guest). Preservar Nitro global V46, shaders/efeitos, 1920×1080, PG-9076, física e proteções térmicas; nenhum ganho de FPS comprovado.

**Evidências**: reports/artefatos das duas runs PRE446/447, este Markdown no GitHub. O `CONTEXTO_NFSMW.md` canônico do Drive deve receber apenas adendo, após backup integral e verificação de versão.
