# NFSMW — PRE123 a PRE126, pipeline V27 PAL/USA (2026-11-04)

## Origem e objetivos

- Manter V26 PAL+USA original e o snapshot PRE99 inalterados.
- Corrigir exclusivamente a rolagem aninhada do `Settings##rex` no Android por PRE117, sem inserir PRE111/tema nem PRE115/reset de rolagem.
- Preservar versão, assinatura permanente, assets PAL+USA, edição USA, 1920×1080, teto 120 FPS, física, gráficos e controles já operacionais.
- A V27 é experimental até teste real no Galaxy S24 FE normal (fora do DeX) e no DeX. Nenhum ganho de FPS pode ser alegado.

## PRE122 — patch preservado

- GitHub Actions [#41833476490](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41833476490), `success`.
- Arquivo `automation/kaggle/patches/pre117_single_scroll_android_verified.patch`, SHA-256 `b26db81bd72075561ddcdaddfadc5f3cde66dad788fe610a42c54ad19d2f087b`.
- Fonte base PRE92 SHA `5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034`.
- Fonte PRE117 proposta SHA `8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af`.
- O dry-run PRE117 anterior passou sintaxe Android NDK r28 ARM64 C++23, mas não comprova comportamento no celular.

## PRE123 — Android build source audit

- GitHub Actions [#41834580799](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41834580799), `success`.
- PRE99 TAR validado por SHA-256 integral. Gradle de app SHA `ef570ba95703cb54df3c0e503fec6bce11aaa0f640e907208bdfb22bd8711230`, CMakeLists, wrapper Gradle, AndroidManifest, fonte PRE92 presentes.
- O diretório `android/app/generated-android` NÃO existe, mas o motor nativo dispõe de árvore `nativo/app` e `nativo/app_usa` que exige auditoria separada. Não inferir ausência de jogo ou release válida por isso.

## PRE124 — native PAL/USA staging + signing metadata

- GitHub Actions [#41835327418](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41835327418), `success`.
- Ambos `nativo/app/generated/default/sources.cmake` e `nativo/app_usa/generated/default/sources.cmake` presentes no PRE99, com 131 fontes C++ geradas em cada pasta.
- Shaders Vulkan e GLES PAL e USA, `nativo/out/usa/edicion.json`, `nativo/app/nfsmw_movil.toml` presentes.
- Diretório de assinatura permanente localizado por metadados no Drive: `.p12`, credenciais `.properties`, contador de versão e arquivo informativo. Nenhum valor privado foi lido nessa auditoria.

## Referência binária V26

- APK original verificado do Drive: `NFSMW_V26_PAL_USA_PRE96_VISUAL_EXPERIMENTAL.apk`, SHA-256 `d8aebdaaf75df75739b47148f69ecfcdf1add37422416249375e31eca7812092`, 47.065.185 bytes.
- A ZIP contém 10 bibliotecas ARM64 incluindo `libmain.so`, `libmain_usa.so` e `librexruntime.so`; shaders PAL e USA, Vulkan/GLES.
- A PRE126 usa V26 como referência imutável e exige correspondência exata de hashes para biblioteca USA e pacotes de shaders, além do arquivo TOML PAL.

## PRE125 — certificação e Gradle preflight concluídos

- GitHub Actions [#41835949128](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41835949128), `success`.
- Em runner efêmero, restaurou PRE99 (28.911 membros), aplicou PRE117 somente nessa cópia e verificou SHA da fonte alvo.
- Recuperou `.p12` e propriedades de assinatura exclusivamente no runner temporário; SHA-256 do keystore `407815601cd41ab6a56a44d0d2eb130a9e0439bf00692d46d43cfba316b5334d` confirmado.
- Verificou por `keytool` certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- `gradlew help` com JDK 21, motor nativo, assinatura permanente e `NFSMW_VERSION_CODE=27` executou `BUILD SUCCESSFUL`. O arquivo original `NFSMW_PROXIMO_VERSION_CODE.txt` no Drive ainda contém `19`; não usá-lo para V27 e não sobrescrevê-lo. O código 27 vem somente da variável de ambiente.
- **Não compila nem assina APK** nesta etapa.

## PRE126 — compilação experimentada, resultado ainda pendente

- Workflow disparado por commit na branch `main`, [GitHub Actions #41837195269](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41837195269).
- Script `automation/kaggle/pre126_build_signed_v27_pal_usa.py`; workflow `.github/workflows/nfsmw-pre126-signed-v27-build.yml`.
- Restaurar PRE99, aplicar PRE117 exata, validar assinatura permanente, importar apenas `libmain_usa.so` e shaders USA já verificados da V26, configurar `-Pnfsmw.motor=nativo -Pnfsmw.edicion=pal_es -Pnfsmw.ediciones=<temporário>`, compilar `assembleRelease`.
- Validar `apksigner`: certificado permanente, `versionCode=27`, pacote `io.github.nfsmwrecomp`; verificar presença das 10 bibliotecas e hashes das edições, shader packs e TOML; garantir alteração de `librexruntime.so` em relação à V26.
- Publicar **somente se TODAS as validações passarem**, como arquivo NOVO na pasta privada `NFSMW_Android/02_APKs`, sem sobrescrever a V26. Se falhar, salvar só diagnóstico sanitizado no GitHub.
- Relatório canônico da execução: `automation/kaggle/status/pre126_v27_signed_release.json` quando Actions terminar.
- Nenhum resultado de build ou upload confirmado ao redigir este adendo; acompanhar o workflow. Nunca declarar V27 pronta enquanto relatório e APK não forem verificados.

## Testes que exigirão o Galaxy S24 FE

- Instalar APK após validação de assinatura; entrar em Settings fora do DeX; verificar uma área de scroll, cabeçalho, primeiras/últimas variáveis, rodapé `SAVE SETTINGS`, toque e PG-9076; repetir no DeX.
- Conferir não-regressão de renderização, ausência de erros, FPS e térmicas com dados reais. Não assumir desempenho por análise estática.
- Não executar as células 0/2 do notebook Kaggle original por automação: PRE120 detectou operações de TAR/Drive e `exec` de script externo. A sessão interativa Kaggle não foi acessada por GitHub Actions.

## Fonte de verdade e preservação

Este adendo privado documenta o trabalho em GitHub. O `CONTEXTO_NFSMW.md` original do Drive NÃO foi sobrescrito; a escrita OAuth anterior retornou 403. Backup do contexto e imagens antigas devem ser preservados. Relatórios GitHub e APKs anteriores permanecem a base de evidência.


## PRE126 result and PRE126B recovery — 2026-11-04 ~13:48 UTC

- Initial [PRE126 run #41837195269](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41837195269) finished **failure** after the full native Gradle `assembleRelease` passed (`gradle_release_exit_code=0`).
- The failure happened strictly in `SELECT_APK_AND_VERIFY`, exception type `ValueError`. The original script recorded no specific validation subcheck. Report: `automation/kaggle/status/pre126_v27_signed_release.json`, `run_id=41837195269`, `signed_apk_verified=false`, `drive_upload_success=false`. Do not claim that V27 is signed/approved/published.
- Verified PRE99 snapshot, exact PRE117 ephemeral patch, permanent certificate and V26 reference integrity all **passed** before validation. Original Kaggle session, V26 Drive APK, signing backups and original version counter were not modified.
- **PRE126B** is a new build retry [run #41841914257](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/41841914257). It uses an updated `automation/kaggle/pre126_build_signed_v27_pal_usa.py` with the same acceptance gates and a new sanitized `verification_subphase`, `validation_failure_code`, `missing_required_arm64_libraries` or `mismatched_preserved_asset` in failure reports.
- Request commit `76506b317fae50d046ea6855e29cb6e0dcadd8af`; triggered by `automation/kaggle/build_pre126_requests/PRE126B_VALIDATION_DIAGNOSTIC_20261104.json`.
- **No current PRE126B success is claimed** until its own `run_id` is found in `automation/kaggle/status/pre126_v27_signed_release.json`, APK is signed/cert verified, package and versionCode are valid, all PAL+USA assets match V26 and the Drive upload readback succeeds.
- Monitoring automation was updated from the failed initial run to PRE126B. The user has no action pending before a valid APK requires device testing or a demonstrable human-only blocker.
