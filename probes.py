"""probes.py -- the frozen probe families and the closed-form reference.

The reference is analytic. It calls no quadrature routine and shares no code
with any implementation under test, which is the independence criterion the
silent-failure study used.
"""

import math

# Declared in SCOPE.md before measurement. Do not extend without recording why.
WIDTHS = [1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8, 1e-10, 1e-12]

A, B = -1.0, 1.0          # integration interval, both families
OFFSET = 1.0 / 3.0        # centre of the off-centre family

FAMILIES = ("centred", "offcentre")


def centre_of(family):
    return 0.0 if family == "centred" else OFFSET


def integrand(family, w):
    """f_w(x) = exp(-((x - c)/w)^2). Returned as a plain Python callable so
    every adapter drives the identical function."""
    c = centre_of(family)

    def f(x):
        t = (x - c) / w
        # exp underflows to 0.0 well before t^2 overflows; guard anyway so the
        # integrand never raises, which would be a loud failure of the probe
        # rather than of the routine.
        if t > 40.0 or t < -40.0:
            return 0.0
        return math.exp(-t * t)

    return f


def exact(family, w):
    """Closed form. erf is from the C library via math, not from any
    quadrature package."""
    c = centre_of(family)
    return 0.5 * w * math.sqrt(math.pi) * (
        math.erf((B - c) / w) + math.erf((c - A) / w)
    )


def cases():
    for family in FAMILIES:
        for w in WIDTHS:
            yield family, w


if __name__ == "__main__":
    print(f"{'family':10} {'width':>8}  {'exact':>22}")
    for family, w in cases():
        print(f"{family:10} {w:8.0e}  {exact(family, w):22.15e}")
