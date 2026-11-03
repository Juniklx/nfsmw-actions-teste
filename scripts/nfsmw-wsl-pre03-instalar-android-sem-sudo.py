#!/usr/bin/env python3
"""NFSMW WSL PRE03: Android SDK/NDK no perfil do usuario (sem sudo).

Somente no Ubuntu WSL2 x86_64, apos PRE02. Nao acessa NFSMW, APKs,
keystore, senhas, tokens, Google Drive ou arquivos fora de toolchain/logs.
Requer --instalar --aceito-licencas para aceitar licencas e instalar SDK.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
BASE = HOME / 'NFSMW_Android_Toolchain'
SDK = BASE / 'android-sdk'
SDKM = SDK / 'cmdline-tools/latest/bin/sdkmanager'
GRADLE = BASE / 'gradle-9.1.0/bin/gradle'
LOGDIR = HOME / 'NFSMW_Android_Logs'
PACOTES = [
    'platforms;android-36',
    'build-tools;36.0.0',
    'platform-tools',
    'ndk;28.2.13676358',
]
VERIFICAR = {
    'Android Platform 36': SDK / 'platforms/android-36/android.jar',
    'Build Tools 36.0.0': SDK / 'build-tools/36.0.0/zipalign',
    'ADB (Platform Tools)': SDK / 'platform-tools/adb',
    'NDK r28c CMake toolchain': SDK / 'ndk/28.2.13676358/build/cmake/android.toolchain.cmake',
    'NDK Clang++ ARM64': SDK / 'ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/clang++',
}


def tamanho_gib(n: int) -> str:
    return f'{n / 2**30:.2f} GiB'


def preflight() -> dict:
    if sys.platform != 'linux' or os.uname().machine != 'x86_64' or 'microsoft' not in os.uname().release.lower():
        raise RuntimeError('PRE03 foi preparado para Ubuntu Linux x86_64 em WSL2')
    if os.geteuid() == 0:
        raise RuntimeError('Nao execute este script como root')
    if not os.access(HOME, os.W_OK):
        raise RuntimeError('HOME nao permite escrita ao usuario')
    if not SDKM.is_file() or not GRADLE.is_file():
        raise RuntimeError('PRE02 incompleto: sdkmanager ou Gradle 9.1.0 ausente')
    disk_linux = shutil.disk_usage(HOME)
    print('=== NFSMW WSL PRE03 - PREFLIGHT ===', flush=True)
    print('Usuario UID:', os.geteuid(), flush=True)
    print('Gradle:', GRADLE, flush=True)
    print('SDK Manager:', SDKM, flush=True)
    print('HOME livre no VHD (virtual):', tamanho_gib(disk_linux.free), flush=True)
    win = Path('/mnt/c')
    if win.is_dir():
        try:
            physical = shutil.disk_usage(win).free
            print('Windows C: espaco livre estimado:', tamanho_gib(physical), flush=True)
            if physical < 15 * 2**30:
                raise RuntimeError('Menos de 15 GiB livres no Windows C:; instalacao recusada')
        except OSError:
            print('[AVISO] Nao foi possivel medir C:. Conferir espaco fisico manualmente.', flush=True)
    if disk_linux.free < 15 * 2**30:
        raise RuntimeError('Menos de 15 GiB livres no filesystem Linux')
    print('Pacotes exatos solicitados:', *PACOTES, sep='\n  - ', flush=True)
    estados = {nome: caminho.is_file() for nome, caminho in VERIFICAR.items()}
    print('Estado atual:', *[f'  {nome}: {"OK" if ok else "AUSENTE"}' for nome, ok in estados.items()], sep='\n', flush=True)
    return estados


def executar(cmd: list[str], logfile: Path, *, data: str | None, timeout: int) -> int:
    with logfile.open('a', encoding='utf-8') as f:
        f.write(f'\n=== COMANDO: {cmd[0]} {" ".join(cmd[1:])} ===\n')
        f.flush()
        try:
            run = subprocess.run(cmd, input=data, stdin=subprocess.DEVNULL if data is None else None,
                                 stdout=f, stderr=subprocess.STDOUT, text=True,
                                 timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            f.write('\n[FALHA] Tempo maximo da operacao ultrapassado\n')
            return 124
        f.write(f'\n[EXIT] {run.returncode}\n')
    return run.returncode


def resumo_log(p: Path) -> None:
    print('\n=== FINAL DO LOG ===')
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    for line in lines[-24:]:
        print(line[-400:])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instalar', action='store_true', help='Instalar apenas os 4 pacotes Android descritos acima')
    parser.add_argument('--aceito-licencas', action='store_true',
                        help='Confirmo que li e aceito as licencas Android SDK solicitadas no sdkmanager')
    args = parser.parse_args()
    estados = preflight()
    if not args.instalar:
        print('[PRE03] DIAGNOSTICO CONCLUIDO, sem alteracoes.', flush=True)
        return 0
    if not args.aceito_licencas:
        raise RuntimeError('Para instalar e aceitar licencas, confirme explicitamente --aceito-licencas')
    LOGDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    log = LOGDIR / f'LOG_NFSMW_WSL_PRE03_{ts}.log'
    report = LOGDIR / f'RELATORIO_NFSMW_WSL_PRE03_{ts}.json'
    result = {'etapa': 'WSL_PRE03', 'status': 'erro', 'data_utc': datetime.now(timezone.utc).isoformat(),
              'pacotes_solicitados': PACOTES, 'sdk': str(SDK), 'log': str(log),
              'modificou_nfsmw': False, 'usou_sudo': False, 'usou_assinatura': False}
    begin = time.monotonic()
    try:
        print('=== LICENCAS DO ANDROID SDK ===', flush=True)
        # Aceitacao automatizada e permitida apenas com a opcao explicita --aceito-licencas.
        # Para instalar no perfil, nao usar sudo nem modificar /usr ou /opt.
        code = executar([str(SDKM), f'--sdk_root={SDK}', '--licenses'], log,
                        data='y\n' * 80, timeout=600)
        print('Licencas: codigo de saida', code, flush=True)
        if code != 0:
            raise RuntimeError(f'SDK Manager licencas retornou {code}')
        print('=== INSTALANDO OS QUATRO PACOTES ===', flush=True)
        code = executar([str(SDKM), f'--sdk_root={SDK}', '--install', *PACOTES], log,
                        data=None, timeout=3600)
        print('Instalacao: codigo de saida', code, flush=True)
        if code != 0:
            raise RuntimeError(f'Instalacao SDK Manager retornou {code}')
        missing = [nome for nome, caminho in VERIFICAR.items() if not caminho.is_file()]
        for nome, caminho in VERIFICAR.items():
            print(f'{nome}: {"OK" if caminho.is_file() else "AUSENTE"}', flush=True)
        if missing:
            raise RuntimeError('Componentes ausentes apos instalacao: ' + '; '.join(missing))
        # Registra a versao do NDK declarada pelo pacote (sem alterar nada).
        props = SDK / 'ndk/28.2.13676358/source.properties'
        version = next((m.group(1) for line in props.read_text(errors='replace').splitlines()
                        if (m := re.match(r'^\s*Pkg\.Revision\s*=\s*(\S+)', line))), None) if props.is_file() else None
        if version != '28.2.13676358':
            raise RuntimeError('Pkg.Revision do NDK ausente ou diferente: ' + str(version))
        result['ndk_revision'] = version
        result['status'] = 'sucesso'
        print('[SUCESSO] WSL PRE03: SDK 36, Build Tools 36, Platform Tools e NDK 28.2 completos.', flush=True)
        return 0
    except Exception as exc:
        result['erro'] = f'{type(exc).__name__}: {exc}'
        print('[FALHA]', result['erro'], flush=True)
        return 1
    finally:
        result['disco_livre_home_gib'] = round(shutil.disk_usage(HOME).free / 2**30, 2)
        result['duracao_segundos'] = round(time.monotonic() - begin, 2)
        result['componentes'] = {nome: caminho.is_file() for nome, caminho in VERIFICAR.items()}
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if log.is_file():
            resumo_log(log)
        print('Log:', log, flush=True)
        print('Relatorio:', report, flush=True)
        print('Resultado:', result['status'], flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
