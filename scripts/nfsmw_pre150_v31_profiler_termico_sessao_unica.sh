#!/usr/bin/env bash
# PRE150 — NFSMW V31; coleta passiva e pareada de Vulkan + telemetria Android.
# Requer Termux, Shizuku ativo e ~/rish. Nao modifica configuracoes do aparelho.
set -u

DURATION="${1:-300}"
INTERVAL="${2:-3}"
case "$DURATION" in ''|*[!0-9]*) echo 'Duracao deve ser um inteiro (segundos)' >&2; exit 2;; esac
case "$INTERVAL" in ''|*[!0-9]*) echo 'Intervalo deve ser um inteiro (segundos)' >&2; exit 2;; esac
if (( DURATION < 30 || DURATION > 1800 || INTERVAL < 1 || INTERVAL > 60 || INTERVAL > DURATION )); then
  echo 'Faixa permitida: duracao 30..1800 s, intervalo 1..60 s (<= duracao)' >&2
  exit 2
fi

RISH="$HOME/rish"
if [[ ! -f "$RISH" ]]; then
  echo "ERRO: nao encontrei $RISH; configure o Shizuku/rish antes de executar." >&2
  exit 3
fi

DEST="$HOME/storage/downloads"
if [[ ! -d "$DEST" || ! -w "$DEST" ]]; then
  DEST="$HOME"
fi
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$DEST/nfsmw_pre150_v31_profiler_termico_${STAMP}.txt"
ERR="$DEST/nfsmw_pre150_v31_profiler_erros_${STAMP}.txt"
umask 077

# Script executado pelo shell Android sob Shizuku, em UMA unica chamada ao rish.
# As duas variaveis interpoladas antes sao numericas e validadas acima.
REMOTE_SCRIPT=$(cat <<'ANDROID_SH'
set -u
PACKAGE='io.github.nfsmwrecomp'
printf '%s\n' '=== NFSMW PRE150 — V31, VULKAN + TERMICA, SESSAO UNICA ==='
printf 'data_android=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
printf 'duracao_s=%s intervalo_s=%s\n' "$DURATION" "$INTERVAL"
printf 'uid_rish=%s\n' "$(id -u 2>/dev/null || echo indisponivel)"
if [ "$(id -u 2>/dev/null)" != '2000' ]; then
  echo 'ABORTADO: Shizuku nao concedeu uid 2000 (shell).'
  exit 10
fi

VERSION_LINE=$(dumpsys package "$PACKAGE" 2>/dev/null | grep -m 1 -E 'versionCode=[0-9]+' || true)
VERSION=$(printf '%s\n' "$VERSION_LINE" | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)
printf 'pacote=%s versionCode=%s\n' "$PACKAGE" "${VERSION:-indisponivel}"
if [ "$VERSION" != '31' ]; then
  echo 'ABORTADO: versao divergente ou impossivel confirmar; nenhuma Activity iniciada.'
  exit 11
fi

INICIO_JOGO_EPOCH=$(date +%s)
printf 'INICIO_JOGO_EPOCH=%s\n' "$INICIO_JOGO_EPOCH"
echo '=== START GAME / PROFILER ==='
# Mesmo argumento confirmado pela PRE148, sem alterar TOML, modo de apresentacao ou FPS.
START_OUTPUT=$(am start -W -n "$PACKAGE/.SetupActivity" --ez nfsmw.banco true --esa nfsmw.args --present_perfil_pintado 2>&1)
START_STATUS=$?
printf '%s\n' "$START_OUTPUT"
printf 'am_start_exit=%s\n' "$START_STATUS"
if [ "$START_STATUS" -ne 0 ]; then
  echo 'ABORTADO: am start falhou; nao iniciar coleta como se o jogo estivesse ativo.'
  exit 12
fi
case "$START_OUTPUT" in
  *'Error:'*|*'Exception'*|*'Status: timeout'*)
    echo 'ABORTADO: erro ou timeout no launch.'; exit 12;;
esac
echo 'STATUS=INTENT_ENVIADO (nao prova que a jogabilidade iniciou)'

