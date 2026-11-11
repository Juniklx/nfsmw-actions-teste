#!/usr/bin/env bash
# PRE686 — SurfaceFlinger frame-present timing for the NFSMW Android process.
# Use with user's existing Shizuku/rish shell. Does not require root or modify APK.
set -euo pipefail

APP='io.github.nfsmwrecomp'
RISH="${NFSMW_RISH_PATH:-$HOME/rish}"
OUTPUT_DIR="${NFSMW_PRE686_OUTPUT_DIR:-$HOME/storage/downloads}"
[ -d "$OUTPUT_DIR" ] || OUTPUT_DIR="$HOME"
STATE_FILE="$HOME/.nfsmw_pre686_sf_started_at"

run_rish() {
    if [ ! -f "$RISH" ]; then
        printf 'PRE686_RISH_NOT_FOUND=%s\n' "$RISH" >&2
        return 3
    fi
    sh "$RISH" -c "$1"
}

usage() {
    printf '%s\n' 'Uso: bash nfsmw_pre686_surfaceflinger_timestats.sh start | stop | abort'
    printf '%s\n' 'start: zera e ativa os contadores globais temporarios do SurfaceFlinger.'
    printf '%s\n' 'stop: coleta somente a camada NFSMW e desativa os contadores.'
    printf '%s\n' 'abort: desativa os contadores sem coletar.'
}

case "${1:-}" in
start)
    run_rish 'id' >/dev/null
    run_rish 'dumpsys SurfaceFlinger --timestats -clear -enable' >/dev/null
    date '+%Y-%m-%dT%H:%M:%S%z' > "$STATE_FILE"
    printf 'PRE686_SF_TIMESTATS_CAPTURE_STARTED=TRUE\n'
    printf 'PRE686_SF_GLOBAL_COUNTERS_RESET=TRUE\n'
    printf 'Abra o NFSMW, execute o teste no carro parado, depois rode o modo stop.\n'
    ;;
stop)
    # Never save an unfiltered global dump; it may contain other app names.
    trap 'run_rish "dumpsys SurfaceFlinger --timestats -disable" >/dev/null 2>&1 || true' EXIT
    dump="$(run_rish 'dumpsys SurfaceFlinger --timestats -dump')"
    stamp="$(date '+%Y%m%d_%H%M%S')"
    out="$OUTPUT_DIR/NFSMW_PRE686_SURFACEFLINGER_${stamp}.txt"
    {
        printf 'PRE686_SURFACEFLINGER_TIMESTATS_CAPTURE\n'
        printf 'PACKAGE=%s\n' "$APP"
        printf 'COLLECTION_END=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
        if [ -f "$STATE_FILE" ]; then
            printf 'COLLECTION_START=%s\n' "$(cat "$STATE_FILE")"
        fi
        printf 'SOURCE=Android SurfaceFlinger timestats (global collection, filtered to NFSMW layer)\n'
        printf 'NOTE=Reported frame presents may differ from internal engine Swap counters\n'
    } > "$out"
    active=0
    matches=0
    while IFS= read -r line; do
        case "$line" in
        'layerName = '*)
            active=0
            if [[ "$line" == *"$APP"* ]]; then
                active=1
                matches=$((matches+1))
                printf '%s\n' "$line" >> "$out"
            fi
            ;;
        *)
            if [ "$active" -eq 1 ]; then
                case "$line" in
                    *'totalFrames ='*|*'averageFPS ='*|*'presentToPresent histogram'*|*'ms='*)
                        printf '%s\n' "$line" >> "$out" ;;
                esac
            fi
            ;;
        esac
    done <<< "$dump"
    rm -f "$STATE_FILE"
    printf 'PRE686_MATCHED_NFSMW_LAYERS=%s\n' "$matches" >> "$out"
    printf 'PRE686_TIMESTATS_OUTPUT=%s\n' "$out"
    if [ "$matches" -eq 0 ]; then
        printf 'PRE686_NO_GAME_LAYER_FOUND: teste nao comprova frame pacing da tela.\n' >&2
        exit 4
    fi
    printf 'PRE686_SF_TIMESTATS_CAPTURE=RECORDED_UNVALIDATED\n'
    ;;
abort)
    run_rish 'dumpsys SurfaceFlinger --timestats -disable' >/dev/null
    rm -f "$STATE_FILE"
    printf 'PRE686_SF_TIMESTATS_STOPPED=TRUE\n'
    ;;
*) usage; exit 2 ;;
esac
