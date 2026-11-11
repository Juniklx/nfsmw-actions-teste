# PRE691 — RADV Xclipse v1.8.0 vs APK nativa V51: auditoria estática

Data: 2026-11-11. Sem instalação de driver, compilação ou alteração de aparelho.

## Base de comparação

- Referência preservada: V51 PRE652, APK de 47.104.417 bytes, armazenada no Drive em 02_APKs/NFSMW_V51_PRE652_GPU_SHADER_PASS_FREQUENCY_DIAGNOSTIC.apk, SHA256 do APK auditado 207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b.
- Não inferir que o APK auditado foi extraído do aparelho: o arquivo é do Drive, inspecionado offline.
- PRE690 documentou SurfaceView ativa com 2335 timestamps únicos, 2333 intervalos contínuos (<100 ms). Arredondados: 8-9ms=257, 16-17ms=1818, 25ms=256, 33ms=2; 290 transições 8↔25ms; lacuna ~1116ms de cobertura incerta. Não inferir causa no driver.

## Pacote RADV público, não executado

- Repositório: https://github.com/JimVulkan/radv-xclipse
- Release v1.8.0 (2026-10-19), pacote não Wayland radv-xclipse-27.0.0-devel-269238e.zip, 4.383.848 bytes, SHA256 oficial 0545b1b24817cc0ed4a9e4fc440a7080cbaf69a9ce5d1e4bb22b0e697129c223.
- GitHub Actions run 43021930151, job 130526974277: completed/success. Confirma SHA256, integridade ZIP/CRC, meta.json com libraryName=vulkan.radeon.so, ELF64 AArch64. A biblioteca não foi executada nem instalada.
- Autor declara suporte à Xclipse 940, mas não a comprovação de NFSMW no S24 FE nem ganho de FPS.

## Código-base Android auditado

Fonte victorgbd/NFSMW-Recompiled-Mobile, commit fixado 0b3b3be1f700e2227c03b557dc33e9e50a56c6cc:
- Drivers.java importa ZIP, lê meta.json/libraryName, copia .so para armazenamento interno e registra .libreria; não limita a biblioteca a libvulkan_freedreno.so. esTurnip() separa a opção de turbo.
- Ajustes.java passa --android_gpu_driver_dir e --android_gpu_driver_name; turbo apenas se d.esTurnip() && turbo().
- tools/parche_turnip.py inclui adrenotools_open_libvulkan com ADRENOTOOLS_DRIVER_CUSTOM, se REX_HAS_ADRENOTOOLS; pode tentar fallback para driver de sistema.
- A CI conferiu esses três arquivos do commit fixado. Isso, isoladamente, não prova o comportamento da APK atual.

## APK V51 REAL DO DRIVE: auditoria independente

Analisada somente via ZIP/DEX/ELF:
- APK íntegra por zipfile.testzip(). DEX classes.dex contém strings gpu_drivers, libraryName, android_gpu_driver_name e libvulkan_freedreno.so.
- lib/arm64-v8a/librexruntime.so é ELF64 AArch64 e exporta adrenotools_open_libvulkan e adrenotools_set_turbo, confirmados por readelf -Ws. Contém mensagens de sucesso Vulkan: driver propio cargado con adrenotools e fallback Vulkan: adrenotools no pudo cargar.
- libmain.so e libmain_usa.so referenciam librexruntime.so via DT_NEEDED.
- Conclusão: V51 empacota componentes necessários para tentar carregar driver personalizado. NÃO comprova que RADV inicializa VkInstance/VkDevice, apresenta imagens ou desenha corretamente.

## Limites e riscos

- O autor do RADV alerta para travamentos de GPU que podem provocar reinício do aparelho. Evitar substituir driver global, forçar propriedades Vulkan, modificar thermal ou usar turbo.
- BCn e outros formatos podem afetar fidelidade; preservar gráficos, efeitos, 1920x1080, física, limite de 60 FPS observado na PRE690, saves e controles.
- Preservar V51: pacote io.github.nfsmwrecomp, versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b.

## Próximo gate

Obter PRIMEIRO relatório Test Vulkan/Probar Vulkan com driver do sistema na V51; registrar driver efetivamente carregado, GPU e resultado. Eventual importação do RADV e teste Vulkan apenas após ciência do risco de GPU hang, mantendo possibilidade de retorno ao sistema. Comparação A/B de fps/frame pacing somente após gate de compatibilidade, sem reduzir qualidade ou alterar proteção térmica.

STATUS PRE691: RELEASE_SHA256_AND_FORMAT_PASS; UPSTREAM_GENERIC_DRIVER_IMPORT_PASS; V51_APK_ADRENOTOOLS_LOADER_PRESENT; DEVICE_RADV_TEST_PENDING; NO_APK_BUILD; NO_RADV_INSTALLED; NO_FPS_GAIN_PROVEN.
