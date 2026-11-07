# PRE344 — V42: quatro destinos de Nitro na sessão nova (2026-11-07)

## Fonte real e integridade
- **Arquivo fornecido pelo usuário:** `nfsmw.log` nesta conversa. Análise local somente leitura.
- SHA-256 `6bb43f510a3818b23a7c5b3430f9f53c93c3a6bb35e1c0e5638f728c25085441`; 794.852 bytes; 3.074 linhas.
- Janela do log: `2026-11-07 19:30:10.967`–`19:33:18.373`.
- Marcadores: PRE336 **62**; PRE316 **188**; PRE247 **72**.
- Diferente da coleta PRE343, o arquivo é uma sessão curta, não o log cumulativo antigo. O teste anterior foi explicitamente descrito pelo usuário como **exploração livre sem adversários**. O contexto exato do novo teste (corrida, quantidade de veículos) deve ser confirmado pelo usuário; o log isolado não o prova.

## Resultado PRE336 — quatro endereços guest distintos

| Slot efêmero por processo | Primeiro registro | Registros PRE336 | Sites registrados | Máscara final |
|---|---|---:|---|---|
| 1 | 19:31:12.654 | 42 | 1/2/3/4 | 0x0F |
| 2 | 19:31:20.826 | 8 | 1/2/3/4 | 0x0F |
| 3 | 19:31:53.458 | 8 | 1/2/3/4 | 0x0F |
| 4 | 19:31:58.397 | 4 | 1/2/3/4 | 0x0F |

- `distinct` alcançou **4**, todas as observações `overflow=false`; nenhum site 5.
- O monitor PRE336 identifica destinos de escrita guest, **não modelos de carro**; valores de slot são posições de tabela locais ao processo, NÃO player/NPC.
- A comparação com a PRE343 anterior (`distinct=1` em exploração livre com carro sozinho) indica mudança significativa no contexto de execução.
- PRE247, limitado aos primeiros 12 logs/site, observou apenas o endereço de Nitro `0xBFB0BF7C` nos sites 1–4, por isso **não permite mapear os demais slots aos endereços brutos**; Speedbreaker sites 7/8: `0xBFA7CD34`.
- O endereço observado agora (`0xBFB0BF7C`) **é diferente** do primeiro endereço visto na V41 e PRE343 (`0xBFA9E7FC`), reforçando que endereços guest não são identidades estáveis e não devem ser fixados em cheat.

## PRE316 — atividade de consumo e recarga
- Consumo site 1: 45 linhas, último checkpoint agregado `n=1024`, `last=0.8233335`, `min~0.0000008149`, `max~0.99666667`.
- Consumo site 2: 45 linhas, último `n=1024`, `last=0.71500033`, `min=0`, `max~0.99666667`.
- Recarga sites 3 e 4: 49 linhas cada; últimos `n=8192`, `last~0.85000169`; máximo aproximadamente 1.0005/1.0000.
- **As contagens PRE316 são agregadas por site, não por slot**, portanto não atribuir esses floats a um carro específico.

## Erros independentes
- `19:30:34.672`: aviso/erro C3 da thread de texturas: desabilitada até o fim da sessão por inconsistência de índice em voo, marcador PRE194.
- `19:31:03.268`: amostragem de fingerprints de textura C3 desabilitada depois de 4555 reverificações devido a divergência.
- Nenhuma ocorrência textual de `FATAL EXCEPTION` ou `SIGSEGV` neste arquivo. Isso não comprova estabilidade fora da janela.
- Configuração de inicialização `1920x1080` interna e `limite FPS 60`, não o objetivo de 120; não alegar ganho de desempenho.

## Impacto na hipótese Nitro infinito
- **Verificado:** a mesma função PAL Nitro processou pelo menos quatro destinos guest, cada um com sites 1/2/3/4. Uma intervenção global indiscriminada em `sub_82424AF0` pode modificar mais de uma instância e não é segura como cheat exclusivo do jogador.
- **Não verificado:** quatro carros distintos, slots identificados jogador/IA, qual slot pertence ao jogador, ou que a função só roda em corrida.
- Próximo gate: estabelecer referência **independente** ao carro do jogador. Em instrumentação futura, comparar `ctx.r3` à referência independente (sem hardcode de endereços), com estado `desconhecido` por padrão e teste negativo IA. Não gerar cheat global.
- V42 continua diagnóstica com Nitro infinito desativado. V41 backup, `MARCEK`, controles, gráficos, assinatura permanente e proteções térmicas preservadas.
