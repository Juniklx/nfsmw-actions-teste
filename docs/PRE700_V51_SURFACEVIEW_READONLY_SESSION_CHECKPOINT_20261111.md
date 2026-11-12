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
