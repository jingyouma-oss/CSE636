from pricing import item_total, apply_tax


def test_item_total():
    # 4 units at $3.00 should cost $12.00. Fails while item_total adds.
    assert item_total(3.0, 4) == 12.0


def test_apply_tax():
    assert apply_tax(100.0, 0.08) == 108.0
