# NFSMW — Adendo PRE286 / PRE287 — 2026-11-07

## Escopo corrigido pelo usuário
- Peças Junkman: usuário informa resolvidas. Não reabrir este trabalho.
- Descartados os antigos objetivos de manter a BMW inicial e de vencer Razor mantendo-a.
- Problema ativo único: BMW M3 GTR já inserida no save MARCEK e dirigível, mas oficina só exibe Visual; Peças e Desempenho não aparecem.
- Preservar save MARCEK, controles touch/PG-9076, 1920x1080, limite atual de 60 FPS, recursos gráficos e térmicos.

## PRE286 verificada no GitHub Actions
- Run: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42332473337
- Job completed/success e logs internos:
  - PRE286_STATUS AUDIT_OK
  - PRE286_CONFIG True
  - PRE286_TARGET nfsmw
  - PRE286_LIBMAIN_LINKED True
  - PRE286_CALLBACK_DEFINITIONS 1
  - PRE286_APK_BUILT False
- Esta prova é de configure/link ARM64 da libmain.so PAL em workspace descartável, com callback PRE283 passivo registrado e default OFF. NÃO comprova correção de menu ou execução no Galaxy S24 FE.

## PRE287 preparada e disparada
- Script: automation/kaggle/pre287_bmw_pal_native_diagnostic_gate.py
- Workflow: .github/workflows/nfsmw-pre287-bmw-pal-native-diagnostic-gate.yml
- Trigger: automation/kaggle/pre287_requests/launch_20261107.json
- Run inicial: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42335391592
- Testa novamente restore PRE99 autenticado, replay V37, link da libmain PAL e condições fail-closed: callback único, flag default OFF, CMake registrado uma vez, fonte reversível, no APK/signing/save. Não gera APK nem ativa o diagnóstico.
- Resultado: PENDENTE de conclusão e leitura do log (status queued no momento do registro).

## Próxima decisão
1. Conferir log/artifact PRE287, não somente status verde.
2. Se AUDIT_OK, planejar APK diagnóstica incremental com chave permanente original; NÃO gerar/sinalizar release sem validar assinatura e versionCode.
3. Testar em aparelho por observação de categorias da oficina e logs, sem editar novamente o save.
4. Somente depois avaliar alterações reversíveis para habilitar as categorias, sem inventar níveis/peças.

## Integridade
- Identificador do aplicativo: io.github.nfsmwrecomp
- Última APK diagnóstica reconhecida neste fluxo: V37; não confundir com nova V38.
- Certificado permanente SHA-256: 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b.
- Nenhuma senha/chave foi acessada na PRE287.
- Adendo no repositório GitHub. O arquivo bruto CONTEXTO_NFSMW.md no Drive não foi substituído por este commit.


## Atualização — PRE287 aprovada e PRE288 iniciada (2026-11-07)
- PRE287 run 42335391592: completed/success; log PRE287_STATUS AUDIT_OK; 13/13 verificações true, incluindo link real PAL ARM64, callback uma vez, default OFF, reversibilidade e ausência de APK, assinatura e acesso ao save.
- PRE288 adicionada em `automation/kaggle/pre288_bmw_feature_on_pal_native_preflight.py`, workflow `.github/workflows/nfsmw-pre288-bmw-pal-feature-on-native.yml`, trigger `automation/kaggle/pre288_requests/launch_20261107.json`.
- Run PRE288: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42352633132 (queued na última consulta). Ainda não há resultado.
- PRE288 recompila o motor PAL com `-DNFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE=1` exclusivamente em workspace descartável. Verifica a presença da definição no compile_commands.json do shard `nfsmw_recomp.11.cpp` e exige libmain ARM64 vinculada com callback único. Não compila APK, não assina, não modifica save e não habilita patches de menu.
- Objetivo ativo: BMW M3 GTR já presente no MARCEK, oficina mostra apenas Visual; Peças e Desempenho ausentes. Junkman informado como resolvido; descartar metas anteriores sobre manter BMW inicial/vencer Razor.
- Se PRE288 passar, próxima etapa deve ser uma APK diagnóstica versionCode superior ao da V37, com certificado permanente original, mediante validação de assinatura e teste no Galaxy S24 FE. Nenhuma V38 produzida nesta atualização.


## Atualização PRE288 aprovada / PRE289 iniciada — 2026-11-07
- PRE288 GitHub Actions run 42352633132 completed/success, log interno PRE288_STATUS AUDIT_OK; CMake True; target nfsmw; libmain linked True; callback definitions 1; APK built False.
- PRE289 é nova tentativa de APK diagnóstica V38 a partir da cadeia de build/assinatura usada pela V37. Script automation/kaggle/pre289_build_signed_v38_bmw_passive.py, workflow .github/workflows/nfsmw-pre289-v38-bmw-passive-signed.yml.
- Run PRE289 https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42354940551: queued na última consulta. Não declarar APK compilada/assinada/publicada antes do relatório de verificação, leitura de assinatura e readback no Drive.
- versionCode 38 e pacote io.github.nfsmwrecomp. Manter certificado original SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b; não recriar chave nem expor segredos.
- Objetivo único: sonda passiva de vtable da BMW M3 GTR na oficina (Peças/Desempenho ausentes; Visual presente). Feature habilitada somente para diagnóstico na recompilação PAL. Patches PRE264/PRE281 de alteração no menu não habilitados.
- O script exige marcador BMW na libmain.so do APK assinada, além dos checks da V37 para shaders, dependências, pacote, versão e certificado. Instalação e efeito no aparelho NÃO comprovados. MARCEK não deve ser modificado pelo build.
- Próxima ação: consultar log da run 42354940551 e respectivo relatório/artefato. Se falhar, corrigir apenas o erro demonstrado; se passar, conferir artefato e orientar teste da oficina sem inferir sucesso do menu.


