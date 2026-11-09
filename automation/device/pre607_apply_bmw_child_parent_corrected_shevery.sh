#!/system/bin/sh
# PRE607 — manual, fail-closed BMW level1 child collection parent inheritance diagnostic (experimental) staging for Shevery.
# Never modifies saves, APK or keys; may change TWO game archive files only
# after validating original hashes, patch hashes and staged full-archive SHA.
# Usage: sh pre607_apply_bmw_child_parent_corrected_shevery.sh /ABSOLUTE/GAME_ROOT /ABSOLUTE/PATCH_FOLDER
set -eu
fail(){ echo "PRE607_ABORTADO: $*" >&2; exit 1; }
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
PZ="$PATCH/PRE606_ZDIR_BMW_CHILD_PARENT_CORRECTED.bin"
PD="$PATCH/PRE606_ZZDATA4_FIRST341_BMW_PARENT_CORRECTED.bin"
WZ="$NFS/ZDIR.BIN.pre607_new"
WD="$NFS/ZZDATA4.BIN.pre607_new"
BZ="$NFS/ZDIR.BIN.pre607_original_backup"
BD="$NFS/ZZDATA4.BIN.pre607_original_backup"
[ -d "$NFS" ] || fail "GAME_ROOT/NFS nao existe"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "ZDIR ou ZZDATA4 original nao encontrado"
[ -f "$PZ" ] && [ -f "$PD" ] || fail "Fragmentos PRE606 nao encontrados na pasta informada"
[ ! -e "$WZ" ] && [ ! -e "$WD" ] || fail "Ja existem arquivos temporarios PRE607; revisar manualmente"
[ ! -e "$BZ" ] && [ ! -e "$BD" ] || fail "Ja existem backups PRE607; nao repetir"
h(){ sha256sum "$1" | awk '{print $1}'; }
n(){ wc -c < "$1" | tr -d '[:space:]'; }
[ "$(n "$ZDIR")" = 33312 ] || fail "ZDIR tamanho de origem difere"
[ "$(n "$DATA")" = 401068032 ] || fail "ZZDATA4 tamanho de origem difere"
[ "$(n "$PZ")" = 33312 ] || fail "ZDIR patch tamanho difere"
[ "$(n "$PD")" = 698368 ] || fail "Fragmento 341 setores tamanho difere"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "ZDIR fonte PTBR desconhecido"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "ZZDATA4 fonte PTBR desconhecido"
[ "$(h "$PZ")" = "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" ] || fail "ZDIR patch SHA diferente"
[ "$(h "$PD")" = "93327b44eb54b0ec9b14e51e7b35da9071e9531454c49819c35e6e6172c284a5" ] || fail "Setor patch SHA diferente"
echo "PRE607_FONTE=VERIFICADA"
echo "PRE607_ESTAGIANDO_COPIA_DE_401MB"
cp "$DATA" "$WD" || fail "Falha copiando archive; original preservado"
[ "$(n "$WD")" = 401068032 ] && [ "$(h "$WD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Copia ZZDATA4 incompleta; original preservado"
dd if="$PD" of="$WD" bs=2048 count=341 conv=notrunc 2>/dev/null || fail "Falha gravando fragmento na COPIA"
[ "$(n "$WD")" = 401068032 ] || fail "Tamanho da copia alterado"
[ "$(h "$WD")" = "1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146" ] || fail "Hash completo da copia modificada diferente, nao aplicar"
cp "$PZ" "$WZ" || fail "Falha preparando ZDIR patch"
[ "$(h "$WZ")" = "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" ] || fail "ZDIR patch temporario corrompido"
# Only now, with app stopped and two fully verified staged files, do renames.
mv "$DATA" "$BD" || fail "Nao foi possivel preservar original ZZDATA4"
mv "$WD" "$DATA" || fail "Falha ao ativar ZZDATA4; backup original continua em *.pre607_original_backup"
mv "$ZDIR" "$BZ" || fail "Nao foi possivel preservar original ZDIR"
mv "$WZ" "$ZDIR" || fail "Falha ao ativar ZDIR; backup original continua em *.pre607_original_backup"
[ "$(h "$ZDIR")" = "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" ] || fail "ZDIR final diferente"
[ "$(h "$DATA")" = "1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146" ] || fail "ZZDATA4 final diferente"
echo "PRE607_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS"
echo "PRE607_APK_MODIFICADA=NAO"
echo "PRE607_SAVE_MODIFICADO_PELO_SCRIPT=NAO"
echo "PRE607_GUEST_TESTADO=NAO"
echo "PRE607_BACKUPS_ORIGINAIS=ZDIR.BIN.pre607_original_backup,ZZDATA4.BIN.pre607_original_backup"
