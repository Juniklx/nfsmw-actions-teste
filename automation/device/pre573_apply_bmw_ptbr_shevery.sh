#!/system/bin/sh
# PRE573 — manual, fail-closed PTBR BMW experimental file staging for Shevery.
# Never modifies saves, APK or keys; may change TWO game archive files only
# after validating original hashes, patch hashes and staged full-archive SHA.
# Usage: sh pre573_apply_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT /ABSOLUTE/PATCH_FOLDER
set -eu
fail(){ echo "PRE573_ABORTADO: $*" >&2; exit 1; }
[ "$#" -eq 2 ] || fail "Use: sh script.sh /game/root /patch/folder"
ROOT="$1"; PATCH="$2"
case "$ROOT" in /*) :;; *) fail "GAME_ROOT deve ser caminho absoluto";; esac
case "$PATCH" in /*) :;; *) fail "PATCH_FOLDER deve ser caminho absoluto";; esac
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum indisponivel"
command -v dd >/dev/null 2>&1 || fail "dd indisponivel"
command -v pidof >/dev/null 2>&1 || fail "pidof indisponivel"
pidof io.github.nfsmwrecomp >/dev/null 2>&1 && fail "Feche completamente a V48 antes de continuar"
NFS="$ROOT/NFS"
ZDIR="$NFS/ZDIR.BIN"
DATA="$NFS/ZZDATA4.BIN"
PZ="$PATCH/PRE572_ZDIR_PTBR_BMW_TESTE_FRAGMENT.bin"
PD="$PATCH/PRE572_ZZDATA4_PRIMEIROS_341_SETORES_BMW_TESTE.bin"
WZ="$NFS/ZDIR.BIN.pre573_new"
WD="$NFS/ZZDATA4.BIN.pre573_new"
BZ="$NFS/ZDIR.BIN.pre573_original_backup"
BD="$NFS/ZZDATA4.BIN.pre573_original_backup"
[ -d "$NFS" ] || fail "GAME_ROOT/NFS nao existe"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "ZDIR ou ZZDATA4 original nao encontrado"
[ -f "$PZ" ] && [ -f "$PD" ] || fail "Fragmentos PRE572 nao encontrados na pasta informada"
[ ! -e "$WZ" ] && [ ! -e "$WD" ] || fail "Ja existem arquivos temporarios PRE573; revisar manualmente"
[ ! -e "$BZ" ] && [ ! -e "$BD" ] || fail "Ja existem backups PRE573; nao repetir"
h(){ sha256sum "$1" | awk '{print $1}'; }
n(){ wc -c < "$1" | tr -d '[:space:]'; }
[ "$(n "$ZDIR")" = 33312 ] || fail "ZDIR tamanho de origem difere"
[ "$(n "$DATA")" = 401068032 ] || fail "ZZDATA4 tamanho de origem difere"
[ "$(n "$PZ")" = 33312 ] || fail "ZDIR patch tamanho difere"
[ "$(n "$PD")" = 698368 ] || fail "Fragmento 341 setores tamanho difere"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "ZDIR fonte PTBR desconhecido"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "ZZDATA4 fonte PTBR desconhecido"
[ "$(h "$PZ")" = "d625d5f7195c7b1596c03d2632f87de3a34cec69da902b6604e82949677e4832" ] || fail "ZDIR patch SHA diferente"
[ "$(h "$PD")" = "29a62931ee0cb68e96100014260d41d0f627d8348bdcc6406e529ad0482bb7eb" ] || fail "Setor patch SHA diferente"
echo "PRE573_FONTE=VERIFICADA"
echo "PRE573_ESTAGIANDO_COPIA_DE_401MB"
cp "$DATA" "$WD" || fail "Falha copiando archive; original preservado"
[ "$(n "$WD")" = 401068032 ] && [ "$(h "$WD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Copia ZZDATA4 incompleta; original preservado"
dd if="$PD" of="$WD" bs=2048 count=341 conv=notrunc 2>/dev/null || fail "Falha gravando fragmento na COPIA"
[ "$(n "$WD")" = 401068032 ] || fail "Tamanho da copia alterado"
[ "$(h "$WD")" = "4eca61a0969bd1311e7b664f073ecaab50c950b43b10bb4438858ff3c57b665e" ] || fail "Hash completo da copia modificada diferente, nao aplicar"
cp "$PZ" "$WZ" || fail "Falha preparando ZDIR patch"
[ "$(h "$WZ")" = "d625d5f7195c7b1596c03d2632f87de3a34cec69da902b6604e82949677e4832" ] || fail "ZDIR patch temporario corrompido"
# Only now, with app stopped and two fully verified staged files, do renames.
mv "$DATA" "$BD" || fail "Nao foi possivel preservar original ZZDATA4"
mv "$WD" "$DATA" || fail "Falha ao ativar ZZDATA4; backup original continua em *.pre573_original_backup"
mv "$ZDIR" "$BZ" || fail "Nao foi possivel preservar original ZDIR"
mv "$WZ" "$ZDIR" || fail "Falha ao ativar ZDIR; backup original continua em *.pre573_original_backup"
[ "$(h "$ZDIR")" = "d625d5f7195c7b1596c03d2632f87de3a34cec69da902b6604e82949677e4832" ] || fail "ZDIR final diferente"
[ "$(h "$DATA")" = "4eca61a0969bd1311e7b664f073ecaab50c950b43b10bb4438858ff3c57b665e" ] || fail "ZZDATA4 final diferente"
echo "PRE573_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS"
echo "PRE573_APK_MODIFICADA=NAO"
echo "PRE573_SAVE_MODIFICADO_PELO_SCRIPT=NAO"
echo "PRE573_GUEST_TESTADO=NAO"
echo "PRE573_BACKUPS_ORIGINAIS=ZDIR.BIN.pre573_original_backup,ZZDATA4.BIN.pre573_original_backup"
