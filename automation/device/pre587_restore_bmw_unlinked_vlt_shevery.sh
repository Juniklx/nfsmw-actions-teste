#!/system/bin/sh
# PRE587 rollback unlinked BMW VLT collection diagnostic; run only after closing the game.
# Preserve experiment files as *.pre587_test_previous, never delete user saves.
set -eu
fail(){ echo "PRE587_RESTORE_ABORTADO: $*" >&2; exit 1; }
[ "$#" -eq 1 ] || fail "Use: sh pre587_restore_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT"
ROOT="$1"
case "$ROOT" in /*) :;; *) fail "GAME_ROOT deve ser absoluto";; esac
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum indisponivel"
command -v pidof >/dev/null 2>&1 || fail "pidof indisponivel"
pidof io.github.nfsmwrecomp >/dev/null 2>&1 && fail "Feche a V48"
NFS="$ROOT/NFS"
ZDIR="$NFS/ZDIR.BIN"; DATA="$NFS/ZZDATA4.BIN"
BZ="$NFS/ZDIR.BIN.pre587_original_backup"
BD="$NFS/ZZDATA4.BIN.pre587_original_backup"
[ -f "$BZ" ] && [ -f "$BD" ] || fail "Backups originais PRE587 ausentes"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "Arquivos ativos ausentes"
[ ! -e "$NFS/ZDIR.BIN.pre587_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
[ ! -e "$NFS/ZZDATA4.BIN.pre587_test_previous" ] || fail "Arquivo experimental anterior ja preservado"
h(){ sha256sum "$1" | awk '{print $1}'; }
[ "$(h "$BZ")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Backup ZDIR nao original"
[ "$(h "$BD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Backup ZZDATA4 nao original"
[ "$(h "$ZDIR")" = "3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025" ] || fail "ZDIR ativo nao corresponde ao teste PRE587"
[ "$(h "$DATA")" = "524c22622039086c9207f25b3a82823fb62d8879e70d0142730bca2b5cdda996" ] || fail "ZZDATA4 ativo nao corresponde ao teste PRE587"
mv "$DATA" "$NFS/ZZDATA4.BIN.pre587_test_previous" || fail "Falha preservando dado experimental"
mv "$BD" "$DATA" || fail "Falha restaurando ZZDATA4, backup ainda no disco"
mv "$ZDIR" "$NFS/ZDIR.BIN.pre587_test_previous" || fail "Falha preservando indice experimental"
mv "$BZ" "$ZDIR" || fail "Falha restaurando ZDIR"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Restauracao incompleta ZZDATA4"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "Restauracao incompleta ZDIR"
echo "PRE587_RESTORE=ORIGINAIS_VERIFICADOS"
echo "PRE587_SAVES=NAO_MODIFICADOS_PELO_SCRIPT"
