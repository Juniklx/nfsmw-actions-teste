# NFSMW Android — PRE259: BMW M3 GTR / prólogo Razor, ensaio seguro (2026-11-06)

## Resultado confirmado (sem importação)
- O usuário autorizou continuar a proposta: **simulação offline da adição da BMW ao perfil MARCEK, sem substituir Fiat Punto, e investigação separada da corrida inicial contra Razor**.
- Rodou localmente sobre as duas exportações já disponíveis: ZIP original `nfsmw_partidas_2026-11-06_2052.zip` e ZIP editado Junkman de 8 fichas por categoria. **Nenhum ZIP original, save, APK, key ou credencial alterado**.
- Modelo utilizado no ensaio: **BMW M3 GTR normal/fim de carreira**, template público `sprintstate/nfs-mw-save-editor/assets/unique_cars/blacklist/boss_car_snapshot_BMW_M3_GTR.json`; **não** corresponde à variante `M3GTRCAREERSTART` do prólogo.
- Candidato de nova entrada MC02 big-endian: car_number **82**, linha do registro 1 em `0x6235`; bloco de peças **32** em `0x9E6D`; garagem de carreira **1** em `0xE32D`; tudo verificado como disponível no save de referência. Preserva Fiat Punto `car_number=81`, `parts_slot=31`, `career_slot=0` e carro ativo 81.
- Em ambos os ensaios **apenas em memória**, o candidato passou MD5 + 3 CRCs EA, preservou saldo **3000**, marcadores Junkman nos 63 slots e os bytes dos registros do Punto, com todas as diferenças limitadas às regiões novas e checksums. 223 bytes diferentes em cada candidato temporário; nenhum arquivo candidato foi gerado ou testado no celular.
- Testes de falha fecharam caminho quando saldo/ativo mudaram, BMW já estava presente, checksum inválido, padding/layout inesperado ou modelo de referência diferente. Zips originais com mesmos SHA256 antes/depois.
- **Não confundir** checksums aprovados com BMW disponível no jogo: ainda não houve importação, boot, renderização, seleção, condução, progressão ou persistência da BMW neste ensaio. **Nenhum ZIP BMW foi entregue para importação.**

## Investigação do roteiro de Razor
- `dbalatoni13/nfsmw/src/Speed/Indep/Src/Frontend/Database/VehicleDB.cpp`: `FEPlayerCarDB::Default()` cria `M3GTRCAREERSTART` como preset `FE_CAR_FILTER_LIST_DEBUG`, não como carro de carreira persistente.
- `dbalatoni13/nfsmw/src/Speed/Indep/Src/Frontend/Database/FEDatabase.cpp`: `StartNewCareer`/`ResumeCareer` selecionam `M3GTRCAREERSTART`; progresso do prólogo DDay avalia `GetDDayEndRace()`.
- `GRaceDatabase.cpp`: sequência de eventos DDay `16.1.0, 16.2.2, 16.2.3, 16.1.1, 16.2.1`; `uiCareerMain.cpp` também testa conclusão de `16.2.1`.
- Essas fontes públicas são referência decompilada de várias edições e não dão endereços comprovados no binário V37; **não foi identificada** a rotina exata de sabotagem, derrota, transição de propriedade da BMW ou desfecho de Razor. Um `force-win` isolado não é justificadamente seguro. Patch Razor **não implementado**.

## Artefatos e próxima ação
- Relatório técnico PRE259 privado no Drive:
  https://drive.google.com/file/d/1ympFxK4IxCSz4LqTVkAV_JdlrcckPK6q/view
- Script autônomo `nfsmw_pre259_bmw_dryrun_mc02.py` e testes `nfsmw_pre259_bmw_dryrun_mc02_test.py` no workspace local; exigem fornecimento do snapshot JSON externo para a simulação plena, sem redistribuir asset comercial. JSON de plano sem bytes privados do save.
- Antes de gerar um novo ZIP experimental com BMW: **pedir exportação atual do save** feita no app após o sucesso persistente de Junkman, porque a exportação histórica é anterior às sessões posteriores. Não reutilizar o ZIP velho para importação e apagar progresso novo. Após receber, repetir checksums, disponibilidade de vagas e não duplicação, solicitar confirmação para importação. Manter backup, selecionar MARCEK e preservar outros perfis.
- Para alterar a corrida inicial Razor, trabalhar em perfil de teste separado e identificar controles de evento/cinemática via análise própria da recompilação usa/PAL. Não aplicar alterações a saves de carreira existentes.
- APK mais recente continua **V37**, pacote `io.github.nfsmwrecomp`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; nenhuma V38 compilada/assinada, nenhum ganho de FPS alegado. Preservar 1920×1080, cap 60 FPS, shaders, física, controle, limites térmicos.
- Contexto Drive `CONTEXTO_NFSMW.md` ainda histórico terminando em PRE237 na última leitura; para consolidar, fazer backup antes de apensar esta entrada PRE259 e os adendos PRE250-258.
