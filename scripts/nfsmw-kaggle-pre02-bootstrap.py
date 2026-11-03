#!/usr/bin/env python3
"""Kaggle PRE02: prepara isoladamente Gradle 9.1.0 e Android command-line tools.

Nao instala SDK packages/NDK ainda, nao aceita licencas automaticamente,
nao monta Google Drive e nao acessa arquivos, APKs ou chaves do NFSMW.
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
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path('/kaggle/working/NFSMW_Kaggle_Toolchain')
LOGDIR = Path('/kaggle/working/NFSMW_Kaggle_Logs')
SDK = ROOT / 'android-sdk'
GRADLE_BIN = ROOT / 'gradle-9.1.0' / 'bin' / 'gradle'
CLI = SDK / 'cmdline-tools' / 'latest' / 'bin' / 'sdkmanager'
ANDROID_URL = 'https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip'
ANDROID_SHA256 = '4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583'
GRADLE_URL = 'https://services.gradle.org/distributions/gradle-9.1.0-bin.zip'
GRADLE_SHA_URL = GRADLE_URL + '.sha256'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(buf)
    return h.hexdigest()


def get(url: str, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + '.part')
    if tmp.exists():
        tmp.unlink()
    req = urllib.request.Request(url, headers={'User-Agent': 'NFSMW-Kaggle-PRE02/1.0'})
    logging.info('Baixando: %s', url)
    try:
        with urllib.request.urlopen(req, timeout=90) as src, tmp.open('wb') as dst:
            shutil.copyfileobj(src, dst, 4 * 1024 * 1024)
        if tmp.stat().st_size < 500_000:
            raise RuntimeError(f'Download inesperadamente pequeno: {tmp.stat().st_size} bytes')
        tmp.replace(path)
        logging.info('Download: %d bytes', path.stat().st_size)
    finally:
        tmp.unlink(missing_ok=True)


def get_remote_sha256(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'NFSMW-Kaggle-PRE02/1.0'})
    with urllib.request.urlopen(req, timeout=45) as f:
        text = f.read(300).decode('ascii').strip()
    hashtext = text.split()[0]
    if not re.fullmatch(r'[0-9a-fA-F]{64}', hashtext):
        raise RuntimeError('Checksum oficial Gradle tem formato inesperado')
    return hashtext.lower()


def extract_official_zip(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts:
                raise RuntimeError('Entrada ZIP insegura: ' + name)
        z.extractall(dest)


def main() -> None:
    ap = argparse.ArgumentParser(description='Instalacao Kaggle PRE02 sem credenciais, sem aceitar licencas automaticamente.')
    ap.add_argument('--concordo-termos-download-android', action='store_true',
                    help='Confirmacao explicita de que usuario leu/aceitou termos Android SDK em https://developer.android.com/studio')
    args = ap.parse_args()
    if not args.concordo_termos_download_android:
        sys.exit('Leia https://developer.android.com/studio e execute novamente com '
                 '--concordo-termos-download-android somente apos concordar com os termos de download.')

    LOGDIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGDIR / ('LOG_NFSMW_KAGGLE_PRE02_BOOTSTRAP_' + time.strftime('%Y%m%d_%H%M%S', time.gmtime()) + '.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding='utf-8')])
    logging.info('INICIO PRE02 | ferramenta somente de ambiente | log=%s', log_path)
    try:
        if sys.platform != 'linux' or os.uname().machine != 'x86_64':
            raise RuntimeError('Este bootstrap foi preparado apenas para Linux x86_64')
        if not Path('/kaggle/working').is_dir():
            raise RuntimeError('Diretorio /kaggle/working nao encontrado')
        ROOT.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(ROOT).free
        logging.info('Espaco disponivel em /kaggle/working: %.2f GiB', free / 1024 ** 3)
        if free < 5 * 1024 ** 3:
            raise RuntimeError('Espaco abaixo de 5 GiB; parar antes do download')
        logging.info('SDK=%s; Gradle=%s', SDK, GRADLE_BIN)
        with tempfile.TemporaryDirectory(prefix='nfsmw_pre02_', dir=str(ROOT)) as td:
            tmp = Path(td)
            if not CLI.is_file():
                zip_file = tmp / 'android-cli.zip'
                get(ANDROID_URL, zip_file)
                actual = sha256(zip_file)
                if actual != ANDROID_SHA256:
                    raise RuntimeError(f'Checksum Android CLI divergente: {actual}')
                logging.info('[OK] SHA256 oficial Android CLI: %s', actual)
                staged = tmp / 'android-staging'
                extract_official_zip(zip_file, staged)
                src = staged / 'cmdline-tools'
                if not (src / 'bin' / 'sdkmanager').is_file():
                    raise RuntimeError('Estrutura oficial cmdline-tools inesperada')
                dest = SDK / 'cmdline-tools' / 'latest'
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    raise RuntimeError('Existe instalacao CLI incompleta; auditar manualmente: ' + str(dest))
                shutil.move(str(src), str(dest))
                logging.info('[OK] Android commandline tools em %s', dest)
            else:
                logging.info('[OK] Android CLI ja existe: %s', CLI)
            if not GRADLE_BIN.is_file():
                expected = get_remote_sha256(GRADLE_SHA_URL)
                logging.info('SHA256 Gradle oficial obtido em %s: %s', GRADLE_SHA_URL, expected)
                zip_file = tmp / 'gradle.zip'
                get(GRADLE_URL, zip_file)
                actual = sha256(zip_file)
                if actual != expected:
                    raise RuntimeError(f'Checksum Gradle divergente: {actual}')
                logging.info('[OK] SHA256 Gradle: %s', actual)
                extract_official_zip(zip_file, ROOT)
                if not GRADLE_BIN.is_file():
                    raise RuntimeError('Gradle nao foi encontrado apos extracao')
            else:
                logging.info('[OK] Gradle ja existe: %s', GRADLE_BIN)
        os.environ['ANDROID_HOME'] = str(SDK)
        os.environ['ANDROID_SDK_ROOT'] = str(SDK)
        os.environ['GRADLE_USER_HOME'] = str(ROOT / '.gradle')
        os.environ['PATH'] = f"{GRADLE_BIN.parent}:{CLI.parent}:" + os.environ.get('PATH', '')
        for cmd in ([str(GRADLE_BIN), '--version'], [str(CLI), '--version']):
            out = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
            if out.returncode:
                raise RuntimeError(f'Falhou teste comando {cmd}:\n{out.stdout[-2000:]}')
            logging.info('[OK] %s: %s', cmd[0], out.stdout[:500].strip())
        logging.info('DISCO FINAL: %.2f GiB disponiveis', shutil.disk_usage(ROOT).free / 1024**3)
        logging.info('[SUCESSO] PRE02 instalou CLI e Gradle 9.1; NAO instalou NDK, NAO aceitou licencas, NAO gerou APK.')
        logging.info('PROXIMO: examinar termos Android SDK e usar sdkmanager --licenses de forma explicita antes de instalar Android 36 e NDK r28c.')
        logging.info('LOG=%s', log_path)
    except Exception as e:
        logging.exception('[FALHA] %s', e)
        logging.info('LOG=%s', log_path)
        raise


if __name__ == '__main__':
    main()
