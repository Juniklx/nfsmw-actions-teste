#!/usr/bin/env python3
"""NFSMW WSL PRE02 — bootstrap de Gradle/Android CLI sem sudo.

Somente para Ubuntu WSL2 x86_64 com permissao de instalar ferramentas no
perfil do usuario. Nao acessa NFSMW, credenciais, chaves, APKs ou Drive.
Nao aceita licencas SDK automaticamente nem instala NDK ainda.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path.home() / 'NFSMW_Android_Toolchain'
LOGDIR = Path.home() / 'NFSMW_Android_Logs'
SDK = ROOT / 'android-sdk'
CLI = SDK / 'cmdline-tools' / 'latest' / 'bin' / 'sdkmanager'
GRADLE = ROOT / 'gradle-9.1.0' / 'bin' / 'gradle'
CLI_URL = 'https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip'
CLI_SHA = '4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583'
GRADLE_URL = 'https://services.gradle.org/distributions/gradle-9.1.0-bin.zip'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fp:
        for block in iter(lambda: fp.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_expected_gradle_sha() -> str:
    req = urllib.request.Request(GRADLE_URL + '.sha256', headers={'User-Agent': 'NFSMW-WSL-PRE02/1.0'})
    with urllib.request.urlopen(req, timeout=90) as stream:
        text = stream.read(200).decode('ascii').strip()
    checksum = text.split()[0].lower()
    if not re.fullmatch(r'[0-9a-f]{64}', checksum):
        raise RuntimeError('SHA256 Gradle oficial com formato inesperado')
    return checksum


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': 'NFSMW-WSL-PRE02/1.0'})
    logging.info('Baixando URL oficial: %s', url)
    with urllib.request.urlopen(req, timeout=120) as src, path.open('wb') as dst:
        shutil.copyfileobj(src, dst, length=4*1024*1024)
    logging.info('Recebidos %s bytes', path.stat().st_size)
    if path.stat().st_size < 500_000:
        raise RuntimeError('Download incompleto ou inesperadamente pequeno')


def extract_zip_safe(path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as zp:
        for member in zp.infolist():
            p = PurePosixPath(member.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in member.filename:
                raise RuntimeError('Entrada insegura no ZIP: ' + member.filename[:120])
            unix_type = (member.external_attr >> 16) & 0o170000
            if unix_type not in (0, 0o040000, 0o100000):
                raise RuntimeError('ZIP inclui tipo de arquivo nao permitido')
        zp.extractall(target)


def inspect() -> None:
    print('=== NFSMW WSL PRE02 — PREFLIGHT ===')
    print('Sistema:', sys.platform, os.uname().machine, os.uname().release)
    print('Usuario UID:', os.getuid())
    print('HOME:', Path.home())
    print('JAVA:', shutil.which('java'))
    print('CMake:', shutil.which('cmake'))
    print('Ninja:', shutil.which('ninja'))
    print('Gradle local:', GRADLE.is_file())
    print('SDK Manager local:', CLI.is_file())
    print('Livre no HOME (GiB - WSL VHD virtual):', round(shutil.disk_usage(Path.home()).free/2**30, 2))
    if 'microsoft' not in os.uname().release.lower() or sys.platform != 'linux' or os.uname().machine != 'x86_64':
        raise RuntimeError('Este script foi preparado apenas para Ubuntu WSL2 x86_64')
    if not os.access(Path.home(), os.W_OK):
        raise RuntimeError('Sem escrita no HOME do WSL')
    if shutil.which('java') is None:
        raise RuntimeError('Java nao encontrado no WSL')
    if (ROOT / 'gradle-9.1.0').exists() and not GRADLE.is_file():
        raise RuntimeError('Gradle parcialmente instalado; auditar sem sobrescrever: ' + str(ROOT / 'gradle-9.1.0'))
    if (SDK / 'cmdline-tools/latest').exists() and not CLI.is_file():
        raise RuntimeError('Android CLI parcialmente instalada; auditar sem sobrescrever')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bootstrap', action='store_true', help='Baixar e instalar apenas Gradle e Android CLI, sem sudo')
    args = ap.parse_args()
    inspect()
    if not args.bootstrap:
        print('[PRE02] Modo somente leitura; para instalar use --bootstrap APOS autorizar instalacao e ler termos Android SDK.')
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGDIR / ('LOG_NFSMW_WSL_PRE02_' + time.strftime('%Y%m%d_%H%M%S', time.gmtime()) + '.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding='utf-8')])
    logging.info('Iniciando bootstrap, sem sudo, em %s', ROOT)
    try:
        if shutil.disk_usage(Path.home()).free < 8 * 1024**3:
            raise RuntimeError('HOME WSL abaixo de 8 GiB livres')
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='wsl_pre02_') as t:
            tmp = Path(t)
            if not CLI.is_file():
                archive = tmp / 'cli.zip'
                download(CLI_URL, archive)
                current = sha256(archive)
                if current != CLI_SHA:
                    raise RuntimeError('SHA256 Android CLI divergente: ' + current)
                logging.info('[OK] CLI SHA256 %s', current)
                stage = tmp / 'cli-stage'
                extract_zip_safe(archive, stage)
                source = stage / 'cmdline-tools'
                if not (source / 'bin/sdkmanager').is_file():
                    raise RuntimeError('SDK Manager ausente no ZIP oficial')
                destination = SDK / 'cmdline-tools' / 'latest'
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    raise RuntimeError('Destino CLI ja existe; nao sobrescrever')
                shutil.move(str(source), str(destination))
                for f in (destination / 'bin').iterdir():
                    if f.is_file():
                        f.chmod(f.stat().st_mode | 0o111)
            else:
                logging.info('[OK] CLI encontrada; download pulado')
            if not GRADLE.is_file():
                expected = read_expected_gradle_sha()
                archive = tmp / 'gradle.zip'
                download(GRADLE_URL, archive)
                current = sha256(archive)
                if current != expected:
                    raise RuntimeError('SHA256 Gradle divergente: ' + current)
                logging.info('[OK] Gradle SHA256 %s', current)
                stage = tmp / 'gradle-stage'
                extract_zip_safe(archive, stage)
                source = stage / 'gradle-9.1.0'
                if not (source / 'bin/gradle').is_file():
                    raise RuntimeError('Gradle ausente no ZIP oficial')
                destination = ROOT / 'gradle-9.1.0'
                if destination.exists():
                    raise RuntimeError('Destino Gradle ja existe; nao sobrescrever')
                shutil.move(str(source), str(destination))
                GRADLE.chmod(GRADLE.stat().st_mode | 0o111)
            else:
                logging.info('[OK] Gradle encontrado; download pulado')
        env_file = ROOT / 'env.sh'
        if not env_file.exists():
            env_file.write_text(
                '#!/usr/bin/env bash\n'
                'export ANDROID_HOME="$HOME/NFSMW_Android_Toolchain/android-sdk"\n'
                'export ANDROID_SDK_ROOT="$ANDROID_HOME"\n'
                'export GRADLE_USER_HOME="$HOME/NFSMW_Android_Toolchain/.gradle"\n'
                'export PATH="$HOME/NFSMW_Android_Toolchain/gradle-9.1.0/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"\n',
                encoding='utf-8')
        for label, cmd in [('Gradle 9.1.0', [str(GRADLE),'--version']),
                           ('Android SDK Manager', [str(CLI),'--version'])]:
            done = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, timeout=120, check=False)
            logging.info('%s exit=%s: %s', label, done.returncode, done.stdout[:850].strip())
            if done.returncode:
                raise RuntimeError('Falha de execucao: ' + label)
        logging.info('[SUCESSO] WSL PRE02 Gradle e Android CLI. SDK 36/NDK ainda NAO instalados.')
        logging.info('LOG: %s', log_file)
        logging.info('Ambiente para futura sessao: source "$HOME/NFSMW_Android_Toolchain/env.sh"')
    except Exception as exc:
        logging.exception('[FALHA] %s', exc)
        logging.info('LOG: %s', log_file)
        raise


if __name__ == '__main__':
    main()
