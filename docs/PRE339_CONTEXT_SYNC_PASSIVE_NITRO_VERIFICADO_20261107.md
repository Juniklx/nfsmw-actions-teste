# PRE339 — Contexto canônico atualizado com PRE336–PRE338 (2026-11-07)

## Execução autenticada
- Arquivo original: `CONTEXTO_NFSMW.md` ID `1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB` no Google Drive.
- Workflow `.github/workflows/nfsmw-pre339-sync-passive-nitro-context.yml` e script `automation/kaggle/pre339_sync_passive_nitro_context.py` preservam o histórico e acrescentam seção `PRE339_NITRO_DIVERSIDADE_PASSIVA_PRE336_338_20261107`.
- Run inicial `42412734392` concluiu job `success`; conector Drive confirmou a seção nova e backup `CONTEXTO_NFSMW_BACKUP_ANTES_PRE339_NITRO_20261107.md` (ID `1a4G5048-xmLPAq2wqEBrYGnwI-kXoql3`, 639.364 bytes). **O resumo inicial de CI estava `NO_REPORT` porque o caminho local tinha sido herdado de PRE335**, não porque o contexto estivesse ausente.
- Corrigido caminho `/tmp/nfsmw-pre339/CONTEXT_SYNC_STATUS.json` no commit `c9d20ebc4e2a53fb28a3b38f8fb1427b8cbc3ac2`. Reexecução idempotente run `42412811107`, job `128524387256`, `completed/success`; status allowlisted `ALREADY_PRESENT`, `readback=true`, `context_bytes=641744`. Não duplicou a seção.
- Snapshot atual do contexto no Drive: **641.744 bytes**, seção PRE339 conferida. Backup anterior permanece.
- Nenhuma alteração de APK, jogo, assinatura, controle, save ou recursos gráficos.

## Evidências adicionadas
- PRE336 C++ host-only de diversidade do destino Nitro: run `42412305302` AUDIT_OK.
- PRE337 staging reversível de callback em código temporário: run `42412457916` AUDIT_OK.
- PRE338 compilação C++ nativa (runner Linux com stub logger): run `42412580592` AUDIT_OK.
- **Nenhum desses testes prova ARM64/Android ou owner exclusivo do jogador**. Nenhuma V42 foi produzida. Nitro infinito não está implementado funcionalmente.
- Próximo gate: integração e link ARM64 isolados, com controle das operações guest inalteradas; posteriormente APK passiva diagnóstica testada na S24 FE apenas quando a build estiver verificada.
