# NFSMW PRE444 — logs reais das sete categorias (2026-11-08)

## Origem
Arquivos separados fornecidos pelo usuário: `nfsmw-bmw_tunningcompleta.log` (323.448 bytes, 1.530 linhas, SHA256 `53f47d001306b4af18c0860eebe1f21b02b97036e496a1e575bdcbf169cd4779`) e `nfsmw-punto_tunningcompleta.log` (338.773 bytes, 1.531 linhas, SHA256 `c7f84341264605dd9c1065ccca9aa1d6471533f835fe8a2e7f0e37fc4f2519ca`). Os logs privados não foram publicados no GitHub. Leitura integral local, sem modificação de save ou APK. Identidade: PRE292 type 41 BMW, 74 Punto; entrada PRE429 uma vez em cada sessão; exatamente sete LEVEL por sessão, mesmo manager `0x82C5D9E8`.

## Resultados reais
| Categoria PAL | ID | BMW | Fiat Punto |
|---|---:|---:|---:|
| Motor | 4 | **0** | **4** |
| Transmissão | 3 | **0** | **4** |
| Suspensão | 2 | **0** | **3** |
| Nitro | 6 | **3** | **3** |
| Pneus | 0 | **0** | **3** |
| Freios | 1 | **0** | **4** |
| Indução forçada | 5 | **0** | **3** |

**Observação:** valores de `candidate_count` são retornos de consulta existentes, **não contagem verificada de peças válidas/compráveis**. As sete consultas foram observadas na ordem acima. No código PAL PRE440 o retorno não positivo impede o loop normal de criação da lista de itens.

## Evidência adicional
- `NFSMW_PRE398_GLOBAL_NITRO_FULL active=1` **apareceu uma vez na BMW**, evidência de execução do trecho Nitro no processo; **não apareceu no Punto**, o que não comprova falha. Nenhuma medição explícita de refill em corrida.
- `pvehicle=0x00000000` registrado na entrada das duas sessões. Não atribuir os zeros da BMW exclusivamente a esse campo, nem inferir que permaneceu nulo durante toda a consulta.
- Cada log tem um erro PRE194 C3 com `copia_duplicada=true`; fallback desligou a thread de texturas durante a sessão. Nenhum texto literal `FATAL EXCEPTION` / `SIGSEGV` encontrado.
- Resolução interna 1920×1080 e teto configurado 60 FPS em ambos. Não houve medição de ganho de FPS.
- Com tipo de Nitro `6`, BMW **não** retorna zero em todas as categorias. Isso aumenta a prioridade de investigar atributos/tabela por categoria e por modelo em vez de forçar nível padrão.

## Próximo passo e salvaguardas
A divergência está amplamente caracterizada, mas **não está demonstrado qual dos caminhos da função `sub_823E5988` retorna zero** na BMW. Pode ser uma categoria sem descritor, lookup de atributo falho ou valor configurado como zero. Não trocar 0 por 4 nem forçar upgrades/nem comprar entradas `Option title`, `20/20`, `999.999.999`. Próximo passo é estudar fonte autenticada PRE99 e eventual prévia *somente em memória* de instrumentação passiva dos ramos, sem novas chamadas guest. Nenhuma V48 foi produzida; V46 segue referência comprovada de Nitro, V47 segue APK diagnóstica. Preservar save MARCEK, assinatura permanente, shaders, efeitos, física, PG-9076 e limites térmicos.

Auditorias: PRE440 `42489165527` e PRE441B `42489540474`, ambas aprovadas. Relatório em arquivo para usuário: `NFSMW_PRE444_BMW_PUNTO_7_CATEGORIAS_20261108.md`. Histórico canônico do Drive deve ser atualizado após backup integral com conferência byte a byte.