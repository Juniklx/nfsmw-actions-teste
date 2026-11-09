#!/system/bin/sh
# PRE592 rollback BMW active RefSpec pointer-only diagnostic (engine levels zero); run only after closing the game.
# Preserve experiment files as *.pre592_test_previous, never delete user saves.
set -eu
fail(){ echo "PRE592_RESTORE_ABORTADO: $*" >&2; exit 1; }
[ "$#" -eq 1 ] || fail "Use: sh pre592_restore_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT"
ROOT="$1"
case "$ROOT" in /*) :;; *) fail "GAME_ROOT deve ser absoluto";; esac
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum indisponivel"
command -v pidof >/dev/null 2>&1 || fail "pidof indisponivel"
pidof io.github.nfsmwrecomp >/dev/null 2>&1 && fail "Feche a V48"
NFS="$ROOT/NFS"
ZDIR="$NFS/ZDIR.BIN"; DATA="$NFS/ZZDATA4.BIN"
BZ="$NFS/ZDIR.BIN.pre592_original_backup"
BD="$NFS/ZZDATA4.BIN.pre592_original_backup"
[ -f "$BZ" ] && [ -f "$BD" ] || fail "Backups originais PRE592 ausentes"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "Arquivos ativos ausentes"
[ ! -e "$NFS/ZDIR.BIN.pre592_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
[ ! -e "$NFS/ZZDATA4.BIN.pre592_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
h(){ sha256sum "$1" | awk '{print $1}'; }
[ "$(h "$BZ")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Backup ZDIR nao original"
[ "$(h "$BD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Backup ZZDATA4 nao original"
[ "$(h "$ZDIR")" = "f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da" ] || fail "ZDIR ativo nao corresponde ao teste PRE592"
[ "$(h "$DATA")" = "522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29" ] || fail "ZZDATA4 ativo nao corresponde ao teste PRE592"
mv "$DATA" "$NFS/ZZDATA4.BIN.pre592_test_previous" || fail "Falha preservando dado experimental"
mv "$BD" "$DATA" || fail "Falha restaurando ZZDATA4, backup ainda no disco"
mv "$ZDIR" "$NFS/ZDIR.BIN.pre592_test_previous" || fail "Falha preservando indice experimental"
mv "$BZ" "$ZDIR" || fail "Falha restaurando ZDIR"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Restauracao incompleta ZZDATA4"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Restauracao incompleta ZDIR"
echo "PRE592_RESTORE=ORIGINAIS_VERIFICADOS"
echo "PRE592_SAVES=NAO_MODIFICADOS_PELO_SCRIPT"
