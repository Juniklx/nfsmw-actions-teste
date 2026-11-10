#!/usr/bin/env python3
"""PRE635: IN-MEMORY reversible proposal for duplicate C3-copy diagnostics.
Input must be a PRE194-authenticated PAL source; does not write a build tree/APK.
The historical PRE99 source is NOT assumed to be identical to running V49.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

PRE194_SHA='a01f25e531af783d37f70a3c3caa0f3e7a979d2bdbdd923abf7b2c6062d29d1e'
MARKER='NFSMW_PRE635_C3_TWOREQUEST_TRACE'
OLD='''    if (indice_fuera || referencia_distinta || copia_duplicada) {
      ApagarEnlaces(fmt::format('''
NEW='''    if (indice_fuera || referencia_distinta || copia_duplicada) {
      // NFSMW_PRE635_C3_TWOREQUEST_TRACE: only log the proven duplicate-copy guard.
      // No pointers or game content are logged; both requested buffer offsets are metadata.
      // Bounds and reference are checked BEFORE consulting the first request's fields.
      if (!indice_fuera && !referencia_distinta && copia_duplicada) {
        const TexturaEnVuelo& primera = en_vuelo_[indice];
        REXLOG_INFO("[NFSMW_PRE635_C3_TWOREQUEST_TRACE] indice={} en_vuelo={} "
                    "frame={} textura_frame={} epoca_ahora={} epoca_primera={} "
                    "offset_primera={} offset_segunda={} mismos_comandos={} "
                    "subir={} trabajo_huella={} datos_bytes={}",
                    indice, en_vuelo_.size(), fotograma_, textura.fotograma,
                    epoca_subida_, primera.copia_epoca,
                    uint64_t(primera.copia_offset), uint64_t(offset),
                    primera.copia_comandos == subida,
                    textura.subir, textura.huella_trabajo, textura.datos.size());
      }
      ApagarEnlaces(fmt::format('''
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def patch_p194(blob:bytes)->bytes:
    if sha(blob)!=PRE194_SHA:raise ValueError('Requires verified PRE194 PAL source; do not assume V49')
    a,b=OLD.encode(),NEW.encode()
    if blob.count(a)!=1 or b in blob:raise ValueError('Missing/duplicated anchor or already patched')
    patched=blob.replace(a,b,1)
    if patched.count(MARKER.encode())!=2 or patched.replace(b,a,1)!=blob:
        raise ValueError('Marker count or exact reversal invalid')
    for marker in (b'ApagarEnlaces(fmt::format(',b'return false;'):
        if patched.count(marker)!=blob.count(marker):
            raise ValueError('C3 safety fallback changed')
    return patched
def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path)
    args=p.parse_args();source=args.source.read_bytes();modified=patch_p194(source)
    try:patch_p194(modified)
    except ValueError:pass
    else:raise RuntimeError('Double-application guard missing')
    print(json.dumps({'stage':'PRE635','status':'DRYRUN_OK',
        'pre194_sha256':sha(source),'proposal_sha256':sha(modified),
        'bytes_before':len(source),'bytes_after':len(modified),
        'patch_applied_to_build_tree':False,'apk_built':False,
        'first_second_guard_metadata_only':True,
        'fallback_preserved':True,'reversible':True,
        'not_proven':'Exact V49 source, runtime C3 cause, or FPS effect'
    },indent=2))
if __name__=='__main__':main()
