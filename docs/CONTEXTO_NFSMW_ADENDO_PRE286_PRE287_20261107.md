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
