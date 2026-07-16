"""Tiny pricing helpers for the Week 3 CI/CD agent demo.

`item_total` contains a deliberate bug (it adds instead of multiplies) so the
CI build goes red. The agent's job is to find and fix exactly this one line.
"""


def item_total(price, quantity):
    """Total cost of `quantity` units at `price` each."""
    return price * quantity


def apply_tax(amount, rate):
    """Apply a tax `rate` (e.g. 0.08 for 8%) to `amount`, rounded to cents."""
    return round(amount * (1 + rate), 2)
