# NFSMW — PRE155 | Configuração efetiva V31 e desenho de repetição A/A

**Data de referência:** 2026-11-04 (horário de Bahia). **Resultado:** auditoria offline confirmada; **nenhuma APK, shader, configuração do telefone, assinatura, proteção térmica ou fonte C++ modificada**.

## 1. Materiais lidos e validação

1. APK `NFSMW_V31_PAL_USA_LOG_INFO_DIAG_EXPERIMENTAL.apk`, id Drive `1rpny5oKDfSmMElsHYGynESFzYMeFeAgc`: tamanho `47101449` bytes, SHA-256 `bf9a01f1c82c06f585385a0e2a547ffed77ce267b56eade1a7b20aa68cc46611`. `ZipFile.testzip()` não indicou erro. Não usar esse resultado como verificação criptográfica adicional da assinatura: o certificado permanente já foi conferido na PRE138.
2. Arquivo de configuração da própria APK `assets/nativo/nfsmw.toml`, SHA-256 `9602e9f7409eaab83b295521d00fecb95b04d629a8f7cea48911473f77a4f0d2`. Este é o **modelo empacotado**, não o TOML privado ativo no aparelho.
3. `nfsmw.log` completo da PRE153, SHA-256 `30715ef0f76367452f6128651a696627e0afb7420a46fcd94b64d21895d55d71`, Drive `1CtEjIIeIr0Jtor_8ZgLEHAT2qbaZsvaO`. A análise isolou **exclusivamente** a sessão `2026-11-04 21:12:49` até `21:17:13`, sem misturar sessões anteriores registradas no mesmo log; `3288` linhas válidas.
4. PRE152 `SurfaceFlinger`, SHA-256 `9a423721b1bc9ebf37909d1557bd7fb44e4e3cd8be45e1af77469ebaaf13548f`, Drive `1-P7UVO5bjJGFc0EAyUnd0DARZ1NSAGN6`; report PRE153 estruturado SHA-256 `42e79d0b54f5d85fb51b376b2fbeb5d3319d9e10c54a8a8864207c510ee03353`. Os SHA-256 dos logs brutos foram comparados com os previstos pela PRE153 e coincidiram. `VERSION_CODE=31` foi lido do TXT do aparelho.
5. Reprodutor `nfsmw_pre155_auditar_config_v31.py`, disponível no pacote ZIP de reprodutibilidade arquivado no Drive, sem pacotes de terceiros; o teste sintético `--self-test` foi aprovado localmente e o processamento dos arquivos reais foi executado offline. **Não houve execução de CI PRE155 independente no GitHub**: a tentativa de criar essa automação foi bloqueada por uma restrição da ferramenta. Os resultados foram registrados como relatório e artefato, não como validação independente em CI.

## 2. Valores empacotados versus os observados no jogo

| Tema | `nfsmw.toml` da APK V31 (padrão) | Log efetivo PRE153 | Interpretação |
|---|---|---|---|
| Resolução | `nfsmw_resolucion_interna = "1280x720"` | 1920x1080 | Resolução interna real confirmada pelo log e pela swapchain |
| Limite FPS | `nfsmw_limite_fps = "60"` | 120 | Limite informado pelo jogo, não FPS de tela medido |
| Modo de apresentação | Permissão padrão `vulkan_allow_present_mode_immediate = true` | Vulkan `MAILBOX` (enum 1) | **Não** concluir que IMMEDIATE é suportado, nem trocar modo |
| Thread de apresentação | `present_hilo_propio = false` | `desde el hilo del juego, presentando en el acto` | Log mostra último modo selecionado após transições de inicialização |
| Fence vazia / selagem | `present_refresco_sellado_perezoso = false` | **Não declarado no log** | Não inferir configuração privada efetiva |
| Perfilador de apresentação | `present_perfil_pintado = false` | 45 blocos do profiler presentes | Flag ativada temporariamente pela linha de inicialização PRE152 |

A linha `modo de video 1280x720 a 120.000000 Hz` é **modo virtual apresentado ao jogo**, não comprovação de a GPU estar renderizando a 720p nem prova da taxa física da tela. O mesmo início de sessão declara 1920×1080 real. O TOML dentro do APK diz que o arquivo é copiado para o armazenamento privado e uma cópia de usuário já existente pode ser preservada; o estado desta cópia privada não foi acessado. Não modificar nem apagar o arquivo do usuário para “testar o padrão”.

## 3. Identidade Vulkan e observações de apresentação

