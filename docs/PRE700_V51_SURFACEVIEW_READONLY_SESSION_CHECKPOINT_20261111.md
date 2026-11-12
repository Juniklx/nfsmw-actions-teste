# PRE700 — SurfaceView V51: sessão de latência somente leitura

**Estado em 11/11/2026:** `PRE700_LOCAL_SYNTHETIC_PASS; PRE700_PHONE_CAPTURE_NOT_EXECUTED`.

## Motivação e distinção necessária

A PRE699 real auditou a fonte Perfetto FrameTimeline, mas só conseguiu vincular 673 quadros à janela Android `VRI-io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity`, **não** à `SurfaceView` em que o motor Vulkan do NFSMW apresenta o jogo. Esses eventos VRI não são prova de 120 FPS. [Relatório PRE699](PRE699_REAL_FRAMETIMELINE_READONLY_AUDIT_20261111.md).

A PRE700 reutiliza **exatamente o fluxo de captura de SurfaceFlinger da PRE690**, já empregado no teste real PRE694: `dumpsys SurfaceFlinger --list`, seleção da única `SurfaceView` do NFSMW com `actualPresent` avançando, `--latency-clear` só nessa camada e consultas `--latency` por 30 amostras de 1 s. O atraso após armar permanece **110 s**, como na PRE694, para o protocolo da primeira cinemática e carro parado. Não tenta correlacionar tokens FrameTimeline com quadros sem clock/ID comum.

## Artefato preparado e validado localmente

