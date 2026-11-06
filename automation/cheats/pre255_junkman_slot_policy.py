#!/usr/bin/env python3
"""PRE255: standalone slot-count planning policy for *hypothetical* Junkman inventory.

No edition-specific save offsets, binary encoding, checksums or raw memory access.
A future Xbox360/PAL adapter must verify real type IDs, capacity, and persistence.
This module never reads or writes a game save.
"""
from __future__ import annotations
from collections import Counter
from typing import Iterable, Optional, Sequence

class InventoryPolicyError(ValueError):
    pass

def _strict_nonnegative(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise InventoryPolicyError(f"{label} must be a nonnegative integer")
    return value

def plan_token_count(
    slots: Sequence[Optional[int]],
    type_id: int,
    desired_count: int,
    *,
    allowed_type_ids: Iterable[int],
    slot_capacity: int,
    max_count_per_type: int,
) -> tuple[Optional[int], ...]:
    """Return an immutable copy with only target-type slots adjusted.

    The caller must supply a proven edition-specific parser. None means a
    confirmed empty slot, not a zero-valued unknown token.
    """
    capacity = _strict_nonnegative(slot_capacity, "slot_capacity")
    limit = _strict_nonnegative(max_count_per_type, "max_count_per_type")
    target = _strict_nonnegative(type_id, "type_id")
    wanted = _strict_nonnegative(desired_count, "desired_count")
    if target == 0:
        raise InventoryPolicyError("type_id zero is reserved")
    if capacity == 0 or len(slots) != capacity:
        raise InventoryPolicyError("slot layout/capacity mismatch")
    if wanted > min(capacity, limit):
        raise InventoryPolicyError("requested count exceeds validated limits")
    allowed = set(allowed_type_ids)
    if target not in allowed:
        raise InventoryPolicyError("target type not validated for this edition")
    if any(type(t) is not int or t <= 0 for t in allowed):
        raise InventoryPolicyError("invalid allowlist entry")
    if any(t is not None and (type(t) is not int or t <= 0)
           for t in slots):
        raise InventoryPolicyError("unknown slot representation")
    out = list(slots)
    owned = [i for i,t in enumerate(out) if t == target]
    if len(owned) > wanted:
        for i in reversed(owned[wanted:]):
            out[i] = None
    elif len(owned) < wanted:
        empty = [i for i,t in enumerate(out) if t is None]
        needed = wanted-len(owned)
        if needed > len(empty):
            raise InventoryPolicyError("insufficient verified empty slots")
        for i in empty[:needed]:
            out[i] = target
    result = tuple(out)
    if Counter(x for x in result if x is not None)[target] != wanted:
        raise AssertionError("unexpected target token count")
    for i,old in enumerate(slots):
        if old is not None and old != target and result[i] != old:
            raise AssertionError("another token was modified")
    return result
