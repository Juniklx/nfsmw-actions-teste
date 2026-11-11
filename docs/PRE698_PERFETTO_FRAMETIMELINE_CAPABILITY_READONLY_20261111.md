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
