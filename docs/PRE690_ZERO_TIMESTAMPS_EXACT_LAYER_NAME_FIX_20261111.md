# PRE690 — timestamps zero em três camadas e correção de seleção (2026-11-11)

## Evidência recebida (texto do usuário, não arquivo bruto verificado)
```text
PRE690_MATCHING_NFSMW_LAYERS=3
PRE690_LAYER_1_BEFORE_ACTUAL_NS=0
PRE690_LAYER_2_BEFORE_ACTUAL_NS=0
PRE690_LAYER_3_BEFORE_ACTUAL_NS=0
PRE690_LAYER_1_AFTER_ACTUAL_NS=0
PRE690_LAYER_2_AFTER_ACTUAL_NS=0
PRE690_LAYER_3_AFTER_ACTUAL_NS=0
PRE690_ADVANCING_NFSMW_LAYERS=0
PRE690_LAYER_AMBIGUOUS_OR_INACTIVE_ABORT=TRUE
PRE690_WORKER_EXIT_CODE=20
```

O script abortou de forma segura antes de `--latency-clear` ou da captura de quadros. Valor 0 significa ausência de timestamp válido extraído, não 0 FPS do jogo. Não há prova de travamento.

## Hipótese técnica com base AOSP

Na versão de referência do AOSP, `SurfaceFlinger::listLayers` emite `layer->getDebugString()`, enquanto `SurfaceFlinger::dumpStats(--latency <name>)` compara `layer->getName() == name` por igualdade exata. `RequestedLayerState::getDebugString()` constrói `RequestedLayerState{NOME ...}`; portanto, transmitir a linha inteira de `--list` a `--latency` pode resultar apenas no período de refresh sem linhas de timestamps. Não foi verificado ainda que o firmware da Samsung devolva especificamente esse invólucro.

Fontes oficiais: 
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/android16-qpr2-release/services/surfaceflinger/SurfaceFlinger.cpp
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/FrontEnd/RequestedLayerState.cpp

## Correção e testes

- Commit de código `38d81bdb05dd01f2b894fe25e1cc99324601baa1`: o script `automation/termux/nfsmw_pre690_ordered_latency_adb.sh` extrai apenas o nome do NFSMW de um eventual invólucro `RequestedLayerState{...}` e falha de forma segura em formato inesperado. Continua exigindo uma só camada com timestamps avançando.
- Teste sintético atualizado para devolver linhas `RequestedLayerState{... parentId=778}` no `--list` e negar timestamps quando o nome completo de debug é usado por engano.
- GitHub Actions run `43001684832`, job `130459093993`, `completed/success`, commit `09321543121c6e4524ddee917fdf245c2bc6af8f`. Confirma parse sintético, rejeição quando duas camadas avançam, escolha quando apenas uma das três avança e análise offline; **não valida o firmware Samsung**.
- Nenhuma alteração na APK, fontes do jogo, assinatura, shaders, física, saves, PG-9076, limites térmicos ou refresh.

## Próximo teste

No Termux, baixar novamente o script, fazer `bash -n`, `preflight` e `arm 110 30` com ADB pareado. Manter NFSMW no foreground e carro parado durante a coleta. Enviar novo `NFSMW_PRE690_CAPTURE_*.status.txt`, `NFSMW_PRE690_ORDERED_PRESENT_*.txt` caso exista e `nfsmw.log` da mesma sessão. Se os três timestamps continuarem em zero, inspecionar `--list` e a resposta exata de `--latency` sem assumir automaticamente o tipo de falha.

Baseline V51 PRE652, pacote `io.github.nfsmwrecomp`, versionCode 51, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Sem ganho comprovado de FPS.

Status: REAL_DEVICE_ZERO_VALID_TIMESTAMPS; ROOT_CAUSE_HYPOTHESIS_AOSP_DEBUG_NAME_MISMATCH; CODE_FIXED; SYNTHETIC_GATE_PASS; REAL_RETEST_PENDING; NO_APK; NO_FPS_GAIN.
