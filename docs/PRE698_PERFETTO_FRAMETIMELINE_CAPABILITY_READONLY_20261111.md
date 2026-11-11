# PRE698 — viabilidade FrameTimeline/SurfaceFlinger no Galaxy S24 FE (somente leitura)

**Estado inicial, 2026-11-11:** protocolo e preflight criados; **ainda não executados no aparelho**. Não há trace de nova sessão e não há atribuição causal do frame pacing.

## Base técnica confirmada

- A PRE694 A/B/A real e PRE695 mostram `desiredPresent` próximo de 16,67 ms e variação adicional em `actualPresent`, com alternâncias próximas de 8/25 ms. A PRE697 autenticou duas diferenças lexicais pequenas e terminou `completed/success`, run [43102881692](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43102881692); não demonstrou causa.
- A V51 `io.github.nfsmwrecomp` está instalada e foi usada nas sessões reais anteriores; **não** se deve deduzir que continua no aparelho sem novo preflight.
- As três janelas SurfaceFlinger PRE694 e o analisador PRE695 são referência de apresentação **observacional**, não de fila Vulkan individual.
- O Perfetto documenta `perfetto --query --long` como consulta de estado do serviço, sem iniciar trace: https://perfetto.dev/docs/reference/perfetto-cli.
- A fonte `android.surfaceflinger.frametimeline` é descrita em https://perfetto.dev/docs/data-sources/frametimeline; essa documentação informa suporte Android 12+ e alerta que `SurfaceView` não tem suporte completo. **Não pressupor tokens de quadros do NFSMW presentes no FrameTimeline**.
- Exemplo de gravação Perfetto por CLI: https://perfetto.dev/docs/learning-more/android. **Não executar gravação ainda**.
- Não solicitar fonte `android.log` no preflight: documentação indica suporte condicionado a userdebug; não inferir disponibilidade no firmware Samsung de produção: https://perfetto.dev/docs/data-sources/android-log.

## Ferramentas preparadas

- [Preflight Termux/ADB](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/automation/termux/nfsmw_pre698_perfetto_preflight_readonly.sh): lê modelo, UID de shell, versionCode instalado, resposta do Perfetto e período da interface `dumpsys SurfaceFlinger --latency`. Não grava trace nem troca propriedade do Android.
- [Teste com ADB fictício](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/automation/kaggle/nfsmw_pre698_perfetto_preflight_synthetic.py): cobertura positiva/negativa para dados de fonte listados ou não listados, interface indisponível, versão 52 errada, modelo errado, UID diferente de shell e ausência de aparelho.
- [Workflow sintético](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre698-perfetto-readonly-preflight-synthetic.yml): apenas `bash -n`, `py_compile` e testes com mocks. Nenhuma credencial, APK ou dispositivo necessários.

## Instrução de campo (somente após pareamento ADB já válido)

Em Termux, com `adb devices` mostrando um único aparelho `device`, e sem recompilar a APK:

```bash
curl -fL https://raw.githubusercontent.com/Juniklx/nfsmw-actions-teste/main/automation/termux/nfsmw_pre698_perfetto_preflight_readonly.sh -o "$HOME/nfsmw_pre698_perfetto_preflight_readonly.sh"
bash -n "$HOME/nfsmw_pre698_perfetto_preflight_readonly.sh"
bash "$HOME/nfsmw_pre698_perfetto_preflight_readonly.sh" preflight | tee "$HOME/nfsmw_pre698_preflight.txt"
```

O resultado `PRE698_PREFLIGHT=PASS_READONLY_NO_TRACE` valida **somente pré-condições**, não FrameTimeline real. `FRAME_TIMELINE_SOURCE=ADVERTISED_NOT_RUNTIME_VALIDATED` significa que o serviço anuncia uma fonte, **não** que a timeline do NFSMW contenha tokens/frames. `NOT_LISTED_NOT_PROVEN_UNSUPPORTED` não comprova ausência definitiva; avaliar resposta e versão concreta da ferramenta.

Se o preflight falhar em modelo, UID, ADB ou versão, **não executar novos testes**, e conservar o relatório local para auditoria. Não usar root, Shizuku/Shevery para modificar térmica, mudança de `setprop`, instalação de APK, troca de driver, FPS cap ou gráficos.

## Critério para possível captura futura (PRE699, não aprovada nesta etapa)

Somente depois de confirmar o preflight em hardware real, desenhar **uma captura curta e explicitamente opt-in**, com configuração Perfetto documentada e coleta PRE690 sincronizada. Separar: (a) `desired/ready/actual` da `SurfaceView`; (b) FrameTimeline de compositor se o aparelho disponibilizar; (c) escalonamento/CPU, se autorizado; (d) telemetria interna do jogo, ainda sem correlação por ID comum. Cuidado: timestamps do Perfetto e `--latency` não representam automaticamente o mesmo clock nem o mesmo frame; validar antes de pareá-los.

