#!/system/bin/sh
# PRE618: READ-ONLY checks of live PTBR game asset identity.
# No writes, no save edits, no APK/keystore changes, no network.
# Usage: sh pre618_check_active_bmw_archive_readonly_shevery.sh /storage/emulated/0/NFSMW_PTBR
set -eu
if [ "$#" -ne 1 ]; then echo "PRE618_ABORT: informe /CAMINHO/ROOT/NFSMW_PTBR" >&2; exit 2; fi
ROOT="$1"
case "$ROOT" in /*) : ;; *) echo "PRE618_ABORT: caminho deve ser absoluto" >&2;exit 2;; esac
NFS="$ROOT/NFS"
Z="$NFS/ZDIR.BIN"
D="$NFS/ZZDATA4.BIN"
command -v sha256sum >/dev/null 2>&1 || { echo "PRE618_ABORT: sha256sum indisponivel" >&2;exit 2; }
[ -f "$Z" ] && [ -f "$D" ] || { echo "PRE618_ABORT: arquivos NFS ausentes" >&2;exit 2; }
n(){ wc -c < "$1" | tr -d '[:space:]'; }
h(){ sha256sum "$1" | awk '{print $1}'; }
SZ="$(n "$Z")"
SD="$(n "$D")"
[ "$SZ" = 33312 ] && [ "$SD" = 401068032 ] || {
  echo "PRE618_TAMANHOS_INESPERADOS: ZDIR=$SZ ZZDATA4=$SD" >&2
  exit 2
}
HZ="$(h "$Z")"
HD="$(h "$D")"
echo "PRE618_MODO=SOMENTE_LEITURA"
echo "PRE618_ZDIR_SHA256=$HZ"
echo "PRE618_ZZDATA4_SHA256=$HD"
if [ "$HZ" = "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" ] && \
   [ "$HD" = "1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146" ]; then
   echo "PRE618_IDENTIDADE=PRE607_BMW_PARENT_CORRECTED_VERIFICADA"
elif [ "$HZ" = "832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" ] && \
     [ "$HD" = "7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" ]; then
   echo "PRE618_IDENTIDADE=PTBR_ORIGINAL_VERIFICADA"
elif [ "$HZ" = "f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da" ] && \
     [ "$HD" = "522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29" ]; then
   echo "PRE618_IDENTIDADE=PRE592_REFSPEC_COUNT_ZERO_VERIFICADA"
else
   echo "PRE618_IDENTIDADE=DESCONHECIDA_NAO_MODIFICAR"
fi
echo "PRE618_JOGO_MODIFICADO_PELO_SCRIPT=NAO"
echo "PRE618_SAVE_MODIFICADO_PELO_SCRIPT=NAO"
