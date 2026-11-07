# PRE335 — Contexto canônico Drive sincronizado com fluxo GitHub Actions + Kaggle e Nitro PRE329–PRE334 (2026-11-07)

## Resultado confirmado
- GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42411960233, job `128521824842`, terminou `completed/success`.
- Status interno `SYNC_OK`, `readback=true`, `backup_created=true`, `backup_unchanged=true` consultado em `docs/generated/PRE328_PRE335_SANITIZED_STATUS.json`.
- Arquivo canônico editado preservando **o mesmo ID**: [CONTEXTO_NFSMW.md](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view). Nova extensão de 639.364 bytes.
- Backup prévio validado via readback, preservado com nome `CONTEXTO_NFSMW_BACKUP_ANTES_PRE335_NITRO_20261107.md`, ID `1USXrOO9QKEHTYd7xrI2pDqIhBAFzRMtz`, 635.133 bytes, pasta preexistente de backups.
- Verificação adicional com o conector Drive: seção `PRE335_NITRO_CHEATS_GITHUB_KAGGLE_PRE329_334_20261107` presente no arquivo canônico atualizado; `modifiedTime=2026-11-07T20:37:52.940Z`.
- Script `automation/kaggle/pre335_sync_nitro_actions_kaggle_context.py` e workflow `.github/workflows/nfsmw-pre335-sync-nitro-context.yml` usam credenciais já configuradas no GitHub Actions, fazem backup antes de sobrescrever, conferem versão e verificam conteúdo por readback. Nenhuma credencial foi divulgada nos logs.
- O contexto preservou histórico anterior e ganhou seção final com fluxo GitHub Actions/Kaggle/Drive, readback PRE328, resultados PRE325/PRE327 e evidências PRE329–PRE334.

## Estado do jogo e limitações
- Nenhuma APK nova, patch guest, alteração de assinatura ou save. V41 PRE318 continua referência.
- Na PRE334, apenas a função Nitro `sub_82424AF0` entre as seis qualificadas apresentou a combinação estrita de origem r3, leitura/gravação do campo +252 e consulta +296. Isso **não** identifica o owner do jogador.
- Nitro infinito, Speedbreaker infinito e dinheiro ilimitado **não são funcionais** na V41; não criar V42 usando somente endereço fixo `0xBFA9E7FC`.
- Próxima ação técnica: referência independente ao veículo do jogador e comparação real com NPC/IA, mantendo indeterminado quando não for possível provar identidade.
