#include "pre244_nfsmw_resource_policy.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>

int main() {
    using namespace nfsmw_cheats;
    Toggles flags;
    assert(!flags.money_infinite && !flags.nitro_infinite && !flags.speedbreaker_infinite);
    assert(preserve_money(false, 50, 0) == 0);
    assert(preserve_money(true, 50, 0) == 50);
    assert(preserve_money(true, 50, 100) == 100);
    assert(preserve_money(true, 0, 100) == 100);
    assert(preserve_meter_f32_bits(false, f32_bits(5.0f), f32_bits(0.0f)) == f32_bits(0.0f));
    assert(preserve_meter_f32_bits(true, f32_bits(5.0f), f32_bits(0.0f)) == f32_bits(5.0f));
    assert(preserve_meter_f32_bits(true, f32_bits(5.0f), f32_bits(8.0f)) == f32_bits(8.0f));
    assert(preserve_meter_f32_bits(true, f32_bits(-1.0f), f32_bits(0.0f)) == f32_bits(0.0f));
    assert(preserve_meter_f32_bits(true, f32_bits(8.0f), f32_bits(-1.0f)) == f32_bits(-1.0f));
    const auto nan = f32_bits(std::numeric_limits<float>::quiet_NaN());
    assert(preserve_meter_f32_bits(true, nan, f32_bits(1.0f)) == f32_bits(1.0f));
    assert(preserve_meter_f32_bits(true, f32_bits(1.0f), nan) == nan);
    assert(preserve_meter_f32_bits(true, f32_bits(1.0f),
        f32_bits(std::numeric_limits<float>::infinity())) ==
        f32_bits(std::numeric_limits<float>::infinity()));
    std::mt19937 gen(0x1ABE42u);
    for (int i = 0; i < 100000; ++i) {
        std::uint32_t old = gen(), val = gen();
        assert(preserve_money(false, old, val) == val);
        assert(preserve_money(true, old, val) >= old);
        const float f_old = static_cast<float>(old % 100000) / 100.0f;
        const float f_new = static_cast<float>(val % 100000) / 100.0f;
        auto f_o = f32_bits(f_old), f_n = f32_bits(f_new);
        assert(preserve_meter_f32_bits(false, f_o, f_n) == f_n);
        auto actual = f32_from_bits(preserve_meter_f32_bits(true, f_o, f_n));
        assert(actual >= f_old);
        assert(actual == (f_new < f_old ? f_old : f_new));
    }
    std::cout << "PRE244_SYNTHETIC_100000_OK\n";
}
