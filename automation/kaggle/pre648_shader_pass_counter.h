// PRE648 - fixed-memory shader/pass diagnostic. Never used to change Vulkan commands.
// One C++ source can include this header in an isolated, gated source replay.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace nfsmw::nativo::pre648 {
struct Fila {
  uint32_t categoria = 0;
  uint32_t vs_mas_uno = 0;
  uint32_t ps_mas_uno = 0;  // zero means depth-only / no fragment stage
  uint32_t dibujos = 0;
};
struct Informe {
  uint64_t total = 0;
  uint64_t normales = 0;
  uint64_t cielo_aplazado_emitido = 0;
  uint64_t fuera_de_rango = 0;
  std::array<Fila, 12> primeros{};
};
class ContadorShaderPases {
 public:
  static constexpr uint32_t kVs = 128;
  static constexpr uint32_t kPs = 128;
  static constexpr uint32_t kCategorias = 16;
  static constexpr size_t kCasillas = size_t(kCategorias) * kVs * kPs;
  static constexpr size_t kMemoriaContadores = kCasillas * sizeof(uint32_t);

  // Called only by the native Vulkan ring thread, AFTER vkCmdDraw* was recorded.
  // The sky is counted when it is actually emitted, never when it is deferred.
  void Anotar(uint32_t vs_mas_uno, uint32_t ps_mas_uno,
              uint32_t categoria, bool cielo_aplazado) noexcept {
    if (vs_mas_uno == 0 || vs_mas_uno >= kVs ||
        ps_mas_uno >= kPs || categoria >= kCategorias) {
      ++fuera_de_rango_;
      return;
    }
    const size_t index = (size_t(categoria) * kVs + vs_mas_uno) * kPs + ps_mas_uno;
    ++casillas_[index];
    ++total_;
    if (cielo_aplazado) {
      ++cielo_;
    } else {
      ++normales_;
    }
  }

  // Call at most once per reporting interval on the SAME ring thread.
  // Reports a bounded top 12; exact counts are retained inside the table until here.
  Informe ExtraerYLimpiar() noexcept {
    Informe out;
    out.total = total_;
    out.normales = normales_;
    out.cielo_aplazado_emitido = cielo_;
    out.fuera_de_rango = fuera_de_rango_;
    for (size_t i = 0; i < kCasillas; ++i) {
      const uint32_t n = casillas_[i];
      if (!n) continue;
      casillas_[i] = 0;
      if (n <= out.primeros.back().dibujos) continue;
      Fila item;
      item.categoria = uint32_t(i / (kVs * kPs));
      item.vs_mas_uno = uint32_t((i / kPs) % kVs);
      item.ps_mas_uno = uint32_t(i % kPs);
      item.dibujos = n;
      size_t pos = 0;
      while (pos < out.primeros.size() && out.primeros[pos].dibujos >= n) ++pos;
      if (pos < out.primeros.size()) {
        for (size_t j = out.primeros.size() - 1; j > pos; --j) {
          out.primeros[j] = out.primeros[j - 1];
        }
        out.primeros[pos] = item;
      }
    }
    total_ = normales_ = cielo_ = fuera_de_rango_ = 0;
    return out;
  }

 private:
  // 1 MiB fixed cost; no dynamic allocation, hash table, locks or per-draw logging.
  std::array<uint32_t, kCasillas> casillas_{};
  uint64_t total_ = 0;
  uint64_t normales_ = 0;
  uint64_t cielo_ = 0;
  uint64_t fuera_de_rango_ = 0;
};
static_assert(ContadorShaderPases::kMemoriaContadores == 1048576);
}  // namespace nfsmw::nativo::pre648
