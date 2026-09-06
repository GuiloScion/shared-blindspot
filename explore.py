"""explore.py -- a playground for breaking the result.

Nothing here is part of the frozen study. run.py and analyse.py produce the
reported numbers; this file is for poking at them. Change the CAPITALISED knobs
at the top of each experiment and re-run.

    python explore.py          # run all four
    python explore.py 2        # run just experiment 2

Each experiment prints what scipy returns, what the truth is, and whether the
routine noticed. "SILENT" always means: wrong, and said nothing.
"""

import math
import sys
import warnings

from scipy.integrate import quad
import mpmath


# ---------------------------------------------------------------- plumbing
def ask(f, a, b, **kw):
    """Run scipy.quad and report whether it complained. Warnings are captured
    rather than printed so the output stays a table."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            value, claimed = quad(f, a, b, **kw)
            return value, claimed, len(caught) > 0, None
        except Exception as exc:                        # noqa: BLE001
            return None, None, True, str(exc)


def verdict(value, truth, warned, tol=1e-3):
    if value is None:
        return "loud (raised)"
    if truth == 0:
        return "n/a"
    rel = abs(value - truth) / abs(truth)
    if rel <= tol:
        return "ok"
    return "loud" if warned else "SILENT"


def row(label, value, truth, warned):
    got = "raised" if value is None else f"{value:.6e}"
    print(f"  {label:<26} got {got:>14}   truth {truth:14.6e}   "
          f"{verdict(value, truth, warned)}")


# ============================================================ EXPERIMENT 1
def experiment_1_move_the_bump():
    """MOVE IT. Was passing ever about robustness, or just about where the
    bump happened to sit?

    The study found adaptive Simpson passed every centred case and failed
    off-centre. Here is the same effect in scipy: slide the bump across the
    interval at a fixed width and watch the verdict flip depending on nothing
    but position."""
    WIDTH = 1e-3                       # <-- knob: how narrow the bump is
    #      1e-3 straddles scipy's limit, so some centres pass and some
    #      do not. Set it to 1e-4 and every centre fails; 1e-2 and all pass.
    CENTRES = [0.0, 0.1, 1/3, 0.5, 0.7071, 0.9]   # <-- knob: where it sits

    print("\n=== 1. MOVE THE BUMP (width fixed at "
          f"{WIDTH:.0e}, only the centre changes) ===")
    for c in CENTRES:
        def f(x, c=c):
            t = (x - c) / WIDTH
            return math.exp(-t * t) if abs(t) < 40 else 0.0
        truth = 0.5 * WIDTH * math.sqrt(math.pi) * (
            math.erf((1 - c) / WIDTH) + math.erf((c + 1) / WIDTH))
        v, _, w, _ = ask(f, -1.0, 1.0)
        row(f"centre = {c:.4f}", v, truth, w)
    print("  -> at this width position alone decides it: same function,")
    print("     same tolerance, verdict flips on where the mass sits.")


# ============================================================ EXPERIMENT 2
def experiment_2_change_the_shape():
    """CHANGE IT. Is the agreement-in-failure specific to Gaussian bumps?

    This is the biggest gap in the study as published -- REPORT.md lists
    'one integrand shape' as the first limitation. Here are three other
    shapes with known exact integrals. If they behave the same way, that
    limitation is smaller than it looks; if they don't, that is a finding."""
    W = 1e-6                           # <-- knob: feature width
    C = 1/3                            # <-- knob: feature location

    print(f"\n=== 2. CHANGE THE SHAPE (width {W:.0e}, centre {C:.4f}) ===")

    # (a) triangular spike: height 1, half-width W  -> area = W
    def spike(x):
        d = abs(x - C)
        return max(0.0, 1.0 - d / W)

    # (b) rectangular pulse: height 1 on [C-W, C+W] -> area = 2W
    def box(x):
        return 1.0 if abs(x - C) <= W else 0.0

    # (c) Lorentzian / Cauchy bump, width W -> area = W*(atan((1-C)/W)+atan((1+C)/W))
    def lorentz(x):
        return 1.0 / (1.0 + ((x - C) / W) ** 2)

    cases = [
        ("triangular spike", spike, W),
        ("rectangular pulse", box, 2 * W),
        ("Lorentzian", lorentz,
         W * (math.atan((1 - C) / W) + math.atan((1 + C) / W))),
    ]
    for name, f, truth in cases:
        v, _, w, _ = ask(f, -1.0, 1.0)
        row(name, v, truth, w)
    print("  -> if these are SILENT too, the 'one shape' limitation shrinks.")


