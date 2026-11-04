#!/usr/bin/env bash
# PRE140 - GitHub Actions compiler launcher: cache ONLY SDK runtime source files.
# Game translation sources under nativo/app and nativo/app_usa bypass ccache.
# Does not touch signing keys, APKs, output libs, or generated game code.
set -euo pipefail
if (( $# < 2 )); then echo "PRE140 launcher expects compiler plus arguments" >&2; exit 2; fi
compiler="$1"
shift
if [[ "${NFSMW_SDK_ONLY_CCACHE_ENABLED:-}" != "1" ]]; then
  exec "$compiler" "$@"
fi
SDK_ROOT="${NFSMW_SDK_SOURCE_ROOT:?PRE140 SDK source root missing}"
CCACHE_BINARY="${NFSMW_CCACHE_BIN:?PRE140 ccache binary missing}"
CACHE_ROOT="${CCACHE_DIR:?PRE140 CCACHE_DIR missing}"
RUNNER_ROOT="${RUNNER_TEMP:?PRE140 RUNNER_TEMP missing}"
if [[ ! -d "$SDK_ROOT" || ! -x "$CCACHE_BINARY" || -L "$CACHE_ROOT" ]]; then
  echo "PRE140 invalid SDK, compiler cache, or cache path" >&2; exit 3
fi
sdk_real="$(realpath -e "$SDK_ROOT")"
runner_real="$(realpath -e "$RUNNER_ROOT")"
cache_real="$(realpath -m "$CACHE_ROOT")"
if [[ "$cache_real" != "$runner_real/nfsmw-ccache-sdk-only" ]]; then
  echo "PRE140 CCACHE_DIR must be exclusive inside RUNNER_TEMP" >&2; exit 3
fi
source_arg=""
prev=""
for item in "$@"; do
  if [[ "$prev" == "-c" ]]; then source_arg="$item"; break; fi
  if [[ "$item" == -c?* && "$item" != "-c" ]]; then source_arg="${item:2}"; break; fi
  prev="$item"
done
if [[ -z "$source_arg" || ! -f "$source_arg" ]]; then
  exec "$compiler" "$@"
fi
source_real="$(realpath -e "$source_arg")"
# Cache only SDK's runtime src/, not the game's translation units.
case "$source_real" in
  "$sdk_real"/src/*.cpp|"$sdk_real"/src/*.c|"$sdk_real"/src/*.cc)
    exec "$CCACHE_BINARY" "$compiler" "$@"
    ;;
  *)
    exec "$compiler" "$@"
    ;;
esac
