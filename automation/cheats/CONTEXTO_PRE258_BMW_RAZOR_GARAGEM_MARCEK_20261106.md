# PRE258 — BMW M3 GTR inicial, Razor e garagem MARCEK: auditoria somente leitura

Data: 2026-11-06. Escopo do usuário: investigar manter BMW inicial e vencer Razor no prólogo, sem quebrar carreira. V37 e saves não foram modificados.

## Evidência do save Xbox 360 MC02 (exportado pelo próprio app)
- Save original: `nfsmw_partidas_2026-11-06_2052.zip`, 62.688 bytes MC02, validação dos três CRC32 EA e MD5 OK.
- Perfil **MARCEK**: saldo 3.000; carro ativo nº 81, assinatura nativa `a6ee7a11a6ee7a11`, mapeada à **Fiat Punto** no catálogo de carros do editor público `sprintstate/nfs-mw-save-editor`.
- Registros de propriedade: 119, **1 ocupado e 118 vazios**. Registros da garagem de carreira: 25, **1 ativo e 24 vazios**. Blocos de peças: 44, **1 ocupado e 43 marcadores vazios**.
- **Nenhuma BMW M3 GTR normal nem variante lenta/inicial** na tabela de carros possuídos do save MARCEK. Assinaturas PC do catálogo público, convertidas de u32 little para big endian nativo: BMW normal `4e4acc23b35f084e` (PC) e `slow/start` `4e4acc23f8e0da39`.
- A versão de ZIP com **8 Junkman por categoria** preserva dinheiro, registro de veículos e estado da garagem em comparação com o ZIP original, ambas conferidas com o mesmo auditor sem alterações. Isto não é uma reexportação pós-reinicialização; persistência das fichas em jogo foi confirmada verbalmente pelo usuário na PRE257B.

## Referência de código do prólogo (decompilação pública, versões não necessariamente iguais)
- `dbalatoni13/nfsmw/src/Speed/Indep/Src/Frontend/Database/FEDatabase.cpp`: `CareerSettings::StartNewCareer` seleciona `M3GTRCAREERSTART`, configurando uma corrida `GRaceDatabase::GetDDayStartRace()`.
- `CareerSettings::ResumeCareer` consulta `IsCareerRaceComplete(...GetDDayEndRace()...)` antes de retomar a sequência DDay, e seleciona novamente `M3GTRCAREERSTART` caso o prólogo ainda esteja incompleto.
- `GRaceDatabase.cpp`: sequência DDay `16.1.0`, `16.2.2`, `16.2.3`, `16.1.1`, `16.2.1`. `GetDDayStartRace()='16.1.0'`; `GetDDayEndRace()='16.2.1'`.
- **Limite:** fonte pública cobre múltiplas versões, inclusive protótipo PAL Xbox 360; não foi provada equivalência binária/endereços com a V37 USA/PAL. **Ainda não há função identificada de sabotagem do motor, derrota contra Razor, remoção persistente da BMW ou sequência de cutscenes** na V37.

## Duas metas distintas
1. **BMW disponível na garagem durante a carreira**, conservando o Punto e progressão: abordagem potencial via edição offline do save; há espaço estrutural, e o editor `sprintstate/nfs-mw-save-editor` inclui snapshot de **BMW de fim de carreira (normal)**. Não é a mesma variante de início `M3GTRCAREERSTART`. Nenhum ZIP BMW foi gerado nem importado. Antes de gerar, executar planner de alocação e solicitar confirmação explícita.
2. **Vencer a corrida de Razor e não perder a BMW na narrativa original**: exige alterar script/resultado e investigar gates DDay, sabotagem, cinematicas e transições de saves. Dar somente vitória pode causar progressão inconsistente; patch **não implementado nem comprovado**.

## Artefatos
- Relatório detalhado, sem bytes pessoais do save, no Drive: https://drive.google.com/file/d/1B_MR8qdPOc7XXpcH28E8LDEw_2gXXAQL/view
- Script local read-only executado sobre ZIP original e ZIP Junkman: `nfsmw_pre258_bmw_razor_save_audit_readonly.py`, MD5 e três CRCs aprovados, 118/24/43 disponíveis, 0 BMW nas tabelas.
- Nenhuma chave acessada, nova APK compilada ou progresso alterado. A última é V37, `io.github.nfsmwrecomp`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; preservar saves e outras versões.
- Próximo passo técnico: planner somente leitura de adição da BMW em cópia MC02, seguido de auditoria de fluxos DDay/race e teste de próximo save de perfil separado quando autorizado. Atualizar `CONTEXTO_NFSMW.md` canônico após backup, pois o do Drive ainda terminava em PRE237 no instante desta análise.
