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


## PRE691B — evidência real de ambiente e loader da APK V51 (2026-11-11)

**Relatório enviado pelo usuário e arquivado no Drive:** `NFSMW_PRE691_VULKAN_ENV_20261111_095541.txt`, 505 bytes, SHA256 `09cb89e2c03b79d89229dadb660d6acc0fee96ab9af557780db484cb276bf54d`; Drive ID `1QpL0G2J9c3qIFHVmvJavrwK8C4MnmO70`, pasta `06_Logs_e_Medicoes`, [abrir](https://drive.google.com/file/d/1QpL0G2J9c3qIFHVmvJavrwK8C4MnmO70/view). Readback de 505 bytes igual à saída original.

- `PACKAGE=io.github.nfsmwrecomp`, `DEVICE_MODEL=SM-S721B`, `PACKAGE_VERSION_CODE=51`, `V51_VERSION_MATCH=TRUE`, `ANDROID_SDK=37`.
- `PROP_ro.hardware.vulkan=samsung`, `PROP_ro.hardware.egl=samsung`, `PROP_ro.board.platform=erd9945`, `PROP_ro.gfx.driver.0=UNSET`; módulo listado: `/vendor/lib64/hw/vulkan.samsung.so`.
- **Limitação:** propriedades e módulo instalado **não determinam** se o jogo carregou o driver Samsung ou uma biblioteca customizada em execução. O coletor omitiu PID, não inspecionou mapas de processo e não alterou propriedades ou APK.

**APK V51 real arquivada, verificada localmente, sem publicar seu conteúdo:** `NFSMW_V51_PRE652_GPU_SHADER_PASS_FREQUENCY_DIAGNOSTIC.apk`, 47.104.417 bytes, SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`, CRC ZIP sem erros.

- `classes.dex` (8.680.496 bytes) contém marcadores `Lio/github/nfsmwrecomp/Drivers;`, `gpu_drivers`, `libraryName`, `--android_gpu_driver_dir=`, `--android_gpu_driver_name=`.
- A biblioteca real `lib/arm64-v8a/librexruntime.so` (9.098.232 bytes) exporta o símbolo ELF AArch64 **`adrenotools_open_libvulkan`** (observado com `readelf --dyn-syms --wide`). Também contém `adrenotools_set_turbo`, argumentos de seleção customizada e mensagens de sucesso/fallback do carregador Vulkan. `libmain.so` e `libmain_usa.so` contêm termos relacionados a adrenotools; não presumir que o código do driver esteja implementado neles.
- **Limites:** presença de classe/argumentos/símbolo e mensagens na APK não demonstra que a biblioteca customizada é carregada com sucesso na Xclipse 940, que a APK *instalada no dispositivo* é byte a byte idêntica à V51 arquivada, ou que o RADV melhora FPS, mantém todos os efeitos ou seja estável.

**Nova checagem de identidade instalada (sem root, download ou upload da APK):** script público `automation/termux/nfsmw_pre691_installed_apk_identity_readonly.sh`, obtém `base.apk` via `pm path` e lê apenas SHA256 usando `adb shell sha256sum`. Compara com o hash V51 arquivado e ABORTA em incompatibilidade. GitHub Actions sintético [43025444456](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43025444456), job `130538881991`, status `completed/success`, `PRE691_INSTALLED_APK_SHA_MOCK_AND_FAIL_CLOSED=PASS`. Falhas simuladas para múltiplos dispositivos, modelo errado, versionCode diferente e hash divergente; **nenhum dispositivo real nesse gate**.

**Próximo passo:** rodar o coletor de hash no Galaxy, confirmar `PRE691_INSTALLED_V51_BINARY_IDENTITY=PASS` e então documentar eventual ensaio A/B RADV v1.8.0 somente mediante segurança de rollback para driver `sistema`. Evitar ativar turbo KGSL, alterações térmicas, root, mods no OS ou alterar fidelidade gráfica; verificar carregamento efetivo por log e comparar com baseline PRE690. Em qualquer falha, manter Samsung. Sem APK nova, sem prova de ganho de FPS.

Status PRE691B: REAL_ANDROID_ENV_READONLY_PASS; PRIVATE_DRIVE_LOG_SAVED_READBACK_PASS; STORED_V51_APK_SHA_CRC_PASS; V51_DEX_DRIVER_IMPORT_ANCHORS_FOUND; REXRUNTIME_ADRENOTOOLS_SYMBOL_VERIFIED; INSTALLED_APK_SHA_GATE_PENDING; RADV_RUNTIME_NOT_TESTED; NO_NEW_APK; NO_FPS_GAIN.


## PRE691C — identidade da APK instalada verificada em hardware real (2026-11-11)

- O usuario executou `automation/termux/nfsmw_pre691_installed_apk_identity_readonly.sh` no Galaxy S24 FE SM-S721B. Arquivo privado `NFSMW_PRE691_INSTALLED_APK_IDENTITY_20261111_101620.txt`: 389 bytes, SHA256 **`dc46058262e64a4caaa2505abecde0ffcbe16ac71cf0bc0fb2fa0613066464f4`**. Conferidos `PACKAGE_VERSION_CODE=51`, `PACKAGE=io.github.nfsmwrecomp`, `EXPECTED_BASE_APK_SHA256` e `INSTALLED_BASE_APK_SHA256`, ambos idênticos a `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`.
- Resultado **`PRE691_INSTALLED_V51_BINARY_IDENTITY=PASS`**, portanto a APK V51 real instalada é byte a byte idêntica à V51 arquivada e auditada estaticamente, sem precisar copiar o binário do aparelho. Evidência no Google Drive `06_Logs_e_Medicoes`: [NFSMW_PRE691_INSTALLED_APK_IDENTITY_20261111_101620.txt](https://drive.google.com/file/d/1nDmZEFdOGyZ9_m0g7yonWuvuzfxqkEMi/view), ID `1nDmZEFdOGyZ9_m0g7yonWuvuzfxqkEMi`. Upload verificado pelo Google Drive (389 bytes), readback confirmou as duas linhas SHA e resultado PASS.
- A identidade correlaciona a instalação com a auditoria estática da classe `Drivers`, argumentos `--android_gpu_driver_name` e `librexruntime.so` exportando `adrenotools_open_libvulkan`. Ela **não demonstra** que o driver alternativo é carregado com sucesso pelo VulkanPresenter nem que qualquer jogo seja estável ou mais rápido sob RADV.
- Fonte de interface upstream fixada `victorgbd/NFSMW-Recompiled-Mobile` commit `0b3b3be1f700e2227c03b557dc33e9e50a56c6cc`: `SetupActivity.java` seção Rendimento possui `Importar driver` (ACTION_OPEN_DOCUMENT, application/zip), opção `Driver do sistema` em RadioGroup e botão `Probar Vulkan` na seção Avançado. `Drivers.importar()` lê `meta.json/libraryName`; ao importar, `ajustes.driver(d.nombre)` escolhe automaticamente o driver importado; `Ajustes.argumentosDriver()` informa nome e pasta ao loader. Confirmar rótulos/localização atuais na interface V51, pois source upstream não é equivalência exata do DEX.
- **Próximo gate opcional RADV A/B:** preservar preferências de qualidade, salvar cópia de saves antes dos testes, capturar baseline Samsung separado, baixar somente `radv-xclipse-27.0.0-devel-269238e.zip` da release oficial **v1.8.0 estável**; não usar RC1 nem Wayland. Importar pelo menu do jogo, verificar o nome `vulkan.radeon.so`, começar com sonda Vulkan, procurar log explícito de carregamento `Vulkan: driver propio cargado con adrenotools:` e não aceitar fallback `Se usa el driver del sistema.` como evidência de RADV. Só prosseguir ao gameplay se o teste abrir corretamente e sem regressão visual. Voltar a `Driver do sistema` pela seleção do app sem desinstalar ou limpar dados.
- Para comparação objetiva, manter 1920x1080 e exatamente as opções efetivas, cap de FPS e condição térmica, colher `nfsmw.log` e apresentação ordenada PRE690 em ambos os drivers com sessão pareada e mesmo trecho estável. Não desabilitar efeitos/shaders/física, não tocar em governor térmico/props/clock/turbo, não alterar assinatura, Android, driver do sistema ou instalar APK nova.
- Limite específico: RADV Xclipse v1.8.0 converte BCn com potenciais diferenças de precisão/qualidade e pode falhar, travar ou produzir imagens distintas. Não declarar fidelidade equivalência nem ganho FPS até imagens e métricas em execução serem confrontadas.

Status PRE691C: INSTALLED_V51_SHA_MATCH_VERIFIED; PRIVATE_EVIDENCE_DRIVE_READBACK_PASS; V51_CUSTOM_DRIVER_LOADER_STATICALLY_PRESENT; RADV_DEVICE_LOAD_NOT_TESTED; NO_NEW_APK; NO_PROVEN_FPS_GAIN.


## PRE691D — RADV Xclipse v1.8.0 realmente carregado na V51 do Galaxy S24 FE (2026-11-11)

**Evidência de hardware real (log privado, não republicado aqui):**
- Arquivo `nfsmw.log` enviado pelo usuário em 2026-11-11, 56.943 bytes, 419 linhas, SHA256 `b8d514ba1c0a4e061ff412498a0483a3b8a52f289d7483195a59d32545118db7`. Preservado em `NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE691_RADV_V1_8_FIRST_RUNTIME_NFSMW_20261111_102846.log` (Drive ID `18wagTnevFsS3OrmdW5zUja58LCuY-mhi`). Upload confirmado e leitura de volta de 56.943 bytes / 419 linhas com os mesmos marcadores.
- O próprio runtime informou: `Vulkan: driver propio cargado con adrenotools:` seguido de biblioteca **`vulkan.radeon.so`** sob diretório privado do aplicativo `gpu_drivers/RADV_Xclipse_Mesa_27.0.0-devel-269238e_`.
- O dispositivo Vulkan utilizado aparece como `AMD Radeon Graphics (RADV MAGELLAN CARL)`, `driverID: MesaRadv`, `driverName: radv`, `driverInfo: Mesa 27.0.0-devel (git-269238e853)`, `VK_KHR_swapchain` habilitada. Evidência forte de que o RADV Xclipse **v1.8.0 foi realmente carregado e inicializado**, e **não** fallback silencioso para o Samsung nesta tentativa.
- `VulkanPresenter: Created 1920x1080 swapchain`, `MAILBOX`, quatro imagens solicitadas. Game render nativo iniciou; houve atividade C2/C3/C6 e pré-aquecimento C6 `145 de 145 pipelines precalentados`, sendo 91 compilados e **0 falhos**.
- Um único `VK_ERROR_INCOMPATIBLE_DRIVER` foi emitido durante sondagem de `/dev/dri/renderD129` sem AMDGPU / permission denied **ANTES** da identificação bem-sucedida da GPU RADV. Não afirmar que essa mensagem foi fatal, visto que o Vulkan device e swapchain surgiram após ela. Também não afirmar que não exista outro problema em tempo de jogo.
- O log tem 323 linhas `info` e 96 linhas `warning` (dentre elas avisos de caminhos virtuais `D:\...` indisponíveis), **zero `[error]` e zero `[fatal]`**. Mensagens sobre arquivos ausentes por si sós não comprovam corrupção, embora possam requerer análise se surgirem sintomas.
- Cobertura temporal **somente 5,384 s**: 10:28:46.624 a 10:28:52.008. O último evento é XInput, não uma mensagem de shutdown ou erro. **Não foi comprovado** que o jogo continuou além desse ponto, que entrou em gameplay estável, que a qualidade visual é equivalente nem que houve ganho de FPS. Sem `PRE648 GPU_SHADER10s` neste trecho, como esperado numa janela tão curta.
- Parâmetro registrado: resolução interna 1920x1080 e limite efetivo 60 FPS (com modo de vídeo guest 1280x720). A resolução interna e o modo guest são campos distintos; o log não autoriza concluir redução de resolução interna.

### Próximo gate
1. Confirmar observação do usuário: o app fechou sozinho após ~5s ou o log foi copiado antes de uma execução mais longa? Não declarar crash até testemunho/logcat.
2. Se o app permaneceu aberto: sessão controlada de gameplay 90–120 s sob RADV v1.8.0, sem mudar configurações gráficas, registrar `nfsmw.log` com `PRE648 GPU_SHADER10s` e `C2`; coletar PRE690 ordered SurfaceFlinger sob RADV e comparar com baseline Samsung no mesmo trecho e mesmas condições. Observar fidelidade, shaders, sombras, blur e controles PG-9076.
3. Se houve fechamento/crash: evitar benchmark; coletar logcat de processo/fatal signal daquela sessão via ADB, sem root e sem mensagens de outras apps; voltar ao `Driver do sistema` no menu do NFSMW. Investigar causa antes de outro ensaio.
4. Não atribuir melhora ou piora à RADV enquanto não existirem medições de timestamps emparelhadas, temperatura/clock e resultado visual. Não recompilar V51, não mudar assinatura/versionCode, não tocar em configs térmicas ou driver global do Android.

**Status PRE691D: ACTUAL_RADV_V1_8_LOADED=PASS; VULKAN_DEVICE_AND_SWAPCHAIN_CREATED=PASS; C6_PIPELINE_WARMUP_PASS; OBSERVATION_WINDOW_5S_ONLY; GAMEPLAY_STABILITY_UNKNOWN; RADV_VS_SAMSUNG_PACING_UNTESTED; NO_NEW_APK; NO_FPS_GAIN.**


## PRE691E — usuário confirma que o aplicativo permaneceu aberto (2026-11-11)

Após o primeiro log real de 5,38 segundos com RADV Xclipse v1.8.0, o usuário confirmou explicitamente: **"Permaneceu aberto"**. Essa observação refuta a hipótese de *fechamento imediato* na sessão inicial, mas **não** confirma gameplay de minutos, ausência de problemas gráficos ou estabilidade prolongada. O log continua cobrindo somente os cinco segundos registrados.

**Gate seguinte, somente diagnóstico:** repetir o coletor PRE690 `automation/termux/nfsmw_pre690_ordered_latency_adb.sh` com `preflight` e `arm 110 30` durante NFSMW V51 com RADV selecionado, preferencialmente carro parado no mesmo trecho do baseline Samsung. O coletor termina em arquivos `NFSMW_PRE690_CAPTURE_*.status.txt` e `NFSMW_PRE690_ORDERED_PRESENT_*.txt`, que devem acompanhar `nfsmw.log` da mesma sessão. `arm 110 30` faz uma pré-espera de 110s, escolhe camada SurfaceView ativa e lê 30 consultas de histórico ordenado, aproximadamente uma por segundo; não assumir janela exata de 30s. Não trocar o driver ou ajustes entre a captura e o log. Se falhar, não repetir às cegas: examinar status e log.

**Critérios de comparação:** ambas as sessões devem ter `DRIVER` comprovado no log, resolução interna 1920x1080, modo de apresentação, limite FPS, efeitos e trecho de cena equivalentes, com condição térmica semelhante. Computar distribuições, sequências consecutivas 8↔25ms e caudas por intervalo de 100ms da PRE690, sem inferir causa específica. O histórico SF pode ser parcial; não atribuir lacuna a travamento sem corroborar logcat e C2. Sem patch ou APK nova. `CONTEXTO_NFSMW.md` canônico ainda não recebeu esta atualização; este relatório registra a evidência verificada para sincronização posterior.

Status PRE691E: USER_CONFIRMED_APP_REMAINED_OPEN; DRIVER_LOAD_RUNTIME_VERIFIED; LONG_GAMEPLAY_PENDING; RADV_PACING_CAPTURE_PENDING; NO_NEW_APK; NO_FPS_GAIN_PROVEN.


## PRE691F — comparação A/B real dos timestamps Samsung × RADV (2026-11-11)

**Verificação dupla com o mesmo analisador** `pre691_triple_timestamp_phase_audit.py` sobre as duas capturas reais do Galaxy:
- Samsung PRE690: raw SHA256 `29f20955434bbcebc4b622995026b2ace00702d20245b57585e1fd6dd7f05dc7`, 30 amostras, 2335 triples únicos, 2333 intervalos contínuos, lacuna incerta 1115.961ms, cobertura 38.888066s, 59.993 fps estimados, intervalo médio 16.668695ms, desvio-padrão 3.945334ms, histograma arredondado 8=246, 9=11, 16=96, 17=1722, 25=256, 33=2, alternâncias 8↔25 = 290 (136 + 154).
- RADV v1.8.0 PRE691E: raw SHA256 `5fd11328ba20b338bd773bb61dcf550b702a6e0329ba9f825858bfbbd1dec174`, 30 amostras, 2323 triples únicos, 2321 intervalos contínuos, lacuna incerta 1049.723ms, cobertura 38.685168s, 59.997 fps estimados, intervalo médio 16.667457ms, desvio-padrão 3.654309ms, histograma 8=213, 9=7, 16=81, 17=1799, 25=220, 33=1, alternâncias 8↔25 = 250 (141 + 109).
- Diferenças **observadas, não causais**: RADV teve ~7.38% menor desvio-padrão e ~13.79% menos transições 8↔25 (sem considerar diferenças de cena/condição térmica). O deslocamento médio `actual_present - desired_present` aumentou ~0.649ms no RADV (19.001ms Samsung, 19.649ms RADV), o que **não** é latência de input demonstrada.
- `nfsmw.log` RADV contém **três inícios de processo** (10:28, 11:00, 11:10). A captura 11:13:57–11:14:36 pertence ao processo iniciado 11:10:29, com `driverName: radv`, resolução interna **1920x1080**, cap **60 FPS** e swapchain `MAILBOX`. Não confundir com a sessão temporária das 11:00 configurada em 120 FPS.
- Durante a janela: C2 Swaps 15-18ms 1169/1201 em 11:14:07 e 1181/1200 em 11:14:27; GPU real por Swap reportada 7.54 e 7.64 ms nestas janelas. Interno C2 mais regular que timestamps efetivos na SurfaceView.
- **Alerta independente C3:** na sessão RADV, `C3: hilo de enlaces de texturas APAGADO para el resto de la sesion` às 11:12:16.746, guard `NFSMW_PRE194_C3 copia_duplicada=true`, com fallback de criação na thread do anel. Isso ocorreu ANTES da captura e afeta sua comparabilidade. Também houve registro equivalente na sessão 11:00. Não reativar esse mecanismo nem aplicar patch sem auditar a árvore atual.
- **Watchdog:** houve episódios em que as threads guest pararam de avançar e depois retomaram, antes da janela (11:10–11:12) e depois dela (11:17–11:19); retomadas após 31, 11, 28, 24, 11 e 23s. Nenhuma nova declaração de watchdog na janela 11:13:57–11:14:36; o log termina durante outro episódio e não prova crash. A causa e a associação ao RADV permanecem NÃO demonstradas.
- Arquivos privados preservados em `NFSMW_Android/06_Logs_e_Medicoes`: status 517 bytes SHA256 `2b2c115e214a440b2519644ce34ecd55a143359ef84e5816d8df67c11aefa987` Drive ID `1ThmSU3pdi75XhTl3dHP6mVIQ8OmFbDXb`; raw 189548 bytes Drive ID `1x0CL8OEFsKA3nTdXqXQgLkKUCQvq9rvr`; `nfsmw.log` 1549711 bytes SHA256 `44d57cb808e86f828b40dc8ca161d30a772186ced56e478461135f0037b1943c` Drive ID `1RMjDqkzTu6mS9PnGXxXmKkruQS31MP-2`. Metadados de tamanho do Drive e readbacks textuais conferidos.
- Relatório reproduzível gerado e salvo no Drive: ZIP `NFSMW_PRE691F_RADV_SAMSUNG_AUDIT_REPORT_20261111.zip` ID `1_HvnA8z5hXPq6rKxRZAtsu60X_2PLyG-` (5122 bytes), e documento `NFSMW_PRE691F_REAL_RADV_VS_SAMSUNG_COMPARISON_20261111.md` ID `1pbdKalJGh-sT7vANkvPu02KsllH78r8M` (4062 bytes). Não publicou logs brutos no GitHub.

**Recomendação:** NÃO declarar aumento de FPS nem jitter resolvido. Investigar o desarme C3 e paralisações do guest; se estável, repetir amostras A/B/A com driver Samsung-RADV-Samsung, mesma cena, cap 60, 1920x1080, opções gráficas e condições térmicas. Manter APK V51, assinatura permanente, saves, controle e efeitos. `CONTEXTO_NFSMW.md` canônico ainda precisa de adendo; não foi alterado automaticamente.

Status PRE691F: REAL_RADV_CAPTURE_PASS; SAMSUNG_RADV_SAME_ANALYZER_PASS; SMALL_JITTER_REDUCTION_OBSERVED_NONCAUSAL; C3_FALLBACK_OBSERVED; GUEST_WATCHDOG_FREEZES_OBSERVED_OUTSIDE_CAPTURE; FPS_GAIN_UNPROVEN; NO_APK.