# ============================================================ EXPERIMENT 3
def experiment_3_widen_the_interval():
    """WIDEN IT. Is it the bump's absolute width that matters, or its width
    relative to the interval being searched?

    Hold the bump fixed and stretch the interval. If the failure tracks the
    ratio rather than the width, that tells you the mechanism is sampling
    density, not floating-point."""
    WIDTH = 1e-3                       # <-- knob: bump width, held FIXED
    HALF_WIDTHS = [1, 10, 100, 1000]   # <-- knob: interval is [-H, +H]
    C = 0.0                            # centred, so it stays inside every span

    print(f"\n=== 3. WIDEN THE INTERVAL (bump fixed at width {WIDTH:.0e}) ===")
    for H in HALF_WIDTHS:
        def f(x):
            t = (x - C) / WIDTH
            return math.exp(-t * t) if abs(t) < 40 else 0.0
        truth = 0.5 * WIDTH * math.sqrt(math.pi) * (
            math.erf((H - C) / WIDTH) + math.erf((C + H) / WIDTH))
        v, _, w, _ = ask(f, -float(H), float(H))
        row(f"interval [-{H}, {H}]  ratio 1:{int(2*H/WIDTH):,}", v, truth, w)
    print("  -> the knob is the RATIO of feature width to search span.")


# ============================================================ EXPERIMENT 4
def experiment_4_break_the_reference():
    """BREAK THE REFEREE. The whole study rests on the closed-form value being
    right. What happens if it isn't?

    Every verdict in results.csv is 'routine vs reference'. If the reference
    were wrong, correct routines would be scored as failures and you would
    never know from the table alone. This is the study's real single point of
    failure, and it is worth feeling."""
    W, C = 1e-6, 1/3

    def f(x):
        t = (x - C) / W
        return math.exp(-t * t) if abs(t) < 40 else 0.0

    good = 0.5 * W * math.sqrt(math.pi) * (
        math.erf((1 - C) / W) + math.erf((C + 1) / W))
    sloppy = W * math.sqrt(math.pi)          # the small-W approximation
    typo = 2.0 * good                        # a plausible factor-of-2 slip

    print("\n=== 4. BREAK THE REFERENCE ===")
    print(f"  closed form           {good:.15e}")
    print(f"  small-W approximation {sloppy:.15e}   "
          f"rel diff {abs(sloppy-good)/good:.2e}")
    print(f"  a factor-of-2 typo    {typo:.15e}   "
          f"rel diff {abs(typo-good)/good:.2e}")

    # an independent third opinion, driven properly so it actually works
    told = float(mpmath.quad(f, [-1, C, 1]))
    print(f"  mpmath, told where    {told:.15e}   "
          f"rel diff vs closed form {abs(told-good)/good:.2e}")
    print("  -> the closed form and a correctly-driven independent routine")
    print("     agree to ~1e-11. That agreement is what licenses the whole")
    print("     table. A reference nobody cross-checks is just another engine.")
    print("     Note the small-W approximation is indistinguishable HERE only")
    print("     because erf saturates at this width; raise W to 0.5 and it")
    print("     drifts. Approximations that hold in the tested regime and")
    print("     fail outside it are the easiest way to get a bad referee.")


EXPERIMENTS = [
    experiment_1_move_the_bump,
    experiment_2_change_the_shape,
    experiment_3_widen_the_interval,
    experiment_4_break_the_reference,
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        EXPERIMENTS[int(sys.argv[1]) - 1]()
    else:
        for fn in EXPERIMENTS:
            fn()
