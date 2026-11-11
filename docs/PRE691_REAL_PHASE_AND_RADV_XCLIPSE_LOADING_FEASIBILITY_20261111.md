# PRE691 — Frame pacing real e viabilidade de RADV Xclipse (2026-11-11)

## Estado imutável
APK baseline V51 PRE652, `io.github.nfsmwrecomp`, versionCode=51, SHA256 da APK `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nenhuma APK recompilada, assinada, instalada ou alterada nesta etapa; sem alteração de resolução, shaders, sombras, física, saves, PG-9076, limite FPS, política térmica ou settings Android.

## Evidência real PRE690 -> PRE691 (arquivos privados, não publicados no GitHub)
Captura fornecida pelo usuário `NFSMW_PRE690_ORDERED_PRESENT_20261111_085059.txt`, SHA256 `29f20955434bbcebc4b622995026b2ace00702d20245b57585e1fd6dd7f05dc7`, 189497 bytes. Camada `SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0(BLAST)`, duas candidatas, uma avançando; 30 amostras válidas, 2.335 timestamps de apresentação distintos, 1.308 duplicados descartados. Lacuna de 1.115,960977 ms excluída por **incerteza de cobertura**, não classificada automaticamente como travamento real.

Reexecução local do analisador `pre691_triple_timestamp_phase_audit.py` produziu JSON byte a byte idêntico ao relatório PRE691 existente (SHA256 JSON `e39bc9dd30a579fcf7a9f06d7ef1ac84184aee725347711fb4703b7d289d75f0`). 2.333 intervalos contínuos:
- delta **desired** média 16,665876 ms, desvio-padrão populacional 0,816197 ms;
- delta **frame-ready** média 16,665740 ms, desvio-padrão 2,325713 ms;
- delta **actual** média 16,668695 ms, desvio-padrão 3,945334 ms;
- buckets arredondados de actual: 8ms=246, 9ms=11, 16ms=96, 17ms=1722, 25ms=256, 33ms=2;
- transições consecutivas de intervalos actual **8->25 = 136** e **25->8 = 154**, sem atravessar a lacuna.

A informação `frame_ready` pode derivar de fallback, não prova término da GPU. `desired_present` não é timestamp da chamada `vkQueuePresentKHR`; `actual_present` não é uma medição óptica do painel. Não foi demonstrada causa exclusiva em `MAILBOX`, driver Samsung, SurfaceFlinger, display ou thread do app. Log original mostrou `VulkanPresenter` com swapchain `1920x1080`, modo `MAILBOX`, mas não imprimiu nome/versão do driver.

## Audit RADV Xclipse: opção existente no upstream, não validada na APK V51
Repositório oficial da adaptação: https://github.com/JimVulkan/radv-xclipse
- RELEASE ESTÁVEL PINADA: v1.8.0 de 2026-10-19. Artefato `radv-xclipse-27.0.0-devel-269238e.zip`, SHA256 `0545b1b24817cc0ed4a9e4fc440a7080cbaf69a9ce5d1e4bb22b0e697129c223` verificado no GitHub Actions 43021930151. O pacote possui `meta.json` com `libraryName=vulkan.radeon.so`, `NOTICE.txt` e biblioteca ELF64 AArch64. ZIP CRC PASS; a biblioteca **não foi executada**. Autor declara suporte Xclipse 940, mas não houve teste deste driver no Galaxy S24 FE ou NFSMW.
- PRÉ-RELEASE mais recente encontrada: v1.9.0-RC1 de 2026-10-28, explicitamente EXPERIMENTAL; não escolhemos a RC como base.
- CÓDIGO FONTE UPSTREAM FIXADO: `victorgbd/NFSMW-Recompiled-Mobile` revisão `0b3b3be1f700e2227c03b557dc33e9e50a56c6cc`.
  - `Drivers.java` lê `meta.json` e `libraryName` e aceita biblioteca pelo nome, sem impor `libvulkan_freedreno.so` na **importação**.
  - `Ajustes.java::argumentosDriver` passa `--android_gpu_driver_dir` e `--android_gpu_driver_name` quando um driver customizado está selecionado.
  - `d.esTurnip() && turbo()` só restringe o controle de turbo KGSL, não a seleção da biblioteca; não ativar opções turbo no Xclipse.
  - `tools/parche_turnip.py` aplica `adrenotools_open_libvulkan(... ADRENOTOOLS_DRIVER_CUSTOM ...)` se `REX_HAS_ADRENOTOOLS` estiver compilado. Ao falhar, retorna ao carregador Vulkan do sistema e registra warning. Isto é **caminho de FONTE UPSTREAM**, não teste do ELF V51 assinado.
  - A chamada `adrenotools_set_turbo(...)` existe no patch upstream, inclusive no caso false; não alterar esses switches sem auditoria. Nenhuma chamada `setprop` ou alteração térmica foi solicitada neste diagnóstico.
- GATE 1 de pacote upstream: GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43021930151, `completed/success`. Valida pacote fixado, ELF, nomes de campos e source anchors. **Não** valida compatibilidade nativa Vulkan, capacidade de carregamento na APK V51 ou efeito na fluidez.
- GATE 2 de observação Termux: `automation/termux/nfsmw_pre691_vulkan_driver_readonly_probe.sh`; GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43022295898, `completed/success`, ADB simulado (um dispositivo, falha segura para múltiplos/modelo diferente). Não foi executado em telefone real. O script obtém versão instalada e nomes do vendor ICD, mas **NÃO consegue provar qual driver a app usa**.
- Não confundir importador de driver do upstream com compatibilidade/execução comprovada na V51. Também não concluir que a v1.9.0-RC1 melhora FPS: RC experimental e nenhuma medição no jogo.

## Próximo gate: V51 instalada e compatibilidade do loader
1. Rodar o probe ADB somente leitura no Galaxy via Termux e coletar seu relatório `NFSMW_PRE691_VULKAN_ENV_*.txt`.
2. Auditar a APK V51 **real**, sem publicar o binário nem logs privados: confirmar presença de `Drivers`, dos argumentos `--android_gpu_driver_name`, biblioteca(s) de importação/adrenotools, e documentação/execução do loader. Strings em DEX/ELF indicam candidatos estáticos, não execução.
3. Se e apenas se o gate de importador passar e houver rollback claro para `sistema`: considerar ensaio temporário A/B **com a v1.8.0 estável**, mesmas preferências, 1920x1080, cap 60 observado, efeitos integrais, sem turbo/tweaks térmicos, logs privados e PRE690 SurfaceFlinger emparelhados. Não reproduzir o teste com RC1 primeiro.
4. Se o importador faltar na V51, NÃO fazer patch às cegas. Preparar plano de código reversível com fonte autenticada e eventual versão >51 assinada pela chave permanente; antes de qualquer build, checar status atual de C3/PG-9076/BMW/Nitro e preservar todos os artefatos.

STATUS: PRE691_REAL_PHASE_AUDIT_PASS; RADV_V1_8_STATIC_ARCHIVE_PASS; UPSTREAM_GENERIC_IMPORT_PATH_FOUND; V51_LOADER_NOT_VERIFIED; PRE691_ADB_SYNTHETIC_PASS; REAL_DEVICE_DRIVER_PROBE_PENDING; NO_NEW_APK; NO_FPS_GAIN_PROVEN.