SAMPLE=0
ELAPSED=0
while [ "$ELAPSED" -lt "$DURATION" ]; do
  SAMPLE=$((SAMPLE + 1))
  printf '\n=== AMOSTRA %s ===\n' "$SAMPLE"
  printf 'epoch=%s local=%s decorrido_s=%s\n' "$(date +%s)" "$(date '+%Y-%m-%d %H:%M:%S %z')" "$ELAPSED"
  echo '--- THERMAL SERVICE ---'
  dumpsys thermalservice 2>&1 | grep -iE 'current thermal status|mstatus|throttling|temperature|value=|thermal status' | head -n 36 || true
  echo '--- GPU DEVFREQ ---'
  FOUND_GPU=0
  for GPU in /sys/class/devfreq/*; do
    case "$GPU" in
      *gpu*|*GPU*|*mali*|*sgpu*)
        [ -d "$GPU" ] || continue
        FOUND_GPU=1
        printf 'path=%s\n' "$GPU"
        for KEY in cur_freq min_freq max_freq available_frequencies; do
          if [ -r "$GPU/$KEY" ]; then
            printf '%s=' "$KEY"
            head -c 256 "$GPU/$KEY" 2>/dev/null || true
            printf '\n'
          else
            printf '%s=indisponivel\n' "$KEY"
          fi
        done
        ;;
    esac
  done
  if [ "$FOUND_GPU" -eq 0 ]; then echo 'GPU_DEVFREQ=nao_exposto_ao_shell'; fi
  echo '--- BATTERY ---'
  dumpsys battery 2>&1 | grep -iE 'temperature:|level:|status:' | head -n 8 || true
  REMAINING=$((DURATION - ELAPSED))
  if [ "$REMAINING" -lt "$INTERVAL" ]; then SLEEP_FOR="$REMAINING"; else SLEEP_FOR="$INTERVAL"; fi
  if [ "$SLEEP_FOR" -gt 0 ]; then sleep "$SLEEP_FOR"; fi
  ELAPSED=$((ELAPSED + SLEEP_FOR))
done
printf '\nFIM_MONITOR_EPOCH=%s\n' "$(date +%s)"
printf 'AMOSTRAS=%s\n' "$SAMPLE"

# Somente copia de arquivo de log externo, sem sobrescrever original ou saves.
SRC='/sdcard/Android/data/io.github.nfsmwrecomp/files/logs/nfsmw.log'
COPY_STAMP=$(date +%Y%m%d_%H%M%S)
DST="/sdcard/Download/nfsmw_pre150_v31_profiler_${COPY_STAMP}.log"
if [ -r "$SRC" ]; then
  if cp "$SRC" "$DST" 2>/dev/null; then
    printf 'LOG_COPIADO=%s\n' "$DST"
  else
    echo 'LOG_COPIADO=nao (acesso ou escrita indisponivel; enviar nfsmw.log manualmente)'
  fi
else
  echo 'LOG_COPIADO=nao (leitura externa indisponivel; enviar nfsmw.log manualmente)'
fi
printf '%s\n' 'STATUS_FINAL=COLETA_CONCLUIDA'
ANDROID_SH
)
REMOTE_SCRIPT="DURATION=$DURATION; INTERVAL=$INTERVAL
$REMOTE_SCRIPT"

{
  printf 'PRE150_LOCAL=%s\n' "$(date -Iseconds 2>/dev/null || date)"
  printf 'DURACAO=%s INTERVALO=%s\n' "$DURATION" "$INTERVAL"
  printf 'OBS=nao altera configuracoes, fonte, APK ou limites termicos\n'
  sh "$RISH" -c "$REMOTE_SCRIPT"
} > "$OUT" 2> "$ERR"
STATUS=$?
printf 'Relatorio: %s\n' "$OUT"
printf 'Erros: %s\n' "$ERR"
printf 'Codigo de saida: %s\n' "$STATUS"
if [[ "$STATUS" -ne 0 ]]; then
  printf 'Leia os dois arquivos e nao suponha que o monitoramento foi concluido.\n'
fi
exit "$STATUS"
