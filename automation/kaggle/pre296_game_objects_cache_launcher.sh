#!/usr/bin/env bash
# PRE296 experiment: dedicated game C++ objects only; OFF until explicit gate.
# No source file, signing key, save, APK, ISO or asset is copied by this wrapper.
set -euo pipefail
if (( $# < 2 )); then exit 2; fi
compiler="$1"; shift
if [[ "${NFSMW_CACHE_GAME_OPT_IN:-0}" != "1" ]]; then
  exec "$compiler" "$@"
fi
: "${NFSMW_GAME_CACHE_SOURCE_ROOT:?}"
: "${NFSMW_GAME_CCACHE_BIN:?}"
: "${NFSMW_GAME_CCACHE_DIR:?}"
: "${RUNNER_TEMP:?}"
[[ -x "$NFSMW_GAME_CCACHE_BIN" && -d "$NFSMW_GAME_CACHE_SOURCE_ROOT" ]] || exit 3
repo_root="$(realpath -e "$NFSMW_GAME_CACHE_SOURCE_ROOT")"
runner="$(realpath -e "$RUNNER_TEMP")"
cache="$(realpath -m "$NFSMW_GAME_CCACHE_DIR")"
[[ "$cache" == "$runner/nfsmw-game-objects" && ! -L "$cache" ]] || exit 3
src=""
prev=""
for arg in "$@"; do
  if [[ "$prev" == "-c" ]]; then src="$arg"; break; fi
  if [[ "$arg" == -c?* && "$arg" != "-c" ]]; then src="${arg:2}"; break; fi
  prev="$arg"
done
if [[ -z "$src" || ! -f "$src" ]]; then exec "$compiler" "$@"; fi
src="$(realpath -e "$src")"
case "$src" in
  "$repo_root"/nativo/app/generated/default/*.cpp|"$repo_root"/nativo/app/src/*.cpp|"$repo_root"/nativo/app_usa/generated/default/*.cpp|"$repo_root"/nativo/app_usa/src/*.cpp)
    exec "$NFSMW_GAME_CCACHE_BIN" "$compiler" "$@" ;;
  *) exec "$compiler" "$@" ;;
esac
