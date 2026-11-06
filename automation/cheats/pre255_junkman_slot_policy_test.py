#!/usr/bin/env python3
"""PRE255 synthetic tests only. No save files, Android, or signing."""
from __future__ import annotations
from collections import Counter
from random import Random
from pre255_junkman_slot_policy import plan_token_count, InventoryPolicyError

def must_fail(*args, **kwargs):
    try:
        plan_token_count(*args, **kwargs)
    except InventoryPolicyError:
        return
    raise AssertionError("unsafe invalid plan was accepted")

def tests():
    example=(None, 2, 1, 1, None, 9, None)
    c=plan_token_count(example,1,3,allowed_type_ids={1,2},
                       slot_capacity=7,max_count_per_type=4)
    assert c==(1,2,1,1,None,9,None)
    assert example==(None,2,1,1,None,9,None)
    assert plan_token_count(c,1,3,allowed_type_ids={1,2},
                            slot_capacity=7,max_count_per_type=4)==c
    z=plan_token_count(c,1,0,allowed_type_ids={1,2},
                       slot_capacity=7,max_count_per_type=4)
    assert z==(None,2,None,None,None,9,None)
    must_fail((1,2,3),1,3,allowed_type_ids={1},slot_capacity=3,max_count_per_type=3)
    must_fail((None,2),1,1,allowed_type_ids={2},slot_capacity=2,max_count_per_type=1)
    must_fail((None,2),1,-1,allowed_type_ids={1},slot_capacity=2,max_count_per_type=2)
    must_fail((None,2),1,1,allowed_type_ids={1},slot_capacity=3,max_count_per_type=2)
    must_fail((None,2),1,5,allowed_type_ids={1},slot_capacity=2,max_count_per_type=2)
    must_fail((None,2),True,1,allowed_type_ids={1},slot_capacity=2,max_count_per_type=2)
    must_fail((0,2),1,1,allowed_type_ids={1},slot_capacity=2,max_count_per_type=2)
    must_fail((None,2),1,1,allowed_type_ids={0,1},slot_capacity=2,max_count_per_type=2)
    rng=Random(255)
    cases=20000
    for case in range(cases):
        size=rng.randint(1,80)
        old=tuple(None if rng.random()<.36 else rng.randint(1,15)
                  for _ in range(size))
        target=rng.randint(1,7)
        desired=rng.randint(0,size)
        current=old.count(target); empty=old.count(None)
        if desired>current+empty:
            must_fail(old,target,desired,allowed_type_ids=set(range(1,8)),
                      slot_capacity=size,max_count_per_type=size)
        else:
            result=plan_token_count(old,target,desired,
                                    allowed_type_ids=set(range(1,8)),
                                    slot_capacity=size,max_count_per_type=size)
            assert len(result)==size
            assert result.count(target)==desired
            for x,y in zip(old,result):
                if x is not None and x!=target:assert x==y
            assert Counter(x for x in old if x not in (None,target))==Counter(
                   x for x in result if x not in (None,target))
            assert plan_token_count(result,target,desired,
                   allowed_type_ids=set(range(1,8)),slot_capacity=size,
                   max_count_per_type=size)==result
    print("PRE255_STATUS AUDIT_OK")
    print("PRE255_SYNTHETIC_CASES",cases)
    print("PRE255_REAL_XBOX360_SAVE_FORMAT_VERIFIED",False)
    print("PRE255_GAME_CODE_MODIFIED",False)
    print("PRE255_GAME_SAVE_MODIFIED",False)

if __name__=="__main__":tests()
