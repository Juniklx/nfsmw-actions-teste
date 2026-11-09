# PRE575 — OBSERVAÇÃO EM DISPOSITIVO: PERFIL MARCEK INFORMADO COMO CORROMPIDO (2026-11-09)

**Fonte direta:** captura de tela fornecida pelo usuário neste chat, após aplicação manual PRE573 no Galaxy S24 FE, mensagem visível `MARCEK está corrompido.`. A captura é evidência visual, mas não acompanha log nativo nem prova de leitura do recurso `GLOBAL/ATTRIBUTES.BIN`.

## Observações verificáveis / comunicadas

- PRE573 no telefone foi relatada pelo usuário com `PRE573_FONTE=VERIFICADA`, `PRE573_ESTAGIANDO_COPIA_DE_401MB`, `PRE573_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`, e nomes de backups `ZDIR.BIN.pre573_original_backup`, `ZZDATA4.BIN.pre573_original_backup`. Esses são outputs fornecidos pelo usuário, não nova verificação remota dos bytes do aparelho.
- A captura mostra diálogo da interface do jogo: `MARCEK está corrompido.`; o jogo abriu ao menos até a interface de carregamento do perfil, mas **não houve conclusão demonstrada do carregamento da carreira**. Contador gráfico `60 fps 16.7 ms` na imagem é apenas uma leitura instantânea, não benchmark de desempenho.
- A captura **não comprova** que a alteração dos dados BMW é a causa da corrupção; também não comprova corrupção física/permanente do save. Hipóteses distintas: save já incompatível/corrompido, descompasso de dados após PRE573 ou erro de interpretação do perfil. É necessária comparação A/B.
- Consultado Google Drive após a captura: nenhum novo `nfsmw.log` do dispositivo localizado com `modifiedTime > 2026-11-09T04:17:36Z`. Último contexto canônico localizado: 876.816 bytes, SHA256 reportado pela PRE574 `86570cc299df4adaa84318dfd44f98a79edce6ac50193ed43e266874797dd762`.
- O usuário previamente informou aceitar criar novo save depois, sem exigir isolamento de `MARCEK`; isso **não exige** exclusão imediata do save nem justifica qualquer apagamento automático.

## Próximo teste diagnóstico sem inventar evidências

1. **Fechar completamente o jogo**. Se possível, recolher `nfsmw.log` da sessão com erro e salvar no Google Drive antes de novo teste. Não sobrescrever o log útil.
2. Executar deliberadamente o script de rollback PRE573 documentado em `automation/device/pre573_restore_bmw_ptbr_shevery.sh`, no mesmo **GAME_ROOT** usado na aplicação, preservando ambos os arquivos experimentais como `.pre573_test_previous`. O script recusa hashes inesperados. Não alterar saves pelo script.
3. Com os **arquivos originais PT-BR** restaurados, abrir a mesma APK V48 e tentar abrir a mesma carreira `MARCEK`. Se o aviso desaparecer, há uma associação com os recursos experimentais; ainda é necessária análise do VPAK / carregador para localizar causalidade. Se persistir, investigar o próprio save/versão e o caminho de carga.
4. Considerando que o usuário aceita recomeçar, uma carreira nova poderá ser testada depois dos controles de integridade, mas **isso não prova compatibilidade BMW**. Em nova tentativa PRE573, avaliar abertura da interface e menu de desempenho BMW sem confundir sucesso de boot com compra, física e persistência.
5. Não editar `GLOBAL/ATTRIBUTES.BIN`, APK, saves ou chave sem novo resultado; não gerar V49 agora.

**Estado:** primeira observação de falha de carregamento de perfil em dispositivo com dados experimentais PRE573 presentes; `BMW_tuning_enabled=false`, `guest_loader_acceptance_proven=false`, `profile_corruption_root_cause_proven=false`; backup de jogo relatado preservado, original do Drive intocado; relatório textual não lê o aparelho, não altera save nem APK.
