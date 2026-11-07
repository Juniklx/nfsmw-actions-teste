# PRE316–PRE318 — Nitro ciclo completo, monitor passivo e build V41

Data: 2026-11-07.

## Base
PRE313 log 14:57 usuário drenou Nitro por completo e esperou recarga visual completa. Logger PRE247 limitado a 12 amostras não registrou limiares finais. PRE312 PAL fonte autenticada 5 stores +252 em `sub_82424AF0`. Não tocar nem alterar esses stores.

## PRE316
Novo header `automation/kaggle/pre316_nitro_cycle_monitor.hpp`:
- Usa exclusivamente bits `float` já escritos (passados pelo PRE247) para amostras sem leitura adicional de memória guest.
- Mantém mínimos/máximos e número de amostras por site 1–5.
- Emite eventos ao mudar faixa 0–0.5%, 0.5–5%, 5–25%, 25–75%, 75–95%, 95–99.5%, 99.5–101% e checkpoints na contagem potência de 2 até 8192.
- Ignora NaN/Inf/negativos/floats fora da faixa válida; conta e limita transições a 36/site. Sem ativação de cheats, save ou escrita adicional.
- Não substitui store original: logs de `NFSMW_PRE316_NITRO_CYCLE` resumem apenas mudanças.

## PRE317
`automation/kaggle/pre317_nitro_cycle_staging.py` injeta novo logger na fonte auxiliar **já criada** pela PRE247 em workspace isolado, exigindo fonte exata `CPP_TEXT`. Mantém o `NFSMW_PRE247_CHEATS_DIAG`, checksum/backup do logger, CMake existente, sem alterações nos stores PPC, usuário ou arquivos do save.
`pre317_nitro_cycle_staging_mock.py` executa callback completo com C++ host, incluindo 40.000 chamadas repetidas para provar volume limitado.

**Verificação:** GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42399887087 `completed/success`, `PRE316_STATUS AUDIT_OK` (4 asserts) e `PRE317_STATUS AUDIT_OK` (`PRE317_SYNTHETIC_LOG_CAP_OK 57`). Isso não é compile real NDK/Android e não prova Nitro infinito.

## PRE318 / V41
Builder `automation/kaggle/pre318_build_signed_v41_nitro_cycle_passive.py` derivado da V40 PRE305 com:
- `versionCode 41`; `io.github.nfsmwrecomp`; mesmo certificado permanente esperado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Preserva V40: menu BMW gate, PRE283/PRE292, C3, PRE246 dinheiro e PRE247 diagnóstico. Novo `apply_pre317(root)` somente após PRE247.
- Exige `NFSMW_PRE316_NITRO_CYCLE` no `libmain.so` antes de declarar APK válida.
- Usar fonte PRE99 hash autenticado e runner isolado, sem reusar/reaplicar patch em árvore antiga.
- Workflow `.github/workflows/nfsmw-pre318-v41-passive-nitro-cycle.yml` exige os canários PRE316/PRE317 e gate macro PRE305B antes do build.
- **Run acionada:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42400074496 . Ao registrar este documento, `queued`, **ainda sem APK V41 validada/assinada/publicada/testada**.

## Próximo passo
1. Conferir run PRE318 até completar; se falhar, examinar relatório sanitizado antes de alterar patch.
2. Se `success`, confirmar versão/certificado, `APK verified True`, `Drive upload True` e arquivo no Drive.
3. Só após backup independente do save MARCEK, teste no S24 FE: iniciar jogo, gastar Nitro até zero e esperar recarregar, coletar `nfsmw.log`; procurar `NFSMW_PRE316_NITRO_CYCLE` site 1–5 incluindo faixas e mínimos/máximos.
4. Nitro infinito, Speedbreaker infinito e dinheiro ilimitado **continuam não ativados**. PRE309 é política C++ mock desconectada do jogo. Não usar valores falsos ou bypasses de proteções térmicas.
