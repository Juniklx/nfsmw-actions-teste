# PRE159 — Coleta SF/C2/Vulkan/termica da APK V32 (somente leitura)

- Fonte: PRE152 validada para V31 (mesma coleta); única mudança funcional é aceitar `versionCode=32` e usar identificador de saída PRE159/V32.
- SHA-256 do arquivo local testado: `b417b68d4cf4a116377aadcb490665ecea753c55a5f9975dc23bae96360958d9`.
- No Galaxy S24 FE, com Termux e Shizuku ativos, APK V32 instalada e jogo fechado:

```bash
bash ~/storage/downloads/nfsmw_pre159_v32_surfaceflinger_pareado.sh 240 20
```

- Ele próprio abre o jogo com `--present_perfil_pintado`, recolhe 12 amostras a cada 20 s, tenta desabilitar TimeStats no final, e grava `/sdcard/Download/nfsmw_pre159_v32_surfaceflinger_*.txt`.
- Enviar o TXT e os `nfsmw.log`/`nfsmw.1.log` mais recentes; validar `VERSION_CODE=32`, `REMOTE_RC=0`, camada `SurfaceView`, GPU e térmica, FPS de intervalos e condição inicial antes de comparar V31/V32.
- A coleta PRE159 ainda não foi executada no telefone. Não muda FPS, gráficos, sincronização Vulkan, assinatura, controles ou proteções térmicas.
