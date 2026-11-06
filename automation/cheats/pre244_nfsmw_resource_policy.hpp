#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>

// PRE244: independently testable policy; not connected to the game.
// Unsigned money, nonnegative finite IEEE754 meter inputs.
namespace nfsmw_cheats {
struct Toggles {
    bool money_infinite = false;
    bool nitro_infinite = false;
    bool speedbreaker_infinite = false;
};

inline std::uint32_t preserve_money(bool enabled,
                                    std::uint32_t previous,
                                    std::uint32_t proposed) noexcept {
    if (!enabled) return proposed;
    return proposed < previous ? previous : proposed;
}

inline float f32_from_bits(std::uint32_t bits) noexcept {
    float value;
    static_assert(sizeof(value) == sizeof(bits), "Requires IEEE754 float32");
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}
inline std::uint32_t f32_bits(float value) noexcept {
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

inline std::uint32_t preserve_meter_f32_bits(bool enabled,
                                              std::uint32_t previous_bits,
                                              std::uint32_t proposed_bits) noexcept {
    if (!enabled) return proposed_bits;
    const float previous = f32_from_bits(previous_bits);
    const float proposed = f32_from_bits(proposed_bits);
    // Never rewrite NaN, Inf, negative, or unrecognized meter states.
    if (!std::isfinite(previous) || !std::isfinite(proposed) ||
        previous < 0.0f || proposed < 0.0f) {
        return proposed_bits;
    }
    return proposed < previous ? previous_bits : proposed_bits;
}
} // namespace nfsmw_cheats
