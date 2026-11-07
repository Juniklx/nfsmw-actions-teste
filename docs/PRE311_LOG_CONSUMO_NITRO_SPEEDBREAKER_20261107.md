# PRE311 — Evidências de consumo e recarga dos cheats a partir do novo nfsmw.log

Data: 2026-11-07. Fonte: log anexado pelo usuário, analisado localmente (não publicado integralmente).

**Integridade do log:** SHA-256 `d0f9bd0344399f38fcaac110a6a4328e32efe6ccf58dc1cd242ed8f8efbbc386`, 1.168.427 bytes, 5.019 linhas.

**Atenção:** arquivo contém sessões anteriores (11:27, 14:14) e a sessão nova (14:53). Não somar contagens do arquivo como se todas fossem testes novos.

## Sessão nova 14:53 — PRE247

| Candidato PRE247 | Store PAL | Primeira → última leitura | Registros | Endereço guest observado |
|---|---|---|---:|---|
| Nitro, site 1 | +252, sub_82424AF0 | 0,9933333 → 0,9200001 | 12 | 0xBFA9E7FC |
| Nitro, site 2 | +252, sub_82424AF0 | 0,9933333 → 0,9200001 | 12 | 0xBFA9E7FC |
| Nitro, site 3 | +252, sub_82424AF0 | 0,3470036 → 0,3507603 | 12 | 0xBFA9E7FC |
| Nitro, site 4 | +252, sub_82424AF0 | 0,3470036 → 0,3507603 | 12 | 0xBFA9E7FC |
| Nitro, site 5 | +252 | sem evento | 0 | — |
| Speedbreaker, site 6 | +132, sub_8246C2F0 | 0,9983333 → 0,9792224 | 12 | 0xBFAAD1E4 |
| Speedbreaker, site 7 | +132 | sem evento novo | 0 | — |
| Speedbreaker, site 8 | +132 | 0,9983333 → 0,9792224 | 12 | 0xBFAAD1E4 |

- Nitro 1/2 ocorreu entre 14:53:07.907–08.088; queda gradual monotônica de cerca de 0,006667 por quadro.
- Speedbreaker 6/8 ocorreu entre 14:53:17.941–18.124; queda gradual monotônica de aproximadamente 0,0017 por quadro, não tão linear quanto Nitro.
- Nitro 3/4 ocorreu entre 14:53:24.172–24.355; recuperação/adição monotônica pequena, compatível com recarga.
- Os sites 1/2 e 3/4 apresentam valores iguais nos mesmos endereços e instantes de cada par; registrar isso como confirmação de fluxos com escrita/limitação, não como dois medidores separados.
- As duas sessões antigas tinham PRE247 sites 7/8 no mesmo endereço 0xBFA7CD34: site 7 valores acima de 1,0, site 8 limitando a 1,0. São ocorrências distintas do evento novo 6/8, com endereço 0xBFAAD1E4.
- Não há captura direta da tecla Nitro/Speedbreaker junto com os logs; sem telemetria de entrada correlacionada, a identificação semântica ainda é evidência circunstancial forte apoiada pelo mapeamento PPC, **não** experimento causal isolado.
- O próprio logger PRE247 limita 12 mensagens por site e por processo, de modo que não registrar site 5/7 na nova sessão não demonstra que nunca sejam executados.
- PRE246 (dinheiro) não apareceu no log; não avançar escrita do saldo sem validar objeto, proprietários, contexto e lógica de débitos.

## Conclusão técnica e restrições

**Avanço:** o teste captura dinâmica real de redução (candidatos Nitro sites 1/2 e Speedbreaker 6/8) e recuperação (Nitro sites 3/4). Priorizar futuro patch de instrumentação que isole o *último* store por caminho e capture contexto de jogador/objeto sem ler endereços guest arbitrários.

**Não habilitar cheat ainda:** substituir genericamente por 1,0 seria prematuro; o campo pode ter limites contextuais, a disponibilidade pode depender da carreira, e múltiplas escritas no mesmo frame podem sobrescrever uma intervenção. A política PRE309 está somente testada no host, desligada e não instalada no jogo.

**Estado preservado:** V40 PRE305 assinada e testada para oficina, V39 backup; pacote io.github.nfsmwrecomp, certificado permanente existente, save MARCEK, 1920×1080, gráficos/shaders/física/controles/termal, sem alterações nesta auditoria.

**Próximo gate:** confirmar mapa de fluxo Nitro sites 1–5 com fonte PRE99 autenticada (como PRE308 fez para Speedbreaker), decidir política de *single authoritative store* por caminho e compilar somente teste sintético de substituição com controles OFF por padrão. Depois, se aprovado, montar versão experimental incrementada com opt-in real e regressão de assinatura/rollback.
