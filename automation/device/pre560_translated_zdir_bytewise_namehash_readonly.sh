#!/system/bin/sh
# PRE560: scan the translated PAL ZDIR by little-endian BYTES, read-only.
# Without arguments: find the one user-reported SHA256 file on device.
# With arguments: file and expected SHA256 for a disposable CI fixture.
# No path, file content, or user data is printed.
EXPECTED=${2:-832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf}
scan_one() {
  F="$1"
  [ -r "$F" ] || return
  [ "$(stat -c %s "$F" 2>/dev/null)" = 33312 ] || return
  H=$(sha256sum "$F" 2>/dev/null | awk '{print $1}')
  [ "$H" = "$EXPECTED" ] || return
  echo PRE560_ZDIR_SHA256=CONFIRMADO
  od -An -v -tu1 "$F" 2>/dev/null | awk '
    function u32(k) {
      return b[k]+256*b[k+1]+65536*b[k+2]+16777216*b[k+3]
    }
    {
      for (i=1; i<=NF; i++) {
        b[n%24]=$i+0
        n++
        if (n%24!=0) continue
        rows++
        hash=u32(0)
        archive=u32(4)
        if(archive>=2147483648) archive-=4294967296
        sector=u32(8)
        resource_size=u32(16)
        checksum=u32(20)
        if (archive>=0 && archive<=9 && resource_size>0 && resource_size<1000000000) plausible++
        if (hash==2541041562) {
          attrs++
          printf "PRE560_ATTR_ROW=%.0f\n",rows-1
          printf "PRE560_ATTR_ARCHIVE=%.0f\n",archive
          printf "PRE560_ATTR_SECTOR=%.0f\n",sector
          printf "PRE560_ATTR_SIZE=%.0f\n",resource_size
          printf "PRE560_ATTR_CHECKSUM_U32=%.0f\n",checksum
          printf "PRE560_ATTR_OFFSET=%.0f\n",sector*2048
        }
        if (hash==2159967075) fe++
        if (hash==1284741942) gblz++
        if (hash==1284730898) gbbun++
        if (hash==1283544977) gabun++
      }
    }
    END {
      printf "PRE560_TOTAL_REGISTROS=%.0f\n",rows
      printf "PRE560_REGISTROS_PLAUSIVEIS=%.0f\n",plausible
      printf "PRE560_ATTR_MATCHES=%.0f\n",attrs
      printf "PRE560_FE_ATTRIB_MATCHES=%.0f\n",fe
      printf "PRE560_GLOBALB_LZC_MATCHES=%.0f\n",gblz
      printf "PRE560_GLOBALB_BUN_MATCHES=%.0f\n",gbbun
      printf "PRE560_GLOBALA_BUN_MATCHES=%.0f\n",gabun
      if(n%24!=0) print "PRE560_AVISO=REGISTRO_INCOMPLETO"
    }'
}
echo PRE560_INICIO
if [ -n "${1:-}" ]; then
  scan_one "$1"
else
  find /storage/emulated/0 -type f -name ZDIR.BIN 2>/dev/null |
  while IFS= read -r F; do
    case "$F" in */NFS/ZDIR.BIN) scan_one "$F";; esac
  done
fi
echo PRE560_FIM
