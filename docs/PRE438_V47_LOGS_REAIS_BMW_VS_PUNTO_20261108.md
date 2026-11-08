# PRE438 — V47: comparação real BMW versus Fiat Punto (2026-11-08)

## Dados coletados
Dois logs enviados separadamente pelo usuário e lidos localmente, sem edição de save/APK. **Não publicar os arquivos brutos no repositório público.**

| Campo | Fiat Punto | BMW M3 GTR |
|---|---|---|
| Arquivo | `nfsmw-punto.log` | `nfsmw-bmw.log` |
| Tamanho | 376.962 bytes | 395.130 bytes |
| Linhas | 1.609 | 1.719 |
| SHA-256 | `8a1a319b264c05c42596e03ae45537b2c6a4756894ef53c377aa2f20ff5b81c9` | `4d3f04e4b0fdb13a7328789de411fdf3b90db1312cab1ee2c028faef082e5323` |
| `PRE292_BMW_MENU type` | **74** | **41** |
| `PRE429_ENTRY` | 1 | 1 |
| `PRE429_LEVEL category` | **4** | **4** |
| `PRE429_LEVEL candidate_count` | **4** | **0** |
| `manager` | `0x82C5D9E8` | `0x82C5D9E8` |
| `pvehicle` registrado na entrada | `0x00000000` | `0x00000000` |
| PRE194 C3 | 1 alerta | 1 alerta |
| PRE398 marcador Nitro global | 0 | 0 |
| `FATAL EXCEPTION` / `SIGSEGV` no texto | 0 / 0 | 0 / 0 |

## Eventos auditáveis

- Punto: `PRE429_ENTRY` 11:01:51.248; `PRE292_BMW_MENU type=74` 11:01:51.249; `PRE429_LEVEL manager=0x82C5D9E8 category=4 candidate_count=4` 11:01:58.194.
- BMW: `PRE429_ENTRY` 11:03:42.555; `PRE292_BMW_MENU type=41` 11:03:42.556; `PRE429_LEVEL manager=0x82C5D9E8 category=4 candidate_count=0` 11:03:48.224; segundo evento de menu BMW às 11:03:59.175.
- Ambos têm `pvehicle=0x00000000` **na entrada**, portanto isso não diferencia BMW/Punto, tampouco prova persistência do ponteiro nulo.

## Interpretação e limites

**Confirmado em runtime:** para o mesmo endereço-base da personalização e categoria interna 4, a chamada existente devolveu contagem candidata **4 no Punto** e **0 na BMW M3 GTR**, identificadas de forma independente pelo marcador de menu `type=74/41`.

**Hipótese plausível:** o catálogo de desempenho da BMW é vazio nessa categoria, consistente com as opções `Option title` / `20/20` / `999.999.999`. Não prova que todas as categorias estejam vazias, que o número 4 sejam quatro peças compráveis, nem que a função esteja inequivocamente identificada como `GetMaxLevel` na build PAL.

Na reconstrução pública `dbalatoni13/nfsmw` (`PhysicsUpgrades.hpp`), `PUT_ENGINE=4` (motor): https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Physics/PhysicsUpgrades.hpp . A identidade exata entre esse enum e `category=4` do marcador PAL ainda depende de prova; **não chamar oficialmente de motor até validação cruzada**.

Os dois logs contêm alerta C3 PRE194 de cópia duplicada e desligamento de thread de ligações de texturas. Nenhum `FATAL EXCEPTION`/`SIGSEGV` textual, o que não comprova estabilidade. Nenhum marcador Nitro PRE398 nas sessões de menus, sem implicação sobre funcionamento do Nitro no gameplay. Resolução interna 1920x1080 e limite 60 FPS reportados.

## Decisão de segurança

- **Não alterar `candidate_count=0` para 4**, não fabricar pacotes nem comprar opções inválidas.
- Se a interface permitir, visitar demais categorias normais de desempenho em sessões separadas BMW/Punto e preservar os logs individuais. Outras categorias não foram observadas aqui: **ausência de log não equivale a zero**.
- Examinar apenas via fonte auditada a origem do valor zero e a ligação às tabelas de atributos/pvehicle. Não invocar `sub_823E5988` artificialmente, pois pode modificar referências guest.
- V47 PRE434 compilada, assinada e instalada/aberta ao ponto de emitir os logs — mas confirmação explícita de instalação pode ser inferida dos logs da V47; Nitro da V47 não retestado. V46 PRE401 continua baseline de Nitro infinito global comprovado.
- Preservar save `MARCEK`, Fiat Punto, BMW, Junkman, Nitro, C3/SDL, gráficos, controles, resolução e proteções térmicas. Nenhum ganho de FPS comprovado.
- Contexto canônico Drive deve receber adendo PRE438 após backup integral e leitura de versão atual. Logs completos ficam fora do GitHub.

Caminho local adicional: `NFSMW_PRE438_BMW_PUNTO_V47_LOG_ANALISE_20261108.json` e `NFSMW_PRE438_BMW_PUNTO_V47_RELATORIO_20261108.md` criados a partir dos dois arquivos, sem alterar os originais.
