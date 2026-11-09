#!/system/bin/sh
# PRE607 rollback BMW level1 child collection parent inheritance diagnostic (experimental); run only after closing the game.
# Preserve experiment files as *.pre607_test_previous, never delete user saves.
set -eu
fail(){ echo "PRE607_RESTORE_ABORTADO: $*" >&2; exit 1; }
[ "$#" -eq 1 ] || fail "Use: sh pre607_restore_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT"
ROOT="$1"
case "$ROOT" in /*) :;; *) fail "GAME_ROOT deve ser absoluto";; esac
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum indisponivel"
command -v pidof >/dev/null 2>&1 || fail "pidof indisponivel"
pidof io.github.nfsmwrecomp >/dev/null 2>&1 && fail "Feche a V48"
NFS="$ROOT/NFS"
ZDIR="$NFS/ZDIR.BIN"; DATA="$NFS/ZZDATA4.BIN"
BZ="$NFS/ZDIR.BIN.pre607_original_backup"
BD="$NFS/ZZDATA4.BIN.pre607_original_backup"
[ -f "$BZ" ] && [ -f "$BD" ] || fail "Backups originais PRE607 ausentes"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "Arquivos ativos ausentes"
[ ! -e "$NFS/ZDIR.BIN.pre607_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
[ ! -e "$NFS/ZZDATA4.BIN.pre607_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
h(){ sha256sum "$1" | awk '{print $1}'; }
[ "$(h "$BZ")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Backup ZDIR nao original"
[ "$(h "$BD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Backup ZZDATA4 nao original"
[ "$(h "$ZDIR")" = "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" ] || fail "ZDIR ativo nao corresponde ao teste PRE607"
[ "$(h "$DATA")" = "1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146" ] || fail "ZZDATA4 ativo nao corresponde ao teste PRE607"
mv "$DATA" "$NFS/ZZDATA4.BIN.pre607_test_previous" || fail "Falha preservando dado experimental"
mv "$BD" "$DATA" || fail "Falha restaurando ZZDATA4, backup ainda no disco"
mv "$ZDIR" "$NFS/ZDIR.BIN.pre607_test_previous" || fail "Falha preservando indice experimental"
mv "$BZ" "$ZDIR" || fail "Falha restaurando ZDIR"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Restauracao incompleta ZZDATA4"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Restauracao incompleta ZDIR"
echo "PRE607_RESTORE=ORIGINAIS_VERIFICADOS"
echo "PRE607_SAVES=NAO_MODIFICADOS_PELO_SCRIPT"
