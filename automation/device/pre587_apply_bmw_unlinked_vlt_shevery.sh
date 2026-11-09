#!/system/bin/sh
# PRE587 — manual, fail-closed unlinked BMW VLT collection diagnostic staging for Shevery.
# Never modifies saves, APK or keys; may change TWO game archive files only
# after validating original hashes, patch hashes and staged full-archive SHA.
# Usage: sh pre587_apply_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT /ABSOLUTE/PATCH_FOLDER
set -eu
fail(){ echo "PRE587_ABORTADO: $*" >&2; exit 1; }
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
PZ="$PATCH/PRE586_ZDIR_VLT_NEW_COLLECTION_UNLINKED.bin"
PD="$PATCH/PRE586_ZZDATA4_FIRST341_UNLINKED_VLT.bin"
WZ="$NFS/ZDIR.BIN.pre587_new"
WD="$NFS/ZZDATA4.BIN.pre587_new"
BZ="$NFS/ZDIR.BIN.pre587_original_backup"
BD="$NFS/ZZDATA4.BIN.pre587_original_backup"
[ -d "$NFS" ] || fail "GAME_ROOT/NFS nao existe"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "ZDIR ou ZZDATA4 original nao encontrado"
[ -f "$PZ" ] && [ -f "$PD" ] || fail "Fragmentos PRE572 nao encontrados na pasta informada"
[ ! -e "$WZ" ] && [ ! -e "$WD" ] || fail "Ja existem arquivos temporarios PRE587; revisar manualmente"
[ ! -e "$BZ" ] && [ ! -e "$BD" ] || fail "Ja existem backups PRE587; nao repetir"
h(){ sha256sum "$1" | awk '{print $1}'; }
n(){ wc -c < "$1" | tr -d '[:space:]'; }
[ "$(n "$ZDIR")" = 33312 ] || fail "ZDIR tamanho de origem difere"
[ "$(n "$DATA")" = 401068032 ] || fail "ZZDATA4 tamanho de origem difere"
[ "$(n "$PZ")" = 33312 ] || fail "ZDIR patch tamanho difere"
[ "$(n "$PD")" = 698368 ] || fail "Fragmento 341 setores tamanho difere"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "ZDIR fonte PTBR desconhecido"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "ZZDATA4 fonte PTBR desconhecido"
[ "$(h "$PZ")" = "3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025" ] || fail "ZDIR patch SHA diferente"
[ "$(h "$PD")" = "11f233a7a22df3822573a3a52af50f7c9b27f4b5c5cba77fdaad3c4e03041271" ] || fail "Setor patch SHA diferente"
echo "PRE587_FONTE=VERIFICADA"
echo "PRE587_ESTAGIANDO_COPIA_DE_401MB"
cp "$DATA" "$WD" || fail "Falha copiando archive; original preservado"
[ "$(n "$WD")" = 401068032 ] && [ "$(h "$WD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Copia ZZDATA4 incompleta; original preservado"
dd if="$PD" of="$WD" bs=2048 count=341 conv=notrunc 2>/dev/null || fail "Falha gravando fragmento na COPIA"
[ "$(n "$WD")" = 401068032 ] || fail "Tamanho da copia alterado"
[ "$(h "$WD")" = "524c22622039086c9207f25b3a82823fb62d8879e70d0142730bca2b5cdda996" ] || fail "Hash completo da copia modificada diferente, nao aplicar"
cp "$PZ" "$WZ" || fail "Falha preparando ZDIR patch"
[ "$(h "$WZ")" = "3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025" ] || fail "ZDIR patch temporario corrompido"
# Only now, with app stopped and two fully verified staged files, do renames.
mv "$DATA" "$BD" || fail "Nao foi possivel preservar original ZZDATA4"
mv "$WD" "$DATA" || fail "Falha ao ativar ZZDATA4; backup original continua em *.pre587_original_backup"
mv "$ZDIR" "$BZ" || fail "Nao foi possivel preservar original ZDIR"
mv "$WZ" "$ZDIR" || fail "Falha ao ativar ZDIR; backup original continua em *.pre587_original_backup"
[ "$(h "$ZDIR")" = "3ed3070bd10bb41789ef7b32b4203805cdb395fabf2665b528848bba3ad31025" ] || fail "ZDIR final diferente"
[ "$(h "$DATA")" = "524c22622039086c9207f25b3a82823fb62d8879e70d0142730bca2b5cdda996" ] || fail "ZZDATA4 final diferente"
echo "PRE587_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS"
echo "PRE587_APK_MODIFICADA=NAO"
echo "PRE587_SAVE_MODIFICADO_PELO_SCRIPT=NAO"
echo "PRE587_GUEST_TESTADO=NAO"
echo "PRE587_BACKUPS_ORIGINAIS=ZDIR.BIN.pre587_original_backup,ZZDATA4.BIN.pre587_original_backup"
