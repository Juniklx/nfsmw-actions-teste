# PRE372 — V44: correlação real XInput/Nitro em duas fases da sessão (2026-11-07)

## Fonte e escopo
- Arquivo **`nfsmw.log` recebido do usuário** nesta conversa; SHA-256 `533f6619bf133225a69c7976e74420f1819e4e6b3950d6f6dd3f6ad11ee2eba2`, 1.353.757 bytes, 5.640 linhas.
- O arquivo concatena **duas sessões**: inicialização V43 às 20:19:41.098; inicialização **V44 às 22:04:03.721**, encerrando registro em 22:06:38.702. Nunca somar logs históricos como sessão única.
- **Apenas V44:** 139 registros `NFSMW_PRE364_XINPUT_USER0`, 154 registros `NFSMW_PRE348_NITRO_SLOT_VALUES`, 58 `NFSMW_PRE336_NITRO_DIVERSITY`, 184 `NFSMW_PRE316_NITRO_CYCLE`, 72 `NFSMW_PRE247_CHEATS_DIAG`.
- PRE336: `distinct=4`, `overflow=false`; quatro slots com consumo e recarga (sites 1/2/3/4).
- O aplicativo V44 efetivamente executou marcador PRE364 no aparelho, comprovando instalação e utilização do runtime. Não comprova integridade de todas as funcionalidades, FPS ou cheats.

## Correlação temporal verificável
- 22:04:39.351: `NFSMW_PRE364_XINPUT_USER0 seq=23 buttons=0x2000 lt=0 rt=255`; 22:04:39.368: primeiro `NFSMW_PRE348_NITRO_SLOT_VALUES site=1 slot=1 samples=1` (0,99333), distância **17 ms**.
- 22:05:58.967: `NFSMW_PRE364_XINPUT_USER0 seq=123 buttons=0x2000 lt=0 rt=255`; 22:05:58.985: primeiro consumo `site=1 slot=2 samples=1` (0,99333), distância **18 ms**.
- Essas duas ativações independentes de `buttons=0x2000` coincidem com o **início de consumo** em dois slots diferentes. Outros 9 pulsos do mesmo botão não produzem *novos checkpoints amostrados em até 100ms*; PRE348 registra primeiro evento e potências de dois, não cada store. Não alegar correspondência completa nem identidade confirmada.
- Inferência forte: `0x2000` é candidato ao comando Nitro nesta configuração, e **slot1 num contexto, slot2 em contexto posterior** podem corresponder ao carro controlado. Não provado: mapeamento causal exclusivo, troca real de carro/contexto, player-owner semanticamente verificado, ou slots 3/4 pertencendo individualmente à IA.
- É **inseguro** fixar `slot=1` ou `slot=2` num cheat. Slot é índice da tabela PRE336, atribuído pela ordem de aparição.

## Checkpoints por slot: amostras não são valores finais
| Slot | Consumo (site 1): primeiro→último checkpoint | Recarga (site 3): primeiro→último checkpoint | Maior ordinal site 1/site 3 |
|---|---|---|---|
| 1 | 0,99333→0,92333 (mín. amostrado 0,14667) | 0,00056→0,77333 | 256 / 2048 |
| 2 | 0,99333→0,14667 | 0,00056→0,56889 | 128 / 1024 |
| 3 | 0,99667→0,80667 | 0,76722→0,76222 | 128 / 1024 |
| 4 | 0,99667→0,82000 | 0,75389→0,78445 | 128 / 512 |

- Recarga e consumo alternam ao longo do tempo. Um último checkpoint alto não invalida consumo anterior até zero.
- C3: 1 erro nesta sessão às 22:04:36.451 sobre thread de texturas, separado do Nitro; nenhuma ocorrência textual `FATAL EXCEPTION`/`SIGSEGV` nesta janela.
- A inicialização V44 registra `1920x1080` e cap `60 FPS`, não meta 120; nenhuma melhora de FPS comprovada.

## Conclusão e próximo gate
- **Progresso verificado:** V44 executa PRE364, entradas humanas monitoradas no estado XInput nativo, e duas transições `0x2000` antecederam por aproximadamente um frame o começo do consumo de Nitro em slots diferentes.
- **A identificação de player owner permanece NÃO COMPROVADA.** Para cheat exclusivo do jogador, extrair e verificar ponteiro/ID estrutural do veículo controlado, ou um vínculo independente e testado entre input, contexto do objeto e as stores Nitro.
- Proposta de teste **sem nova APK**: o usuário confirma se entrou em exploração livre primeiro e depois corrida por volta das 22:05:40–22:06:00; o log sozinho não comprova esse modo. O trecho permite uma hipótese contextual, não semântica. Não é preciso repetir um teste Nitro até zero. Depois disso, avaliar instrumentação de vínculo com veículo, nunca aplicar mutação global em `sub_82424AF0`.
- Preservar V43/V44, save `MARCEK`, mesmo certificado permanente, shaders, 1920×1080 e proteções térmicas.
