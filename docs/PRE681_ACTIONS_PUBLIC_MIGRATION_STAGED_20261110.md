# PRE681 — migração para o Actions público original (2026-11-10)

## Identidade e estado conferidos

- Repositório: `Juniklx/nfsmw-actions-teste`, visibilidade `public` confirmada via API GitHub.
- Script criado: `automation/kaggle/pre681_actions_v51_archive_readonly.py` (commit `6233eaaa40663a4fc1ea32cd8f5c3ebd22ed78ec`).
- Workflow manual criado: `.github/workflows/nfsmw-pre681-v51-graphics-readonly.yml` (último commit de ajuste `8b5c0f69af7e08be32d9e4b7f169e9fff141a921`).
- `workflow_dispatch` exclusivamente, branch `main`, `github.actor=Juniklx`, runner `ubuntu-latest`, `permissions: contents: read`. Nenhum trigger de PR/push, `upload-artifact`, assinatura ou build de APK.
- Secrets de repositório requeridos: `GOOGLE_REFRESH_TOKEN`, `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`. O workflow PRE194 existente referencia esses mesmos nomes. A existência/validade dos valores nos Settings atuais não foi verificada; não enviar valores para chat.
- Entradas privadas pinadas via Drive: APK V51 PRE652 (47.104.417 B SHA256 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b), snapshot fonte (21.026.481 B SHA256 0ab7c949e62d377f444fb7b2489bc66d6387bd49b1798f184c4a953314064231), log PRE656 (576.129 B SHA256 649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7).
- Resultado planejado: baixar somente os insumos, validar CRC, TOML e anchors Java/DEX arquivados, observar resolução 1920x1080 e cap 60 no log PRE656, enviar somente ZIP de evidência ao Drive privado em `06_Logs_e_Medicoes` e conferir SHA256 do readback.
- Status: **MIGRATION_STAGED_NOT_EXECUTED**, Secrets **NOT_VERIFIED**, GPU/FPS/valores reais de blur/sombras do dispositivo **UNKNOWN**, nenhuma APK V52, nenhuma otimização/patcheamento.

## Aviso de segurança após tornar público

- O run histórico PRE194 42145746704 mantém artefato `nfsmw-pre194-v36-PAL-C3-42145746704` (id 13470459762, ~45 MB, `expired=false`, expiração informada para 2026-11-20). Segundo o histórico, seu ZIP contém APK V36. Como o repo agora é público, verificar/remover artefatos antigos sensíveis antes de acrescentar credenciais novas e auditar workflows antigos que recebam Secrets.
- **Nunca colocar ISO, APK, arquivo .p12, .properties, saves ou logs privados no Git, nos logs públicos ou nos artefatos do Actions.** Prefira acesso OAuth com menor escopo possível e monitorar as permissões.
- Chave de assinatura permanente permanece no Drive privado, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; PRE681 não a lê nem assina nada.

## Próximo passo

1. Revisar/remover artefatos antigos de APK e auditar acesso a Secrets após a mudança de visibilidade.
2. Confirmar três Secrets em `Settings > Secrets and variables > Actions` sem mostrá-los.
3. Disparar manualmente `NFSMW PRE681 - V51 graphics archive (private Drive, read-only)` na `main`.
4. Consultar logs e artefato privado mais recente no Drive; somente depois registrar RUN e PASS/FAIL no CONTEXTO_NFSMW.md canônico.

Sem testes no Galaxy nem medição de FPS nesta migração.
