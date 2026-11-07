# PRE340 — APK V42 diagnóstica compilada, assinada e publicada (2026-11-07)

## Evidência primária verificada
- GitHub Actions `42413667387`, job `128526993478`: `completed/success`, incluindo build, verificação e gate final de release.
- Artifact ID `13590129971`, nome `nfsmw-pre340-v42-nitro-diversity-42413667387`, contém `pre340-v42-report.json` e `nfsmw-v42-nitro-diversity-verified.apk`.
- Relatório do builder: `PRE340_V42_PASSIVE_NITRO_DIVERSITY_SIGNED_VERIFIED_ARTIFACT`, `phase=COMPLETE`, `gradle_release_succeeded=true`, `signed_apk_verified=true`, `drive_upload_success=true`.
- SHA-256 da APK calculado independentemente em cópia extraída do artifact e novamente em bytes baixados pelo conector Google Drive: `5bcb301663149f516d60b1327d9b51992ddf1698cd71a7a571d5190a9d037c1a`.
- Tamanho: `47103185` bytes nas duas cópias.
- Drive APK: `NFSMW_V42_PRE340_NITRO_DIVERSITY_PASSIVE.apk`, ID `1fZ4_4iBNuVEKKkMBmRTgH81WHSALrN3V`, https://drive.google.com/file/d/1fZ4_4iBNuVEKKkMBmRTgH81WHSALrN3V/view ; upload retornou `remote_md5_matches=true` e `folder_verified=true`.
- `package_id=io.github.nfsmwrecomp`, `version_code=42`; pacote exigido e certificado release permanente do APK v2 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` conferidos.
- Dez bibliotecas ARM64 requeridas presentes, shaders PAL/USA preservados, library USA original preservada.
- Dentro do libmain ARM64 assinado: marcadores `NFSMW_PRE316_NITRO_CYCLE` e `NFSMW_PRE336_NITRO_DIVERSITY` confirmados.
- Staging PRE337: `guest_stores_rewritten=0`, `extra_guest_loads=0`, `cheat_enabled=false`, `owner_verified=false`, `reverse_exact=true`; nenhum cheat funcional foi adicionado.

## Distinção de estados
- **Comprovado:** APK V42 compilada, assinada com certificado original, verificada e publicada no Drive; bytes do Drive coincidem com artifact GitHub.
- **Não comprovado:** instalação da V42 no Samsung Galaxy S24 FE, abertura do jogo, logs PRE336 reais, identificador exclusivo do veículo jogador, melhora de FPS ou qualquer cheat infinito.
- PRE336 é diagnóstico passivo que registra slots efêmeros do endereço guest; nunca interpreta slot como dono/jogador sem evidência independente.

## Próximo teste no aparelho
1. Com backup independente do save `MARCEK` já preservado, instalar V42 sobre V41 **sem desinstalar** o jogo, evitando perder dados.
2. Abrir jogo, dirigir e utilizar Nitro até esvaziar; deixar recarregar. Capturar `nfsmw.log`.
3. Procurar `NFSMW_PRE336_NITRO_DIVERSITY` e `NFSMW_PRE316_NITRO_CYCLE`, verificar contagem/overflow/slots sem pressupor carro jogador.
4. Se falhar instalação ou jogo, recuperar logs e APK V41 e não mexer em save ou certificado.
5. Sem evidência independente de player car/NPC, Nitro infinito, Speedbreaker infinito e dinheiro ilimitado permanecem **desativados**.

## Integridade
APK V41 preservada. Nenhuma modificação de gráficos, 1920x1080, física, controle PG-9076/touch ou limitações térmicas. Não criar nova chave ou solicitar senha.
