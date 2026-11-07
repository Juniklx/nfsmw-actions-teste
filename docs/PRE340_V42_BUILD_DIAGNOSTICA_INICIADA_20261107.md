# PRE340 — V42 Nitro diversity passive diagnostic: build started (2026-11-07)

## Source, scope and run
- Derived build script: `automation/kaggle/pre340_build_signed_v42_nitro_diversity_passive.py`, derived from V41 PRE318 builder, with `VERSION_CODE=42` and `APK_NAME=NFSMW_V42_PRE340_NITRO_DIVERSITY_PASSIVE.apk`.
- Workflow: `.github/workflows/nfsmw-pre340-v42-nitro-diversity-passive.yml`.
- Trigger commit: `3bd0b7c14250663db49ef62edaa0b510b05e0e14`.
- Run: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42413667387; job ID `128526993478`.
- **Estado quando este registro foi criado:** job `in_progress`, etapa `Build V42 signed passive Nitro diversity diagnostic and verify permanent certificate and both ELF markers` em execução. **Não declarar APK gerada, assinada ou publicada sem relatório e artefato final.**

## Características da alteração
- A base PRE318/PRE317/PRE316 da V41 foi preservada.
- PRE337 acrescenta observador PRE336 após a aplicação PRE317 em workspace descartável, com `guest_stores_rewritten=0`, `extra_guest_loads=0`, `cheat_enabled=false`, `owner_verified=false`, reversão exata e proibição de aplicar duas vezes.
- O construtor exige marcador `NFSMW_PRE336_NITRO_DIVERSITY` no ELF PAL e na APK assinada, além da instrumentação PRE316, dos marcadores BMW e C3 da V41 e da conferência de certificado permanente.
- Identificador do pacote `io.github.nfsmwrecomp`; `versionCode=42`, mesma chave permanente e certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não regenerar chave, não expor senhas.
- PRE336/PRE337/PRE338 foram validadas via CI previamente; no próprio workflow V42 os testes sintéticos e a compilação nativa do callback no Linux concluíram com sucesso antes do estágio de release.
- O workflow cria artefato privado `nfsmw-pre340-v42-nitro-diversity-<run_id>` com JSON e APK, se produzida. A publicação no Drive deve ser verificada por readback no relatório do construtor.

## Critérios obrigatórios para promover o estado
1. Verificar status do job (inclusive etapa `Build` e gate final, não só `success` do workflow).
2. Recuperar JSON do artifact e conferir `gradle_release_succeeded`, `signed_apk_verified`, `target_version_code=42`, certificado exato, SHA do APK, ELF PAL e marcadores PRE316/PRE336.
3. Se upload falhar, diferenciar APK validada localmente de cópia no Drive; artefato GitHub é recuperação possível, não prova de upload.
4. Mesmo com APK assinada, Galaxy S24 FE ainda não terá testado PRE336 até instalação controlada com save MARCEK preservado.
5. `owner_verified=false` até evidência independente de veículo jogador/NPC. Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam DESATIVADOS na V42 diagnóstica.

## Proibições
- Não remover limitações térmicas, reduzir 1920x1080, shaders, efeitos ou física.
- Não tocar no controle PG-9076/touch, save MARCEK ou APK V41.
- Nenhum valor de Nitro forçado, nenhum endereço fixo usado como seletor de jogador.