## Atualização PRE289 falha de upload / PRE289B recovery — 2026-11-07
- PRE289 run 42354940551 completed/failure; log interno: `PRE170 stopped at UPLOAD_NEW_APK_TO_PRIVATE_DRIVE ResumableUploadError`, subfase `APK_ALL_GATES_PASSED`; `APK verified: True`, `Drive upload: False`. Erro NÃO foi de compilação/assinatura, e V38 instalável NÃO foi publicada no Drive.
- Artifact GitHub 13567394025 preserva APK `nfsmw-v38-bmw-passive-verified.apk` e relatório `pre289-v38-report.json`; zip ~45,7 MB.
- Consulta à pasta de APK no Drive não encontrou V38/PRE289.
- PRE289B prepara recuperação de upload apenas, sem recompilar ou assinar, reaproveitando artifact da run 42354940551. O script valida hash SHA256 e tamanho contra relatório PRE289, marcador BMW, hash libmain PAL, assinatura v2 com certificado permanente, pacote e versionCode 38, faz lookup idempotente por nome+MD5 no Drive e só então tenta upload; não toca no save.
- Workflow `.github/workflows/nfsmw-pre289b-v38-upload-only.yml`; script `automation/kaggle/pre289b_upload_verified_v38_only.py`.
- Run PRE289B 42367222713: queued na última consulta. Só declarar upload/publicação após `PRE289B_STATUS AUDIT_OK` e readback do Drive. Falha do Drive anterior pode ocorrer novamente; não alterar assinatura.


## PRE289B falha verificada e correção pontual — 2026-11-07
- Run 42367222713, completed/failure: artifact PRE289 V38 recuperado com sucesso; log `PRE289B_APK_VERIFIED True`, `PRE289B_ERROR_TYPE TypeError`, `PRE289B_DRIVE_FILE_ID None`; portanto nenhuma publicação ao Drive comprovada.
- Inspeção estática do script de recuperação encontrou parâmetro inválido `page_size=100` em `googleapiclient.files().list`; corrigido para `pageSize=100` no commit `2c90c0189da309ea09381abf7ab2f5c492088e49`. É a causa técnica identificada, mas o traceback original não foi capturado integralmente.
- Novo disparo sem rebuild/reassinatura: PRE289B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42368174035 (queued na última consulta). Reusa exatamente a APK assinada da PRE289.
- Próximo passo: examinar `PRE289B_STATUS`, MD5 e ID confirmado por readback na pasta Drive; não declarar sucesso até a aprovação.


## PRE289B segunda falha — Google Drive HTTP 403 (2026-11-07)
- Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42368174035: completed/failure.
- Log interno: PRE289B_APK_VERIFIED True; PRE289B_ERROR_TYPE ResumableUploadError; PRE289B_HTTP_STATUS 403; PRE289B_DRIVE_FILE_ID None.
- A correção do argumento pageSize resolveu o TypeError, mas o Drive recusou a criação do arquivo. O log sanitizado não contém o reason do 403; não afirmar ser quota/permissão específica sem confirmar.
- Metadados consultados pela conexão Drive: pasta 02_APKs ID 1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh existe no My Drive e consta permissão owner. Essa conexão não necessariamente utiliza o mesmo OAuth do GitHub Actions.
- Não disparar upload idêntico sem diagnosticar razão 403 e a identidade/scopes da credencial do workflow (nunca imprimir tokens ou credenciais).
- APK V38 e relatório continuam disponíveis no artifact GitHub da run 42354940551 (artifact 13567394025); sem recompilação ou reassinatura; instalação e correção da tunagem não testadas.


## PRE289C — diagnóstico SOMENTE LEITURA do Google Drive 403 (2026-11-07)
- Run GitHub Actions 42369148031; job completed/success. Sem tentativas de upload e sem acesso à APK nem às credenciais de assinatura.
- Resultados logados: `PRE289C_STATUS APP_ACCESS_NOT_AUTHORIZED`; pasta `02_APKs` encontrada; `can_add_children=true`; `can_list_children=true`; `is_app_authorized=false`; `is_shared_drive=false`. Quota lida: `enough_for_v38=true`, `quota_at_or_above_limit=false`.
- **Interpretação com ressalva:** a identidade autenticada pelo workflow consegue localizar a pasta e tem capacidade de adicionar filhos, mas o app OAuth usado pelo GitHub NÃO está autorizado para essa pasta segundo `isAppAuthorized`. Isso é compatível com restrição `drive.file` de acesso por arquivo/app e com HTTP 403 de upload, mas a resposta original do erro não capturou o campo `reason`, portanto a causa exata da API ainda precisa de confirmação.
- **Correção segura recomendada:** conceder à MESMA aplicação OAuth do workflow autorização à pasta pelo Google Picker (quando a app suporta) ou reautorizar o cliente OAuth com o escopo adequado, usando consentimento explícito; comparar o token efetivo com os escopos aceitos, sem expor, apagar ou recriar segredos nos logs. `drive.file` tem acesso por arquivo/app; `drive` é escopo restrito e só deve ser considerado se necessário.
- Não repetir upload enquanto `is_app_authorized=false`. Continuar usando artifact Github 13567394025 para V38; nenhum efeito no jogo ou correção de tuning foi comprovado.