- Pacote privado persistente [NFSMW_PRE700_SF_READONLY_TOOLS_20261111.zip](https://drive.google.com/file/d/1f-RLf-9VBxW47uAOE2EtU80-cM-pxhuN/view), em `NFSMW_Android/06_Logs_e_Medicoes`, ZIP 3 arquivos, CRC local PASS, SHA256 `21b99d03330291f1454b36355fb0deb4cbcad2786915c124f573d1373c6c09b7`.
- Script `nfsmw_pre700_surfaceview_session_readonly.sh`: 6.553 bytes, SHA256 `276d2512ea29bb533ecbd3fa2234d1e5b447127d41386a4039165a9d5fd26391`. Disponibilizado também como arquivo individual na conversa.
- Suíte sintética offline `nfsmw_pre700_surfaceview_session_synthetic.py`: SHA256 `44cca2a25c10396d41a69f3bc7eb63a43651dd0cc6ff36b36f317e0d5816f01c`.
- README com pré-condições e comandos. Execução local `bash -n`, `py_compile` e **12 verificações sintéticas**: sintaxe, preflight positivo, versionCode errado, modelo errado, UID diferente de shell, arm, rejeição de arm duplicado, status, finish, rejeição de finish repetido, camadas ambíguas e amostras insuficientes. Todas passaram.
- Dependência existente: `automation/termux/nfsmw_pre690_ordered_latency_adb.sh`, blob Git `64eee262c286da9b218941130e7cf7684aeefb01` na revisão atual. Não foi modificado. O script PRE700 valida `bash -n` desse coletor, mas não verifica o hash; o usuário deve utilizar a cópia autenticada no projeto.

## Gate real pendente

No S24 FE com ADB já pareado e coletor PRE690 presente, guardar o script PRE700 em `~/storage/downloads/`, conferir SHA256 e executar `preflight`; depois `arm`, iniciar o modo história e deixar o carro parado após a primeira cinemática. Após o período da coleta, executar `status` e `finish`.

`finish` exige: versão V51, um alvo ADB UID 2000, modelo S24 FE, uma única camada avançando, status `PRE690_CAPTURE=RECORDED_UNANALYZED`, 30 amostras e pelo menos 25 janelas não vazias. O `PRE700_VALIDATED.txt` registra os hashes dos arquivos da sessão. **A aprovação desse arquivo é estrutural, não análise de FPS.**

Arquivos a fornecer da pasta `NFSMW_PRE700/PRE700_*:` manifesto, captura PRE690, status e validação PRE700, e `nfsmw.log` da mesma sessão quando disponível. Não salvar por padrão logs privados do jogo em repositório público.

## Limites

- Nenhuma APK V52, nova assinatura, rebuild, alteração de `MAILBOX`, driver, resolução interna 1920×1080, cap de teste 60 FPS, shaders/efeitos/física, controles touch/iPega, saves ou proteção térmica.
- `--latency-clear` limpa apenas o histórico de timing da SurfaceView selecionada, não altera renderização.
- Captura `desired/actual/ready`, não timestamps de `vkQueuePresentKHR`, submission, guest vblank, GPU nem fence.
- Ainda não houve teste real PRE700; não declarar causa das alternâncias 8↔25ms nem melhoria de FPS.

**Próxima decisão após dados reais:** reprocessar `actual` e `ready` da **mesma sessão**, validar driver/configuração pelo log, confrontar PRE694/PRE695 apenas como observação entre sessões. Sem instrumentação invasiva enquanto o custo/causa não estiver isolado.


---

## PRE700 REAL — resultados analisados (12/11/2026, 00:09–00:10 UTC−03)

O usuário anexou `nfsmw3.zip` (455.171 bytes, SHA256 `fc09b22f46d4ac74d8582bd09dd884c53b4f361b3d6fec3684ccc64b11636a18`) contendo `nfsmw.log`, captura PRE690, status e manifesto PRE700. **ZIP CRC PASS; SHA256 de manifesto/status/dados brutos coincidem** com `PRE700_VALIDATED.txt`. O arquivo original não foi publicado no GitHub.

- `PRE700_CAPTURE=PASS_STRUCTURAL_ONLY`; 30/30 consultas não vazias; duas camadas candidatas e **somente uma SurfaceView do jogo avançando**: `SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]`.
- Dados brutos: **3.642** linhas; após deduplicação de registros históricos reapresentados pelo SurfaceFlinger: **2.279** apresentações únicas, **1.363** linhas repetidas; **2.278** intervalos totais.
- Uma lacuna entre amostras iniciais de **999,482344ms** coincide com lacuna de `desired` (~999,73ms) e é tratada como **descontinuidade de cobertura**, não prova de travada do jogo. Excluindo esse salto: **2.277** intervalos que somam **37,955321s**, taxa **59,991589 apresentações/s**, mediana `actualPresent` **16,658555ms**, desvio padrão **3,976662ms**, p95 **25,023141ms**.
- Período da tela **8.333.333ns** (120Hz), versus limite da V51 **60FPS**. Intervalos `actualPresent` quantizados em ticks de display: **246×1**, **1.788×2**, **240×3**, **1×4**, **1×5**, **1×6**, mais a lacuna de 120 ticks. Transições diretas: **122** de 1→3 ticks e **146** de 3→1 (**268**), com eventos longos reais observados de **33,186836 / 41,632890 / 49,887344ms**.
- `desired` mediana **16,654238ms**, `ready` mediana **16,652168ms**; `ready−desired` mediana **0,369024ms** e `actualPresent−ready` mediana **18,549453ms**. Essas diferenças não isolam tempo exclusivo do SurfaceFlinger, GPU nem driver.
- `nfsmw.log` da mesma execução iniciou às **00:07:43,584**, com **1920×1080**, cap **60 FPS**, GPU Xclipse 940 e **SamsungProprietary**; após a cinemática `conduciendo` às **00:09:01,134**, antes da captura. Contadores C2: `presentados` avançou **1.200** em **20,002s** (00:09:44,399–00:10:04,401), cerca de **59,994 FPS**, `GPU real por Swap=8,80ms` na janela. O C2 não fornece ID de quadro cruzável com os timestamps `actualPresent`.

**Interpretação limitada:** pacing irregular medido na apresentação efetiva da SurfaceView, enquanto a produção/pacing desejado permanece predominantemente em 2 ticks; **sem causalidade confirmada** de GPU, Vulkan, MAILBOX, vblank ou SurfaceFlinger, sem comprovação de FPS ganho e sem correlação térmica/frequências.

Artefatos sanitizados, **sem logs brutos nem trace de outros processos**, salvos na pasta `NFSMW_Android/06_Logs_e_Medicoes`:
- [Relatório de análise PRE700](https://drive.google.com/file/d/1oRoyx0HsbNvsI-jhbQWbvDNZpXoG0bbR/view), Markdown 6.977 bytes, SHA256 `29a34777e0b2de84fcfa847ca47f4a6828cc0a68de3f26d7ac857f3278af033e`.
- [ZIP de relatório, JSON agregado e analisador reproduzível](https://drive.google.com/file/d/1XWtN2aoK3RgjIluZKRVkGJ0uHTiwzYap/view), 8.421 bytes, SHA256 `4522924b5eed34e9bf0979c2f0d8fdf5294245eb7d9c9c0d1c43272278ddac3f`, CRC PASS local e tamanho Drive confirmado.

**Próximo gate PRE701 (não executado):** projetar alinhamento por clock/IDs de quadros entre guest vblank, `vkQueuePresentKHR`, SurfaceFlinger `ready`/`actualPresent`. Validar viabilidade e overhead antes de qualquer instrumentação reversível; preservar assinatura, package, V51 e 1080p, efeitos, controles, saves e proteções térmicas. Nenhuma V52 autorizada/compilada.

**STATUS:** `PRE700_REAL_CAPTURE_PASS; SURFACEVIEW_FRAMES_VALIDATED; CAPPED_60_FPS; ACTUAL_PRESENT_JITTER_CONFIRMED; CAUSE_UNPROVEN; NO_FPS_GAIN; NEXT_PRE701_PROPOSED`.