**Não demonstrado:** suporte efetivo do FrameTimeline para quadros da `SurfaceView` do NFSMW, eventos por `vkQueuePresentKHR` ou fence, dados de GPU hardware, ganho de FPS, superioridade de driver ou causa do stutter.

**Preservar:** APK V51 `versionCode=51`, pacote `io.github.nfsmwrecomp`, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução interna 1920×1080, limite do teste 60 FPS (meta futura 120), shaders, efeitos, física, controles e proteções térmicas. Nenhum patch de código ativo aplicado pela PRE698.

## CI sintético verificado (adendo de 11/11/2026)

A execução [GitHub Actions 43117440370](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43117440370), job `130848948700`, foi consultada e terminou **completed/success**. Logs confirmam `PRE698_TEST_BASELINE=PASS`, `FT_NOT_LISTED=PASS`, `QUERY_UNAVAILABLE=PASS`, `LATENCY_UNAVAILABLE=PASS`, `WRONG_VERSION=PASS`, `WRONG_MODEL=PASS`, `WRONG_UID=PASS`, `NO_DEVICE=PASS` e `PRE698_SYNTHETIC_NO_REAL_DEVICE=TRUE`.

Isto valida **o script em condições simuladas**, não mede o telefone real. O preflight precisa ser executado via ADB já pareado para estabelecer a disponibilidade efetiva do serviço no S24 FE. Ainda não houve nova captura Perfetto nem V52; preservar a V51, seu certificado permanente e todas as configurações visuais/térmicas. O histórico principal CONTEXTO_NFSMW.md no Drive ainda requer adendo PRE697/PRE698.


---

## PRE698 REAL — preflight no SM-S721B (11/11/2026)

O usuário executou o script de preflight no Termux/ADB e compartilhou a seguinte saída observada. **Esta evidência foi fornecida no chat; ainda não há arquivo bruto desta nova execução no Drive**, e a sessão não deve ser confundida com uma medição Perfetto de quadros:

- SHA do script conferido no terminal: mensagem `o_preflight_readonly.sh: OK` (trecho exibido; hash do binário não foi recalculado remotamente neste registro).
- `PRE698_PERFETTO_BINARY=RESPONDING`;
- `PRE698_PREFLIGHT=PASS_READONLY_NO_TRACE`;
- `PRE698_MODEL=SM-S721B`;
- `PRE698_PACKAGE=io.github.nfsmwrecomp`, `PRE698_VERSION_CODE=51`;
- `PRE698_ADB_UID=2000`;
- `PRE698_PERFETTO_QUERY_COMPLETED=true`;
- `PRE698_FRAME_TIMELINE_SOURCE=ADVERTISED_NOT_RUNTIME_VALIDATED`;
- `PRE698_SURFACEFLINGER_LATENCY=PERIOD_READABLE`, `PRE698_DISPLAY_PERIOD_NS=8333333`;
- `PRE698_REAL_FRAME_TIMELINE_DATA=NOT_CAPTURED`;
- `PRE698_APP_TO_SURFACE_FRAME_MAPPING=UNVERIFIED`;
- `PRE698_GPU_QUEUE_AND_FENCE_TIMESTAMPS=NOT_MEASURED`;
- `PRE698_APK_OR_DEVICE_SETTINGS_MODIFIED=FALSE`, `PRE698_FPS_GAIN_PROVEN=FALSE`.

**Interpretação:** o binário e o serviço Perfetto respondem e anunciam a fonte `android.surfaceflinger.frametimeline`, porém os tokens do `SurfaceView` do NFSMW não foram observados; a documentação oficial avisa que `SurfaceView` não tem suporte completo neste contexto. A interface de `SurfaceFlinger --latency` continua legível a 120 Hz, sem que isso prove FPS real, latência de entrada ou sincronização por ID de frame.

**Próximo gate proposto, separado:** PRE699, uma única captura curta do FrameTimeline solicitada explicitamente por execução de comando do usuário, sem root, alteração de driver, APK, FPS cap, graphics, thermal ou saves. O trace é sistêmico e deve permanecer privado; avaliar arquivos e seu conteúdo antes de correlacionar com PRE690/PRE695.

**STATUS:** PRE698_SYNTHETIC_CI_PASS; PRE698_REAL_PREFLIGHT_PASS_USER_OUTPUT; FRAME_TIMELINE_SOURCE_ADVERTISED; NFSMW_FRAME_TIMELINE_RUNTIME_UNVERIFIED; NO_TRACE; NO_NEW_APK; NO_FPS_GAIN.
