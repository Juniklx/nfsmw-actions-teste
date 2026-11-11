# PRE690 — lista real de SurfaceViews do Galaxy S24 FE e correção do parser

Data do checkpoint: 2026-11-11.

## Evidência diretamente fornecida pelo usuário

O usuário executou uma captura `adb shell dumpsys SurfaceFlinger --list` durante o jogo, com `ADB_EXIT=0`, e informou três entradas relevantes:

- `RequestedLayerState{Background for <token> SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0#<id> parentId=...}`
- `RequestedLayerState{<token> SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0#<id> parentId=...}`
- `RequestedLayerState{<token> SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0(BLAST)#<id> parentId=...}`

Identificadores voláteis e demais nomes de janelas foram omitidos deste registro público. A saída real também contém `GameActivity`, `SetupActivity`, `VRI`, `ActivityRecord` e sinks de entrada que NÃO são superfícies candidatas.

O coletor anterior falhou com `PRE690_LAYER_LIST_SCHEMA_UNEXPECTED_ABORT=TRUE` / `PRE690_WORKER_EXIT_CODE=20`. A falha foi na extração do nome, antes da leitura ordenada ou do `--latency-clear`, não no próprio jogo. Em tentativa anterior, três consultas via nome inadequado retornaram timestamps 0, compatíveis com ausência de linha válida do `--latency`; não comprova 0 FPS nem falha na GPU.

## Explicação e correção

No AOSP, `RequestedLayerState::getDebugString()` imprime um wrapper com `name` seguido de ` parentId=` e demais propriedades. O nome pode incluir prefixo em hexadecimal + espaço + `SurfaceView[...]` e sufixo `#id`. `SurfaceFlinger --latency` compara o nome completo exato (`layer->getName()`).

Referências:
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/FrontEnd/RequestedLayerState.cpp
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/SurfaceFlinger.cpp
- https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/Layer.cpp

Alteração no script público `automation/termux/nfsmw_pre690_ordered_latency_adb.sh`, commit **b69169b3cdd08d8e71e6f79ef9a2ed2531cc0979**:
1. Mantém apenas linhas com SurfaceView do `GameActivity` deste pacote.
2. Remove o wrapper `RequestedLayerState{`, truncando os metadados apenas em ` parentId=`.
3. Ignora `Background for ...` (não é a camada emissora principal do jogo).
4. Valida por expressão regular tanto o nome com token hexadecimal quanto um nome sem prefixo; exige sufixo `#id`. Rejeita outras variações sem escolher uma camada arbitrária.
5. Continua exigindo **exatamente uma** camada com timestamp de apresentação avançando. Zero ou múltiplas continuam abortando sem gravar dados de FPS.
6. Continua sem chamadas Shevery/Shizuku/root e sem mexer no APK, código do jogo, assinatura, efeitos, resolução, limites térmicos ou refresh.

## Validação

O teste sintético do GitHub foi atualizado para emular o formato observado, com prefixos, camada background e nomes reais em `--latency` (commit **4509ea10fe0af625382d451dae0ec37ca9a50363**).

- GitHub Actions run **43007313656**, job **130477897873**, status `completed/success`, commit **0e25439c7754be9fc84e685b4bd5bdd9fa23ada5**.
- Log: `PRE690_SCRIPT_SYNTAX_AND_NO_SYSTEM_CHANGE=PASS`, `PRE690_SYNTHETIC_ROLLING_DEDUP=PASS`, `PRE690_SYNTHETIC_DOUBLE_LAYER_FAIL_CLOSED=PASS`, `PRE690_SYNTHETIC_THREE_LAYER_UNIQUELY_ACTIVE=PASS`.
- Teste de caso de uma camada ativa, duas avançando (rejeita) e três candidatas com uma avançando (aceita) concluídos.
- **Limitação:** mocks offline, não houve nova coleta com a versão corrigida no Galaxy.

## Próximo gate real

Baixar novamente o script, executar `bash -n`, `preflight` e `arm 110 30` após conferir ADB pareado. Abrir NFSMW, entrar no modo história, aguardar a primeira cinemática, manter carro parado e jogo no primeiro plano. Enviar `NFSMW_PRE690_CAPTURE_*.status.txt`, `NFSMW_PRE690_ORDERED_PRESENT_*.txt` caso exista, e `nfsmw.log` da mesma sessão. Se nenhuma camada avançar, diagnosticar `--latency` pela saída do ADB sem atribuir falha ao jogo.

Baseline preservada: APK V51 PRE652, `io.github.nfsmwrecomp`, versionCode 51, certificado SHA256 permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Sem ganho FPS demonstrado.

Status: REAL_LAYER_LIST_CAPTURED; PREVIOUS_SCHEMA_ABORT_CONFIRMED; PARSER_FIXED; SYNTHETIC_ACTIONS_PASS; REAL_RETEST_PENDING; NO_APK; NO_FPS_GAIN.
