#!/system/bin/sh
# PRE592 — manual, fail-closed BMW active RefSpec pointer-only diagnostic (engine levels zero) staging for Shevery.
# Never modifies saves, APK or keys; may change TWO game archive files only
# after validating original hashes, patch hashes and staged full-archive SHA.
# Usage: sh pre592_apply_bmw_ptbr_shevery.sh /ABSOLUTE/GAME_ROOT /ABSOLUTE/PATCH_FOLDER
set -eu
fail(){ echo "PRE592_ABORTADO: $*" >&2; exit 1; }
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
PZ="$PATCH/PRE591_ZDIR_BMW_REFSPEC_POINTER_ONLY.bin"
PD="$PATCH/PRE591_ZZDATA4_FIRST341_REFSPEC_POINTER_ONLY.bin"
WZ="$NFS/ZDIR.BIN.pre592_new"
WD="$NFS/ZZDATA4.BIN.pre592_new"
BZ="$NFS/ZDIR.BIN.pre592_original_backup"
BD="$NFS/ZZDATA4.BIN.pre592_original_backup"
[ -d "$NFS" ] || fail "GAME_ROOT/NFS nao existe"
[ -f "$ZDIR" ] && [ -f "$DATA" ] || fail "ZDIR ou ZZDATA4 original nao encontrado"
[ -f "$PZ" ] && [ -f "$PD" ] || fail "Fragmentos PRE572 nao encontrados na pasta informada"
[ ! -e "$WZ" ] && [ ! -e "$WD" ] || fail "Ja existem arquivos temporarios PRE592; revisar manualmente"
[ ! -e "$BZ" ] && [ ! -e "$BD" ] || fail "Ja existem backups PRE592; nao repetir"
h(){ sha256sum "$1" | awk '{print $1}'; }
n(){ wc -c < "$1" | tr -d '[:space:]'; }
[ "$(n "$ZDIR")" = 33312 ] || fail "ZDIR tamanho de origem difere"
[ "$(n "$DATA")" = 401068032 ] || fail "ZZDATA4 tamanho de origem difere"
[ "$(n "$PZ")" = 33312 ] || fail "ZDIR patch tamanho difere"
[ "$(n "$PD")" = 698368 ] || fail "Fragmento 341 setores tamanho difere"
[ "$(h "$ZDIR")" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] || fail "ZDIR fonte PTBR desconhecido"
[ "$(h "$DATA")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "ZZDATA4 fonte PTBR desconhecido"
[ "$(h "$PZ")" = "f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da" ] || fail "ZDIR patch SHA diferente"
[ "$(h "$PD")" = "6ad6e5748115380ab057e65642b2bad0ce83f74282b4d80dbbc5b71f33c8c12d" ] || fail "Setor patch SHA diferente"
echo "PRE592_FONTE=VERIFICADA"
echo "PRE592_ESTAGIANDO_COPIA_DE_401MB"
cp "$DATA" "$WD" || fail "Falha copiando archive; original preservado"
[ "$(n "$WD")" = 401068032 ] && [ "$(h "$WD")" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ] || fail "Copia ZZDATA4 incompleta; original preservado"
dd if="$PD" of="$WD" bs=2048 count=341 conv=notrunc 2>/dev/null || fail "Falha gravando fragmento na COPIA"
[ "$(n "$WD")" = 401068032 ] || fail "Tamanho da copia alterado"
[ "$(h "$WD")" = "522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29" ] || fail "Hash completo da copia modificada diferente, nao aplicar"
cp "$PZ" "$WZ" || fail "Falha preparando ZDIR patch"
[ "$(h "$WZ")" = "f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da" ] || fail "ZDIR patch temporario corrompido"
# Only now, with app stopped and two fully verified staged files, do renames.
mv "$DATA" "$BD" || fail "Nao foi possivel preservar original ZZDATA4"
mv "$WD" "$DATA" || fail "Falha ao ativar ZZDATA4; backup original continua em *.pre592_original_backup"
mv "$ZDIR" "$BZ" || fail "Nao foi possivel preservar original ZDIR"
mv "$WZ" "$ZDIR" || fail "Falha ao ativar ZDIR; backup original continua em *.pre592_original_backup"
[ "$(h "$ZDIR")" = "f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da" ] || fail "ZDIR final diferente"
[ "$(h "$DATA")" = "522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29" ] || fail "ZZDATA4 final diferente"
echo "PRE592_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS"
echo "PRE592_APK_MODIFICADA=NAO"
echo "PRE592_SAVE_MODIFICADO_PELO_SCRIPT=NAO"
echo "PRE592_GUEST_TESTADO=NAO"
echo "PRE592_BACKUPS_ORIGINAIS=ZDIR.BIN.pre592_original_backup,ZZDATA4.BIN.pre592_original_backup"
