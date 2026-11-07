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