## PRE289D — Escopos OAuth efetivos CONFIRMADOS (2026-11-07)
- Usuário ativou escopo Drive no Google Auth Platform, mas não reautorizou o token GitHub. App Web, externo e em teste, e usuário de teste coincide com a conta proprietária da pasta.
- Run GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42372037871: completed/success; log `PRE289D_STATUS NO_FULL_DRIVE_SCOPE_IN_CURRENT_TOKEN`, `PRE289D_SCOPE_SOURCE google_tokeninfo`, `drive_full=false`, `drive_file=false`, `drive_readonly=true`; `PRE289D_UPLOAD_ATTEMPTED False`.
- **Causa operacional agora demonstrada:** o token OAuth vigente usado em GitHub Secrets tem SOMENTE escopo de leitura `https://www.googleapis.com/auth/drive.readonly`; não autoriza criar APK no Drive. O 403 das PRE289/PRE289B é consistente com isso, ainda que `reason` original não esteja capturado.
- Solução: refazer consentimento OAuth no MESMO cliente Web e conta testadora, solicitando pelo menos escopo de escrita autorizado adequado à pasta (escopo drive completo, caso necessário, sujeito às restrições do Google). Obter NOVO refresh token e atualizar exclusivamente o Secret `GOOGLE_REFRESH_TOKEN` de modo seguro pelo usuário; não compartilhar com chat, não trocar client_id/secret ou chave de assinatura. Avaliar migrar para `drive.file` + seleção via Google Picker para menor privilégio quando possível.
- IMPORTANTE: Modo Testando + escopos de Drive pode limitar duração do refresh token; não colocar app em produção nem alterar escopos sem considerar requisitos OAuth. Repetir PRE289D até flag correta antes de PRE289B upload-only; preservar artefato V38 13567394025.


## Atualização — OAuth atualizado pelo usuário; erro unauthorized_client (2026-11-07)
- Usuário relata ter atualizado autorização/Secret do token após ativar escopo `drive` no Console; cliente tipo Web, app externo em Testando, a mesma conta do Drive cadastrada como usuário de teste.
- PRE289D run 42372774798: workflow success mas auditoria INTERNA `OAUTH_REFRESH_OR_CLIENT_FAILED`, sem tokeninfo e sem upload.
- PRE289D run 42372864087: também `OAUTH_REFRESH_OR_CLIENT_FAILED`; diagnóstico sanitizado: `RefreshError`, código `unauthorized_client` (confirmado), sem status HTTP explícito. `PRE289D_UPLOAD_ATTEMPTED False`.
- Antes da troca do token, PRE289D run 42372037871 conseguia autenticar e provou token antigo somente `drive.readonly`.
- Interpretação: a nova combinação client_id/client_secret/refresh_token ou configuração de fluxo OAuth não está aceita no endpoint de refresh. Não afirmar ainda qual componente é inválido; confirmar que novo refresh token veio do EXATO cliente Web existente do GitHub, `Use your own OAuth credentials` ligado no Playground, redirect URI autorizada, access_type offline, escopo drive, e que foi copiado o refresh token (não authorization code nem access token). Não expor credenciais. Só atualizar `GOOGLE_REFRESH_TOKEN` após confirmação; não recriar cliente/chave.
- Não disparar upload PRE289B enquanto PRE289D não confirmar `drive_full=true`. APK V38 original preservada no artifact 13567394025.


## PRE289D OAuth corrigido e PRE289B V38 publicada — 2026-11-07
- Usuário informou nova tentativa de autorização OAuth. PRE289D run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42373143816: `FULL_DRIVE_SCOPE_PRESENT`, tokeninfo verificou `drive_full=true`; nenhuma tentativa de upload nesta auditoria.
- PRE289B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42373209767: completed/success; log `PRE289B_STATUS AUDIT_OK`, `PRE289B_APK_VERIFIED True`, `PRE289B_DRIVE_FILE_ID 1V0AnQnsUpDOwRo2b208uRkg3yFWXwy0W`, `PRE289B_ERROR_TYPE None`.
- Arquivo validado pelo processo de recuperação: `NFSMW_V38_PRE289_BMW_PASSIVE_VTABLE_DIAGNOSTIC.apk`, 47.102.221 bytes, pacote `io.github.nfsmwrecomp`, versionCode 38; assinatura permanente revalidada no PRE289B e SHA/MD5 comparados com relatório original e readback do Drive.
- Consulta independente via conector Drive: ID `1V0AnQnsUpDOwRo2b208uRkg3yFWXwy0W`, pasta `02_APKs` ID `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`, tamanho 47.102.221, MIME APK. Link: https://drive.google.com/file/d/1V0AnQnsUpDOwRo2b208uRkg3yFWXwy0W/view .
- Nenhuma recompilação/reassinatura/alteração do save MARCEK na recuperação. V38 ainda NÃO instalada/testada no Galaxy S24 FE; o diagnóstico da BMW não demonstra correção das categorias Peças e Desempenho.
- Próximo passo: guardar backup do save, instalar V38 por cima sem desinstalar para preservar dados (se Android aceitar a assinatura e a versão); selecionar a edição PAL/PT-BR, abrir oficina com a BMW M3 GTR e obter `nfsmw.log` com marcador `NFSMW_PRE283_BMW_VTABLE`. Se o marcador não aparecer, auditar caminho da interface e edição ativa antes de novos patches.


