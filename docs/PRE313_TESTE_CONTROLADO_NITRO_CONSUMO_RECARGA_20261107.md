# PRE313 — Teste controlado Nitro até esgotar e recarregar, log real 2026-11-07

## Origem
- Arquivo enviado pelo usuário `nfsmw.log`, 1.609.683 bytes, 6.880 linhas, SHA-256 `2032fe0ac3fcc7e558ec1985e828eaa7482ddc9ea9cc87c926548d568ae00eb2`.
- Atenção: mesmo arquivo contém várias sessões anteriores, e o teste isolado novo está na janela 14:57:49–14:57:54; não somar sessões indistintamente.
- Procedimento informado diretamente pelo usuário: **acionou apenas Nitro até zerar visualmente e esperou recarregar completamente**. O código PRE247 apenas registra as primeiras 12 gravações por site/processo, portanto não capturou a conclusão da descarga e recarga.

## Evidência PRE247 da nova sessão

| Sites | Candidato/offset | Instante primeira→última amostra | 1ª→12ª float | Bytes iniciais→finais | Endereço guest observado |
|---|---|---|---|---|---|
| 1 e 2 | Nitro +252 | 14:57:49.329→49.512 | 0,99333334→0,92000008 | `0x3F7E4B18`→`0x3F6B8520` | `0xBFA9E7FC` |
| 3 e 4 | Nitro +252 | 14:57:53.864→54.048 | 0,00055555557→0,00666666590 | `0x3A11A2B4`→`0x3BDA740C` | `0xBFA9E7FC` |
| 5 | Nitro +252 | Sem evento | — | — | — |
| 7 | Speedbreaker +132 | 14:57:50.432→50.615 | 1,00133336→1,00066662 | `0x3F802BB1`→`0x3F8015D8` | `0xBFA7CD34` |
| 8 | Speedbreaker +132 | 14:57:50.432→50.615 | 1,0→1,0 | `0x3F800000`→`0x3F800000` | `0xBFA7CD34` |
| 6 | Speedbreaker +132 | Sem evento novo | — | — | — |

- Sites Nitro 1 e 2 registraram a **mesma sequência decrescente**; sites 3 e 4 registraram a **mesma sequência ascendente**. Isso sustenta consumo e recarga, mas não informa se o site 2/4 é limitador, espelho ou outro store sem revisar fluxo PPC e sem logs adicionais.
- Informações de uso do Nitro até esvaziar e de recarga total vêm da observação do usuário. **O log não registra os valores finais `0` e `1` desses dois eventos**, pois a cota de 12 amostras por site foi consumida em cerca de 184 ms.
- Mesmo sem pressionar Speedbreaker, sites 7/8 apareceram durante o teste só de Nitro e o site 8 limitou a 1,0; portanto não se deve interpretar a simples presença de 7/8 como comprovação de ativação pelo usuário.
- Sites PRE246 dinheiro não apareceram nesse teste.
- Não há indício de que checar esse log tenha alterado o save; a aplicação V40 contém rotinas de save normais, cujo estado deve continuar protegido por backup.

## Consequência para implementação

1. PRE312 auditou fonte PAL autentificada com cinco stores Nitro, run `42398849592` `AUDIT_OK`, sites 1–5 em linhas relativas `377,411,508,518,525`. O workflow original não enviou artefato por nome de arquivo divergente, e o caminho foi corrigido posteriormente. Revalidar se precisar dos trechos antes de patch.
2. Próximo diagnóstico deve resumir **mudanças de faixa, mínimos, máximos, saturações e número de eventos**, armazenando snapshots sem logar a cada quadro. Capturar o valor final de cada ramo e eventuais registros de 0/1, sem adicionar leituras guest não confiáveis.
3. Manter política PRE309 desligada por padrão, com permissão explícita, fail-closed, original preserved quando OFF, sem alteração de dinheiro e sem ativar cheats na V40.
4. Só testar Nitro infinito mediante validação do *store definitivo*, preservação de lógica física e recarga, benchmark contra OFF e cópia independente do save MARCEK. V41 futuramente deve manter pacote e assinatura permanente existentes.

**Estado:** evidência de consumo e início de recarga Nitro comprovada, ciclo completo observado pelo usuário mas não instrumentado até o fim, sem cheat ativo ou compilação nova.
