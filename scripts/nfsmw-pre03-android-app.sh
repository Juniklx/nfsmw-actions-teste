#!/usr/bin/env bash
set -euo pipefail

# PRE03: projeto Android COMPLETAMENTE SINTETICO. Sem arquivos ou credenciais de NFSMW.
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
NDK_VERSION="28.2.13676358"
ROOT="${RUNNER_TEMP:-/tmp}/nfsmw_pre03_synthetic_app"
mkdir -p "$ROOT/app/src/main/java/dev/nfsmw/pre03" "$ROOT/app/src/main/cpp"

cat > "$ROOT/settings.gradle.kts" <<'EOF'
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "NFSMW-PRE03-Synthetic-App"
include(":app")
EOF

cat > "$ROOT/build.gradle.kts" <<'EOF'
plugins {
    id("com.android.application") version "9.0.1" apply false
}
EOF

cat > "$ROOT/gradle.properties" <<'EOF'
org.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=768m -Dfile.encoding=UTF-8
org.gradle.parallel=false
android.useAndroidX=true
EOF

cat > "$ROOT/app/build.gradle.kts" <<'EOF'
plugins {
    id("com.android.application")
}

android {
    namespace = "dev.nfsmw.pre03"
    compileSdk = 36
    buildToolsVersion = "36.0.0"
    ndkVersion = "28.2.13676358"

    defaultConfig {
        applicationId = "dev.nfsmw.pre03"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1"
        ndk { abiFilters += "arm64-v8a" }
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
}
EOF

cat > "$ROOT/app/src/main/AndroidManifest.xml" <<'EOF'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="PRE03 Synthetic" android:hasCode="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
EOF

cat > "$ROOT/app/src/main/java/dev/nfsmw/pre03/MainActivity.java" <<'EOF'
package dev.nfsmw.pre03;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public final class MainActivity extends Activity {
    static { System.loadLibrary("nfsmw_pre03_probe"); }
    private static native long probe(long value);

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        TextView text = new TextView(this);
        text.setText("PRE03 Android synthetic JNI: " + probe(7));
        setContentView(text);
    }
}
EOF

cat > "$ROOT/app/src/main/cpp/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.22)
project(nfsmw_pre03_probe LANGUAGES CXX)
add_library(nfsmw_pre03_probe SHARED probe.cpp)
target_compile_features(nfsmw_pre03_probe PRIVATE cxx_std_17)
EOF

cat > "$ROOT/app/src/main/cpp/probe.cpp" <<'EOF'
#include <jni.h>

extern "C" JNIEXPORT jlong JNICALL
Java_dev_nfsmw_pre03_MainActivity_probe(JNIEnv*, jclass, jlong value) {
    return value + 42;
}
EOF

printf '\n=== PRE03: recursos e toolchain ===\n'
java -version 2>&1 | head -n 3
gradle --version | grep -E '^Gradle |^Launcher JVM:' || true
printf 'CPUs: '; nproc
free -h
df -h / "$SDK"
test -f "$SDK/ndk/$NDK_VERSION/build/cmake/android.toolchain.cmake"
test -f "$SDK/platforms/android-36/android.jar"
test -f "$SDK/build-tools/36.0.0/aapt"

echo '=== PRE03: Gradle AGP 9.0.1 Android release SEM ASSINATURA (sintetico) ==='
START=$(date +%s)
gradle -p "$ROOT" --no-daemon --console=plain --max-workers=4 --stacktrace :app:assembleRelease
ELAPSED=$(( $(date +%s) - START ))

mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/release" -maxdepth 1 -type f -name '*.apk' | sort)
if [ "${#APKS[@]}" -ne 1 ]; then
    echo "[ERRO] quantidade de APKs inesperada: ${#APKS[@]}"
    exit 30
fi
APK="${APKS[0]}"
LIB="lib/arm64-v8a/libnfsmw_pre03_probe.so"
unzip -Z -1 "$APK" | grep -Fx "$LIB" >/dev/null || { echo '[ERRO] JNI arm64 nao empacotada'; exit 31; }
unzip -p "$APK" "$LIB" > "$ROOT/pre03_check.so"
test -s "$ROOT/pre03_check.so"
file "$ROOT/pre03_check.so"
readelf -h "$ROOT/pre03_check.so" | grep -F 'AArch64'
"$SDK/build-tools/36.0.0/aapt" dump badging "$APK" | head -n 3
sha256sum "$APK"
ls -lh "$APK"
df -h / "$SDK"

# Este APK demonstrativo nao deve ser instalado como NFSMW nem tratado como release assinada.
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    {
        echo '## PRE03 - aplicativo Android totalmente sintetico'
        echo ''
        echo '| Verificacao | Resultado |'
        echo '|---|---|'
        echo '| AGP | 9.0.1 |'
        echo '| Gradle | 9.1.0 |'
        echo '| Android compileSdk | 36 |'
        echo '| NDK | 28.2.13676358 |'
        echo '| Arquitetura JNI | arm64-v8a (AArch64 confirmado) |'
        echo '| APK sintetico | Gerado (release unsigned, sem credenciais) |'
        echo "| Gradle :app:assembleRelease | ${ELAPSED} segundos |"
        echo "| APK bytes | $(stat -c '%s' "$APK") |"
        echo "| SHA256 APK | $(sha256sum "$APK" | awk '{print $1}') |"
        echo '| NFSMW real | Nao compilado |'
    } >> "$GITHUB_STEP_SUMMARY"
fi

echo "[PRE03] SUCESSO: Android Java + AGP + CMake/NDK + JNI AArch64; tempo=${ELAPSED}s; APK sintetico SEM ASSINATURA"
