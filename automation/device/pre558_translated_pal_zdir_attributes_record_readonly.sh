#!/system/bin/sh
# PRE558: read only. No private paths printed. Hash-match translated ZDIR.
EXPECTED=832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf
WANTED=$((0x9775379a))
echo PRE558_TRANSLATED_ZDIR_SCAN=START
find /storage/emulated/0 -type f -name 'ZDIR.BIN' 2>/dev/null |
while IFS= read -r ZDIR; do
  case "$ZDIR" in */NFS/ZDIR.BIN) ;; *) continue ;; esac
  [ "$(stat -c %s "$ZDIR" 2>/dev/null)" = 33312 ] || continue
  HASH=$(sha256sum "$ZDIR" 2>/dev/null | awk '{print $1}')
  [ "$HASH" = "$EXPECTED" ] || continue
  DATA="${ZDIR%/*}/ZZDATA4.BIN"
  echo PRE558_EXACT_TRANSLATED_ZDIR=YES
  if [ -r "$DATA" ]; then
    echo PRE558_ZZDATA4_SIBLING_PRESENT=YES
    echo "PRE558_ZZDATA4_SIBLING_BYTES=$(stat -c %s "$DATA" 2>/dev/null)"
  else
    echo PRE558_ZZDATA4_SIBLING_PRESENT=NO
  fi
  od -An -v -tu4 "$ZDIR" 2>/dev/null | awk -v target="$WANTED" '
    {
      for(i=1;i<=NF;i++) {
        v[n%6]=$i
        n++
        if(n%6==0) {
          if ((v[0]+0)==(target+0)) {
            printf "PRE558_ATTR_ROW=%.0f\n", n/6-1
            printf "PRE558_ATTR_ARCHIVE=%.0f\n", v[1]+0
            printf "PRE558_ATTR_SECTOR=%.0f\n", v[2]+0
            printf "PRE558_ATTR_TOTAL_FIELD=%.0f\n", v[3]+0
            printf "PRE558_ATTR_SIZE_BYTES=%.0f\n", v[4]+0
            printf "PRE558_ATTR_CHECKSUM_U32=%.0f\n", v[5]+0
            printf "PRE558_ATTR_OFFSET_BYTES=%.0f\n", (v[2]+0)*2048
            hits++
          }
        }
      }
    }
    END {
      printf "PRE558_TOTAL_WORDS=%.0f\n",n
      printf "PRE558_TOTAL_ROWS=%.0f\n",n/6
      printf "PRE558_ATTR_MATCHES=%.0f\n",hits
      if(n%6!=0)print "PRE558_PARSE_WARNING=INCOMPLETE_RECORD"
    }'
done
echo PRE558_TRANSLATED_ZDIR_SCAN=END