## PRE290 — PT-BR versus PAL e alcance do trace BMW V38 (2026-11-07)
- Usuário confirmou que na V38 abriu oficina BMW M3 GTR, viu apenas `Visual` e entrou nessa categoria; `Peças` e `Desempenho` não estavam listadas. Logs recentes não registraram `NFSMW_PRE283_BMW_VTABLE` e não identificam diretamente o versionCode/distribuição da biblioteca.
- Drive DIAG41 PRE15 log (https://drive.google.com/file/d/1RS8SravbzjvC1Kp2j9hAAxQ75hWegF-F/view): `default.xex` PAL SHA256 `aad15fc218d034de3131f746e0b763dd8049a40dd676efc87667fcaf4fc72694` / 3.940.352 bytes; PTBR SHA256 `684ceef963806ae7ba2f6d0936c267f9ff0134d20da1f85a390862dd9c676c28` / 3.938.304 bytes; imagens PE ambas 13.434.880 bytes, código diferente.
- Drive DIAG41 PRE16 log (https://drive.google.com/file/d/1_ix_UsPFGR5XpoG00sLURytXb8d2Ivn3/view): comparação descomprimida apresenta APENAS **10 bytes diferentes no PE inteiro**, em função `0x822C62E0`: PAL lê byte em `0x82A2CE06`, PTBR substitui por `li r3,1; blr; nop`. Não é prova de relocalização de código entre as edições.
- DIAG41 PRE18 identifica fonte PAL `nativo/app/generated/default/nfsmw_recomp.74.cpp` `sub_822C62E0`; PRE19-V2 registra patch correspondente aplicado na árvore histórica DIAG41, mas não demonstra origem exata do binário V38. Não inferir efeito sobre construção de menu sem callgraph.
- PRE191/192/193 documentação confirmou roteamento configurado `ptbr` e `pal_es` para `libmain.so`, USA `libmain_usa.so`, com ressalva de não existir leitura direta de bibliotecas mapeadas no processo específico.
- PRE290 GitHub workflow run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42375553849 `completed/success`; log `PRE290_STATUS AUDIT_OK`, 10 verificações de fontes; não baixou XEX, não criou APK.
- Distinção crítica nas receitas auditadas: PRE264 `sub_82578988` é CANDIDATO à montagem do menu principal (flag de patch `NFSMW_PRE264_BMW_MENU_ENABLE`, mock/dryrun; não está provado ser endereço final de `BuildOptionsList`). V38 PRE283 `sub_82582F70` instrumenta call virtual em fluxo de `CustomizePerformance::Setup`, isto é, CAMINHO DIFERENTE do menu principal. Como `Desempenho` nem aparece e usuário entrou apenas em `Visual`, ausência do marcador V38 é compatível com o fluxo não ter alcançado Setup; **não é prova de endereços PTBR diferentes ou de biblioteca errada**.
- Conclusão: manter V38 e save inalterados; próxima etapa verificar identidade do callsite de criação de opções do menu e versionCode/biblioteca efetiva em runtime, usando trace limitado e somente diagnóstico antes de qualquer mudança de comportamento. Não tratar `Peças`/`Desempenho` visíveis como garantia de listas de upgrades disponíveis. Nenhum ganho FPS ou desbloqueio comprovado.


## PRE291 — auditoria autenticada do ponto de trace do menu BMW (2026-11-07)
- Run: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42375930691, workflow completed/success, `PRE291_STATUS AUDIT_OK`; `PRE291_DEFAULT_OFF True`, `PRE291_SOURCE_ONLY True`, `PRE291_APK_BUILT False`.
- Fonte PAL gerada foi lida no snapshot PRE99 autenticado do Drive, verificada com SHA-256 fixo `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`, arquivo `workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp`.
- Candidato principal: `sub_82578988` contém sequência verificada de chamada do tipo de carro e comparação com modelo 41, mais cinco chamadas estruturais `__imp__sub_82575370(ctx, base)` de adição de opções. Ponto passivo colocado EM MEMÓRIA depois de `cr6.compare<int32_t>(ctx.r3.s32,41,xer)`; flag `NFSMW_PRE291_BMW_MAIN_MENU_TRACE_ENABLE` desligada por padrão, callback `NFSMW_PRE291_BMW_MAIN_MENU_TRACE(model_type, fixed_callsite)` sem leituras/escritas adicionais em memória guest.
- Verificou inserção única de protótipo/callback, SHA do original, reversibilidade exata por remoção e preservação de chamadas originais. Nenhum código salvo à árvore, APK compilada ou assinatura/chave/save acessados.
- INTERPRETAÇÃO: a V38 investigou `sub_82582F70` (caminho Setup desempenho) e não o `sub_82578988` (candidato à montagem do menu principal). A ausência de `NFSMW_PRE283_BMW_VTABLE` quando jogador abre Visual é compatível com esse caminho não executado; não prova divergência de endereços PTBR/PAL.
- **Não aprovado para release**: PRE291 é somente ensaio do ponto de inserção, não logger nativo linkado nem prova runtime, e não identifica pacotes de upgrade existentes. Próximo passo candidato: preflight de logger nativo habilitado e, se validado, nova build diagnóstica de versionCode >38 com mesma assinatura permanente, sem alteração de condição de menu, capturando logs limitados somente durante reprodução no S24 FE. Evitar PRE264 desbloqueio direto enquanto listas de peças/desempenho não estiverem validadas.


## PRE292 — Preparação de instrumentação passiva da função do menu BMW (2026-11-07)
- Fontes versionadas: `automation/kaggle/pre292_bmw_main_menu_native_link_nosign.py`, workflow `.github/workflows/nfsmw-pre292-bmw-menu-native-link.yml`.
- Reaproveita PRE288 como preflight de link ARM64 real; recompõe PRE99→patches V37 e logger PRE283 em diretório descartável, introduz callback nativo `NFSMW_PRE291_BMW_MAIN_MENU_TRACE` com limite 16 logs e flag apenas no compilador do shard `nfsmw_recomp.5.cpp` (`NFSMW_PRE291_BMW_MAIN_MENU_TRACE_ENABLE=1`). O callback somente observa tipo/modelo do carro em `sub_82578988`. Nenhum desbloqueio da BMW, guest memory write, save, Gradle APK ou signer.
- Duas falhas **de infraestrutura do script, não do jogo**: run 42376367276 `FileNotFoundError` porque foi passado diretório `automation/kaggle` ao replay em vez do root do repo; run 42376558775 repetiu o erro; run 42376726666 `ValueError` em `STAGE_PRE292_MENU_SOURCE` devido ao escape incorreto em regex de inserção; foi corrigido regex/CMake newline no commit `2590529d37753733593a0da559607871df79b954`. Todas sem APK e sem assinatura.
- Novo run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42376933757 lançado com correções. **Última consulta durante esta atualização: in_progress, passo `Compile and link original PAL ARM64 target in disposable workspace`**. NÃO declarar `AUDIT_OK` até obter log conclusivo `PRE292_STATUS AUDIT_OK`, `PRE292_GUEST_FLAG True`, `PRE292_CALLBACK_DEFINITIONS 1`, `PRE292_LIBMAIN_LINKED True`; se falhar, investigar o `failed_safe_stage`/relatório antes de patch adicional.
- Até essa evidência: V38 segue última APK publicada, menu Peças/Desempenho ainda ausente, versão instalada efetiva e chamada do menu em PTBR não comprovadas de modo independente.


## PRE292 aprovada e PRE293/V39 iniciada — 2026-11-07
- PRE292 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42376933757 final **completed/success**, log `PRE292_STATUS AUDIT_OK`, `PRE292_CONFIG True`, `PRE292_TARGET nfsmw`, `PRE292_LIBMAIN_LINKED True`, `PRE292_CALLBACK_DEFINITIONS 1`, `PRE292_GUEST_FLAG True`, `PRE292_APK_BUILT False`. A compilação ARM64 efetiva do `libmain.so` em cópia isolada comprovou vinculação do callback do menu `NFSMW_PRE291_BMW_MAIN_MENU_TRACE` uma vez. Não comprova chamada em execução no Galaxy S24 FE.
- PRE293 `automation/kaggle/pre293_build_signed_v39_bmw_menu_trace.py` derivada do builder validado PRE289/V38: preserva patches e verificações anteriores, invoca `stage_trace` da PRE292, liga flags de traço de menu e Setup em seus respectivos shards PAL, verifica ambos marcadores nativos `NFSMW_PRE292_BMW_MENU` e `NFSMW_PRE283_BMW_VTABLE` na `libmain.so` de APK produzida, impõe `versionCode=39`, `io.github.nfsmwrecomp`, certificado permanente esperado (SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`). Sem mudar condição de ocultação da categoria BMW e sem mexer em saves.
- Workflow `.github/workflows/nfsmw-pre293-v39-bmw-main-menu-signed.yml`; execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42378263558 **em andamento na última verificação** no passo de build/signed audit, não afirmar APK pronta/assinada/Drive antes do resultado.
- Próximos gates: status interno `PRE293_V39_BMW_MENU_DIAGNOSTIC_SIGNED_VERIFIED_ARTIFACT`, certificado permanente por apksigner/v2, `versionCode 39`, ambas strings em PAL `libmain.so`, SHA/MD5 readback do Drive e pasta `02_APKs`. Só após isso pedir teste Android da oficina BMW/MARCEK e log `NFSMW_PRE292_BMW_MENU`; não afirmar desbloqueio ou FPS.


## V39 PRE293 publicada e PRE294 auditoria do cache — 2026-11-07
- PRE293 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42378263558 concluiu `success`. Log interno `PRE293_V39_BMW_MENU_DIAGNOSTIC_SIGNED_VERIFIED_ARTIFACT`, `APK verified: True`, `Drive upload: True`. Confirmado no Drive em `02_APKs`: ID `10Hefzqcq1ejeCpxRcyH9cQ4f_qeZevC6`, `NFSMW_V39_PRE293_BMW_MAIN_MENU_PASSIVE_TRACE.apk`, 47.102.277 bytes, https://drive.google.com/file/d/10Hefzqcq1ejeCpxRcyH9cQ4f_qeZevC6/view . versionCode=39, pacote/certificado permanente aferidos pelo builder. Usuário instalará e enviará `nfsmw.log` para observar `NFSMW_PRE292_BMW_MENU`; não afirmar instalação/teste ainda.
- PRE294 feita como inspeção de logs, launcher e políticas, sem novo workflow/build. Relatório: `docs/PRE294_CACHE_AUDITORIA_V38_V39_20261107.md`. A V38 e V39 tiveram cache hit Gradle 386 MB e PRE140 ccache SDK-only ~7 MB. Etapas principais ~26 e ~24 min, não apenas tempo de compilador.
- `pre140_sdk_only_ccache_launcher.sh` exclui de propósito `nativo/app` e `app_usa`; sem reuso de objetos C++ recompilados do motor. Na V39, cache PRE140 restaurou 379 arquivos/7.659.924 bytes e terminou com 469 arquivos/15.267.774 bytes, mas o salvamento foi SKIPPED por hit exato de chave imutável: novos objetos desse cache não persistiram.
- Próxima etapa técnica opcional PRE295: pré-auditoria/medições de ganhos em cache SDK e plano estrito para cache separado do motor nativo com isolamento dos dados sensíveis, chaves por fonte/flags/NDK/headers, validação cold vs warm, sem modificar V39 ou saves; não estimar ganho nem aplicar alterações cegas. O usuário testará V39 enquanto auditoria cache prossegue.


## PRE295–PRE297: canário cache SDK e PRE296 objetos sintéticos (2026-11-07)
- Relatório técnico `docs/PRE295_PRE297_CACHE_ROLANTE_E_TESTE_SINTETICO_20261107.md`.
- Novo workflow `.github/workflows/nfsmw-pre295-297-cache-canary.yml` restaura cache SDK com fallback PRE140 e salva nova chave única `nfsmw-sdk-rolling-v2-Linux-<runId>`; só canário, **não altera o build V39 ou próximas releases**.
- PRE295 canário run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382269949 `success`, `PRE297_STATUS AUDIT_OK`, 1 hit de ccache sintético, objeto SHA igual, nova chave SDK salva.
- PRE296 scripts experimentais `automation/kaggle/pre296_game_objects_cache_launcher.sh` e `pre296_game_objects_cache_policy.py`. Isolam `RUNNER_TEMP/nfsmw-game-objects`, opt-in `NFSMW_CACHE_GAME_OPT_IN=1`, desligado por padrão, não publicam objetos reais do jogo. Não são aprovados para produção.
- PRE297 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382484905 `success`, prova de uso do launcher PRE296 com fonte sintética e comparação cold/warm: `PRE297_SYNTHETIC_OBJECT_HASH_EQUAL True`, `PRE297_SYNTHETIC_CCACHE_HITS 1`, política sintética validada; `REAL_GAME_CACHE_VALIDATED False`.
- PRE295B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382664244 `success`: **readback exato** da chave rotativa `nfsmw-sdk-rolling-v2-Linux-42382484905` com `Cache hit`, verificação PRE140 dos arquivos e `PRE295B_EXACT_ROLLING_CACHE_READBACK_OK`. Isso comprova que cache foi efetivamente persistido e pode ser restaurado.
- Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382717266 `success`, mas **restauração por prefixo voltou a selecionar chave legado PRE140**, apesar de haver chave rotativa exata disponível; nenhuma alegação de que a seleção automática da chave mais recente está resolvida. Foi salva nova chave rotativa `nfsmw-sdk-rolling-v2-Linux-42382717266`.
- PRE295 inicial teve ensaios falhos por problemas de teste ccache/stat parser e ordem sintética da flag `-c`; corrigidos. Passagens conclusivas citadas acima.
- Necessidade antes de aplicar cache real do jogo: testar cold/warm em `libmain.so` real, hash de DSO, métricas e política de dados no repositório privado, sem persistir game objects entre jobs até gates validarem. Não prometer redução de minutos nem ganho de FPS.


## PRE295C validada e PRE298 real ARM64 iniciada — 2026-11-07
- PRE295C [run 42382849112](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42382849112) **completed/success**; restauro da chave rotativa existente `nfsmw-sdk-rolling-v2-Linux-42382717266`, relatório PRE140 `POLICY_PASS`, teste sintético `PRE297_STATUS AUDIT_OK`, 1 hit de ccache, salvou nova `nfsmw-sdk-rolling-v2-Linux-42382849112`. Para resolver seleção de prefixo, usou explicitamente a chave rotativa validada como primeira alternativa e chave antiga como fallback. Isto ainda é canário, não release.
- PRE298 criou script `automation/kaggle/pre298_real_pal_cold_warm_nocachepersist.py` e workflow `.github/workflows/nfsmw-pre298-real-pal-cache-audit.yml`. Restore PRE99 autenticado e build CMake PAL ARM64 real **duas vezes** com a mesma instrumentação PRE292, em árvores descartáveis; `ccache` exclusivo `RUNNER_TEMP/nfsmw-game-objects` comum às duas execuções, sem Actions cache/save de objeto do jogo, sem Gradle release, assinatura, APK, save ou publicação de `libmain.so`.
- PRE298 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42383054863 foi acionado e está **em andamento** na última consulta, preparando SDK NDK/CMake. Não afirmar compilação dupla, equivalência de SHA, hit real, ganho de tempo ou status `AUDIT_OK` até examinar resultado e relatório.
- Aprovação para uso do cache de **objetos do jogo** em releases continua proibida até PRE298 comprovar identidade do `libmain.so`, hits e proteção dos objetos, e a política de armazenamento privado ser revisada. A V39 do Drive e o save MARCEK seguem preservados.


## PRE298 FINAL — Cache do motor NÃO APROVADO — 2026-11-07
- GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42383054863 completed/success; PRE298 script AUDIT_OK **apenas para compilações nativas bem-sucedidas**. Metadados extraídos com PRE298B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42387021709 e documentados em `docs/PRE298_RESULTADO_REAL_PAL_CACHE_SEM_HITS_20261107.md`.
- Compilação real PAL #1: 1330.06 s; 49 chamadas cacheáveis, 0 hits, 49 misses; `libmain.so` 116758848 bytes, SHA-256 `74068d1a512c34b134a16838faf5f6ef12f36cd7182f29ea29ab8efd961a81fc`.
- Compilação real PAL #2: 1378.91 s; total 98 chamadas cacheáveis, 0 hits, 98 misses; `libmain.so` 116758816 bytes, SHA-256 `4357e9ddd42d9c97d26ffebde39fa2d50228f15af397b48b758f810eb2331299`.
- Segunda passagem 48.85 s mais lenta; bibliotecas diferem em 32 bytes e hashes; sem aceleração e sem igualdade binária. **Não ativar cache de objetos do jogo em releases ou persistir no GitHub.** Nenhuma APK, signer, save ou fonte de jogo alterada.
- Próxima etapa PRE301: investigar diferença de caminhos temporários/flags/headers/cache stats e seções ELF, somente em fontes isoladas, e exigir hits >0, equivalência e economia medidos antes de habilitar cache real. O cache rotativo SDK PRE295C segue validado apenas em canário.


## TESTE V39 NO GALAXY S24 FE — LOG ENTREGUE — 2026-11-07
- Usuário enviou arquivo `nfsmw.log` da sessão de 2026-11-07 11:27:41 até 11:29:07 (horário registrado no log); 1486 linhas, 335153 bytes, SHA-256 `2543f00a48b7e86bbcfb3d6234c922550a5f5b90b82cb09f21addd8c3219a1a7`. O log não inclui comprovante independente de `versionCode 39`, mas contém marcador exclusivo do diagnóstico PRE292 presente na V39.
- **CONFIRMADO EM RUNTIME:** 2026-11-07 11:29:00.056, thread t10006: `[NFSMW_PRE292_BMW_MENU] callsite=0x82578988 type=41 event=1`. Instrumentação funcionou; tipo de modelo 41 no ponto imediatamente após `cr6.compare<int32_t>(ctx.r3.s32,41,xer)` em `sub_82578988`. `event=1` é contador de callback, não resultado de ramificação/condição de acesso.
- `NFSMW_PRE283_BMW_VTABLE` ausente (0 eventos) neste log; não inferir se a categoria foi exibida, aberta ou chegou ao seu Setup sem confirmação de percurso visual. O código PRE264 tem candidato de condição HeroCar `ctx.r3.s32 == 41` com opção de tratar como não-Hero, mas é somente mock/dry-run sem validação real do ramo; **não aplicar desbloqueio cegamente**.
- Erros relevantes: `D:\\FRONTEND\\PLATFORMS\\CUSTOMIZATION_SHOP.LZC` e `CSHOP_frontEndEnv.dds` com `NtCreateFile FAILED 0xc000000f` durante abertura da loja; também `D:\\CARS\\BMWM3GTRE46\\VINYLS.BIN` e outros. Faltas podem ser recursos opcionais/fallback; não atribuir ausência das categorias a essas mensagens sem auditar fonte e mapeamento. 
- Persistiu C3 às 11:28:40.481: `[NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true]`; caminho de texturas por thread desabilitado pelo restante da sessão. Independente do diagnóstico BMW; sem prova de FPS.
- Log reporta resolução interna 1920x1080, limite FPS 60, dispositivo Samsung Xclipse 940. Sessão saiu para segundo plano e encerrou normalmente por fechamento da janela às 11:29:07; não aparece sinal fatal de crash.
- Próximo passo técnico: PRE302 diagnóstico **somente leitura** de `sub_82578988` para verificar se comparação `type=41` de fato dirige criação de opções via `__imp__sub_82575370`, e inspecionar fallbacks de CUSTOMIZATION_SHOP.LZC antes de qualquer patch no ramo ou release V40. Preservar assinatura permanente, MARCEK, 1920x1080, controles e V39.


## PRE302–PRE305: BMW modelo 41 — 2026-11-07
- V39 log real PRE303 registrou `[NFSMW_PRE292_BMW_MENU] callsite=0x82578988 type=41 event=1`. Esse marcador é pré-salto lógico; não revela execução dos itens nem atribui rótulos.
- PRE302 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42389794686 **completed/success**, auditou função PAL original `sub_82578988` do PRE99 SHA `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`, sem patch. Encontrou uma comparação a `41` na linha relativa 32, salto condicional à linha 35, destino 39 e cinco chamadas a `__imp__sub_82575370(ctx, base)`. PRE302B https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42389945142 reproduziu trecho de PPC para revisão.
- Caminho verificado: `r10=1` quando `type=41`, `r10=0` em outros carros; com flag global `0`, `r10=1` salta sobre chamadas 1 e 2 (IDs `2049`, `2050`), enquanto com flag global não-zero salta sobre chamadas 3 e 4 (mesmos IDs). Chamada 5 `2051` não condicionada por esses saltos. Código mostra `2051` como opção remanescente, mas rótulo Visual é inferência a validar.
- PRE304 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42390247261 **success**, `PRE304_STATUS AUDIT_OK`, confirmou tabela de condições dos dois caminhos da fonte: modelo `41` adiciona somente código `2051`; demais modelos geram `2049,2050,2051` (sem afirmar que todos têm conteúdo de upgrade válido). Sem alterar guest, save ou build.
- PRE305 implementou builder EXPERIMENTAL `automation/kaggle/pre305_build_signed_v40_bmw_menu_gate_experimental.py`, derivado do builder assinado V39. Somente em `sub_82578988` PAL insere PRE264 `cr6.eq=false` para `r3.s32 == 41` **dentro de macro habilitada no builder**, preservando `r3`, código de upgrades, guest loads/stores, chamadas existentes, controles e diagnósticos V39. Alvo versionCode `40`, pacote `io.github.nfsmwrecomp`, **mesmo certificado permanente** `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; backups V39/MARCEK intactos.
- Workflow PRE305 https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42390457193 iniciado; estado **em execução** na última consulta. **Não afirmar V40 compilada, assinada, validada, publicada ou testada até relatórios/Drive comprovarem.**
- PRE305 é teste de desbloqueio de **opções do menu**, não garantia de que peças/desempenho funcionarão para um veículo de tipo especial nem de preservação do save em gameplay. Um APK experimental só deve ser testado após backup externo do save; abrir categorias pode expor caminhos de jogo originalmente bloqueados. Se falhar, restaurar V39 com mesma chave e versão downgrade requer desinstalação ou outro procedimento que preserva dados, não recomendar desinstalação sem backup confirmado.
- Se PRE305 compilar e publicar, auditar certificado, versionCode=40, hash de Drive e comportamento da BMW antes de promover qualquer patch como resolvido.


## PRE305/V40 falha identificada, PRE305B reparada e retry — 2026-11-07
- Primeiro run experimental V40 https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42390457193 **failed**, relatório da execução mostra `PRE170_GRADLE_BUILD_FALHOU`, `gradle_release_exit_code=1`, `APK verified False`, `Drive upload False`. Inspeção do relatório com PRE305B https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392051414 confirma erro Clang em PAL C++ gerado, linha 22762: `token is not a valid binary operator in a preprocessor subexpression`. Macro do builder tinha barra invertida+n literal dentro de `#define NFSMW_PRE264_BMW_MENU_ENABLE 1\\n` em vez de uma quebra real de linha, incluindo guarda de reversão. **Não é erro da chave, Drive nem versão Android**.
- Correção comitada no builder `automation/kaggle/pre305_build_signed_v40_bmw_menu_gate_experimental.py`: substituir ambas as ocorrências por newline Python real, verificar `preview.splitlines().count(directive)==1`, recusar `directive+r"\\n"`. Não reaplicar patch em workspace antigo: nova run usa PRE99 original autenticado, fonte com fingerprint obrigatório e staging uma só vez.
- Gate sintético `automation/kaggle/pre305b_gate_macro_preflight.py` compilou com C++ (sem fonte do jogo, APK ou chaves), run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392338077 **completed/success**, `PRE305B_MACRO_AST_OK True`, `PRE305B_SYNTHETIC_CPP_COMPILE_OK True`. A falha do primeiro canário foi apenas no filtro AST do teste, corrigido no segundo.
- Workflow V40 agora exige PRE305B antes de preparar SDK/Gradle. **Nova tentativa** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392404962 foi acionada. Último estado confirmado para este registro: queued; verificar resultado antes de afirmar build/assinatura/upload. versionCode 40, assinatura permanente e V39 preservados, sem modificação do save MARCEK.
