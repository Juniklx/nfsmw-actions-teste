#!/usr/bin/env bash
set -euo pipefail

# Diagnostico publico, exclusivamente sintetico: nao baixa nem compila NFSMW.
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
NDK_REV="28.2.13676358"
NDK="$SDK/ndk/$NDK_REV"
ROOT="${RUNNER_TEMP:-/tmp}/nfsmw_android_diag"

say() { printf '\n=== %s ===\n' "$1"; }
row() { if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then printf '| %s | %s |\n' "$1" "$2" >> "$GITHUB_STEP_SUMMARY"; fi; }

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo '## NFSMW - Android toolchain (teste sintetico, sem jogo)'
    echo ''
    echo '| Item | Resultado |'
    echo '|---|---|'
  } >> "$GITHUB_STEP_SUMMARY"
fi

say 'Ambiente real'
uname -a
printf 'CPUs: '; nproc
free -h
df -h / "${RUNNER_TEMP:-/tmp}"
row 'CPUs logicas' "$(nproc)"
row 'RAM total (KiB)' "$(awk '/MemTotal:/ {print $2}' /proc/meminfo)"
row 'Disco disponivel em / (KiB)' "$(df -Pk / | awk 'NR==2{print $4}')"

say 'Java e Gradle'
java -version 2>&1
printf 'JAVA_HOME=%s\n' "${JAVA_HOME:-nao_definido}"
gradle --version | sed -n '1,18p'
row 'Java' "$(java -version 2>&1 | head -n 1 | tr '|' '/')"
row 'Gradle' "$(gradle --version | awk '/^Gradle / {print $2; exit}')"

say 'SDK Android'
echo "ANDROID_HOME=$SDK"
for rel in 'platforms/android-36/android.jar' 'build-tools/36.0.0/zipalign' 'platform-tools/adb'; do
  if [ -f "$SDK/$rel" ]; then
    echo "[OK] $rel"
    row "$rel" 'encontrado'
  else
    echo "[AUSENTE] $rel"
    row "$rel" 'ausente'
    exit 2
  fi
done

say 'NDK Android exato e CMake'
if [ ! -f "$NDK/build/cmake/android.toolchain.cmake" ]; then
  echo "[AUSENTE] NDK $NDK_REV (nao instalar automaticamente)"
  if [ -d "$SDK/ndk" ]; then ls -1 "$SDK/ndk"; fi
  row "NDK $NDK_REV" 'ausente'
  exit 3
fi
row "NDK $NDK_REV" 'encontrado'
cmake --version | head -n 1
ninja --version
"$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/clang++" --version | head -n 1

say 'Build cruzado C++ Android arm64-v8a, somente sintetico'
mkdir -p "$ROOT/native" "$ROOT/gradle/src/main/java/example"
cat > "$ROOT/native/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.18)
project(nfsmw_android_probe LANGUAGES CXX)
add_library(nfsmw_android_probe SHARED probe.cpp)
target_compile_features(nfsmw_android_probe PRIVATE cxx_std_17)
EOF
cat > "$ROOT/native/probe.cpp" <<'EOF'
#include <cstdint>
extern "C" std::uint64_t nfsmw_android_probe(std::uint64_t x) {
  return (x ^ 0xAA55AA55ULL) + 1;
}
EOF
start=$(date +%s)
cmake -S "$ROOT/native" -B "$ROOT/native/out" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$ROOT/native/out" --parallel "$(nproc)"
end=$(date +%s)
LIB="$ROOT/native/out/libnfsmw_android_probe.so"
test -s "$LIB"
file "$LIB"
readelf -h "$LIB" | grep -F 'AArch64'
row 'CMake/NDK arm64-v8a' 'compilacao concluida; ELF AArch64 confirmado'
row 'CMake/NDK tempo (s)' "$((end-start))"

say 'Gradle Java sintetico (sem Android Gradle Plugin)'
cat > "$ROOT/gradle/settings.gradle.kts" <<'EOF'
rootProject.name = "nfsmw-runner-gradle-diagnostico"
EOF
cat > "$ROOT/gradle/build.gradle.kts" <<'EOF'
plugins { `java-library` }
EOF
cat > "$ROOT/gradle/src/main/java/example/Probe.java" <<'EOF'
package example;
public final class Probe {
  public static int soma(int a, int b) { return a + b; }
}
EOF
start=$(date +%s)
gradle -p "$ROOT/gradle" --offline --no-daemon --max-workers=4 --console=plain classes
end=$(date +%s)
test -s "$ROOT/gradle/build/classes/java/main/example/Probe.class"
row 'Gradle Java sintetico' 'compilacao concluida'
row 'Gradle tempo (s)' "$((end-start))"

say 'Disco depois dos testes'
df -h / "${RUNNER_TEMP:-/tmp}"
row 'Disco livre final em / (KiB)' "$(df -Pk / | awk 'NR==2{print $4}')"
row 'Compilacao real NFSMW' 'nao realizada'
echo '[SUCESSO] Toolchain e builds sinteticos concluídos; sem arquivos privados ou APK.'
