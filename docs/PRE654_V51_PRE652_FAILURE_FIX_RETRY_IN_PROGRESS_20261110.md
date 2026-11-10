# PRE654 — PRE652 V51 bloqueada em PRE305, composicao corrigida e retry PRE651/652 (2026-11-10)

## Evidencia da primeira falha — nenhum APK V51

- Run GitHub Actions [42797492310](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42797492310): `completed/failure`. Job `129766279147` chegou a receita do PRE401 e parou na fase `PRE305_STAGE_BMW_MAIN_MENU_PASSIVE_TRACES` com `ValueError`. O relatorio bruto `pre652-v51-report.json` contem `signed_apk_verified=false`, `drive_upload_success=false`, `PRE652_STATUS=NOT_VERIFIED` e `PRE652_V51_GPU_DIAGNOSTIC_NOT_VERIFIED`. Artefato bruto GitHub ID `13754912561`, ZIP arquivado no Drive `06_Logs_e_Medicoes/NFSMW_PRE652_V51_FAILED_PRE305_REPORT_42797492310.zip` ([abrir](https://drive.google.com/file/d/1ZcvtDTcfIVNF82oOG5DM4b_Mmw92CrfC/view)). SHA-256 ZIP `e3e56018f7154e784675b5261a146d9afa22cb672dd1a823359074dbd8e987a1`, CRC testado.
- **Causa de composicao sustentada pelo codigo:** o primeiro script V51 usou `pre648.stage_source()`, uma rotina feita para a arvore PRE648 nativa **ja reconstituida** pelo PRE431. Tal rotina troca temporariamente o helper PRE292 pelo `skip_duplicate_menu`, que exige a inscricao de menu preexistente. Na receita de release PRE401/PRE305 isso e chamado **antes** da inscricao de menu: conflito no estagio de fonte. O log sanitizado so registrou `ValueError`, sem resumo preciso da excecao; a causa detalhada e inferida de inspecao do codigo e fase de falha, nao uma mensagem literal da excecao.
- Nao houve build ARM64 da V51, APK gerada, assinatura testada ou upload da V51 na primeira tentativa; nenhuma chave de assinatura foi recriada. V50 PRE638 permanece a ultima APK assinada **confirmada**.

## Correção no codigo de producao

- Commit `c015570775b6cab71cd052e8afbdac2676a947cc`: `automation/kaggle/pre652_build_signed_v51_gpu_shader_counts_diag.py` agora chama **`v50.stage_v50(root)` somente uma vez**, que realiza todo o estagio de producao PRE638/V49/menu normal e autentica SHA original C3, **antes** de invocar `shader.patch_bytes(original)`. Em seguida exige SHA-256 exato da fonte instrumentada `9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2` e do header `9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe`, readback e reversibilidade. Recusa header preexistente/patch duplicado. Nao altera shader SPIR-V, guard C3, Nitro, BMW, controles, efeitos ou fontes/arquivos do Drive.
- A PRE651 anterior run 42796992562 era valida **somente para o script V51 anterior** e foi preservada no Drive e `docs/PRE651_V51_INITIAL_PREFLIGHT_SUPERSEDED_AFTER_PRE652_STAGE_ERROR.json`. Nao reutilizar esse gate inicial como autorizacao de novo build.

## Revalidacao apos correção

- Novo run GitHub Actions [42798605525](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42798605525): `completed/success`, job `129770042729`, `AUDIT_OK_NO_APK`. A verificacao confirmou contratualmente `v50.stage_v50(root)` seguida por `shader.patch_bytes(original)` e a identidade de release existente, com ASan/UBSan do contador. NAO realizou novo staging real, build Android ou assinatura.
- Artefato PRE651 retry (CRC validado): ZIP SHA-256 `1ecba3e5c7fef96c073d272d56c3f3bf9ca924338e4f8e94e5fd03a66a0ab305`, JSON SHA-256 `c707dab9dcaed9876fa60b64b21a6d16c801b659efc76e1137760a86adbed87a`; [ZIP arquivado no Drive](https://drive.google.com/file/d/17doJ3BNHwxHeClS-LpqvBVcny-sfwQVN/view). Novo script PRE652 SHA-256 `97f5b455a1cc09405b5afcb8e0f941cfc6ca5b73d59c1d8114b7df64f20e919f`. Registro ativo `docs/PRE651_V51_GPU_RELEASE_PREFLIGHT_VERIFIED.json` atualizado com novo run, registro inicial preservado em arquivo distinto.
- Retry PRE652 [42798909503](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42798909503), acionada via trigger `automation/kaggle/pre652_requests/retry_after_PRE651_corrected_source_composition_20261110.json` (commit `02e27461d78791c6125299c979ffccffd61a5d42`). Acompanhada em `in_progress` na fase de preparacao de ferramentas Android, **ainda SEM resultado confirmado neste checkpoint**.
- Politicas intactas: `io.github.nfsmwrecomp`, `versionCode 51`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; nada de nova chave/assinatura debug. Contador agrega frequencias VS/PS/passe a cada ~10s, sem logs por draw, SPIR-V/qualidade/fisica/regras termicas modificados. Nenhum FPS ganho comprovado.

## Proximo gate

1. Consultar **run 42798909503**, job/log e relatorio de artefatos. Se falhar, identificar fase e erro antes de qualquer novo patch, sem reaplicar instrucao a cegas.
2. Se run for sucesso, conferir APK V51 por assinatura v2 e `apksigner` com certificado permanente; `aapt` pacote e versionCode 51; SHA256 e ZIP; marcador `PRE648 GPU_SHADER10s`, Nitro PRE398, C3 PRE194/PRE635, quatro callbacks BMW; comparacao PAL/USA shaders com hashes historicos; upload remoto no Drive, nome novo, MD5/SHA.
3. So apos APK validada solicitar instalacao de atualizacao **sem desinstalar** e testes no Samsung Galaxy S24 FE. Recolher `nfsmw.log`, verificar contagens por shader e passe, invalid e cenas. Nao confundir contagens de draws com tempo GPU individual, nem anunciar ganho FPS.
4. Prioridade permanece shaders/GPU; analise C3 PRE643 adicional, fluidez e SurfaceFlinger suspensas por decisao anterior. Preservar 1920x1080, alvo 120FPS, qualidade integral, controle touch/PG-9076 e protecoes termicas.

**Estado no checkpoint:** PRE651 corrigida APROVADA; PRE652 retry em execucao, nao concluiu; V50 ultima APK assinada comprovada.
