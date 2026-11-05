#!/data/data/com.termux/files/usr/bin/bash
# NFSMW PRE166/V33: coletor de TimeStats por camada, Vulkan/termica, sem rebuild.
# ATENCAO: -clear/-enable e -disable alteram TEMPORARIAMENTE o estado GLOBAL dos
# contadores de diagnostico SurfaceFlinger; nao mexem em graficos/VSYNC/thermal.
set -u
DURATION="${1:-240}"
INTERVAL="${2:-20}"
case "$DURATION" in ''|*[!0-9]*) echo 'Duracao invalida' >&2; exit 2;; esac
case "$INTERVAL" in ''|*[!0-9]*) echo 'Intervalo invalido' >&2; exit 2;; esac
if ((DURATION < 60 || DURATION > 600 || INTERVAL < 10 || INTERVAL > 60 || DURATION % INTERVAL != 0)); then
  echo 'Use duracao 60..600s, intervalo 10..60s, divisivel.' >&2
  exit 2
fi
RISH="$HOME/rish"
if [[ ! -f "$RISH" ]]; then
  echo "Nao encontrei $RISH (Shizuku/rish)" >&2
  exit 3
fi

# Todas as expansoes de dados pessoais ficam no shell Android, nao no Bash local.
# Apenas valores numéricos ja validados entram no codigo remoto.
REMOTE=$(cat <<'ANDROID_SH'
set -u
umask 077
PKG='io.github.nfsmwrecomp'
STAMP="$(date +%Y%m%d_%H%M%S)_$$"
FILE="/sdcard/Download/nfsmw_pre166_v33_surfaceflinger_${STAMP}.txt"
if ! ( set -C; : > "$FILE" ) 2>/dev/null; then
  echo 'PRE166_ERRO: shell sem escrita em /sdcard/Download; nada iniciado'
  exit 20
fi

SF_ACTIVE=0
cleanup() {
  if [ "$SF_ACTIVE" = '1' ]; then
    # Alteracao diagnosticada, reversao sempre tentada na saida normal/sinal.
    dumpsys SurfaceFlinger --timestats -disable >/dev/null 2>&1 || true
    echo 'SF_TIMESTATS_DISABLE_TENTADO=1'
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

capture() {
  echo '=== NFSMW PRE166 SURFACEFLINGER + VULKAN/THERMAL ==='
  echo 'MODO=DIAGNOSTICO; sem alteracao em FPS/graficos/sincronizacao/release'
  echo 'SF_GLOBAL_COUNTERS=clear_enable_temporario_com_disable_no_fim'
  echo 'AVISO=nao iniciar em paralelo com outro perfilador SurfaceFlinger'
  printf 'START_LOCAL=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
  printf 'DURACAO_SOLICITADA_S=%s INTERVALO_S=%s\n' "$DURATION" "$INTERVAL"
  UID_NOW=$(id -u 2>/dev/null || echo indisponivel)
  printf 'UID_SHELL=%s\n' "$UID_NOW"
  [ "$UID_NOW" = '2000' ] || { echo 'ABORTADO_UID_DIFERENTE_2000'; return 10; }
  VERSION=$(dumpsys package "$PKG" 2>/dev/null | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)
  printf 'VERSION_CODE=%s\n' "${VERSION:-indisponivel}"
  [ "$VERSION" = '33' ] || { echo 'ABORTADO_VERSION_DIFERENTE_33'; return 11; }

  # Mesma entrada de diagnostico confirmada no PRE148/PRE149, sem persistir TOML.
  echo '=== START_GAME ==='
  START_GAME=$(am start -W -n "$PKG/.SetupActivity" --ez nfsmw.banco true --esa nfsmw.args --present_perfil_pintado 2>&1)
  START_RC=$?
  printf '%s\n' "$START_GAME"
  printf 'AM_START_RC=%s\n' "$START_RC"
  if [ "$START_RC" -ne 0 ]; then echo 'ABORTADO_LAUNCH'; return 12; fi
  case "$START_GAME" in *'Error:'*|*'Exception'*|*'Status: timeout'*) echo 'ABORTADO_LAUNCH'; return 12;; esac
  echo 'GAME_LAUNCH=INTENT_ENVIADO_NAO_PROVA_JOGABILIDADE'

  echo '=== SURFACEFLINGER_LISTA_CAMADAS_DO_JOGO ==='
  # A lista pode estar vazia no primeiro instante da abertura.
  LAYERS=$(dumpsys SurfaceFlinger --list 2>&1)
  printf '%s\n' "$LAYERS" | grep -F "$PKG" || echo 'CAMADA_JOGO_AINDA_NAO_ENCONTRADA'

  echo '=== SF_TIMESTATS_ENABLE ==='
  SF_ENABLE_OUT=$(dumpsys SurfaceFlinger --timestats -clear -enable 2>&1)
  SF_ENABLE_RC=$?
  printf 'ENABLE_RC=%s\n' "$SF_ENABLE_RC"
  if [ "$SF_ENABLE_RC" -ne 0 ]; then
    printf 'ENABLE_OUT=%s\n' "$SF_ENABLE_OUT"
    echo 'ABORTADO_SEM_PERMISSAO_TIMESTATS'
    return 13
  fi
  case "$SF_ENABLE_OUT" in *'Permission Denial'*|*'Unknown option'*|*'permission denied'*)
    echo 'ABORTADO_TIMESTATS_NAO_SUPORTADO'; return 13;; esac
  SF_ACTIVE=1
  echo 'SF_TIMESTATS=HABILITADO_TEMPORARIAMENTE'
  START_EPOCH=$(date +%s)
  printf 'START_MONITOR_EPOCH=%s\n' "$START_EPOCH"
  I=0
  SAMPLES=$((DURATION / INTERVAL))
  while [ "$I" -lt "$SAMPLES" ]; do
    sleep "$INTERVAL"
    I=$((I + 1))
    printf '\n=== SAMPLE %s ===\n' "$I"
    printf 'SAMPLE_EPOCH=%s SAMPLE_LOCAL=%s\n' "$(date +%s)" "$(date '+%Y-%m-%d %H:%M:%S %z')"
    echo '--- SF_TIMESTATS_GAME_LAYER ---'
    # Captura pontual somente de secao pertencente ao pacote, nao de outros apps.
    SF_DUMP=$(dumpsys SurfaceFlinger --timestats -dump 2>&1)
    SF_DUMP_RC=$?
    printf 'SF_DUMP_RC=%s\n' "$SF_DUMP_RC"
    if [ "$SF_DUMP_RC" -eq 0 ]; then
      printf '%s\n' "$SF_DUMP" | awk -v pkg="$PKG" '
        /layerName[[:space:]]*=/ {
           found=(index($0,pkg)>0); if(found){count++; print $0}; next
        }
        found && (/totalFrames[[:space:]]*=/ || /averageFPS[[:space:]]*=/ || /presentToPresent/ || /^[[:space:]]*[0-9]+ms=/) { print }
        END {if(count==0)print "SF_LAYER_METRICS=NO_MATCH"}
      '
    else
      echo 'SF_LAYER_METRICS=DUMP_FAILED'
    fi
    echo '--- THERMAL_STATUS ---'
    THERMAL=$(dumpsys thermalservice 2>&1)
    printf '%s\n' "$THERMAL" | grep -m1 '^Thermal Status:' || echo 'THERMAL_STATUS=indisponivel'
    printf '%s\n' "$THERMAL" | awk '
      /^Current temperatures from HAL:/ {hal=1; next}
      hal && (/^Temperature static thresholds/ || /^Temperature headroom/) {exit}
      hal && /Temperature\{.*mName=(SKIN|BAT|AP),/ {print}
    '
    echo '--- GPU_DEVFREQ_INSTANTANEO ---'
    for NODE in /sys/class/devfreq/*sgpu /sys/class/devfreq/*gpu; do
      [ -d "$NODE" ] || continue
      printf 'GPU_NODE=%s ' "$NODE"
      for KEY in cur_freq min_freq max_freq; do
        VALUE='NA'
        [ ! -r "$NODE/$KEY" ] || VALUE=$(cat "$NODE/$KEY" 2>/dev/null || echo NA)
        printf '%s=%s ' "$KEY" "$VALUE"
      done
      printf '\n'
    done
    echo '--- BATTERY_ATUAL ---'
    dumpsys battery 2>&1 | grep -E '^[[:space:]]*(temperature|level|status):' | head -n 5 || true
  done
  printf 'END_MONITOR_EPOCH=%s\n' "$(date +%s)"
  echo 'STATUS_FINAL=COLETA_ENCERRADA'
}

# Grava resultados em arquivo do Android, evitando misturar stdout/stderr rish.
capture > "$FILE" 2>&1
RC=$?
# Desabilitar explicitamente AQUI para registrar no arquivo antes de retornar.
if [ "$SF_ACTIVE" = '1' ]; then
  dumpsys SurfaceFlinger --timestats -disable >/dev/null 2>&1 || true
  SF_ACTIVE=0
  printf 'SF_TIMESTATS_DISABLE_TENTADO=1\n' >> "$FILE"
fi
printf 'REMOTE_RC=%s\n' "$RC" >> "$FILE"
printf 'PRE166_RESULT_FILE=%s\n' "$FILE"
printf 'PRE166_EXIT_CODE=%s\n' "$RC"
exit "$RC"
ANDROID_SH
)
REMOTE="DURATION=$DURATION; INTERVAL=$INTERVAL
$REMOTE"
# Uma unica chamada rish; final sempre imprime caminho do arquivo, se permitido.
sh "$RISH" -c "$REMOTE"