- GPU `Samsung Xclipse 940`, Vulkan API 1.3.304. `driverInfo` observado: `SPAL Driver version: 25.3.3, git hash: 9d9e5e5dc2`.
- `VulkanPresenter: Created 1920x1080 swapchain with format 37, color space 0, presentation mode 1 (MAILBOX), 4 images requested`: **uma criação** na sessão filtrada, não quatro imagens concedidas comprovadas.
- Foram registradas **3 transições** de modo de pintura na inicialização; o modo final foi `desde el hilo del juego, presentando en el acto (vsync implicito no, dibujantes de interfaz 0)`. A transição transitória para UI durante a inicialização não prova um modo alternado continuamente durante o teste.
- Extensões de dispositivo listadas como habilitadas: `VK_EXT_extended_dynamic_state3`, `VK_EXT_memory_budget`, `VK_KHR_swapchain`. Ausência de uma extensão nesse conjunto não demonstra que o driver seja incapaz de suportá-la.
- **VSync implícito do apresentador: `no`** conforme o log. Essa declaração **não é uma medida direta** de VSync/refresh físico do painel nem dispensa a sincronização obrigatória do Vulkan.
- O log não expõe uma lista de modos de apresentação suportados pelo driver, número de imagens efetivamente concedidas ou a totalidade das configurações privadas atuais.

## 4. Relação com a medição PRE153, sem extrapolação

- Superfície do jogo: FPS estimados por diferenças de `totalFrames` de **116.333** no intervalo máximo para **91.286** no último, não uma comparação de janelas idênticas.
- `SKIN` de **35.6 °C** para **44.5 °C**, status térmico Android de **0** para **2**. O aumento de custo de GPU por Swap foi confirmado na PRE154, mas não isola o fator térmico.
- `vkQueuePresentKHR` medido no lado CPU domina a função `PaintAndPresent`, **não o frame inteiro**. O valor não deve ser somado ao tempo `RefreshGuestOutput: depois` da instrumentação C2, pois há sobreposição.
- **Não foi encontrado fundamento suficiente para alterar** `present_hilo_propio`, `present_refresco_sellado_perezoso`, semáforos, fences, número de imagens, VSync, driver, clocks ou limites térmicos.

## 5. Protocolo PRE156 proposto: duas execuções A/A com a mesma V31

**Ainda não executado.** A/B exige alterar algum parâmetro; por enquanto **A/A é uma repetição de controle**, para estimar variação natural sem mexer no renderizador.

1. Manter a **V31 atual**, 1920×1080 e limite 120 FPS, sem reinstalar o app, sem alterar TOML ou shaders; Shizuku disponível, outros perfiladores SurfaceFlinger fechados.
2. Escolher a **mesma cena estável de direção livre**, com o mesmo veículo e posição/câmera, preferencialmente parado e sem alternar menus, cenas ou corridas durante a captura. Registrar qualquer alteração imprevista do cenário: o jogo tem tráfego/clima/ciclo visual que podem mudar.
3. Fazer captura A1 apenas depois de o aparelho ter resfriado **naturalmente**, observando no TXT o status térmico de partida e a temperatura SKIN. Executar exatamente o script PRE152 já distribuído: `bash ~/storage/downloads/nfsmw_pre152_v31_surfaceflinger_pareado.sh 240 20`.
4. Guardar o TXT e uma cópia identificada do `nfsmw.log` correspondente à sessão A1. Esperar resfriamento natural e condições de partida similares; **sem resfriamento artificial agressivo nem bypass térmico**. Executar A2 com o mesmo script, mesma cena e opções; guardar TXT + log A2, sem sobrescrever os arquivos da A1.
5. Comparar janelas correspondentes de 20–21 s: FPS apresentados por delta da `SurfaceView`, métricas C2 `GPU real por Swap` e carga da cena, tempos CPU de `vkQueuePresentKHR`, temperatura/thermal, devfreq. Comparar **formas das curvas** e dispersão A1↔A2 antes de inferir causalidade ou escolher patches.

**Limitações:** A/A sozinho não isola variação térmica da cena; não há medida sincronizada do modo físico da tela nem aprovação para alterações em apresentação. Se não houver cenários comparáveis, pedir somente a evidência faltante, não concluir que houve ganho. Não automatizar sessões adicionais sem necessidade se o aparelho esquentar.

## 6. Estado ao encerrar PRE155

PRE155 auditoria offline concluída; PRE156 proposta, teste físico pendente e opcional. **Nenhuma APK V32, otimização comprovada ou alteração do certificado permanente.** Preservar `versionCode=31` até justificativa técnica real; eventual release seguinte requer versionCode maior e a **mesma** assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
